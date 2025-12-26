#!/usr/bin/env python3
"""
Common utility functions for the research pipeline.

This module provides shared helper functions used across multiple stages,
including path utilities, statistical formatters, and data loading/saving.

Usage
-----
from src.utils.helpers import (
    get_project_root,
    load_data,
    save_data,
    format_coefficient,
    format_pvalue,
    format_sample_size,
)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, Any
import os


# ============================================================
# PATH UTILITIES
# ============================================================

def get_project_root() -> Path:
    """Get the project root directory."""
    # Walk up from this file to find the project root
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'src').exists() and (parent / 'manuscript_quarto').exists():
            return parent
    raise RuntimeError("Could not find project root")


def get_data_dir(subdir: str = 'work') -> Path:
    """
    Get data directory path.

    Parameters
    ----------
    subdir : str
        Subdirectory: 'raw', 'work', or 'diagnostics'

    Returns
    -------
    Path
        Path to the data directory
    """
    root = get_project_root()
    if subdir == 'raw':
        return root / 'data_raw'
    elif subdir == 'work':
        return root / 'data_work'
    elif subdir == 'diagnostics':
        return root / 'data_work' / 'diagnostics'
    else:
        return root / f'data_{subdir}'


def get_output_dir() -> Path:
    """Get the output directory for figures."""
    return get_project_root() / 'figures'


def get_figures_dir() -> Path:
    """Get the manuscript figures directory."""
    return get_project_root() / 'manuscript_quarto' / 'figures'


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


# ============================================================
# STATISTICAL FORMATTERS
# ============================================================

def format_pvalue(p: float, threshold: float = 0.001) -> str:
    """Format p-value for display."""
    if p < threshold:
        return f"<{threshold}"
    return f"{p:.3f}"


def format_ci(lo: float, hi: float, decimals: int = 3) -> str:
    """Format confidence interval as [lo, hi]."""
    return f"[{lo:.{decimals}f}, {hi:.{decimals}f}]"


def add_significance_stars(p: float) -> str:
    """Add significance stars based on p-value."""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    return ""


def format_coefficient(
    coef: float,
    se: Optional[float] = None,
    decimals: int = 3,
    include_stars: bool = False,
    pvalue: Optional[float] = None
) -> str:
    """
    Format a coefficient with optional standard error and stars.

    Parameters
    ----------
    coef : float
        Coefficient value
    se : float, optional
        Standard error
    decimals : int
        Number of decimal places
    include_stars : bool
        Whether to add significance stars
    pvalue : float, optional
        P-value for significance stars

    Returns
    -------
    str
        Formatted coefficient string

    Examples
    --------
    >>> format_coefficient(0.123, 0.045, pvalue=0.006, include_stars=True)
    '0.123** (0.045)'
    """
    result = f"{coef:.{decimals}f}"

    if include_stars and pvalue is not None:
        result += add_significance_stars(pvalue)

    if se is not None:
        result += f" ({se:.{decimals}f})"

    return result


def format_fstat(f: float, df1: int, df2: int, p: Optional[float] = None) -> str:
    """
    Format an F-statistic for display.

    Parameters
    ----------
    f : float
        F-statistic value
    df1 : int
        Numerator degrees of freedom
    df2 : int
        Denominator degrees of freedom
    p : float, optional
        P-value

    Returns
    -------
    str
        Formatted F-statistic string

    Examples
    --------
    >>> format_fstat(12.34, 3, 100, 0.001)
    'F(3, 100) = 12.34, p < 0.001'
    """
    result = f"F({df1}, {df2}) = {f:.2f}"
    if p is not None:
        result += f", p = {format_pvalue(p)}"
    return result


def format_sample_size(n: int, label: str = "N") -> str:
    """
    Format sample size with thousands separator.

    Parameters
    ----------
    n : int
        Sample size
    label : str
        Label prefix (default: "N")

    Returns
    -------
    str
        Formatted sample size

    Examples
    --------
    >>> format_sample_size(12345)
    'N = 12,345'
    """
    return f"{label} = {n:,}"


def format_percent(value: float, decimals: int = 1) -> str:
    """
    Format a value as a percentage.

    Parameters
    ----------
    value : float
        Value to format (0-1 scale or 0-100 scale)
    decimals : int
        Number of decimal places

    Returns
    -------
    str
        Formatted percentage string
    """
    # Auto-detect scale
    if abs(value) <= 1:
        value = value * 100
    return f"{value:.{decimals}f}%"


def format_difference(
    value: float,
    decimals: int = 3,
    show_sign: bool = True
) -> str:
    """
    Format a difference with sign.

    Parameters
    ----------
    value : float
        Difference value
    decimals : int
        Number of decimal places
    show_sign : bool
        Whether to show + sign for positive values

    Returns
    -------
    str
        Formatted difference string
    """
    if show_sign and value > 0:
        return f"+{value:.{decimals}f}"
    return f"{value:.{decimals}f}"


# ============================================================
# DATA LOADING AND SAVING
# ============================================================

def load_data(
    path: Union[str, Path],
    **kwargs
) -> 'pd.DataFrame':
    """
    Load data from various formats (auto-detected by extension).

    Supported formats: .parquet, .csv, .xlsx, .gpkg, .dta

    Parameters
    ----------
    path : str or Path
        Path to the data file
    **kwargs
        Additional arguments passed to the underlying reader

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame
    """
    import pandas as pd

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    ext = path.suffix.lower()

    if ext == '.parquet':
        return pd.read_parquet(path, **kwargs)
    elif ext == '.csv':
        return pd.read_csv(path, **kwargs)
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(path, **kwargs)
    elif ext == '.gpkg':
        import geopandas as gpd
        return gpd.read_file(path, **kwargs)
    elif ext == '.dta':
        return pd.read_stata(path, **kwargs)
    elif ext == '.json':
        return pd.read_json(path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def save_data(
    df: 'pd.DataFrame',
    path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> Path:
    """
    Save data to various formats (auto-detected by extension).

    Supported formats: .parquet, .csv, .xlsx, .gpkg

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save
    path : str or Path
        Output path
    index : bool
        Whether to include index (default: False)
    **kwargs
        Additional arguments passed to the underlying writer

    Returns
    -------
    Path
        Path to saved file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ext = path.suffix.lower()

    if ext == '.parquet':
        df.to_parquet(path, index=index, **kwargs)
    elif ext == '.csv':
        df.to_csv(path, index=index, **kwargs)
    elif ext in ['.xlsx', '.xls']:
        df.to_excel(path, index=index, **kwargs)
    elif ext == '.gpkg':
        df.to_file(path, driver='GPKG', **kwargs)
    elif ext == '.json':
        df.to_json(path, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return path


def load_diagnostic(name: str, subdir: str = '') -> 'pd.DataFrame':
    """
    Load a diagnostic CSV file from data_work/diagnostics/.

    Parameters
    ----------
    name : str
        Name of the diagnostic file (without .csv extension)
    subdir : str
        Optional subdirectory within diagnostics/

    Returns
    -------
    pd.DataFrame
        Loaded diagnostic data
    """
    import pandas as pd

    diag_dir = get_data_dir('diagnostics')
    if subdir:
        diag_dir = diag_dir / subdir

    path = diag_dir / f'{name}.csv'
    if not path.exists():
        raise FileNotFoundError(f"Diagnostic file not found: {path}")

    return pd.read_csv(path)


def save_diagnostic(
    df: 'pd.DataFrame',
    name: str,
    subdir: str = ''
) -> Path:
    """
    Save a diagnostic DataFrame to data_work/diagnostics/.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save
    name : str
        Name for the output file (without .csv extension)
    subdir : str
        Optional subdirectory within diagnostics/

    Returns
    -------
    Path
        Path to saved file
    """
    diag_dir = get_data_dir('diagnostics')
    if subdir:
        diag_dir = diag_dir / subdir

    ensure_dir(diag_dir)
    path = diag_dir / f'{name}.csv'
    df.to_csv(path, index=False)

    return path


# ============================================================
# CONFIGURATION MANAGEMENT
# ============================================================

def load_config(config_name: str) -> dict:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    config_name : str
        Name of the config file (without extension) in manuscript_quarto/journal_configs/

    Returns
    -------
    dict
        Parsed configuration
    """
    import yaml
    config_path = get_project_root() / 'manuscript_quarto' / 'journal_configs' / f'{config_name}.yml'
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_config(config: dict, config_name: str, config_dir: str = 'journal_configs') -> Path:
    """
    Save a configuration to YAML file.

    Parameters
    ----------
    config : dict
        Configuration dictionary
    config_name : str
        Name for the config file (without extension)
    config_dir : str
        Subdirectory within manuscript_quarto/

    Returns
    -------
    Path
        Path to saved config file
    """
    import yaml

    config_path = get_project_root() / 'manuscript_quarto' / config_dir / f'{config_name}.yml'
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config_path


# ============================================================
# DATA CLEANING UTILITIES
# ============================================================

def clean_numeric(
    df: 'pd.DataFrame',
    columns: list,
    replace_inf: bool = True,
    fill_value: Optional[float] = None
) -> 'pd.DataFrame':
    """
    Clean numeric columns by handling inf and NaN values.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to clean
    columns : list
        Columns to clean
    replace_inf : bool
        Whether to replace inf with NaN
    fill_value : float, optional
        Value to fill NaN with (if None, keeps NaN)

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame
    """
    import numpy as np

    df = df.copy()

    for col in columns:
        if col in df.columns:
            if replace_inf:
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            if fill_value is not None:
                df[col] = df[col].fillna(fill_value)

    return df


def calculate_match_rate(
    df: 'pd.DataFrame',
    key_column: str,
    value_column: str
) -> dict:
    """
    Calculate match rate statistics.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with match results
    key_column : str
        Column with keys
    value_column : str
        Column with matched values (NaN if unmatched)

    Returns
    -------
    dict
        Dictionary with 'matched', 'unmatched', 'total', 'rate' keys
    """
    total = len(df)
    matched = df[value_column].notna().sum()
    unmatched = df[value_column].isna().sum()

    return {
        'matched': int(matched),
        'unmatched': int(unmatched),
        'total': int(total),
        'rate': matched / total if total > 0 else 0.0
    }
