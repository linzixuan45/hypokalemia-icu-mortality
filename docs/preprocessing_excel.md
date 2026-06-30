# Excel-Based Preprocessing and Reproduction Path

**Scope:** credentialed users who hold a local `data/mimic_dataset.xlsx`. This repository does **not** redistribute patient-level data and does **not** include MIMIC raw-table ETL.

The manuscript once referenced `export_low_k_20feature_dataset.py`; that script was never committed. For public reproduction, use the Excel input plus the scripts below.

---

## Required input

Place your authorized export at:

```
data/mimic_dataset.xlsx
```

### Required sheets

| Sheet | Purpose |
|-------|---------|
| `mimic3_low_k` | MIMIC-III development / internal test source |
| `mimic4_low_k` | MIMIC-IV temporal validation source |
| `Feature_names` | Optional; used by exploratory `dataset.py` / LASSO flows |

### Minimum columns

**Identifiers**

| Column | MIMIC-III | MIMIC-IV |
|--------|-----------|----------|
| `subject_id` | required | required |
| `icustay_id` | required (preferred join key) | — |

**Outcome and follow-up**

| Column | Purpose |
|--------|---------|
| `hospital_expire_flag` | In-hospital death indicator |
| `hosp_survival_days` or `icu_survival_days` | Used to derive `outcome_7d` from t₀ |

**Cohort filters**

| Column | Purpose |
|--------|---------|
| `admission_age` | Clipped to 18–100 years |
| `los_icu` | Primary analysis: ≥ 1 day (24 h ICU stay) |

**t₀ proxy (Excel path)**

| Column | Purpose |
|--------|---------|
| `potassium_1st` | Admission-stratum proxy |
| `potassium_min` | Acquired-hypokalemia proxy |

**8-feature model panel** — see [data_dictionary.md](data_dictionary.md):

`rdw_mean`, `wbc_min`, `admission_age`, `spo2_min`, `lactate_min`, `is_noninvasive_ventilator`, `platelet_min`, `aniongap_1st`

**20-feature / severity benchmark**

| Column | Purpose |
|--------|---------|
| `sofa_score` | Table 5 SOFA comparator (Excel proxy) |
| APACHE II / SAPS II | **Not in Excel**; require SQL export via [sql/README.md](../sql/README.md) |

---

## Pipeline (Excel path)

```bash
python scripts/validate_excel_input.py
python scripts/prepare_t0_labs_parquet.py
python scripts/build_t0_cohort.py
python scripts/r2_locked_run.py
python scripts/r2_extended_outputs.py
python scripts/benchmark_severity_scores.py
python scripts/build_table1_baseline.py
python scripts/export_github_weights.py
```

Or run the full chain:

```bash
python scripts/run_locked_pipeline.py
```

### Step-by-step

| Step | Script | Output |
|------|--------|--------|
| 1. Validate | `validate_excel_input.py` | JSON report; exit 0/1 |
| 2. t₀ proxy | `prepare_t0_labs_parquet.py` | `data/mimic_t0_labs.parquet` (`source=excel_derived_interim`) |
| 3. Cohorts | `build_t0_cohort.py` | `result/r2_locked/cohorts/*`, `manifest.json`, SOFA severity proxy |
| 4. Train | `r2_locked_run.py` | Model weights, preds, Tables 2–6, S8–S9 |
| 5. Extended | `r2_extended_outputs.py` | DCA, subgroups, S7–S15 |
| 6. Severity | `benchmark_severity_scores.py` | Table 5 (SOFA-only when SQL absent) |
| 7. Table 1 | `build_table1_baseline.py` | `tables/table1_baseline.csv` |
| 8. Subgroup | `subgroup_analysis.py` (via extended outputs) | `tables/table_s6_subgroup_full.csv`, `table4_subgroup_summary.csv` |
| 9. Public weights | `export_github_weights.py` | `model_weights/8_features_model.pkl` |

---

## Optional SQL upgrade

When co-authors with PhysioNet SQL access export definitive charttime-level t₀:

1. Run [sql/export_t0_cohort.sql](../sql/export_t0_cohort.sql) → `data/mimic_t0_labs.parquet`
2. Optionally [sql/export_severity_at_t0.sql](../sql/export_severity_at_t0.sql) → `data/mimic_severity_scores.parquet`
3. Re-run from `build_t0_cohort.py` onward

See [sql/README.md](../sql/README.md).

---

## Diagnostic tools

```bash
python scripts/audit_mimic_excel.py
python scripts/validate_excel_input.py --report
python scripts/validate_parquet_export.py
```

Reports are written under `result/r2_locked/reports/` (local only, not redistributed).

---

## Role of `dataset.py`

| Component | Responsibility |
|-----------|----------------|
| Excel sheets | Pre-aggregated admission-to-window features (user-prepared) |
| `prepare_t0_labs_parquet.py` | Synthetic t₀ timing from `potassium_*` + `los_icu` |
| `build_t0_cohort.py` | Filters, `outcome_7d`, train/test/val ID lists |
| `dataset.py` `data_preprocess()` | Exploratory / LASSO path: encoding, clipping, optional SMOTE |
| `r2_locked_run.py` `prep_frame()` | Locked-run training: encoding, imputation, scaling |

The **locked R2 manuscript path** uses `r2_locked_run.py`, not `DATASET.data_preprocess()`.

---

## Known limitations (Excel path)

- No charttime-level serum potassium in the Excel export; t₀ uses **excel_derived_interim** proxy per [MC1_spec.md](MC1_spec.md).
- APACHE II and SAPS II are absent unless SQL severity export is added.
- F3/NH geographic validation is skipped when `data/external/mimic_validation_cohorts.xlsx` is absent (MIMIC-only path).
- Metrics may differ slightly from the published locked v2 run if your Excel build or proxy timing differs.
- **Research use only. Not for clinical use.**
