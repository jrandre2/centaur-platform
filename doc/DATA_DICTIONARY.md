# Data Dictionary

**Related**: [PIPELINE.md](PIPELINE.md) | [METHODOLOGY.md](METHODOLOGY.md) | [ARCHITECTURE.md](ARCHITECTURE.md)
**Status**: Template
**Last Updated**: [Date]

---

## Overview

This document defines all variables used in the analysis, their naming conventions, data types, and handling rules.

---

## Naming Conventions

### General Rules

1. **Lowercase with underscores**: Use `snake_case` for all variable names
   - Good: `sale_price`, `treatment_date`, `unit_id`
   - Bad: `SalePrice`, `treatmentDate`, `UnitID`

2. **Descriptive but concise**: Names should be self-documenting
   - Good: `log_price`, `post_treatment`
   - Bad: `lp`, `pt`, `var1`

3. **Consistent prefixes**: Use prefixes to indicate variable type or source

| Prefix | Meaning | Example |
|--------|---------|---------|
| `log_` | Natural log transformation | `log_price`, `log_income` |
| `pct_` | Percentage (0-100) | `pct_change`, `pct_vacant` |
| `is_` | Boolean indicator | `is_treated`, `is_valid` |
| `n_` | Count | `n_bedrooms`, `n_transactions` |
| `d_` | Dummy/indicator variable | `d_post`, `d_treat` |
| `fe_` | Fixed effect | `fe_unit`, `fe_time` |

4. **Suffix conventions**:

| Suffix | Meaning | Example |
|--------|---------|---------|
| `_id` | Identifier | `unit_id`, `parcel_id` |
| `_date` | Date variable | `sale_date`, `treatment_date` |
| `_m` | Monthly period | `sale_m`, `event_m` |
| `_q` | Quarterly period | `sale_q` |
| `_y` | Annual period | `sale_y` |

### Signed Conventions

For spatial or directional variables, maintain consistent sign conventions:

```
Example: Distance from boundary
- Negative = INSIDE the boundary (e.g., in flood zone)
- Positive = OUTSIDE the boundary (e.g., not in flood zone)
```

Document any signed conventions clearly in this section.

---

## Data Types

### Standard Types

| Type | Python Type | Description | Example Values |
|------|-------------|-------------|----------------|
| `string` | `str` | Text identifier | `"ABC123"`, `"parcel_001"` |
| `int` | `int64` | Integer numeric | `1`, `42`, `-5` |
| `float` | `float64` | Decimal numeric | `1.5`, `-3.14`, `NaN` |
| `boolean` | `bool` | True/False | `True`, `False` |
| `datetime` | `datetime64` | Date/time | `2020-01-15` |
| `period` | `period` | Time period | `2020-01`, `2020Q1` |
| `category` | `category` | Categorical | `"high"`, `"medium"`, `"low"` |

### Type Coercion Rules

1. **IDs should be strings**: Even if numeric, store as strings to avoid precision issues
2. **Dates should be datetime**: Not strings, to enable date arithmetic
3. **Booleans preferred over 0/1**: Except when used in regression

---

## Identifier Variables

Core identifiers used across all data files:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `unit_id` | string | Primary unit identifier | `"U0001"` |
| `period` | int | Time period index | `0`, `1`, `12` |
| `obs_id` | string | Unique observation ID | `"U0001_P12"` |

### Panel Structure

The primary unit of analysis is `unit_id` × `period`:

```
unit_id | period | outcome | treatment
--------|--------|---------|----------
U0001   | 0      | 10.5    | 0
U0001   | 1      | 11.2    | 0
U0001   | 2      | 12.8    | 1
U0002   | 0      | 8.3     | 0
...
```

---

## Outcome Variables

### Primary Outcomes

| Variable | Type | Unit | Range | Description |
|----------|------|------|-------|-------------|
| `outcome` | float | units | [0, ∞) | Main outcome of interest |
| `log_outcome` | float | log units | (-∞, ∞) | Natural log of outcome |

### Derived Outcomes

| Variable | Formula | Description |
|----------|---------|-------------|
| `outcome_change` | `outcome_t - outcome_{t-1}` | First difference |
| `outcome_pct_change` | `(outcome_t - outcome_{t-1}) / outcome_{t-1} × 100` | Percent change |
| `outcome_zscore` | `(outcome - mean) / std` | Standardized outcome |

---

## Treatment Variables

### Treatment Status

| Variable | Type | Values | Description |
|----------|------|--------|-------------|
| `treatment` | int | 0, 1 | Currently treated (DiD) |
| `ever_treated` | int | 0, 1 | Ever receives treatment |
| `post` | int | 0, 1 | Post-treatment period |
| `treat_x_post` | int | 0, 1 | Treatment × Post interaction |

### Treatment Timing

| Variable | Type | Description |
|----------|------|-------------|
| `treatment_time` | int/NaN | Period when treatment begins (NaN if never treated) |
| `treatment_date` | datetime | Calendar date of treatment |
| `treatment_cohort` | string | Cohort identifier for staggered adoption |

### Event Time

| Variable | Type | Range | Description |
|----------|------|-------|-------------|
| `event_time` | int | [-K, L] | Periods relative to treatment |
| `event_time_binned` | int | [-K, L] | Event time with endpoint binning |

Event time conventions:
- `event_time = 0`: Treatment period
- `event_time < 0`: Pre-treatment
- `event_time > 0`: Post-treatment
- `NaN`: Never-treated units (optional)

---

## Control Variables

### Continuous Controls

| Variable | Type | Unit | Description |
|----------|------|------|-------------|
| `covariate_0` | float | varies | First continuous covariate |
| `covariate_1` | float | varies | Second continuous covariate |
| `covariate_2` | float | varies | Third continuous covariate |

### Categorical Controls

| Variable | Type | Categories | Description |
|----------|------|------------|-------------|
| `category` | category | A, B, C | Categorical grouping |
| `region` | category | varies | Geographic region |

---

## Fixed Effect Variables

| Variable | Type | Levels | Description |
|----------|------|--------|-------------|
| `fe_unit` | category | N_units | Unit fixed effect group |
| `fe_time` | category | N_periods | Time fixed effect group |
| `fe_unit_time` | category | N_units × N_periods | Unit-time interaction FE |

### Fixed Effect Implementation

Fixed effects are implemented via the within transformation (demeaning):

```python
# Unit FE: demean within unit
df['outcome_demeaned'] = df.groupby('unit_id')['outcome'].transform(
    lambda x: x - x.mean()
)
```

---

## Spatial Variables

For projects with spatial components:

| Variable | Type | Unit | Description |
|----------|------|------|-------------|
| `latitude` | float | degrees | WGS84 latitude |
| `longitude` | float | degrees | WGS84 longitude |
| `distance_to_boundary` | float | meters | Signed distance (negative = inside) |

### Spatial Conventions

- Coordinates: WGS84 (EPSG:4326) unless otherwise specified
- Distances: Meters
- Areas: Square meters or hectares
- Sign: Negative inside, positive outside

---

## Data Files

### Pipeline Stage Outputs

| Stage | Output File | Key Variables |
|-------|-------------|---------------|
| s00 | `data_work/data_raw.parquet` | Raw variables after cleaning |
| s01 | `data_work/data_linked.parquet` | + linkage indicators |
| s02 | `data_work/panel.parquet` | + FE, event time, treatment |

### Main Analysis Panel

**File:** `data_work/panel.parquet`

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `unit_id` | string | s00 | Unit identifier |
| `period` | int | s00 | Time period |
| `outcome` | float | s00 | Outcome variable |
| `treatment` | int | s02 | Treatment indicator |
| `ever_treated` | int | s02 | Ever treated indicator |
| `event_time` | int | s02 | Event time relative to treatment |
| `fe_unit` | category | s02 | Unit fixed effect |
| `fe_time` | category | s02 | Time fixed effect |

### Diagnostic Files

**Directory:** `data_work/diagnostics/`

| File | Variables | Description |
|------|-----------|-------------|
| `estimation_results.csv` | specification, coefficient, std_error, p_value, n_obs | Main results |
| `robustness_results.csv` | test_name, test_type, coefficient, std_error, p_value | Robustness checks |
| `linkage_summary.csv` | source, n_matched, match_rate | Linkage diagnostics |
| `panel_diagnostics.csv` | n_units, n_periods, balance_rate | Panel structure |

---

## Value Coding

### Boolean/Indicator Variables

| Value | Meaning |
|-------|---------|
| 0 | No / False / Control / Pre-treatment |
| 1 | Yes / True / Treated / Post-treatment |

### Missing Value Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `NaN` | Not available | Standard missing |
| `-999` | Never applicable | Recode to NaN |
| Empty string | Missing text | Recode to NaN |

---

## Missing Value Handling

### Default Rules

| Variable Type | Default Handling |
|---------------|------------------|
| Identifiers | Must not be missing (validation error) |
| Outcomes | Drop observation |
| Treatment | Must not be missing (validation error) |
| Controls | Impute or drop (document choice) |

### Imputation Methods

If imputation is used, document the method:

| Variable | Method | Details |
|----------|--------|---------|
| [var1] | Mean imputation | Group mean by unit |
| [var2] | Forward fill | Within unit time series |
| [var3] | Regression imputation | Predicted from [predictors] |

---

## Synthetic Data Variables

When using demo data from `SyntheticDataGenerator`:

### Panel Data (`generate_panel`)

| Variable | Type | Description |
|----------|------|-------------|
| `unit_id` | int | Unit identifier (0 to n_units-1) |
| `period` | int | Time period (0 to n_periods-1) |
| `outcome` | float | Simulated outcome with treatment effect |
| `treatment` | int | Treatment indicator |
| `ever_treated` | int | Ever treated indicator |
| `treatment_time` | int/NaN | Period of treatment onset |
| `covariate_0` to `covariate_4` | float | Random covariates (N(0,1)) |

### Event Study Data (`generate_event_study`)

| Variable | Type | Description |
|----------|------|-------------|
| `event_time` | int | Periods relative to treatment |
| `dynamic_effect` | float | True dynamic effect (for validation) |

### RD Data (`generate_rd_data`)

| Variable | Type | Description |
|----------|------|-------------|
| `running_var` | float | Continuous running variable |
| `above_cutoff` | int | Above cutoff indicator |
| `true_effect` | float | True treatment effect (for validation) |

---

## Quality Checks

### Required Validations

| Check | Variables | Rule |
|-------|-----------|------|
| No duplicates | `unit_id`, `period` | Unique combinations |
| No missing IDs | `unit_id` | Complete |
| Valid treatment | `treatment` | Values in {0, 1} |
| Balanced panel | all | Optional: equal periods per unit |

### Recommended Checks

| Check | Implementation |
|-------|----------------|
| Outliers | Flag values > 3 SD from mean |
| Time gaps | Check for missing periods |
| Treatment timing | Verify treatment_time matches treatment=1 |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| [Date] | 1.0 | Initial data dictionary |
| [Date] | 1.1 | Added [variables] |

---

## Project-Specific Variables

[Add your project-specific variable definitions here]

| Variable | Type | Unit | Description |
|----------|------|------|-------------|
| | | | |
