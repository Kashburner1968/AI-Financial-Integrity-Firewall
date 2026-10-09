"""Convert a cloud snapshot to evidence ledger; self-contained per-run snapshot, no fake continuity."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from live_engine import Engine

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="output/bars.csv")
    parser.add_argument("--database",default="output/firewall.db")
    args=parser.parse_args()
    eng=Engine(args.database)
    rows=[]
    with open(args.input,newline="",encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                minute=datetime.fromisoformat(row["bar_time_utc"]).astimezone(timezone.utc).replace(second=0,microsecond=0).isoformat()
                if row["close"] not in ("",None):
                    rows.append((minute,row["symbol"],float(row["close"]),float(row["volume"]) if row["volume"] not in ("",None) else None,row["source"]))
            except (ValueError,KeyError):
                continue
    for minute,symbol,close,volume,source in sorted(rows):
        eng.bar(symbol,minute,close,volume,source)
        # time in CSV is historical; finalize each processed minute in order
        eng.finalize(now=datetime.fromisoformat(minute).timestamp()+60)
    if not eng.ledger.verify():
        raise SystemExit("Hash verification failure")
    print(f"Imported {len(rows)} source bars to independently verifiable per-run SQLite ledger")

if __name__=="__main__":
    main()
