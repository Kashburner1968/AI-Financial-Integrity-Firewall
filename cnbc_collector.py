"""CNBC quote snapshot collector (unofficial, undocumented CNBC endpoint).

Read-only. Samples quotes at a configured interval; CNBC does NOT supply one-minute
OHLCV candles or exchange order flow through this endpoint. A quote snapshot is not
a candle. Never fabricate breadth, liquidity, or institutional positions.
"""
import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

URL = "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
DEFAULT_SYMBOLS = ("SPY", "QQQ", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "GOOG", "NFLX", "US10Y", "VIX", "@LCO.1")
HEADERS = ("collected_at_utc", "symbol", "last", "change", "change_pct", "volume", "quote_time", "source", "realtime", "status")
USER_AGENT = "Mozilla/5.0 (compatible; FinancialIntegrityFirewall/0.1; research-only)"

def fetch_quotes(symbols, timeout=15):
    params = urlencode({"symbols": "|".join(symbols), "requestMethod": "itv", "noform": 1,
                        "partnerId": 2, "fund": 1, "exthrs": 1, "output": "json", "events": 1})
    request = Request(URL + "?" + params, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    quotes = payload.get("FormattedQuoteResult", {}).get("FormattedQuote", [])
    if isinstance(quotes, dict):
        quotes = [quotes]
    if not isinstance(quotes, list):
        raise ValueError("CNBC quote payload changed: FormattedQuote is not a list")
    return quotes

def make_rows(quotes, symbols, collected_at=None):
    collected_at = collected_at or datetime.now(timezone.utc).isoformat()
    by_symbol = {str(q.get("symbol", "")).upper(): q for q in quotes if isinstance(q, dict)}
    rows = []
    for symbol in symbols:
        q = by_symbol.get(symbol.upper(), {})
        rows.append({
            "collected_at_utc": collected_at,
            "symbol": symbol,
            "last": q.get("last", ""),
            "change": q.get("change", ""),
            "change_pct": q.get("change_pct", ""),
            "volume": q.get("volume", ""),
            "quote_time": q.get("last_time", ""),
            "source": q.get("provider", "CNBC quote cache") if q else "",
            "realtime": q.get("realTime", ""),
            "status": "ok" if q.get("last") not in (None, "", "--") else "missing",
        })
    return rows

def append_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        if is_new:
            writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--output", default="data/cnbc_snapshots.csv")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between snapshots; minimum 60")
    parser.add_argument("--once", action="store_true", help="Collect one snapshot and exit")
    args = parser.parse_args()
    if args.interval < 60:
        parser.error("Minimum polling interval is 60 seconds")
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        parser.error("At least one symbol is required")
    while True:
        try:
            quotes = fetch_quotes(symbols)
            rows = make_rows(quotes, symbols)
            append_csv(args.output, rows)
            print(f"{rows[0]['collected_at_utc']} | CNBC | {sum(r['status']=='ok' for r in rows)}/{len(rows)} quotes saved", flush=True)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"CNBC collection failed: {exc}", flush=True)
            if args.once:
                raise SystemExit(1)
        if args.once:
            break
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
