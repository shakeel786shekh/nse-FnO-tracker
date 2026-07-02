# 📉 NSE F&O Live Tracker

> **Real-time NSE Options Chain Data with Black-Scholes Greeks — Powered by Angel One SmartAPI**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Angel One](https://img.shields.io/badge/Angel_One-SmartAPI-FF6B35?style=for-the-badge)](https://smartapi.angelbroking.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 Overview

A production-ready Python tracker for **NSE Futures & Options** market data. Connects to **Angel One SmartAPI** with TOTP-based 2FA, fetches live index prices + full options chain, computes **Black-Scholes Greeks**, and writes everything to **Google Sheets** automatically.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🔐 **Auto-TOTP Login** | Automated 2FA authentication with Angel One SmartAPI |
| 📊 **Live Index Data** | NIFTY 50, BANK NIFTY, SENSEX, FIN NIFTY, MIDCAP NIFTY |
| 📉 **Options Chain** | CE + PE for every strike/expiry with OI, Volume, IV |
| 📐 **Black-Scholes Greeks** | Delta, Gamma, Theta, Vega — computed in real-time |
| 🔄 **Auto Refresh** | Configurable interval (default: every 60 seconds) |
| 📋 **Google Sheets Output** | 3 sheet tabs — Indices, FnO Stocks, Options Chain |
| ⚡ **Parallel Fetching** | ThreadPoolExecutor for fast multi-strike data |

---

## 📁 Project Structure

```
nse-fo-tracker/
├── main_angel.py          ← Entry point — run this
├── angel_fetcher.py       ← Angel One SmartAPI data fetcher
├── greeks.py              ← Black-Scholes Greeks calculator
├── config.py              ← All settings in one place
├── requirements.txt       ← Python dependencies
├── RUN_SCANNER.bat        ← Windows one-click launcher
├── .gitignore
└── README.md
```

> ⚠️ **`Angel_login.json`** and **`service_account.json`** are NOT included — you must create these yourself (see setup below).

---

## 🚀 Quick Start

### Step 1 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Create `Angel_login.json`

```json
{
  "API_KEY":     "your_angel_one_api_key",
  "CLIENT_ID":   "your_client_id",
  "PASSWORD":    "your_login_password",
  "TOTP_SECRET": "your_totp_secret_key"
}
```

> Get these from [Angel One SmartAPI Dashboard](https://smartapi.angelbroking.com)

### Step 3 — Setup Google Sheets (15 min)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable **Google Sheets API** + **Google Drive API**
3. Create **Service Account** → Download JSON key → Rename to `service_account.json`
4. Create a Google Sheet named: **`NSE FnO Live Tracker`**
5. Share the sheet with your service account email (Editor access)

### Step 4 — Run

```bash
# Single run
python main_angel.py --once

# Continuous (every 60 seconds)
python main_angel.py

# Custom interval + specific expiries
python main_angel.py --interval 120 --expiries 27JUN2024,25JUL2024
```

### Windows Users

Double-click **`RUN_SCANNER.bat`** — choose scan mode from menu!

---

## 📊 Google Sheets Output

| Sheet Tab | Contents |
|-----------|---------|
| `Indices` | Live NIFTY, BANKNIFTY, SENSEX, etc. with % change |
| `FnO Stocks` | All FnO stocks — live LTP |
| `Options Chain` | CE+PE per strike/expiry — IV, OI, ΔOI, Greeks |

---

## 📐 Black-Scholes Greeks

| Greek | Meaning |
|-------|---------|
| **Delta** | Price change per ₹1 move in underlying |
| **Gamma** | Rate of Delta change |
| **Theta** | Daily time decay (₹ per day) |
| **Vega** | Price change per 1% IV move |

---

## ⚙️ Configuration (`config.py`)

```python
RISK_FREE_RATE         = 0.065   # 6.5% Indian T-bill rate
UPDATE_INTERVAL_SECONDS = 60     # Refresh every 60 sec
MAX_WORKERS            = 8       # Parallel API threads
GSHEETS_WRITE_PAUSE    = 1.2    # Pause between Sheet writes
```

---

## 🛠️ Troubleshooting

| Error | Fix |
|-------|-----|
| `SpreadsheetNotFound` | Sheet name must match `SPREADSHEET_NAME` in config.py exactly |
| `Login failed` | Check API_KEY, CLIENT_ID, PASSWORD in Angel_login.json |
| `TOTP invalid` | Sync system clock — TOTP is time-sensitive |
| `RESOURCE_EXHAUSTED` | Increase `GSHEETS_WRITE_PAUSE` in config.py |
| `scipy import error` | Run `pip install scipy numpy` |

---

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. It does not constitute financial advice. Always do your own research before trading.

---

## 👤 Author

**Shakeel Shekh** — Data Analyst & AI Automation Specialist

- 📧 shakeel786shekh@gmail.com
- 🔗 [GitHub](https://github.com/shakeel786shekh)
- 🌐 [Portfolio](https://shakeel786shekh.github.io)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
