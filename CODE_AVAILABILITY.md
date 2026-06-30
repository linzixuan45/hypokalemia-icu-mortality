# Code Availability

## Research demonstration calculator

- URL: https://k.mixaihub.top
- Purpose: 8-feature research probability calculator with SHAP audit (not for clinical use)

## GitHub

- Repository: `[GitHub URL — fill after public push]`
- Release tag: `v1.0.0` (recommended)

## Zenodo (DOI-assigning archive)

- Concept DOI: `[Zenodo concept DOI — fill after linking GitHub]`
- Version DOI: `[Zenodo version DOI — fill after release]`

## What is deposited

The archived repository includes:

- Analysis pipeline (`scripts/`)
- MIMIC SQL extraction scripts (`sql/`)
- Inference code (`inference.py`)
- Released 8-feature model bundle (`model_weights/8_features_model.pkl`)
- Model card and data dictionary (`MODEL_CARD.md`, `docs/data_dictionary.md`)
- Methods documentation (`docs/MC1_spec.md`, `docs/data_flow_cohorts.md`)

Raw patient-level data, cohort ID lists, and summary result tables are **not** redistributed because MIMIC and local validation data are access-restricted.

## Manuscript text (paste into Methods or Code Availability)

```text
An HTTPS research demonstration calculator for the 8-feature model is available at https://k.mixaihub.top (not for clinical use). The underlying code and released research model bundle are available at [GitHub URL] and archived with a DOI at [Zenodo DOI]. The repository includes the analysis pipeline, SQL extraction scripts, inference code, model card, and data dictionary. Raw patient-level data are not redistributed because access to MIMIC and local validation data is restricted.
```

## Zenodo release checklist

1. Push `Project_low_K` to a public GitHub repository.
2. In Zenodo, enable GitHub integration and select the repository.
3. Create a GitHub release (e.g. `v1.0.0`).
4. Confirm Zenodo generates a version DOI.
5. Replace placeholders in this file, `README.md`, and the manuscript.
6. Add the Zenodo DOI to the point-by-point response letter.
