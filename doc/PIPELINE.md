# Pipeline Documentation

**Related**: [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | [METHODOLOGY.md](METHODOLOGY.md)
**Status**: Active
**Last Updated**: 2025-12-25

---

## TL;DR

```bash
source .venv/bin/activate

# Full pipeline
python src/pipeline.py ingest_data
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation --specification baseline
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures

# Render manuscript
cd manuscript_quarto && ./render_all.sh
```

Note: `ingest_data` generates synthetic demo data if `data_raw/` has no matching files.

Journal validation is optional. If no journal config is set, skip `validate_submission` and render with Quarto only. When a journal config exists, `validate_submission` enforces word counts, section requirements, and formatting rules.

Review cycles are handled through `review_new`, `review_verify`, and `review_archive`, with `manuscript_quarto/REVISION_TRACKER.md` and `doc/reviews/archive/` preserving responses. Divergent drafts use manuscript variants (see `doc/MANUSCRIPT_VARIANTS.md`).

---

## Pipeline Overview

```
data_raw/ ──► ingest_data ──► data_work/data_raw.parquet
                           │
                           ▼
                link_records ──► data_work/data_linked.parquet
                           │           └─► data_work/diagnostics/linkage_summary.csv
                           ▼
                build_panel ──► data_work/panel.parquet
                           │           └─► data_work/diagnostics/panel_summary.csv
                           ▼
             run_estimation ──► data_work/diagnostics/estimation_results.csv
                           │           └─► data_work/diagnostics/coefficients.csv
                           ▼
          estimate_robustness ──► data_work/diagnostics/robustness_results.csv
                           │           └─► data_work/diagnostics/placebo_results.csv
                           ▼
              make_figures ──► manuscript_quarto/figures/*.png ──► render_all.sh ──► manuscript_quarto/_output/
```

---

## Stage Details

### Stage 00: Data Ingestion

**Command:** `python src/pipeline.py ingest_data`

**Purpose:** Load and preprocess raw data files. Generates synthetic demo data if no inputs exist in `data_raw/`.

**Input:** `data_raw/`
**Output:** `data_work/data_raw.parquet`

**Implementation:** `src/stages/s00_ingest.py`

---

### Stage 01: Record Linkage

**Command:** `python src/pipeline.py link_records`

**Purpose:** Link records across multiple data sources.

**Input:** `data_work/data_raw.parquet`
**Output:** `data_work/data_linked.parquet`
**Diagnostics:** `data_work/diagnostics/linkage_summary.csv`

**Implementation:** `src/stages/s01_link.py`

---

### Stage 02: Panel Construction

**Command:** `python src/pipeline.py build_panel`

**Purpose:** Create the analysis panel from linked data.

**Input:** `data_work/data_linked.parquet`
**Output:** `data_work/panel.parquet`
**Diagnostics:** `data_work/diagnostics/panel_summary.csv`

**Implementation:** `src/stages/s02_panel.py`

---

### Stage 03: Primary Estimation

**Command:** `python src/pipeline.py run_estimation [options]`

**Options:**
- `--specification, -s`: Specification name (default: baseline)
- `--sample`: Sample restriction (default: full)

**Purpose:** Run primary estimation specifications.

**Input:** `data_work/panel.parquet`
**Output:** `data_work/diagnostics/estimation_results.csv`, `data_work/diagnostics/coefficients.csv`

**Implementation:** `src/stages/s03_estimation.py`

---

### Stage 04: Robustness Checks

**Command:** `python src/pipeline.py estimate_robustness`

**Purpose:** Run robustness specifications and sensitivity analyses.

**Input:** `data_work/panel.parquet`
**Output:** `data_work/diagnostics/robustness_results.csv`, `data_work/diagnostics/placebo_results.csv`

**Implementation:** `src/stages/s04_robustness.py`

---

### Stage 05: Figure Generation

**Command:** `python src/pipeline.py make_figures`

**Purpose:** Generate publication-quality figures.

**Input:** `data_work/panel.parquet`, `data_work/diagnostics/*.csv`
**Output:** `manuscript_quarto/figures/*.png`

**Implementation:** `src/stages/s05_figures.py`

If you need a top-level export, copy from `manuscript_quarto/figures/` to `figures/`.

---

### Stage 06: Manuscript Validation

**Command:** `python src/pipeline.py validate_submission [options]`

**Options:**
- `--journal, -j`: Target journal (default: jeem)
- `--report`: Generate markdown report

**Purpose:** Validate manuscript against journal requirements.

**Output (with `--report`):** `data_work/diagnostics/submission_validation.md`

**Implementation:** `src/stages/s06_manuscript.py`

---

### Stage 07: Review Management

**Commands:**
- `python src/pipeline.py review_status`
- `python src/pipeline.py review_new --discipline economics`
- `python src/pipeline.py review_verify`
- `python src/pipeline.py review_archive`
- `python src/pipeline.py review_report`

**Purpose:** Manage synthetic peer review cycles and track responses.

**Outputs:**
- `manuscript_quarto/REVISION_TRACKER.md`
- `doc/reviews/archive/` (archived reviews)

**Implementation:** `src/stages/s07_reviews.py`

---

### Stage 08: Journal Configuration Tools

**Commands:**
- `python src/pipeline.py journal_list`
- `python src/pipeline.py journal_validate --config natural_hazards`
- `python src/pipeline.py journal_compare --journal natural_hazards`
- `python src/pipeline.py journal_parse --input guidelines.txt --output new_journal.yml`

**Purpose:** List, validate, compare, and parse journal requirements.

**Outputs:**
- `manuscript_quarto/journal_configs/<name>.yml` (for `journal_parse`)

**Implementation:** `src/stages/s08_journal_parser.py`

---

## Manuscript Rendering

### Render All Formats

```bash
cd manuscript_quarto
./render_all.sh
```

Output in `manuscript_quarto/_output/`:
- HTML files
- PDF
- DOCX

PDF/DOCX filenames follow the `book.title` in `manuscript_quarto/_quarto.yml`.

### Journal-Specific Rendering

```bash
./render_all.sh --profile jeem   # JEEM format
./render_all.sh --profile aer    # AER format
```

### Live Preview

```bash
cd manuscript_quarto
../tools/bin/quarto preview
```

---

## Data Audit

```bash
python src/pipeline.py audit_data
python src/pipeline.py audit_data --full
python src/pipeline.py audit_data --full --report
```

`audit_data` prints a summary to the console and optionally writes a markdown report to `data_work/diagnostics/`.

---

## Common Workflows

### Full Rebuild

```bash
source .venv/bin/activate
python src/pipeline.py ingest_data
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures
cd manuscript_quarto && ./render_all.sh
```

### Update After Data Change

```bash
python src/pipeline.py ingest_data
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures
```

### Update Figures Only

```bash
python src/pipeline.py make_figures
cd manuscript_quarto && ./render_all.sh
```

---

## Minimal Demo

See `demo/README.md` for a small sample dataset and expected outputs that exercise the full data → manuscript path.
