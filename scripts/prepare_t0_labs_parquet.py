#!/usr/bin/env python3
"""
Build data/mimic_t0_labs.parquet from Excel when MIMIC SQL export is unavailable.

Co-authors with PhysioNet access should replace this file by running:
  sql/export_t0_cohort.sql

This interim export enables pipeline v2 (t0_source=parquet) using proxy t₀ timing
derived from potassium_1st / potassium_min and los_icu.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "mimic_dataset.xlsx"
OUT = ROOT / "data" / "mimic_t0_labs.parquet"
BASE_TS = pd.Timestamp("2000-01-01")


def _stratum(row: pd.Series) -> str:
    k1 = pd.to_numeric(row.get("potassium_1st", np.nan), errors="coerce")
    kmin = pd.to_numeric(row.get("potassium_min", np.nan), errors="coerce")
    if pd.notna(k1) and k1 < 3.5:
        return "admission"
    if pd.notna(kmin) and kmin < 3.5:
        return "acquired"
    return "unknown"


def _hours_to_t0(row: pd.Series) -> float:
    """Proxy: admission hypokalemia → first lab ~6h; acquired → mid-stay before nadir."""
    k1 = pd.to_numeric(row.get("potassium_1st", np.nan), errors="coerce")
    los_h = float(pd.to_numeric(row.get("los_icu", 1), errors="coerce")) * 24.0
    if pd.notna(k1) and k1 < 3.5:
        return min(24.0, max(1.0, los_h * 0.05))
    return min(max(24.0, los_h * 0.35), max(los_h - 12.0, 24.0))


def sheet_to_labs(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        sid = r.get(id_col)
        if pd.isna(sid):
            continue
        hours = _hours_to_t0(r)
        t0 = BASE_TS + pd.Timedelta(hours=hours)
        first_k = BASE_TS + pd.Timedelta(hours=min(6.0, hours))
        rows.append(
            {
                "stay_id": int(sid) if id_col != "subject_id" else int(sid),
                "subject_id": int(r["subject_id"]) if "subject_id" in r.index else int(sid),
                "icu_intime": BASE_TS,
                "t0_charttime": t0,
                "first_k_lab_charttime": first_k,
                "potassium_at_t0": float(
                    pd.to_numeric(
                        r.get("potassium_1st", r.get("potassium_min", np.nan)), errors="coerce"
                    )
                ),
                "hypokalemia_stratum": _stratum(r),
                "hours_icu_to_t0": hours,
                "source": "excel_derived_interim",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    m3 = pd.read_excel(DATA_PATH, sheet_name="mimic3_low_k")
    m4 = pd.read_excel(DATA_PATH, sheet_name="mimic4_low_k")
    id_m3 = "icustay_id" if "icustay_id" in m3.columns else "subject_id"
    id_m4 = "subject_id"
    labs = pd.concat([sheet_to_labs(m3, id_m3), sheet_to_labs(m4, id_m4)], ignore_index=True)
    labs = labs.drop_duplicates(subset=["stay_id"], keep="first")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    labs.to_parquet(OUT, index=False)
    print(f"Wrote {OUT} ({len(labs)} rows, source=excel_derived_interim)")
    print("Replace with SQL export from export_t0_cohort.sql when available.")


if __name__ == "__main__":
    main()
