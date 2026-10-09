import unittest
from tradier_collector import normalize
from tradier_detector import analyze

class PipelineTests(unittest.TestCase):
    def test_normalization(self):
        data=[{"time":"2026-10-09T09:30:00","open":100,"high":101,"low":99,"close":100,"volume":10}]
        self.assertEqual(normalize("SPY",data,"now")[0]["symbol"],"SPY")
    def test_signal(self):
        rows=[{"symbol":"SPY","time":"a","close":"100","volume":"100"},
              {"symbol":"SPY","time":"b","close":"99.8","volume":"200"}]
        self.assertEqual(analyze(rows)[0]["classification"],"unverified_candidate")

if __name__=="__main__":
    unittest.main()
