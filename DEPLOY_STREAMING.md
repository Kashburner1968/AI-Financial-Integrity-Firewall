# Cloud deployment: optional Tradier streaming and dashboard

The final five-layer architecture in FINAL_ARCHITECTURE.md is unchanged.

## Important infrastructure distinctions

The existing GitHub Actions workflow is a **five-minute scheduled batch job**. It cannot be converted into an always-on reliable WebSocket daemon; GitHub-hosted runners are ephemeral. For a continuous streaming process and a live public dashboard, provision an external always-on VM or container service with a **persistent disk**, or a managed database.

The previous direction was **no Tradier and no user computer**. The public batch collector remains the default, with no credentials. This optional streaming implementation is provided because the latest deployment directive explicitly requested Tradier. It cannot run without a **user-authorized production Tradier token**. ChatGPT cannot create that token or set cloud secrets by itself.

## Deploy optional streaming stack on cloud VM

1. Provision an always-on Linux VM or container host that supports Docker Compose, persistent volumes, outbound HTTPS/WSS, and an inbound TLS-secured dashboard endpoint. Configure firewall, HTTPS reverse proxy and authentication.
2. Clone this repository and create a **cloud-host environment secret** named `TRADIER_TOKEN`. Never store it in git, send it in chat, or put it in public issue history.
3. On the cloud host, set `TRADIER_TOKEN` securely and start `docker compose up -d --build`. Cloud storage is the Docker named volume `firewall-data`, not a laptop.
4. Access the dashboard at the TLS address routed to container port 8501. Do **not** expose raw Streamlit directly to the public Internet without a reverse proxy, TLS and access controls.
5. View cloud service logs using `docker compose logs -f stream`. Investigate missing/late quotes and feed interruptions.
6. Back up the named volume and externally anchor signed ledger checkpoints; the local SHA-256 chain alone is not tamper-proof against a privileged attacker who can rewrite the entire database.

## Market-data and model constraints

Tradier sends quote/trade/timesale events; this first stream consumes **trade/timesale prices and sizes**. Full bid/ask collection and spread statistics, 50-*trading-day* return correlation backfills, timestamped crude-oil futures trade data, exact S&P 500 breadth, and independent institutional-identity evidence remain distinct integration tasks. Existing code does not claim these fields are present.

`live_engine.py` finalizes completed UTC-minute buckets with no minute-boundary assumption about source delivery, and only evaluates adjacent minutes. `evidence_ledger.py` stores SHA-256 linked alerts in SQLite with explicit verification. `streamlit_app.py` displays recorded bars and **unverified candidate** alerts.

For no-token deployment, use the repository's existing GitHub Actions batch collector; it is not WebSocket streaming and needs no local PC. External cloud infrastructure is still required for continuous data capture and public web hosting.
