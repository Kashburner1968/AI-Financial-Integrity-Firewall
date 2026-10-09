# Data activation guide

The governing architecture is `FINAL_ARCHITECTURE.md`; this guide does not amend it.

## Tradier: live collection on your own machine

A **production** Tradier token is required for production market data. Keep it on your computer and never commit it, paste it in a GitHub issue, or upload it into this public repository. Tradier personal tokens can authorize account actions even though **our collector only calls the read-only markets/timesales endpoint**.

Windows PowerShell:

```powershell
$env:TRADIER_TOKEN = "YOUR_TOKEN_HERE"
python tradier_collector.py --once
python tradier_collector.py --interval 60
```

In a second terminal:

```powershell
python tradier_detector.py --input data/tradier_1min.csv
```

Output: `data/tradier_1min.csv` and `data/candidate_alerts.csv`. These files stay local. If markets are closed, no new bars may be available. Tradier's published history limits apply. The collector catches errors per symbol and prints them; no missing values are fabricated.

## Additional official sources

- FINRA OTC transparency: https://developer.finra.org/docs — published ATS and non-ATS aggregated trade data; not a real-time participant-level tape. Production endpoints may require FINRA API registration/authorization.
- SEC public filings: https://data.sec.gov/ — institutional filings and issuer disclosures. Form 13F is delayed and does not reveal intraday counterparties.
- CNBC: `cnbc_collector.py` — secondary quote snapshots, not guaranteed one-minute bars.
- Tradier: https://docs.tradier.com/reference/brokerage-api-markets-get-timesales — minute bars and ticks subject to account entitlements and retention.

## Still required for full firewall

Authorized order-level audit trails, beneficial-ownership identification, market-wide order-book liquidity, accurate constituent breadth, and regulatory access to nonpublic records. The public prototype must not imply these are available.

## Deployment

GitHub stores source code; it does not run a persistent 60-second process automatically. Run on a trusted always-on computer or licensed hosted machine. Before redistributing market data or publishing a public dashboard, verify vendor permissions and exchange licensing.
