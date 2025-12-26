#!/usr/bin/env python3
"""
Module: pipeline.py
Purpose: Main orchestration CLI for the research analysis pipeline.

This module provides a command-line interface to execute individual stages
of the analysis pipeline. Each stage processes data and produces intermediate
or final outputs.

Commands
--------
# Data Processing
ingest_data : Load and preprocess raw data
    Output: data_work/data_raw.parquet
link_records : Link records across data sources
    Output: data_work/data_linked.parquet
build_panel : Create analysis panel
    Output: data_work/panel.parquet

# Analysis
run_estimation : Run primary estimation
    Options: --specification, --sample
estimate_robustness : Run robustness checks
    Output: data_work/diagnostics/

# Figures and Manuscript
make_figures : Generate publication figures
    Output: manuscript_quarto/figures/*.png
validate_submission : Validate against journal requirements
    Options: --journal, --report

# Review Management
review_status : Show current review cycle status
review_new : Initialize new review cycle
    Options: --discipline
review_archive : Archive current cycle and reset
review_verify : Run verification checklist
review_report : Generate summary of all review cycles

# Journal Configuration
journal_list : List available journal configurations
journal_validate : Validate journal config against template
    Options: --config
journal_compare : Compare manuscript to journal requirements
    Options: --journal, --manuscript
journal_parse : Parse raw guidelines into config
    Options: --input, --output, --journal

# Data Audit
audit_data : Audit pipeline data files
    Options: --full, --report, --output

# Project Migration (AI Agent Tools)
analyze_project : Analyze external project structure
    Options: --path, --output
map_project : Map project structure to template
    Options: --path, --output
plan_migration : Generate migration plan
    Options: --path, --target, --output
migrate_project : Execute migration (interactive)
    Options: --path, --target, --dry-run

Usage
-----
    python src/pipeline.py ingest_data
    python src/pipeline.py run_estimation --specification baseline

Notes
-----
Requires activation of project virtual environment before running.
"""
from __future__ import annotations

import os
import sys
import argparse


def ensure_env():
    """Verify virtual environment is activated."""
    venv = os.getenv('VIRTUAL_ENV')
    if not venv or not venv.endswith('/.venv'):
        print(
            'ERROR: Please activate project .venv (source .venv/bin/activate) before running.',
            file=sys.stderr
        )
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        description='Research Project Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest='cmd', required=True)

    # Data Processing Commands
    sub.add_parser('ingest_data', help='Load and preprocess raw data')
    sub.add_parser('link_records', help='Link records across data sources')
    sub.add_parser('build_panel', help='Create analysis panel')

    # Estimation Commands
    p_est = sub.add_parser('run_estimation', help='Run primary estimation')
    p_est.add_argument(
        '--specification', '-s',
        default='baseline',
        help='Specification name (default: baseline)'
    )
    p_est.add_argument(
        '--sample',
        default='full',
        help='Sample restriction (default: full)'
    )

    sub.add_parser('estimate_robustness', help='Run robustness checks')

    # Figure and Manuscript Commands
    sub.add_parser('make_figures', help='Generate publication figures')

    p_val = sub.add_parser('validate_submission', help='Validate manuscript')
    p_val.add_argument(
        '--journal', '-j',
        default='jeem',
        help='Target journal (default: jeem)'
    )
    p_val.add_argument(
        '--report',
        action='store_true',
        help='Generate markdown report'
    )

    # Review Management Commands
    sub.add_parser('review_status', help='Show current review cycle status')

    p_new = sub.add_parser('review_new', help='Initialize new review cycle')
    p_new.add_argument(
        '--discipline', '-d',
        default='general',
        choices=['economics', 'engineering', 'social_sciences', 'general'],
        help='Discipline for review prompts (default: general)'
    )

    sub.add_parser('review_archive', help='Archive current cycle and reset')
    sub.add_parser('review_verify', help='Run verification checklist')
    sub.add_parser('review_report', help='Generate summary of all review cycles')

    # Journal Configuration Commands
    sub.add_parser('journal_list', help='List available journal configurations')

    p_jval = sub.add_parser('journal_validate', help='Validate journal config')
    p_jval.add_argument(
        '--config', '-c',
        default='natural_hazards',
        help='Config file name without .yml (default: natural_hazards)'
    )

    p_jcmp = sub.add_parser('journal_compare', help='Compare manuscript to journal')
    p_jcmp.add_argument(
        '--journal', '-j',
        default='natural_hazards',
        help='Journal config name (default: natural_hazards)'
    )
    p_jcmp.add_argument(
        '--manuscript', '-m',
        default=None,
        help='Path to manuscript directory (default: manuscript_quarto/)'
    )

    p_jparse = sub.add_parser('journal_parse', help='Parse guidelines into config')
    p_jparse.add_argument(
        '--input', '-i',
        required=True,
        help='Input file with raw guidelines'
    )
    p_jparse.add_argument(
        '--output', '-o',
        default='new_journal.yml',
        help='Output config filename (default: new_journal.yml)'
    )
    p_jparse.add_argument(
        '--journal', '-j',
        default=None,
        help='Journal name (optional)'
    )

    # Data Audit Commands
    p_audit = sub.add_parser('audit_data', help='Audit pipeline data files')
    p_audit.add_argument(
        '--full', '-f',
        action='store_true',
        help='Run full audit with detailed column info'
    )
    p_audit.add_argument(
        '--report', '-r',
        action='store_true',
        help='Save markdown report to data_work/diagnostics/'
    )
    p_audit.add_argument(
        '--output', '-o',
        default=None,
        help='Output path for JSON report'
    )

    # Project Migration Commands (AI Agent Tools)
    p_analyze = sub.add_parser('analyze_project', help='Analyze external project structure')
    p_analyze.add_argument(
        '--path', '-p',
        required=True,
        help='Path to project to analyze'
    )
    p_analyze.add_argument(
        '--output', '-o',
        default=None,
        help='Output file for JSON analysis (optional)'
    )

    p_map = sub.add_parser('map_project', help='Map project structure to template')
    p_map.add_argument(
        '--path', '-p',
        required=True,
        help='Path to project to map'
    )
    p_map.add_argument(
        '--output', '-o',
        default=None,
        help='Output file for mapping (optional)'
    )

    p_plan = sub.add_parser('plan_migration', help='Generate migration plan')
    p_plan.add_argument(
        '--path', '-p',
        required=True,
        help='Path to source project'
    )
    p_plan.add_argument(
        '--target', '-t',
        required=True,
        help='Path for migrated project'
    )
    p_plan.add_argument(
        '--output', '-o',
        default=None,
        help='Output file for plan (optional)'
    )

    p_migrate = sub.add_parser('migrate_project', help='Execute migration')
    p_migrate.add_argument(
        '--path', '-p',
        required=True,
        help='Path to source project'
    )
    p_migrate.add_argument(
        '--target', '-t',
        required=True,
        help='Path for migrated project'
    )
    p_migrate.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    return p.parse_args()


def main():
    """Main entry point."""
    ensure_env()
    args = parse_args()

    if args.cmd == 'ingest_data':
        from stages import s00_ingest
        s00_ingest.main()

    elif args.cmd == 'link_records':
        from stages import s01_link
        s01_link.main()

    elif args.cmd == 'build_panel':
        from stages import s02_panel
        s02_panel.main()

    elif args.cmd == 'run_estimation':
        from stages import s03_estimation
        s03_estimation.main(
            specification=args.specification,
            sample=args.sample
        )

    elif args.cmd == 'estimate_robustness':
        from stages import s04_robustness
        s04_robustness.main()

    elif args.cmd == 'make_figures':
        from stages import s05_figures
        s05_figures.main()

    elif args.cmd == 'validate_submission':
        from stages import s06_manuscript
        s06_manuscript.validate(
            journal=args.journal,
            report=args.report
        )

    # Review Management Commands
    elif args.cmd == 'review_status':
        from stages import s07_reviews
        s07_reviews.status()

    elif args.cmd == 'review_new':
        from stages import s07_reviews
        s07_reviews.new_cycle(discipline=args.discipline)

    elif args.cmd == 'review_archive':
        from stages import s07_reviews
        s07_reviews.archive()

    elif args.cmd == 'review_verify':
        from stages import s07_reviews
        s07_reviews.verify()

    elif args.cmd == 'review_report':
        from stages import s07_reviews
        s07_reviews.report()

    # Journal Configuration Commands
    elif args.cmd == 'journal_list':
        from stages import s08_journal_parser
        s08_journal_parser.list_configs()

    elif args.cmd == 'journal_validate':
        from stages import s08_journal_parser
        s08_journal_parser.validate_config(args.config)

    elif args.cmd == 'journal_compare':
        from stages import s08_journal_parser
        s08_journal_parser.compare_manuscript(args.journal, args.manuscript)

    elif args.cmd == 'journal_parse':
        from stages import s08_journal_parser
        s08_journal_parser.parse_guidelines(
            input_file=args.input,
            output_file=args.output,
            journal_name=args.journal
        )

    # Data Audit Commands
    elif args.cmd == 'audit_data':
        import data_audit
        data_audit.main(
            full=args.full,
            report=args.report,
            output=args.output
        )

    # Project Migration Commands (AI Agent Tools)
    elif args.cmd == 'analyze_project':
        from pathlib import Path
        from agents.project_analyzer import ProjectAnalyzer

        analyzer = ProjectAnalyzer(Path(args.path))
        analysis = analyzer.analyze()

        print(analysis.summary())

        if args.output:
            Path(args.output).write_text(analysis.to_json())
            print(f"\nJSON saved to: {args.output}")

    elif args.cmd == 'map_project':
        from pathlib import Path
        from agents.project_analyzer import ProjectAnalyzer
        from agents.structure_mapper import StructureMapper

        analyzer = ProjectAnalyzer(Path(args.path))
        analysis = analyzer.analyze()

        mapper = StructureMapper(analysis)
        mapping = mapper.generate_mapping()

        print(mapping.summary())

        if args.output:
            Path(args.output).write_text(mapping.to_json())
            print(f"\nJSON saved to: {args.output}")

    elif args.cmd == 'plan_migration':
        from pathlib import Path
        from agents.project_analyzer import ProjectAnalyzer
        from agents.structure_mapper import StructureMapper
        from agents.migration_planner import MigrationPlanner

        analyzer = ProjectAnalyzer(Path(args.path))
        analysis = analyzer.analyze()

        mapper = StructureMapper(analysis)
        mapping = mapper.generate_mapping()

        planner = MigrationPlanner(analysis, mapping)
        plan = planner.generate_plan(args.target)

        print(plan.to_markdown())

        if args.output:
            Path(args.output).write_text(plan.to_markdown())
            print(f"\nPlan saved to: {args.output}")

    elif args.cmd == 'migrate_project':
        from pathlib import Path
        from agents.project_analyzer import ProjectAnalyzer
        from agents.structure_mapper import StructureMapper
        from agents.migration_planner import MigrationPlanner
        from agents.migration_executor import MigrationExecutor

        source_path = Path(args.path)
        target_path = Path(args.target)

        # Get the template path (this project's root)
        template_path = Path(__file__).parent.parent

        print(f"Analyzing source project: {source_path}")
        analyzer = ProjectAnalyzer(source_path)
        analysis = analyzer.analyze()

        print(f"Mapping to template structure...")
        mapper = StructureMapper(analysis)
        mapping = mapper.generate_mapping()

        print(f"Generating migration plan...")
        planner = MigrationPlanner(analysis, mapping)
        plan = planner.generate_plan(str(target_path))

        print(f"\n{'DRY RUN - ' if args.dry_run else ''}Executing migration...")
        print(f"  Source: {source_path}")
        print(f"  Target: {target_path}")
        print(f"  Steps: {len(plan.steps)}")
        print()

        executor = MigrationExecutor(
            plan=plan,
            source_path=source_path,
            template_path=template_path,
            dry_run=args.dry_run,
            verbose=True
        )

        report = executor.execute()

        print()
        print("=" * 60)
        print("MIGRATION COMPLETE" if report.overall_success else "MIGRATION FAILED")
        print("=" * 60)
        print(f"  Successful: {report.success_count}/{len(report.results)}")
        print(f"  Failed: {report.failure_count}/{len(report.results)}")

        # Save execution report
        report_path = target_path / 'MIGRATION_REPORT.md'
        if not args.dry_run and target_path.exists():
            report_path.write_text(report.to_markdown())
            print(f"\nReport saved to: {report_path}")


if __name__ == '__main__':
    main()
