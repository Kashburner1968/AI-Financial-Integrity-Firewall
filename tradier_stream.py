"""Optional Tradier WebSocket market stream. Cloud secrets only; no order endpoints."""
import asyncio
import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import websockets

SYMBOLS = ["SPY","QQQ","NVDA","AAPL","MSFT","AMZN","GOOGL","META","AVGO","TSLA","GOOG"]
SESSION_URL = "https://api.tradier.com/v1/markets/events/session"
STREAM_URL = "wss://ws.tradier.com/v1/markets/events"

def session():
    token = os.environ.get("TRADIER_TOKEN")
    if not token:
        raise RuntimeError("TRADIER_TOKEN must be configured as a cloud secret; do not commit it.")
    request = Request(SESSION_URL, data=b"", method="POST", headers={
        "Authorization": "Bearer " + token, "Accept": "application/json"})
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    result = payload.get("stream") or {}
    if not result.get("sessionid"):
        raise RuntimeError("Market streaming session was not returned")
    return result["sessionid"]

def event_time(msg):
    raw = msg.get("date") or msg.get("biddate") or msg.get("askdate")
    try:
        epoch = float(raw)
        return epoch/1000 if epoch > 1e11 else epoch
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).timestamp()

async def events():
    backoff = 1
    while True:
        try:
            sid = await asyncio.to_thread(session)
            async with websockets.connect(STREAM_URL, ping_interval=20, compression=None) as ws:
                await ws.send(json.dumps({"symbols": SYMBOLS, "sessionid":sid,
                                          "filter":["trade","quote","timesale"], "linebreak":True}))
                backoff=1
                async for data in ws:
                    for line in data.splitlines():
                        try:
                            msg=json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if msg.get("type") not in ("trade","timesale"):
                            continue
                        price = msg.get("price") or msg.get("last")
                        if price is None or not msg.get("symbol"):
                            continue
                        yield {"symbol":msg["symbol"],"price":float(price),
                               "size":float(msg.get("size") or 0), "event_ts":event_time(msg),
                               "source":"Tradier market WebSocket"}
        except (OSError, ValueError, RuntimeError, websockets.exceptions.WebSocketException) as exc:
            print("Tradier stream reconnect:",type(exc).__name__,str(exc),flush=True)
            await asyncio.sleep(backoff)
            backoff=min(backoff*2,60)
