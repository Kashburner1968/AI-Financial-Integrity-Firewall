"""Entry point for optional production Tradier cloud stream."""
import asyncio
import os
from live_engine import Engine
from tradier_stream import events
if __name__=="__main__":
    asyncio.run(Engine(os.environ.get("FIREWALL_DB","data/firewall.db")).run(events()))
