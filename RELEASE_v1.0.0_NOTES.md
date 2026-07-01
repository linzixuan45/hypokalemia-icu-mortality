# Release v1.0.0 — version of record

**Repository:** https://github.com/linzixuan45/hypokalemia-icu-mortality  
**Tag:** `v1.0.0`  
**Commit:** `21c8de4`  
**Manuscript:** Scientific Reports revision (submission `91406a0b-fc8b-4fcf-95bc-820b99f21793`)

## Summary

Auditable analysis source code deposit for the hypokalemia ICU mortality stratification study. This release is the version of record linked from the manuscript Code Availability statement and Zenodo archive.

## Included

- Analysis pipeline (`scripts/`)
- MIMIC SQL extraction scripts (`sql/`)
- Inference code (`inference.py`)
- Released 8-feature research model bundle (`model_weights/8_features_model.pkl`)
- Model card and data dictionary (`MODEL_CARD.md`, `docs/data_dictionary.md`)
- Methods documentation (`docs/internal/`)

## Not included

- Raw patient-level data
- Access-restricted cohort ID lists
- Summary result tables tied to restricted datasets

## Related links

- Research demonstration calculator (not for clinical use): https://k.mixaihub.top
- Code Availability text: see `CODE_AVAILABILITY.md`
- After Zenodo archive: fill DOI via `./scripts/apply_zenodo_doi.sh <version_doi> [concept_doi]`
