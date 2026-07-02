# ============================================================
#  config.py  –  Central configuration for NSE FnO Tracker
# ============================================================

import os

# ── Google Sheets ────────────────────────────────────────────
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDS_JSON", "service_account.json")
SPREADSHEET_NAME        = "NSE FnO Live Tracker"          # exact name in Drive
SHEET_INDICES           = "Indices"
SHEET_FNO_STOCKS        = "FnO Stocks"
SHEET_OPTIONS_CHAIN     = "Options Chain"

# ── NSE Endpoints ────────────────────────────────────────────
NSE_BASE_URL            = "https://www.nseindia.com"
NSE_OPTION_CHAIN_URL    = "https://www.nseindia.com/api/option-chain-indices"
NSE_OPTION_CHAIN_EQ_URL = "https://www.nseindia.com/api/option-chain-equities"
NSE_INDICES_URL         = "https://www.nseindia.com/api/allIndices"
NSE_QUOTE_URL           = "https://www.nseindia.com/api/quote-equity"
NSE_FNO_LIST_URL        = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"

# ── Indices to track ─────────────────────────────────────────
INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]

# ── Scraping / Session ───────────────────────────────────────
REQUEST_TIMEOUT         = 15        # seconds
RETRY_ATTEMPTS          = 5
RETRY_BASE_DELAY        = 2         # seconds (exponential backoff base)
SESSION_REFRESH_EVERY   = 300       # re-warm session every 5 minutes

# ── Risk-Free Rate for Greeks ────────────────────────────────
RISK_FREE_RATE          = 0.065     # 6.5 % p.a. (approx Indian T-bill)

# ── Concurrency ──────────────────────────────────────────────
MAX_WORKERS             = 8         # ThreadPoolExecutor workers

# ── Update Interval ──────────────────────────────────────────
UPDATE_INTERVAL_SECONDS = 60        # how often to refresh data

# ── Google Sheets API safety ─────────────────────────────────
GSHEETS_WRITE_PAUSE     = 1.2       # seconds between batch_update calls
