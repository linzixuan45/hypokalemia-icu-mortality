"""
Subgroup analysis for the hypokalemia mortality prediction paper.
Computes AUROC + 95% DeLong CI for Ensemble_Stacking across clinically
relevant patient subgroups, producing Supplementary Table S6.
"""
from __future__ import annotations

import pickle
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from external_cohort_data import (
    external_cohorts_available,
    load_corrected_f3_feature_table,
    load_corrected_nh_feature_table,
)

OUT = ROOT / "result" / "analysis"
TABLES = OUT / "tables"
MIN_POS, MIN_NEG = 5, 5


def _compute_midrank(x):
    j = np.argsort(x)
    z = x[j]
    n = len(x)
    rank = np.zeros(n)
    i = 0
    while i < n:
        k = i
        while k < n - 1 and z[k + 1] == z[k]:
            k += 1
        for t in range(i, k + 1):
            rank[t] = 0.5 * (i + k) + 1
        i = k + 1
    rank_out = np.empty(n)
    rank_out[j] = rank
    return rank_out


def delong_ci(y_true, y_score, alpha=0.05):
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    pos, neg = y_score[y_true == 1], y_score[y_true == 0]
    m, n = len(pos), len(neg)
    if m < MIN_POS or n < MIN_NEG:
        return np.nan, np.nan, np.nan
    all_scores = np.concatenate([pos, neg])
    midranks = _compute_midrank(all_scores)
    auc = (np.sum(midranks[:m]) - m * (m + 1) / 2) / (m * n)
    v10 = np.array([(np.sum(neg < p) + 0.5 * np.sum(neg == p)) / n for p in pos])
    v01 = np.array([(np.sum(pos > q) + 0.5 * np.sum(pos == q)) / m for q in neg])
    s10 = np.var(v10, ddof=1) if m > 1 else 0.0
    s01 = np.var(v01, ddof=1) if n > 1 else 0.0
    se = np.sqrt(s10 / m + s01 / n)
    z = stats.norm.ppf(1 - alpha / 2)
    return auc, max(0.0, auc - z * se), min(1.0, auc + z * se)


def load_evaluation_cohorts():
    """Load evaluation cohorts aligned with result/analysis/cohorts ID lists."""
    data_path = ROOT / "data" / "mimic_dataset.xlsx"
    cohort_dir = OUT / "cohorts"
    mimic3_raw = pd.read_excel(data_path, sheet_name="mimic3_low_k")
    mimic4_raw = pd.read_excel(data_path, sheet_name="mimic4_low_k")
    test_ids = pd.read_csv(cohort_dir / "mimic3_test_ids.csv")
    val_ids = pd.read_csv(cohort_dir / "mimic4_val_ids.csv")
    id_m3 = "icustay_id" if "icustay_id" in test_ids.columns else "subject_id"
    test_raw = mimic3_raw.merge(test_ids, on=id_m3, how="inner")
    val_raw = mimic4_raw.merge(val_ids, on="subject_id", how="inner")
    return val_raw, test_raw


def _pred_pkl_path(split: str, model_tag: str = "8_features") -> Path:
    for path in (
        OUT / "preds" / model_tag / f"{split}_preds.pkl",
        OUT / "preds" / f"{model_tag}_{split}_preds.pkl",
    ):
        if path.exists():
            return path
    raise FileNotFoundError(f"No prediction file for split={split} tag={model_tag}")


def _load_mimic_pred(split: str, model_tag: str = "8_features") -> dict:
    with open(_pred_pkl_path(split, model_tag), "rb") as f:
        data = pickle.load(f)
    d = data[-1]
    if isinstance(d, dict) and d.get("model_name") != "Ensemble_Stacking":
        d = next(x for x in data if x.get("model_name") == "Ensemble_Stacking")
    return {
        "y_true": np.array(d["lable"]),
        "y_prob": np.array(d["pred_prob"]),
    }


def load_predictions(model_tag: str = "8_features"):
    """Load MIMIC predictions from pkl; score F3/NH when external data exist."""
    preds = {
        "val": _load_mimic_pred("val", model_tag),
        "test": _load_mimic_pred("test", model_tag),
    }

    weight_dir = OUT / "model_weight" / model_tag
    with open(weight_dir / "model_weight.pkl", "rb") as f:
        bundle = pickle.load(f)
    model = bundle.get("Ensemble_Stacking") or bundle.get("model")
    imp = bundle["imputer"]
    with open(weight_dir / "stand_encoder.pkl", "rb") as f:
        scaler = pickle.load(f)
    feat8 = list(bundle.get("features", scaler.feature_names_in_))

    def score_external(df, y_true):
        x_raw = df[feat8].copy()
        x_raw["is_noninvasive_ventilator"] = (
            pd.to_numeric(x_raw["is_noninvasive_ventilator"], errors="coerce") >= 0.5
        ).astype(int)
        x_i = pd.DataFrame(imp.transform(x_raw), columns=feat8)
        scaled = pd.DataFrame(scaler.transform(x_i), columns=feat8)
        y_prob = model.predict_proba(scaled)[:, 1]
        return {
            "y_true": np.asarray(y_true, dtype=int),
            "y_prob": np.asarray(y_prob, dtype=float),
        }

    if external_cohorts_available():
        f3 = load_corrected_f3_feature_table()
        nh = load_corrected_nh_feature_table()
        preds["F3"] = score_external(f3, (f3["hospital_expire_flag"] == 1).astype(int))
        preds["NH"] = score_external(nh, nh["hospital_expire_flag"].astype(int))

    return preds


def define_subgroups(df):
    """Return {subgroup_label: boolean_mask} for variables present in df."""
    groups = {}

    if "admission_age" in df.columns:
        groups["Age <= 65"] = df["admission_age"].values <= 65
        groups["Age > 65"] = df["admission_age"].values > 65

    if "gender" in df.columns:
        g = df["gender"].values
        if g.dtype == object or (len(g) and isinstance(g[0], str)):
            groups["Male"] = np.array([str(x).upper().startswith("M") or x == 0 for x in g])
            groups["Female"] = np.array([str(x).upper().startswith("F") or x == 1 for x in g])
        else:
            groups["Male"] = g == 0
            groups["Female"] = g == 1
    elif "性别" in df.columns:
        groups["Male"] = df["性别"].values == "男"
        groups["Female"] = df["性别"].values == "女"

    if "sofa_score" in df.columns:
        median_sofa = np.nanmedian(df["sofa_score"].values)
        groups[f"SOFA <= {median_sofa:.0f}"] = df["sofa_score"].values <= median_sofa
        groups[f"SOFA > {median_sofa:.0f}"] = df["sofa_score"].values > median_sofa

    if "potassium_min" in df.columns:
        k = df["potassium_min"].values
        groups["K+ < 3.0 mmol/L"] = k < 3.0
        groups["K+ 3.0-3.5 mmol/L"] = (k >= 3.0) & (k < 3.5)

    if "is_ventilator" in df.columns:
        v = df["is_ventilator"].values
        groups["Ventilated"] = v == 1
        groups["Not ventilated"] = v == 0
    elif "is_noninvasive_ventilator" in df.columns:
        v = df["is_noninvasive_ventilator"].values
        groups["NIV used"] = v == 1
        groups["NIV not used"] = v == 0

    vaso_cols = [c for c in ["norepinephrine_used", "vasopressin_used", "dopamine_used"] if c in df.columns]
    if vaso_cols:
        any_vaso = df[vaso_cols].max(axis=1).values == 1
        groups["Vasopressors"] = any_vaso
        groups["No vasopressors"] = ~any_vaso

    if "creatinine_mean" in df.columns:
        cr = df["creatinine_mean"].values
        groups["Renal dysfunction"] = cr > 1.5
        groups["No renal dysfunction"] = cr <= 1.5

    return groups


def run_subgroup_analysis(model_tag: str = "8_features") -> pd.DataFrame:
    print("=" * 80)
    print(f"  Subgroup Analysis — Ensemble_Stacking AUROC + 95% DeLong CI ({model_tag})")
    print("=" * 80)

    print("\n[1] Loading evaluation cohort splits...")
    val_raw, test_raw = load_evaluation_cohorts()
    preds = load_predictions(model_tag=model_tag)

    print(f"    val  (MIMIC-IV): raw={len(val_raw)}, pkl={len(preds['val']['y_true'])}")
    print(f"    test (MIMIC-III): raw={len(test_raw)}, pkl={len(preds['test']['y_true'])}")
    if external_cohorts_available():
        print(f"    NH: pkl={len(preds['NH']['y_true'])}")
        print(f"    F3: pkl={len(preds['F3']['y_true'])}")

    assert len(val_raw) == len(preds["val"]["y_true"])
    assert len(test_raw) == len(preds["test"]["y_true"])

    cohorts = {
        "MIMIC-IV (val)": (val_raw.reset_index(drop=True), preds["val"]["y_true"], preds["val"]["y_prob"]),
        "MIMIC-III (test)": (test_raw.reset_index(drop=True), preds["test"]["y_true"], preds["test"]["y_prob"]),
    }
    if external_cohorts_available():
        f3 = load_corrected_f3_feature_table()
        nh = load_corrected_nh_feature_table()
        cohorts["Third Xiangya (F3)"] = (
            f3.reset_index(drop=True),
            preds["F3"]["y_true"],
            preds["F3"]["y_prob"],
        )
        cohorts["Nanhua (NH)"] = (
            nh.reset_index(drop=True),
            preds["NH"]["y_true"],
            preds["NH"]["y_prob"],
        )

    print("\n[2] Computing subgroup AUROCs...\n")
    rows = []
    for cohort_name, (raw_df, y_true, y_prob) in cohorts.items():
        auc, lo, hi = delong_ci(y_true, y_prob)
        rows.append(
            {
                "Cohort": cohort_name,
                "Subgroup": "Overall",
                "n": len(y_true),
                "Events": int(np.sum(y_true == 1)),
                "AUROC": auc,
                "CI_lower": lo,
                "CI_upper": hi,
            }
        )
        for sg_name, mask in define_subgroups(raw_df).items():
            mask = np.asarray(mask)
            if mask.sum() == 0:
                continue
            yt = y_true[mask]
            yp = y_prob[mask]
            auc_sg, lo_sg, hi_sg = delong_ci(yt, yp)
            rows.append(
                {
                    "Cohort": cohort_name,
                    "Subgroup": sg_name,
                    "n": len(yt),
                    "Events": int(np.sum(yt == 1)),
                    "AUROC": auc_sg,
                    "CI_lower": lo_sg,
                    "CI_upper": hi_sg,
                }
            )

    results = pd.DataFrame(rows)

    def fmt(row):
        if pd.isna(row["AUROC"]):
            return "N/A (insufficient events)"
        return f"{row['AUROC']:.3f} ({row['CI_lower']:.3f}\u2013{row['CI_upper']:.3f})"

    results["AUROC (95% CI)"] = results.apply(fmt, axis=1)

    TABLES.mkdir(parents=True, exist_ok=True)
    out_path = TABLES / "table_s6_subgroup_full.csv"
    results.to_csv(out_path, index=False)
    print(f"\n  Results saved to {out_path}")

    return results


if __name__ == "__main__":
    run_subgroup_analysis()
