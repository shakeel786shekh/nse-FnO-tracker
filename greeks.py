# ============================================================
#  greeks.py  –  Black-Scholes Option Greeks Calculator
# ============================================================

import math
from scipy.stats import norm
from config import RISK_FREE_RATE


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float):
    """Compute d1 and d2 for Black-Scholes."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None, None
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def calculate_greeks(
    S: float,        # Spot price
    K: float,        # Strike price
    T: float,        # Time to expiry in years
    sigma: float,    # IV (as decimal, e.g. 0.20 for 20%)
    option_type: str,  # "CE" or "PE"
    r: float = RISK_FREE_RATE,
) -> dict:
    """
    Returns a dict with Delta, Gamma, Theta (per day), Vega (per 1% IV move).
    Returns zeros if inputs are invalid.
    """
    empty = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    d1, d2 = _d1_d2(S, K, T, r, sigma)
    if d1 is None:
        return empty

    sqrt_T = math.sqrt(T)
    nd1    = norm.pdf(d1)          # standard normal PDF at d1
    Nr_d1  = norm.cdf(d1)
    Nr_d2  = norm.cdf(d2)

    # ── Gamma (same for CE and PE) ───────────────────────────
    gamma = nd1 / (S * sigma * sqrt_T)

    # ── Vega (per 1 % change in IV) ──────────────────────────
    vega = S * nd1 * sqrt_T * 0.01   # multiply by 0.01 → per 1 %

    # ── Theta (per calendar day) ─────────────────────────────
    if option_type.upper() == "CE":
        delta = Nr_d1
        theta = (
            -(S * nd1 * sigma) / (2 * sqrt_T)
            - r * K * math.exp(-r * T) * Nr_d2
        ) / 365.0

    elif option_type.upper() == "PE":
        delta = Nr_d1 - 1
        theta = (
            -(S * nd1 * sigma) / (2 * sqrt_T)
            + r * K * math.exp(-r * T) * norm.cdf(-d2)
        ) / 365.0

    else:
        return empty

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 4),
        "vega":  round(vega, 4),
    }
