"""Public read-only dashboard backed by Supabase persistent PostgreSQL."""
import os
import urllib.parse
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI Financial Integrity Firewall",layout="wide")
st.title("AI Financial Integrity Firewall")
st.caption("Public research telemetry. Statistical candidates are not findings of manipulation.")
def setting(name):
    try:
        return st.secrets.get(name) or os.environ.get(name)
    except Exception:
        return os.environ.get(name)
url=(setting("SUPABASE_URL") or "").rstrip("/")
key=setting("SUPABASE_PUBLISHABLE_KEY")
if not url or not key:
    st.info("Waiting for Supabase connection. Configure SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in Streamlit secrets.")
    st.stop()
@st.cache_data(ttl=60)
def fetch(table,order,limit=500):
    endpoint=url+"/rest/v1/"+table
    response=requests.get(endpoint,headers={"apikey":key},
        params={"select":"*","order":order,"limit":limit},timeout=20)
    response.raise_for_status()
    return pd.DataFrame(response.json())
try:
    runs=fetch("collection_runs","collected_utc.desc",10)
    bars=fetch("market_bars","bar_time_utc.desc",1000)
    alerts=fetch("market_alerts","bar_time_utc.desc",200)
except requests.RequestException as exc:
    st.error("Database request failed. Check schema, API keys, RLS policies and connectivity.")
    st.stop()
a,b,c=st.columns(3)
a.metric("Market bars displayed",len(bars))
b.metric("Candidate alerts displayed",len(alerts))
c.metric("Latest collection",runs.iloc[0]["collected_utc"] if not runs.empty else "None")
if not runs.empty:
    st.subheader("Cloud collection status")
    st.dataframe(runs[["collected_utc","bar_count","alert_count","status"]],use_container_width=True)
if not bars.empty:
    symbols=sorted(bars.symbol.unique())
    selected=st.multiselect("Market symbols",symbols,default=[x for x in ("SPY","QQQ") if x in symbols])
    for symbol in selected:
        df=bars[bars.symbol==symbol].sort_values("bar_time_utc").copy()
        df["bar_time_utc"]=pd.to_datetime(df["bar_time_utc"],utc=True)
        st.subheader(symbol)
        st.line_chart(df.set_index("bar_time_utc")["close"])
st.subheader("Unverified anomaly candidates")
if alerts.empty:
    st.info("No candidate alerts available.")
else:
    st.dataframe(alerts,use_container_width=True)
st.caption("Data may be delayed or incomplete. This dashboard does not establish institutional identities, dark-pool counterparties, or verified manipulation.")
