#!/usr/bin/env python3
"""
Sample data generators for testing.

This module provides functions to generate various types of test data
that can be used across the test suite.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


def generate_cross_section(
    n: int = 1000,
    n_covariates: int = 5,
    treatment_share: float = 0.5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a cross-sectional dataset for testing.

    Parameters
    ----------
    n : int
        Number of observations
    n_covariates : int
        Number of covariates to generate
    treatment_share : float
        Share of observations in treatment group
    seed : int
        Random seed for reproducibility

    Returns
    -------
    pd.DataFrame
        Generated dataset
    """
    np.random.seed(seed)

    data = {
        'id': range(1, n + 1),
        'treatment': np.random.choice([0, 1], n, p=[1-treatment_share, treatment_share])
    }

    # Add covariates
    for i in range(n_covariates):
        data[f'x{i+1}'] = np.random.randn(n)

    # Generate outcome with treatment effect
    treatment_effect = 0.5
    data['outcome'] = (
        data['treatment'] * treatment_effect +
        data['x1'] * 0.3 +
        np.random.randn(n) * 0.5
    )

    return pd.DataFrame(data)


def generate_panel(
    n_units: int = 100,
    n_periods: int = 24,
    treatment_period: int = 12,
    treatment_share: float = 0.5,
    treatment_effect: float = 0.5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a balanced panel dataset for testing.

    Parameters
    ----------
    n_units : int
        Number of units
    n_periods : int
        Number of time periods
    treatment_period : int
        Period when treatment begins
    treatment_share : float
        Share of units in treatment group
    treatment_effect : float
        True treatment effect
    seed : int
        Random seed

    Returns
    -------
    pd.DataFrame
        Balanced panel dataset
    """
    np.random.seed(seed)

    n_treated = int(n_units * treatment_share)
    treated_units = set(range(1, n_treated + 1))

    data = []
    for unit in range(1, n_units + 1):
        unit_fe = np.random.randn() * 0.5

        for period in range(1, n_periods + 1):
            is_treated = unit in treated_units
            is_post = period >= treatment_period
            treatment = 1 if is_treated and is_post else 0

            outcome = (
                unit_fe +
                period * 0.01 +  # Time trend
                treatment * treatment_effect +
                np.random.randn() * 0.3
            )

            data.append({
                'unit_id': unit,
                'period': period,
                'treatment': treatment,
                'treated_unit': int(is_treated),
                'post': int(is_post),
                'outcome': outcome,
                'covariate': np.random.randn()
            })

    return pd.DataFrame(data)


def generate_event_study(
    n_units: int = 100,
    pre_periods: int = 12,
    post_periods: int = 12,
    staggered: bool = False,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate an event study dataset.

    Parameters
    ----------
    n_units : int
        Number of units
    pre_periods : int
        Number of pre-treatment periods
    post_periods : int
        Number of post-treatment periods
    staggered : bool
        If True, treatment timing varies across units
    seed : int
        Random seed

    Returns
    -------
    pd.DataFrame
        Event study dataset with event_time variable
    """
    np.random.seed(seed)

    n_periods = pre_periods + post_periods
    base_treatment_period = pre_periods

    data = []
    for unit in range(1, n_units + 1):
        if staggered:
            # Staggered treatment timing
            treatment_period = base_treatment_period + np.random.randint(-3, 4)
        else:
            treatment_period = base_treatment_period

        unit_fe = np.random.randn() * 0.5

        for period in range(n_periods):
            event_time = period - treatment_period
            is_post = period >= treatment_period

            # Dynamic treatment effects
            if is_post:
                dynamic_effect = 0.5 + 0.02 * event_time
            else:
                dynamic_effect = 0

            outcome = (
                unit_fe +
                period * 0.01 +
                dynamic_effect +
                np.random.randn() * 0.3
            )

            data.append({
                'unit_id': unit,
                'period': period,
                'treatment_period': treatment_period,
                'event_time': event_time,
                'treated': int(is_post),
                'outcome': outcome
            })

    return pd.DataFrame(data)


def generate_linkage_data(
    n_records: int = 1000,
    match_rate: float = 0.8,
    seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate two datasets for record linkage testing.

    Parameters
    ----------
    n_records : int
        Number of records in each dataset
    match_rate : float
        Fraction of records that should match
    seed : int
        Random seed

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        Two DataFrames that can be linked
    """
    np.random.seed(seed)

    # Generate master dataset
    names = [f'Entity_{i:04d}' for i in range(n_records)]

    df1 = pd.DataFrame({
        'id1': range(1, n_records + 1),
        'name': names,
        'value1': np.random.randn(n_records)
    })

    # Generate second dataset with some matches
    n_matches = int(n_records * match_rate)
    matched_indices = np.random.choice(n_records, n_matches, replace=False)

    df2_records = []
    for i, idx in enumerate(matched_indices):
        df2_records.append({
            'id2': i + 1,
            'name': names[idx],  # Exact match
            'value2': np.random.randn()
        })

    # Add non-matching records
    for i in range(n_records - n_matches):
        df2_records.append({
            'id2': n_matches + i + 1,
            'name': f'Other_{i:04d}',
            'value2': np.random.randn()
        })

    df2 = pd.DataFrame(df2_records)

    return df1, df2


def generate_with_missing(
    n: int = 1000,
    missing_rate: float = 0.1,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a dataset with controlled missing values.

    Parameters
    ----------
    n : int
        Number of observations
    missing_rate : float
        Fraction of values to set as missing
    seed : int
        Random seed

    Returns
    -------
    pd.DataFrame
        Dataset with missing values
    """
    np.random.seed(seed)

    df = pd.DataFrame({
        'id': range(1, n + 1),
        'complete_col': np.random.randn(n),
        'partial_col': np.random.randn(n),
        'sparse_col': np.random.randn(n)
    })

    # Introduce missing values
    n_missing = int(n * missing_rate)
    partial_mask = np.random.choice(n, n_missing, replace=False)
    sparse_mask = np.random.choice(n, n_missing * 2, replace=False)

    df.loc[partial_mask, 'partial_col'] = np.nan
    df.loc[sparse_mask, 'sparse_col'] = np.nan

    return df


def generate_time_series(
    n_periods: int = 100,
    trend: float = 0.01,
    seasonality: bool = True,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a time series dataset.

    Parameters
    ----------
    n_periods : int
        Number of time periods
    trend : float
        Linear trend coefficient
    seasonality : bool
        Whether to include seasonal pattern
    seed : int
        Random seed

    Returns
    -------
    pd.DataFrame
        Time series dataset
    """
    np.random.seed(seed)

    dates = pd.date_range('2020-01-01', periods=n_periods, freq='M')

    trend_component = np.arange(n_periods) * trend
    noise = np.random.randn(n_periods) * 0.1

    if seasonality:
        seasonal = 0.2 * np.sin(2 * np.pi * np.arange(n_periods) / 12)
    else:
        seasonal = 0

    value = trend_component + seasonal + noise

    return pd.DataFrame({
        'date': dates,
        'period': range(1, n_periods + 1),
        'value': value,
        'trend': trend_component,
        'seasonal': seasonal if seasonality else np.zeros(n_periods)
    })
