# -*- coding: utf-8 -*-
"""Figure 1. Test 1. Under mutual adjustment, employment and income outrank
insurance.

The grey connector is the point of the figure: its length is what mutual
adjustment costs each estimate. Values transcribed from figures/fig4_sdoh_forest.py
(frozen 2026-09-02 re-run) and printed in Table 3.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import (
    INK,
    MM,
    NAVY,
    RULE,
    TEAL,
    apply_style,
    log_axis,
    panel_labels,
    save,
    sig,
)

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "figures"
)

#  label, domain-specific (aor, lo, hi), joint (aor, lo, hi)
GROUPS = [
    (
        "Income",
        [
            ("<$10,000", (1.505, 1.326, 1.708), (1.215, 1.049, 1.406)),
            ("$10,000–24,999", (1.409, 1.244, 1.596), (1.206, 1.054, 1.381)),
            ("$25,000–34,999", (1.176, 1.012, 1.367), (1.099, 0.942, 1.283)),
            ("$100,000–149,999", (1.170, 1.002, 1.368), (1.216, 1.038, 1.424)),
            ("$150,000–199,999", (1.206, 0.971, 1.498), (1.264, 1.014, 1.576)),
            ("≥$200,000", (1.088, 0.887, 1.336), (1.153, 0.935, 1.422)),
        ],
    ),
    (
        "Employment",
        [
            ("Unemployed", (1.547, 1.398, 1.711), (1.342, 1.192, 1.511)),
            ("Student", (1.478, 1.140, 1.917), (1.368, 1.050, 1.782)),
            ("Retired or other", (1.398, 1.254, 1.557), (1.281, 1.140, 1.439)),
        ],
    ),
    (
        "Insurance",
        [
            ("Medicaid", (1.536, 1.380, 1.710), (1.188, 1.043, 1.354)),
            ("Medicare", (1.152, 1.014, 1.309), (0.978, 0.852, 1.123)),
            ("Other or none", (1.328, 1.146, 1.538), (1.102, 0.941, 1.291)),
        ],
    ),
    (
        "Housing",
        [
            ("Renting", (1.282, 1.175, 1.400), (1.163, 1.055, 1.281)),
            ("Other arrangement", (1.129, 0.980, 1.300), (0.979, 0.841, 1.139)),
            ("Housing instability", (1.002, 0.908, 1.105), (0.907, 0.817, 1.005)),
        ],
    ),
    (
        "Education",
        [
            ("Below GED", (1.290, 1.130, 1.474), (1.057, 0.916, 1.219)),
            ("GED or some college", (1.107, 1.015, 1.206), (1.008, 0.918, 1.107)),
        ],
    ),
]

apply_style()
fig, ax = plt.subplots(figsize=(180 * MM, 158 * MM))

y, rows, headers = [], [], []
cur = 0.0
for gi, (gname, items) in enumerate(GROUPS):
    cur += 1.7 if gi else 0.8
    headers.append((gname, cur))
    cur += 1.0
    for it in items:
        rows.append(it)
        y.append(cur)
        cur += 1.0
bottom = cur - 1.0
y = [bottom - v for v in y]
headers = [(g, bottom - v) for g, v in headers]

XLIM = (0.74, 2.35)
OFF = 0.20
# faint row bands so each label is unambiguously tied to its pair
for k, yi in enumerate(y):
    if k % 2 == 0:
        ax.axhspan(yi - 0.5, yi + 0.5, color=NAVY, alpha=0.045, lw=0, zorder=0)
for yi, (lab, dom, jnt) in zip(y, rows):
    ax.plot(
        [dom[0], jnt[0]],
        [yi + OFF, yi - OFF],
        color="0.78",
        lw=2.2,
        solid_capstyle="round",
        zorder=1.5,
    )
    for v, col, mk, off in ((dom, TEAL, "o", OFF), (jnt, NAVY, "s", -OFF)):
        a, lo, hi = v
        ax.plot(
            [lo, hi],
            [yi + off, yi + off],
            color=col,
            lw=1.4,
            solid_capstyle="butt",
            zorder=2,
        )
        ax.plot(
            [a],
            [yi + off],
            marker=mk,
            ms=5.8,
            color=col,
            zorder=3,
            mfc=col if sig(lo, hi) else "white",
            mew=1.2,
        )

log_axis(ax, XLIM, [0.8, 1, 1.25, 1.5, 2], "Adjusted odds ratio (95% CI), log scale")
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in rows])
ax.set_ylim(min(y) - 1.0, max(h[1] for h in headers) + 0.9)

for gname, gy in headers:
    ax.text(
        -0.245,
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

ax.legend(
    handles=[
        Line2D(
            [],
            [],
            color=TEAL,
            marker="o",
            ms=5.8,
            lw=1.4,
            label="Domain-specific model (that domain alone)",
        ),
        Line2D(
            [],
            [],
            color=NAVY,
            marker="s",
            ms=5.8,
            lw=1.4,
            label="Joint model (all five domains)",
        ),
        Line2D([], [], color="0.78", lw=2.2, label="Change under mutual adjustment"),
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.075),
    ncol=3,
    columnspacing=1.8,
    handletextpad=0.5,
)
panel_labels([ax])
save(fig, os.path.join(OUT, "Figure1"))
print("  rows:", len(rows))
