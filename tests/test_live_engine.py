import os
import tempfile
import unittest
from evidence_ledger import Ledger
from live_engine import Engine, pearson

class EngineTests(unittest.TestCase):
    def test_append_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,"db.sqlite")
            log=Ledger(path)
            log.alert("first",{"type":"test"})
            log.alert("second",{"type":"test2"})
            self.assertTrue(log.verify())
            with log._db() as db:
                db.execute("UPDATE alerts SET payload=? WHERE event_id=?", ('{}',"first"))
            self.assertFalse(log.verify())
    def test_finalized_bars(self):
        with tempfile.TemporaryDirectory() as tmp:
            eng=Engine(os.path.join(tmp,"db.sqlite"))
            eng.tick("SPY",100,100,event_ts=60)
            eng.tick("SPY",99.8,300,event_ts=120)
            eng.finalize(now=180)
            with eng.ledger._db() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM alerts").fetchone()[0],1)
    def test_short_correlation_unknown(self):
        self.assertIsNone(pearson([1,2],[2,3]))

if __name__=="__main__":
    unittest.main()
