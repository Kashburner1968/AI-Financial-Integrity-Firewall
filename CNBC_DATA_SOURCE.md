# CNBC quote collection

Run from the repository root:

```bash
python cnbc_collector.py --once
python cnbc_collector.py --interval 60
python -m unittest discover -s tests
```

The default file is `data/cnbc_snapshots.csv`. Each row is a **quote snapshot**, not an exchange-confirmed one-minute candle. Symbols include SPY, QQQ, major technology names, US10Y, VIX and a Brent futures proxy (`@LCO.1`). Verify symbols and quote timestamps at runtime. Brent futures are not the same as a particular Brent spot benchmark.

**Important:** CNBC's quote service is undocumented and unofficial. Access, field names, freshness and licensing can change without notice. The service may block automated requests. The collector records missing values rather than silently substituting data. No guarantees of real-time exchange-grade quotes. Check CNBC's terms and secure permission or a licensed market-data feed before public redistribution or sustained production use.

CNBC quotes do **not** establish beneficial ownership, dark-pool participant identities, institutional intent, ETF creations/redemptions, S&P 500 breadth, or order-book liquidity. Do not infer those from snapshots. The existing `firewall.py` requires independently supplied breadth and liquidity columns; these are intentionally **not** invented by this collector.

The collector is read-only and does not trade.
