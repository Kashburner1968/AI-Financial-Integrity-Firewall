# Persistent cloud storage + public dashboard

No Tradier, local computer, or brokerage API token required.

## 1. Create Supabase project (account owner action)

Visit https://supabase.com/dashboard and create a PostgreSQL project. In its SQL Editor, execute `supabase_schema.sql`. The schema enables anonymous **read only** telemetry and prohibits anonymous writes. In the project's Connect / API keys view, find the Project URL, a **publishable** key, and a **secret** key. Never put the secret key in source code or Streamlit secrets.

## 2. Configure GitHub Actions cloud ingestion

GitHub repository → Settings → Secrets and variables → Actions → New repository secret:

- `SUPABASE_URL`: Supabase project HTTPS URL
- `SUPABASE_SECRET_KEY`: Supabase secret API key (server-side only)

Once these are set, the existing `cloud-market-surveillance.yml` runs every five minutes on weekdays and uploads each successful collection into PostgreSQL. The cloud job still produces local artifacts as a fallback. Check the workflow logs to confirm ingestion.

## 3. Deploy public dashboard

Visit https://share.streamlit.io and select Create app → Existing GitHub repository.
Repository: `Kashburner1968/AI-Financial-Integrity-Firewall`
Branch: `main`
Entry point: `streamlit_cloud.py`
In Advanced settings → Secrets enter:

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_YOUR_KEY"
```

Do **not** put SUPABASE_SECRET_KEY in Streamlit. Deploy and copy the assigned public streamlit.app URL.

## 4. Validation

Check Supabase Table Editor for `market_bars`, `market_alerts`, `collection_runs`. Trigger the GitHub workflow manually and verify that the latest run appears in Streamlit. No values are fabricated for missing market feeds.

## Operational limits

GitHub scheduled runs are not continuous and may be delayed. Public Yahoo chart data is unofficial, possibly delayed/blocked, and may have licensing restrictions. Public market bars do not reveal institutional identities. The SQLite per-run hash ledger remains a separate artifact; the cloud database stores public alert metadata, not a globally chained, externally anchored evidence history. Do not describe it as tamper-proof. The free plans have quotas, possible pauses, and are not an SLA-backed regulatory production environment.
