"""Read-only Tradier one-minute market data ingestion. Requires TRADIER_TOKEN.
No trading endpoints, orders, or account information are accessed.
"""
import argparse
import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.tradier.com/v1/markets/timesales"
SYMBOLS = ("SPY", "QQQ", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "AVGO", "TSLA")
FIELDS = ("symbol", "time", "timestamp", "open", "high", "low", "close", "volume", "source", "collected_at_utc")
def fetch(symbol, start, end, token, timeout=20):
    params = urlencode({"symbol": symbol, "interval": "1min", "start": start, "end": end, "session_filter": "open"})
    req = Request(BASE + "?" + params, headers={"Authorization": "Bearer " + token, "Accept": "application/json",
                                                "User-Agent": "AI-Financial-Integrity-Firewall/0.1"})
    with urlopen(req, timeout=timeout) as response:
        payload = json.load(response)
    result = payload.get("series") or {}
    data = result.get("data") or []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("Unexpected Tradier time-series response")
    return data

def normalize(symbol, items, collected_at):
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if not all(item.get(k) is not None for k in ("time", "open", "high", "low", "close", "volume")):
            continue
        rows.append({"symbol": symbol, "time": item["time"], "timestamp": item.get("timestamp", ""),
                     "open": item["open"], "high": item["high"], "low": item["low"], "close": item["close"],
                     "volume": item["volume"], "source": "Tradier 1min timesales", "collected_at_utc": collected_at})
    return rows

def append_unique(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists() and path.stat().st_size:
        with path.open(newline="", encoding="utf-8") as file:
            existing = {(r["symbol"], r["time"]) for r in csv.DictReader(file)}
    fresh = [r for r in rows if (r["symbol"], r["time"]) not in existing]
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if not existing and path.stat().st_size == 0:
            writer.writeheader()
        writer.writerows(fresh)
    return len(fresh)

def collect(symbols, output, lookback, token):
    # Tradier API documents local-market datetime strings; use America/New_York.
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("America/New_York"))
    start = (now - timedelta(minutes=lookback)).strftime("%Y-%m-%d %H:%M")
    end = now.strftime("%Y-%m-%d %H:%M")
    stamp = datetime.now(timezone.utc).isoformat()
    total = 0
    for symbol in symbols:
        try:
            rows = normalize(symbol, fetch(symbol, start, end, token), stamp)
            count = append_unique(output, rows)
            total += count
            print(f"{symbol}: {count} new bars, {len(rows)} returned", flush=True)
        except Exception as exc:
            print(f"{symbol}: collection error: {exc}", flush=True)
    return total

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", default=",".join(SYMBOLS))
    parser.add_argument("--output", default="data/tradier_1min.csv")
    parser.add_argument("--lookback", type=int, default=10)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    token = os.getenv("TRADIER_TOKEN")
    if not token:
        parser.error("TRADIER_TOKEN is not set. Never paste tokens into GitHub.")
    if args.interval < 60 or args.lookback < 1:
        parser.error("Interval must be >= 60 seconds and lookback >= 1 minute")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    while True:
        collect(symbols, args.output, args.lookback, token)
        if args.once:
            break
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
