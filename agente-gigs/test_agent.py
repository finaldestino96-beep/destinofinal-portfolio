import unittest

from agent import Opportunity, payout_route, score


class ScoreTests(unittest.TestCase):
    def test_easier_opportunity_scores_higher(self):
        easy = Opportunity("easy", "https://example.com/a", "demo", 100, difficulty=1, kyc="no")
        hard = Opportunity("hard", "https://example.com/b", "demo", 100, difficulty=5, kyc="yes")
        self.assertGreater(score(easy), score(hard))

    def test_payout_requires_configured_matching_network(self):
        config = {"identity": {"wallets": {"solana": "PublicSolAddress"}}}
        self.assertTrue(payout_route(config, "SOL")["accepted"])
        self.assertFalse(payout_route(config, "BTC")["accepted"])


if __name__ == "__main__":
    unittest.main()
