"""Upload public research bars/alerts to persistent Supabase via HTTPS.
Requires SUPABASE_URL and SUPABASE_SECRET_KEY, set only in GitHub Actions secrets.
"""
import csv
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

def config():
    url=os.environ.get("SUPABASE_URL","").rstrip("/")
    key=os.environ.get("SUPABASE_SECRET_KEY","")
    if not url.startswith("https://") or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY are required as cloud secrets")
    return url,key

def post(table,records,key,url):
    if not records:
        return
    endpoint=url+"/rest/v1/"+table
    request=urllib.request.Request(endpoint,data=json.dumps(records,allow_nan=False).encode(),
        headers={"apikey":key,"Authorization":"Bearer "+key,
                 "Content-Type":"application/json","Prefer":"resolution=ignore-duplicates,return=minimal"},
        method="POST")
    with urllib.request.urlopen(request,timeout=45) as response:
        if response.status not in (200,201,204):
            raise RuntimeError("Supabase rejected records: "+str(response.status))

def batched(table,records,key,url):
    for i in range(0,len(records),250):
        post(table,records[i:i+250],key,url)

def upload(root="output"):
    url,key=config()
    root=Path(root)
    with (root/"bars.csv").open(newline="",encoding="utf-8") as f:
        raw=list(csv.DictReader(f))
    bars=[]
    for r in raw:
        try:
            bars.append({k:(float(r[k]) if r.get(k) not in ("",None) else None)
                 for k in ("open","high","low","close","volume")} |
                 {k:r[k] for k in ("symbol","bar_time_utc","source","retrieved_utc")})
        except (ValueError,KeyError):
            continue
    with (root/"candidate_alerts.csv").open(newline="",encoding="utf-8") as f:
        raw_alerts=list(csv.DictReader(f))
    alerts=[]
    for r in raw_alerts:
        try:
            event_id="|".join((r["source"],r["symbol"],r["bar_time_utc"],r["signal"]))
            alerts.append({"event_id":event_id,"symbol":r["symbol"],"bar_time_utc":r["bar_time_utc"],
                "signal":r["signal"],"change_pct":float(r["change_pct"]),
                "volume_ratio":float(r["volume_ratio"]),"classification":r["classification"],
                "source":r["source"],"retrieved_utc":r["retrieved_utc"]})
        except (ValueError,KeyError):
            continue
    batched("market_bars",bars,key,url)
    batched("market_alerts",alerts,key,url)
    status=json.loads((root/"run_status.json").read_text(encoding="utf-8"))
    run_id=os.environ.get("GITHUB_RUN_ID",datetime.now(timezone.utc).isoformat())
    post("collection_runs",[{"run_id":str(run_id),"collected_utc":status["retrieved_utc"],
        "bar_count":len(bars),"alert_count":len(alerts),"status":"completed","details":{
            "source":status.get("source"),"symbols_with_data":status.get("symbols_with_data",[]),
            "errors":status.get("errors",[])}}],key,url)
    print("Persisted",len(bars),"bars and",len(alerts),"candidate alerts in Supabase")

if __name__=="__main__":
    upload()
