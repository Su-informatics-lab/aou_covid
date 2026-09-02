# -*- coding: utf-8 -*-
"""Figure 5. Wave-varying social and racial associations.

Both panels come from single models carrying exposure-by-wave interaction
terms, so every matched stratum contributes.

Coefficients are transcribed from the frozen model outputs of the 2026-09-02
re-run; their provenance is in the round record. Run from the repository root:

    python3 figures/fig5_wave.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from jamia_forest import MM, NAVY, WAVE, apply_style, forest, save

OUT = sys.argv[1] if len(sys.argv) > 1 else "results/figures"
os.makedirs(OUT, exist_ok=True)

INC = [
    ("<$10,000", (1.361, 1.104, 1.678), (1.423, 0.731, 2.770), (1.636, 1.218, 2.198)),
    (
        "$10,000–24,999",
        (1.305, 1.061, 1.606),
        (1.265, 0.656, 2.439),
        (1.400, 1.062, 1.846),
    ),
    (
        "$25,000–34,999",
        (1.093, 0.850, 1.404),
        (1.595, 0.722, 3.526),
        (1.081, 0.773, 1.512),
    ),
    (
        "$100,000–149,999",
        (1.112, 0.833, 1.486),
        (1.403, 0.696, 2.830),
        (1.175, 0.859, 1.607),
    ),
    (
        "$150,000–199,999",
        (1.096, 0.732, 1.640),
        (1.692, 0.577, 4.962),
        (1.500, 1.002, 2.246),
    ),
    ("≥$200,000", (1.392, 0.963, 2.013), (1.363, 0.373, 4.981), (1.103, 0.756, 1.608)),
]
RACE = [
    ("Pre-Delta", (2.304, 2.011, 2.641)),
    ("Delta", (2.239, 1.774, 2.825)),
    ("Omicron", (1.784, 1.520, 2.093)),
]


apply_style()
fig, axes = plt.subplots(
    1, 2, figsize=(180 * MM, 78 * MM), gridspec_kw={"width_ratios": [1.65, 1]}
)
forest(
    axes[0],
    [(l, {"Pre-Delta": p, "Delta": d, "Omicron": o}) for l, p, d, o in INC],
    {"Pre-Delta": (WAVE[0], "o"), "Delta": (WAVE[1], "s"), "Omicron": (WAVE[2], "^")},
    (0.3, 6.0),
    [0.5, 1, 2, 4],
    "Adjusted odds ratio (95% CI), log scale",
    top_first=True,
)
axes[0].legend(
    handles=[
        plt.Line2D([], [], color=WAVE[i], marker=m, ms=3.4, lw=0.8, label=n)
        for i, (m, n) in enumerate(
            [("o", "Pre-Delta"), ("s", "Delta"), ("^", "Omicron")]
        )
    ],
    frameon=False,
    loc="lower right",
    fontsize=6,
)

forest(
    axes[1],
    [(l, {"r": v}) for l, v in RACE],
    {"r": (NAVY, "o")},
    (1.2, 3.4),
    [1.5, 2, 3],
    "Adjusted odds ratio (95% CI), log scale",
)
axes[1].annotate(
    "pre-Delta vs Omicron, P = 0.017\npre-Delta vs Delta, P = 0.83",
    xy=(0.02, 0.06),
    xycoords="axes fraction",
    fontsize=6,
    ha="left",
    va="bottom",
    color="0.25",
)
for ax, lab in zip(axes, "ab"):
    ax.text(
        -0.02,
        1.02,
        lab,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        ha="right",
        va="bottom",
    )
save(fig, os.path.join(OUT, "Figure5"))
print("  figure 5: %d income rows, %d wave rows" % (len(INC), len(RACE)))
