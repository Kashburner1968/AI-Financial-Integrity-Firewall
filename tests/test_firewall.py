import unittest
from firewall import screen

class ScreenTests(unittest.TestCase):
    def test_candidate_signals(self):
        rows = [
            {"timestamp":"t1","spy":100.0,"breadth_pct":60.0,"volume":100.0,"liquidity_proxy":100.0},
            {"timestamp":"t2","spy":100.1,"breadth_pct":55.0,"volume":110.0,"liquidity_proxy":90.0},
            {"timestamp":"t3","spy":99.9,"breadth_pct":54.0,"volume":200.0,"liquidity_proxy":30.0}
        ]
        signals = {a["candidate_signal"] for a in screen(rows)}
        self.assertEqual(signals, {"price_up_breadth_down","selling_volume_spike","liquidity_proxy_decline"})

if __name__ == "__main__":
    unittest.main()
