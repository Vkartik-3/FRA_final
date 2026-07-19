"""Test one-row-per-plan FRA aggregation (Gap 2).

Verifies that 3-super-district-rows-per-plan source files aggregate to exactly
one row per plan with unique plan_id and conserved seat/vote totals.
"""
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fra_pipeline" / "scripts"))
import pandas as pd  # noqa: E402
import analyze_fra_ensemble as afe  # noqa: E402


def _write_plan(fra_dir: Path, plan_id: int, rows):
    df = pd.DataFrame(rows, columns=[
        "superdistrict_id", "total_seats", "dem_votes", "rep_votes",
        "dem_seats", "rep_seats", "dem_share", "population"])
    df.to_csv(fra_dir / f"fra_results_{plan_id}.csv", index=False)


class TestFraAggregation(unittest.TestCase):
    def setUp(self):
        self.fra = Path(tempfile.mkdtemp())
        # plan 1: seats 2+3+2 dem = 7, total 14
        _write_plan(self.fra, 1, [
            (0, 5, 856342, 1138596, 2, 3, 0.429, 3801498),
            (1, 5, 1072054, 895542, 3, 2, 0.545, 3819142),
            (2, 4, 785213, 862803, 2, 2, 0.476, 3058620),
        ])
        # sparse id above 1000 with a different split (5 dem)
        _write_plan(self.fra, 1500, [
            (0, 5, 800000, 1200000, 2, 3, 0.40, 3800000),
            (1, 5, 900000, 1100000, 2, 3, 0.45, 3800000),
            (2, 4, 700000, 900000, 1, 3, 0.44, 3000000),
        ])

    def test_one_row_per_plan(self):
        df = afe.load_all_fra_results(self.fra)
        self.assertEqual(len(df), 2)
        self.assertEqual(df["plan_id"].nunique(), 2)
        self.assertListEqual(sorted(df["plan_id"]), [1, 1500])

    def test_totals_conserved(self):
        df = afe.load_all_fra_results(self.fra).set_index("plan_id")
        self.assertEqual(df.loc[1, "total_dem_seats"], 7)
        self.assertEqual(df.loc[1, "total_rep_seats"], 7)
        self.assertEqual(df.loc[1500, "total_dem_seats"], 5)
        self.assertEqual(df.loc[1500, "total_rep_seats"], 9)
        # each plan's seats sum to 14
        self.assertTrue(((df["total_dem_seats"] + df["total_rep_seats"]) == 14).all())

    def test_required_schema_columns(self):
        df = afe.load_all_fra_results(self.fra)
        required = {"plan_id", "total_dem_seats", "total_rep_seats", "dem_vote_share",
                    "rep_vote_share", "seat_share_dem", "proportionality_gap"}
        self.assertTrue(required.issubset(df.columns))


if __name__ == "__main__":
    unittest.main(verbosity=2)
