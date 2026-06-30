# Local data directory (not redistributed)

Patient-level files are **not** included in this repository. See [docs/USER_GUIDE.md](../docs/USER_GUIDE.md) for what the deposit provides.

Place your credentialed MIMIC feature export here:

```
data/mimic_dataset.xlsx
```

**Do not commit** patient-level files to version control.

## Required format

See [docs/preprocessing_excel.md](../docs/preprocessing_excel.md) for required sheets and columns.

## Re-running the pipeline

```bash
python scripts/validate_excel_input.py
python scripts/run_pipeline.py
```

Pipeline outputs are written under `result/analysis/` (also gitignored). Metrics may differ slightly from the manuscript when using the default Excel t₀ proxy.
