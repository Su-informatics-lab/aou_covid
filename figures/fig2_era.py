# -*- coding: utf-8 -*-
"""Figure 2. Test 3. What changed across pandemic eras, and what did not.

Income rows: eTable 12 (within-wave models carrying that domain alone).
Medicaid row: eTable 11c, joint column (within-wave models carrying all six).
Black race: eTable 11b and the v19 Figure 5b (within-wave base models).
Omnibus interaction tests come from the corresponding pooled models and are
printed, not plotted.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import ERA, INK, MM, RULE, apply_style, log_axis, panel_labels, save, sig

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "figures"
)
WAVES = ("Pre-Delta", "Delta", "Omicron")
MK = ("o", "s", "^")

GROUPS = [
    (
        "Income",
        "chi-square 19.32, 14 df,  P = 0.15",
        "holds across eras",
        False,
        [
            (
                "Below $10,000",
                (1.361, 1.104, 1.678),
                (1.423, 0.731, 2.770),
                (1.636, 1.218, 2.198),
            ),
            (
                "$10,000–24,999",
                (1.305, 1.061, 1.606),
                (1.265, 0.656, 2.439),
                (1.400, 1.062, 1.846),
            ),
        ],
    ),
    (
        "Insurance",
        "chi-square 25.50, 8 df,  P = 0.001",
        "varies across eras",
        True,
        [
            (
                "Medicaid",
                (1.518, 1.217, 1.894),
                (0.875, 0.411, 1.864),
                (0.987, 0.729, 1.337),
            ),
        ],
    ),
    (
        "Race",
        "chi-square 12.78, 6 df,  P = 0.047",
        "narrows by Omicron",
        True,
        [
            (
                "Black race",
                (2.310, 2.030, 2.628),
                (2.245, 1.812, 2.781),
                (1.794, 1.541, 2.089),
            ),
        ],
    ),
]

apply_style()
fig, ax = plt.subplots(figsize=(180 * MM, 84 * MM))

y, rows, heads = [], [], []
cur = 0.0
for gi, (gname, ptxt, verdict, flag, items) in enumerate(GROUPS):
    cur += 0.5 if gi else 0.7
    heads.append((gname, ptxt, verdict, flag, cur))
    cur += 1.0
    for it in items:
        rows.append(it)
        y.append(cur)
        cur += 1.35
bottom = cur - 1.35
y = [bottom - v for v in y]
heads = [(g, p, v, f, bottom - c) for g, p, v, f, c in heads]

XLIM = (0.38, 3.4)
OFF = (0.30, 0.0, -0.30)
for yi, item in zip(y, rows):
    lab = item[0]
    for k in range(3):
        a, lo, hi = item[1 + k]
        col = ERA[k]
        yy = yi + OFF[k]
        ax.plot([lo, hi], [yy, yy], color=col, lw=1.5, solid_capstyle="butt", zorder=2)
        ax.plot(
            [a],
            [yy],
            marker=MK[k],
            ms=6.2,
            color=col,
            zorder=3,
            mfc=col if sig(lo, hi) else "white",
            mew=1.2,
        )

log_axis(ax, XLIM, [0.5, 1, 1.5, 2, 3], "Adjusted odds ratio (95% CI), log scale")
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in rows])
ax.set_ylim(min(y) - 0.75, max(h[4] for h in heads) + 0.85)

for gname, ptxt, verdict, flag, gy in heads:
    ax.text(
        -0.185,
        gy,
        gname,
        transform=ax.get_yaxis_transform(),
        ha="left",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )
    ax.plot(
        [0.0, 1.0],
        [gy, gy],
        transform=ax.get_yaxis_transform(),
        color=RULE,
        lw=0.7,
        zorder=0,
        clip_on=False,
    )
    ax.text(
        1.0,
        gy,
        "  " + ptxt,
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=9.5,
        color="0.35",
        clip_on=False,
    )

ax.legend(
    handles=[
        Line2D([], [], color=ERA[k], marker=MK[k], ms=6.2, lw=1.5, label=WAVES[k])
        for k in range(3)
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=3,
    columnspacing=2.4,
    handletextpad=0.5,
    title=None,
)
panel_labels([ax])
save(fig, os.path.join(OUT, "Figure2"))
print("  rows:", len(rows))
