#!/usr/bin/env python3
"""
Data validation framework for the research pipeline.

This module provides a flexible validation system for checking data quality
at various pipeline stages. It supports custom rules, severity levels,
and generates detailed validation reports.

Usage
-----
from src.utils.validation import DataValidator, no_missing_values, unique_values

# Create validator and add rules
validator = DataValidator()
validator.add_rule(no_missing_values(['id', 'outcome']))
validator.add_rule(unique_values('id'))

# Run validation
report = validator.validate(df)
if report.has_errors:
    print(report.format())
    raise ValueError("Validation failed")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Any, Union, Literal
from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ValidationRule:
    """
    A single validation rule.

    Attributes
    ----------
    name : str
        Short name for the rule
    check : Callable
        Function that takes a DataFrame and returns (passed: bool, message: str)
    severity : str
        'error', 'warning', or 'info'
    description : str
        Longer description of what this rule checks
    """
    name: str
    check: Callable[[pd.DataFrame], tuple[bool, str]]
    severity: Literal['error', 'warning', 'info'] = 'error'
    description: str = ''


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    rule_name: str
    passed: bool
    message: str
    severity: Literal['error', 'warning', 'info']


@dataclass
class ValidationReport:
    """
    Complete validation report.

    Attributes
    ----------
    results : list
        List of ValidationResult objects
    """
    results: list = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if any error-level validations failed."""
        return any(
            not r.passed and r.severity == 'error'
            for r in self.results
        )

    @property
    def has_warnings(self) -> bool:
        """Check if any warning-level validations failed."""
        return any(
            not r.passed and r.severity == 'warning'
            for r in self.results
        )

    @property
    def passed(self) -> bool:
        """Check if all validations passed (including warnings)."""
        return all(r.passed for r in self.results)

    @property
    def error_count(self) -> int:
        """Count of failed error-level validations."""
        return sum(1 for r in self.results if not r.passed and r.severity == 'error')

    @property
    def warning_count(self) -> int:
        """Count of failed warning-level validations."""
        return sum(1 for r in self.results if not r.passed and r.severity == 'warning')

    def format(self, show_passed: bool = False) -> str:
        """
        Format the report as a string.

        Parameters
        ----------
        show_passed : bool
            Whether to include passed checks in output

        Returns
        -------
        str
            Formatted validation report
        """
        lines = ["=" * 50, "VALIDATION REPORT", "=" * 50, ""]

        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        lines.append(f"Total checks: {total}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {total - passed}")

        if self.error_count > 0:
            lines.append(f"  Errors: {self.error_count}")
        if self.warning_count > 0:
            lines.append(f"  Warnings: {self.warning_count}")

        lines.append("")

        # Details
        for result in self.results:
            if result.passed and not show_passed:
                continue

            status = "[PASS]" if result.passed else f"[FAIL:{result.severity.upper()}]"
            lines.append(f"{status} {result.rule_name}")
            if result.message:
                lines.append(f"    {result.message}")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            'passed': self.passed,
            'has_errors': self.has_errors,
            'has_warnings': self.has_warnings,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'results': [
                {
                    'rule_name': r.rule_name,
                    'passed': r.passed,
                    'message': r.message,
                    'severity': r.severity
                }
                for r in self.results
            ]
        }


# ============================================================
# VALIDATOR CLASS
# ============================================================

class DataValidator:
    """
    Validator for DataFrame quality checks.

    Examples
    --------
    >>> validator = DataValidator()
    >>> validator.add_rule(no_missing_values(['id', 'value']))
    >>> validator.add_rule(unique_values('id'))
    >>> report = validator.validate(df)
    >>> if report.has_errors:
    ...     raise ValueError(report.format())
    """

    def __init__(self):
        self.rules: list[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> 'DataValidator':
        """
        Add a validation rule.

        Parameters
        ----------
        rule : ValidationRule
            The rule to add

        Returns
        -------
        DataValidator
            Self, for method chaining
        """
        self.rules.append(rule)
        return self

    def add_rules(self, rules: list[ValidationRule]) -> 'DataValidator':
        """Add multiple rules at once."""
        for rule in rules:
            self.add_rule(rule)
        return self

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """
        Run all validation rules on a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate

        Returns
        -------
        ValidationReport
            Report with all validation results
        """
        report = ValidationReport()

        for rule in self.rules:
            try:
                passed, message = rule.check(df)
            except Exception as e:
                passed = False
                message = f"Rule execution error: {str(e)}"

            report.results.append(ValidationResult(
                rule_name=rule.name,
                passed=passed,
                message=message,
                severity=rule.severity
            ))

        return report

    def validate_or_raise(self, df: pd.DataFrame) -> ValidationReport:
        """
        Validate and raise exception if errors found.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate

        Returns
        -------
        ValidationReport
            Report (if no errors)

        Raises
        ------
        ValueError
            If any error-level validations fail
        """
        report = self.validate(df)
        if report.has_errors:
            raise ValueError(f"Validation failed:\n{report.format()}")
        return report

    def validate_schema(
        self,
        df: pd.DataFrame,
        schema: dict[str, type]
    ) -> ValidationReport:
        """
        Validate DataFrame against a schema.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        schema : dict
            Dictionary mapping column names to expected types

        Returns
        -------
        ValidationReport
            Validation results
        """
        report = ValidationReport()

        # Check for required columns
        for col, expected_type in schema.items():
            if col not in df.columns:
                report.results.append(ValidationResult(
                    rule_name=f'column_exists:{col}',
                    passed=False,
                    message=f"Required column '{col}' not found",
                    severity='error'
                ))
            else:
                # Check type
                actual_type = df[col].dtype
                if not np.issubdtype(actual_type, expected_type):
                    report.results.append(ValidationResult(
                        rule_name=f'column_type:{col}',
                        passed=False,
                        message=f"Column '{col}' has type {actual_type}, expected {expected_type}",
                        severity='warning'
                    ))
                else:
                    report.results.append(ValidationResult(
                        rule_name=f'column:{col}',
                        passed=True,
                        message=f"Column '{col}' present with correct type",
                        severity='info'
                    ))

        return report


# ============================================================
# BUILT-IN VALIDATORS
# ============================================================

def no_missing_values(columns: list[str], severity: str = 'error') -> ValidationRule:
    """
    Create a rule that checks for no missing values in specified columns.

    Parameters
    ----------
    columns : list
        Column names to check
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        missing = {}
        for col in columns:
            if col in df.columns:
                n_missing = df[col].isna().sum()
                if n_missing > 0:
                    missing[col] = int(n_missing)

        if missing:
            return False, f"Missing values found: {missing}"
        return True, f"No missing values in {columns}"

    return ValidationRule(
        name='no_missing_values',
        check=check,
        severity=severity,
        description=f"Check for no missing values in columns: {columns}"
    )


def unique_values(column: str, severity: str = 'error') -> ValidationRule:
    """
    Create a rule that checks for unique values in a column.

    Parameters
    ----------
    column : str
        Column name to check
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        if column not in df.columns:
            return False, f"Column '{column}' not found"

        n_total = len(df)
        n_unique = df[column].nunique()

        if n_total != n_unique:
            n_dups = n_total - n_unique
            return False, f"Column '{column}' has {n_dups} duplicate values ({n_unique} unique of {n_total})"
        return True, f"Column '{column}' has all unique values ({n_unique})"

    return ValidationRule(
        name=f'unique_values:{column}',
        check=check,
        severity=severity,
        description=f"Check that column '{column}' has unique values"
    )


def value_range(
    column: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    severity: str = 'warning'
) -> ValidationRule:
    """
    Create a rule that checks values are within a specified range.

    Parameters
    ----------
    column : str
        Column name to check
    min_val : float, optional
        Minimum allowed value
    max_val : float, optional
        Maximum allowed value
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        if column not in df.columns:
            return False, f"Column '{column}' not found"

        values = df[column].dropna()
        issues = []

        if min_val is not None:
            n_below = (values < min_val).sum()
            if n_below > 0:
                issues.append(f"{n_below} values below {min_val}")

        if max_val is not None:
            n_above = (values > max_val).sum()
            if n_above > 0:
                issues.append(f"{n_above} values above {max_val}")

        if issues:
            return False, f"Column '{column}': " + ", ".join(issues)

        range_str = f"[{min_val}, {max_val}]"
        return True, f"Column '{column}' values within {range_str}"

    return ValidationRule(
        name=f'value_range:{column}',
        check=check,
        severity=severity,
        description=f"Check that '{column}' values are in range [{min_val}, {max_val}]"
    )


def categorical_values(
    column: str,
    valid_values: set,
    severity: str = 'error'
) -> ValidationRule:
    """
    Create a rule that checks values are from a valid set.

    Parameters
    ----------
    column : str
        Column name to check
    valid_values : set
        Set of allowed values
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        if column not in df.columns:
            return False, f"Column '{column}' not found"

        actual_values = set(df[column].dropna().unique())
        invalid = actual_values - valid_values

        if invalid:
            return False, f"Column '{column}' has invalid values: {invalid}"
        return True, f"Column '{column}' values are valid"

    return ValidationRule(
        name=f'categorical_values:{column}',
        check=check,
        severity=severity,
        description=f"Check that '{column}' values are in {valid_values}"
    )


def date_range(
    column: str,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
    severity: str = 'warning'
) -> ValidationRule:
    """
    Create a rule that checks dates are within a specified range.

    Parameters
    ----------
    column : str
        Column name to check
    min_date : str, optional
        Minimum date (YYYY-MM-DD format)
    max_date : str, optional
        Maximum date (YYYY-MM-DD format)
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        if column not in df.columns:
            return False, f"Column '{column}' not found"

        dates = pd.to_datetime(df[column], errors='coerce')
        issues = []

        if min_date is not None:
            min_dt = pd.to_datetime(min_date)
            n_before = (dates < min_dt).sum()
            if n_before > 0:
                issues.append(f"{n_before} dates before {min_date}")

        if max_date is not None:
            max_dt = pd.to_datetime(max_date)
            n_after = (dates > max_dt).sum()
            if n_after > 0:
                issues.append(f"{n_after} dates after {max_date}")

        if issues:
            return False, f"Column '{column}': " + ", ".join(issues)

        return True, f"Column '{column}' dates within range"

    return ValidationRule(
        name=f'date_range:{column}',
        check=check,
        severity=severity,
        description=f"Check that '{column}' dates are in range [{min_date}, {max_date}]"
    )


def row_count(
    min_rows: Optional[int] = None,
    max_rows: Optional[int] = None,
    severity: str = 'error'
) -> ValidationRule:
    """
    Create a rule that checks the number of rows.

    Parameters
    ----------
    min_rows : int, optional
        Minimum required rows
    max_rows : int, optional
        Maximum allowed rows
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        n = len(df)
        issues = []

        if min_rows is not None and n < min_rows:
            issues.append(f"only {n} rows (minimum: {min_rows})")

        if max_rows is not None and n > max_rows:
            issues.append(f"{n} rows exceeds maximum ({max_rows})")

        if issues:
            return False, "Row count issue: " + ", ".join(issues)
        return True, f"Row count OK ({n} rows)"

    return ValidationRule(
        name='row_count',
        check=check,
        severity=severity,
        description=f"Check row count in range [{min_rows}, {max_rows}]"
    )


def no_duplicate_rows(
    columns: Optional[list[str]] = None,
    severity: str = 'error'
) -> ValidationRule:
    """
    Create a rule that checks for duplicate rows.

    Parameters
    ----------
    columns : list, optional
        Columns to check for duplicates. If None, checks all columns.
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    def check(df: pd.DataFrame) -> tuple[bool, str]:
        if columns:
            subset = [c for c in columns if c in df.columns]
            if not subset:
                return False, f"None of specified columns found: {columns}"
            dups = df.duplicated(subset=subset).sum()
            col_str = f" on {subset}"
        else:
            dups = df.duplicated().sum()
            col_str = ""

        if dups > 0:
            return False, f"Found {dups} duplicate rows{col_str}"
        return True, f"No duplicate rows{col_str}"

    return ValidationRule(
        name='no_duplicate_rows',
        check=check,
        severity=severity,
        description="Check for duplicate rows"
    )


def positive_values(column: str, severity: str = 'warning') -> ValidationRule:
    """
    Create a rule that checks for positive values.

    Parameters
    ----------
    column : str
        Column name to check
    severity : str
        'error', 'warning', or 'info'

    Returns
    -------
    ValidationRule
        The validation rule
    """
    return value_range(column, min_val=0, max_val=None, severity=severity)


# ============================================================
# SCHEMA HELPERS
# ============================================================

def create_schema(columns: dict[str, str]) -> dict[str, type]:
    """
    Create a schema dictionary from string type names.

    Parameters
    ----------
    columns : dict
        Dictionary mapping column names to type strings
        ('int', 'float', 'str', 'bool', 'datetime')

    Returns
    -------
    dict
        Dictionary mapping column names to numpy types
    """
    type_map = {
        'int': np.integer,
        'float': np.floating,
        'str': np.object_,
        'bool': np.bool_,
        'datetime': np.datetime64,
    }

    return {
        col: type_map.get(type_str, np.object_)
        for col, type_str in columns.items()
    }


# ============================================================
# MAIN (TEST)
# ============================================================

if __name__ == '__main__':
    # Test the validation framework
    import numpy as np

    # Create sample data
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10.5, 20.3, np.nan, 15.2, 25.1],
        'category': ['A', 'B', 'A', 'C', 'B'],
        'date': pd.date_range('2020-01-01', periods=5)
    })

    print("Sample data:")
    print(df)
    print()

    # Create validator
    validator = DataValidator()
    validator.add_rule(unique_values('id'))
    validator.add_rule(no_missing_values(['id', 'value'], severity='warning'))
    validator.add_rule(categorical_values('category', {'A', 'B', 'C'}))
    validator.add_rule(value_range('value', min_val=0, max_val=100))
    validator.add_rule(row_count(min_rows=3))

    # Run validation
    report = validator.validate(df)
    print(report.format(show_passed=True))

    print(f"\nHas errors: {report.has_errors}")
    print(f"Has warnings: {report.has_warnings}")
