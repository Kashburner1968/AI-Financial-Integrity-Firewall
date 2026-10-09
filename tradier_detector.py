"""Read-only candidate screening on Tradier one-minute OHLCV data.
A candidate is NOT evidence of market manipulation or institutional identity.
"""
import argparse
import csv
from collections import defaultdict

def analyze(rows):
    by_symbol = defaultdict(list)
    for row in rows:
        by_symbol[row["symbol"]].append(row)
    out = []
    for symbol, items in by_symbol.items():
        items.sort(key=lambda x: x["time"])
        for a, b in zip(items, items[1:]):
            try:
                p0, p1 = float(a["close"]), float(b["close"])
                v0, v1 = float(a["volume"]), float(b["volume"])
            except (ValueError, KeyError, TypeError):
                continue
            if p0 <= 0 or v0 <= 0:
                continue
            delta = 100 * (p1 / p0 - 1)
            volume_ratio = v1 / v0
            if delta < -0.05 and volume_ratio >= 1.5:
                out.append({"time": b["time"], "symbol": symbol, "signal": "selling_volume_spike",
                            "price_change_pct": round(delta, 5), "volume_ratio": round(volume_ratio, 3),
                            "source": "Tradier", "classification": "unverified_candidate"})
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/tradier_1min.csv")
    parser.add_argument("--output", default="data/candidate_alerts.csv")
    args = parser.parse_args()
    with open(args.input, newline="", encoding="utf-8") as stream:
        alerts = analyze(list(csv.DictReader(stream)))
    from pathlib import Path
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("time", "symbol", "signal", "price_change_pct", "volume_ratio", "source", "classification"))
        writer.writeheader()
        writer.writerows(alerts)
    print(f"{len(alerts)} unverified candidates saved to {args.output}")

if __name__ == "__main__":
    main()
