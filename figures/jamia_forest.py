# -*- coding: utf-8 -*-
"""Shared style and forest-plot helper for Figures 3-5.

Journal conventions applied here: 180 mm double-column width, 7 pt sans-serif
body type, 0.5-1 pt rules, no gridlines, type 42 fonts so the production team
can still edit the text, and the NPG palette (navy / teal / coral), which is
colourblind-safe at the counts used here.

Marker fill carries significance: filled when the interval excludes 1, open
when it does not, so the reader does not have to squint at the whiskers.
"""

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

MM = 1 / 25.4
NAVY, TEAL, CORAL = "#3C5488", "#00A087", "#E64B35"
WAVE = (CORAL, "#4DBBD5", TEAL)  # pre-Delta, Delta, Omicron


def apply_style():
    r = mpl.rcParams
    r["pdf.fonttype"] = r["ps.fonttype"] = 42
    r["svg.fonttype"] = "none"
    r["font.family"] = "sans-serif"
    r["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
    r["font.size"] = 7
    r["axes.labelsize"] = r["axes.titlesize"] = r["figure.titlesize"] = 7
    r["xtick.labelsize"] = r["ytick.labelsize"] = r["legend.fontsize"] = 6
    r["mathtext.default"] = "regular"
    r["axes.linewidth"] = 0.5
    for ax_ in ("xtick", "ytick"):
        r[f"{ax_}.major.width"] = 0.5
        r[f"{ax_}.major.size"] = 3
        r[f"{ax_}.direction"] = "out"
    r["lines.linewidth"] = 1.0
    r["lines.markersize"] = 4
    r["lines.markeredgewidth"] = 0.5
    r["legend.frameon"] = False
    r["legend.borderpad"] = 0.3
    r["legend.handlelength"] = 1.4
    r["legend.labelspacing"] = 0.3
    r["axes.grid"] = False
    r["axes.spines.top"] = r["axes.spines.right"] = False
    r["figure.facecolor"] = r["savefig.facecolor"] = "white"


def sig(lo, hi):
    return lo > 1 or hi < 1


def forest(ax, rows, series, xlim, xticks, xlabel, top_first=False, connect=False):
    """rows: [(label, {series_name: (aor, lo, hi) or None})]
    series: {name: (colour, marker)} in legend order
    top_first: put the first series highest within each group
    connect: grey segment between the two point estimates (Figure 4)
    """
    y = list(range(len(rows)))[::-1]
    names = list(series)
    k = len(names)
    off = (
        {n: ((k - 1) / 2 - i) * 0.22 for i, n in enumerate(names)}
        if top_first
        else {n: (i - (k - 1) / 2) * 0.22 for i, n in enumerate(names)}
    )
    for yi, (lab, vals) in zip(y, rows):
        if connect and all(vals.get(n) for n in names):
            pts = [(vals[n][0], yi + off[n]) for n in names]
            ax.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                color="0.72",
                lw=1.6,
                solid_capstyle="round",
                zorder=1.5,
            )
        for n in names:
            v = vals.get(n)
            if v is None:
                continue
            a, lo, hi = v
            c, m = series[n]
            yy = yi + off[n]
            ax.plot(
                [lo, hi], [yy, yy], color=c, lw=0.8, solid_capstyle="butt", zorder=2
            )
            ax.plot(
                [a],
                [yy],
                marker=m,
                ms=3.4,
                color=c,
                zorder=3,
                mfc=c if sig(lo, hi) else "white",
                mew=0.8,
            )
    ax.axvline(1.0, color="0.35", lw=0.6, ls=(0, (3, 2)), zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.set_xticks(xticks)
    ax.set_xticklabels(["%g" % t for t in xticks])
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def save(fig, stem):
    """PDF is the submission artefact; PNG is for Word and co-authors."""
    for ext in ("pdf", "png"):
        fig.savefig(f"{stem}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {stem}.pdf and {stem}.png")
