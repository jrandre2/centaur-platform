#!/usr/bin/env python3
"""
Figure styling configuration for manuscript.

This module sets matplotlib defaults to match the LaTeX article document style
used by Quarto. Import this module at the start of any script that generates
figures for the manuscript.

Usage
-----
from src.utils.figure_style import apply_style, set_profile, save_figure
apply_style()

# Use different profiles
set_profile('presentation')  # For slides
set_profile('publication')   # For journal submission (default)
set_profile('draft')         # For quick iteration

# Use journal-specific presets
from src.utils.figure_style import get_journal_preset
preset = get_journal_preset('jeem')
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, Literal
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from contextlib import contextmanager

# ============================================================
# STYLE PROFILES
# ============================================================

STYLE_PROFILES = {
    'publication': {
        'font.family': 'serif',
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.spines.top': False,
        'axes.spines.right': False,
    },
    'presentation': {
        'font.family': 'sans-serif',
        'font.size': 14,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.dpi': 100,
        'savefig.dpi': 150,
        'axes.grid': True,
        'grid.alpha': 0.4,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'lines.linewidth': 2.5,
        'axes.linewidth': 1.5,
    },
    'draft': {
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 72,
        'savefig.dpi': 100,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.spines.top': True,
        'axes.spines.right': True,
    },
}

# ============================================================
# JOURNAL PRESETS
# ============================================================

JOURNAL_PRESETS = {
    'jeem': {
        'figwidth': 6.5,
        'figheight': 4.5,
        'fontsize': 10,
        'dpi': 300,
        'font_family': 'serif',
        'single_column_width': 3.25,
        'double_column_width': 6.5,
    },
    'aer': {
        'figwidth': 6.0,
        'figheight': 4.0,
        'fontsize': 9,
        'dpi': 300,
        'font_family': 'serif',
        'single_column_width': 3.0,
        'double_column_width': 6.0,
    },
    'nhaz': {
        'figwidth': 174 / 25.4,  # 174mm in inches
        'figheight': 120 / 25.4,
        'fontsize': 10,
        'dpi': 300,
        'font_family': 'serif',
        'single_column_width': 84 / 25.4,
        'double_column_width': 174 / 25.4,
        'max_height': 234 / 25.4,
    },
    'default': {
        'figwidth': 6.5,
        'figheight': 4.5,
        'fontsize': 10,
        'dpi': 300,
        'font_family': 'serif',
        'single_column_width': 3.25,
        'double_column_width': 6.5,
    },
}

# ============================================================
# COLOR PALETTES
# ============================================================

COLOR_PALETTES = {
    'default': [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
    ],
    'colorblind': [
        '#0072B2',  # Blue
        '#E69F00',  # Orange
        '#009E73',  # Green
        '#CC79A7',  # Pink
        '#F0E442',  # Yellow
        '#56B4E9',  # Light blue
        '#D55E00',  # Vermillion
        '#000000',  # Black
    ],
    'grayscale': [
        '#000000',  # Black
        '#404040',  # Dark gray
        '#808080',  # Medium gray
        '#a0a0a0',  # Light gray
        '#c0c0c0',  # Lighter gray
        '#e0e0e0',  # Very light gray
    ],
    'accent': [
        '#e41a1c',  # Red
        '#377eb8',  # Blue
        '#4daf4a',  # Green
        '#984ea3',  # Purple
        '#ff7f00',  # Orange
    ],
    'treatment': [
        '#2166ac',  # Treated (blue)
        '#b2182b',  # Control (red)
        '#4dac26',  # Neutral (green)
    ],
}

# ============================================================
# DEFAULT PARAMETERS (for backward compatibility)
# ============================================================

FONT_FAMILY = 'serif'
FONT_SIZE = 10
TITLE_SIZE = 11
LABEL_SIZE = 10
TICK_SIZE = 9
LEGEND_SIZE = 9

FIG_WIDTH_SINGLE = 6.5
FIG_HEIGHT_SINGLE = 4.5
FIG_WIDTH_DOUBLE = 6.5
FIG_HEIGHT_DOUBLE = 8.0

DPI = 300

# Current active profile
_current_profile = 'publication'
_current_journal = None


# ============================================================
# CORE FUNCTIONS
# ============================================================

def apply_style(profile: str = 'publication') -> None:
    """
    Apply consistent figure styling for manuscript figures.

    Parameters
    ----------
    profile : str
        Style profile to use. Options: 'publication', 'presentation', 'draft'
    """
    global _current_profile
    _current_profile = profile

    if profile not in STYLE_PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Choose from {list(STYLE_PROFILES.keys())}")

    style = STYLE_PROFILES[profile]
    plt.rcParams.update(style)

    # Common settings for all profiles
    plt.rcParams.update({
        'legend.framealpha': 0.9,
        'figure.constrained_layout.use': True,
        'axes.xmargin': 0.0,
        'axes.autolimit_mode': 'data',
    })


def set_profile(profile: str) -> None:
    """Set the active style profile."""
    apply_style(profile)


def get_journal_preset(journal: str) -> dict:
    """
    Get figure parameters for a specific journal.

    Parameters
    ----------
    journal : str
        Journal abbreviation (e.g., 'jeem', 'aer', 'nhaz')

    Returns
    -------
    dict
        Dictionary with figwidth, figheight, fontsize, dpi, etc.
    """
    if journal not in JOURNAL_PRESETS:
        print(f"Warning: Unknown journal '{journal}', using default preset")
        return JOURNAL_PRESETS['default']
    return JOURNAL_PRESETS[journal]


def apply_journal_preset(journal: str) -> None:
    """
    Apply journal-specific figure settings.

    Parameters
    ----------
    journal : str
        Journal abbreviation
    """
    global _current_journal
    _current_journal = journal

    preset = get_journal_preset(journal)
    plt.rcParams.update({
        'figure.figsize': (preset['figwidth'], preset['figheight']),
        'font.size': preset['fontsize'],
        'font.family': preset['font_family'],
        'savefig.dpi': preset['dpi'],
    })


def get_color_palette(name: str = 'default', n: Optional[int] = None) -> list:
    """
    Get a color palette.

    Parameters
    ----------
    name : str
        Palette name: 'default', 'colorblind', 'grayscale', 'accent', 'treatment'
    n : int, optional
        Number of colors to return. If None, returns all colors in palette.

    Returns
    -------
    list
        List of color hex codes
    """
    if name not in COLOR_PALETTES:
        raise ValueError(f"Unknown palette: {name}. Choose from {list(COLOR_PALETTES.keys())}")

    colors = COLOR_PALETTES[name]
    if n is None:
        return colors
    if n > len(colors):
        # Cycle colors if more requested than available
        return [colors[i % len(colors)] for i in range(n)]
    return colors[:n]


# ============================================================
# FIGURE CREATION HELPERS
# ============================================================

def get_figure_single(journal: Optional[str] = None):
    """
    Create a single-panel figure with standard dimensions.

    Parameters
    ----------
    journal : str, optional
        If provided, use journal-specific dimensions
    """
    apply_style(_current_profile)
    if journal:
        preset = get_journal_preset(journal)
        return plt.figure(figsize=(preset['figwidth'], preset['figheight']))
    return plt.figure(figsize=(FIG_WIDTH_SINGLE, FIG_HEIGHT_SINGLE))


def get_figure_double(journal: Optional[str] = None):
    """
    Create a two-panel figure with standard dimensions.

    Parameters
    ----------
    journal : str, optional
        If provided, use journal-specific dimensions
    """
    apply_style(_current_profile)
    if journal:
        preset = get_journal_preset(journal)
        return plt.figure(figsize=(preset['figwidth'], preset['figheight'] * 1.8))
    return plt.figure(figsize=(FIG_WIDTH_DOUBLE, FIG_HEIGHT_DOUBLE))


def get_figure_grid(nrows: int, ncols: int, journal: Optional[str] = None, **kwargs):
    """
    Create a figure with a grid of subplots.

    Parameters
    ----------
    nrows : int
        Number of rows
    ncols : int
        Number of columns
    journal : str, optional
        Journal for sizing
    **kwargs
        Additional arguments passed to plt.subplots

    Returns
    -------
    tuple
        (fig, axes) tuple from plt.subplots
    """
    apply_style(_current_profile)
    if journal:
        preset = get_journal_preset(journal)
        figsize = (preset['figwidth'], preset['figheight'] * nrows / 1.5)
    else:
        figsize = (FIG_WIDTH_SINGLE, FIG_HEIGHT_SINGLE * nrows / 1.5)

    return plt.subplots(nrows, ncols, figsize=figsize, **kwargs)


# ============================================================
# ANNOTATION HELPERS
# ============================================================

def annotate_panel(
    ax,
    label: str,
    loc: str = 'upper left',
    fontsize: Optional[int] = None,
    fontweight: str = 'bold'
) -> None:
    """
    Add a panel label (a), (b), etc. to an axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to annotate
    label : str
        The label text, e.g., '(a)' or 'A'
    loc : str
        Location: 'upper left', 'upper right', 'lower left', 'lower right'
    fontsize : int, optional
        Font size for the label
    fontweight : str
        Font weight
    """
    if fontsize is None:
        fontsize = plt.rcParams.get('font.size', 10) + 2

    # Position mapping
    positions = {
        'upper left': (0.02, 0.98),
        'upper right': (0.98, 0.98),
        'lower left': (0.02, 0.02),
        'lower right': (0.98, 0.02),
    }

    if loc not in positions:
        raise ValueError(f"Unknown location: {loc}")

    x, y = positions[loc]
    ha = 'left' if 'left' in loc else 'right'
    va = 'top' if 'upper' in loc else 'bottom'

    ax.text(
        x, y, label,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight=fontweight,
        ha=ha, va=va
    )


def add_treatment_line(
    ax,
    x: float = 0,
    label: str = 'Treatment',
    color: str = 'black',
    linestyle: str = '--',
    alpha: float = 0.7
) -> None:
    """
    Add a vertical treatment line to a plot.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes
    x : float
        X-coordinate for the line
    label : str
        Label for the line
    color : str
        Line color
    linestyle : str
        Line style
    alpha : float
        Transparency
    """
    ax.axvline(x, color=color, linestyle=linestyle, alpha=alpha, label=label)


# ============================================================
# SAVING HELPERS
# ============================================================

def save_figure(
    fig,
    path: Union[str, Path],
    formats: list = None,
    dpi: Optional[int] = None,
    tight: bool = True,
    transparent: bool = False
) -> list:
    """
    Save a figure in multiple formats.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save
    path : str or Path
        Base path (without extension) or full path with extension
    formats : list, optional
        List of formats to save. Default: ['png', 'pdf']
    dpi : int, optional
        Resolution. If None, uses current profile setting.
    tight : bool
        Use tight bounding box
    transparent : bool
        Transparent background

    Returns
    -------
    list
        List of saved file paths
    """
    if formats is None:
        formats = ['png', 'pdf']

    if dpi is None:
        dpi = plt.rcParams.get('savefig.dpi', DPI)

    path = Path(path)

    # If path has an extension, treat it as a single format
    if path.suffix:
        formats = [path.suffix.lstrip('.')]
        path = path.with_suffix('')

    saved_paths = []
    for fmt in formats:
        save_path = path.with_suffix(f'.{fmt}')
        save_path.parent.mkdir(parents=True, exist_ok=True)

        fig.savefig(
            save_path,
            dpi=dpi,
            bbox_inches='tight' if tight else None,
            transparent=transparent,
            format=fmt
        )
        saved_paths.append(save_path)

    return saved_paths


@contextmanager
def temporary_style(profile: str = 'draft'):
    """
    Context manager for temporarily changing style.

    Usage
    -----
    with temporary_style('presentation'):
        # Figures created here use presentation style
        fig, ax = plt.subplots()
        ...
    # Returns to previous style after context
    """
    global _current_profile
    old_profile = _current_profile
    old_params = dict(plt.rcParams)

    try:
        apply_style(profile)
        yield
    finally:
        _current_profile = old_profile
        plt.rcParams.update(old_params)


# ============================================================
# MAIN (TEST)
# ============================================================

if __name__ == '__main__':
    # Test the style
    apply_style()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9], 'o-', label='Test data')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_title('Test Figure with Manuscript Style')
    ax.legend()
    plt.savefig('test_style.png')
    print('Saved test_style.png')

    # Test color palettes
    print("\nAvailable palettes:", list(COLOR_PALETTES.keys()))
    print("Colorblind palette:", get_color_palette('colorblind', 5))

    # Test journal presets
    print("\nJournal presets:")
    for journal in JOURNAL_PRESETS:
        print(f"  {journal}: {JOURNAL_PRESETS[journal]}")
