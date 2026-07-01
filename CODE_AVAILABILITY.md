# Code Availability

## Research demonstration calculator

- URL: https://k.mixaihub.top
- Purpose: 8-feature research probability calculator with SHAP audit (not for clinical use)

## GitHub

- Repository: https://github.com/linzixuan45/hypokalemia-icu-mortality
- Release tag: `v2.0.0` (version of record)

## Zenodo (DOI-assigning archive)

- Concept DOI: `10.5281/zenodo.21107168`
- Version DOI: `10.5281/zenodo.21107169`

## What is deposited

The archived repository is positioned as **auditable analysis source code**. It includes:

- Analysis pipeline (`scripts/`)
- MIMIC SQL extraction scripts (`sql/`)
- Inference code (`inference.py`)
- Released 8-feature model bundle (`model_weights/8_features_model.pkl`)
- Model card and data dictionary (`MODEL_CARD.md`, `docs/data_dictionary.md`)
- Methods documentation (`docs/internal/MC1_spec.md`, `docs/internal/data_flow_cohorts.md`)

Raw patient-level data, cohort ID lists, and summary result tables are **not** redistributed because MIMIC and local validation data are access-restricted.

## Manuscript text (paste into Methods or Code Availability)

```text
An HTTPS research demonstration calculator for the 8-feature model is available at https://k.mixaihub.top (not for clinical use). The underlying code and released research model bundle are available at https://github.com/linzixuan45/hypokalemia-icu-mortality and archived with a DOI at https://doi.org/10.5281/zenodo.21107169. The repository includes the analysis pipeline, SQL extraction scripts, inference code, model card, and data dictionary. Raw patient-level data are not redistributed because access to MIMIC and local validation data is restricted.
```

## Zenodo release checklist

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the full publication-day checklist.

1. Push to the public GitHub repository.
2. In Zenodo, enable GitHub integration and select the repository.
3. Create a GitHub release (e.g. `v2.0.0`).
4. Confirm Zenodo generates a version DOI.
5. Replace Zenodo placeholders in this file, `README.md`, `CITATION.bib`, and the manuscript.
6. Add the Zenodo DOI to the point-by-point response letter.
