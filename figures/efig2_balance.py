# -*- coding: utf-8 -*-
"""eFigure 2. Propensity score matching balance for the encounter-density proxies.

Values transcribed from eTables 6, 7 and 8, which are the MatchIt summaries of
the frozen runs. Standardized mean differences use the treated-group standard
deviation, as MatchIt reports them; absolute values are plotted.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import DARK, INK, MM, PT_BODY, PT_HEAD, PT_SMALL, RULE, apply_style

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "submission_v25",
    "04_figures",
    "supplement",
)

AOU = [
    ("Survey date", 0.095, 0.015),
    ("Number of diagnoses", 0.410, 0.003),
    ("Length of EHR history", 0.041, 0.012),
]
MS = [
    ("Enrollment date", 0.241, 0.063),
    ("Number of diagnoses", 0.199, 0.012),
    ("Coverage span", 0.400, 0.045),
]

apply_style()
plt.rcParams.update(
    {
        "xtick.labelsize": PT_SMALL,
        "ytick.labelsize": PT_SMALL,
        "axes.labelsize": PT_BODY,
    }
)
fig, (ax, bx) = plt.subplots(
    2,
    1,
    figsize=(172 * MM, 92 * MM),
    sharex=True,
    gridspec_kw=dict(hspace=0.62, left=0.22, right=0.97, top=0.88, bottom=0.22),
)


def panel(a, rows, title_n):
    y = list(range(len(rows)))[::-1]
    for yi, (lab, pre, post) in zip(y, rows):
        a.plot(
            [pre, post],
            [yi, yi],
            color="0.80",
            lw=2.0,
            solid_capstyle="round",
            zorder=1,
        )
        a.plot([pre], [yi], marker="^", ms=6.5, color="#A6A6A6", zorder=3)
        a.plot([post], [yi], marker="o", ms=6.0, color=DARK, zorder=3)
    a.axvline(0.10, color=RULE, lw=1.0, ls=(0, (4, 3)), zorder=0)
    a.set_yticks(y)
    a.set_yticklabels([r[0] for r in rows])
    a.set_ylim(-0.7, len(rows) - 0.3)
    a.set_xlim(-0.012, 0.45)
    a.set_xticks([0, 0.1, 0.2, 0.3, 0.4])
    a.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4"])
    a.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        a.spines[s].set_visible(False)
    a.text(
        -0.28,
        1.06,
        title_n,
        transform=a.transAxes,
        fontsize=PT_HEAD,
        fontweight="bold",
        color=INK,
        va="bottom",
    )


panel(ax, AOU, "A   All of Us, COVID-19")
panel(bx, MS, "B   MarketScan")
bx.set_xlabel("Absolute standardized mean difference")

fig.legend(
    handles=[
        Line2D(
            [],
            [],
            color="#A6A6A6",
            marker="^",
            ms=6.5,
            lw=0,
            label="Before matching",
        ),
        Line2D([], [], color=DARK, marker="o", ms=6.0, lw=0, label="After matching"),
        Line2D([], [], color=RULE, lw=1.0, ls=(0, (4, 3)), label="|SMD| = 0.10"),
    ],
    loc="lower center",
    bbox_to_anchor=(0.55, 0.0),
    ncol=3,
    fontsize=PT_SMALL,
    columnspacing=2.4,
    handletextpad=0.6,
    frameon=False,
)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "eFigure2." + ext), dpi=400)
print("wrote eFigure2")
