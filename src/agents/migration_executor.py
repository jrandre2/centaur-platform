#!/usr/bin/env python3
"""
Migration Executor

Executes migration plans, carrying out the steps to transform
a project into the standardized template format.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime

from .migration_planner import MigrationPlan, MigrationStep


@dataclass
class ExecutionResult:
    """Result of executing a migration step."""
    step: MigrationStep
    success: bool
    message: str = ""
    error: Optional[str] = None
    duration_ms: float = 0


@dataclass
class ExecutionReport:
    """Complete execution report."""
    plan: MigrationPlan
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    results: list[ExecutionResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def overall_success(self) -> bool:
        return self.failure_count == 0

    def to_markdown(self) -> str:
        """Generate markdown execution report."""
        lines = [
            "# Migration Execution Report",
            "",
            f"**Started:** {self.started_at}",
            f"**Completed:** {self.completed_at or 'In Progress'}",
            f"**Source:** `{self.plan.source_project}`",
            f"**Target:** `{self.plan.target_location}`",
            "",
            f"## Summary",
            "",
            f"- Total Steps: {len(self.results)}",
            f"- Successful: {self.success_count}",
            f"- Failed: {self.failure_count}",
            f"- Status: {'✅ Complete' if self.overall_success else '❌ Failed'}",
            "",
            "## Step Results",
            "",
        ]

        for result in self.results:
            status = "✅" if result.success else "❌"
            lines.append(f"### {status} Step {result.step.order}: {result.step.action}")
            lines.append("")
            lines.append(f"- Category: {result.step.category}")
            lines.append(f"- Duration: {result.duration_ms:.0f}ms")
            if result.message:
                lines.append(f"- Message: {result.message}")
            if result.error:
                lines.append(f"- Error: `{result.error}`")
            lines.append("")

        return "\n".join(lines)


class MigrationExecutor:
    """
    Executes migration plans step by step.

    Usage:
        from migration_planner import generate_migration_plan

        plan = generate_migration_plan(analysis, mapping, target)
        executor = MigrationExecutor(plan, dry_run=True)
        report = executor.execute()
        print(report.to_markdown())
    """

    def __init__(
        self,
        plan: MigrationPlan,
        source_path: Path,
        template_path: Optional[Path] = None,
        dry_run: bool = False,
        verbose: bool = False,
        step_callback: Optional[Callable[[MigrationStep, ExecutionResult], None]] = None
    ):
        self.plan = plan
        self.source_path = Path(source_path)
        self.target_path = Path(plan.target_location)
        self.template_path = template_path
        self.dry_run = dry_run
        self.verbose = verbose
        self.step_callback = step_callback

    def execute(self) -> ExecutionReport:
        """Execute all steps in the migration plan."""
        report = ExecutionReport(plan=self.plan)

        for step in self.plan.steps:
            result = self._execute_step(step)
            report.results.append(result)

            if self.step_callback:
                self.step_callback(step, result)

            if not result.success and step.category != 'verify':
                # Stop on non-verify failures
                break

        report.completed_at = datetime.now().isoformat()
        return report

    def _execute_step(self, step: MigrationStep) -> ExecutionResult:
        """Execute a single migration step."""
        import time
        start = time.time()

        try:
            if step.category == 'setup':
                result = self._execute_setup(step)
            elif step.category == 'copy':
                result = self._execute_copy(step)
            elif step.category == 'transform':
                result = self._execute_transform(step)
            elif step.category == 'generate':
                result = self._execute_generate(step)
            elif step.category == 'verify':
                result = self._execute_verify(step)
            else:
                result = ExecutionResult(
                    step=step,
                    success=False,
                    error=f"Unknown category: {step.category}"
                )
        except Exception as e:
            result = ExecutionResult(
                step=step,
                success=False,
                error=str(e)
            )

        result.duration_ms = (time.time() - start) * 1000

        if result.success:
            step.completed = True

        if self.verbose:
            status = "✓" if result.success else "✗"
            print(f"  {status} {step.action}")
            if result.error:
                print(f"    Error: {result.error}")

        return result

    def _execute_setup(self, step: MigrationStep) -> ExecutionResult:
        """Execute setup steps (directory creation, git init, etc.)."""
        action = step.action.lower()

        if 'directory structure' in action:
            return self._create_directory_structure()
        elif 'git' in action and 'init' in step.details.lower():
            return self._init_git()
        elif 'virtual environment' in action:
            return self._create_venv()
        elif 'claude.md' in action.lower():
            return self._copy_template_file('CLAUDE.md')
        elif 'requirements' in action.lower():
            return self._copy_template_file('requirements.txt')
        else:
            return ExecutionResult(
                step=step,
                success=True,
                message="Skipped (manual step)"
            )

    def _execute_copy(self, step: MigrationStep) -> ExecutionResult:
        """Execute file copy operations."""
        if not step.source or not step.target:
            return ExecutionResult(
                step=step,
                success=False,
                error="Missing source or target path"
            )

        source_pattern = step.source
        target_dir = self.target_path / step.target

        # Find matching files in source
        source_files = self._find_files(source_pattern)

        if not source_files:
            return ExecutionResult(
                step=step,
                success=True,
                message=f"No files matching {source_pattern}"
            )

        if self.dry_run:
            return ExecutionResult(
                step=step,
                success=True,
                message=f"Would copy {len(source_files)} files to {target_dir}"
            )

        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        for src in source_files:
            dst = target_dir / src.name
            if src.is_file():
                shutil.copy2(src, dst)
                copied += 1
            elif src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                copied += 1

        return ExecutionResult(
            step=step,
            success=True,
            message=f"Copied {copied} items to {target_dir}"
        )

    def _execute_transform(self, step: MigrationStep) -> ExecutionResult:
        """Execute transformation/merge operations."""
        # Transformations are complex and typically need human/AI review
        # For now, create placeholder with merge instructions

        if not step.target:
            return ExecutionResult(
                step=step,
                success=False,
                error="Missing target path"
            )

        target_file = self.target_path / step.target

        if self.dry_run:
            return ExecutionResult(
                step=step,
                success=True,
                message=f"Would create merge scaffold at {target_file}"
            )

        # Create directory if needed
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Create a scaffold file with merge instructions
        sources = step.source.split(", ") if step.source else []

        content = self._generate_merge_scaffold(target_file.name, sources, step.details)
        target_file.write_text(content)

        return ExecutionResult(
            step=step,
            success=True,
            message=f"Created merge scaffold at {target_file} (manual merge required)"
        )

    def _execute_generate(self, step: MigrationStep) -> ExecutionResult:
        """Execute generation steps (docs, CLI, etc.)."""
        action = step.action.lower()

        if not step.target:
            return ExecutionResult(
                step=step,
                success=False,
                error="Missing target path"
            )

        target_file = self.target_path / step.target

        if self.dry_run:
            return ExecutionResult(
                step=step,
                success=True,
                message=f"Would generate {target_file}"
            )

        # Create directory if needed
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Generate appropriate template
        if 'data_dictionary' in action:
            content = self._generate_data_dictionary_template()
        elif 'methodology' in action:
            content = self._generate_methodology_template()
        elif 'pipeline.md' in action:
            content = self._generate_pipeline_doc_template()
        elif 'pipeline.py' in action or 'cli' in action:
            content = self._generate_pipeline_cli_template()
        else:
            content = f"# {step.action}\n\n[TODO: Complete this file]\n"

        target_file.write_text(content)

        return ExecutionResult(
            step=step,
            success=True,
            message=f"Generated {target_file}"
        )

    def _execute_verify(self, step: MigrationStep) -> ExecutionResult:
        """Execute verification steps."""
        action = step.action.lower()

        if self.dry_run:
            return ExecutionResult(
                step=step,
                success=True,
                message="Verification skipped (dry run)"
            )

        if 'import' in action:
            return self._verify_imports()
        elif 'test' in action:
            return self._verify_tests()
        elif 'data' in action and 'load' in action:
            return self._verify_data_loading()
        elif 'doc' in action:
            return self._verify_documentation()
        else:
            return ExecutionResult(
                step=step,
                success=True,
                message="Verification passed (manual check)"
            )

    # Helper methods

    def _find_files(self, pattern: str) -> list[Path]:
        """Find files matching a pattern in the source directory."""
        files = []

        # Handle glob patterns
        if '*' in pattern:
            # Convert pattern like 'data/*' to actual glob
            glob_pattern = pattern.replace('/*', '/**/*')
            files = list(self.source_path.glob(glob_pattern))
        else:
            # Exact path
            path = self.source_path / pattern
            if path.exists():
                files = [path]

        return files

    def _create_directory_structure(self) -> ExecutionResult:
        """Create the standard directory structure."""
        dirs = [
            'src/stages',
            'src/utils',
            'src/agents',
            'tests',
            'doc',
            'figures',
            'data_raw',
            'data_work',
            'manuscript_quarto/code',
            'manuscript_quarto/data',
            'manuscript_quarto/figures',
            'manuscript_quarto/journal_configs',
        ]

        if self.dry_run:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', 'Create directories'),
                success=True,
                message=f"Would create {len(dirs)} directories"
            )

        for d in dirs:
            (self.target_path / d).mkdir(parents=True, exist_ok=True)

        return ExecutionResult(
            step=MigrationStep(0, 'setup', 'Create directories'),
            success=True,
            message=f"Created {len(dirs)} directories"
        )

    def _init_git(self) -> ExecutionResult:
        """Initialize git repository."""
        if self.dry_run:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', 'Git init'),
                success=True,
                message="Would initialize git repository"
            )

        try:
            result = subprocess.run(
                ['git', 'init'],
                cwd=self.target_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ExecutionResult(
                    step=MigrationStep(0, 'setup', 'Git init'),
                    success=True,
                    message="Initialized git repository"
                )
            else:
                return ExecutionResult(
                    step=MigrationStep(0, 'setup', 'Git init'),
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', 'Git init'),
                success=False,
                error=str(e)
            )

    def _create_venv(self) -> ExecutionResult:
        """Create virtual environment."""
        if self.dry_run:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', 'Create venv'),
                success=True,
                message="Would create virtual environment"
            )

        try:
            result = subprocess.run(
                ['python', '-m', 'venv', '.venv'],
                cwd=self.target_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ExecutionResult(
                    step=MigrationStep(0, 'setup', 'Create venv'),
                    success=True,
                    message="Created virtual environment"
                )
            else:
                return ExecutionResult(
                    step=MigrationStep(0, 'setup', 'Create venv'),
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', 'Create venv'),
                success=False,
                error=str(e)
            )

    def _copy_template_file(self, filename: str) -> ExecutionResult:
        """Copy a template file to the target."""
        if not self.template_path:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', f'Copy {filename}'),
                success=True,
                message="Skipped (no template path)"
            )

        src = self.template_path / filename
        dst = self.target_path / filename

        if not src.exists():
            return ExecutionResult(
                step=MigrationStep(0, 'setup', f'Copy {filename}'),
                success=False,
                error=f"Template file not found: {src}"
            )

        if self.dry_run:
            return ExecutionResult(
                step=MigrationStep(0, 'setup', f'Copy {filename}'),
                success=True,
                message=f"Would copy {src} to {dst}"
            )

        shutil.copy2(src, dst)
        return ExecutionResult(
            step=MigrationStep(0, 'setup', f'Copy {filename}'),
            success=True,
            message=f"Copied {filename}"
        )

    def _generate_merge_scaffold(
        self,
        target_name: str,
        sources: list[str],
        details: str
    ) -> str:
        """Generate a scaffold file for merging multiple modules."""
        return f'''#!/usr/bin/env python3
"""
{target_name}

This module was created by merging the following source files:
{chr(10).join(f"  - {s}" for s in sources)}

{details}

TODO: Review and integrate the merged code below.
"""
from __future__ import annotations

# =============================================================================
# IMPORTS FROM SOURCE MODULES
# =============================================================================

# TODO: Add imports from source modules
# from ... import ...

# =============================================================================
# MERGED CODE
# =============================================================================

# TODO: Merge the code from the source modules listed above.
# Review for:
#   - Import conflicts
#   - Naming collisions
#   - Consistent code style
#   - Updated internal references

pass
'''

    def _generate_data_dictionary_template(self) -> str:
        """Generate DATA_DICTIONARY.md template."""
        return '''# Data Dictionary

**Status**: Draft
**Last Updated**: [Date]

---

## Overview

This document defines variables used in the analysis.

## Raw Data Variables

| Variable | Type | Description | Source |
|----------|------|-------------|--------|
| `id` | int | Unique identifier | [source] |

## Constructed Variables

| Variable | Type | Description | Construction |
|----------|------|-------------|--------------|
| [var] | [type] | [desc] | [how computed] |

## Panel Variables

| Variable | Type | Description | Notes |
|----------|------|-------------|-------|
| `unit_id` | int | Unit identifier | |
| `period` | int | Time period | |
'''

    def _generate_methodology_template(self) -> str:
        """Generate METHODOLOGY.md template."""
        return '''# Methodology

**Status**: Draft
**Last Updated**: [Date]

---

## Research Design

[Describe the research design]

## Identification Strategy

[Describe how causal effects are identified]

## Estimation

### Main Specification

[Document the main estimating equation]

### Standard Errors

[Document standard error computation]

## Robustness Checks

[List planned robustness checks]
'''

    def _generate_pipeline_doc_template(self) -> str:
        """Generate PIPELINE.md template."""
        return '''# Pipeline Documentation

**Status**: Draft
**Last Updated**: [Date]

---

## Overview

This document describes the data processing and analysis pipeline.

## Pipeline Stages

### Stage 0: Data Ingestion (`s00_ingest.py`)

**Purpose**: Load and validate raw data

**Inputs**:
- `data_raw/*.csv`

**Outputs**:
- `data_work/data_raw.parquet`

### Stage 1: Record Linkage (`s01_link.py`)

**Purpose**: Link records across data sources

### Stage 2: Panel Construction (`s02_panel.py`)

**Purpose**: Build analysis panel

### Stage 3: Estimation (`s03_estimation.py`)

**Purpose**: Run main estimations

### Stage 4: Robustness (`s04_robustness.py`)

**Purpose**: Run robustness checks

### Stage 5: Figures (`s05_figures.py`)

**Purpose**: Generate publication figures

### Stage 6: Manuscript (`s06_manuscript.py`)

**Purpose**: Validate manuscript

## Running the Pipeline

```bash
source .venv/bin/activate
python src/pipeline.py ingest_data
python src/pipeline.py build_panel
python src/pipeline.py run_estimation
python src/pipeline.py make_figures
```
'''

    def _generate_pipeline_cli_template(self) -> str:
        """Generate pipeline.py CLI template."""
        return '''#!/usr/bin/env python3
"""
Research Pipeline CLI

Main entry point for the research pipeline.
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Research Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Data ingestion
    p_ingest = subparsers.add_parser('ingest_data', help='Load and validate raw data')
    p_ingest.add_argument('--demo', action='store_true', help='Use synthetic demo data')

    # Panel construction
    p_panel = subparsers.add_parser('build_panel', help='Construct analysis panel')
    p_panel.add_argument('--balance', action='store_true', help='Create balanced panel')

    # Estimation
    p_est = subparsers.add_parser('run_estimation', help='Run main estimations')
    p_est.add_argument('--spec', help='Specific specification to run')

    # Robustness
    p_rob = subparsers.add_parser('estimate_robustness', help='Run robustness checks')

    # Figures
    p_fig = subparsers.add_parser('make_figures', help='Generate figures')
    p_fig.add_argument('--only', help='Generate specific figure')

    # Parse and dispatch
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Import and run the appropriate stage
    if args.command == 'ingest_data':
        from stages.s00_ingest import run
        return run(demo=args.demo)
    elif args.command == 'build_panel':
        from stages.s02_panel import run
        return run(balance=args.balance)
    elif args.command == 'run_estimation':
        from stages.s03_estimation import run
        return run(spec=args.spec)
    elif args.command == 'estimate_robustness':
        from stages.s04_robustness import run
        return run()
    elif args.command == 'make_figures':
        from stages.s05_figures import run
        return run(only=args.only)

    return 0


if __name__ == '__main__':
    sys.exit(main())
'''

    def _verify_imports(self) -> ExecutionResult:
        """Verify Python imports resolve."""
        try:
            result = subprocess.run(
                ['python', '-c', 'import src.stages'],
                cwd=self.target_path,
                capture_output=True,
                text=True,
                env={**os.environ, 'PYTHONPATH': str(self.target_path)}
            )
            if result.returncode == 0:
                return ExecutionResult(
                    step=MigrationStep(0, 'verify', 'Check imports'),
                    success=True,
                    message="Imports resolve successfully"
                )
            else:
                return ExecutionResult(
                    step=MigrationStep(0, 'verify', 'Check imports'),
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return ExecutionResult(
                step=MigrationStep(0, 'verify', 'Check imports'),
                success=False,
                error=str(e)
            )

    def _verify_tests(self) -> ExecutionResult:
        """Run pytest."""
        tests_dir = self.target_path / 'tests'
        if not tests_dir.exists():
            return ExecutionResult(
                step=MigrationStep(0, 'verify', 'Run tests'),
                success=True,
                message="No tests directory"
            )

        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v'],
                cwd=self.target_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ExecutionResult(
                    step=MigrationStep(0, 'verify', 'Run tests'),
                    success=True,
                    message="All tests passed"
                )
            else:
                return ExecutionResult(
                    step=MigrationStep(0, 'verify', 'Run tests'),
                    success=False,
                    error=f"Tests failed:\n{result.stdout}"
                )
        except Exception as e:
            return ExecutionResult(
                step=MigrationStep(0, 'verify', 'Run tests'),
                success=False,
                error=str(e)
            )

    def _verify_data_loading(self) -> ExecutionResult:
        """Verify data can be loaded."""
        # Check if demo mode works
        try:
            result = subprocess.run(
                ['python', 'src/pipeline.py', 'ingest_data', '--demo'],
                cwd=self.target_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return ExecutionResult(
                    step=MigrationStep(0, 'verify', 'Data loading'),
                    success=True,
                    message="Demo data loads successfully"
                )
            else:
                return ExecutionResult(
                    step=MigrationStep(0, 'verify', 'Data loading'),
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return ExecutionResult(
                step=MigrationStep(0, 'verify', 'Data loading'),
                success=False,
                error=str(e)
            )

    def _verify_documentation(self) -> ExecutionResult:
        """Verify documentation links."""
        doc_dir = self.target_path / 'doc'
        if not doc_dir.exists():
            return ExecutionResult(
                step=MigrationStep(0, 'verify', 'Check docs'),
                success=True,
                message="No doc directory"
            )

        # Check that required docs exist
        required = ['README.md', 'PIPELINE.md', 'METHODOLOGY.md']
        missing = [f for f in required if not (doc_dir / f).exists()]

        if missing:
            return ExecutionResult(
                step=MigrationStep(0, 'verify', 'Check docs'),
                success=False,
                error=f"Missing docs: {', '.join(missing)}"
            )

        return ExecutionResult(
            step=MigrationStep(0, 'verify', 'Check docs'),
            success=True,
            message="All required documentation present"
        )


def execute_migration(
    plan: MigrationPlan,
    source_path: Path,
    template_path: Optional[Path] = None,
    dry_run: bool = False,
    verbose: bool = True
) -> ExecutionReport:
    """Convenience function to execute a migration plan."""
    executor = MigrationExecutor(
        plan=plan,
        source_path=source_path,
        template_path=template_path,
        dry_run=dry_run,
        verbose=verbose
    )
    return executor.execute()
