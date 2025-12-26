#!/usr/bin/env python3
"""
Synthetic data generator for demonstration and testing.

This module provides generators for creating realistic synthetic datasets
that can be used to demonstrate the pipeline without real data.

Usage
-----
from src.utils.synthetic_data import SyntheticDataGenerator

gen = SyntheticDataGenerator(seed=42)

# Generate panel data
panel = gen.generate_panel(n_units=1000, n_periods=24)

# Generate cross-sectional data
cross = gen.generate_cross_section(n_obs=5000)

# Generate event study data
event = gen.generate_event_study(n_units=500, pre_periods=12, post_periods=12)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union, Literal
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ============================================================
# SYNTHETIC DATA GENERATOR CLASS
# ============================================================

class SyntheticDataGenerator:
    """
    Generator for synthetic research data.

    This class provides methods to generate various types of synthetic
    datasets commonly used in empirical research, including panel data,
    cross-sectional data, event studies, and more.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility

    Examples
    --------
    >>> gen = SyntheticDataGenerator(seed=42)
    >>> panel = gen.generate_panel(n_units=100, n_periods=24)
    >>> panel.shape
    (2400, 8)
    """

    def __init__(self, seed: int = 42):
        """Initialize the generator with a random seed."""
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def reset_seed(self, seed: Optional[int] = None):
        """Reset the random number generator with a new or original seed."""
        self.rng = np.random.default_rng(seed or self.seed)

    # ============================================================
    # PANEL DATA GENERATORS
    # ============================================================

    def generate_panel(
        self,
        n_units: int = 1000,
        n_periods: int = 24,
        treatment_period: int = 12,
        treatment_share: float = 0.5,
        treatment_effect: float = 0.1,
        unit_fe_sd: float = 0.5,
        time_trend: float = 0.01,
        noise_sd: float = 0.3,
        n_covariates: int = 3,
        include_dates: bool = True,
        start_date: str = '2020-01-01'
    ) -> pd.DataFrame:
        """
        Generate a balanced panel dataset with treatment effects.

        Parameters
        ----------
        n_units : int
            Number of cross-sectional units
        n_periods : int
            Number of time periods
        treatment_period : int
            Period when treatment begins (0-indexed)
        treatment_share : float
            Fraction of units that receive treatment
        treatment_effect : float
            True average treatment effect
        unit_fe_sd : float
            Standard deviation of unit fixed effects
        time_trend : float
            Coefficient on linear time trend
        noise_sd : float
            Standard deviation of idiosyncratic errors
        n_covariates : int
            Number of additional covariates to generate
        include_dates : bool
            Whether to include calendar dates
        start_date : str
            Starting date if include_dates is True

        Returns
        -------
        pd.DataFrame
            Balanced panel dataset
        """
        n_treated = int(n_units * treatment_share)
        treated_units = set(range(1, n_treated + 1))

        # Generate unit fixed effects
        unit_fe = {
            unit: self.rng.normal(0, unit_fe_sd)
            for unit in range(1, n_units + 1)
        }

        # Generate time fixed effects
        time_fe = {
            period: self.rng.normal(0, 0.1)
            for period in range(n_periods)
        }

        data = []
        for unit in range(1, n_units + 1):
            is_treated_unit = unit in treated_units

            for period in range(n_periods):
                is_post = period >= treatment_period
                treatment = 1 if is_treated_unit and is_post else 0

                # Generate outcome
                outcome = (
                    unit_fe[unit] +
                    time_fe[period] +
                    period * time_trend +
                    treatment * treatment_effect +
                    self.rng.normal(0, noise_sd)
                )

                row = {
                    'unit_id': unit,
                    'period': period,
                    'treatment': treatment,
                    'treated_unit': int(is_treated_unit),
                    'post': int(is_post),
                    'outcome': outcome,
                }

                # Add covariates
                for i in range(n_covariates):
                    row[f'covariate_{i+1}'] = self.rng.normal(0, 1)

                data.append(row)

        df = pd.DataFrame(data)

        # Add calendar dates if requested
        if include_dates:
            base_date = pd.to_datetime(start_date)
            df['date'] = df['period'].apply(
                lambda p: base_date + pd.DateOffset(months=p)
            )
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month

        return df

    def generate_unbalanced_panel(
        self,
        n_units: int = 1000,
        n_periods: int = 24,
        attrition_rate: float = 0.02,
        entry_rate: float = 0.01,
        **kwargs
    ) -> pd.DataFrame:
        """
        Generate an unbalanced panel with entry and exit.

        Parameters
        ----------
        n_units : int
            Initial number of units
        n_periods : int
            Number of time periods
        attrition_rate : float
            Per-period probability of exit
        entry_rate : float
            Per-period probability of new entry (as fraction of initial n)
        **kwargs
            Additional arguments passed to generate_panel

        Returns
        -------
        pd.DataFrame
            Unbalanced panel dataset
        """
        # Start with balanced panel
        df = self.generate_panel(n_units=n_units, n_periods=n_periods, **kwargs)

        # Mark units for exit
        exit_period = {}
        for unit in range(1, n_units + 1):
            for period in range(n_periods):
                if self.rng.random() < attrition_rate:
                    exit_period[unit] = period
                    break

        # Remove observations after exit
        mask = df.apply(
            lambda row: row['period'] < exit_period.get(row['unit_id'], n_periods),
            axis=1
        )
        df = df[mask].copy()

        # Add new entrants
        next_unit_id = n_units + 1
        new_data = []
        for period in range(1, n_periods):
            n_entrants = int(n_units * entry_rate)
            for _ in range(n_entrants):
                for t in range(period, n_periods):
                    new_data.append({
                        'unit_id': next_unit_id,
                        'period': t,
                        'treatment': 0,
                        'treated_unit': 0,
                        'post': int(t >= kwargs.get('treatment_period', 12)),
                        'outcome': self.rng.normal(0, 0.5),
                        'entry_period': period
                    })
                next_unit_id += 1

        if new_data:
            df_new = pd.DataFrame(new_data)
            df = pd.concat([df, df_new], ignore_index=True)

        return df.sort_values(['unit_id', 'period']).reset_index(drop=True)

    # ============================================================
    # EVENT STUDY GENERATORS
    # ============================================================

    def generate_event_study(
        self,
        n_units: int = 500,
        pre_periods: int = 12,
        post_periods: int = 12,
        staggered: bool = False,
        stagger_range: tuple = (-3, 4),
        never_treated_share: float = 0.0,
        dynamic_effects: bool = True,
        base_effect: float = 0.5,
        effect_growth: float = 0.02,
        pre_trend: float = 0.0,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generate event study data with dynamic treatment effects.

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
        stagger_range : tuple
            Range for staggered treatment timing (min, max offset)
        never_treated_share : float
            Fraction of units never treated (pure control)
        dynamic_effects : bool
            If True, effects vary with time since treatment
        base_effect : float
            Immediate treatment effect
        effect_growth : float
            Per-period growth in treatment effect
        pre_trend : float
            Coefficient on pre-treatment trend (for testing)
        seed : int, optional
            Override seed for this generation

        Returns
        -------
        pd.DataFrame
            Event study dataset with event_time variable
        """
        if seed is not None:
            self.reset_seed(seed)

        n_periods = pre_periods + post_periods
        base_treatment_period = pre_periods

        # Determine treatment timing for each unit
        n_never_treated = int(n_units * never_treated_share)
        never_treated = set(range(n_units - n_never_treated + 1, n_units + 1))

        treatment_timing = {}
        for unit in range(1, n_units + 1):
            if unit in never_treated:
                treatment_timing[unit] = None
            elif staggered:
                offset = self.rng.integers(stagger_range[0], stagger_range[1])
                treatment_timing[unit] = base_treatment_period + offset
            else:
                treatment_timing[unit] = base_treatment_period

        # Generate unit fixed effects
        unit_fe = {
            unit: self.rng.normal(0, 0.5)
            for unit in range(1, n_units + 1)
        }

        data = []
        for unit in range(1, n_units + 1):
            treat_period = treatment_timing[unit]

            for period in range(n_periods):
                if treat_period is None:
                    event_time = None
                    is_post = False
                else:
                    event_time = period - treat_period
                    is_post = period >= treat_period

                # Calculate treatment effect
                if is_post and dynamic_effects:
                    te = base_effect + effect_growth * event_time
                elif is_post:
                    te = base_effect
                else:
                    te = 0

                # Add pre-trend if specified
                if not is_post and pre_trend != 0:
                    te += pre_trend * (period - base_treatment_period)

                outcome = (
                    unit_fe[unit] +
                    period * 0.01 +  # Time trend
                    te +
                    self.rng.normal(0, 0.3)
                )

                data.append({
                    'unit_id': unit,
                    'period': period,
                    'treatment_period': treat_period,
                    'event_time': event_time,
                    'treated': int(is_post),
                    'never_treated': int(unit in never_treated),
                    'outcome': outcome
                })

        return pd.DataFrame(data)

    # ============================================================
    # CROSS-SECTIONAL GENERATORS
    # ============================================================

    def generate_cross_section(
        self,
        n_obs: int = 5000,
        n_covariates: int = 10,
        treatment_share: float = 0.5,
        treatment_effect: float = 0.5,
        covariate_effects: Optional[list] = None,
        noise_sd: float = 0.5,
        include_categorical: bool = True
    ) -> pd.DataFrame:
        """
        Generate a cross-sectional dataset.

        Parameters
        ----------
        n_obs : int
            Number of observations
        n_covariates : int
            Number of continuous covariates
        treatment_share : float
            Fraction in treatment group
        treatment_effect : float
            True treatment effect
        covariate_effects : list, optional
            Coefficients for each covariate
        noise_sd : float
            Standard deviation of error term
        include_categorical : bool
            Whether to include categorical variables

        Returns
        -------
        pd.DataFrame
            Cross-sectional dataset
        """
        if covariate_effects is None:
            covariate_effects = [0.3 / (i + 1) for i in range(n_covariates)]

        # Generate treatment assignment
        treatment = self.rng.choice(
            [0, 1], n_obs, p=[1 - treatment_share, treatment_share]
        )

        # Generate covariates
        X = self.rng.standard_normal((n_obs, n_covariates))

        # Generate outcome
        covariate_contribution = sum(
            X[:, i] * covariate_effects[i]
            for i in range(min(len(covariate_effects), n_covariates))
        )
        outcome = (
            treatment * treatment_effect +
            covariate_contribution +
            self.rng.normal(0, noise_sd, n_obs)
        )

        data = {
            'id': range(1, n_obs + 1),
            'treatment': treatment,
            'outcome': outcome
        }

        # Add covariates
        for i in range(n_covariates):
            data[f'x{i+1}'] = X[:, i]

        df = pd.DataFrame(data)

        # Add categorical variables
        if include_categorical:
            df['region'] = self.rng.choice(
                ['North', 'South', 'East', 'West'], n_obs
            )
            df['category'] = self.rng.choice(['A', 'B', 'C'], n_obs)

        return df

    # ============================================================
    # RECORD LINKAGE DATA
    # ============================================================

    def generate_linkage_data(
        self,
        n_records: int = 1000,
        match_rate: float = 0.8,
        fuzzy_match_rate: float = 0.1,
        typo_rate: float = 0.05
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate two datasets suitable for record linkage.

        Parameters
        ----------
        n_records : int
            Number of records in primary dataset
        match_rate : float
            Fraction with exact matches
        fuzzy_match_rate : float
            Fraction with fuzzy matches (variations)
        typo_rate : float
            Rate of character-level typos in fuzzy matches

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            Two DataFrames that can be linked
        """
        # Generate primary dataset
        names = [f'Entity_{i:04d}' for i in range(n_records)]
        addresses = [f'{i * 10 + 100} Main Street' for i in range(n_records)]

        df1 = pd.DataFrame({
            'id1': range(1, n_records + 1),
            'name': names,
            'address': addresses,
            'value1': self.rng.normal(100, 20, n_records)
        })

        # Generate secondary dataset
        n_exact = int(n_records * match_rate)
        n_fuzzy = int(n_records * fuzzy_match_rate)

        records2 = []

        # Exact matches
        exact_indices = self.rng.choice(n_records, n_exact, replace=False)
        for i, idx in enumerate(exact_indices):
            records2.append({
                'id2': i + 1,
                'name': names[idx],
                'address': addresses[idx],
                'value2': self.rng.normal(50, 10),
                'match_type': 'exact'
            })

        # Fuzzy matches (with typos)
        fuzzy_indices = self.rng.choice(
            [i for i in range(n_records) if i not in exact_indices],
            min(n_fuzzy, n_records - n_exact),
            replace=False
        )
        for idx in fuzzy_indices:
            name = self._add_typos(names[idx], typo_rate)
            records2.append({
                'id2': len(records2) + 1,
                'name': name,
                'address': addresses[idx],
                'value2': self.rng.normal(50, 10),
                'match_type': 'fuzzy'
            })

        # Non-matching records
        n_unmatched = n_records - n_exact - len(fuzzy_indices)
        for i in range(n_unmatched):
            records2.append({
                'id2': len(records2) + 1,
                'name': f'Other_{i:04d}',
                'address': f'{9000 + i} Unknown Ave',
                'value2': self.rng.normal(50, 10),
                'match_type': 'none'
            })

        df2 = pd.DataFrame(records2)
        df2 = df2.sample(frac=1, random_state=self.seed).reset_index(drop=True)

        return df1, df2

    def _add_typos(self, text: str, rate: float) -> str:
        """Add random character-level typos to text."""
        chars = list(text)
        for i in range(len(chars)):
            if self.rng.random() < rate:
                # Replace with adjacent character
                if chars[i].isalpha():
                    offset = self.rng.choice([-1, 1])
                    chars[i] = chr(ord(chars[i]) + offset)
        return ''.join(chars)

    # ============================================================
    # SPATIAL DATA GENERATORS
    # ============================================================

    def generate_spatial_data(
        self,
        n_points: int = 1000,
        center: tuple = (40.0, -74.0),
        spread: float = 0.5,
        n_clusters: int = 0,
        include_treatment_zone: bool = True,
        treatment_radius: float = 0.1
    ) -> pd.DataFrame:
        """
        Generate spatial point data.

        Parameters
        ----------
        n_points : int
            Number of spatial points
        center : tuple
            Center coordinates (lat, lon)
        spread : float
            Spread of points around center
        n_clusters : int
            Number of spatial clusters (0 for uniform)
        include_treatment_zone : bool
            Whether to include a treatment zone
        treatment_radius : float
            Radius of treatment zone around center

        Returns
        -------
        pd.DataFrame
            Spatial dataset with lat/lon coordinates
        """
        if n_clusters > 0:
            # Generate clustered points
            cluster_centers = self.rng.normal(
                [center[0], center[1]], spread / 2, (n_clusters, 2)
            )
            cluster_assignment = self.rng.integers(0, n_clusters, n_points)

            lats = []
            lons = []
            for i in range(n_points):
                cc = cluster_centers[cluster_assignment[i]]
                lats.append(self.rng.normal(cc[0], spread / 4))
                lons.append(self.rng.normal(cc[1], spread / 4))
        else:
            # Uniform distribution
            lats = self.rng.normal(center[0], spread, n_points)
            lons = self.rng.normal(center[1], spread, n_points)

        df = pd.DataFrame({
            'id': range(1, n_points + 1),
            'latitude': lats,
            'longitude': lons,
            'value': self.rng.normal(100, 20, n_points)
        })

        if include_treatment_zone:
            # Calculate distance from center
            df['dist_to_center'] = np.sqrt(
                (df['latitude'] - center[0]) ** 2 +
                (df['longitude'] - center[1]) ** 2
            )
            df['in_treatment_zone'] = (
                df['dist_to_center'] < treatment_radius
            ).astype(int)

        if n_clusters > 0:
            df['cluster'] = cluster_assignment

        return df

    # ============================================================
    # TIME SERIES GENERATORS
    # ============================================================

    def generate_time_series(
        self,
        n_periods: int = 100,
        trend: float = 0.01,
        seasonality_period: int = 12,
        seasonality_amplitude: float = 0.2,
        ar_coef: float = 0.7,
        noise_sd: float = 0.1,
        start_date: str = '2015-01-01',
        freq: str = 'M'
    ) -> pd.DataFrame:
        """
        Generate time series data with trend, seasonality, and AR structure.

        Parameters
        ----------
        n_periods : int
            Number of time periods
        trend : float
            Linear trend coefficient
        seasonality_period : int
            Period of seasonal cycle
        seasonality_amplitude : float
            Amplitude of seasonal component
        ar_coef : float
            Autoregressive coefficient
        noise_sd : float
            Standard deviation of innovations
        start_date : str
            Starting date
        freq : str
            Pandas frequency string

        Returns
        -------
        pd.DataFrame
            Time series dataset
        """
        dates = pd.date_range(start_date, periods=n_periods, freq=freq)

        # Trend component
        trend_component = np.arange(n_periods) * trend

        # Seasonal component
        seasonal = seasonality_amplitude * np.sin(
            2 * np.pi * np.arange(n_periods) / seasonality_period
        )

        # AR(1) component
        ar_component = np.zeros(n_periods)
        for t in range(1, n_periods):
            ar_component[t] = (
                ar_coef * ar_component[t-1] +
                self.rng.normal(0, noise_sd)
            )

        value = trend_component + seasonal + ar_component

        return pd.DataFrame({
            'date': dates,
            'period': range(n_periods),
            'value': value,
            'trend': trend_component,
            'seasonal': seasonal,
            'residual': ar_component
        })

    # ============================================================
    # REGRESSION DISCONTINUITY DATA
    # ============================================================

    def generate_rd_data(
        self,
        n_obs: int = 2000,
        cutoff: float = 0.0,
        treatment_effect: float = 0.5,
        slope_left: float = 0.3,
        slope_right: float = 0.3,
        noise_sd: float = 0.5,
        running_var_range: tuple = (-1, 1),
        bandwidth: float = 0.5
    ) -> pd.DataFrame:
        """
        Generate regression discontinuity data.

        Parameters
        ----------
        n_obs : int
            Number of observations
        cutoff : float
            RD cutoff value
        treatment_effect : float
            True effect at the cutoff
        slope_left : float
            Slope of outcome on running variable (left of cutoff)
        slope_right : float
            Slope on right of cutoff
        noise_sd : float
            Standard deviation of error term
        running_var_range : tuple
            Range of running variable
        bandwidth : float
            Suggested optimal bandwidth

        Returns
        -------
        pd.DataFrame
            RD dataset
        """
        # Generate running variable
        running = self.rng.uniform(
            running_var_range[0], running_var_range[1], n_obs
        )

        # Treatment assignment
        treatment = (running >= cutoff).astype(int)

        # Centered running variable
        running_centered = running - cutoff

        # Generate outcome
        outcome = np.where(
            running < cutoff,
            slope_left * running_centered,
            treatment_effect + slope_right * running_centered
        )
        outcome += self.rng.normal(0, noise_sd, n_obs)

        df = pd.DataFrame({
            'id': range(1, n_obs + 1),
            'running_var': running,
            'running_centered': running_centered,
            'treatment': treatment,
            'outcome': outcome
        })

        # Add bandwidth indicator
        df['in_bandwidth'] = (
            np.abs(df['running_centered']) <= bandwidth
        ).astype(int)

        return df

    # ============================================================
    # HELPER: SAVE GENERATED DATA
    # ============================================================

    def save_demo_data(
        self,
        output_dir: Union[str, Path],
        overwrite: bool = False
    ) -> dict:
        """
        Generate and save a complete set of demo data.

        Parameters
        ----------
        output_dir : str or Path
            Directory to save data files
        overwrite : bool
            Whether to overwrite existing files

        Returns
        -------
        dict
            Paths to generated files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        # Generate and save each type
        datasets = {
            'panel': self.generate_panel(n_units=500, n_periods=24),
            'cross_section': self.generate_cross_section(n_obs=2000),
            'event_study': self.generate_event_study(n_units=300),
            'rd_data': self.generate_rd_data(n_obs=1500),
            'time_series': self.generate_time_series(n_periods=60),
            'spatial': self.generate_spatial_data(n_points=500),
        }

        for name, df in datasets.items():
            path = output_dir / f'{name}.parquet'
            if path.exists() and not overwrite:
                print(f"Skipping {name} (file exists)")
                continue
            df.to_parquet(path)
            files[name] = path
            print(f"Saved {name}: {len(df)} rows -> {path}")

        return files


# ============================================================
# CLI FUNCTION
# ============================================================

def main():
    """Generate demo data from command line."""
    from utils.helpers import get_data_dir

    gen = SyntheticDataGenerator(seed=42)
    output_dir = get_data_dir('raw')

    print("Generating synthetic demo data...")
    files = gen.save_demo_data(output_dir, overwrite=True)

    print(f"\nGenerated {len(files)} demo datasets in {output_dir}")


if __name__ == '__main__':
    main()
