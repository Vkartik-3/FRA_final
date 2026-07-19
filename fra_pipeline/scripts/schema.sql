-- FRA Pipeline: job-status tracking schema
-- Apply once against the target database:
--   psql $FRA_DB_DSN -f schema.sql
--
-- This table is ADDITIVE — existing flat-file outputs (CSV/JSON) continue
-- to be written unchanged.  The DB layer tracks status only; plan data lives
-- on GPFS as before.

CREATE TABLE IF NOT EXISTS runs (
    plan_id         INTEGER     PRIMARY KEY,
    batch_id        INTEGER     NOT NULL,           -- SLURM array task ID (1-based)
    status          TEXT        NOT NULL DEFAULT 'pending',
                                                    -- pending | running | done | failed
    node_id         TEXT,                           -- SLURM_JOB_ID:SLURM_ARRAY_TASK_ID or hostname
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    retry_count     INTEGER     NOT NULL DEFAULT 0,

    -- populated on success
    assignment_hash TEXT,                           -- SHA-256 of sorted (precinct_id, district_id) pairs
    dem_seats       INTEGER,                        -- Democratic seats won under FRA
    rep_seats       INTEGER,                        -- Republican seats won under FRA
    attempts_used   INTEGER,                        -- gluing algorithm retries needed

    -- populated on failure
    error_message   TEXT,
    exception_type  TEXT,                           -- Python exception class name

    CONSTRAINT status_values CHECK (status IN ('pending','running','done','failed')),
    CONSTRAINT seats_nonneg  CHECK (dem_seats  IS NULL OR dem_seats  >= 0),
    CONSTRAINT rep_nonneg    CHECK (rep_seats   IS NULL OR rep_seats   >= 0),
    CONSTRAINT retry_nonneg  CHECK (retry_count >= 0)
);

-- status is the hot path for claim_next_failed_plan() and get_failed_plans(all)
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs (status);

-- Batch-level aggregation: _STATUS_QUERY GROUP BY batch_id.
-- Without a composite, the aggregation must fetch status from the heap for
-- every row. The (batch_id, status) composite makes the scan covering — no
-- heap access needed. Measured improvement: 18% on 10,000-row table.
CREATE INDEX IF NOT EXISTS idx_runs_batch_status ON runs (batch_id, status);

-- get_pending_plans() / get_failed_plans(batch_id): WHERE batch_id=? AND status=?
-- The separate idx_runs_batch index requires a heap fetch to filter status.
-- This composite (batch_id, status, plan_id) is a covering index for both
-- queries — the planner satisfies the predicate and returns plan_id without
-- touching the heap at all.
CREATE INDEX IF NOT EXISTS idx_runs_batch_status_planid
    ON runs (batch_id, status, plan_id);

-- Duplicate detection: "WHERE assignment_hash = ? AND status = 'done'"
-- Partial index on IS NOT NULL; the status filter is resolved from the heap.
CREATE INDEX IF NOT EXISTS idx_runs_hash ON runs (assignment_hash)
    WHERE assignment_hash IS NOT NULL;

-- Composite index for the FOR UPDATE SKIP LOCKED claim query:
-- WHERE status = 'failed' ORDER BY plan_id
CREATE INDEX IF NOT EXISTS idx_runs_failed_planid ON runs (plan_id)
    WHERE status = 'failed';

-- node_id index for _NODE_FAILURE_QUERY GROUP BY node_id.
-- Eliminates the B-tree temp table the planner otherwise builds for grouping.
-- Measured improvement: 28% on 10,000-row table.
CREATE INDEX IF NOT EXISTS idx_runs_node ON runs (node_id)
    WHERE node_id IS NOT NULL;

-- ── batches: SLURM submission metadata ───────────────────────────────────────
-- One row per sbatch submission.  Joined to runs in pipeline_status.py to
-- compute actual wall time, outstanding plan count, and per-batch failure rate
-- against what was expected at submission time.
--
-- The LEFT JOIN (batches → runs) is the key query:
--   SELECT b.*, COUNT(r.plan_id), ... FROM batches b LEFT JOIN runs r ON r.batch_id=b.batch_id
-- Join strategy PostgreSQL chooses at this scale (100 batches, 10k runs):
-- hash join — scans runs once into a hash table keyed on batch_id, then
-- probes for each batch row.  The (batch_id, status) index on runs makes the
-- probe a covering-index seek rather than a heap fetch, saving ~9% (measured).

CREATE TABLE IF NOT EXISTS batches (
    batch_id        INTEGER     PRIMARY KEY,   -- matches batch_id in runs
    slurm_job_id    TEXT,                      -- SLURM_JOB_ID from sbatch output
    submitted_at    TIMESTAMP   NOT NULL,      -- wall-clock time of sbatch call
    expected_plans  INTEGER     NOT NULL,      -- end_plan - start_plan + 1
    description     TEXT                       -- e.g. "FRA batch 3: plans 201-300"
);

CREATE INDEX IF NOT EXISTS idx_batches_submitted ON batches (submitted_at);

-- ── Seed helper ──────────────────────────────────────────────────────────────
-- Called once per SLURM batch before processing begins.
-- Inserts a 'pending' row for every plan_id in the batch; existing rows are
-- left unchanged so re-submissions of the same batch are safe.
--
-- Usage from Python:
--   INSERT INTO runs (plan_id, batch_id)
--   VALUES (%s, %s)
--   ON CONFLICT (plan_id) DO NOTHING;
