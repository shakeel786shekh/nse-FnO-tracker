# ============================================================
#  main_angel.py  –  AngelOne version of the tracker
#  Run: python main_angel.py
#       python main_angel.py --once
#       python main_angel.py --interval 120 --expiries 27JUN2024,25JUL2024
# ============================================================

import argparse
import logging
import sys
import time

from angel_fetcher import AngelFetcher
from sheets_writer  import SheetsWriter
from config         import UPDATE_INTERVAL_SECONDS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("tracker_angel.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main_angel")


def run_once(fetcher: AngelFetcher, writer: SheetsWriter, expiries, strikes_range):
    index_rows, stock_rows, option_rows = fetcher.run(
        expiries=expiries, strikes_range=strikes_range
    )
    logger.info("Writing to Google Sheets …")
    writer.write_indices(index_rows)
    writer.write_fno_stocks(stock_rows)
    if option_rows:
        writer.write_options_chain(option_rows)
    logger.info("✅ Sheets updated.")


def run_loop(fetcher, writer, interval, expiries, strikes_range):
    logger.info("Continuous mode — interval=%ds", interval)
    cycle = 0
    while True:
        cycle += 1
        logger.info("── Cycle #%d ──", cycle)
        try:
            run_once(fetcher, writer, expiries, strikes_range)
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
            break
        except Exception as e:
            logger.error("Cycle #%d error: %s", cycle, e, exc_info=True)
        logger.info("Sleeping %ds …\n", interval)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="AngelOne FnO Tracker → Google Sheets")
    parser.add_argument("--once",     action="store_true", help="Single run then exit")
    parser.add_argument("--interval", type=int, default=UPDATE_INTERVAL_SECONDS)
    parser.add_argument(
        "--expiries", type=str, default="",
        help="Comma-separated expiry dates e.g. 27JUN2024,25JUL2024"
    )
    parser.add_argument(
        "--strikes", type=int, default=10,
        help="Number of strikes above/below ATM (default 10)"
    )
    args = parser.parse_args()

    expiries = [e.strip() for e in args.expiries.split(",") if e.strip()] or None

    logger.info("Initialising AngelOne session …")
    fetcher = AngelFetcher(creds_path="Angel_login.json")
    writer  = SheetsWriter()

    if args.once:
        run_once(fetcher, writer, expiries, args.strikes)
    else:
        run_loop(fetcher, writer, args.interval, expiries, args.strikes)


if __name__ == "__main__":
    main()
