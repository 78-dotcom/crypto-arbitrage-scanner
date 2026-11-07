import asyncio
import logging
import os
import time
from aiohttp import web
import ccxt.async_support as ccxt

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("scanner")

SYMBOLS = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT").split(",")
EXCHANGES = ["bybit", "okx", "kraken"]
TRADE_QUOTE = float(os.getenv("TRADE_QUOTE_USDT", "100"))
MIN_NET_PERCENT = float(os.getenv("MIN_NET_PERCENT", "0.5"))
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "5"))
DEFAULT_FEE = float(os.getenv("TAKER_FEE", "0.001"))
FEES = {name: float(os.getenv(f"{name.upper()}_TAKER_FEE", str(DEFAULT_FEE))) for name in EXCHANGES}

state = {"status": "starting", "updated_at": None, "opportunities": [], "errors": []}
clients = {}

def buy_with_quote(asks, quote_budget):
    remaining = quote_budget
    base = cost = 0.0
    for price, amount in asks:
        take_quote = min(remaining, price * amount)
        take_base = take_quote / price
        base += take_base
        cost += take_quote
        remaining -= take_quote
        if remaining <= 1e-9:
            break
    return (base, cost) if remaining <= 1e-6 and base > 0 else (0.0, 0.0)

def sell_base(bids, base_amount):
    remaining = base_amount
    proceeds = 0.0
    for price, amount in bids:
        take = min(remaining, amount)
        proceeds += take * price
        remaining -= take
        if remaining <= 1e-12:
            break
    return proceeds if remaining <= 1e-8 else 0.0

async def scan_once():
    books = {}
    errors = []
    for name, exchange in clients.items():
        for symbol in SYMBOLS:
            try:
                market_symbol = symbol if symbol in exchange.markets else None
                if not market_symbol:
                    # Kraken commonly exposes XBT rather than BTC in market ids;
                    # CCXT's unified symbol is normally still BTC/USDT.
                    continue
                book = await exchange.fetch_order_book(market_symbol, limit=50)
                if book.get("asks") and book.get("bids"):
                    books[(name, symbol)] = book
            except Exception as exc:
                errors.append(f"{name} {symbol}: {type(exc).__name__}: {exc}")
    opportunities = []
    for symbol in SYMBOLS:
        venues = [(name, books[(name, symbol)]) for name in EXCHANGES if (name, symbol) in books]
        for buy_name, buy_book in venues:
            base_amount, buy_cost = buy_with_quote(buy_book["asks"], TRADE_QUOTE)
            if not base_amount:
                continue
            for sell_name, sell_book in venues:
                if buy_name == sell_name:
                    continue
                sell_value = sell_base(sell_book["bids"], base_amount)
                if not sell_value:
                    continue
                buy_fee = buy_cost * FEES[buy_name]
                sell_fee = sell_value * FEES[sell_name]
                net = sell_value - sell_fee - buy_cost - buy_fee
                net_pct = net / (buy_cost + buy_fee) * 100
                if net_pct >= MIN_NET_PERCENT:
                    opportunities.append({
                        "symbol": symbol, "buy_exchange": buy_name,
                        "sell_exchange": sell_name, "base_amount": round(base_amount, 10),
                        "buy_cost_usdt": round(buy_cost, 6),
                        "sell_value_usdt": round(sell_value, 6),
                        "estimated_fees_usdt": round(buy_fee + sell_fee, 6),
                        "net_profit_usdt": round(net, 6),
                        "net_percent": round(net_pct, 4),
                        "timestamp": int(time.time()),
                    })
    opportunities.sort(key=lambda x: x["net_percent"], reverse=True)
    state.update(status="ok", updated_at=int(time.time()),
                 opportunities=opportunities, errors=errors[-20:])
    for item in opportunities:
        log.info("OPPORTUNITY %s", item)

async def scan_loop(app):
    while True:
        try:
            await scan_once()
        except Exception:
            log.exception("Scan cycle failed")
            state["status"] = "degraded"
        await asyncio.sleep(POLL_SECONDS)

async def health(request):
    return web.json_response({"service": "crypto-arbitrage-scanner", "status": state["status"],
                              "updated_at": state["updated_at"]})

async def latest(request):
    return web.json_response(state)

async def on_startup(app):
    for name in EXCHANGES:
        cls = getattr(ccxt, name)
        clients[name] = cls({"enableRateLimit": True, "timeout": 15000})
        await clients[name].load_markets()
    app["scanner_task"] = asyncio.create_task(scan_loop(app))

async def on_cleanup(app):
    task = app.get("scanner_task")
    if task:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    await asyncio.gather(*(client.close() for client in clients.values()), return_exceptions=True)

app = web.Application()
app.router.add_get("/", health)
app.router.add_get("/health", health)
app.router.add_get("/latest", latest)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
