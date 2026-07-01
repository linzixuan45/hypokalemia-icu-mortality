# Hypokalemia ICU Mortality Risk Model

**Research use only. Not for clinical use.**

Code repository for the manuscript:

> *SHAP-Audited Machine-Learning Model for Short-Term Mortality Risk Stratification in ICU Patients With Documented Hypokalemia: Development and Temporal External Validation*

This repository is deposited as **auditable analysis source code**: the pipeline, inference code, model card, data dictionary, and a released 8-feature research model bundle. **Raw patient-level data are not redistributed.**

- **Repository:** https://github.com/linzixuan45/hypokalemia-icu-mortality  
- **Research calculator:** https://k.mixaihub.top (not for clinical use)

To learn more about the underlying critical care databases, see [MIMIC](https://mimic.mit.edu) and the community [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code).

**User guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

---

## What this repository provides

| Provided | Not provided |
|----------|--------------|
| Full analysis scripts (`scripts/`) and optional SQL (`sql/`) | MIMIC raw tables or patient identifiers |
| Released 8-feature model weights (`model_weights/`) | Pre-built `mimic_dataset.xlsx` |
| Local inference CLI (`inference.py`) | ETL from raw MIMIC to Excel |
| Model card, data dictionary, methods specs | Bit-exact guarantee of manuscript AUROC/tables |
| Online SHAP research calculator (Track B below) | Chinese validation cohort files |

Python ≥3.10 recommended.

---

## Access to data

Re-running the pipeline requires credentialed access to MIMIC on PhysioNet:

| Database | PhysioNet |
|----------|-----------|
| MIMIC-III | [mimiciii](https://physionet.org/content/mimiciii/) |
| MIMIC-IV | [mimiciv](https://physionet.org/content/mimiciv/) |

Access requires completion of required training and a data-use agreement. Place locally prepared feature tables at `data/mimic_dataset.xlsx` (format in [docs/preprocessing_excel.md](docs/preprocessing_excel.md)). Chinese geographic validation (F3/NH) requires additional local files under `data/external/` — see [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

---

## Navigating this repository

| Path | Contents |
|------|----------|
| [`inference.py`](inference.py) | Single-patient 7-day mortality probability (CLI demo) |
| [`model_weights/`](model_weights/) | Released 8-feature ensemble + imputer + scaler |
| [`scripts/`](scripts/) | End-to-end analysis pipeline (Python) |
| [`sql/`](sql/) | Optional SQL exports for charttime-level t₀ and severity scores |
| [`docs/`](docs/) | User guide, methods specs, data dictionary, Excel preprocessing |
| [`config/`](config/) | Non-patient metadata (e.g. LASSO feature list) |
| [`data/README.md`](data/README.md) | Where to place local `mimic_dataset.xlsx` |

Pipeline outputs are written to `result/analysis/` (local only; gitignored).

### Analysis pipeline (`scripts/`)

| Script | Role |
|--------|------|
| [`run_pipeline.py`](scripts/run_pipeline.py) | Run the full Excel-based pipeline |
| [`validate_excel_input.py`](scripts/validate_excel_input.py) | Validate `mimic_dataset.xlsx` before analysis |
| [`prepare_t0_labs_parquet.py`](scripts/prepare_t0_labs_parquet.py) | Build interim t₀ timing from Excel (`excel_derived_interim`) |
| [`build_t0_cohort.py`](scripts/build_t0_cohort.py) | Cohort filters, `outcome_7d`, train/test/val ID lists, `manifest.json` |
| [`train_models.py`](scripts/train_models.py) | Train 20/8-feature stacking models; Tables 2–6, S8–S9 |
| [`supplementary_analysis.py`](scripts/supplementary_analysis.py) | DCA, sensitivities, subgroups, SHAP Figure 7; Tables S6–S15 |
| [`benchmark_severity_scores.py`](scripts/benchmark_severity_scores.py) | Table 5 severity-score benchmark |
| [`build_table1_baseline.py`](scripts/build_table1_baseline.py) | Table 1 baseline characteristics |
| [`export_github_weights.py`](scripts/export_github_weights.py) | Export `model_weights/8_features_model.pkl` |

`subgroup_analysis.py` is invoked by `supplementary_analysis.py`; no need to run it separately.

Further detail: [docs/preprocessing_excel.md](docs/preprocessing_excel.md) · [docs/internal/data_flow_cohorts.md](docs/internal/data_flow_cohorts.md)

### SQL extraction (`sql/`)

Optional upgrade when definitive charttime-level t₀ and APACHE/SAPS scores are available from PhysioNet SQL access. See [sql/README.md](sql/README.md).

| File | Purpose |
|------|---------|
| [`export_t0_cohort.sql`](sql/export_t0_cohort.sql) | Charttime-level t₀ → `data/mimic_t0_labs.parquet` |
| [`export_severity_at_t0.sql`](sql/export_severity_at_t0.sql) | SOFA / APACHE II / SAPS II at t₀ |

After SQL export, re-run from `build_t0_cohort.py`.

---

## Quick start

### Track A — Local probability (no MIMIC data required)

```bash
pip install -r requirements.txt
python inference.py
```

### Track B — SHAP audit

- **Online (recommended):** https://k.mixaihub.top — interactive probability + SHAP exploration.
- **Local Figure 7 (optional):** requires your own `data/mimic_dataset.xlsx`:

```bash
pip install -r requirements-optional.txt
python scripts/run_pipeline.py
```

---

## Re-running the analysis pipeline

Requires a user-prepared `data/mimic_dataset.xlsx`. The default public path uses an Excel-derived t₀ proxy; metrics may differ slightly from the published manuscript. See [docs/preprocessing_excel.md](docs/preprocessing_excel.md) (Known limitations).

**One command:**

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
```

**Step by step:**

```bash
python scripts/validate_excel_input.py
python scripts/prepare_t0_labs_parquet.py
python scripts/build_t0_cohort.py
python scripts/train_models.py
python scripts/supplementary_analysis.py
python scripts/benchmark_severity_scores.py
python scripts/build_table1_baseline.py
python scripts/export_github_weights.py
```

**Diagnostic tools:**

```bash
python scripts/audit_mimic_excel.py
python scripts/validate_excel_input.py --report
python scripts/validate_parquet_export.py
```

`run_pipeline.py` flags: `--skip-validate`, `--skip-extended`, `--skip-weights`, `--strict-validate`.

---

## Model overview

| Item | Definition |
|------|------------|
| **Study population** | ICU patients with documented hypokalemia (K⁺ < 3.5 mmol/L) |
| **Prediction origin (primary locked analysis)** | ICU admission / early-ICU observation window — **not** first-hypokalemia anchoring |
| **Outcome (primary)** | Death within 7 calendar days from ICU admission in the primary locked analysis |
| **Sensitivity analysis** | First-hypokalemia anchoring (`t₀` = first K⁺ < 3.5 mmol/L) is implemented in code for sensitivity checks only and should not be interpreted as the primary deployment workflow |
| **Model** | 8-feature stacking ensemble (XGBoost + Random Forest + Logistic Regression meta-learner) |
| **Class balance** | Natural prevalence (no random undersampling) |

**8 input features:** `rdw_mean`, `wbc_min`, `admission_age`, `spo2_min`, `lactate_min`, `is_noninvasive_ventilator`, `platelet_min`, `aniongap_1st` — see [docs/data_dictionary.md](docs/data_dictionary.md) and [MODEL_CARD.md](MODEL_CARD.md).

**Reported performance** (manuscript; see `result/analysis/manifest.json` after a local run):

| Cohort | AUROC |
|--------|-------|
| MIMIC-III internal test | 0.717 |
| MIMIC-IV temporal validation | 0.835 |

---

## Acknowledgement

If you use this repository, we ask that you:

1. Cite the accompanying manuscript (BibTeX below; also in [CITATION.bib](CITATION.bib)).
2. Cite the MIMIC database(s) you used, as described on PhysioNet: [MIMIC-III](https://physionet.org/content/mimiciii/) · [MIMIC-IV](https://physionet.org/content/mimiciv/).
3. Acknowledge use of the [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code) if you adopt its data-access or SQL workflow patterns.

```bibtex
@article{hypokalemia_icu_mortality,
  title   = {SHAP-Audited Machine-Learning Model for Short-Term Mortality Risk Stratification in ICU Patients With Documented Hypokalemia: Development and Temporal External Validation},
  author  = {Xie, Liangpeng and [Other authors] and Li, Yapei},
  journal = {Scientific Reports},
  volume  = {[Volume -- fill]},
  number  = {[Issue -- fill]},
  pages   = {[Pages -- fill]},
  year    = {2026},
  doi     = {[DOI -- fill]},
  note    = {Manuscript under revision at Scientific Reports. Accompanying code: https://github.com/linzixuan45/hypokalemia-icu-mortality}
}
```

Additional availability text: [CODE_AVAILABILITY.md](CODE_AVAILABILITY.md).

---

## Archive and citation

| Resource | Link |
|----------|------|
| GitHub | https://github.com/linzixuan45/hypokalemia-icu-mortality |
| Zenodo DOI | `https://doi.org/10.5281/zenodo.21107312` — see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) |
| Research demo | https://k.mixaihub.top |

Version of record release tag: `v2.0.1`

---

## License / use

Research use only. No standard open-source license is attached. MIMIC and local validation data require separate authorized access. **Do not use for clinical decision-making.**
