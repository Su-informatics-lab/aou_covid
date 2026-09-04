# -*- coding: utf-8 -*-
"""Figure 2. Test 2. What the six social domains account for in the
Black-race association.

Values transcribed from eTable 11a. Single-domain percentages are competing,
not sequential, additions and are not additive. The three rows of panel (a)
are an ordered analytic sequence, so they carry an ordered cool ramp.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from style import (
    GREY,
    INK,
    MM,
    NAVY,
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
MID = "#3E6E97"

SEQ = [
    ("Base model, no exposures", (2.387, 2.175, 2.619), TEAL, "o"),
    ("Adding income alone", (2.160, 1.960, 2.380), MID, "D"),
    ("Adding all five domains", (2.100, 1.900, 2.320), NAVY, "s"),
]

DECOMP = [
    ("Income", 11.7),
    ("Housing (ownership)", 8.7),
    ("Insurance", 6.2),
    ("Education", 4.8),
    ("Employment", 3.8),
    ("Housing (stability)", 0.1),
]
JOINT_PCT = 14.7

apply_style()
fig, (ax, bx) = plt.subplots(
    1,
    2,
    figsize=(180 * MM, 84 * MM),
    gridspec_kw={"width_ratios": [1.0, 1.0], "wspace": 0.62},
)

# ── panel a ──
ys = [2, 1, 0]
ax.plot(
    [v[0] for _, v, _, _ in SEQ],
    ys,
    color="0.78",
    lw=2.4,
    solid_capstyle="round",
    zorder=1.5,
)
for yi, (lab, v, col, mk) in zip(ys, SEQ):
    a, lo, hi = v
    ax.plot([lo, hi], [yi, yi], color=col, lw=1.6, solid_capstyle="butt", zorder=2)
    ax.plot(
        [a],
        [yi],
        marker=mk,
        ms=7.0,
        color=col,
        zorder=3,
        mfc=col if sig(lo, hi) else "white",
        mew=1.2,
    )
    ax.text(
        a,
        yi + 0.18,
        "%.2f" % a,
        ha="center",
        va="bottom",
        fontsize=10,
        color=col,
        fontweight="bold",
    )

log_axis(ax, (0.92, 3.3), [1, 1.5, 2, 3], "Black-race adjusted odds ratio (95% CI)")
ax.set_yticks(ys)
ax.set_yticklabels([s[0] for s in SEQ])
ax.set_ylim(-0.55, 2.7)

# ── panel b ──
lab = [d for d, _ in DECOMP][::-1]
val = [v for _, v in DECOMP][::-1]
yb = list(range(len(lab)))
import matplotlib.colors as mc

_top = max(val)
_cols = [mc.to_rgba(NAVY, 1.0 if v == _top else 0.52) for v in val]
bx.barh(yb, val, height=0.62, color=_cols, zorder=2)
bx.axvline(JOINT_PCT, color=GREY, lw=1.2, ls=(0, (4, 3)), zorder=1)
bx.text(
    JOINT_PCT - 0.45,
    0.62,
    "all five domains\njointly, 14.7%",
    fontsize=9.5,
    color="0.35",
    va="center",
    ha="right",
    linespacing=1.5,
)
for yi, v in zip(yb, val):
    bx.text(v + 0.3, yi, "%.1f" % v, va="center", ha="left", fontsize=10, color=INK)
bx.set_yticks(yb)
bx.set_yticklabels(lab)
bx.set_ylim(-0.7, len(lab) - 0.15)
bx.set_xlim(0, 17.5)
bx.set_xticks([0, 5, 10, 15])
bx.set_xlabel("Percentage-point attenuation")
bx.tick_params(axis="y", length=0)
for s in ("top", "right", "left"):
    bx.spines[s].set_visible(False)

panel_labels([ax, bx], alpha=1.0)
save(fig, os.path.join(OUT, "Figure2"))
