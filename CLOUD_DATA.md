# Cloud market data (no local computer, no Tradier)

The workflow `.github/workflows/cloud-market-surveillance.yml` schedules a GitHub-hosted runner every five minutes on weekdays. It collects available one-minute price bars for SPY, QQQ, 10 major stocks, 10-year yield proxy (`^TNX`), Brent futures (`BZ=F`), and VIX (`^VIX`). It screens candidate price/volume anomalies and stores CSVs and a status JSON as GitHub Actions artifacts retained for seven days.

**No brokerage account, API token, or personal computer is required.** The source is an unofficial Yahoo Finance chart endpoint, which may rate-limit, delay, change or block access. Availability and licensing for redistribution must be verified. A scheduled GitHub Actions job is **not** a guaranteed real-time system: schedules may be delayed or skipped; the shortest supported interval is five minutes. The collector fetches available one-minute bars retrospectively each run; it does not stream ticks.

### View results
Open GitHub repository → Actions → Cloud market surveillance → most recent run → Artifacts → download `firewall-market-snapshot-...`. The workflow can also be launched with **Run workflow**.

### Limitations
The collected bars are public market proxies only. They do not establish identity of buyers or sellers, beneficial ownership, dark-pool order flow, institutional risk transfers, or illegal coordination. `^TNX` is a Yahoo yield index representation, not a four-decimal institutional-grade Treasury yield feed. FINRA's public ATS/OTC reports and SEC EDGAR filings can supply *delayed* corroboration; restricted regulatory feeds require authorization.

The governing five-layer architecture remains unchanged in `FINAL_ARCHITECTURE.md`. This is a first operational research data source, not the completed firewall.
