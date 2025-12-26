#!/usr/bin/env python3
"""
Tests for src/stages/s00_ingest.py

Tests cover:
- Data loading from various formats
- Initial validation
- Output file generation
"""
from __future__ import annotations

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


class TestIngestStage:
    """Tests for the data ingestion stage."""

    def test_placeholder(self):
        """Placeholder test until stage is implemented."""
        # TODO: Implement once s00_ingest.py is complete
        assert True

    def test_loads_csv(self, temp_data_dir, sample_df):
        """Stage should load CSV files."""
        # TODO: Implement once s00_ingest.py is complete
        pass

    def test_loads_parquet(self, temp_data_dir, sample_df):
        """Stage should load parquet files."""
        # TODO: Implement once s00_ingest.py is complete
        pass

    def test_validates_required_columns(self):
        """Stage should validate required columns exist."""
        # TODO: Implement once s00_ingest.py is complete
        pass

    def test_outputs_parquet(self):
        """Stage should output parquet file."""
        # TODO: Implement once s00_ingest.py is complete
        pass
