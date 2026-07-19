"""Tests for shared atomic-write helpers (Gaps 29 & 30)."""
import json
import os
import sys
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fra_pipeline" / "scripts"))
import io_utils  # noqa: E402
import tempfile


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_write_json_roundtrip(self):
        p = self.dir / "a.json"
        io_utils.atomic_write_json(p, {"x": 1, "y": [1, 2, 3]})
        self.assertEqual(json.loads(p.read_text()), {"x": 1, "y": [1, 2, 3]})

    def test_no_tmp_remnants(self):
        p = self.dir / "b.json"
        io_utils.atomic_write_json(p, {"ok": True})
        remnants = [f for f in os.listdir(self.dir) if f.endswith(".tmp")]
        self.assertEqual(remnants, [], f"leftover temp files: {remnants}")

    def test_unique_temp_paths_under_concurrency(self):
        """Gap 29: concurrent writers to the SAME target must not share a temp path.

        We patch os.replace to capture each temp path before it is renamed away.
        """
        seen = []
        real_replace = os.replace
        target = self.dir / "shared.json"

        def spy_replace(src, dst):
            seen.append(str(src))
            return real_replace(src, dst)

        io_utils.os.replace = spy_replace
        try:
            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(lambda i: io_utils.atomic_write_json(target, {"i": i}), range(64)))
        finally:
            io_utils.os.replace = real_replace

        self.assertEqual(len(seen), 64)
        self.assertEqual(len(set(seen)), 64, "temp paths collided across concurrent writers")
        self.assertTrue(target.exists())
        json.loads(target.read_text())  # final file is valid JSON, never partial

    def test_failure_leaves_no_partial_target(self):
        p = self.dir / "c.json"
        p.write_text('{"old": true}')

        class Boom:
            def __repr__(self):
                raise RuntimeError("cannot serialize")

        with self.assertRaises(TypeError):
            io_utils.atomic_write_json(p, {"bad": {1, 2, 3}})  # sets aren't JSON serializable
        # original untouched, no tmp remnants
        self.assertEqual(json.loads(p.read_text()), {"old": True})
        self.assertEqual([f for f in os.listdir(self.dir) if f.endswith(".tmp")], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
