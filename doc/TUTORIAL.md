# Tutorial: Getting Started

This tutorial walks through setting up and running the research pipeline from scratch using synthetic demo data.

## Prerequisites

- Python 3.10+
- pip or conda for package management
- Quarto (for manuscript rendering)

## Step 1: Setup and Configuration

### 1.1 Create Virtual Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.3 Verify Installation

```bash
# Check pipeline CLI
python src/pipeline.py --help

# Check Quarto (if installed)
quarto --version
```

### 1.4 Create Data Directories

```bash
mkdir -p data_raw data_work/diagnostics figures
```

## Step 2: Data Ingestion

### 2.1 Using Demo Data

The pipeline can generate synthetic demo data for testing:

```bash
python src/pipeline.py ingest_data --demo
```

This creates `data_work/data_raw.parquet` with:
- 1,000 synthetic units
- 24 time periods
- Treatment and outcome variables
- Covariates

### 2.2 Using Your Own Data

Place your data files in `data_raw/`:

```bash
# CSV files
cp your_data.csv data_raw/

# Then ingest
python src/pipeline.py ingest_data
```

The ingestion stage:
1. Loads CSV/Excel/Parquet files
2. Cleans column names
3. Validates data quality
4. Saves as parquet format

### 2.3 Verify Ingestion

```bash
# Check output file
python -c "import pandas as pd; df = pd.read_parquet('data_work/data_raw.parquet'); print(df.info())"

# View validation report
cat data_work/diagnostics/ingest_validation.csv
```

## Step 3: Record Linkage

If you have multiple data sources to merge:

```bash
python src/pipeline.py link_records
```

For demo data (single source), this passes through with linkage metadata:

```bash
python src/pipeline.py link_records --verbose
```

Output: `data_work/data_linked.parquet`

### Linkage Options

```bash
# Specify key columns
python src/pipeline.py link_records --keys id entity_id

# Add additional sources
python src/pipeline.py link_records --sources additional_data.parquet
```

## Step 4: Panel Construction

Build the analysis panel with fixed effects and event study variables:

```bash
python src/pipeline.py build_panel --verbose
```

This creates:
- Balanced or unbalanced panel
- Unit and time fixed effects
- Event time indicators (for treatment timing)
- Treatment status variables

### Panel Options

```bash
# Balance panel (keep only complete observations)
python src/pipeline.py build_panel --balance

# Specify treatment timing column
python src/pipeline.py build_panel --treatment-col treatment_start
```

Output: `data_work/panel.parquet`

### Verify Panel Structure

```bash
python -c "
import pandas as pd
df = pd.read_parquet('data_work/panel.parquet')
print('Units:', df['unit_id'].nunique())
print('Periods:', df['period'].nunique())
print('Obs:', len(df))
"
```

## Step 5: Estimation

Run the main treatment effect estimation:

```bash
python src/pipeline.py run_estimation --verbose
```

This runs all specifications defined in the specification registry:

| Specification | Description |
|--------------|-------------|
| `baseline` | Treatment effect only |
| `with_controls` | Treatment + covariates |
| `unit_fe` | Unit fixed effects |
| `twoway_fe` | Unit + time fixed effects |

### Estimation Options

```bash
# Run specific specification
python src/pipeline.py run_estimation --spec baseline

# Use robust standard errors
python src/pipeline.py run_estimation --se robust

# Cluster at different level
python src/pipeline.py run_estimation --cluster state_id
```

### View Results

```bash
# Quick results summary
cat data_work/diagnostics/estimation_results.csv

# Or in Python
python -c "
import pandas as pd
results = pd.read_csv('data_work/diagnostics/estimation_results.csv')
print(results[['specification', 'coefficient', 'std_error', 'p_value']].to_string())
"
```

## Step 6: Robustness Checks

Run sensitivity analyses:

```bash
python src/pipeline.py estimate_robustness --verbose
```

This runs:
- Placebo tests (fake treatment timing)
- Sample restrictions (exclude endpoints, subsamples)
- Alternative specifications

### Robustness Options

```bash
# Skip placebo tests
python src/pipeline.py estimate_robustness --no-placebos

# Only sample restrictions
python src/pipeline.py estimate_robustness --samples-only
```

Output: `data_work/diagnostics/robustness_results.csv`

## Step 7: Figure Generation

Create publication-quality figures:

```bash
python src/pipeline.py make_figures
```

Generated figures:
- `figures/fig_event_study.png` - Dynamic treatment effects
- `figures/fig_trends.png` - Treatment vs. control trends
- `figures/fig_coefficients.png` - Coefficient comparison
- `figures/fig_robustness.png` - Robustness results
- `figures/fig_distribution.png` - Outcome distribution

### Figure Options

```bash
# Generate specific figure
python src/pipeline.py make_figures --only event_study

# Use different style
python src/pipeline.py make_figures --style presentation

# Custom output directory
python src/pipeline.py make_figures --output manuscript_quarto/figures/
```

### Customize Figure Style

Edit `src/utils/figure_style.py` to modify:
- Color palettes
- Font sizes
- Figure dimensions
- Journal-specific presets

## Step 8: Manuscript Validation

Validate manuscript against journal requirements:

```bash
# Validate for default journal
python src/pipeline.py validate_submission

# Validate for specific journal
python src/pipeline.py validate_submission --journal jeem

# Generate report
python src/pipeline.py validate_submission --journal jeem --report
```

Checks performed:
- Word count limits
- Abstract length
- Required sections
- Figure formats
- Reference completeness

Output: `data_work/diagnostics/submission_validation.md`

## Step 9: Render Manuscript

### Prerequisites

Ensure Quarto is installed:

```bash
quarto --version
```

### Render All Formats

```bash
cd manuscript_quarto
./render_all.sh
```

This creates:
- `_output/index.html` - Web version
- `_output/Manuscript.pdf` - PDF version
- `_output/Manuscript.docx` - Word version

### Render with Journal Profile

```bash
# Use JEEM formatting
quarto render --profile jeem

# Use custom journal
quarto render --profile custom_journal
```

### Preview During Writing

```bash
quarto preview
```

Opens live preview in browser, auto-refreshes on file changes.

## Step 10: Data Audit

Audit the pipeline data files:

```bash
# Quick audit
python src/pipeline.py audit_data

# Full audit with column details
python src/pipeline.py audit_data --full

# Generate markdown report
python src/pipeline.py audit_data --full --report
```

The audit tracks:
- Row counts at each stage
- Column availability
- Sample attrition
- Data quality metrics

## Complete Workflow

Run the entire pipeline:

```bash
# Activate environment
source .venv/bin/activate

# Run all stages
python src/pipeline.py ingest_data --demo
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures
python src/pipeline.py validate_submission --report

# Render manuscript
cd manuscript_quarto && ./render_all.sh
```

Or create a shell script:

```bash
#!/bin/bash
# run_pipeline.sh

set -e  # Exit on error

source .venv/bin/activate

echo "Running research pipeline..."

python src/pipeline.py ingest_data --demo
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures
python src/pipeline.py validate_submission --report

echo "Pipeline complete. Rendering manuscript..."
cd manuscript_quarto && ./render_all.sh

echo "Done!"
```

## Running Tests

Verify the pipeline works correctly:

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_utils/test_helpers.py

# Run with coverage report
pytest --cov=src tests/
```

## Troubleshooting

### Common Issues

**1. Module not found**

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Data file not found**

```bash
# Check data directories exist
ls -la data_raw data_work

# Run from project root
cd /path/to/project
python src/pipeline.py ingest_data
```

**3. Quarto render fails**

```bash
# Check Quarto installation
quarto check

# Verify _quarto.yml exists
ls manuscript_quarto/_quarto.yml

# Try rendering single file
quarto render manuscript_quarto/index.qmd
```

**4. Figure generation fails**

```bash
# Check matplotlib backend
python -c "import matplotlib; print(matplotlib.get_backend())"

# Run with non-interactive backend
MPLBACKEND=Agg python src/pipeline.py make_figures
```

### Getting Help

- Check [doc/README.md](README.md) for documentation index
- Review [doc/ARCHITECTURE.md](ARCHITECTURE.md) for system overview
- See [doc/PIPELINE.md](PIPELINE.md) for stage details
- Run `python src/pipeline.py --help` for CLI options

## Next Steps

After completing this tutorial:

1. **Customize for your data** - See [CUSTOMIZATION.md](CUSTOMIZATION.md)
2. **Understand methodology** - See [METHODOLOGY.md](METHODOLOGY.md)
3. **Define your variables** - See [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
4. **Configure journal** - Edit `manuscript_quarto/journal_configs/`
5. **Write manuscript** - Edit `manuscript_quarto/index.qmd`
