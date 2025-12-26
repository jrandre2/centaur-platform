# Research Project Management Software - Claude Code Instructions

## Quick Start

```bash
source .venv/bin/activate  # REQUIRED for all scripts
```

### Common Commands

```bash
# Run pipeline stages
python src/pipeline.py ingest_data
python src/pipeline.py run_estimation --specification baseline
python src/pipeline.py make_figures

# Render manuscript
cd manuscript_quarto && ./render_all.sh
cd manuscript_quarto && ./render_all.sh --profile jeem  # Journal-specific

# Synthetic review management
python src/pipeline.py review_status              # Check status
python src/pipeline.py review_new -d economics    # Start new review
python src/pipeline.py review_verify              # Run verification
python src/pipeline.py review_archive             # Archive completed

# Project migration tools
python src/pipeline.py analyze_project --path /path/to/project
python src/pipeline.py map_project --path /path/to/project
python src/pipeline.py plan_migration --path /source --target /target
python src/pipeline.py migrate_project --path /source --target /target --dry-run
```

## Key Concepts

### AI-Powered Project Migration

This software provides tools for analyzing and migrating existing research projects to a standardized template format.

1. **Project Analyzer** - Scans project directories, extracts Python module metadata (imports, functions, classes, docstrings)
2. **Structure Mapper** - Maps source modules to template stages (s00-s07) based on content keywords
3. **Migration Planner** - Generates actionable migration plans with setup, copy, transform, generate, and verify steps
4. **Migration Executor** - Executes plans with dry-run support, creates scaffold files for manual code merge

### Template Stage Pattern

| Stage | Purpose | Keywords |
|-------|---------|----------|
| `s00_ingest.py` | Data ingestion | load, ingest, read |
| `s01_link.py` | Record linkage | link, merge, join |
| `s02_panel.py` | Panel construction | panel, construct, balance |
| `s03_estimation.py` | Main estimation | model, estim, regress |
| `s04_robustness.py` | Robustness checks | robust, sensitiv, placebo |
| `s05_figures.py` | Figure generation | figure, plot, viz |
| `s06_manuscript.py` | Manuscript validation | manuscript, valid, check |
| `s07_reviews.py` | Review management | review, cycle |

### Data Conventions

- **Source projects**: Analyzed from any directory structure
- **Target projects**: Follow `src/stages/sXX_name.py` naming pattern
- **Data files**: Raw data in `data_raw/`, working data in `data_work/`
- **Outputs**: Figures in `figures/`, diagnostics in `data_work/diagnostics/`

## Critical Constraints

### DO NOT

- Modify raw data in `data_raw/`
- Modify source projects during migration (copy only)
- Execute migrations without testing with `--dry-run` first

### ALWAYS

- Activate `.venv` before running scripts
- Run diagnostics after estimation changes
- Re-render Quarto after modifying `.qmd` files
- Review `MIGRATION_REPORT.md` after executing migrations

## Data Files

| File | Purpose |
|------|---------|
| `data_work/panel.parquet` | Main analysis panel |
| `data_work/diagnostics/*.csv` | Estimation diagnostics |

## Agent Modules

| Module | Purpose |
|--------|---------|
| `src/agents/project_analyzer.py` | Scan and analyze project structures |
| `src/agents/structure_mapper.py` | Map modules to template stages |
| `src/agents/migration_planner.py` | Generate migration plans |
| `src/agents/migration_executor.py` | Execute migrations |

## Manuscript

Location: `manuscript_quarto/`

### Rendering All Formats

**Problem:** Quarto book projects overwrite `_output/` on each render.

**Solution:** Use `render_all.sh`:

```bash
cd manuscript_quarto
./render_all.sh                    # All formats (HTML, PDF, DOCX)
./render_all.sh --profile jeem     # JEEM submission format
./render_all.sh --profile aer      # AER submission format
```

Output files in `manuscript_quarto/_output/`:
- `index.html` (+ appendix HTMLs)
- `[ProjectName].pdf`
- `[ProjectName].docx`

### Manuscript Writing Standards

**DO NOT include in manuscript prose:**

- References to Python scripts or file paths (e.g., `script.py`, `src/...`)
- Internal documentation references
- Metacommentary about the writing process
- TODO/FIXME placeholders

**All manuscript text should be:**

- Self-contained academic prose
- Supported by formal citations where needed
- Free of implementation details visible only to developers

## Synthetic Peer Review

Use synthetic reviews to stress-test methodology before submission.

### Workflow

1. **Generate**: `python src/pipeline.py review_new --discipline economics`
2. **Triage**: Classify comments in `manuscript_quarto/REVISION_TRACKER.md`
3. **Track**: Update checklist as changes are made
4. **Verify**: `python src/pipeline.py review_verify`
5. **Archive**: `python src/pipeline.py review_archive`

### Status Classifications

- `VALID - ACTION NEEDED` - Requires changes
- `ALREADY ADDRESSED` - Already handled
- `BEYOND SCOPE` - Valid but deferred
- `INVALID` - Reviewer misunderstanding

### Discipline Templates

- `economics` - Identification, causal inference, econometrics
- `engineering` - Reproducibility, benchmarks, validation
- `social_sciences` - Theory, generalizability, ethics
- `general` - Structure, clarity, contribution

See `doc/SYNTHETIC_REVIEW_PROCESS.md` for full methodology.

## Project Migration Tools

AI-powered tools for analyzing and migrating external research projects.

### Migration Workflow

```bash
# 1. Analyze project structure
python src/pipeline.py analyze_project --path /path/to/project

# 2. See how it maps to template
python src/pipeline.py map_project --path /path/to/project

# 3. Generate migration plan
python src/pipeline.py plan_migration --path /source --target /target --output plan.md

# 4. Test with dry-run
python src/pipeline.py migrate_project --path /source --target /target --dry-run

# 5. Execute migration
python src/pipeline.py migrate_project --path /source --target /target
```

### Migration Step Categories

1. **Setup** - Create directory structure, git init, virtual environment
2. **Copy** - Transfer data, figures, docs, tests to standard locations
3. **Transform** - Create scaffold stage files with merge instructions
4. **Generate** - Create documentation templates (DATA_DICTIONARY.md, etc.)
5. **Verify** - Check imports, run tests, validate documentation

### Post-Migration Tasks

After migration, review `MIGRATION_REPORT.md` in the target directory:
- Complete scaffold files by merging source code
- Fill in documentation templates
- Run verification steps manually

See `doc/AGENT_TOOLS.md` for complete module reference.

## Documentation

See `doc/README.md` for complete index:

- `doc/PIPELINE.md` - Pipeline stages and commands
- `doc/METHODOLOGY.md` - Statistical methods
- `doc/DATA_DICTIONARY.md` - Variable definitions
- `doc/SYNTHETIC_REVIEW_PROCESS.md` - Review methodology
- `doc/AGENT_TOOLS.md` - Project migration agent reference
- `doc/agents.md` - AI agent guidelines
- `doc/skills.md` - Available skills/actions

## Troubleshooting

**Git hangs:** `rm -f .git/index.lock` (if no git operation running)

**Quarto errors:** Check that `.venv` is activated and all dependencies installed

**OneDrive issues:** See `doc/agents.md`
