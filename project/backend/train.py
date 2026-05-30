"""
Offline training script for HealthSaathi anomaly detection models.

Loads a synthetic audit-log CSV, engineers the same 8 behavioural features
used by anomaly_service.py, trains one IsolationForest per role, evaluates
each model with Silhouette Score, and saves the results to the models/ directory.

Usage
-----
    python train.py --data path/to/09_audit_logs_synthetic.csv
    python train.py --data data/09_audit_logs_synthetic.csv --output-dir models/
"""

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score


# ---------------------------------------------------------------------------
# Constants -- must stay in sync with anomaly_service.FEATURE_ORDER
# ---------------------------------------------------------------------------

FEATURE_ORDER: List[str] = [
    "actions_per_hour",
    "unique_patients_accessed",
    "off_hours_flag",
    "untreated_patient_ratio",
    "record_type_entropy",
    "rapid_edit_flag",
    "cross_role_action_flag",
    "session_duration_minutes",
]

ROLES: List[str] = ["Admin", "Doctor", "Nurse", "Patient"]

WINDOW_MINUTES: int = 60

FORBIDDEN_ACTIONS: Dict[str, List[str]] = {
    "Patient": ["medical_record_created", "medical_record_updated", "walk_in_registered"],
    "Nurse":   ["medical_record_created", "medical_record_updated"],
    "Doctor":  [],
    "Admin":   [],
}


# ---------------------------------------------------------------------------
# Feature engineering (slow path -- raw audit-log CSVs only)
# ---------------------------------------------------------------------------

def _extract_patient_ids(group: pd.DataFrame) -> set:
    """Pull patient_id values out of the record_data JSON column."""
    ids: set = set()
    if "record_data" not in group.columns:
        return ids
    for raw in group["record_data"]:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                continue
        if isinstance(raw, dict):
            pid = raw.get("patient_id")
            if pid is not None:
                try:
                    ids.add(int(pid))
                except (ValueError, TypeError):
                    pass
    return ids


def engineer_features(window: pd.DataFrame, role: str) -> Dict[str, float]:
    """
    Compute all 8 behavioural features for a single user/time-window slice.

    Mirrors the logic in anomaly_service.extract_features() so that models
    trained here are compatible with runtime scoring.

    Args:
        window: Rows belonging to one user within a 60-minute window.
        role:   Plain-string role name ("Doctor", "Admin", ...).

    Returns:
        dict with exactly the 8 keys in FEATURE_ORDER.
    """
    n = len(window)

    # 1. actions_per_hour
    actions_per_hour = float(n * (60.0 / WINDOW_MINUTES))

    # 2. unique_patients_accessed
    patient_ids = _extract_patient_ids(window)
    unique_patients_accessed = float(len(patient_ids))

    # 3. off_hours_flag  (22:00 - 05:59 based on first event in window)
    first_hour = int(window["timestamp"].iloc[0].hour)
    off_hours_flag = float(1 if (first_hour >= 22 or first_hour <= 5) else 0)

    # 4. untreated_patient_ratio  (Doctor only)
    #    Approximated from record_data: patients whose records lack an
    #    appointment_id field are considered "untreated" in this context.
    untreated_patient_ratio = 0.0
    if role == "Doctor" and patient_ids:
        treated_ids: set = set()
        if "record_data" in window.columns:
            for raw in window["record_data"]:
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except Exception:
                        continue
                if isinstance(raw, dict) and raw.get("appointment_id") is not None:
                    pid = raw.get("patient_id")
                    if pid is not None:
                        try:
                            treated_ids.add(int(pid))
                        except (ValueError, TypeError):
                            pass
        unmatched = len(patient_ids - treated_ids)
        untreated_patient_ratio = float(unmatched / len(patient_ids))

    # 5. record_type_entropy  (Shannon entropy over record_type distribution)
    if "record_type" in window.columns:
        types = [v for v in window["record_type"].dropna() if v]
    else:
        types = []
    if types:
        counts = Counter(types)
        total = len(types)
        record_type_entropy = float(
            -sum((c / total) * math.log2(c / total) for c in counts.values())
        )
    else:
        record_type_entropy = 0.0

    # 6. rapid_edit_flag  (same record_id modified >3 times in last 15 min)
    rapid_cutoff = window["timestamp"].max() - pd.Timedelta(minutes=15)
    recent = window[window["timestamp"] >= rapid_cutoff]
    if "record_id" in recent.columns and len(recent) > 0:
        id_counts = recent["record_id"].value_counts()
        rapid_edit_flag = float(1 if (id_counts > 3).any() else 0)
    else:
        rapid_edit_flag = 0.0

    # 7. cross_role_action_flag
    forbidden_types = set(FORBIDDEN_ACTIONS.get(role, []))
    if forbidden_types and "record_type" in window.columns:
        cross_role_action_flag = float(
            1 if window["record_type"].isin(forbidden_types).any() else 0
        )
    else:
        cross_role_action_flag = 0.0

    # 8. session_duration_minutes
    if n >= 2:
        session_duration_minutes = float(
            (window["timestamp"].max() - window["timestamp"].min()).total_seconds() / 60.0
        )
    else:
        session_duration_minutes = 0.0

    return {
        "actions_per_hour":         actions_per_hour,
        "unique_patients_accessed": unique_patients_accessed,
        "off_hours_flag":           off_hours_flag,
        "untreated_patient_ratio":  untreated_patient_ratio,
        "record_type_entropy":      record_type_entropy,
        "rapid_edit_flag":          rapid_edit_flag,
        "cross_role_action_flag":   cross_role_action_flag,
        "session_duration_minutes": session_duration_minutes,
    }


def build_feature_matrix(df: pd.DataFrame, role: str) -> np.ndarray:
    """
    Build a feature matrix for all users of the given role.

    Fast path -- pre-computed feature columns present
    -------------------------------------------------
    If the CSV already contains all 8 columns named in FEATURE_ORDER
    (e.g. the synthetic dataset 09_audit_logs_synthetic.csv), each row is
    treated as one ready-made training example and the columns are read
    directly.  No window slicing is performed.

    Slow path -- raw audit-log CSV
    ------------------------------
    If the feature columns are absent, the function falls back to computing
    them from raw event timestamps.  Each user's timeline is divided into
    consecutive non-overlapping WINDOW_MINUTES (60 min) buckets; every
    non-empty bucket produces exactly one feature vector via
    engineer_features().  Stride equals window size so there is no overlap
    and each event belongs to exactly one bucket -- consistent with how
    anomaly_service.extract_features() operates at runtime.

    Args:
        df:   Full preprocessed DataFrame (all roles).
        role: Role to filter on.

    Returns:
        Float numpy array of shape (n_rows, 8).
    """
    role_df = df[df["role"] == role].copy()

    if len(role_df) == 0:
        return np.zeros((10, len(FEATURE_ORDER)), dtype=float)

    # ------------------------------------------------------------------
    # Fast path: all 8 feature columns already exist in the CSV.
    # ------------------------------------------------------------------
    if all(f in role_df.columns for f in FEATURE_ORDER):
        X = role_df[FEATURE_ORDER].to_numpy(dtype=float)
        return X if len(X) > 0 else np.zeros((10, len(FEATURE_ORDER)), dtype=float)

    # ------------------------------------------------------------------
    # Slow path: compute features from raw event timestamps.
    # ------------------------------------------------------------------
    rows: List[List[float]] = []
    window_td = pd.Timedelta(minutes=WINDOW_MINUTES)  # stride == window: no overlap

    for user_id, user_df in role_df.groupby("user_id"):
        user_df = user_df.sort_values("timestamp").reset_index(drop=True)
        t_min = user_df["timestamp"].min()
        t_max = user_df["timestamp"].max()

        t = t_min
        while t <= t_max:
            window = user_df[
                (user_df["timestamp"] >= t) &
                (user_df["timestamp"] < t + window_td)
            ]
            if len(window) > 0:
                feats = engineer_features(window, role)
                rows.append([feats[k] for k in FEATURE_ORDER])
            t += window_td  # advance by one full window -- no overlap

    if not rows:
        return np.zeros((10, len(FEATURE_ORDER)), dtype=float)

    return np.array(rows, dtype=float)


# ---------------------------------------------------------------------------
# CSV loading & normalisation
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> pd.DataFrame:
    """
    Load and normalise the audit-log CSV.

    Handles common column-name variants (role/user_role, timestamp/created_at)
    and coerces the timestamp column to timezone-naive UTC datetime.
    Role values are normalised to title-case ("admin" -> "Admin") so they
    match the ROLES list regardless of how the CSV was generated.

    Args:
        path: Path to the CSV file.

    Returns:
        Cleaned DataFrame with columns: user_id, role, timestamp,
        record_id, record_type, record_data (where available).

    Raises:
        SystemExit: If required columns are missing or the file is unreadable.
    """
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"ERROR: Cannot read CSV - {exc}", file=sys.stderr)
        sys.exit(1)

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Resolve role column
    if "role" not in df.columns:
        if "user_role" in df.columns:
            df.rename(columns={"user_role": "role"}, inplace=True)
        else:
            print("ERROR: CSV must contain a 'role' or 'user_role' column.", file=sys.stderr)
            sys.exit(1)

    # Normalise role values to title-case so "admin"/"ADMIN" -> "Admin" etc.,
    # matching the ROLES list and anomaly_service.UserRole enum values.
    df["role"] = df["role"].astype(str).str.strip().str.title()

    # Resolve timestamp column
    ts_candidates = [c for c in df.columns if "timestamp" in c or c == "created_at"]
    if not ts_candidates:
        print("ERROR: CSV must contain a 'timestamp' or 'created_at' column.", file=sys.stderr)
        sys.exit(1)
    ts_col = ts_candidates[0]

    df["timestamp"] = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    # Drop timezone info for uniform arithmetic (data assumed UTC)
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    required = {"user_id", "role", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        print(f"ERROR: Missing required columns: {missing}", file=sys.stderr)
        sys.exit(1)

    before = len(df)
    df = df.dropna(subset=["user_id", "role", "timestamp"])
    dropped = before - len(df)
    if dropped:
        print(f"  Warning: dropped {dropped:,} rows with null user_id/role/timestamp.")

    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train per-role IsolationForest anomaly detection models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--data",
        required=True,
        metavar="CSV_PATH",
        help="Path to 09_audit_logs_synthetic.csv (or any audit-log CSV).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "models"),
        metavar="DIR",
        help="Directory to write .pkl model files (default: ./models/).",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    print(f"Loading: {data_path}")
    df = load_csv(data_path)
    total_rows = len(df)
    roles_found = sorted(df["role"].unique())
    print(f"Loaded {total_rows:,} rows | roles found: {roles_found}")

    precomputed = all(f in df.columns for f in FEATURE_ORDER)
    print(f"Feature columns pre-computed in CSV: {precomputed}\n")

    # ------------------------------------------------------------------
    # Per-role training loop
    # ------------------------------------------------------------------
    summary_rows = []

    for role in ROLES:
        role_df = df[df["role"] == role]
        n_rows = len(role_df)
        n_users = role_df["user_id"].nunique() if n_rows > 0 else 0

        if n_rows == 0:
            print(f"[{role:<8}] No data - skipping.")
            summary_rows.append({
                "role": role, "rows": 0, "windows": 0,
                "anomaly_pct": "N/A", "silhouette": "N/A",
            })
            continue

        print(f"[{role:<8}] {n_rows:,} rows, {n_users} users -- building feature matrix ...")
        X = build_feature_matrix(df, role)
        n_windows = len(X)
        print(f"[{role:<8}] Feature matrix shape: {X.shape}")

        n_samples = min(256, n_windows)
        model = IsolationForest(
            n_estimators=200,
            contamination=0.08,
            random_state=42,
            max_samples=n_samples,
        )
        model.fit(X)

        # Predict: -1 = anomaly, 1 = normal
        labels = model.predict(X)
        n_anomalies = int((labels == -1).sum())
        anomaly_rate = n_anomalies / n_windows if n_windows > 0 else 0.0
        anomaly_pct = f"{anomaly_rate * 100:.1f}%"

        # Silhouette Score -- meaningful only when both classes are present
        unique_labels = np.unique(labels)
        if len(unique_labels) >= 2 and n_windows >= 2:
            sil = silhouette_score(X, labels)
            sil_str = f"{sil:.4f}"
        else:
            sil = None
            sil_str = "N/A (1 class)"

        # Save model
        pkl_path = output_dir / f"{role}_isolation_forest.pkl"
        joblib.dump(model, pkl_path)
        print(f"[{role:<8}] Saved -> {pkl_path}\n")

        summary_rows.append({
            "role": role,
            "rows": n_rows,
            "windows": n_windows,
            "anomaly_pct": anomaly_pct,
            "silhouette": sil_str,
        })

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    sep = "=" * 68
    print(sep)
    print("TRAINING SUMMARY")
    print(sep)
    print(f"{'Role':<10} {'Rows':>8} {'Windows':>9} {'Anomaly%':>10} {'Silhouette':>13}")
    print("-" * 68)
    for r in summary_rows:
        print(
            f"{r['role']:<10} {r['rows']:>8,} {r['windows']:>9} "
            f"{r['anomaly_pct']:>10} {r['silhouette']:>13}"
        )
    print(sep)
    print(f"\nOutput directory : {output_dir.resolve()}")
    print(f"Total rows used  : {total_rows:,}")
    print("Done.")


if __name__ == "__main__":
    main()
