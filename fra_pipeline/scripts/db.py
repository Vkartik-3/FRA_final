#!/usr/bin/env python3
"""
FRA pipeline — PostgreSQL job-status tracking layer.

All writes here are ADDITIVE: existing atomic CSV/JSON outputs on GPFS are
never touched.  This module only tracks plan lifecycle state in the `runs`
table so that pipeline_status.py and rerun_failed_plans.py can query it
instead of scanning thousands of flat files.

Configuration
─────────────
Set FRA_DB_DSN to a libpq connection string before running any pipeline script:

    export FRA_DB_DSN="postgresql://user:pass@host:5432/fra_pipeline"

If FRA_DB_DSN is unset, every function in this module is a no-op and the
pipeline behaves exactly as before.  This lets the DB layer be enabled
incrementally without breaking existing SLURM submissions.

Schema
──────
Apply schema.sql once before first use:

    psql $FRA_DB_DSN -f scripts/schema.sql
"""

import contextlib
import logging
import os
import socket
from typing import Optional

log = logging.getLogger(__name__)

# ── Lazy import of psycopg2 ───────────────────────────────────────────────────
# Keeps the import from blowing up on HPC nodes where psycopg2 is not in the
# virtual environment yet.
try:
    import psycopg2
    import psycopg2.pool
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    _PSYCOPG2_AVAILABLE = False

_DSN: Optional[str] = None
_pool: Optional[object] = None   # psycopg2.pool.ThreadedConnectionPool


# ── Pool initialisation ───────────────────────────────────────────────────────

def _get_dsn() -> Optional[str]:
    return os.environ.get("FRA_DB_DSN")


def _get_pool():
    global _pool, _DSN
    dsn = _get_dsn()
    if not dsn:
        return None
    if not _PSYCOPG2_AVAILABLE:
        log.warning("FRA_DB_DSN is set but psycopg2 is not installed — DB layer disabled.")
        return None
    # Re-create the pool if DSN changed (e.g. test isolation).
    if _pool is None or dsn != _DSN:
        if _pool is not None:
            _pool.closeall()
        _pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=8, dsn=dsn)
        _DSN = dsn
    return _pool


def _enabled() -> bool:
    return _get_pool() is not None


# ── Transaction context manager ───────────────────────────────────────────────

@contextlib.contextmanager
def _tx():
    """Yield a psycopg2 connection inside a transaction; commit on exit, rollback on error."""
    pool = _get_pool()
    if pool is None:
        yield None
        return
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ── Node identifier ───────────────────────────────────────────────────────────

def _node_id() -> str:
    """Return a node identifier: SLURM_JOB_ID:SLURM_ARRAY_TASK_ID or hostname."""
    job  = os.environ.get("SLURM_JOB_ID")
    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    if job and task:
        return f"{job}:{task}"
    return socket.gethostname()


# ── Seed: register a batch of plans as 'pending' before processing ────────────

def register_batch(
    batch_id: int,
    expected_plans: int,
    slurm_job_id: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """
    Insert a row into the `batches` table at sbatch submission time.

    Called once per SLURM array submission, before any array tasks start.
    ON CONFLICT DO NOTHING makes re-submissions safe.

    The batches table is joined to runs in pipeline_status.py to produce the
    "batch progress + wall time" report — a LEFT JOIN that is meaningless
    without at least one row per batch here.
    """
    if not _enabled():
        return
    import datetime
    now = datetime.datetime.utcnow().isoformat(timespec="seconds")
    with _tx() as conn:
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO batches (batch_id, slurm_job_id, submitted_at, expected_plans, description) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (batch_id) DO NOTHING",
                (batch_id, slurm_job_id, now, expected_plans, description),
            )


def seed_batch(plan_ids: list, batch_id: int) -> int:
    """
    Insert a 'pending' row for every plan_id in plan_ids.

    Uses ON CONFLICT DO NOTHING so re-submitting the same batch is safe.
    Returns the number of rows actually inserted (0 if all already existed).
    """
    if not _enabled() or not plan_ids:
        return 0
    inserted = 0
    with _tx() as conn:
        if conn is None:
            return 0
        with conn.cursor() as cur:
            for pid in plan_ids:
                cur.execute(
                    "INSERT INTO runs (plan_id, batch_id) VALUES (%s, %s) "
                    "ON CONFLICT (plan_id) DO NOTHING",
                    (pid, batch_id),
                )
                inserted += cur.rowcount
    return inserted


# ── Status transitions ────────────────────────────────────────────────────────

def mark_running(plan_id: int, node_id: Optional[str] = None) -> None:
    """Transition plan_id → running.  Called immediately before process_single_plan()."""
    if not _enabled():
        return
    nid = node_id or _node_id()
    with _tx() as conn:
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE runs "
                "SET status='running', node_id=%s, start_time=NOW() "
                "WHERE plan_id=%s",
                (nid, plan_id),
            )


def mark_done(
    plan_id: int,
    assignment_hash: Optional[str] = None,
    dem_seats: Optional[int] = None,
    rep_seats: Optional[int] = None,
    attempts_used: Optional[int] = None,
) -> None:
    """Transition plan_id → done.  Called after successful process_single_plan()."""
    if not _enabled():
        return
    with _tx() as conn:
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE runs "
                "SET status='done', end_time=NOW(), "
                "    assignment_hash=%s, dem_seats=%s, rep_seats=%s, attempts_used=%s "
                "WHERE plan_id=%s",
                (assignment_hash, dem_seats, rep_seats, attempts_used, plan_id),
            )


def mark_failed(
    plan_id: int,
    error_message: str,
    exception_type: Optional[str] = None,
) -> None:
    """
    Transition plan_id → failed and increment retry_count.
    Called in the except block of the per-plan processing loop.
    """
    if not _enabled():
        return
    with _tx() as conn:
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE runs "
                "SET status='failed', end_time=NOW(), "
                "    error_message=%s, exception_type=%s, "
                "    retry_count = retry_count + 1 "
                "WHERE plan_id=%s",
                (error_message, exception_type, plan_id),
            )


# ── Queries ───────────────────────────────────────────────────────────────────

def get_pending_plans(batch_id: int) -> list:
    """Return sorted list of plan_ids with status='pending' in batch_id."""
    if not _enabled():
        return []
    with _tx() as conn:
        if conn is None:
            return []
        with conn.cursor() as cur:
            cur.execute(
                "SELECT plan_id FROM runs "
                "WHERE batch_id=%s AND status='pending' "
                "ORDER BY plan_id",
                (batch_id,),
            )
            return [row[0] for row in cur.fetchall()]


def get_failed_plans(batch_id: Optional[int] = None) -> list:
    """
    Return sorted list of plan_ids with status='failed'.
    If batch_id is None, returns failed plans across ALL batches.
    This replaces scanning fra_failed_plans_*.csv files.
    """
    if not _enabled():
        return []
    with _tx() as conn:
        if conn is None:
            return []
        with conn.cursor() as cur:
            if batch_id is not None:
                cur.execute(
                    "SELECT plan_id FROM runs "
                    "WHERE batch_id=%s AND status='failed' "
                    "ORDER BY plan_id",
                    (batch_id,),
                )
            else:
                cur.execute(
                    "SELECT plan_id FROM runs "
                    "WHERE status='failed' "
                    "ORDER BY plan_id"
                )
            return [row[0] for row in cur.fetchall()]


def claim_next_failed_plan(node_id: Optional[str] = None) -> Optional[int]:
    """
    Atomically claim one failed plan for reprocessing using FOR UPDATE SKIP LOCKED.

    Multiple SLURM workers can call this concurrently without double-processing:
    each worker atomically reads and locks a row that no other worker has locked
    yet.  Workers that see no unlocked failed rows get None and exit cleanly.

    Returns the claimed plan_id, or None if no failed plans remain.
    """
    if not _enabled():
        return None
    nid = node_id or _node_id()
    with _tx() as conn:
        if conn is None:
            return None
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runs
                SET status = 'running',
                    node_id = %s,
                    start_time = NOW()
                WHERE plan_id = (
                    SELECT plan_id FROM runs
                    WHERE  status = 'failed'
                    ORDER  BY plan_id
                    FOR UPDATE SKIP LOCKED
                    LIMIT  1
                )
                RETURNING plan_id
                """,
                (nid,),
            )
            row = cur.fetchone()
            return row[0] if row else None


def find_duplicate_hash(assignment_hash: str) -> Optional[int]:
    """
    Return the plan_id of any existing done plan with the same assignment_hash,
    or None if this is a genuinely new plan.

    Replaces scanning all superdistrict_assignment_N.json files.
    """
    if not _enabled():
        return None
    with _tx() as conn:
        if conn is None:
            return None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT plan_id FROM runs "
                "WHERE assignment_hash = %s AND status = 'done' "
                "LIMIT 1",
                (assignment_hash,),
            )
            row = cur.fetchone()
            return row[0] if row else None
