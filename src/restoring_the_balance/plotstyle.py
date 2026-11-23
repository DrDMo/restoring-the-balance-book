"""Shared figure style so every chart in the book reads as one system."""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

PATHWAY_COLORS = {
    "vertical": "#2b6cb0",  # elections and parties
    "horizontal": "#c05621",  # courts and legislatures
    "diagonal": "#2f855a",  # media and civil society
}
PATHWAY_LABELS = {
    "vertical": "Vertical (elections)",
    "horizontal": "Horizontal (courts, legislature)",
    "diagonal": "Diagonal (media, civil society)",
}
# V-Dem e_regionpol_6C codes
REGION_LABELS = {
    1: "Eastern Europe & Central Asia",
    2: "Latin America & Caribbean",
    3: "Middle East & North Africa",
    4: "Sub-Saharan Africa",
    5: "Western Europe & North America",
    6: "Asia & Pacific",
}
NEUTRAL = "#4a5568"


def apply() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "font.family": "serif",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#e2e8f0",
            "grid.linewidth": 0.6,
            "legend.frameon": False,
        }
    )


def save(fig: plt.Figure, path_stem) -> None:
    """Save as PNG (for review) and PDF (for print)."""
    fig.savefig(f"{path_stem}.png")
    fig.savefig(f"{path_stem}.pdf")
    plt.close(fig)
