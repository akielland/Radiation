"""Shared utilities for plotting, constants, and helper functions."""

from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from math import radians, sin, cos, sqrt, atan2


# --- Paths ---

def project_root() -> Path:
    """Find project root by looking for .git or PROJECT_SPEC.md."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "PROJECT_SPEC.md").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent


def _figures_dir() -> Path:
    """Return path to figures directory."""
    return project_root() / "figures"


# --- Style configuration ---

STYLE_CONFIGURED = False


def configure_style() -> None:
    """Apply consistent plotting style. Called once at import time."""
    global STYLE_CONFIGURED
    if STYLE_CONFIGURED:
        return

    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams.update({
        "figure.figsize": (12, 6),
        "figure.dpi": 100,
        "savefig.dpi": 200,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.2,
    })
    STYLE_CONFIGURED = True


# Apply style on import
configure_style()


# --- Color constants ---

STATION_TYPE_COLORS = {
    "fixed": "#2196F3",
    "air_filter": "#FF9800",
    "mobile": "#9C27B0",
}

UPTIME_COLORS = {
    "reliable": "#4CAF50",
    "unstable": "#FFC107",
    "offline": "#F44336",
}


# --- Helper functions ---

def classify_uptime(pct: float) -> str:
    """Classify station uptime percentage into reliability category.

    Args:
        pct: Uptime as fraction (0.0 to 1.0).

    Returns:
        One of: 'reliable' (>95%), 'unstable' (50-95%), 'offline' (<50%)
    """
    if pct > 0.95:
        return "reliable"
    elif pct > 0.50:
        return "unstable"
    else:
        return "offline"


def save_figure(fig: matplotlib.figure.Figure, name: str, fmt: str = "png") -> Path:
    """Save figure to the figures/ directory.

    Args:
        fig: Matplotlib figure object.
        name: Filename without extension.
        fmt: File format (default: png).

    Returns:
        Path to saved file.
    """
    figures_dir = _figures_dir()
    figures_dir.mkdir(parents=True, exist_ok=True)
    filepath = figures_dir / f"{name}.{fmt}"
    fig.savefig(filepath)
    return filepath



def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Distance in km between two points. Args in (x, y) = (lon, lat) order."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))