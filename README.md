# Crypto Arbitrage Scanner

Read-only order-book monitor for Bybit, OKX and Kraken. It compares BTC/USDT, ETH/USDT, SOL/USDT and XRP/USDT using visible order-book depth.

## Safety
- Public market data only. No API keys, private endpoints, orders, withdrawals or transfers.
- Opportunities are estimates, not guaranteed fills.
- Default taker fee is 0.10% per side. Configure exchange-specific fees to match your account tier.
- Transfer costs, funding, taxes, withdrawal delays and inventory rebalancing are not included.
- Alerts are shown only when estimated net return meets the configured threshold.

## Run
```bash
pip install -r requirements.txt
python scanner.py
``

Endpoints: `/health` and `/latest`.

## Environment
- `SYMBOLS`: comma-separated unified symbols (default BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT)
- `TRADE_QUOTE_USDT`: simulated quote amount per opportunity (default 100)
- `MIN_NET_PERCENT`: minimum estimated net return percentage (default 0.5)
- `POLL_SECONDS`: scan interval (default 5)
- `TAKER_FEE`: fallback taker fee fraction (default 0.001)
- `BYBIT_TAKER_FEE`, `OKX_TAKER_FEE`, `KRAKEN_TAKER_FEE`: per-exchange overrides

The scanner estimates executable VWAP using available order-book levels and ignores opportunities where the displayed depth cannot fill the simulated size. Account-specific fees and available balances are not yet checked.
