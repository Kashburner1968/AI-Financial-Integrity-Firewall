"""Read-only one-minute ingestion and detection; timestamps use UTC minute buckets."""
import asyncio
import json
import math
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from evidence_ledger import Ledger

def utc_minute(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).replace(second=0, microsecond=0).isoformat()

def pearson(a, b):
    if len(a) < 20 or len(a) != len(b):
        return None
    am, bm = sum(a)/len(a), sum(b)/len(b)
    da, db = [x-am for x in a], [y-bm for y in b]
    denom = math.sqrt(sum(x*x for x in da)*sum(y*y for y in db))
    return sum(x*y for x, y in zip(da, db))/denom if denom else None

class Engine:
    def __init__(self, database="data/firewall.db"):
        self.ledger = Ledger(database)
        self.buckets = {}
        self.history = defaultdict(lambda: deque(maxlen=50*390))
        self.latest = {}
        self.last_finalized = None

    def tick(self, symbol, price, size, event_ts=None, source="market_stream"):
        if not math.isfinite(float(price)) or float(price) <= 0:
            return
        epoch = float(event_ts if event_ts is not None else time.time())
        minute = utc_minute(epoch)
        key = (symbol, minute)
        b = self.buckets.get(key)
        if b is None:
            b = {"close": float(price), "volume": 0.0, "source": source}
            self.buckets[key] = b
        b["close"] = float(price)
        if size is not None:
            b["volume"] += max(0., float(size))

    def bar(self, symbol, minute, close, volume, source="public_1min"):
        # Accepts a completed minute; never converts price snapshots into fake trade volume.
        if float(close) <= 0:
            return
        key = (symbol, minute)
        self.buckets[key] = {"close": float(close), "volume": None if volume is None else float(volume), "source": source}

    def finalize(self, now=None):
        current_minute = utc_minute(float(now if now is not None else time.time()))
        ready = sorted((k,v) for k,v in self.buckets.items() if k[1] < current_minute)
        for (symbol, minute), b in ready:
            previous = self.latest.get(symbol)
            self.ledger.bar(symbol, minute, b["close"], b["volume"], b["source"])
            if previous:
                old_minute, old_close, old_volume = previous
                # Only compare adjacent one-minute observations; gaps are not minute signals.
                delta_mins = (datetime.fromisoformat(minute)-datetime.fromisoformat(old_minute)).total_seconds()/60
                if delta_mins == 1 and old_close > 0:
                    change = 100*(b["close"]/old_close-1)
                    ratio = b["volume"]/old_volume if old_volume and b["volume"] is not None else None
                    if change < -0.05 and ratio is not None and ratio >= 1.5:
                        evidence = {"timestamp": minute, "symbol": symbol, "signal": "selling_volume_spike",
                                    "price_change_pct": round(change,5), "volume_ratio": round(ratio,3),
                                    "source": b["source"], "classification": "unverified_candidate"}
                        self.ledger.alert(symbol+"|"+minute+"|selling_volume_spike", evidence)
                    self.history[symbol].append((minute, change))
            self.latest[symbol] = (minute, b["close"], b["volume"])
            del self.buckets[(symbol,minute)]

    def correlation(self, first="SPY", second="BZ=F", window=390):
        # Correlates minute RETURN changes, never raw price levels. 50 days need historical backfill.
        a = dict(self.history[first])
        b = dict(self.history[second])
        keys = sorted(a.keys() & b.keys())[-window:]
        return pearson([a[k] for k in keys], [b[k] for k in keys])

    async def run(self, source):
        """source: async iterator yielding {symbol,price,size,event_ts,source}."""
        queue = asyncio.Queue(maxsize=10000)
        async def consume():
            async for tick in source:
                await queue.put(tick)
        async def process():
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=1)
                    self.tick(**item)
                except asyncio.TimeoutError:
                    pass
                self.finalize()
        await asyncio.gather(consume(), process())
