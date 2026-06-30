# 8-Feature Model — Data Dictionary

| Feature | Description | Unit / encoding |
|---------|-------------|-----------------|
| `admission_age` | Age at admission | years |
| `rdw_mean` | Red cell distribution width (mean to t₀) | % |
| `wbc_min` | White blood cell count (min to t₀) | K/µL |
| `spo2_min` | SpO₂ (min to t₀) | % |
| `lactate_min` | Lactate (min to t₀) | mmol/L |
| `platelet_min` | Platelet count (min to t₀) | K/µL |
| `aniongap_1st` | Anion gap (first to t₀) | mEq/L |
| `is_noninvasive_ventilator` | Non-invasive ventilation before t₀ | 0/1 |

Outcome (training): death within 7 calendar days from t₀ (`outcome_7d`).

See `docs/MC1_spec.md` for full variable timing rules.
