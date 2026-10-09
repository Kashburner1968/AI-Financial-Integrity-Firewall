import unittest
from layer4_transparency import summarize

class TransparencyTests(unittest.TestCase):
    def test_counts_and_missing_coverage(self):
        report={"records":[{"status":"reproduced_unverified"},{"status":"not_reproduced"}],"report_sha256":"abc"}
        status={"retrieved_utc":"2026-10-09T14:00:00+00:00","symbols_requested":["SPY","QQQ"],"symbols_with_data":["SPY"],"errors":[{"symbol":"QQQ"}]}
        out=summarize(report,status)
        self.assertEqual(out["coverage"]["missing_symbols"],["QQQ"])
        self.assertEqual(out["indicators"]["reproduced_price_volume_events"],1)
        self.assertEqual(out["indicators"]["independently_corroborated_events"],0)
        self.assertEqual(out["status"],"RESEARCH_ONLY_UNCORROBORATED")
    def test_empty_report(self):
        out=summarize({"records":[]},{})
        self.assertEqual(out["indicators"]["candidate_events"],0)

if __name__=="__main__":unittest.main()
