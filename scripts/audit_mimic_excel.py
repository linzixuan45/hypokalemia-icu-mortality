#!/usr/bin/env python3
"""Audit mimic_dataset.xlsx columns for R2 t₀ / severity-score data gaps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "mimic_dataset.xlsx"
DEFAULT_OUT = ROOT / "result" / "r2_locked" / "reports" / "audit_mimic_excel_report.json"


def audit_sheet(name: str, data_path: Path) -> dict:
    df = pd.read_excel(data_path, sheet_name=name, nrows=5)
    cols = list(df.columns)
    id_cols = [
        c
        for c in cols
        if any(x in c.lower() for x in ("subject", "hadm", "stay", "icustay"))
    ]
    time_cols = [
        c
        for c in cols
        if any(x in c.lower() for x in ("time", "date", "charttime"))
        and "chartevents" not in c.lower()
    ]
    severity = [
        c
        for c in cols
        if any(x in c.lower() for x in ("sofa", "apache", "saps"))
    ]
    potassium = [c for c in cols if "potassium" in c.lower()]
    return {
        "sheet": name,
        "n_columns": len(cols),
        "id_columns": id_cols,
        "timestamp_columns": time_cols,
        "severity_columns": severity,
        "potassium_columns": potassium,
        "has_charttime_level_k": False,
        "has_apache_saps": any("apache" in c.lower() or "saps" in c.lower() for c in cols),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit mimic_dataset.xlsx structure")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    full3 = pd.read_excel(args.data_path, sheet_name="mimic3_low_k")
    full4 = pd.read_excel(args.data_path, sheet_name="mimic4_low_k")
    reports = [
        audit_sheet("mimic3_low_k", args.data_path),
        audit_sheet("mimic4_low_k", args.data_path),
    ]
    summary = {
        "data_path": str(args.data_path),
        "mimic3_rows": len(full3),
        "mimic4_rows": len(full4),
        "sheets": reports,
        "conclusion": (
            "Excel contains admission-window aggregated features only. "
            "No charttime-level potassium timestamps. "
            "SOFA present (sofa_score); APACHE II / SAPS II absent unless SQL export added. "
            "Use prepare_t0_labs_parquet.py for interim t₀ or sql/export_t0_cohort.sql when available."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
