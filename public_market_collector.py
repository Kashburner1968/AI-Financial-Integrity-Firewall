"""Cloud-run, read-only public market-data collection and candidate screening.

Uses Yahoo Finance's unofficial public chart endpoint. Data may be delayed, blocked,
incomplete, or subject to usage terms. No trading, brokerage account, or user machine.
"""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

SYMBOLS = ["SPY", "QQQ", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "^TNX", "BZ=F", "^VIX"]
FIELDS = ["retrieved_utc", "symbol", "bar_time_utc", "open", "high", "low", "close", "volume", "source", "status"]
ALERT_FIELDS = ["retrieved_utc", "symbol", "bar_time_utc", "signal", "change_pct", "volume_ratio", "classification"]

def request_bars(symbol, timeout=18):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol, safe="") + "?" + urlencode({
        "interval": "1m", "range": "1d", "includePrePost": "false"
    })
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 FinancialIntegrityFirewall research prototype",
                                    "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise ValueError(str(chart["error"]))
    result = (chart.get("result") or [None])[0]
    if not result:
        raise ValueError("No chart result")
    timestamps = result.get("timestamp") or []
    quotes = (result.get("indicators", {}).get("quote") or [{}])[0]
    retrieved = datetime.now(timezone.utc).isoformat()
    bars = []
    for i, stamp in enumerate(timestamps):
        def field(name):
            values = quotes.get(name) or []
            return values[i] if i < len(values) else None
        close = field("close")
        if close is None:
            continue
        bars.append({"retrieved_utc": retrieved, "symbol": symbol,
                     "bar_time_utc": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                     "open": field("open"), "high": field("high"), "low": field("low"),
                     "close": close, "volume": field("volume"), "source": "Yahoo Finance unofficial chart",
                     "status": "observed"})
    return bars

def detect(bars):
    alerts = []
    for prev, curr in zip(bars, bars[1:]):
        if prev["close"] is None or not prev["close"]:
            continue
        change = 100 * (curr["close"] / prev["close"] - 1)
        v0, v1 = prev["volume"], curr["volume"]
        if v0 is None or v1 is None or v0 <= 0:
            continue
        ratio = v1 / v0
        if change < -0.05 and ratio >= 1.5:
            alerts.append({"retrieved_utc": curr["retrieved_utc"], "symbol": curr["symbol"],
                           "bar_time_utc": curr["bar_time_utc"], "signal": "selling_volume_spike",
                           "change_pct": round(change, 5), "volume_ratio": round(ratio, 3),
                           "classification": "unverified_candidate"})
    return alerts

def write_csv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--symbols", default=",".join(SYMBOLS))
    args = parser.parse_args()
    all_bars, alerts, errors = [], [], []
    for symbol in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        try:
            bars = request_bars(symbol)
            all_bars.extend(bars)
            alerts.extend(detect(bars))
            print(f"{symbol}: {len(bars)} one-minute bars", flush=True)
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})
            print(f"{symbol}: unavailable: {exc}", flush=True)
        time.sleep(0.3)
    out = Path(args.output_dir)
    write_csv(out / "bars.csv", FIELDS, all_bars)
    write_csv(out / "candidate_alerts.csv", ALERT_FIELDS, alerts)
    (out / "run_status.json").write_text(json.dumps({
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance unofficial chart endpoint", "symbols_requested": args.symbols.split(","),
        "symbols_with_data": sorted(set(r["symbol"] for r in all_bars)),
        "bar_count": len(all_bars), "candidate_count": len(alerts), "errors": errors,
        "warning": "Public price bars only; no institutional identities, regulatory audit trail, or proof of manipulation."
    }, indent=2), encoding="utf-8")
    if not all_bars:
        print("No market data retrieved; marking workflow failed.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
