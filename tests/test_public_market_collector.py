import unittest
from public_market_collector import detect

class CloudDetectionTests(unittest.TestCase):
    def test_selling_volume_candidate(self):
        bars = [
            {"retrieved_utc":"now","symbol":"SPY","bar_time_utc":"t1","close":100.0,"volume":100},
            {"retrieved_utc":"now","symbol":"SPY","bar_time_utc":"t2","close":99.8,"volume":200},
        ]
        self.assertEqual(detect(bars)[0]["signal"], "selling_volume_spike")
    def test_missing_volume_not_flagged(self):
        bars = [
            {"close":100.0,"volume":None},
            {"close":99.8,"volume":200},
        ]
        self.assertEqual(detect(bars), [])

if __name__ == "__main__":
    unittest.main()
