# Migration Plan

**Source:** `/Volumes/T9/Projects/capacity-sem-project`
**Target:** `/Volumes/T9/Projects/capacity-sem-migrated`
**Created:** 2025-12-25T21:52:34.759412
**Complexity:** medium

---

## Steps

### Setup

- [ ] **SETUP**: Create target directory structure
  - Details: mkdir -p src/stages src/utils tests doc figures data_raw data_work

- [ ] **SETUP**: Initialize git repository
  - Details: git init

- [ ] **SETUP**: Create virtual environment
  - Details: python -m venv .venv

- [ ] **SETUP**: Copy platform CLAUDE.md
  - Details: Copy AI agent instructions

- [ ] **SETUP**: Copy platform requirements.txt
  - Details: Base dependencies

### Copy

- [ ] **COPY**: Copy data/*
  - From: `data/*`
  - To: `data_raw/`
  - Details: Raw data files

- [ ] **COPY**: Copy data/*
  - From: `data/*`
  - To: `data_raw/`
  - Details: Raw data files

- [ ] **COPY**: Copy outputs/*
  - From: `outputs/*`
  - To: `manuscript_quarto/figures/`
  - Details: Output files

- [ ] **COPY**: Copy figures/*
  - From: `figures/*`
  - To: `manuscript_quarto/figures/`
  - Details: Output files

- [ ] **COPY**: Copy figures/*
  - From: `figures/*`
  - To: `manuscript_quarto/figures/`
  - Details: Output files

- [ ] **COPY**: Copy docs/*
  - From: `docs/*`
  - To: `doc/`
  - Details: Documentation

- [ ] **COPY**: Copy tests/*
  - From: `tests/*`
  - To: `tests/`
  - Details: Test suite

### Transform

- [ ] **TRANSFORM**: Merge modules into src/stages/s03_estimation.py
  - From: `src/capacity_sem/features/timeliness.py, src/capacity_sem/features/experience_indicators.py, src/capacity_sem/features/program_stratification.py...`
  - To: `src/stages/s03_estimation.py`
  - Details: Combine 8 source modules

- [ ] **TRANSFORM**: Merge modules into src/stages/s00_ingest.py
  - From: `src/capacity_sem/data/external_data.py, src/capacity_sem/data/__init__.py, src/capacity_sem/data/loader.py`
  - To: `src/stages/s00_ingest.py`
  - Details: Combine 3 source modules

### Generate

- [ ] **GENERATE**: Generate DATA_DICTIONARY.md
  - Details: Extract variable definitions from code

- [ ] **GENERATE**: Generate METHODOLOGY.md
  - Details: Document statistical methods from model code

- [ ] **GENERATE**: Generate PIPELINE.md
  - Details: Document pipeline stages and data flow

- [ ] **GENERATE**: Create pipeline.py CLI
  - Details: Main entry point with subcommands

### Verify

- [ ] **VERIFY**: Verify imports resolve
  - Details: Run: python -c 'import src.stages'

- [ ] **VERIFY**: Run existing tests
  - Details: pytest tests/

- [ ] **VERIFY**: Verify data loading
  - Details: python src/pipeline.py ingest_data

- [ ] **VERIFY**: Check documentation links
  - Details: Verify all doc references

---

## Notes

- Project contains Jupyter notebooks - manual review needed
