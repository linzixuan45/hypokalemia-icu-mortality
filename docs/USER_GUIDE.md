# User Guide — Hypokalemia ICU Mortality Repository

**Research use only. Not for clinical use.**

This repository is deposited as **auditable analysis source code**: reviewers and researchers can inspect the pipeline, run local inference, and re-run analyses on credentialed data they prepare themselves. It does **not** redistribute patient-level data and does **not** guarantee bit-exact reproduction of every manuscript table or metric.

---

## 1. What this repository provides

| Provided | Not provided |
|----------|--------------|
| Full analysis scripts (`scripts/`) and optional SQL (`sql/`) | MIMIC raw tables or patient identifiers |
| Released 8-feature model weights (`model_weights/`) | Pre-built `mimic_dataset.xlsx` |
| Local inference CLI (`inference.py`) | ETL from raw MIMIC to Excel |
| Model card, data dictionary, methods specs | Bit-exact guarantee of manuscript AUROC/tables |
| Online SHAP research calculator (see Track B) | Chinese validation cohort files |

---

## 2. Quick start

### Track A — Local probability (no MIMIC data required)

```bash
pip install -r requirements.txt
python inference.py
```

Outputs a 7-day mortality probability and the Youden threshold from the released model bundle.

### Track B — SHAP audit

- **Online (recommended):** https://k.mixaihub.top — interactive probability + SHAP exploration.
- **Local Figure 7 (optional):** requires your own `data/mimic_dataset.xlsx` and:

```bash
pip install -r requirements-optional.txt
python scripts/run_pipeline.py
```

SHAP is not in the base `requirements.txt` because it is only needed for supplementary figures, not for core inference.

---

## 3. Pipeline overview

| Script | Role |
|--------|------|
| `run_pipeline.py` | End-to-end Excel-based pipeline |
| `validate_excel_input.py` | Validate `mimic_dataset.xlsx` before analysis |
| `prepare_t0_labs_parquet.py` | Build interim t₀ timing (`excel_derived_interim`) |
| `build_t0_cohort.py` | Cohort filters, splits, `manifest.json` |
| `train_models.py` | Train models; Tables 2–6, S8–S9 |
| `supplementary_analysis.py` | DCA, subgroups, SHAP Figure 7; Tables S6–S15 |
| `benchmark_severity_scores.py` | Table 5 severity benchmark |
| `build_table1_baseline.py` | Table 1 |
| `export_github_weights.py` | Export `model_weights/8_features_model.pkl` |

`subgroup_analysis.py` is called by `supplementary_analysis.py`; you do not need to run it separately.

Data flow: Excel → parquet t₀ proxy → cohorts → train → supplementary → tables under `result/analysis/` (local only, gitignored).

Further detail: [preprocessing_excel.md](preprocessing_excel.md) · [internal/data_flow_cohorts.md](internal/data_flow_cohorts.md)

---

## 4. What auditors should read

| Document | Purpose |
|----------|---------|
| [MODEL_CARD.md](../MODEL_CARD.md) | Model scope, features, performance, limitations |
| [data_dictionary.md](data_dictionary.md) | 8-feature definitions and units |
| [internal/MC1_spec.md](internal/MC1_spec.md) | Primary prediction origin, outcome, cohort rules; first-hypokalemia sensitivity |
| [preprocessing_excel.md](preprocessing_excel.md) | Excel input contract and known limitations |
| [CODE_AVAILABILITY.md](../CODE_AVAILABILITY.md) | Deposit scope for the manuscript |

---

## 5. Re-running with your own data

1. Obtain credentialed MIMIC access from [PhysioNet](https://physionet.org/).
2. Prepare `data/mimic_dataset.xlsx` per [preprocessing_excel.md](preprocessing_excel.md).
3. Validate and run:

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
```

**Important:** the default public path uses an Excel-derived t₀ proxy (`excel_derived_interim`), not charttime-level serum potassium. Metrics may differ slightly from the published manuscript. For charttime-level t₀ and full APACHE/SAPS benchmarks, use the optional SQL path in [sql/README.md](../sql/README.md) and re-run from `build_t0_cohort.py`.

---

## 6. FAQ

**Why might my AUROC differ from the paper?**  
Your Excel build, t₀ proxy, or MIMIC version may differ. This repository documents the analysis logic; exact numeric reproduction requires the same data construction as the authors.

**Where is SHAP?**  
The online calculator at https://k.mixaihub.top provides SHAP audit. Locally, install `requirements-optional.txt` and run the full pipeline with MIMIC data.

**What can I do without MIMIC access?**  
Run `python inference.py` with the released weights, read the source code and methods docs, and use the online calculator.

---

Python ≥3.10 recommended. See [README.md](../README.md) for citation and archive links.
