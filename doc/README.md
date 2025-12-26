# Documentation Index

**Project**: Research Project Management Platform
**Scope**: Platform, scaffold, and workflow tools (not project-specific analysis)
**Last Updated**: 2025-12-25

---

## Quick Start

| Document | Location | Purpose |
|----------|----------|---------|
| **CLAUDE.md** | Root | AI agent project instructions |
| **README.md** | Root | Project overview, setup, key commands |
| **[TUTORIAL.md](TUTORIAL.md)** | doc/ | Step-by-step getting started guide |

---

## Core References

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow, extension points | Understanding the system |
| [PIPELINE.md](PIPELINE.md) | Pipeline stages and CLI commands | Running the pipeline |
| [METHODOLOGY.md](METHODOLOGY.md) | Statistical methods and equations | Methodology review |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Variable definitions and conventions | Variable lookups |

---

## Guides

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Getting started with demo data |
| [CUSTOMIZATION.md](CUSTOMIZATION.md) | Adapting platform scaffold to your project |
| [MANUSCRIPT_VARIANTS.md](MANUSCRIPT_VARIANTS.md) | Managing divergent manuscript drafts |
| [REPRODUCTION.md](REPRODUCTION.md) | Running analysis from scratch |
| [agents.md](agents.md) | AI agent guidelines |
| [skills.md](skills.md) | Available skills/actions |

---

## Synthetic Review System

| Document | Purpose |
|----------|---------|
| [SYNTHETIC_REVIEW_PROCESS.md](SYNTHETIC_REVIEW_PROCESS.md) | Review methodology and prompts |
| [MANUSCRIPT_REVISION_CHECKLIST.md](MANUSCRIPT_REVISION_CHECKLIST.md) | High-level revision status |
| [reviews/README.md](reviews/README.md) | Review cycles index |

**CLI Commands:**
- `python src/pipeline.py review_status` - Check status
- `python src/pipeline.py review_new --discipline economics` - Start new review
- `python src/pipeline.py review_archive` - Archive completed cycle
- `python src/pipeline.py review_verify` - Run verification
- `python src/pipeline.py review_report` - Summary report

---

## Pipeline Commands

### Data Processing
```bash
python src/pipeline.py ingest_data     # Load raw data (or generate demo data if empty)
python src/pipeline.py link_records    # Link data sources
python src/pipeline.py build_panel     # Construct panel
```

### Analysis
```bash
python src/pipeline.py run_estimation           # Run main estimation
python src/pipeline.py estimate_robustness      # Robustness checks
```

### Output
```bash
python src/pipeline.py make_figures             # Generate figures
python src/pipeline.py validate_submission      # Check manuscript
python src/pipeline.py audit_data [--full]      # Audit data files
```

---

## Journal Configuration

**CLI Commands:**
- `python src/pipeline.py journal_list` - List available configs
- `python src/pipeline.py journal_validate --config natural_hazards` - Validate config
- `python src/pipeline.py journal_compare --journal natural_hazards` - Compare manuscript
- `python src/pipeline.py journal_parse --input guidelines.txt --output new_journal.yml` - Parse guidelines

---

## Status Tracking

| Document | Purpose |
|----------|---------|
| [CHANGELOG.md](CHANGELOG.md) | Change history |

---

## Source Code

| Directory | Purpose |
|-----------|---------|
| `src/pipeline.py` | Main CLI entry point |
| `src/data_audit.py` | Data auditing utilities |
| `src/stages/` | Pipeline and workflow stages (s00-s08) |
| `src/agents/` | Project migration tools |
| `src/utils/` | Shared utilities |
| `tests/` | Test suite |

### Utilities

| Module | Purpose |
|--------|---------|
| `utils/helpers.py` | Path handling, data I/O, formatters |
| `utils/validation.py` | Data validation framework |
| `utils/figure_style.py` | Matplotlib styling |
| `utils/synthetic_data.py` | Demo data generation |

---

## Project Migration (AI Agent Tools)

AI-powered tools for analyzing and migrating external research projects.

| Document | Purpose |
|----------|---------|
| [AGENT_TOOLS.md](AGENT_TOOLS.md) | Agent module reference and API |
| [skills.md](skills.md) | Migration skills (/analyze-project, /map-project, etc.) |
| [MIGRATION_PLAN_capacity-sem.md](MIGRATION_PLAN_capacity-sem.md) | Example migration plan |

### Agent Modules

| Module | Purpose |
|--------|---------|
| `agents/project_analyzer.py` | Scan and analyze project structures |
| `agents/structure_mapper.py` | Map modules to platform stages |
| `agents/migration_planner.py` | Generate migration plans |
| `agents/migration_executor.py` | Execute migrations |

### CLI Commands

```bash
python src/pipeline.py analyze_project --path /path/to/project
python src/pipeline.py map_project --path /path/to/project
python src/pipeline.py plan_migration --path /source --target /target
python src/pipeline.py migrate_project --path /source --target /target --dry-run
```

---

## Adding New Documentation

When adding a new document:

1. Create the file in `doc/`
2. Add an entry to this index
3. Add a related link header to the new file:

```markdown
**Related**: [File1](file1.md) | [File2](file2.md)
**Status**: Active
**Last Updated**: YYYY-MM-DD
```

## Document Status Legend

- **Active** - In use, regularly updated
- **Template** - Placeholder for project-specific content
- **Reference** - Stable, infrequently changed
- **Archive** - Historical, moved to `archive/`
