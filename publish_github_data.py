"""Create bounded, public GitHub-hosted research snapshots from existing collector output.
No third-party accounts or tokens; GitHub Actions supplies GITHUB_TOKEN.
"""
import csv
import json
from layer4_transparency import summarize
from datetime import datetime, timezone
from pathlib import Path

def main():
    root=Path("output")
    dest=Path("site/data")
    dest.mkdir(parents=True,exist_ok=True)
    status=json.loads((root/"run_status.json").read_text(encoding="utf-8"))
    with (root/"bars.csv").open(newline="",encoding="utf-8") as f:
        bars=list(csv.DictReader(f))
    with (root/"candidate_alerts.csv").open(newline="",encoding="utf-8") as f:
        alerts=list(csv.DictReader(f))
    # No stale data presented as live; every record carries its source timestamp.
    latest={}
    for row in bars:
        symbol=row["symbol"]
        if symbol not in latest or row["bar_time_utc"]>latest[symbol]["bar_time_utc"]:
            latest[symbol]=row
    verification=json.loads((root/"verification.json").read_text(encoding="utf-8"))
    transparency=summarize(verification,status)
    data={"transparency":transparency,"verification":{k:v for k,v in verification.items() if k!="source_status"}, "collected_at_utc":status.get("retrieved_utc"),
          "source":status.get("source"),"errors":status.get("errors",[]),
          "latest":latest,"candidate_alerts":alerts[-100:],
          "bars":bars[-6000:],"warning":"Unverified research signals; not findings of market manipulation."}
    (dest/"transparency.json").write_text(json.dumps(transparency,indent=2),encoding="utf-8")
    (dest/"latest.json").write_text(json.dumps(data,separators=(",",":"),allow_nan=False),encoding="utf-8")
    # Persistent daily archive on GitHub main. One file per UTC date; last run replaces that
    # day's archive; prior days remain in git history. This is not an immutable evidence store.
    day=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive=Path("site/archive")
    archive.mkdir(parents=True,exist_ok=True)
    (archive/(day+".json")).write_text(json.dumps({
        "collected_at_utc":data["collected_at_utc"],
        "latest":latest,"candidate_alerts":data["candidate_alerts"],
        "errors":data["errors"],"transparency":transparency},separators=(",",":")),encoding="utf-8")
    print("Created GitHub-hosted dashboard JSON and dated snapshot")
if __name__=="__main__":
    main()
