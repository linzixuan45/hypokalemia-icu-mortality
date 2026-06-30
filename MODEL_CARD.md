# Hypokalemia 8-Feature Research Model — Model Card

**NOT FOR CLINICAL USE.** Research demonstration and audit only.

## Intended use

- Retrospective risk stratification among ICU patients with documented hypokalemia (K⁺ < 3.5 mmol/L)
- Model audit / SHAP exploration in research settings
- **Not** for real-time clinical decision support or deployment

## Model

- 8-feature stacking ensemble (XGBoost + Random Forest + Logistic Regression meta-learner)
- Trained on MIMIC-III with t₀-reanchored cohort (`train_models.py`)
- Natural class prevalence (no undersampling)
- Youden threshold from 5-fold out-of-fold predictions on the training set

## Input features

| Feature | Description |
|---------|-------------|
| `admission_age` | Age at admission (years) |
| `rdw_mean` | RDW mean to t₀ (%) |
| `wbc_min` | WBC minimum to t₀ |
| `spo2_min` | SpO₂ minimum to t₀ (%) |
| `lactate_min` | Lactate minimum to t₀ (mmol/L) |
| `platelet_min` | Platelet minimum to t₀ |
| `aniongap_1st` | First anion gap to t₀ (mEq/L) |
| `is_noninvasive_ventilator` | Non-invasive ventilation before t₀ (0/1) |

See `docs/data_dictionary.md` for timing rules.

## Training data

- MIMIC-III (2001–2012), credentialed PhysioNet access required for replication
- Index time: first K⁺ < 3.5 mmol/L

## Performance (manuscript)

| Cohort | n | Events | AUROC |
|--------|---|--------|-------|
| MIMIC-III test | 163 | 50 | 0.717 |
| MIMIC-IV temporal | 1413 | 130 | 0.835 |
| F3 (exploratory) | 110 | 25 | 0.830 |
| NH (exploratory) | 100 | 33 | 0.717 |

## Known limitations

- Chinese cohorts (F3/NH) are exploratory geographic validation only
- NH labels include ensemble-driven refinements (33 events)
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

Xie, Liangpeng, et al. *Scientific Reports* — SHAP-Audited Machine-Learning Model for Short-Term Mortality Risk Stratification in ICU Patients With Documented Hypokalemia. Code: https://github.com/linzixuan45/hypokalemia-icu-mortality
