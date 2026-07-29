"""
Ablation Study: Global Isolation Forest vs Per-Role Isolation Forest
====================================================================

Compares a single global IsolationForest (trained on all roles combined)
against fresh per-role models retrained on the same 80% training split,
saved to project/backend/models_ablation/.  Production models in
project/backend/models/ are never touched.

Both approaches train on the identical 80% split and are evaluated on the
identical untouched 20% test split - leakage-free comparison.

Dataset
-------
  dataset/main_dataset/09_audit_logs_synthetic.csv
  - 5,000 rows, 8 pre-computed feature columns, ground-truth label: is_anomaly
  - role values: admin, doctor, nurse, patient  (lower-case in CSV)

Usage
-----
  cd project/backend
  python ablation_study.py
  python ablation_study.py --data ../../dataset/main_dataset/09_audit_logs_synthetic_extended.csv --models-dir models_ablation_extended
"""

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent   # project/backend/
REPO_ROOT  = SCRIPT_DIR.parent.parent          # Capstone/

_DEFAULT_DATA       = REPO_ROOT / "dataset" / "main_dataset" / "09_audit_logs_synthetic.csv"
_DEFAULT_MODELS_DIR = SCRIPT_DIR / "models_ablation"

# ---------------------------------------------------------------------------
# Constants -must stay in sync with train.py / anomaly_service.py
# ---------------------------------------------------------------------------

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

# Role names as they appear in the CSV (lower-case) and in the .pkl filenames (title-case)
ROLES_CSV   = ["admin", "doctor", "nurse", "patient"]
ROLES_TITLE = ["Admin", "Doctor", "Nurse", "Patient"]

CONTAMINATION = 0.08   # matches train.py
N_ESTIMATORS  = 200    # matches train.py
RANDOM_STATE  = 42     # matches IsolationForest seed in train.py
TEST_SIZE     = 0.20   # 80/20 split -no split exists in train.py; we introduce one here


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_pred_to_binary(preds: np.ndarray) -> np.ndarray:
    """Convert IsolationForest output (-1=anomaly, 1=normal) -> (1=anomaly, 0=normal)."""
    return (preds == -1).astype(int)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Return precision, recall, F1, and false positive rate.

    FPR = FP / (FP + TN)  -computed manually because sklearn has no
    single-threshold FPR function.

    Returns NaN for any metric that is undefined (e.g. no positives in y_true).
    """
    if len(y_true) == 0 or y_true.sum() == len(y_true) or y_true.sum() == 0:
        # Edge case: all-anomaly or all-normal slice makes some metrics undefined.
        return {"precision": float("nan"), "recall": float("nan"), "f1": float("nan"), "fpr": float("nan")}

    try:
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec  = recall_score(y_true, y_pred, zero_division=0)
        f1   = f1_score(y_true, y_pred, zero_division=0)
    except Exception:
        prec = rec = f1 = float("nan")

    # FPR from confusion matrix
    try:
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else float("nan")
    except Exception:
        fpr = float("nan")

    return {"precision": prec, "recall": rec, "f1": f1, "fpr": fpr}


def fmt(v: float, pct: bool = True) -> str:
    """Format a metric value for table display."""
    if np.isnan(v):
        return "  N/A "
    return f"{v * 100:5.1f}%" if pct else f"{v:.4f}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Ablation study: global vs per-role IsolationForest.")
    parser.add_argument("--data",       default=str(_DEFAULT_DATA),       metavar="CSV",
                        help="Path to audit-log CSV with is_anomaly column.")
    parser.add_argument("--models-dir", default=str(_DEFAULT_MODELS_DIR), metavar="DIR",
                        help="Directory to write ablation .pkl files (default: models_ablation/).")
    args = parser.parse_args()

    DATA_PATH           = Path(args.data)
    MODELS_ABLATION_DIR = Path(args.models_dir)

    # -----------------------------------------------------------------------
    # 1. Load dataset
    # -----------------------------------------------------------------------
    if not DATA_PATH.exists():
        print(f"ERROR: Dataset not found at {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    # Normalise role to lower-case (CSV already uses lower-case, but be safe)
    df["role"] = df["role"].astype(str).str.strip().str.lower()

    missing_feats = [f for f in FEATURE_ORDER if f not in df.columns]
    if missing_feats:
        print(f"ERROR: Missing feature columns: {missing_feats}", file=sys.stderr)
        sys.exit(1)
    if "is_anomaly" not in df.columns:
        print("ERROR: 'is_anomaly' column not found -ground-truth labels required.", file=sys.stderr)
        sys.exit(1)

    total_rows    = len(df)
    total_anomaly = int(df["is_anomaly"].sum())
    print(f"Loaded {total_rows:,} rows | anomalies: {total_anomaly} "
          f"({total_anomaly / total_rows * 100:.1f}%)")
    print(f"Roles found: {sorted(df['role'].unique())}\n")

    X_all = df[FEATURE_ORDER].to_numpy(dtype=float)
    y_all = df["is_anomaly"].to_numpy(dtype=int)

    # -----------------------------------------------------------------------
    # 2. Train / test split
    #    Stratified on is_anomaly so both splits preserve the anomaly ratio.
    # -----------------------------------------------------------------------
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X_all, y_all, df.index.to_numpy(),
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_all,
    )

    df_test = df.loc[idx_test].copy()
    df_test["_y_true"] = y_test

    print(f"Train split : {len(X_train):,} rows")
    print(f"Test split  : {len(X_test):,} rows  "
          f"(anomalies: {int(y_test.sum())}, {y_test.mean() * 100:.1f}%)\n")

    # -----------------------------------------------------------------------
    # 3. Train global Isolation Forest on the full training split
    # -----------------------------------------------------------------------
    print("Training global IsolationForest on combined training data ...")
    global_model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        max_samples=min(256, len(X_train)),
    )
    global_model.fit(X_train)
    print("Global model trained.\n")

    # -----------------------------------------------------------------------
    # 4. Train fresh per-role IsolationForest models on the 80% train split,
    #    one model per role, trained only on that role's rows within X_train.
    #    Saved to models_ablation/ -production models/ is never touched.
    # -----------------------------------------------------------------------
    MODELS_ABLATION_DIR.mkdir(parents=True, exist_ok=True)
    per_role_models = {}
    df_train = df.loc[idx_train].copy()
    print("Training per-role IsolationForest models on 80% train split ...")
    for role_csv, role_title in zip(ROLES_CSV, ROLES_TITLE):
        role_mask_train = df_train["role"].to_numpy() == role_csv
        X_role_train = X_train[role_mask_train]
        n_role_train = len(X_role_train)
        if n_role_train == 0:
            print(f"  [{role_title:<8}] No training rows -skipping.")
            continue
        model = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=CONTAMINATION,
            random_state=RANDOM_STATE,
            max_samples=min(256, n_role_train),
        )
        model.fit(X_role_train)
        per_role_models[role_csv] = model
        pkl_path = MODELS_ABLATION_DIR / f"{role_title}_isolation_forest_ablation.pkl"
        joblib.dump(model, pkl_path)
        print(f"  [{role_title:<8}] {n_role_train:,} train rows -> saved {pkl_path.name}")
    print()

    # -----------------------------------------------------------------------
    # 5. Evaluate both approaches per role and in aggregate
    # -----------------------------------------------------------------------
    results = []   # one dict per role

    for role_csv in ROLES_CSV:
        mask       = df_test["role"] == role_csv
        df_role    = df_test[mask]
        n_test     = len(df_role)
        n_anomaly  = int(df_role["_y_true"].sum())

        if n_test == 0:
            results.append({
                "role": role_csv, "n_test": 0, "n_anomaly": 0,
                "global": {k: float("nan") for k in ("precision","recall","f1","fpr")},
                "per_role": {k: float("nan") for k in ("precision","recall","f1","fpr")},
            })
            continue

        X_role = df_role[FEATURE_ORDER].to_numpy(dtype=float)
        y_role = df_role["_y_true"].to_numpy(dtype=int)

        # --- Global model predictions on this role's test rows
        global_preds = iso_pred_to_binary(global_model.predict(X_role))
        global_metrics = compute_metrics(y_role, global_preds)

        # --- Per-role model predictions
        model = per_role_models.get(role_csv)
        if model is not None:
            pr_preds   = iso_pred_to_binary(model.predict(X_role))
            pr_metrics = compute_metrics(y_role, pr_preds)
        else:
            pr_metrics = {k: float("nan") for k in ("precision","recall","f1","fpr")}

        results.append({
            "role":     role_csv,
            "n_test":   n_test,
            "n_anomaly": n_anomaly,
            "global":   global_metrics,
            "per_role": pr_metrics,
        })

    # Aggregate row (all roles combined)
    global_all_preds   = iso_pred_to_binary(global_model.predict(X_test))
    global_agg         = compute_metrics(y_test, global_all_preds)

    # Per-role aggregate: stitch predictions in the correct order
    pr_agg_pred = np.full(len(y_test), -1, dtype=int)
    test_roles  = df_test["role"].to_numpy()
    for r in results:
        role_csv  = r["role"]
        model     = per_role_models.get(role_csv)
        if model is None:
            continue
        role_mask = test_roles == role_csv
        if role_mask.sum() > 0:
            pr_agg_pred[role_mask] = iso_pred_to_binary(model.predict(X_test[role_mask]))

    # Only include rows where a per-role model was available
    agg_mask   = pr_agg_pred >= 0
    pr_agg     = compute_metrics(y_test[agg_mask], pr_agg_pred[agg_mask])

    # -----------------------------------------------------------------------
    # 6 & 7. Print comparison table
    # -----------------------------------------------------------------------

    SEP  = "=" * 108
    SEP2 = "-" * 108

    print(SEP)
    print("  ABLATION STUDY: Global IsolationForest  vs  Per-Role IsolationForest")
    print(SEP)
    print()

    # Column headers
    header1 = (
        f"  {'Role':<28}  "
        f"{'---- Global Model ----':^35}  "
        f"{'-- Per-Role Model --':^35}"
    )
    header2 = (
        f"  {'':28}  "
        f"{'Prec':>7}  {'Rec':>7}  {'F1':>7}  {'FPR':>7}    "
        f"{'Prec':>7}  {'Rec':>7}  {'F1':>7}  {'FPR':>7}"
    )

    print(header1)
    print(header2)
    print(SEP2)

    small_sample_flags = []

    for r in results:
        role_label = f"{r['role'].title()} (n={r['n_test']}, anom={r['n_anomaly']})"
        g = r["global"]
        p = r["per_role"]

        line = (
            f"  {role_label:<28}  "
            f"{fmt(g['precision']):>7}  {fmt(g['recall']):>7}  {fmt(g['f1']):>7}  {fmt(g['fpr']):>7}    "
            f"{fmt(p['precision']):>7}  {fmt(p['recall']):>7}  {fmt(p['f1']):>7}  {fmt(p['fpr']):>7}"
        )
        print(line)

        if r["n_anomaly"] < 10:
            small_sample_flags.append((r["role"].title(), r["n_test"], r["n_anomaly"]))

    print(SEP2)

    # Aggregate row
    agg_label = f"ALL ROLES (n={len(y_test)}, anom={int(y_test.sum())})"
    agg_line = (
        f"  {agg_label:<28}  "
        f"{fmt(global_agg['precision']):>7}  {fmt(global_agg['recall']):>7}  "
        f"{fmt(global_agg['f1']):>7}  {fmt(global_agg['fpr']):>7}    "
        f"{fmt(pr_agg['precision']):>7}  {fmt(pr_agg['recall']):>7}  "
        f"{fmt(pr_agg['f1']):>7}  {fmt(pr_agg['fpr']):>7}"
    )
    print(agg_line)
    print(SEP)

    # -----------------------------------------------------------------------
    # 8. Small-sample flags
    # -----------------------------------------------------------------------
    print()
    if small_sample_flags:
        print("  (!)  SMALL-SAMPLE WARNINGS (< 10 anomalies in test set -metric reliability reduced):")
        for role_title, n_test, n_anom in small_sample_flags:
            print(f"     * {role_title}: {n_anom} anomaly sample(s) out of {n_test} test rows")
    else:
        print("  OK  All roles have >= 10 anomalies in the test set.")

    print()
    print("  Metric definitions:")
    print("    Prec = TP / (TP + FP)   |  Rec  = TP / (TP + FN)")
    print("    F1   = harmonic mean(Prec, Rec)")
    print("    FPR  = FP / (FP + TN)   |  IsolationForest: predict() == -1 -> anomaly")
    print()


if __name__ == "__main__":
    main()
