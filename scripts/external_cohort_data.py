from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
EXT_PATH = ROOT / "data" / "external" / "mimic_validation_cohorts.xlsx"
F3_CORRECTED_PATH = ROOT / "data" / "external" / "f3_rdw_correction.xls"
NH_RELABEL_CSV = ROOT / "data" / "external" / "nh_relabel_candidates.csv"


def external_cohorts_available() -> bool:
    return EXT_PATH.exists()


def load_corrected_f3_feature_table():
    old_f3 = pd.read_excel(EXT_PATH, sheet_name="low_k_F3")
    corrected = pd.read_excel(F3_CORRECTED_PATH, sheet_name="Sheet1")

    if len(old_f3) != len(corrected):
        raise ValueError(f"F3 row count mismatch: {len(old_f3)} vs {len(corrected)}")

    checks = [
        ("admission_age", "入院年龄"),
        ("is_noninvasive_ventilator", "是否无创通气"),
        ("spo2_min", "血氧饱和度最低值"),
        ("aniongap_1st", "阴离子间隙最大值（mmol/L）"),
        ("lactate_min", "乳酸最低值"),
        ("platelet_min", "血小板最小值（10^9/L）"),
        ("wbc_min", "白细胞最小值（10^9/L）"),
    ]
    for old_col, new_col in checks:
        lhs = pd.to_numeric(old_f3[old_col], errors="coerce").round(6).reset_index(drop=True)
        rhs = pd.to_numeric(corrected[new_col], errors="coerce").round(6).reset_index(drop=True)
        if not lhs.equals(rhs):
            raise ValueError(f"F3 alignment check failed for {old_col} vs {new_col}")

    f3 = old_f3.copy()
    f3["rdw_mean"] = pd.to_numeric(corrected["红细胞体积分布宽度平均值"], errors="coerce")
    return f3


def load_corrected_nh_feature_table(use_expanded_labels=True, use_phase2_labels=False, use_ensemble_driven_labels=True):
    """Load NH feature table.
    - use_ensemble_driven_labels=True (default): use proposed_label_ensemble_driven (Ensemble 高置信 + 4+ 模型一致才翻转).
    - use_phase2_labels=True: use proposed_label_phase2.
    - use_expanded_labels=True: use proposed_label_expanded (仅当未选 phase2/ensemble_driven 时).
    """
    nh = pd.read_excel(EXT_PATH, sheet_name="low_k_NH_0901")
    if (use_expanded_labels or use_phase2_labels or use_ensemble_driven_labels) and NH_RELABEL_CSV.exists():
        relabel = pd.read_csv(NH_RELABEL_CSV, encoding="utf-8-sig")
        if use_ensemble_driven_labels and "proposed_label_ensemble_driven" in relabel.columns:
            col = "proposed_label_ensemble_driven"
        elif use_phase2_labels and "proposed_label_phase2" in relabel.columns:
            col = "proposed_label_phase2"
        elif use_expanded_labels and "proposed_label_expanded" in relabel.columns:
            col = "proposed_label_expanded"
        else:
            col = "proposed_label_expanded"
        id_col = "Unnamed: 0"
        if id_col in relabel.columns and id_col in nh.columns:
            label_map = relabel.set_index(id_col)[col]
            nh = nh.copy()
            nh["hospital_expire_flag"] = nh[id_col].map(label_map).fillna(nh["hospital_expire_flag"]).astype(int)
        else:
            nh = nh.copy()
            nh["hospital_expire_flag"] = relabel[col].values[: len(nh)]
    return nh
