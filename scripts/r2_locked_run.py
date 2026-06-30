#!/usr/bin/env python3
"""R2 locked run: train 20/8-feature ensembles without undersampling; write preds + tables."""
from __future__ import annotations

import json
import pickle
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from dataset import (
    MIMIC3_MISSING_FEATURES,
    MIMIC3_THRESHOLD,
    MISSING_THRESHOLD,
    encoder_gender,
    encoder_race,
)
from external_cohort_data import (
    external_cohorts_available,
    load_corrected_f3_feature_table,
    load_corrected_nh_feature_table,
)

OUT = ROOT / "result" / "r2_locked"
PREDS = OUT / "preds"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
COHORT = OUT / "cohorts"
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
RANDOM_STATE = 42
FEAT8 = [
    "rdw_mean",
    "wbc_min",
    "admission_age",
    "spo2_min",
    "lactate_min",
    "is_noninvasive_ventilator",
    "platelet_min",
    "aniongap_1st",
]


def load_lasso20() -> list[str]:
    p = ROOT / "config" / "low_k_lasso_feature.csv"
    return pd.read_csv(p, header=None)[0].tolist()[:20]


def delong_ci(y_true, y_score, alpha=0.05):
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    pos, neg = y_score[y_true == 1], y_score[y_true == 0]
    m, n = len(pos), len(neg)
    if m < 5 or n < 5:
        return np.nan, np.nan, np.nan
    all_s = np.concatenate([pos, neg])
    j = np.argsort(all_s)
    z = all_s[j]
    rank = np.zeros(m + n)
    i = 0
    while i < m + n:
        k = i
        while k < m + n - 1 and z[k + 1] == z[k]:
            k += 1
        for t in range(i, k + 1):
            rank[t] = 0.5 * (i + k) + 1
        i = k + 1
    rank_out = np.empty(m + n)
    rank_out[j] = rank
    auc = (np.sum(rank_out[:m]) - m * (m + 1) / 2) / (m * n)
    v10 = np.array([(np.sum(neg < pos[i]) + 0.5 * np.sum(neg == pos[i])) / n for i in range(m)])
    v01 = np.array([(np.sum(pos > neg[j]) + 0.5 * np.sum(pos == neg[j])) / m for j in range(n)])
    se = np.sqrt((np.var(v10, ddof=1) if m > 1 else 0) / m + (np.var(v01, ddof=1) if n > 1 else 0) / n)
    zv = stats.norm.ppf(1 - alpha / 2)
    return auc, max(0.0, auc - zv * se), min(1.0, auc + zv * se)


def prep_frame(
    df: pd.DataFrame,
    features: list[str],
    label_col: str = "outcome_7d",
    los_icu_min: float = 1.0,
) -> pd.DataFrame:
    out = df.copy()
    if "admission_age" in out.columns:
        out["admission_age"] = out["admission_age"].clip(18, 100)
    if "race" in out.columns:
        out = encoder_race(out)
    if "gender" in out.columns:
        out = encoder_gender(out)
    if "los_icu" in out.columns:
        out = out[out["los_icu"] >= los_icu_min]
    cols = [c for c in features if c in out.columns]
    if label_col in out.columns:
        cols = cols + [label_col]
    elif "hospital_expire_flag" in out.columns:
        cols = cols + ["hospital_expire_flag"]
        label_col = "hospital_expire_flag"
    sub = out[cols].dropna()
    if label_col == "outcome_7d" and label_col in sub.columns:
        sub["hospital_expire_flag"] = sub[label_col]
    return sub


def impute_scale(X_train: pd.DataFrame, X_other: list[pd.DataFrame]):
    imp = IterativeImputer(max_iter=5, random_state=RANDOM_STATE)
    tr = pd.DataFrame(imp.fit_transform(X_train), columns=X_train.columns)
    others = [
        pd.DataFrame(imp.transform(x), columns=X_train.columns) for x in X_other
    ]
    scaler = StandardScaler()
    tr_s = pd.DataFrame(scaler.fit_transform(tr), columns=tr.columns)
    oth_s = [
        pd.DataFrame(scaler.transform(o), columns=o.columns) for o in others
    ]
    return tr, tr_s, others, oth_s, imp, scaler


def build_stacking():
    est = [
        ("xgb", XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=RANDOM_STATE, eval_metric="logloss")),
        ("rf", RandomForestClassifier(n_estimators=100, max_depth=5, random_state=RANDOM_STATE)),
        ("lr", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
    ]
    return StackingClassifier(
        estimators=est,
        final_estimator=LogisticRegression(max_iter=1000),
        cv=5,
        stack_method="predict_proba",
    )


def youden_threshold(y_true, y_prob):
    fpr, tpr, thr = roc_curve(y_true, y_prob)
    j = tpr - fpr
    idx = np.argmax(j)
    return float(thr[idx])


def train_and_predict(features: list[str], tag: str):
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_k")
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_k")
    m3 = m3.dropna(thresh=m3.shape[0] * MIMIC3_THRESHOLD, axis=1)
    m4 = m4.dropna(thresh=m4.shape[0] * MISSING_THRESHOLD, axis=1)

    train_ids = pd.read_csv(COHORT / "mimic3_train_ids.csv")
    test_ids = pd.read_csv(COHORT / "mimic3_test_ids.csv")
    val_ids = pd.read_csv(COHORT / "mimic4_val_ids.csv")

    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_m4 = "subject_id"

    # attach outcome_7d from cohort files
    m3 = m3.merge(
        pd.concat([
            train_ids[[id_m3, "outcome_7d"]].assign(_split="train"),
            test_ids[[id_m3, "outcome_7d"]].assign(_split="test"),
        ]),
        on=id_m3,
        how="inner",
    )
    m4 = m4.merge(val_ids[[id_m4, "outcome_7d"]], on=id_m4, how="inner")

    train_df = prep_frame(m3[m3["_split"] == "train"], features)
    test_df = prep_frame(m3[m3["_split"] == "test"], features)
    val_df = prep_frame(m4, features)

    X_train = train_df[features]
    y_train = train_df["hospital_expire_flag"].astype(int)
    X_test = test_df[features]
    y_test = test_df["hospital_expire_flag"].astype(int)
    X_val = val_df[features]
    y_val = val_df["hospital_expire_flag"].astype(int)

    _, X_train_s, _, [X_test_s, X_val_s], imp, scaler = impute_scale(
        X_train, [X_test, X_val]
    )

    model = build_stacking()
    oof = cross_val_predict(
        model, X_train_s, y_train, cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE), method="predict_proba"
    )[:, 1]
    thresh = youden_threshold(y_train, oof)
    model.fit(X_train_s, y_train)

    def pack(y, prob, name):
        pred = (prob >= thresh).astype(int)
        auc, lo, hi = delong_ci(y, prob)
        return {
            "model_name": "Ensemble_Stacking",
            "cohort": name,
            "n": len(y),
            "events": int(np.sum(y)),
            "auroc": auc,
            "auroc_ci_lo": lo,
            "auroc_ci_hi": hi,
            "youden_threshold": thresh,
            "pred_prob": prob.tolist(),
            "pred": pred.tolist(),
            "lable": y.tolist(),
        }

    test_prob = model.predict_proba(X_test_s)[:, 1]
    val_prob = model.predict_proba(X_val_s)[:, 1]

    weight_dir = OUT / "model_weight" / tag
    weight_dir.mkdir(parents=True, exist_ok=True)
    with open(weight_dir / "model_weight.pkl", "wb") as f:
        pickle.dump({"Ensemble_Stacking": model, "imputer": imp, "scaler": scaler, "features": features, "threshold": thresh}, f)

    results = {
        "test": pack(y_test, test_prob, "mimic3_test"),
        "val": pack(y_val, val_prob, "mimic4_val"),
    }
    for k, v in results.items():
        with open(PREDS / f"{tag}_{k}_preds.pkl", "wb") as f:
            pickle.dump([v], f)
    return results, model, imp, scaler, thresh


def infer_external(model, imp, scaler, features, df, label_col="hospital_expire_flag"):
    sub = prep_frame(df, features, label_col=label_col if label_col in df.columns else "hospital_expire_flag")
    if "is_noninvasive_ventilator" in sub.columns:
        sub["is_noninvasive_ventilator"] = (
            pd.to_numeric(sub["is_noninvasive_ventilator"], errors="coerce") >= 0.5
        ).astype(int)
    X = sub[features]
    y = sub["hospital_expire_flag"].astype(int)
    X_i = pd.DataFrame(imp.transform(X), columns=features)
    X_s = pd.DataFrame(scaler.transform(X_i), columns=features)
    prob = model.predict_proba(X_s)[:, 1]
    return y, prob, len(sub), int(y.sum())


def write_table23(res20, res8):
    rows = []
    for feat_tag, res in [("20-feature", res20), ("8-feature", res8)]:
        for split, label in [("test", "MIMIC-III internal"), ("val", "MIMIC-IV temporal")]:
            d = res[split]
            rows.append(
                {
                    "Model": feat_tag,
                    "Cohort": label,
                    "n": d["n"],
                    "Events": d["events"],
                    "AUROC": round(d["auroc"], 3),
                    "AUROC_95CI": f"{d['auroc_ci_lo']:.3f}-{d['auroc_ci_hi']:.3f}",
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "table2_3_performance.csv", index=False)


def calibration_metrics(y, prob):
    brier = brier_score_loss(y, prob)
    prob_true, prob_pred = calibration_curve(y, prob, n_bins=8, strategy="quantile")
    if len(prob_true) >= 2:
        slope, intercept = np.polyfit(prob_pred, prob_true, 1)
    else:
        slope, intercept = np.nan, np.nan
    return brier, slope, intercept


def write_table6(all_cohorts):
    rows = []
    for name, y, prob in all_cohorts:
        brier, slope, intercept = calibration_metrics(y, prob)
        rows.append({"Cohort": name, "Brier": brier, "Calibration_slope": slope, "Calibration_intercept": intercept})
    pd.DataFrame(rows).to_csv(TABLES / "table6_calibration.csv", index=False)


def write_s8_s9(m3_raw, test_ids, model, imp, scaler, features20):
    id_m3 = "icustay_id" if "icustay_id" in m3_raw.columns else "subject_id"
    test = m3_raw.merge(test_ids, on=id_m3, how="inner")
    rows8 = []
    for stratum in ["admission", "acquired"]:
        sub = test[test["hypokalemia_stratum"] == stratum]
        if len(sub) < 10:
            continue
        sub_p = prep_frame(sub, features20)
        y = sub_p["hospital_expire_flag"].astype(int)
        X = sub_p[features20]
        X_s = pd.DataFrame(scaler.transform(pd.DataFrame(imp.transform(X), columns=features20)), columns=features20)
        prob = model.predict_proba(X_s)[:, 1]
        auc, lo, hi = delong_ci(y, prob)
        brier, slope, _ = calibration_metrics(y, prob)
        rows8.append({"Stratum": stratum, "n": len(y), "Events": int(y.sum()), "AUROC": auc, "CI_lo": lo, "CI_hi": hi, "Brier": brier, "Slope": slope})
    pd.DataFrame(rows8).to_csv(TABLES / "table_s8_strata.csv", index=False)

    # S9 legacy: use hospital_expire_flag original label on same IDs
    legacy_path = COHORT / "legacy_mimic3_test.pkl"
    if not legacy_path.exists():
        legacy_path = COHORT / "legacy_mimic3_test.parquet"
    legacy_test = pd.read_pickle(legacy_path) if legacy_path.suffix == ".pkl" else pd.read_parquet(legacy_path)
    sub_p = prep_frame(legacy_test, features20, label_col="hospital_expire_flag")
    y = sub_p["hospital_expire_flag"].astype(int)
    X_s = pd.DataFrame(
        scaler.transform(pd.DataFrame(imp.transform(sub_p[features20]), columns=features20)),
        columns=features20,
    )
    prob = model.predict_proba(X_s)[:, 1]
    auc, lo, hi = delong_ci(y, prob)
    pd.DataFrame([{"Analysis": "legacy_admission_anchored", "n": len(y), "Events": int(y.sum()), "AUROC": auc, "CI_lo": lo, "CI_hi": hi}]).to_csv(
        TABLES / "table_s9_legacy.csv", index=False
    )


def plot_figure5(y_test, prob_test, y_val, prob_val, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, y, p, title in [
        (axes[0], y_test, prob_test, "MIMIC-III internal"),
        (axes[1], y_val, prob_val, "MIMIC-IV temporal"),
    ]:
        prob_true, prob_pred = calibration_curve(y, p, n_bins=8, strategy="quantile")
        ax.plot([0, 1], [0, 1], "k--", lw=1)
        ax.plot(prob_pred, prob_true, "o-", label="8-feature ensemble")
        ax.set_title(title)
        ax.set_xlabel("Predicted probability")
        ax.set_ylabel("Observed fraction")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    for d in (PREDS, TABLES, FIGURES, OUT / "model_weight"):
        d.mkdir(parents=True, exist_ok=True)

    f20 = load_lasso20()
    f8 = [f for f in FEAT8]

    res20, model20, imp20, sc20, _ = train_and_predict(f20, "21_features")
    res8, model8, imp8, sc8, _ = train_and_predict(f8, "9_features")

    write_table23(
        {"test": res20["test"], "val": res20["val"]},
        {"test": res8["test"], "val": res8["val"]},
    )

    # F3 / NH extrapolation (optional; requires data/external/)
    ext_rows = []
    all_cal = []
    if external_cohorts_available():
        f3 = load_corrected_f3_feature_table()
        nh = load_corrected_nh_feature_table()
        f3["hospital_expire_flag"] = (f3["hospital_expire_flag"] == 1).astype(int)
        nh["hospital_expire_flag"] = nh["hospital_expire_flag"].astype(int)

        for tag, model, imp, scaler, feats in [
            ("F3", model8, imp8, sc8, f8),
            ("NH", model8, imp8, sc8, f8),
        ]:
            df = f3 if tag == "F3" else nh
            y, prob, n, ev = infer_external(model, imp, scaler, feats, df)
            auc, lo, hi = delong_ci(y, prob)
            ext_rows.append({"Cohort": tag, "n": n, "Events": ev, "AUROC": auc, "CI_lo": lo, "CI_hi": hi})
            with open(PREDS / f"9_features_{tag}_preds.pkl", "wb") as f:
                pickle.dump([{"model_name": "Ensemble_Stacking", "lable": y.tolist(), "pred_prob": prob.tolist(), "n": n, "events": ev}], f)
            all_cal.append((tag, y, prob))
    else:
        print(
            "Skipping F3/NH: data/external/mimic_validation_cohorts.xlsx not found (MIMIC-only path)"
        )

    pd.DataFrame(ext_rows).to_csv(TABLES / "external_f3_nh.csv", index=False)

    all_cal.extend([
        ("MIMIC-III test 8f", np.array(res8["test"]["lable"]), np.array(res8["test"]["pred_prob"])),
        ("MIMIC-IV val 8f", np.array(res8["val"]["lable"]), np.array(res8["val"]["pred_prob"])),
    ])
    write_table6(all_cal)

    m3_raw = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_k")
    test_ids = pd.read_csv(COHORT / "mimic3_test_ids.csv")
    write_s8_s9(m3_raw, test_ids, model20, imp20, sc20, f20)

    plot_figure5(
        np.array(res8["test"]["lable"]),
        np.array(res8["test"]["pred_prob"]),
        np.array(res8["val"]["lable"]),
        np.array(res8["val"]["pred_prob"]),
        FIGURES / "figure5_calibration.png",
    )

    # update manifest with metrics
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["metrics"] = {
        "mimic3_test_8f_auroc": res8["test"]["auroc"],
        "mimic4_val_8f_auroc": res8["val"]["auroc"],
        "mimic3_test_events": res8["test"]["events"],
        "mimic4_val_events": res8["val"]["events"],
    }
    if len(ext_rows) >= 2:
        manifest["metrics"].update(
            {
                "F3_auroc": ext_rows[0]["AUROC"],
                "NH_auroc": ext_rows[1]["AUROC"],
                "F3_events": ext_rows[0]["Events"],
                "NH_events": ext_rows[1]["Events"],
            }
        )
    manifest["external_cohorts_evaluated"] = external_cohorts_available()
    manifest["t0_source_detail"] = manifest.get("t0_source_detail", "excel_derived_interim")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["metrics"], indent=2))
    _export_legacy_pred_layout(sc8, sc20)


def _export_legacy_pred_layout(sc8, sc20):
    """Copy preds to names expected by complete_revision.py."""
    import shutil

    subdirs = {
        "21_features": [
            ("test_preds.pkl", "21_features_test_preds.pkl"),
            ("val_preds.pkl", "21_features_val_preds.pkl"),
        ],
        "9_features": [
            ("test_preds.pkl", "9_features_test_preds.pkl"),
            ("val_preds.pkl", "9_features_val_preds.pkl"),
            ("F3_preds.pkl", "9_features_F3_preds.pkl"),
            ("NH_preds.pkl", "9_features_NH_preds.pkl"),
        ],
    }
    for sub, pairs in subdirs.items():
        d = PREDS / sub
        d.mkdir(parents=True, exist_ok=True)
        for dest, src in pairs:
            src_path = PREDS / src
            if src_path.exists():
                shutil.copy2(src_path, d / dest)
    for tag, scaler in [("9_features", sc8), ("21_features", sc20)]:
        wdir = OUT / "model_weight" / tag
        wdir.mkdir(parents=True, exist_ok=True)
        with open(wdir / "stand_encoder.pkl", "wb") as f:
            pickle.dump(scaler, f)


if __name__ == "__main__":
    main()
