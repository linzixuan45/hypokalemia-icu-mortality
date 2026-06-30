#!/usr/bin/env python3
"""
Build t₀ cohort ID lists and manifest.

Uses data/mimic_t0_labs.parquet when present; otherwise Excel proxy per MC1_spec §3.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
T0_LABS_PATH = ROOT / "data" / "mimic_t0_labs.parquet"
SEVERITY_PATH = ROOT / "data" / "mimic_severity_scores.parquet"
OUT = ROOT / "result" / "analysis"
COHORT_DIR = OUT / "cohorts"
RANDOM_STATE = 42
LOS_ICU_MIN_DAYS = 1.0  # >= 24 h primary analysis

import sys

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dataset import (
    MIMIC3_THRESHOLD,
    MISSING_THRESHOLD,
    encoder_gender,
    encoder_race,
)


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def load_lasso_features(n: int = 20) -> list[str]:
    path = ROOT / "config" / "low_k_lasso_feature.csv"
    feats = pd.read_csv(path, header=None)[0].tolist()[:n]
    return feats


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_k")
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_k")
    return m3, m4


def clean_raw(m3: pd.DataFrame, m4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m3c = m3.dropna(thresh=m3.shape[0] * MIMIC3_THRESHOLD, axis=1)
    m4c = m4.dropna(thresh=m4.shape[0] * MISSING_THRESHOLD, axis=1)
    return m3c, m4c


def apply_base_filters(df: pd.DataFrame, los_icu_min_days: float = LOS_ICU_MIN_DAYS) -> pd.DataFrame:
    out = df.copy()
    if "admission_age" in out.columns:
        out["admission_age"] = out["admission_age"].clip(18, 100)
    if "race" in out.columns:
        out = encoder_race(out)
    if "gender" in out.columns:
        out = encoder_gender(out)
    if "los_icu" in out.columns:
        out = out[out["los_icu"] >= los_icu_min_days]
    return out


def hypokalemia_stratum_proxy(df: pd.DataFrame) -> pd.Series:
    k1 = pd.to_numeric(df.get("potassium_1st", np.nan), errors="coerce")
    kmin = pd.to_numeric(df.get("potassium_min", np.nan), errors="coerce")
    admission = (k1 < 3.5) & k1.notna()
    acquired = (~admission) & (kmin < 3.5)
    return pd.Series(
        np.where(admission, "admission", np.where(acquired, "acquired", "unknown")),
        index=df.index,
    )


def outcome_7d_from_t0(df: pd.DataFrame) -> pd.Series:
    """7-day mortality from t₀; uses hours_icu_to_t0 when parquet merged."""
    expired = pd.to_numeric(df["hospital_expire_flag"], errors="coerce").fillna(0).astype(int)
    if "hosp_survival_days" in df.columns:
        days_from_adm = pd.to_numeric(df["hosp_survival_days"], errors="coerce").fillna(999)
    elif "icu_survival_days" in df.columns:
        raw = pd.to_numeric(df["icu_survival_days"], errors="coerce").fillna(9999)
        days_from_adm = np.where(raw > 30, raw / 24.0, raw)
        days_from_adm = pd.Series(days_from_adm, index=df.index)
    else:
        days_from_adm = pd.Series(999.0, index=df.index)

    if "hours_icu_to_t0" in df.columns:
        hours = pd.to_numeric(df["hours_icu_to_t0"], errors="coerce").fillna(0)
        days_from_t0 = days_from_adm - (hours / 24.0)
    else:
        days_from_t0 = days_from_adm

    return ((expired == 1) & (days_from_t0 <= 7)).astype(int)


def attach_outcomes(raw: pd.DataFrame, cleaned: pd.DataFrame, t0_source: str) -> pd.DataFrame:
    out = cleaned.copy()
    for col in ["hospital_expire_flag", "hosp_survival_days", "icu_survival_days"]:
        if col not in out.columns and col in raw.columns:
            out[col] = raw.loc[out.index, col]
    out["outcome_7d"] = outcome_7d_from_t0(out)
    if "hypokalemia_stratum" not in out.columns or out["hypokalemia_stratum"].isna().all():
        out["hypokalemia_stratum"] = hypokalemia_stratum_proxy(raw).loc[out.index]
    out["t0_source"] = t0_source
    return out


def merge_t0_labs(m3: pd.DataFrame, m4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if not T0_LABS_PATH.exists():
        return m3, m4, "excel_proxy"

    labs = pd.read_parquet(T0_LABS_PATH)
    id_col_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_col_m4 = "stay_id" if "stay_id" in m4.columns else "subject_id"
    join_col = "stay_id" if "stay_id" in labs.columns else id_col_m3

    lab_cols = [
        c
        for c in [
            join_col,
            "t0_charttime",
            "hypokalemia_stratum",
            "hours_icu_to_t0",
            "potassium_at_t0",
            "source",
        ]
        if c in labs.columns
    ]
    labs_sub = labs[lab_cols].drop_duplicates(subset=[join_col])

    m3 = m3.merge(labs_sub, left_on=id_col_m3, right_on=join_col, how="left", suffixes=("", "_t0"))
    m4 = m4.merge(labs_sub, left_on=id_col_m4, right_on=join_col, how="left", suffixes=("", "_t0"))
    return m3, m4, "parquet"


def feature_complete(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    cols = [c for c in features if c in df.columns] + ["outcome_7d"]
    sub = df[cols].copy()
    sub = sub.dropna(subset=[c for c in features if c in sub.columns])
    return df.loc[sub.index]


def assign_splits(m3: pd.DataFrame, m4: pd.DataFrame, features: list[str]) -> dict:
    m3f = feature_complete(apply_base_filters(m3), features)
    m4f = feature_complete(apply_base_filters(m4), features)

    y = m3f["outcome_7d"]
    train_idx, test_idx = train_test_split(
        m3f.index, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    id_col_m3 = "icustay_id" if "icustay_id" in m3f.columns else "subject_id"
    id_col_m4 = "subject_id"

    splits = {
        "mimic3_train": m3f.loc[train_idx, [id_col_m3, "outcome_7d", "hypokalemia_stratum"]],
        "mimic3_test": m3f.loc[test_idx, [id_col_m3, "outcome_7d", "hypokalemia_stratum"]],
        "mimic4_val": m4f[[id_col_m4, "outcome_7d", "hypokalemia_stratum"]],
        "legacy_mimic3_test": m3f.loc[test_idx].copy(),
        "legacy_mimic4_val": m4f.copy(),
        "mimic3_test_indices": pd.Series(test_idx, name="index"),
        "mimic3_train_indices": pd.Series(train_idx, name="index"),
    }
    return splits, m3f, m4f


def export_severity_proxy(m3f: pd.DataFrame, m4f: pd.DataFrame) -> None:
    """Write sofa-only severity file from Excel when SQL export absent."""
    if SEVERITY_PATH.exists():
        sev = pd.read_parquet(SEVERITY_PATH)
        if sev.get("source", pd.Series(["excel_proxy"])).iloc[0] == "mimic_sql":
            return
        if sev["apache_ii"].notna().any():
            return
    rows = []
    id_col_m3 = "icustay_id" if "icustay_id" in m3f.columns else "subject_id"
    for tag, df, idc in [("mimic3", m3f, id_col_m3), ("mimic4", m4f, "subject_id")]:
        if "sofa_score" not in df.columns:
            continue
        for _, r in df.iterrows():
            rows.append(
                {
                    "cohort": tag,
                    "stay_id": r.get(idc),
                    "sofa_at_t0": r.get("sofa_score"),
                    "apache_ii": np.nan,
                    "saps_ii": np.nan,
                    "source": "excel_proxy",
                }
            )
    if rows:
        pd.DataFrame(rows).to_parquet(SEVERITY_PATH, index=False)


def _severity_source() -> str:
    if not SEVERITY_PATH.exists():
        return "excel_proxy_sofa_only"
    sev = pd.read_parquet(SEVERITY_PATH)
    src = sev["source"].iloc[0] if "source" in sev.columns else "unknown"
    if sev.get("apache_ii", pd.Series(dtype=float)).notna().any():
        return "mimic_sql"
    if src == "excel_proxy":
        return "excel_proxy_sofa_only"
    return str(src)


def write_manifest(t0_source: str, n_train: int, n_test: int, n_val: int) -> None:
    manifest = {
        "pipeline": "hypokalemia_mortality",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mc1_spec_status": "finalized_2026-05-24",
        "git_commit": _git_commit(),
        "random_state": RANDOM_STATE,
        "los_icu_min_days": LOS_ICU_MIN_DAYS,
        "downsample_ratio": 0,
        "t0_source": t0_source,
        "outcome": "death_within_7d_from_t0",
        "cohort_counts": {
            "mimic3_train": n_train,
            "mimic3_test": n_test,
            "mimic4_val": n_val,
        },
        "severity_source": _severity_source(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    features = load_lasso_features(20)
    m3_raw, m4_raw = load_raw()
    m3_clean, m4_clean = clean_raw(m3_raw, m4_raw)
    m3, m4, t0_source = merge_t0_labs(m3_clean, m4_clean)
    m3 = attach_outcomes(m3_raw, m3, t0_source)
    m4 = attach_outcomes(m4_raw, m4, t0_source)
    splits, m3f, m4f = assign_splits(m3, m4, features)

    COHORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in splits.items():
        if name.endswith("_indices"):
            df.to_csv(COHORT_DIR / f"{name}.csv", index=False)
        elif name.startswith("legacy"):
            df.to_pickle(COHORT_DIR / f"{name}.pkl")
        else:
            df.to_csv(COHORT_DIR / f"{name}_ids.csv", index=False)

    export_severity_proxy(m3f, m4f)
    write_manifest(
        t0_source,
        len(splits["mimic3_train"]),
        len(splits["mimic3_test"]),
        len(splits["mimic4_val"]),
    )
    print(f"t0_source={t0_source}")
    print(f"train={len(splits['mimic3_train'])} test={len(splits['mimic3_test'])} val={len(splits['mimic4_val'])}")
    print(f"manifest -> {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
