# 8-Feature Model — Data Dictionary

## Prediction origin

- **Primary locked analysis:** ICU admission / early-ICU observation origin
- **Study population:** documented hypokalemia (K⁺ < 3.5 mmol/L)
- **First-hypokalemia anchoring** was evaluated only as a sensitivity analysis and should not be interpreted as the primary deployment workflow

## Features

All predictors below use values **at or before the primary prediction origin** (ICU admission / early-ICU observation window).

| Feature | Description | Unit / encoding |
|---------|-------------|-----------------|
| `admission_age` | Age at admission | years |
| `rdw_mean` | Red cell distribution width (mean within early-ICU observation window) | % |
| `wbc_min` | White blood cell count (minimum within early-ICU observation window) | K/µL |
| `spo2_min` | SpO₂ (minimum within early-ICU observation window) | % |
| `lactate_min` | Lactate (minimum within early-ICU observation window) | mmol/L |
| `platelet_min` | Platelet count (minimum within early-ICU observation window) | K/µL |
| `aniongap_1st` | Anion gap (first within early-ICU observation window) | mEq/L |
| `is_noninvasive_ventilator` | Non-invasive ventilation before the prediction origin | 0/1 |

## Outcome

- **Primary (manuscript):** death within 7 calendar days from ICU admission in the primary locked analysis
- **Code column:** `outcome_7d` (see `docs/internal/MC1_spec.md` for sensitivity-analysis timing rules)

See `docs/internal/MC1_spec.md` for full variable timing rules and sensitivity analyses.
