# Crypto Arbitrage Scanner

Read-only order-book monitor for Bybit, OKX, Kraken, Binance, Coinbase, Bitget, Gate.io, KuCoin and Bitstamp. It compares BTC/USDT, ETH/USDT, SOL/USDT and XRP/USDT using visible order-book depth.

## Exchanges\nThe scanner attempts to connect to all nine venues. Exchanges that are temporarily unavailable, block the server region, or do not list a requested USDT market are skipped; check `/health` for active exchanges and `/latest` for per-market errors.\n\n## Safety
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
- `<EXCHANGE>_TAKER_FEE`: per-exchange overrides, e.g. `BINANCE_TAKER_FEE`, `COINBASE_TAKER_FEE`, `BITGET_TAKER_FEE`, `GATEIO_TAKER_FEE`, `KUCOIN_TAKER_FEE`, `BITSTAMP_TAKER_FEE`, `BYBIT_TAKER_FEE`, `OKX_TAKER_FEE`, `KRAKEN_TAKER_FEE`

The scanner estimates executable VWAP using available order-book levels and ignores opportunities where the displayed depth cannot fill the simulated size. Account-specific fees and available balances are not yet checked.
