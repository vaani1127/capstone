"""
extend_audit_dataset.py
=======================
Extends 09_audit_logs_synthetic.csv with additional Admin and Nurse rows,
bringing each role up to ~1,400 total rows to match Doctor's count.

Generation rules are derived from the observed feature distributions of
existing rows (computed in Step 1 of the ablation study analysis):

  Normal rows  -- sampled from clipped Gaussian matching each role's
                  observed normal-row mean/std, with integer rounding
                  for count-valued features.

  Anomaly rows -- single dominant archetype per role:
    Admin : mass_access pattern
            high actions_per_hour [36-89], high unique_patients_accessed [27-77],
            off_hours_flag=0, cross_role_action_flag=0 (Admin has no forbidden
            actions in FORBIDDEN_ACTIONS), high untreated_patient_ratio [0.65-0.97],
            rapid_edit_flag ~64% probability, session_duration ~143-416 min.

    Nurse : privilege_abuse pattern
            cross_role_action_flag=1 (always -- 43/43 existing anomalies),
            same high-volume profile as Admin anomalies,
            rapid_edit_flag ~60% probability.

Output
------
  dataset/main_dataset/09_audit_logs_synthetic_extended.csv
  Original 5,000 rows + new Admin/Nurse rows.  Original file is never modified.

Usage
-----
  cd project/backend
  python extend_audit_dataset.py
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent.parent
DATA_IN    = REPO_ROOT / "dataset" / "main_dataset" / "09_audit_logs_synthetic.csv"
DATA_OUT   = REPO_ROOT / "dataset" / "main_dataset" / "09_audit_logs_synthetic_extended.csv"

TARGET_ROWS   = 1400   # target total per role after extension
ANOMALY_RATE  = 0.078  # ~7.8% -- matches overall dataset rate
RNG_SEED      = 42

# ---------------------------------------------------------------------------
# Role-specific normal-row distributions (mean, std) from Step 1 analysis.
# Bounds are the observed [min, max] from existing normal rows.
# ---------------------------------------------------------------------------

NORMAL_PARAMS = {
    "admin": {
        "actions_per_hour":         {"mean": 8.037,  "std": 4.067,  "min": 2,    "max": 15,    "int": True},
        "unique_patients_accessed": {"mean": 4.135,  "std": 2.452,  "min": 0,    "max": 8,     "int": True},
        "off_hours_flag":           {"mean": 0.451,  "std": None,   "min": 0,    "max": 1,     "bernoulli": True},
        "untreated_patient_ratio":  {"mean": 0.049,  "std": 0.029,  "min": 0.0,  "max": 0.10,  "int": False},
        "record_type_entropy":      {"mean": 1.643,  "std": 0.296,  "min": 0.81, "max": 2.00,  "int": False},
        "rapid_edit_flag":          {"mean": 0.041,  "std": None,   "min": 0,    "max": 1,     "bernoulli": True},
        "cross_role_action_flag":   {"fixed": 0},
        "session_duration_minutes": {"mean": 37.849, "std": 19.420, "min": 6.38, "max": 74.51, "int": False},
    },
    "nurse": {
        "actions_per_hour":         {"mean": 19.695, "std": 6.670,  "min": 8,    "max": 30,    "int": True},
        "unique_patients_accessed": {"mean": 16.155, "std": 5.686,  "min": 6,    "max": 25,    "int": True},
        "off_hours_flag":           {"mean": 0.473,  "std": None,   "min": 0,    "max": 1,     "bernoulli": True},
        "untreated_patient_ratio":  {"mean": 0.061,  "std": 0.034,  "min": 0.0,  "max": 0.12,  "int": False},
        "record_type_entropy":      {"mean": 1.639,  "std": 0.320,  "min": 0.0,  "max": 2.00,  "int": False},
        "rapid_edit_flag":          {"mean": 0.043,  "std": None,   "min": 0,    "max": 1,     "bernoulli": True},
        "cross_role_action_flag":   {"fixed": 0},
        "session_duration_minutes": {"mean": 40.470, "std": 20.215, "min": 5.19, "max": 74.89, "int": False},
    },
}

# Anomaly-row parameters: ranges are [min, max] from existing anomaly rows per role.
# Continuous features sampled uniformly within observed range (matches generation
# style implied by the near-uniform spread in existing anomaly rows).
ANOMALY_PARAMS = {
    "admin": {
        "actions_per_hour":         {"low": 36,   "high": 89,    "int": True},
        "unique_patients_accessed": {"low": 27,   "high": 77,    "int": True},
        "off_hours_flag":           {"fixed": 0},
        "untreated_patient_ratio":  {"low": 0.65, "high": 0.97,  "int": False},
        "record_type_entropy":      {"low": 1.25, "high": 1.95,  "int": False},
        "rapid_edit_flag":          {"mean": 0.64, "bernoulli": True},
        "cross_role_action_flag":   {"fixed": 0},   # Admin has no forbidden actions
        "session_duration_minutes": {"low": 143.44, "high": 416.47, "int": False},
    },
    "nurse": {
        "actions_per_hour":         {"low": 35,   "high": 86,    "int": True},
        "unique_patients_accessed": {"low": 26,   "high": 80,    "int": True},
        "off_hours_flag":           {"fixed": 0},
        "untreated_patient_ratio":  {"low": 0.66, "high": 0.98,  "int": False},
        "record_type_entropy":      {"low": 1.37, "high": 2.25,  "int": False},
        "rapid_edit_flag":          {"mean": 0.605, "bernoulli": True},
        "cross_role_action_flag":   {"fixed": 1},   # always 1 -- privilege abuse
        "session_duration_minutes": {"low": 124.52, "high": 410.60, "int": False},
    },
}

FEATURE_ORDER = [
    "actions_per_hour",
    "unique_patients_accessed",
    "off_hours_flag",
    "untreated_patient_ratio",
    "record_type_entropy",
    "rapid_edit_flag",
    "cross_role_action_flag",
    "session_duration_minutes",
]

# Actions and record_types per role (from observed value_counts)
ROLE_ACTIONS = {
    "admin": ["update_schedule", "view_report", "view_audit", "manage_user"],
    "nurse": ["update_vitals", "update_queue", "register_walkin", "view_appointment"],
}
ROLE_RECORD_TYPES = {
    "admin": ["schedule", "report", "audit", "user"],
    "nurse": ["appointment", "observation", "audit", "prescription"],
}
# Action/record_type used for anomalous (cross-role) nurse rows
NURSE_ANOMALY_ACTIONS      = ["create_prescription", "update_diagnosis"]
NURSE_ANOMALY_RECORD_TYPES = ["prescription", "condition"]

# User ID patterns: existing Admin has ADM_001-003, Nurse has NUR_001-007.
# New users added beyond the existing pool.
EXISTING_USERS = {
    "admin": ["ADM_001", "ADM_002", "ADM_003"],
    "nurse": ["NUR_001", "NUR_002", "NUR_003", "NUR_004", "NUR_005", "NUR_006", "NUR_007"],
}
NEW_USER_STARTS = {"admin": 4, "nurse": 8}   # first new user index per role


# ---------------------------------------------------------------------------
# Helper: sample one feature vector
# ---------------------------------------------------------------------------

def _sample_feature(params: dict, rng: np.random.Generator) -> float:
    if "fixed" in params:
        return float(params["fixed"])
    if params.get("bernoulli"):
        return float(rng.random() < params["mean"])
    v = rng.normal(params["mean"], params["std"])
    v = float(np.clip(v, params["min"], params["max"]))
    if params.get("int"):
        v = float(round(v))
        v = float(np.clip(v, params["min"], params["max"]))
    return v


def _sample_anomaly_feature(params: dict, rng: np.random.Generator) -> float:
    if "fixed" in params:
        return float(params["fixed"])
    if params.get("bernoulli"):
        return float(rng.random() < params["mean"])
    if params.get("int"):
        v = float(rng.integers(int(params["low"]), int(params["high"]) + 1))
    else:
        v = rng.uniform(params["low"], params["high"])
    return float(v)


def generate_features(role: str, is_anomaly: bool, rng: np.random.Generator) -> dict:
    param_map = ANOMALY_PARAMS[role] if is_anomaly else NORMAL_PARAMS[role]
    sampler   = _sample_anomaly_feature if is_anomaly else _sample_feature
    return {f: sampler(param_map[f], rng) for f in FEATURE_ORDER}


# ---------------------------------------------------------------------------
# Helper: build a full CSV row
# ---------------------------------------------------------------------------

def make_row(
    audit_id:   int,
    role:       str,
    user_id:    str,
    is_anomaly: bool,
    patient_ids: list,
    ts_range:   tuple,
    rng:        np.random.Generator,
) -> dict:
    feats = generate_features(role, is_anomaly, rng)

    # Timestamp: uniform within the existing data date range
    ts_start, ts_span_seconds = ts_range
    offset = timedelta(seconds=int(rng.integers(0, ts_span_seconds)))
    timestamp = (ts_start + offset).strftime("%Y-%m-%d %H:%M:%S")

    # patient_id: draw from existing pool
    patient_id = str(rng.choice(patient_ids))

    # action / record_type
    if is_anomaly and role == "nurse":
        action      = str(rng.choice(NURSE_ANOMALY_ACTIONS))
        record_type = str(rng.choice(NURSE_ANOMALY_RECORD_TYPES))
    else:
        action      = str(rng.choice(ROLE_ACTIONS[role]))
        record_type = str(rng.choice(ROLE_RECORD_TYPES[role]))

    record_id = "{}_{}".format(record_type.upper(), int(rng.integers(1000, 9999)))

    return {
        "audit_id":                   audit_id,
        "user_id":                    user_id,
        "role":                       role,
        "action":                     action,
        "patient_id":                 patient_id,
        "timestamp":                  timestamp,
        "record_type":                record_type,
        "record_id":                  record_id,
        "actions_per_hour":           feats["actions_per_hour"],
        "unique_patients_accessed":   feats["unique_patients_accessed"],
        "off_hours_flag":             feats["off_hours_flag"],
        "untreated_patient_ratio":    round(feats["untreated_patient_ratio"], 3),
        "record_type_entropy":        round(feats["record_type_entropy"], 3),
        "rapid_edit_flag":            feats["rapid_edit_flag"],
        "cross_role_action_flag":     feats["cross_role_action_flag"],
        "session_duration_minutes":   round(feats["session_duration_minutes"], 2),
        "is_anomaly":                 int(is_anomaly),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not DATA_IN.exists():
        print("ERROR: Source dataset not found: {}".format(DATA_IN), file=sys.stderr)
        sys.exit(1)

    rng = np.random.default_rng(RNG_SEED)

    # -----------------------------------------------------------------------
    # Load original dataset
    # -----------------------------------------------------------------------
    df_orig = pd.read_csv(DATA_IN)
    df_orig["role"] = df_orig["role"].str.strip().str.lower()

    next_audit_id = int(df_orig["audit_id"].max()) + 1

    # Date range for new timestamps
    ts_series   = pd.to_datetime(df_orig["timestamp"])
    ts_start    = ts_series.min().to_pydatetime()
    ts_end      = ts_series.max().to_pydatetime()
    ts_span_sec = int((ts_end - ts_start).total_seconds())
    ts_range    = (ts_start, ts_span_sec)

    # Patient IDs: reuse existing UUIDs only
    patient_ids = df_orig["patient_id"].dropna().unique().tolist()

    # -----------------------------------------------------------------------
    # Print before-state
    # -----------------------------------------------------------------------
    print("=" * 65)
    print("  BEFORE:")
    print("=" * 65)
    print("  {:<10}  {:>8}  {:>10}  {:>12}".format(
        "Role", "Rows", "Anomalies", "Anomaly %"))
    print("-" * 65)
    for role in ["admin", "doctor", "nurse", "patient"]:
        rdf = df_orig[df_orig["role"] == role]
        n   = len(rdf)
        na  = int(rdf["is_anomaly"].sum())
        print("  {:<10}  {:>8,}  {:>10,}  {:>11.1f}%".format(
            role.title(), n, na, na/n*100 if n else 0))
    n_total = len(df_orig)
    na_total = int(df_orig["is_anomaly"].sum())
    print("-" * 65)
    print("  {:<10}  {:>8,}  {:>10,}  {:>11.1f}%".format(
        "TOTAL", n_total, na_total, na_total/n_total*100))
    print()

    # -----------------------------------------------------------------------
    # Generate new rows for Admin and Nurse
    # -----------------------------------------------------------------------
    all_new_rows = []

    for role in ["admin", "nurse"]:
        role_df    = df_orig[df_orig["role"] == role]
        n_existing = len(role_df)
        n_needed   = max(0, TARGET_ROWS - n_existing)

        if n_needed == 0:
            print("  [{}] Already at or above target ({} rows) - skipping.".format(
                role.title(), n_existing))
            continue

        n_anomaly_new = round(n_needed * ANOMALY_RATE)
        n_normal_new  = n_needed - n_anomaly_new

        # Build user pool: existing users + new synthetic users spread across rows
        existing_users = EXISTING_USERS[role]
        new_user_start = NEW_USER_STARTS[role]
        # Add ~5 new users per role
        n_new_users    = 5
        prefix         = "ADM" if role == "admin" else "NUR"
        new_users      = [
            "{}_{:03d}".format(prefix, i)
            for i in range(new_user_start, new_user_start + n_new_users)
        ]
        full_user_pool = existing_users + new_users

        print("  [{}] Generating {:,} rows ({:,} normal + {:,} anomaly) ...".format(
            role.title(), n_needed, n_normal_new, n_anomaly_new))

        labels = [False] * n_normal_new + [True] * n_anomaly_new
        rng.shuffle(labels)  # interleave anomalies naturally

        for is_anom in labels:
            user_id = str(rng.choice(full_user_pool))
            row = make_row(
                audit_id    = next_audit_id,
                role        = role,
                user_id     = user_id,
                is_anomaly  = is_anom,
                patient_ids = patient_ids,
                ts_range    = ts_range,
                rng         = rng,
            )
            all_new_rows.append(row)
            next_audit_id += 1

    # -----------------------------------------------------------------------
    # Assemble and write output
    # -----------------------------------------------------------------------
    df_new  = pd.DataFrame(all_new_rows)
    df_out  = pd.concat([df_orig, df_new], ignore_index=True)

    # Preserve original column order
    df_out  = df_out[df_orig.columns]

    df_out.to_csv(DATA_OUT, index=False)

    # -----------------------------------------------------------------------
    # Print after-state
    # -----------------------------------------------------------------------
    print()
    print("=" * 65)
    print("  AFTER ({}):".format(DATA_OUT.name))
    print("=" * 65)
    print("  {:<10}  {:>8}  {:>10}  {:>12}  {:>8}".format(
        "Role", "Rows", "Anomalies", "Anomaly %", "+Rows"))
    print("-" * 65)
    for role in ["admin", "doctor", "nurse", "patient"]:
        rdf_before = df_orig[df_orig["role"] == role]
        rdf_after  = df_out[df_out["role"] == role]
        n_b  = len(rdf_before)
        n_a  = len(rdf_after)
        na_a = int(rdf_after["is_anomaly"].sum())
        added = n_a - n_b
        print("  {:<10}  {:>8,}  {:>10,}  {:>11.1f}%  {:>+8,}".format(
            role.title(), n_a, na_a, na_a/n_a*100 if n_a else 0, added))
    n_out_total  = len(df_out)
    na_out_total = int(df_out["is_anomaly"].sum())
    n_orig_total = len(df_orig)
    print("-" * 65)
    print("  {:<10}  {:>8,}  {:>10,}  {:>11.1f}%  {:>+8,}".format(
        "TOTAL", n_out_total, na_out_total,
        na_out_total/n_out_total*100, n_out_total - n_orig_total))
    print()
    print("  Written: {}".format(DATA_OUT))


if __name__ == "__main__":
    main()
