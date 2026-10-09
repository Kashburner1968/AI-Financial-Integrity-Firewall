"""Read-only market-integrity research dashboard. Run: streamlit run streamlit_app.py"""
import json
import os
import sqlite3
import pandas as pd
import streamlit as st
from evidence_ledger import Ledger

DB=os.getenv("FIREWALL_DB","data/firewall.db")
st.set_page_config(page_title="Financial Integrity Firewall", layout="wide")
st.title("Financial Integrity Firewall — research telemetry")
st.caption("One-minute market anomalies are unverified candidates, NOT established institutional wrongdoing.")
if not os.path.exists(DB):
    st.warning("Waiting for collector database. Nothing is live yet.")
    st.stop()
try:
    ledger=Ledger(DB)
    st.metric("Evidence chain", "VALID" if ledger.verify() else "FAILED — INVESTIGATE")
    with sqlite3.connect(DB) as conn:
        bars=pd.read_sql_query("SELECT symbol,minute,close,volume,source FROM bars ORDER BY minute DESC LIMIT 20000",conn)
        alerts=pd.read_sql_query("SELECT seq,created_at,payload,hash FROM alerts ORDER BY seq DESC LIMIT 200",conn)
    st.metric("Candidate alerts in ledger",len(alerts))
    if not bars.empty:
        symbols=sorted(bars.symbol.unique())
        chosen=st.multiselect("Market symbols",symbols,default=[s for s in ("SPY","QQQ") if s in symbols])
        for symbol in chosen:
            subset=bars[bars.symbol==symbol].sort_values("minute").set_index("minute")
            st.subheader(symbol)
            st.line_chart(subset["close"])
    if not alerts.empty:
        formatted=[]
        for row in alerts.to_dict("records"):
            formatted.append({**{"sequence":row["seq"],"logged_at":row["created_at"],"hash":row["hash"]},
                              **json.loads(row["payload"])})
        st.subheader("Unverified candidate alerts")
        st.dataframe(formatted,use_container_width=True)
    else:
        st.info("No candidate alerts recorded.")
    st.caption("Public one-minute bars do not identify institutional counterparties, dark-pool traders or collusion. "
               "Broad-market equal-weight breadth and verified institutional distribution require additional feeds and review.")
except (sqlite3.Error, ValueError) as exc:
    st.error(f"Database unavailable or verification problem: {exc}")
