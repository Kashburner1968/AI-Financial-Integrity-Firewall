"""Layer 3: reproducible, conservative verification of Layer 2 candidates.

Never equate a price/volume anomaly with manipulation. All inputs are public
one-minute bars, and independent corroboration is unavailable in this feed.
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

FIELDS=("symbol","bar_time_utc","signal","change_pct","volume_ratio")
def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()
def num(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (ValueError,TypeError):
        return None

def verify(bars,alerts,collection_status=None):
    groups=defaultdict(dict)
    for b in bars:
        key=(b.get("symbol"),b.get("bar_time_utc"))
        if key[0] and key[1] and num(b.get("close")) is not None:
            groups[key[0]][key[1]]=b
    reports=[]
    for alert in alerts:
        symbol=alert.get("symbol","")
        when=alert.get("bar_time_utc","")
        rows=sorted(groups.get(symbol,{}).values(),key=lambda b:b["bar_time_utc"])
        index=next((i for i,r in enumerate(rows) if r["bar_time_utc"]==when),None)
        checks={}
        alternatives=[]
        reasons=[]
        actual_change=actual_ratio=None
        if index is None or index==0:
            reasons.append("Missing candidate bar or immediately preceding bar")
        else:
            previous,current=rows[index-1],rows[index]
            p0,p1=num(previous.get("close")),num(current.get("close"))
            v0,v1=num(previous.get("volume")),num(current.get("volume"))
            try:
                gap=(datetime.fromisoformat(when.replace("Z","+00:00"))-
                     datetime.fromisoformat(previous["bar_time_utc"].replace("Z","+00:00"))).total_seconds()
            except (ValueError,TypeError):
                gap=None
            checks["consecutive_one_minute_bars"]=gap==60
            if gap!=60:
                reasons.append("Adjacent rows do not represent consecutive minutes")
            if p0 and p1 is not None and v0 and v1 is not None:
                actual_change=100*(p1/p0-1)
                actual_ratio=v1/v0
                checks["candidate_rule_reproduced"]=(actual_change < -0.05 and actual_ratio>=1.5)
                checks["reported_values_match"]=(
                    abs(actual_change-(num(alert.get("change_pct")) or float("inf")))<0.00002
                    and abs(actual_ratio-(num(alert.get("volume_ratio")) or float("inf")))<0.002)
            else:
                checks["candidate_rule_reproduced"]=False
                checks["reported_values_match"]=False
                reasons.append("Price or volume input invalid")
            window=rows[max(0,index-20):index]
            volumes=[num(r.get("volume")) for r in window]
            volumes=[v for v in volumes if v is not None and v>0]
            if len(volumes)>=10 and v1 is not None:
                median=sorted(volumes)[len(volumes)//2]
                checks["above_recent_volume_median"]=v1>=1.5*median
                if not checks["above_recent_volume_median"]:
                    alternatives.append("Prior-minute ratio may reflect an unusually quiet previous minute")
            else:
                checks["above_recent_volume_median"]=None
                alternatives.append("Insufficient recent volume baseline")
            if len(rows)-1==index:
                alternatives.append("Latest bar may be incomplete when collected")
            try:
                minute=datetime.fromisoformat(when.replace("Z","+00:00"))
                if (minute.hour==13 and minute.minute<=45) or (minute.hour==14 and minute.minute<=45):
                    alternatives.append("Opening-session price discovery or elevated opening volume may contribute; exchange-local time not confirmed")
            except ValueError:
                pass
        alternatives.extend([
            "News, scheduled economic releases, or earnings may explain price and volume",
            "Index constituent moves, ETF hedging, or ordinary portfolio rebalancing may explain the pattern",
            "Vendor data corrections, missing bars, and delayed quotes remain possible",
        ])
        reproducible=bool(checks.get("consecutive_one_minute_bars") and checks.get("candidate_rule_reproduced") and checks.get("reported_values_match"))
        evidence={"candidate":{k:alert.get(k) for k in FIELDS},
                  "previous_bar":rows[index-1] if index is not None and index>0 else None,
                  "candidate_bar":rows[index] if index is not None else None,
                  "checks":checks,"alternatives":alternatives,"limitations":reasons}
        reports.append({
            "event_id":digest({"symbol":symbol,"bar_time_utc":when,"signal":alert.get("signal")})[:24],
            "symbol":symbol,"bar_time_utc":when,"signal":alert.get("signal"),
            "status":"reproduced_unverified" if reproducible else "not_reproduced",
            "reproducible":reproducible,
            "independent_corroboration":False,
            "confidence":"not_assessed",
            "evidence_sha256":digest(evidence),
            "evidence":evidence,
            "conclusion":"Price/volume candidate reproduced; no independent evidence of misconduct." if reproducible else "Candidate cannot be reproduced reliably from supplied bars.",
        })
    report={"schema_version":"layer3-v1","generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "method":"deterministic single-vendor OHLCV rule reproduction; no institutional attribution",
            "source_status":collection_status or {},
            "candidate_count":len(alerts),"reproduced_count":sum(r["reproducible"] for r in reports),
            "independently_verified_count":0,"records":reports}
    report["report_sha256"]=digest({k:v for k,v in report.items() if k!="report_sha256"})
    return report

def read_csv(path):
    with open(path,newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    root=Path("output")
    status=json.loads((root/"run_status.json").read_text(encoding="utf-8"))
    report=verify(read_csv(root/"bars.csv"),read_csv(root/"candidate_alerts.csv"),status)
    (root/"verification.json").write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    print("Layer 3:",report["candidate_count"],"candidates,",report["reproduced_count"],"reproduced; independent confirmations:",report["independently_verified_count"])

if __name__=="__main__":
    main()
