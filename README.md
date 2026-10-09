# AI Financial Integrity Firewall

Independent, open-source research prototype for financial market surveillance.

**Governing architecture:** [FINAL_ARCHITECTURE.md](FINAL_ARCHITECTURE.md). The project implements this user-authored architecture without editing it.

## First milestone

- Layer 1: accept minute-level market records from CSV. No claims of access to restricted order-level, beneficial-ownership, or dark-pool identities.
- Layer 2: screen for potential price/breadth divergence, rising volume with falling prices, and falling prices with weakened liquidity proxies.
- Output candidate anomalies, *not* findings of wrongdoing.

## Run

```bash
python firewall.py --input example_market_data.csv --output alerts.csv
python -m unittest discover -s tests
```

This code does not place trades or perform market interventions. Later layers require additional data, validation and authorization.
