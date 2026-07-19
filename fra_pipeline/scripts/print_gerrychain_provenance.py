#!/usr/bin/env python3
"""
GerryChain Provenance Reporter

Prints the exact GerryChain version, import path, and whether the working tree
has uncommitted modifications.  Run this before any experiment to create a
stable provenance snapshot.

Usage:
    python scripts/print_gerrychain_provenance.py
    python scripts/print_gerrychain_provenance.py --save  # also writes JSON
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def get_dirty_status(package_dir: Path) -> str:
    """Return 'dirty', 'clean', or 'unknown' for the git working tree at package_dir."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(package_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return "unknown (git error)"
        return "dirty" if result.stdout.strip() else "clean"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown (git not available)"


def main():
    parser = argparse.ArgumentParser(description="Print GerryChain provenance information")
    parser.add_argument(
        "--save", action="store_true",
        help="Write provenance JSON to outputs/analysis/gerrychain_provenance.json"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("GERRYCHAIN PROVENANCE REPORT")
    print("=" * 60)

    # ── Import GerryChain ─────────────────────────────────────────────────────
    try:
        import gerrychain
    except ImportError as e:
        print(f"\n❌ Cannot import gerrychain: {e}")
        print("   Activate your virtual environment and ensure GerryChain is installed.")
        sys.exit(1)

    version     = getattr(gerrychain, "__version__", "unknown")
    import_path = Path(gerrychain.__file__).resolve().parent

    print(f"\n  Version:     {version}")
    print(f"  Import path: {import_path}")

    # ── Dirty status of the local copy ───────────────────────────────────────
    # Walk up from the package dir to find the .git directory
    repo_root = import_path
    for _ in range(5):
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent
    else:
        repo_root = None

    if repo_root:
        dirty = get_dirty_status(repo_root)
        print(f"  Git root:    {repo_root}")
        print(f"  Tree status: {dirty}")
    else:
        dirty = "unknown (no .git found)"
        print(f"  Tree status: {dirty}")

    # ── Version string interpretation ─────────────────────────────────────────
    print(f"\n  Version string breakdown:")
    if "untagged" in version:
        print(f"    ⚠  No upstream git tag found — this is a vendored/dev copy.")
    if "dirty" in version:
        print(f"    ⚠  'dirty' flag: uncommitted local modifications exist.")
        print(f"       These may differ from the published PyPI release.")
    if "unknown" in version:
        print(f"    ⚠  Version could not be computed from git metadata.")
    if not any(k in version for k in ("untagged", "dirty", "unknown")):
        print(f"    ✅ Version appears to be a clean tagged release.")

    # ── Python environment ───────────────────────────────────────────────────
    print(f"\n  Python:      {sys.version.split()[0]}")
    print(f"  Executable:  {sys.executable}")

    # ── Key dependencies ─────────────────────────────────────────────────────
    print(f"\n  Key dependency versions:")
    for pkg in ["geopandas", "shapely", "networkx", "pandas", "numpy"]:
        try:
            mod = importlib.import_module(pkg)
            ver = getattr(mod, "__version__", "?")
            print(f"    {pkg:<12} {ver}")
        except ImportError:
            print(f"    {pkg:<12} NOT INSTALLED")

    # ── GPFS / file count note ────────────────────────────────────────────────
    print(f"\n  File-count context for GPFS:")
    print(f"    1,000 plans  →  ~3,002 output files")
    print(f"    10,000 plans →  ~30,002 output files")
    print(f"    All writes use atomic tmp→replace to prevent partial reads.")
    print(f"    No local scratch is used — all writes go directly to shared storage.")
    print(f"    Merge step (merge_fra_outputs.py) consolidates per-plan CSVs post-run.")

    # ── Provenance dict ───────────────────────────────────────────────────────
    provenance = {
        "gerrychain_version": version,
        "gerrychain_path":    str(import_path),
        "git_root":           str(repo_root) if repo_root else None,
        "tree_status":        dirty,
        "python_version":     sys.version.split()[0],
        "python_executable":  sys.executable,
        "captured_at":        time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if args.save:
        script_dir   = Path(__file__).resolve().parent
        base_dir     = script_dir.parent
        analysis_dir = base_dir / "outputs" / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        out_path = analysis_dir / "gerrychain_provenance.json"
        with open(out_path, "w") as f:
            json.dump(provenance, f, indent=2)
        print(f"\n  ✓ Provenance saved to: {out_path}")

    print(f"\n{'=' * 60}")
    return provenance


if __name__ == "__main__":
    main()
