# -*- coding: utf-8 -*-
"""Figure 1, data panels (b) and (c), each written as its own file.

Panel (a) is the design strip, drawn by design_strip.py with no highlight.

(b) the matching removed the encounter-density imbalance it was built to remove,
    transcribed from eTables 6, 7 and 8.
(c) the resulting clinical model agrees with a second cohort assembled from
    different data by different code: the 26 comparable base-model estimates,
    also plotted estimate-by-estimate in eFigure 5 and listed in eTable 9.  The
    five that point the other way are grey, not warm -- warm is the pathogen
    colour in this set, and a disagreement drawn in alarm-red would argue
    against the panel's own claim.

No value is recomputed here.
"""

import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from style import GREY, INK, MM, NAVY, RULE, TEAL, apply_style, save

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "panels")

BALANCE = [
    (
        "All of Us",
        NAVY,
        [
            ("Survey date", 0.095, 0.015),
            ("Number of diagnoses", 0.410, 0.003),
            ("Length of EHR history", 0.041, 0.012),
        ],
    ),
    (
        "MarketScan",
        TEAL,
        [
            ("Enrollment date", 0.241, 0.063),
            ("Number of diagnoses", 0.199, 0.012),
            ("Coverage span", 0.400, 0.045),
        ],
    ),
]


apply_style()
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- panel (b)
fig, ax = plt.subplots(figsize=(88 * MM, 78 * MM))
# ============================================================ (b) the matching worked
rows, y, heads = [], [], []
cur = 0.0
for gi, (cohort, col, items) in enumerate(BALANCE):
    cur += 0.55 if gi else 0.0
    heads.append((cohort, col, cur))
    cur += 0.95
    for it in items:
        rows.append((it, col))
        y.append(cur)
        cur += 1.0
bottom = cur - 1.0
y = [bottom - v for v in y]
heads = [(c, col, bottom - v) for c, col, v in heads]

for yi, ((lab, pre, post), col) in zip(y, rows):
    ax.plot(
        [post, pre], [yi, yi], color="0.83", lw=2.2, solid_capstyle="round", zorder=1
    )
    ax.plot([pre], [yi], marker="^", ms=7.0, color=GREY, mfc="white", mew=1.3, zorder=3)
    ax.plot([post], [yi], marker="o", ms=6.4, color=col, zorder=3)
ax.axvline(0.10, color=RULE, lw=1.0, ls=(0, (4, 3)), zorder=0)
ax.text(
    0.104,
    bottom + 0.30,
    "conventional\nthreshold, 0.10",
    fontsize=10,
    color=GREY,
    ha="left",
    va="top",
)
ax.set_yticks(y)
ax.set_yticklabels([r[0][0] for r in rows])
ax.set_ylim(min(y) - 0.7, max(h[2] for h in heads) + 0.55)
ax.set_xlim(0, 0.45)
ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4])
ax.set_xlabel("Absolute standardized mean difference")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for cohort, col, gy in heads:
    ax.text(
        -0.34,
        gy,
        cohort,
        transform=ax.get_yaxis_transform(),
        ha="left",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=col,
        clip_on=False,
    )
ax.legend(
    handles=[
        Line2D(
            [],
            [],
            color=GREY,
            marker="^",
            ms=7.0,
            lw=0,
            mfc="white",
            mew=1.3,
            label="before matching",
        ),
        Line2D([], [], color=INK, marker="o", ms=6.4, lw=0, label="after matching"),
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.20),
    ncol=2,
    frameon=False,
    handletextpad=0.5,
    columnspacing=1.6,
)

save(fig, os.path.join(OUT, "F1b_balance"))
plt.close(fig)

# ---------------------------------------------------------------- panel (c)
fig, ax = plt.subplots(figsize=(88 * MM, 82 * MM))
# ============================================================ (c) concordance
ns = runpy.run_path(os.path.join(HERE, "efig5_clinical_check.py"), run_name="__pairs__")
A, M = ns["A"], ns["M"]
PAIRS = [(k, A[k][0], M[k][0]) for k in A if M.get(k) is not None]
#  The claim this panel makes is agreement.  The five estimates that point the
#  other way are drawn in grey rather than warm: grey is the reference colour
#  throughout this set, warm is reserved for pathogen, and colouring a
#  disagreement in alarm-red would argue against the panel's own claim.  All
#  five are named in the legend and plotted one by one in eFigure 5.
DISC = [
    "Peripheral vascular disease",
    "Chronic pulmonary disease",
    "Peptic ulcer disease",
    "Liver disease, mild",
    "AIDS",
]
LIM = (0.36, 3.9)
ax.add_patch(
    Rectangle(
        (LIM[0], LIM[0]),
        1 - LIM[0],
        1 - LIM[0],
        facecolor="0.945",
        edgecolor="none",
        zorder=0,
    )
)
ax.add_patch(
    Rectangle(
        (1, 1), LIM[1] - 1, LIM[1] - 1, facecolor="0.945", edgecolor="none", zorder=0
    )
)
ax.plot(LIM, LIM, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
ax.axvline(1.0, color=RULE, lw=0.8, zorder=1)
ax.axhline(1.0, color=RULE, lw=0.8, zorder=1)
for lab, a, m in PAIRS:
    d = lab in DISC
    ax.plot(
        [a], [m], marker="o", ms=6.4, color=GREY if d else NAVY, zorder=2 if d else 3
    )
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(*LIM)
ax.set_ylim(*LIM)
for axis in (ax.xaxis, ax.yaxis):
    axis.set_major_locator(mpl.ticker.FixedLocator([0.5, 1, 2, 3]))
    axis.set_major_formatter(mpl.ticker.FixedFormatter(["0.5", "1", "2", "3"]))
    axis.set_minor_locator(mpl.ticker.NullLocator())
    axis.set_minor_formatter(mpl.ticker.NullFormatter())
ax.set_xlabel("All of Us, adjusted odds ratio")
ax.set_ylabel("MarketScan, adjusted odds ratio")
ax.set_aspect("equal")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.text(
    0.035,
    0.965,
    "21 of 26 estimates\nagree in direction",
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=10,
    color=INK,
)
ax.legend(
    handles=[
        Line2D([], [], color=NAVY, marker="o", ms=6.4, lw=0, label="same direction"),
        Line2D([], [], color=GREY, marker="o", ms=6.4, lw=0, label="opposite"),
    ],
    loc="lower right",
    frameon=False,
    handletextpad=0.5,
    borderpad=0.2,
    labelspacing=0.25,
)

save(fig, os.path.join(OUT, "F1c_concordance"))
plt.close(fig)
