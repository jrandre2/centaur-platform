# Minimal End-to-End Demo

This demo provides a small dataset and expected outputs to validate the data → manuscript workflow.

## 1. Load the Sample Data

```bash
cp demo/sample_data.csv data_raw/
```

If `data_raw/` already contains other inputs, move them aside; `ingest_data` loads all matching files.

The sample data includes:
- `id` (unit identifier)
- `period` (time index)
- `treatment` (0/1)
- `outcome`
- `covariate_1`, `covariate_2`, `covariate_3`

## 2. Run the Pipeline

```bash
source .venv/bin/activate

python src/pipeline.py ingest_data
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation --specification baseline
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures
```

Optional (journal validation):

```bash
python src/pipeline.py validate_submission --journal jeem --report
```

Optional (render manuscript):

```bash
cd manuscript_quarto && ./render_all.sh
```

## 3. Expected Outputs

After running the pipeline, you should see:

**Data outputs**
- `data_work/data_raw.parquet` (12 rows)
- `data_work/data_linked.parquet` (12 rows, includes `source_file`, `link_status`)
- `data_work/panel.parquet` (12 rows, includes `unit_fe`, `time_fe`, `event_time`, `treatment_period`, `ever_treated`, `post_treatment`)

**Diagnostics**
- `data_work/diagnostics/linkage_summary.csv`
- `data_work/diagnostics/panel_summary.csv`
- `data_work/diagnostics/estimation_results.csv` (1 row for `baseline`)
- `data_work/diagnostics/coefficients.csv`
- `data_work/diagnostics/robustness_results.csv`
- `data_work/diagnostics/placebo_results.csv`

**Figures**
- `manuscript_quarto/figures/fig_event_study.png`
- `manuscript_quarto/figures/fig_trends.png`
- `manuscript_quarto/figures/fig_coefficients.png`
- `manuscript_quarto/figures/fig_robustness.png`
- `manuscript_quarto/figures/fig_distribution.png`

**Manuscript validation (optional)**
- `data_work/diagnostics/submission_validation.md`

**Rendered manuscript (optional, requires Quarto)**
- `manuscript_quarto/_output/index.html`
- `manuscript_quarto/_output/[Your-Paper-Title].pdf`
- `manuscript_quarto/_output/[Your-Paper-Title].docx`

PDF/DOCX filenames follow the `book.title` in `manuscript_quarto/_quarto.yml`.

## 4. Quick Sanity Checks

```bash
python -c "import pandas as pd; print(pd.read_parquet('data_work/data_raw.parquet').shape)"
python -c "import pandas as pd; print(pd.read_parquet('data_work/panel.parquet').shape)"
```

Expected output: `(12, <column_count>)` for both.
