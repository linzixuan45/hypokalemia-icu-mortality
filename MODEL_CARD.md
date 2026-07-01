# Hypokalemia 8-Feature Research Model — Model Card

**NOT FOR CLINICAL USE.** Research demonstration and audit only.

## Intended use

- Retrospective risk stratification among ICU patients with documented hypokalemia (K⁺ < 3.5 mmol/L)
- Model audit / SHAP exploration in research settings
- **Not** for real-time clinical decision support or deployment

## Prediction origin (primary locked analysis)

- **Primary analysis:** ICU admission / early-ICU observation origin
- **Study population:** documented hypokalemia (K⁺ < 3.5 mmol/L) defines the retrospective cohort
- **First-hypokalemia anchoring** (`t₀` = first K⁺ < 3.5 mmol/L) was evaluated only as a **sensitivity analysis** in the manuscript and should not be interpreted as the primary deployment workflow

## Model

- 8-feature stacking ensemble (XGBoost + Random Forest + Logistic Regression meta-learner)
- Trained on MIMIC-III under the primary locked ICU-admission / early-ICU observation workflow (`train_models.py`)
- Natural class prevalence (no undersampling)
- Youden threshold from 5-fold out-of-fold predictions on the training set

## Input features

All predictors use values **at or before the primary prediction origin** (ICU admission / early-ICU observation window).

| Feature | Description |
|---------|-------------|
| `admission_age` | Age at admission (years) |
| `rdw_mean` | RDW mean within the early-ICU observation window (%) |
| `wbc_min` | WBC minimum within the early-ICU observation window |
| `spo2_min` | SpO₂ minimum within the early-ICU observation window (%) |
| `lactate_min` | Lactate minimum within the early-ICU observation window (mmol/L) |
| `platelet_min` | Platelet minimum within the early-ICU observation window |
| `aniongap_1st` | First anion gap within the early-ICU observation window (mEq/L) |
| `is_noninvasive_ventilator` | Non-invasive ventilation before the prediction origin (0/1) |

See `docs/data_dictionary.md` for timing rules.

## Training data

- MIMIC-III (2001–2012), credentialed PhysioNet access required for replication
- Primary locked analysis uses ICU-admission / early-ICU observation origin; documented hypokalemia defines eligibility

## Performance (manuscript)

| Cohort | n | Events | AUROC |
|--------|---|--------|-------|
| MIMIC-III test | 163 | 50 | 0.717 |
| MIMIC-IV temporal | 1413 | 130 | 0.835 |
| F3 (exploratory) | 110 | 25 | 0.830 |
| NH (exploratory) | 100 | 33 | 0.717 |

## Known limitations

- Chinese cohorts (F3/NH) are exploratory geographic validation only
- Nanhua cohort results are exploratory because of the small sample size and center-specific heterogeneity
- APACHE II / SAPS II benchmarks require full MIMIC SQL export
- Model probabilities require local prevalence context for interpretation outside derivation settings

## Research demonstration calculator

- Online SHAP audit (HTTPS): https://k.mixaihub.top
- Local probability: `python inference.py` in this repository
- Local SHAP Figure 7: requires MIMIC data + `pip install -r requirements-optional.txt` + full pipeline
- **Not for clinical use** — research audit only

## Security

- The online demo runs over HTTPS; follow the site disclaimer before entering any values
- Local inference runs offline; no patient data sent to external servers when using `inference.py`

## Citation

Xie, Liangpeng, et al. *Scientific Reports* — SHAP-Audited Machine-Learning Model for Short-Term Mortality Risk Stratification in ICU Patients With Documented Hypokalemia. Code: https://github.com/linzixuan45/hypokalemia-icu-mortality · Zenodo: https://doi.org/10.5281/zenodo.21107169
