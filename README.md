# Hypokalemia ICU Mortality Risk Model (R2 Locked Run)

**Research use only. Not for clinical use.**

Public code repository for:

> *SHAP-Audited Machine-Learning Model for Short-Term Mortality Risk Stratification in ICU Patients With Documented Hypokalemia: Development and Temporal External Validation*

This repository contains the analysis pipeline, SQL extraction scripts, inference code, model card, data dictionary, and the released 8-feature research model bundle. Raw patient-level data are **not** redistributed.

## Quick start (inference demo)

**Online research calculator:** https://k.mixaihub.top (not for clinical use)

Local CLI:

```bash
pip install -r requirements.txt
python inference.py
```

## Repository layout

| Path | Purpose |
|------|---------|
| `inference.py` | Single-patient 7-day mortality probability |
| `model_weights/8_features_model.pkl` | Locked ensemble + imputer + scaler |
| `scripts/` | Full analysis pipeline (includes `subgroup_analysis.py`) |
| `sql/` | MIMIC t₀ and severity score export SQL (optional upgrade) |
| `docs/` | Methods specs, data dictionary, **Excel preprocessing guide** |
| `config/` | LASSO feature list (non-patient metadata) |
| `data/README.md` | Where to place local `mimic_dataset.xlsx` |

## Full reproduction (Excel path)

1. Obtain MIMIC-III / MIMIC-IV access via [PhysioNet](https://physionet.org/).
2. Place locally prepared feature tables at `data/mimic_dataset.xlsx` (not provided). See [docs/preprocessing_excel.md](docs/preprocessing_excel.md).
3. Run the locked pipeline:

```bash
python scripts/validate_excel_input.py
python scripts/run_locked_pipeline.py
```

Or step by step:

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

**Optional SQL upgrade:** replace interim t₀ with [sql/export_t0_cohort.sql](sql/export_t0_cohort.sql) output, then re-run from `build_t0_cohort.py`. See [sql/README.md](sql/README.md).

Chinese external validation (F3/NH) requires locally held files under `data/external/` (not redistributed). See `DATA_AVAILABILITY.md`.

## Model summary

- 8-feature stacking ensemble (XGBoost + Random Forest + Logistic Regression meta-learner)
- Index time t₀: first serum K⁺ < 3.5 mmol/L
- Outcome: death within 7 calendar days from t₀
- Natural class prevalence (no undersampling)

Locked run metrics (manifest v2): MIMIC-III test AUROC 0.717; MIMIC-IV AUROC 0.835.

## Citation and availability

- Research demo: https://k.mixaihub.top
- Code: `[GitHub URL — fill after public push]`
- Archived DOI: `[Zenodo version DOI — fill after release]`
- See `CODE_AVAILABILITY.md` and `MODEL_CARD.md`

## License / use

Research use only. No standard open-source license. MIMIC and local validation data require separate authorized access.
