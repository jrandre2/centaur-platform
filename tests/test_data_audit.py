#!/usr/bin/env python3
"""
Tests for src/data_audit.py

Tests cover:
- StageAudit data structure
- AuditReport generation
- PipelineAudit operations
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_audit import (
    StageAudit,
    AuditReport,
    PipelineAudit,
)


# ============================================================
# STAGE AUDIT TESTS
# ============================================================

class TestStageAudit:
    """Tests for StageAudit dataclass."""

    def test_create_existing_stage(self):
        """Create audit for existing stage."""
        audit = StageAudit(
            stage_name='test_stage',
            file_path=Path('/tmp/test.parquet'),
            exists=True,
            row_count=1000,
            column_count=10
        )
        assert audit.stage_name == 'test_stage'
        assert audit.exists is True
        assert audit.row_count == 1000

    def test_create_missing_stage(self):
        """Create audit for missing stage."""
        audit = StageAudit(
            stage_name='missing_stage',
            file_path=Path('/tmp/missing.parquet'),
            exists=False
        )
        assert audit.exists is False
        assert audit.row_count == 0


# ============================================================
# AUDIT REPORT TESTS
# ============================================================

class TestAuditReport:
    """Tests for AuditReport class."""

    def test_empty_report(self):
        """Empty report properties."""
        report = AuditReport()
        assert report.total_stages == 0
        assert report.stages_with_data == 0

    def test_report_with_stages(self):
        """Report with multiple stages."""
        report = AuditReport(stages=[
            StageAudit('s1', Path('/tmp/s1.parquet'), True, 100, 5),
            StageAudit('s2', Path('/tmp/s2.parquet'), True, 90, 6),
            StageAudit('s3', Path('/tmp/s3.parquet'), False),
        ])
        assert report.total_stages == 3
        assert report.stages_with_data == 2

    def test_attrition_calculation(self):
        """Calculate attrition between stages."""
        report = AuditReport(stages=[
            StageAudit('s1', Path('/tmp/s1.parquet'), True, 100, 5),
            StageAudit('s2', Path('/tmp/s2.parquet'), True, 80, 6),
        ])
        attrition = report.get_attrition()
        assert len(attrition) == 1
        assert attrition[0]['difference'] == -20
        assert attrition[0]['percent_change'] == -20.0

    def test_format_report(self):
        """Format report as string."""
        report = AuditReport(stages=[
            StageAudit('s1', Path('/tmp/s1.parquet'), True, 100, 5),
        ])
        formatted = report.format()
        assert 'PIPELINE DATA AUDIT REPORT' in formatted
        assert 's1' in formatted

    def test_to_dict(self):
        """Convert report to dictionary."""
        report = AuditReport(stages=[
            StageAudit('s1', Path('/tmp/s1.parquet'), True, 100, 5),
        ])
        d = report.to_dict()
        assert 'generated_at' in d
        assert 'total_stages' in d
        assert 'stages' in d

    def test_save_report(self, temp_dir):
        """Save report to JSON file."""
        report = AuditReport(stages=[
            StageAudit('s1', Path('/tmp/s1.parquet'), True, 100, 5),
        ])
        output_path = temp_dir / 'audit.json'
        result = report.save(output_path)
        assert result == output_path
        assert output_path.exists()


# ============================================================
# PIPELINE AUDIT TESTS
# ============================================================

class TestPipelineAudit:
    """Tests for PipelineAudit class."""

    def test_default_stages(self):
        """Audit uses default stages if none provided."""
        audit = PipelineAudit()
        assert 's00_raw' in audit.stages

    def test_custom_stages(self):
        """Audit uses custom stages when provided."""
        custom = {'my_stage': 'data/my_file.parquet'}
        audit = PipelineAudit(stages=custom)
        assert 'my_stage' in audit.stages
        assert 's00_raw' not in audit.stages

    def test_audit_missing_stage(self, temp_dir):
        """Audit handles missing files gracefully."""
        audit = PipelineAudit(stages={
            'missing': 'data/nonexistent.parquet'
        })
        # Override project root for testing
        audit.project_root = temp_dir

        result = audit.audit_stage('missing', 'data/nonexistent.parquet')
        assert result.exists is False
        assert 'not found' in result.notes.lower()

    def test_audit_existing_stage(self, temp_dir, sample_df):
        """Audit existing data file."""
        # Create test file
        data_path = temp_dir / 'data_work' / 'test.parquet'
        data_path.parent.mkdir(parents=True, exist_ok=True)
        sample_df.to_parquet(data_path)

        audit = PipelineAudit(stages={
            'test': 'data_work/test.parquet'
        })
        audit.project_root = temp_dir

        result = audit.audit_stage('test', 'data_work/test.parquet')
        assert result.exists is True
        assert result.row_count == len(sample_df)
        assert result.column_count == len(sample_df.columns)

    def test_run_full_audit(self, temp_dir, sample_df):
        """Run full audit across all stages."""
        # Create test files
        data_work = temp_dir / 'data_work'
        data_work.mkdir(parents=True, exist_ok=True)

        sample_df.to_parquet(data_work / 's1.parquet')
        sample_df.head(50).to_parquet(data_work / 's2.parquet')

        audit = PipelineAudit(stages={
            's1': 'data_work/s1.parquet',
            's2': 'data_work/s2.parquet',
        })
        audit.project_root = temp_dir

        report = audit.run_full_audit()
        assert report.total_stages == 2
        assert report.stages_with_data == 2

    def test_compare_stages(self, temp_dir, sample_df):
        """Compare two stages."""
        data_work = temp_dir / 'data_work'
        data_work.mkdir(parents=True, exist_ok=True)

        # Stage 1: full data
        sample_df.to_parquet(data_work / 's1.parquet')
        # Stage 2: subset with extra column
        df2 = sample_df.head(50).copy()
        df2['new_col'] = 1
        df2.to_parquet(data_work / 's2.parquet')

        audit = PipelineAudit(stages={
            's1': 'data_work/s1.parquet',
            's2': 'data_work/s2.parquet',
        })
        audit.project_root = temp_dir

        comparison = audit.compare_stages('s1', 's2')
        assert comparison['row_diff'] < 0  # s2 has fewer rows
        assert 'new_col' in comparison['columns_added']

    def test_generate_markdown_report(self, temp_dir, sample_df):
        """Generate markdown formatted report."""
        data_work = temp_dir / 'data_work'
        data_work.mkdir(parents=True, exist_ok=True)
        sample_df.to_parquet(data_work / 's1.parquet')

        audit = PipelineAudit(stages={
            's1': 'data_work/s1.parquet',
        })
        audit.project_root = temp_dir

        md = audit.generate_markdown_report()
        assert '# Pipeline Data Audit Report' in md
        assert '| Stage |' in md
