# -*- coding: utf-8 -*-
"""eFigure 3. Timing of qualifying visits relative to the COVID-19 index date.

Counts re-extracted from visit_occurrence for the 3,997 matched cases, over the
five visit concepts the hospitalization phenotype counts (9201, 32037, 262,
8717, 9203). Curated Data Repository version 9.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from style import GREY, MM, NAVY, RULE, apply_style, save

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "figures"
)

N = {
    -30: 86,
    -29: 96,
    -28: 103,
    -27: 89,
    -26: 82,
    -25: 105,
    -24: 116,
    -23: 173,
    -22: 140,
    -21: 124,
    -20: 115,
    -19: 116,
    -18: 165,
    -17: 149,
    -16: 119,
    -15: 134,
    -14: 128,
    -13: 98,
    -12: 123,
    -11: 117,
    -10: 72,
    -9: 104,
    -8: 100,
    -7: 85,
    -6: 110,
    -5: 147,
    -4: 131,
    -3: 189,
    -2: 251,
    -1: 570,
    0: 5582,
    1: 1064,
    2: 736,
    3: 672,
    4: 592,
    5: 543,
    6: 464,
    7: 530,
    8: 430,
    9: 418,
    10: 386,
    11: 379,
    12: 429,
    13: 319,
    14: 327,
    15: 292,
    16: 242,
    17: 247,
    18: 257,
    19: 193,
    20: 219,
    21: 209,
    22: 199,
    23: 245,
    24: 209,
    25: 165,
    26: 178,
    27: 153,
    28: 154,
    29: 136,
    30: 132,
}

apply_style()
fig, ax = plt.subplots(figsize=(196 * MM, 76 * MM))
ax.axvspan(-0.5, 14.5, color="0.90", zorder=0)
xs = sorted(N)
cols = [NAVY if 0 <= x <= 14 else GREY for x in xs]
ax.bar(xs, [N[x] for x in xs], width=0.85, color=cols, zorder=2)
ax.set_xlim(-30.8, 30.8)
ax.set_xticks([-30, -20, -10, 0, 14, 20, 30])
ax.set_xlabel("Days from the COVID-19 index date")
ax.set_ylabel("Qualifying visits")
ax.set_ylim(0, 6000)
ax.set_yticks([0, 1000, 2000, 3000, 4000, 5000])
ax.axvline(0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(
    handles=[
        Patch(facecolor=NAVY, label="Counted by the phenotype (days 0-14)"),
        Patch(facecolor=GREY, label="Not counted"),
    ],
    loc="upper right",
    frameon=False,
    handlelength=1.2,
)
save(fig, os.path.join(OUT, "eFigure3"))
