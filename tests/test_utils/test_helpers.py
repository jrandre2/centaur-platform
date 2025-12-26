#!/usr/bin/env python3
"""
Tests for src/utils/helpers.py

Tests cover:
- Path utilities
- Statistical formatters
- Data loading/saving
- Data cleaning utilities
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.helpers import (
    format_pvalue,
    format_ci,
    add_significance_stars,
    format_coefficient,
    format_fstat,
    format_sample_size,
    format_percent,
    format_difference,
    load_data,
    save_data,
    clean_numeric,
    calculate_match_rate,
)


# ============================================================
# STATISTICAL FORMATTER TESTS
# ============================================================

class TestFormatPvalue:
    """Tests for format_pvalue function."""

    def test_small_pvalue(self):
        """P-values below threshold should show <threshold."""
        assert format_pvalue(0.0001) == '<0.001'
        assert format_pvalue(0.0005) == '<0.001'

    def test_normal_pvalue(self):
        """P-values above threshold should show 3 decimals."""
        assert format_pvalue(0.05) == '0.050'
        assert format_pvalue(0.123) == '0.123'

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        assert format_pvalue(0.005, threshold=0.01) == '<0.01'
        assert format_pvalue(0.015, threshold=0.01) == '0.015'


class TestFormatCI:
    """Tests for format_ci function."""

    def test_basic_ci(self):
        """Basic confidence interval formatting."""
        assert format_ci(0.1, 0.3) == '[0.100, 0.300]'

    def test_negative_values(self):
        """CIs with negative values."""
        assert format_ci(-0.5, 0.2) == '[-0.500, 0.200]'

    def test_custom_decimals(self):
        """Custom decimal places."""
        assert format_ci(0.1234, 0.5678, decimals=2) == '[0.12, 0.57]'


class TestSignificanceStars:
    """Tests for add_significance_stars function."""

    def test_three_stars(self):
        """P < 0.001 should get three stars."""
        assert add_significance_stars(0.0005) == '***'

    def test_two_stars(self):
        """P < 0.01 should get two stars."""
        assert add_significance_stars(0.005) == '**'

    def test_one_star(self):
        """P < 0.05 should get one star."""
        assert add_significance_stars(0.03) == '*'

    def test_no_stars(self):
        """P >= 0.05 should get no stars."""
        assert add_significance_stars(0.1) == ''
        assert add_significance_stars(0.05) == ''


class TestFormatCoefficient:
    """Tests for format_coefficient function."""

    def test_basic_coefficient(self):
        """Basic coefficient formatting."""
        assert format_coefficient(0.123) == '0.123'

    def test_with_se(self):
        """Coefficient with standard error."""
        assert format_coefficient(0.123, se=0.045) == '0.123 (0.045)'

    def test_with_stars(self):
        """Coefficient with significance stars."""
        result = format_coefficient(0.123, pvalue=0.005, include_stars=True)
        assert result == '0.123**'

    def test_full_format(self):
        """Full format with SE and stars."""
        result = format_coefficient(0.123, se=0.045, pvalue=0.005, include_stars=True)
        assert result == '0.123** (0.045)'


class TestFormatFstat:
    """Tests for format_fstat function."""

    def test_basic_fstat(self):
        """Basic F-statistic formatting."""
        assert format_fstat(12.34, 3, 100) == 'F(3, 100) = 12.34'

    def test_with_pvalue(self):
        """F-statistic with p-value."""
        result = format_fstat(12.34, 3, 100, 0.001)
        assert 'F(3, 100) = 12.34' in result
        assert 'p = ' in result


class TestFormatSampleSize:
    """Tests for format_sample_size function."""

    def test_basic_sample(self):
        """Basic sample size formatting."""
        assert format_sample_size(1000) == 'N = 1,000'

    def test_large_sample(self):
        """Large sample sizes with commas."""
        assert format_sample_size(1234567) == 'N = 1,234,567'

    def test_custom_label(self):
        """Custom label."""
        assert format_sample_size(100, label='n') == 'n = 100'


class TestFormatPercent:
    """Tests for format_percent function."""

    def test_decimal_input(self):
        """Input in 0-1 range."""
        assert format_percent(0.5) == '50.0%'

    def test_percentage_input(self):
        """Input in 0-100 range."""
        assert format_percent(75) == '75.0%'

    def test_custom_decimals(self):
        """Custom decimal places."""
        assert format_percent(0.3333, decimals=2) == '33.33%'


class TestFormatDifference:
    """Tests for format_difference function."""

    def test_positive_difference(self):
        """Positive differences should show +."""
        assert format_difference(0.5) == '+0.500'

    def test_negative_difference(self):
        """Negative differences."""
        assert format_difference(-0.5) == '-0.500'

    def test_no_sign(self):
        """Without sign prefix."""
        assert format_difference(0.5, show_sign=False) == '0.500'


# ============================================================
# DATA LOADING/SAVING TESTS
# ============================================================

class TestLoadData:
    """Tests for load_data function."""

    def test_load_parquet(self, sample_parquet):
        """Load parquet file."""
        df = load_data(sample_parquet)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_load_csv(self, sample_csv):
        """Load CSV file."""
        df = load_data(sample_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_file_not_found(self, temp_dir):
        """Non-existent file should raise error."""
        with pytest.raises(FileNotFoundError):
            load_data(temp_dir / 'nonexistent.parquet')

    def test_unsupported_format(self, temp_dir):
        """Unsupported format should raise error."""
        fake_file = temp_dir / 'test.xyz'
        fake_file.touch()
        with pytest.raises(ValueError, match='Unsupported'):
            load_data(fake_file)


class TestSaveData:
    """Tests for save_data function."""

    def test_save_parquet(self, temp_dir, sample_df):
        """Save as parquet."""
        path = temp_dir / 'output.parquet'
        result = save_data(sample_df, path)
        assert result == path
        assert path.exists()

    def test_save_csv(self, temp_dir, sample_df):
        """Save as CSV."""
        path = temp_dir / 'output.csv'
        save_data(sample_df, path)
        assert path.exists()

    def test_creates_parent_dirs(self, temp_dir, sample_df):
        """Should create parent directories."""
        path = temp_dir / 'nested' / 'dir' / 'output.parquet'
        save_data(sample_df, path)
        assert path.exists()


# ============================================================
# DATA CLEANING TESTS
# ============================================================

class TestCleanNumeric:
    """Tests for clean_numeric function."""

    def test_replace_inf(self):
        """Replace infinity values with NaN."""
        df = pd.DataFrame({
            'a': [1, np.inf, -np.inf, 4],
            'b': [1, 2, 3, 4]
        })
        result = clean_numeric(df, ['a'])
        assert result['a'].isna().sum() == 2

    def test_fill_value(self):
        """Fill NaN values with specified value."""
        df = pd.DataFrame({
            'a': [1, np.nan, 3, 4]
        })
        result = clean_numeric(df, ['a'], fill_value=0)
        assert result['a'].isna().sum() == 0
        assert result['a'].iloc[1] == 0


class TestCalculateMatchRate:
    """Tests for calculate_match_rate function."""

    def test_full_match(self):
        """All records matched."""
        df = pd.DataFrame({
            'key': [1, 2, 3],
            'value': ['a', 'b', 'c']
        })
        result = calculate_match_rate(df, 'key', 'value')
        assert result['matched'] == 3
        assert result['unmatched'] == 0
        assert result['rate'] == 1.0

    def test_partial_match(self):
        """Some records matched."""
        df = pd.DataFrame({
            'key': [1, 2, 3, 4],
            'value': ['a', None, 'c', None]
        })
        result = calculate_match_rate(df, 'key', 'value')
        assert result['matched'] == 2
        assert result['unmatched'] == 2
        assert result['rate'] == 0.5

    def test_no_match(self):
        """No records matched."""
        df = pd.DataFrame({
            'key': [1, 2],
            'value': [None, None]
        })
        result = calculate_match_rate(df, 'key', 'value')
        assert result['matched'] == 0
        assert result['rate'] == 0.0
