"""Layer 4 public transparency: conservative aggregate indicators from Layer 3."""
from collections import Counter
from datetime import datetime, timezone

def summarize(report, status):
    records=report.get("records",[])
    counts=Counter(r.get("status","unknown") for r in records)
    available=status.get("symbols_with_data",[])
    requested=status.get("symbols_requested",[])
    return {
        "version":"layer4-v1",
        "as_of_utc":status.get("retrieved_utc"),
        "scope":"Public one-minute price/volume data; one unofficial vendor",
        "coverage":{"symbols_requested":len(requested),"symbols_with_data":len(available),
                    "missing_symbols":sorted(set(requested)-set(available)),
                    "source_errors":len(status.get("errors",[]))},
        "indicators":{"candidate_events":len(records),
                      "reproduced_price_volume_events":counts["reproduced_unverified"],
                      "not_reproduced_events":counts["not_reproduced"],
                      "independently_corroborated_events":0},
        "status":"RESEARCH_ONLY_UNCORROBORATED",
        "interpretation":"Counts describe rule-triggering price/volume events, not market manipulation, collusion, institutional identities, or systemic-risk probabilities.",
        "limitations":[
            "Single-source price bars cannot independently corroborate anomalies.",
            "A high event count is not a calibrated systemic-risk score.",
            "Missing or incomplete candles, market hours, news and rebalancing may affect signals.",
            "No transaction-level, beneficial-ownership or dark-pool identification.",
            "This dashboard has no trade-execution or regulatory-enforcement authority."
        ],
        "verification_report_sha256":report.get("report_sha256")
    }
