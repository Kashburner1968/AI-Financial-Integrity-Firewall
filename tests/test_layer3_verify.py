import unittest
from datetime import datetime, timedelta, timezone
from layer3_verify import verify, digest

class Layer3Tests(unittest.TestCase):
    def bars(self):
        start=datetime(2026,10,9,14,0,tzinfo=timezone.utc)
        out=[]
        for i in range(15):
            out.append({"symbol":"SPY","bar_time_utc":(start+timedelta(minutes=i)).isoformat(),
                "close":str(100 if i<14 else 99.9),
                "volume":str(100 if i<14 else 200)})
        return out
    def alert(self,bars):
        return {"symbol":"SPY","bar_time_utc":bars[-1]["bar_time_utc"],
            "signal":"selling_volume_spike","change_pct":"-0.1","volume_ratio":"2.0"}
    def test_reproducible_and_not_independently_verified(self):
        bars=self.bars()
        report=verify(bars,[self.alert(bars)])
        self.assertEqual(report["reproduced_count"],1)
        self.assertEqual(report["independently_verified_count"],0)
        self.assertEqual(report["records"][0]["status"],"reproduced_unverified")
        self.assertEqual(len(report["records"][0]["evidence_sha256"]),64)
        self.assertTrue(report["records"][0]["evidence"]["checks"]["above_recent_volume_median"])
    def test_rejects_false_candidate(self):
        bars=self.bars()
        alert=self.alert(bars)
        alert["change_pct"]="1.0"
        self.assertEqual(verify(bars,[alert])["reproduced_count"],0)
    def test_missing_previous_bar(self):
        bars=self.bars()[-1:]
        report=verify(bars,[self.alert(bars)])
        self.assertEqual(report["reproduced_count"],0)
    def test_hash_determinism(self):
        self.assertEqual(digest({"a":1,"b":2}),digest({"b":2,"a":1}))
    def test_no_alerts(self):
        report=verify(self.bars(),[])
        self.assertEqual(report["candidate_count"],0)
        self.assertEqual(report["reproduced_count"],0)

if __name__=="__main__":
    unittest.main()
