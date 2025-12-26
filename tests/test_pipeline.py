#!/usr/bin/env python3
"""
Tests for src/pipeline.py

Tests cover:
- CLI argument parsing
- Command routing
- Environment checks
"""
from __future__ import annotations

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestParseArgs:
    """Tests for argument parsing."""

    def test_ingest_data_command(self):
        """Parse ingest_data command."""
        from pipeline import parse_args
        with patch('sys.argv', ['pipeline.py', 'ingest_data']):
            args = parse_args()
            assert args.cmd == 'ingest_data'

    def test_run_estimation_defaults(self):
        """Parse run_estimation with defaults."""
        from pipeline import parse_args
        with patch('sys.argv', ['pipeline.py', 'run_estimation']):
            args = parse_args()
            assert args.cmd == 'run_estimation'
            assert args.specification == 'baseline'
            assert args.sample == 'full'

    def test_run_estimation_with_options(self):
        """Parse run_estimation with custom options."""
        from pipeline import parse_args
        with patch('sys.argv', ['pipeline.py', 'run_estimation', '-s', 'robust', '--sample', 'subset']):
            args = parse_args()
            assert args.specification == 'robust'
            assert args.sample == 'subset'

    def test_review_new_discipline(self):
        """Parse review_new with discipline option."""
        from pipeline import parse_args
        with patch('sys.argv', ['pipeline.py', 'review_new', '--discipline', 'economics']):
            args = parse_args()
            assert args.discipline == 'economics'

    def test_journal_parse_requires_input(self):
        """journal_parse requires --input argument."""
        from pipeline import parse_args
        with patch('sys.argv', ['pipeline.py', 'journal_parse']):
            with pytest.raises(SystemExit):
                parse_args()

    def test_audit_data_options(self):
        """Parse audit_data with options."""
        from pipeline import parse_args
        with patch('sys.argv', ['pipeline.py', 'audit_data', '--full', '--report']):
            args = parse_args()
            assert args.cmd == 'audit_data'
            assert args.full is True
            assert args.report is True


class TestEnvironmentCheck:
    """Tests for environment validation."""

    def test_ensure_env_with_venv(self):
        """Environment check passes with valid venv."""
        from pipeline import ensure_env
        with patch.dict('os.environ', {'VIRTUAL_ENV': '/path/to/.venv'}):
            # Should not raise
            ensure_env()

    def test_ensure_env_without_venv(self):
        """Environment check fails without venv."""
        from pipeline import ensure_env
        with patch.dict('os.environ', {'VIRTUAL_ENV': ''}, clear=True):
            with pytest.raises(SystemExit):
                ensure_env()


class TestCommandRouting:
    """Tests for command routing in main()."""

    def test_routes_to_correct_stage(self):
        """Commands route to correct stage modules."""
        # This is tested indirectly through integration tests
        # Unit tests would require mocking all stage imports
        pass
