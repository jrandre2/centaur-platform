#!/usr/bin/env python3
"""
Data audit module for tracking sample attrition across pipeline stages.

This module provides tools to audit data quality and track sample changes
as data flows through the pipeline. It generates reports showing how many
records are lost or gained at each stage.

Usage
-----
from src.data_audit import PipelineAudit

# Create audit
audit = PipelineAudit()

# Run full audit
report = audit.run_full_audit()
print(report.format())

# CLI: python src/pipeline.py audit_data --full --report
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union, Any
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

from utils.helpers import get_project_root, get_data_dir, load_data


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class StageAudit:
    """Audit results for a single pipeline stage."""
    stage_name: str
    file_path: Optional[Path]
    exists: bool
    row_count: int = 0
    column_count: int = 0
    columns: list = field(default_factory=list)
    file_size_mb: float = 0.0
    modified_time: Optional[datetime] = None
    missing_by_column: dict = field(default_factory=dict)
    notes: str = ''


@dataclass
class AuditReport:
    """Complete pipeline audit report."""
    stages: list[StageAudit] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_stages(self) -> int:
        """Number of stages audited."""
        return len(self.stages)

    @property
    def stages_with_data(self) -> int:
        """Number of stages with existing data files."""
        return sum(1 for s in self.stages if s.exists)

    def get_attrition(self) -> list[dict]:
        """
        Calculate sample attrition between consecutive stages.

        Returns
        -------
        list
            List of dictionaries with attrition info
        """
        attrition = []
        stages_with_data = [s for s in self.stages if s.exists and s.row_count > 0]

        for i in range(1, len(stages_with_data)):
            prev = stages_with_data[i - 1]
            curr = stages_with_data[i]

            diff = curr.row_count - prev.row_count
            pct = (diff / prev.row_count * 100) if prev.row_count > 0 else 0

            attrition.append({
                'from_stage': prev.stage_name,
                'to_stage': curr.stage_name,
                'from_rows': prev.row_count,
                'to_rows': curr.row_count,
                'difference': diff,
                'percent_change': pct
            })

        return attrition

    def format(self, show_columns: bool = False) -> str:
        """
        Format the audit report as a string.

        Parameters
        ----------
        show_columns : bool
            Whether to show column lists

        Returns
        -------
        str
            Formatted report
        """
        lines = [
            "=" * 60,
            "PIPELINE DATA AUDIT REPORT",
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            ""
        ]

        # Stage summary table
        lines.append("STAGE SUMMARY")
        lines.append("-" * 60)
        lines.append(f"{'Stage':<20} {'Exists':<8} {'Rows':>10} {'Cols':>6} {'Size MB':>10}")
        lines.append("-" * 60)

        for stage in self.stages:
            exists = "Yes" if stage.exists else "No"
            rows = f"{stage.row_count:,}" if stage.exists else "-"
            cols = str(stage.column_count) if stage.exists else "-"
            size = f"{stage.file_size_mb:.2f}" if stage.exists else "-"
            lines.append(f"{stage.stage_name:<20} {exists:<8} {rows:>10} {cols:>6} {size:>10}")

        lines.append("-" * 60)
        lines.append("")

        # Attrition analysis
        attrition = self.get_attrition()
        if attrition:
            lines.append("SAMPLE ATTRITION")
            lines.append("-" * 60)
            for a in attrition:
                sign = "+" if a['difference'] > 0 else ""
                lines.append(
                    f"{a['from_stage']} -> {a['to_stage']}: "
                    f"{a['from_rows']:,} -> {a['to_rows']:,} "
                    f"({sign}{a['difference']:,}, {sign}{a['percent_change']:.1f}%)"
                )
            lines.append("")

        # Missing values summary
        lines.append("MISSING VALUES BY STAGE")
        lines.append("-" * 60)
        for stage in self.stages:
            if stage.exists and stage.missing_by_column:
                lines.append(f"\n{stage.stage_name}:")
                for col, n_missing in stage.missing_by_column.items():
                    if n_missing > 0:
                        pct = n_missing / stage.row_count * 100 if stage.row_count > 0 else 0
                        lines.append(f"  {col}: {n_missing:,} ({pct:.1f}%)")

        # Column lists (if requested)
        if show_columns:
            lines.append("")
            lines.append("COLUMNS BY STAGE")
            lines.append("-" * 60)
            for stage in self.stages:
                if stage.exists and stage.columns:
                    lines.append(f"\n{stage.stage_name} ({len(stage.columns)} columns):")
                    for col in stage.columns:
                        lines.append(f"  - {col}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            'generated_at': self.generated_at.isoformat(),
            'total_stages': self.total_stages,
            'stages_with_data': self.stages_with_data,
            'attrition': self.get_attrition(),
            'stages': [
                {
                    'stage_name': s.stage_name,
                    'exists': s.exists,
                    'row_count': s.row_count,
                    'column_count': s.column_count,
                    'file_size_mb': s.file_size_mb,
                    'missing_by_column': s.missing_by_column,
                    'notes': s.notes
                }
                for s in self.stages
            ]
        }

    def save(self, path: Union[str, Path]) -> Path:
        """Save report to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        return path


# ============================================================
# PIPELINE AUDIT CLASS
# ============================================================

# Default pipeline stages configuration
DEFAULT_STAGES = {
    's00_raw': 'data_work/data_raw.parquet',
    's01_linked': 'data_work/data_linked.parquet',
    's02_panel': 'data_work/panel.parquet',
}


class PipelineAudit:
    """
    Audit pipeline data files for quality and attrition tracking.

    Examples
    --------
    >>> audit = PipelineAudit()
    >>> report = audit.run_full_audit()
    >>> print(report.format())
    """

    def __init__(self, stages: Optional[dict[str, str]] = None):
        """
        Initialize the audit.

        Parameters
        ----------
        stages : dict, optional
            Dictionary mapping stage names to file paths (relative to project root).
            If None, uses DEFAULT_STAGES.
        """
        self.project_root = get_project_root()
        self.stages = stages or DEFAULT_STAGES

    def count_rows(self, path: Path) -> int:
        """
        Count rows in a data file without loading entire file.

        Parameters
        ----------
        path : Path
            Path to the data file

        Returns
        -------
        int
            Number of rows
        """
        if not path.exists():
            return 0

        ext = path.suffix.lower()

        if ext == '.parquet':
            # For parquet, we can get row count from metadata
            import pyarrow.parquet as pq
            return pq.read_metadata(path).num_rows
        elif ext == '.csv':
            # Count lines in CSV (minus header)
            with open(path, 'r') as f:
                return sum(1 for _ in f) - 1
        else:
            # Fall back to loading
            df = load_data(path)
            return len(df)

    def audit_stage(self, stage_name: str, file_path: str) -> StageAudit:
        """
        Audit a single pipeline stage.

        Parameters
        ----------
        stage_name : str
            Name of the stage
        file_path : str
            Path to the stage's output file (relative to project root)

        Returns
        -------
        StageAudit
            Audit results for this stage
        """
        full_path = self.project_root / file_path

        if not full_path.exists():
            return StageAudit(
                stage_name=stage_name,
                file_path=full_path,
                exists=False,
                notes='File not found'
            )

        try:
            df = load_data(full_path)

            # Calculate missing values
            missing = {}
            for col in df.columns:
                n_missing = df[col].isna().sum()
                if n_missing > 0:
                    missing[col] = int(n_missing)

            # Get file stats
            stat = full_path.stat()

            return StageAudit(
                stage_name=stage_name,
                file_path=full_path,
                exists=True,
                row_count=len(df),
                column_count=len(df.columns),
                columns=list(df.columns),
                file_size_mb=stat.st_size / (1024 * 1024),
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                missing_by_column=missing
            )

        except Exception as e:
            return StageAudit(
                stage_name=stage_name,
                file_path=full_path,
                exists=True,
                notes=f'Error reading file: {str(e)}'
            )

    def run_full_audit(self) -> AuditReport:
        """
        Audit all configured pipeline stages.

        Returns
        -------
        AuditReport
            Complete audit report
        """
        report = AuditReport()

        for stage_name, file_path in self.stages.items():
            stage_audit = self.audit_stage(stage_name, file_path)
            report.stages.append(stage_audit)

        return report

    def check_column_coverage(
        self,
        df: pd.DataFrame,
        required_columns: list[str]
    ) -> dict:
        """
        Check coverage of required columns.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to check
        required_columns : list
            List of required column names

        Returns
        -------
        dict
            Dictionary with 'present', 'missing', 'coverage_rate' keys
        """
        present = [c for c in required_columns if c in df.columns]
        missing = [c for c in required_columns if c not in df.columns]

        return {
            'present': present,
            'missing': missing,
            'coverage_rate': len(present) / len(required_columns) if required_columns else 1.0
        }

    def compare_stages(
        self,
        stage1_name: str,
        stage2_name: str
    ) -> dict:
        """
        Compare two pipeline stages.

        Parameters
        ----------
        stage1_name : str
            Name of first stage
        stage2_name : str
            Name of second stage

        Returns
        -------
        dict
            Comparison results
        """
        if stage1_name not in self.stages or stage2_name not in self.stages:
            raise ValueError(f"Stage not found. Available: {list(self.stages.keys())}")

        audit1 = self.audit_stage(stage1_name, self.stages[stage1_name])
        audit2 = self.audit_stage(stage2_name, self.stages[stage2_name])

        if not audit1.exists or not audit2.exists:
            return {
                'error': 'One or both stage files do not exist',
                'stage1_exists': audit1.exists,
                'stage2_exists': audit2.exists
            }

        # Column comparison
        cols1 = set(audit1.columns)
        cols2 = set(audit2.columns)

        return {
            'stage1': stage1_name,
            'stage2': stage2_name,
            'row_count_1': audit1.row_count,
            'row_count_2': audit2.row_count,
            'row_diff': audit2.row_count - audit1.row_count,
            'columns_added': list(cols2 - cols1),
            'columns_removed': list(cols1 - cols2),
            'columns_common': list(cols1 & cols2)
        }

    def generate_markdown_report(self) -> str:
        """
        Generate a markdown-formatted audit report.

        Returns
        -------
        str
            Markdown report content
        """
        report = self.run_full_audit()

        lines = [
            "# Pipeline Data Audit Report",
            "",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- Total stages: {report.total_stages}",
            f"- Stages with data: {report.stages_with_data}",
            "",
            "## Stage Details",
            "",
            "| Stage | Exists | Rows | Columns | Size (MB) |",
            "|-------|--------|------|---------|-----------|",
        ]

        for stage in report.stages:
            exists = "Yes" if stage.exists else "No"
            rows = f"{stage.row_count:,}" if stage.exists else "-"
            cols = str(stage.column_count) if stage.exists else "-"
            size = f"{stage.file_size_mb:.2f}" if stage.exists else "-"
            lines.append(f"| {stage.stage_name} | {exists} | {rows} | {cols} | {size} |")

        lines.append("")

        # Attrition
        attrition = report.get_attrition()
        if attrition:
            lines.extend([
                "## Sample Attrition",
                "",
                "| From | To | Change | Percent |",
                "|------|----|---------:|---------:|",
            ])
            for a in attrition:
                sign = "+" if a['difference'] > 0 else ""
                lines.append(
                    f"| {a['from_stage']} | {a['to_stage']} | "
                    f"{sign}{a['difference']:,} | {sign}{a['percent_change']:.1f}% |"
                )
            lines.append("")

        return "\n".join(lines)


# ============================================================
# CLI FUNCTION
# ============================================================

def main(full: bool = False, report: bool = False, output: Optional[str] = None):
    """
    Run pipeline audit from command line.

    Parameters
    ----------
    full : bool
        Run full audit with detailed column info
    report : bool
        Save markdown report
    output : str, optional
        Output path for JSON report
    """
    audit = PipelineAudit()
    audit_report = audit.run_full_audit()

    # Print formatted report
    print(audit_report.format(show_columns=full))

    # Save JSON if requested
    if output:
        path = audit_report.save(output)
        print(f"\nJSON report saved to: {path}")

    # Save markdown report if requested
    if report:
        md_content = audit.generate_markdown_report()
        md_path = get_data_dir('diagnostics') / 'audit_report.md'
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, 'w') as f:
            f.write(md_content)
        print(f"\nMarkdown report saved to: {md_path}")

    return audit_report


if __name__ == '__main__':
    main(full=True, report=True)
