"""Tests for explicit tie/rounding policies (Gaps 17, 18, 19)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fra_pipeline" / "scripts"))
import allocation  # noqa: E402


class TestDistrictTiePolicy(unittest.TestCase):
    def test_clear_winners(self):
        self.assertEqual(allocation.decide_district_winner(100, 90), "DEM")
        self.assertEqual(allocation.decide_district_winner(90, 100), "REP")

    def test_tie_default_is_republican_historical(self):
        # Gap 19: historical undocumented else-branch awarded ties to REP.
        self.assertEqual(allocation.decide_district_winner(50, 50), "REP")

    def test_tie_policies(self):
        self.assertEqual(allocation.decide_district_winner(5, 5, "democratic"), "DEM")
        self.assertIsNone(allocation.decide_district_winner(5, 5, "no_seat"))
        with self.assertRaises(ValueError):
            allocation.decide_district_winner(5, 5, "error")
        with self.assertRaises(ValueError):
            allocation.decide_district_winner(5, 5, "bogus")


class TestTwoPartyAllocation(unittest.TestCase):
    def test_sum_invariant(self):
        for share in (0.0, 0.1, 0.42, 0.5, 0.5001, 0.9, 1.0):
            for seats in (4, 5):
                d, r = allocation.allocate_two_party_seats(share, seats)
                self.assertEqual(d + r, seats)
                self.assertGreaterEqual(d, 0)
                self.assertGreaterEqual(r, 0)

    def test_round_half_even_matches_historical(self):
        # Gap 18: default must reproduce Python round() banker's rounding.
        # 0.5 * 5 = 2.5 -> banker's rounds to 2 (even).
        self.assertEqual(allocation.allocate_two_party_seats(0.5, 5), (2, 3))
        # 0.7 * 5 = 3.5 -> banker's rounds to 4 (even).
        self.assertEqual(allocation.allocate_two_party_seats(0.7, 5), (4, 1))
        # 0.5 * 4 = 2.0 -> 2.
        self.assertEqual(allocation.allocate_two_party_seats(0.5, 4), (2, 2))

    def test_round_half_up_differs_at_boundary(self):
        # 2.5 rounds UP to 3 under half-up (vs 2 under half-even).
        self.assertEqual(allocation.allocate_two_party_seats(0.5, 5, "round_half_up"), (3, 2))

    def test_largest_remainder(self):
        # 0.5*5 = 2.5, remainder 0.5 -> DEM takes the seat (deterministic tie).
        self.assertEqual(allocation.allocate_two_party_seats(0.5, 5, "largest_remainder"), (3, 2))
        # 0.44*5 = 2.2, remainder 0.2 -> DEM does not take it -> 2 seats.
        self.assertEqual(allocation.allocate_two_party_seats(0.44, 5, "largest_remainder"), (2, 3))

    def test_bad_method_raises(self):
        with self.assertRaises(ValueError):
            allocation.allocate_two_party_seats(0.5, 5, "dhondt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
