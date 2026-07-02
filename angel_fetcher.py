# ============================================================
#  angel_fetcher.py  –  AngelOne SmartAPI Data Fetcher
#  Replaces nse_session.py + fetcher.py entirely
#  Uses: smartapi-python (official Angel One library)
# ============================================================

import logging
import time
import pyotp
import json
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

from SmartApi import SmartConnect
from greeks import calculate_greeks
from config import RISK_FREE_RATE, MAX_WORKERS

logger = logging.getLogger(__name__)

# ── Load credentials ─────────────────────────────────────────
def _load_creds(path: str = "Angel_login.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)

# ── Indices symbol tokens (Angel uses numeric tokens) ────────
# These are fixed tokens for major indices on Angel SmartAPI
INDEX_TOKENS = {
    "NIFTY 50":     {"token": "99926000", "exch": "NSE"},
    "NIFTY BANK":   {"token": "99926009", "exch": "NSE"},
    "SENSEX":       {"token": "99919000", "exch": "BSE"},
    "NIFTY FIN SERVICE": {"token": "99926037", "exch": "NSE"},
    "NIFTY MID SELECT":  {"token": "99926074", "exch": "NSE"},
}

# AngelOne option chain API base
ANGEL_OPTION_CHAIN_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking/derivatives/v1/fetch_options_chain"


# ── Helpers ──────────────────────────────────────────────────
def _safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def _days_to_expiry(expiry_str: str) -> float:
    """Convert 'DD-MMM-YYYY' or 'DDMMMYYYY' to fractional years."""
    for fmt in ("%d-%b-%Y", "%d%b%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            exp = datetime.strptime(expiry_str, fmt).date()
            delta = (exp - date.today()).days
            return max(delta, 0) / 365.0 or 0.001
        except ValueError:
            continue
    return 0.001


# ── Main Angel Session Class ─────────────────────────────────
class AngelFetcher:
    """
    Authenticates with AngelOne SmartAPI and fetches:
      - Index spot prices (Nifty, BankNifty, Sensex, etc.)
      - FnO stock list + LTP
      - Options chain with Greeks (Black-Scholes)
    """

    def __init__(self, creds_path: str = "Angel_login.json"):
        self.creds    = _load_creds(creds_path)
        self.smart    = SmartConnect(api_key=self.creds["API_KEY"])
        self.auth_token  = None
        self.feed_token  = None
        self._login()

    # ── Authentication ───────────────────────────────────────

    def _login(self):
        """Login using TOTP-based 2FA (required by AngelOne)."""
        totp_code = pyotp.TOTP(self.creds["TOTP_SECRET"]).now()
        logger.info("Generated TOTP: %s", totp_code)

        data = self.smart.generateSession(
            clientCode = self.creds["CLIENT_ID"],
            password   = self.creds["PASSWORD"],
            totp       = totp_code,
        )

        if data["status"] is False:
            raise RuntimeError(f"AngelOne login failed: {data['message']}")

        self.auth_token  = data["data"]["jwtToken"]
        self.feed_token  = self.smart.getfeedToken()
        logger.info("✅ AngelOne login successful. Client: %s", self.creds["CLIENT_ID"])

    def _refresh_if_needed(self):
        """Refresh JWT token proactively before it expires (4 hours)."""
        try:
            refresh_data = self.smart.generateToken(
                self.smart.refresh_token
            )
            self.auth_token = refresh_data["data"]["jwtToken"]
            logger.info("Token refreshed.")
        except Exception as e:
            logger.warning("Token refresh failed, re-logging: %s", e)
            self._login()

    # ── Index Spot Prices ────────────────────────────────────

    def fetch_index_spots(self) -> List[Dict]:
        """Fetch live LTP for major indices using getQuote."""
        rows = []
        for name, info in INDEX_TOKENS.items():
            try:
                resp = self.smart.ltpData(
                    exchange      = info["exch"],
                    tradingsymbol = name,
                    symboltoken   = info["token"],
                )
                d = resp.get("data", {})
                rows.append({
                    "symbol":   name,
                    "ltp":      _safe_float(d.get("ltp")),
                    "open":     _safe_float(d.get("open")),
                    "high":     _safe_float(d.get("high")),
                    "low":      _safe_float(d.get("low")),
                    "close":    _safe_float(d.get("close")),
                    "change":   _safe_float(d.get("ltp")) - _safe_float(d.get("close")),
                    "pct_chg":  round(
                        (_safe_float(d.get("ltp")) - _safe_float(d.get("close")))
                        / (_safe_float(d.get("close")) or 1) * 100, 2
                    ),
                    "prev_cls": _safe_float(d.get("close")),
                })
                logger.info("Index %s LTP: %.2f", name, rows[-1]["ltp"])
            except Exception as e:
                logger.error("Index spot error [%s]: %s", name, e)
        return rows

    # ── FnO Stock List ───────────────────────────────────────

    def fetch_fno_stock_list(self) -> List[Dict]:
        """
        Fetch master scrip list from AngelOne and filter for FnO stocks.
        Returns list of {symbol, token, lotsize}.
        """
        try:
            # Angel provides a master CSV/JSON — filter EQ + FnO eligible
            # Using searchScrip for FnO-enabled equities
            resp = self.smart.getMarketData(
                mode        = "FULL",
                exchangeTokens = {"NSE": list(range(1, 5))}  # placeholder
            )
            # NOTE: For full FnO list, use the scrip master JSON from Angel
            # Download: https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json
            # Filter by: instrumenttype == "FUTSTK" or "OPTSTK"
            logger.warning(
                "Tip: Download OpenAPIScripMaster.json from AngelOne for complete FnO list."
            )
            return []
        except Exception as e:
            logger.error("FnO stock list error: %s", e)
            return []

    def fetch_fno_ltps_from_master(self, master_path: str = "OpenAPIScripMaster.json") -> List[Dict]:
        """
        If you have downloaded OpenAPIScripMaster.json, this method
        extracts all FnO stock symbols + tokens and fetches their LTPs.
        """
        import json, os
        if not os.path.exists(master_path):
            logger.warning("Master file not found: %s — skipping FnO stocks.", master_path)
            return []

        with open(master_path) as f:
            master = json.load(f)

        # Filter for EQ segment FnO stocks
        fno_stocks = [
            s for s in master
            if s.get("instrumenttype") in ("", "EQ")
            and s.get("exch_seg") == "NSE"
            and s.get("symbol", "").endswith("-EQ")
        ][:150]   # cap at 150 to avoid rate limits

        logger.info("Found %d FnO EQ stocks in master.", len(fno_stocks))

        rows = []
        def _get_ltp(stock):
            try:
                resp = self.smart.ltpData(
                    exchange      = "NSE",
                    tradingsymbol = stock["symbol"],
                    symboltoken   = stock["token"],
                )
                return {
                    "symbol": stock["symbol"].replace("-EQ", ""),
                    "token":  stock["token"],
                    "ltp":    _safe_float(resp.get("data", {}).get("ltp")),
                }
            except Exception as e:
                logger.warning("LTP error [%s]: %s", stock.get("symbol"), e)
                return None

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = [pool.submit(_get_ltp, s) for s in fno_stocks]
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    rows.append(result)

        return rows

    # ── Options Chain ────────────────────────────────────────

    def fetch_option_chain(
        self,
        symbol: str,
        expiry: str,
        strike_price: float,
        spot_price: float,
        opt_type: str = "CE",   # "CE" or "PE"
    ) -> Optional[Dict]:
        """Fetch single option quote and compute Greeks."""
        try:
            # Angel option chain fetch
            resp = self.smart.getOptionGreeks(
                Name         = symbol,
                expirydate   = expiry,
                strikeprice  = strike_price,
                optiontype   = opt_type,
            )
            if not resp or resp.get("status") is False:
                return None

            d   = resp.get("data", {})
            iv  = _safe_float(d.get("impliedVolatility")) / 100.0
            ltp = _safe_float(d.get("lastTradedPrice") or d.get("ltp"))
            T   = _days_to_expiry(expiry)

            greeks = calculate_greeks(
                S=spot_price, K=strike_price, T=T,
                sigma=iv, option_type=opt_type, r=RISK_FREE_RATE
            )

            return {
                "symbol":   symbol,
                "expiry":   expiry,
                "strike":   strike_price,
                "type":     opt_type,
                "ltp":      ltp,
                "iv_pct":   round(iv * 100, 2),
                "volume":   int(_safe_float(d.get("tradedVolume") or d.get("volume"))),
                "oi":       int(_safe_float(d.get("openInterest") or d.get("oi"))),
                "chg_oi":   int(_safe_float(d.get("changeinOpenInterest") or d.get("chg_oi"))),
                "delta":    greeks["delta"],
                "gamma":    greeks["gamma"],
                "theta":    greeks["theta"],
                "vega":     greeks["vega"],
                "dte":      max(0, int(T * 365)),
            }
        except Exception as e:
            logger.error("Option quote error [%s %s %s %s]: %s",
                         symbol, expiry, strike_price, opt_type, e)
            return None

    def fetch_option_chain_bulk(
        self,
        symbol: str,
        spot_price: float,
        expiries: List[str],
        strikes: List[float],
    ) -> List[Dict]:
        """
        Fetch CE+PE for every (expiry × strike) combination in parallel.
        Tip: keep strikes to ATM ± 10 to limit API calls.
        """
        tasks = [
            (symbol, exp, strike, spot_price, opt_type)
            for exp     in expiries
            for strike  in strikes
            for opt_type in ("CE", "PE")
        ]
        logger.info("Fetching %d option quotes for %s …", len(tasks), symbol)

        rows = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(self.fetch_option_chain, *t): t
                for t in tasks
            }
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    rows.append(result)

        return rows

    # ── Master Run ───────────────────────────────────────────

    def run(self, expiries: List[str] = None, strikes_range: int = 10):
        """
        Full data-collection cycle.
        Returns (index_rows, stock_rows, option_rows).

        Args:
            expiries:      List of expiry strings e.g. ['27JUN2024','25JUL2024']
                           If None, you must provide them manually or via scrip master.
            strikes_range: How many strikes above/below ATM to fetch (default ±10).
        """
        logger.info("=== AngelOne data fetch cycle started ===")

        # 1. Index spots
        index_rows = self.fetch_index_spots()
        spot_map   = {r["symbol"]: r["ltp"] for r in index_rows}

        # 2. FnO stocks (requires OpenAPIScripMaster.json)
        stock_rows = self.fetch_fno_ltps_from_master()

        # 3. Options chain — Nifty as example
        option_rows = []
        if expiries:
            nifty_spot = spot_map.get("NIFTY 50", 24000)
            # Generate ATM ± strikes_range strikes (multiples of 50 for Nifty)
            atm = round(nifty_spot / 50) * 50
            strikes = [atm + (i * 50) for i in range(-strikes_range, strikes_range + 1)]

            option_rows = self.fetch_option_chain_bulk(
                symbol      = "NIFTY",
                spot_price  = nifty_spot,
                expiries    = expiries,
                strikes     = strikes,
            )

        logger.info(
            "Done → %d indices | %d stocks | %d option rows",
            len(index_rows), len(stock_rows), len(option_rows),
        )
        return index_rows, stock_rows, option_rows
