import unittest
from cnbc_collector import make_rows

class CnbcCollectorTests(unittest.TestCase):
    def test_missing_quotes_are_explicit(self):
        quotes = [{"symbol":"SPY","last":"675.23","volume":"12345","last_time":"12:00 PM EDT"}]
        rows = make_rows(quotes, ["SPY", "US10Y"], "2026-10-09T16:00:00+00:00")
        self.assertEqual(rows[0]["status"], "ok")
        self.assertEqual(rows[1]["status"], "missing")
        self.assertEqual(rows[1]["last"], "")
        self.assertEqual(rows[0]["collected_at_utc"], "2026-10-09T16:00:00+00:00")

if __name__ == "__main__":
    unittest.main()
