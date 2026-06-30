# Local data directory (not redistributed)

Place your credentialed MIMIC feature export here:

```
data/mimic_dataset.xlsx
```

**Do not commit** patient-level files to version control.

## Required format

See [docs/preprocessing_excel.md](../docs/preprocessing_excel.md) for required sheets and columns.

## Quick start

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
```

Pipeline outputs are written under `result/analysis/` (also gitignored).
