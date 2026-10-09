"""Self-contained HTML summary delivered as a workflow artifact, not a deployed website."""
import html
import json
import sqlite3
from pathlib import Path
from evidence_ledger import Ledger

def main():
    root=Path("output")
    status_file=root/"run_status.json"
    status=json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
    db=root/"firewall.db"
    if not db.exists():
        raise SystemExit("No ledger found")
    verified=Ledger(str(db)).verify()
    with sqlite3.connect(db) as conn:
        count=conn.execute("SELECT COUNT(*) FROM bars").fetchone()[0]
        alerts=conn.execute("SELECT created_at,payload,hash FROM alerts ORDER BY seq DESC LIMIT 100").fetchall()
    rows=[]
    for created,payload,digest in alerts:
        data=json.loads(payload)
        rows.append("<tr>"+"".join("<td>"+html.escape(str(x))+"</td>" for x in
            (created,data.get("timestamp"),data.get("symbol"),data.get("signal"),data.get("classification"),digest[:16]))+"</tr>")
    body=f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Financial Integrity Firewall — Cloud Report</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 18px;color:#18212b}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}.meta{{color:#555}}.warn{{background:#fff4db;padding:16px}}</style></head>
<body><h1>Financial Integrity Firewall</h1><p class="warn">Research telemetry only. Flags are unverified statistical candidates and do not establish market manipulation or institutional ownership.</p>
<p>Snapshot retrieved: {html.escape(str(status.get('retrieved_utc','unknown')))}</p>
<p>Bars: {count} · Candidate records: {len(alerts)} · Hash-chain integrity: {'PASS' if verified else 'FAIL'}</p>
<p class="meta">This report represents one cloud batch, not a continuous public stream. Data may be stale, delayed, missing or vendor-restricted.</p>
<h2>Candidate alerts</h2><table><tr><th>Logged</th><th>Minute (UTC)</th><th>Symbol</th><th>Signal</th><th>Status</th><th>Hash prefix</th></tr>{''.join(rows)}</table></body></html>"""
    (root/"index.html").write_text(body,encoding="utf-8")
    if not verified:
        raise SystemExit("Ledger verification failed")
if __name__=="__main__":
    main()
