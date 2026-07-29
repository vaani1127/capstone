#!/usr/bin/env python3
"""
Blockchain / Hash-Chain Tamper Detection Benchmark
====================================================
Measures how quickly verify_chain_integrity() detects a single tampered block
across three tamper positions (start / middle / end) and multiple chain sizes.

Usage
-----
  # From the repo root (d:/My Workspace/capstone work/Capstone/)
  cd project/backend
  python ../../benchmark_tamper_detection.py

  # Custom chain lengths
  python ../../benchmark_tamper_detection.py --chain-lengths 100 500 2000

  # Skip the 10 000-entry run (slow on large existing chains)
  python ../../benchmark_tamper_detection.py --chain-lengths 100 1000

Safety
------
All writes happen inside a SQLAlchemy SAVEPOINT that is always rolled back at
the end of each chain-length run, even if an exception is raised.  No data
is permanently written to the database.

Requirements
------------
No new packages beyond what is already in requirements.txt.  The script uses
only stdlib + the project's own app package.
"""

import argparse
import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap: add project/backend to sys.path so app.* imports work
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = REPO_ROOT / "project" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text

from app.db.session import SessionLocal, engine as _sa_engine
from app.models.audit_chain import AuditChain
from app.services.blockchain_service import create_audit_entry, verify_chain_integrity

# Disable SQL echo for this benchmark script.
# session.py sets echo=settings.DEBUG on the engine, and SQLAlchemy
# re-asserts the log level on every connection — so setLevel() alone is
# not enough.  Setting engine.echo = False directly is the only reliable
# way to suppress the per-query output without touching session.py.
_sa_engine.echo = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BENCHMARK_TAG = "__benchmark__"          # injected into every seeded record_data
DEFAULT_CHAIN_LENGTHS = [100, 1000, 10_000]

RECORD_TYPES = [
    "appointment_created",
    "appointment_status_updated",
    "appointment_cancelled",
    "medical_record",
    "walk_in_registered",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record_data(index: int, run_id: str) -> Dict[str, Any]:
    """Return realistic-looking audit payload for a seeded block."""
    record_type = RECORD_TYPES[index % len(RECORD_TYPES)]
    base: Dict[str, Any] = {
        "_benchmark_run_id": run_id,     # lets us identify our rows if needed
        "_benchmark_tag": BENCHMARK_TAG,
        "index": index,
    }
    if record_type == "medical_record":
        base.update({
            "consultation_notes": f"Patient presents with routine check-up. Entry {index}.",
            "diagnosis": "Z00.00 Encounter for general adult medical examination",
            "prescription": "None",
            "patient_id": 1000 + (index % 50),
            "doctor_id": 1 + (index % 5),
            "version_number": 1,
        })
    elif record_type in ("appointment_created", "appointment_status_updated"):
        base.update({
            "appointment_id": 5000 + index,
            "patient_id": 1000 + (index % 50),
            "doctor_id": 1 + (index % 5),
            "old_status": "SCHEDULED",
            "new_status": "CHECKED_IN",
        })
    elif record_type == "appointment_cancelled":
        base.update({
            "appointment_id": 5000 + index,
            "reason": "Patient requested cancellation",
            "cancelled_by": 1 + (index % 5),
        })
    else:  # walk_in_registered
        base.update({
            "patient_id": 1000 + (index % 50),
            "doctor_id": 1 + (index % 5),
            "queue_position": index % 20 + 1,
        })
    return base


def _seed_chain(db, n: int, run_id: str) -> List[int]:
    """
    Insert N audit chain blocks and return their DB IDs in insertion order.
    Caller owns the surrounding transaction / savepoint.
    """
    ids: List[int] = []
    for i in range(n):
        record_type = RECORD_TYPES[i % len(RECORD_TYPES)]
        record_id   = 9_000_000 + i          # clearly synthetic, no FK constraint
        data        = _make_record_data(i, run_id)
        entry       = create_audit_entry(
            db          = db,
            record_id   = record_id,
            record_type = record_type,
            record_data = data,
            user_id     = None,              # nullable FK — safe for benchmarking
        )
        ids.append(entry.id)
        if (i + 1) % 500 == 0 or (i + 1) == n:
            print(f"    seeded {i + 1}/{n}", end="\r", flush=True)
    print()  # newline after the \r progress line
    db.flush()
    return ids


def _tamper_block(db, block_id: int) -> None:
    """
    Directly mutate record_data for one block via raw SQL, simulating an
    attacker who bypasses the application layer.  The stored hash is left
    unchanged so the mismatch becomes detectable.
    """
    db.execute(
        text(
            "UPDATE audit_chain "
            "SET record_data = record_data || :patch "
            "WHERE id = :bid"
        ),
        {
            "patch": json.dumps({"_tampered": True, "notes": "INJECTED <script>alert(1)</script>"}),
            "bid": block_id,
        },
    )
    db.flush()


@contextmanager
def _savepoint(db):
    """Context manager: runs body inside a SAVEPOINT; always rolls back."""
    sp = db.begin_nested()
    try:
        yield sp
    finally:
        sp.rollback()


def _run_verify(db) -> Tuple[Dict[str, Any], float]:
    """Run verify_chain_integrity and return (result_dict, elapsed_seconds)."""
    t0 = time.perf_counter()
    result = verify_chain_integrity(db)
    elapsed = time.perf_counter() - t0
    return result, elapsed


def _first_inconsistency_index(result: Dict[str, Any]) -> Optional[int]:
    """Return block_index of the earliest inconsistency, or None."""
    incons = result.get("inconsistencies", [])
    if not incons:
        return None
    return min(e["block_index"] for e in incons)


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def _sep(width: int = 90) -> str:
    return "─" * width


def _header(title: str, width: int = 90) -> str:
    pad = max(0, width - len(title) - 4)
    return f"┌─ {title} {'─' * pad}┐"


def _row(*cols: str, widths: List[int]) -> str:
    parts = [f"{c:<{w}}" for c, w in zip(cols, widths)]
    return "  " + "  ".join(parts)


def _print_table(chain_n: int, pre_existing: int, baseline_time: float,
                 rows: List[Dict[str, Any]]) -> None:
    effective_n = pre_existing + chain_n
    print()
    print(_header(f"Chain length: {chain_n:,} seeded  +  {pre_existing:,} pre-existing  =  {effective_n:,} total blocks"))
    print(f"  Baseline verification (no tampering): {baseline_time * 1000:.3f} ms")
    print()
    W = [10, 10, 14, 14, 14]
    print(_row("Position", "Detected", "Detect time", "Block index", "vs baseline",
               widths=W))
    print("  " + "  ".join("─" * w for w in W))
    for r in rows:
        detected    = "YES ✓" if r["detected"] else "NO  ✗"
        det_ms      = f"{r['detect_time'] * 1000:.3f} ms"
        blk_idx     = str(r["block_index"]) if r["block_index"] is not None else "—"
        overhead    = r['detect_time'] - baseline_time
        overhead_s  = f"{overhead * 1000:+.3f} ms"
        print(_row(r["position"], detected, det_ms, blk_idx, overhead_s, widths=W))
    print()


# ---------------------------------------------------------------------------
# Core benchmark for one chain length
# ---------------------------------------------------------------------------

def _benchmark_one_length(db, n: int) -> None:
    run_id = f"bench_{n}_{int(time.time())}"

    # Count pre-existing blocks so we can report effective chain size
    pre_existing: int = db.query(AuditChain).count()

    with _savepoint(db):
        # ── Seed ──────────────────────────────────────────────────────────
        print(f"  Seeding {n:,} blocks … ", end="", flush=True)
        t_seed = time.perf_counter()
        block_ids = _seed_chain(db, n, run_id)
        print(f"done in {time.perf_counter() - t_seed:.2f}s")

        # ── Baseline (no tampering) ────────────────────────────────────────
        print("  Baseline verification … ", end="", flush=True)
        baseline_result, baseline_time = _run_verify(db)
        if not baseline_result["is_valid"]:
            print(
                f"\n  WARNING: chain already shows {len(baseline_result['inconsistencies'])} "
                "inconsistency/ies before any tampering.  "
                "Pre-existing chain may be broken.  Results may be unreliable."
            )
        else:
            print(f"valid — {baseline_time * 1000:.3f} ms")

        # ── Tamper at start / middle / end ────────────────────────────────
        positions = {
            "start":  block_ids[0],
            "middle": block_ids[len(block_ids) // 2],
            "end":    block_ids[-1],
        }

        rows: List[Dict[str, Any]] = []

        for pos_name, target_id in positions.items():
            with _savepoint(db):
                _tamper_block(db, target_id)
                result, detect_time = _run_verify(db)
                rows.append({
                    "position":    pos_name,
                    "detected":    not result["is_valid"],
                    "detect_time": detect_time,
                    "block_index": _first_inconsistency_index(result),
                })
            # inner savepoint rolled back → block is restored; next iteration is clean

        _print_table(n, pre_existing, baseline_time, rows)
    # outer savepoint rolled back → all seeded blocks removed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark blockchain tamper-detection latency."
    )
    parser.add_argument(
        "--chain-lengths",
        nargs="+",
        type=int,
        default=DEFAULT_CHAIN_LENGTHS,
        metavar="N",
        help="Chain sizes to benchmark (default: 100 1000 10000)",
    )
    args = parser.parse_args()

    print()
    print("=" * 90)
    print("  BLOCKCHAIN TAMPER-DETECTION BENCHMARK")
    print(f"  Chain lengths : {args.chain_lengths}")
    print(f"  Started at    : {datetime.utcnow().isoformat()} UTC")
    print("  Cleanup       : ALL writes are rolled back via savepoints — no DB pollution")
    print("=" * 90)

    db = SessionLocal()
    try:
        for n in args.chain_lengths:
            print(f"\n{'━' * 90}")
            print(f"  Running chain length N = {n:,}")
            print(f"{'━' * 90}")
            _benchmark_one_length(db, n)
    except KeyboardInterrupt:
        print("\n  Interrupted — rolling back any open transactions.")
        db.rollback()
    except Exception as exc:
        db.rollback()
        raise
    finally:
        db.close()

    print("=" * 90)
    print("  Benchmark complete.  No data was written to the database.")
    print("=" * 90)
    print()


if __name__ == "__main__":
    main()
