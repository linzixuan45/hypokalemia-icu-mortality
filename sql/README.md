# MIMIC SQL export

Run on credentialed PhysioNet MIMIC-III v1.4 / MIMIC-IV v2.2.

**Default public path:** use the Excel-based pipeline in [docs/preprocessing_excel.md](../docs/preprocessing_excel.md). SQL scripts are an **optional upgrade** when definitive charttime-level t₀ and APACHE/SAPS scores are available.

## Index time (t₀)

### Optional upgrade (replaces Excel proxy)

```bash
# Run export_t0_cohort.sql on PhysioNet → CSV, then:
python3 -c "import pandas as pd; pd.read_csv('mimic_t0_labs.csv').to_parquet('data/mimic_t0_labs.parquet')"
```

Expected columns: `stay_id`, `t0_charttime`, `hypokalemia_stratum`, `hours_icu_to_t0`.

### Interim (no SQL) — default for Excel reproduction

```bash
python3 scripts/prepare_t0_labs_parquet.py
```

This writes `data/mimic_t0_labs.parquet` with `source=excel_derived_interim`. Replace with SQL output when ready, then re-run from `build_t0_cohort.py`.

## Severity scores at t₀

```bash
# After mimic_t0_labs.parquet exists
# Run export_severity_at_t0.sql → CSV, then:
python3 scripts/import_severity_sql_export.py --csv path/to/severity.csv
```

Without SQL, `build_t0_cohort.py` writes a SOFA-only proxy from `sofa_score` in the Excel export.

## Validate

```bash
python3 scripts/validate_excel_input.py
python3 scripts/validate_parquet_export.py
python3 scripts/audit_mimic_excel.py
```

## After SQL or Excel t₀ export

Re-run the locked pipeline from cohort build:

```bash
python3 scripts/build_t0_cohort.py
python3 scripts/r2_locked_run.py
python3 scripts/r2_extended_outputs.py
python3 scripts/benchmark_severity_scores.py
```

Or: `python3 scripts/run_locked_pipeline.py --skip-validate`
