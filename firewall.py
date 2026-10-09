"""Read-only CSV prototype for Layers 1 and 2. No trading or accusations."""
import argparse
import csv
from pathlib import Path

FIELDS = ("timestamp", "spy", "breadth_pct", "volume", "liquidity_proxy")

def load_rows(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        missing = set(FIELDS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(sorted(missing)))
        rows = []
        for record in reader:
            row = {"timestamp": record["timestamp"]}
            for name in FIELDS[1:]:
                row[name] = float(record[name])
            if not 0 <= row["breadth_pct"] <= 100:
                raise ValueError("breadth_pct must be between 0 and 100")
            if row["spy"] <= 0 or row["volume"] < 0 or row["liquidity_proxy"] < 0:
                raise ValueError("Invalid negative or zero market input")
            rows.append(row)
    return rows

def screen(rows):
    alerts = []
    for prev, curr in zip(rows, rows[1:]):
        price_change_pct = 100 * (curr["spy"] / prev["spy"] - 1)
        breadth_change = curr["breadth_pct"] - prev["breadth_pct"]
        volume_ratio = curr["volume"] / prev["volume"] if prev["volume"] else 0
        liquidity_ratio = curr["liquidity_proxy"] / prev["liquidity_proxy"] if prev["liquidity_proxy"] else 0
        candidates = []
        if price_change_pct > 0.05 and breadth_change < -3:
            candidates.append("price_up_breadth_down")
        if price_change_pct < -0.05 and volume_ratio > 1.5:
            candidates.append("selling_volume_spike")
        if price_change_pct < -0.05 and 0 < liquidity_ratio < 0.5:
            candidates.append("liquidity_proxy_decline")
        for label in candidates:
            alerts.append({"timestamp": curr["timestamp"], "candidate_signal": label,
                           "price_change_pct": round(price_change_pct, 4),
                           "breadth_change_points": round(breadth_change, 4),
                           "volume_ratio": round(volume_ratio, 4),
                           "liquidity_ratio": round(liquidity_ratio, 4)})
    return alerts

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="alerts.csv")
    args = parser.parse_args()
    alerts = screen(load_rows(args.input))
    headers = ["timestamp", "candidate_signal", "price_change_pct", "breadth_change_points", "volume_ratio", "liquidity_ratio"]
    with open(args.output, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(alerts)
    print(f"Screened data; wrote {len(alerts)} candidate alerts to {args.output}. Not findings of manipulation.")

if __name__ == "__main__":
    main()
