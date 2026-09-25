# -*- coding: utf-8 -*-
"""Figure 2 — the economic axis holds across eras; insurance does not, in both
pathogens.

One manipulation again, and it is not the model this time: the model is the
joint model throughout, and what changes is which slice of calendar time it is
read on. So the design strip washes zone A, the cohort, and leaves zone C cool.

Four panels, rows = pathogen, columns = domain. Each panel plots one level of
one domain across three eras, with the omnibus interaction test for the whole
domain annotated. The level is the illustration; the P value is the claim, and
the annotation says which is which.

    left column   income below $10,000    flat in both pathogens
    right column  Medicaid coverage       steps down in both, and in COVID-19
                                          the step is at Delta, not Omicron

**The two arms reach their era estimates by different routes, and the legend
has to say so.** In COVID-19 wave varies within a matched stratum (96.1% of
strata), the wave main effect is identified and in the model, and beta + gamma
reconstructs a valid within-wave contrast using every stratum. In influenza
matching is exact on season, so period is constant inside a stratum, drops out
of the conditional likelihood, and the interaction basis is over-complete; a
per-period contrast would not be uniquely defined. The influenza estimates are
therefore the joint model refitted within each period. Same estimand, different
estimator, because the matching designs differ. Do not "harmonise" by
stratifying the COVID-19 arm as well: that discards every stratum straddling a
wave boundary (Delta keeps 301 of 644).

Colour: the ERA ramp, light to dark, ordered in time. Marks are cool because
they are our estimates; the pathogen key stays warm and lives in the row labels.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from style import COVID, FLU, GREY, INK, MM, RULE, apply_style, sig
from v23_strip import draw_strip

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "results", "figures", "v24", "Figure2_data.csv")
OUT = os.path.join(HERE, "..", "results", "figures", "v24")

#  The set's ERA ramp darkened at its light end. In eFigure 5 the ramp fills
#  blocks, where #9CC3D5 is fine; here it carries 1.4 pt confidence bars and
#  open markers, and at 1.9:1 against white the palest step disappears. This
#  ramp keeps the light-to-dark ordering and lifts the first step to ~2.9:1.
ERA = ("#6FA8C6", "#3D7FA6", "#14395C")

ROWS = [("COVID-19", COVID), ("Influenza", FLU)]
COLS = [
    ("income", "Household income below $10 000"),
    ("insurance", "Medicaid coverage"),
]
YLIM = (0.40, 4.90)
YTICKS = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]


def pfmt(p):
    """JAMA style: no leading zero, 2 decimals, 3 below .01, and < .001."""
    if p < 0.001:
        return "P < .001"
    if p < 0.01:
        return "P = ." + ("%.3f" % p)[2:]
    return "P = ." + ("%.2f" % p)[2:]


def draw_panel(ax, d, arm, dom, show_x):
    sub = d[(d.arm == arm) & (d.domain == dom)].sort_values("era_order")
    ax.set_yscale("log")
    ax.set_ylim(*YLIM)
    ax.set_xlim(0.45, 3.55)
    ax.axhline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)

    xs = sub.era_order.to_numpy(dtype=float)
    ys = sub.aor.to_numpy(dtype=float)
    ok = ~np.isnan(ys)
    if ok.sum() > 1:
        ax.plot(xs[ok], ys[ok], color="#BFBFBF", lw=1.0, zorder=2)
    for (_, r), col in zip(sub.iterrows(), ERA):
        if np.isnan(r.aor):
            continue
        ax.plot(
            [r.era_order] * 2,
            [r.lo, r.hi],
            color=col,
            lw=1.4,
            zorder=3,
            solid_capstyle="butt",
        )
        f = sig(r.lo, r.hi)
        ax.plot(
            [r.era_order],
            [r.aor],
            marker="o",
            ms=6.0,
            color=col,
            mfc=col if f else "white",
            mew=1.5,
            zorder=4,
        )

    if not ok.any():
        #  An empty panel must look deliberately empty, or a reader assumes the
        #  estimates were null. Wash it, and name the file that is missing.
        ax.set_facecolor("#FBF1EE")
        ax.text(
            0.5,
            0.60,
            "NOT YET DRAWN",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#9C4A3C",
        )
        ax.text(
            0.5,
            0.47,
            "the estimates exist; they sit\n"
            "on the stopped COVID-19 machine\n"
            "(mi40b/wave_contrasts_mi.csv)",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=10,
            color="#9C4A3C",
            linespacing=1.5,
        )

    #  the omnibus test for the whole domain, not for the line that is drawn
    r0 = sub.iloc[0]
    what = "wave" if arm == "COVID-19" else "period"
    #  Two short lines rather than one long one: the middle era sits at the
    #  centre of the panel and a wide annotation runs into its interval.
    ax.text(
        0.035,
        0.960,
        "%s × %s" % (dom.capitalize(), what),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=INK,
    )
    ax.text(
        0.035,
        0.862,
        "%s, %d df" % (pfmt(r0.omnibus_P), int(r0.omnibus_df1)),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=GREY,
    )

    ax.set_yticks(YTICKS)
    ax.set_yticklabels(["%g" % t for t in YTICKS])
    ax.yaxis.set_minor_locator(plt.NullLocator())
    ax.set_xticks([1, 2, 3])
    if show_x:
        ax.set_xticklabels(list(sub.era_label))
    else:
        ax.set_xticklabels([])
    ax.tick_params(axis="x", length=0, pad=3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return sub


def main():
    apply_style()
    d = pd.read_csv(DATA)

    #  Positions are set by hand rather than by gridspec: the strip has to run
    #  the full width while the panels are inset by the y-axis labels, and the
    #  two row headers have to clear the n counts printed under the row above.
    H = 164.0
    fig = plt.figure(figsize=(180 * MM, H * MM))
    ax_strip = fig.add_axes([0.004, 0.775, 0.992, 0.205])
    draw_strip(ax_strip, "period")

    XP = [(0.098, 0.408), (0.578, 0.414)]  # (left, width) per column
    YP = [0.480, 0.155]  # bottom of each panel row
    PH = 0.215  # panel height
    letters = iter("BCDE")
    for i, (arm, col) in enumerate(ROWS):
        hy = YP[i] + PH + 0.028
        fig.text(
            0.004,
            hy + 0.004,
            "BD"[i],
            fontsize=12,
            fontweight="bold",
            ha="left",
            va="bottom",
            color=INK,
        )
        fig.text(
            0.052,
            hy + 0.010,
            arm,
            fontsize=11,
            fontweight="bold",
            ha="left",
            va="center",
            color=col,
        )
        fig.add_artist(
            plt.Line2D(
                [0.036],
                [hy + 0.010],
                marker="s",
                ms=7,
                color=col,
                mec=col,
                transform=fig.transFigure,
            )
        )
        for j, (dom, title) in enumerate(COLS):
            ax = fig.add_axes([XP[j][0], YP[i], XP[j][1], PH])
            sub = draw_panel(ax, d, arm, dom, show_x=True)
            if i == 0:
                ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
            ax.set_ylabel("Adjusted odds ratio", labelpad=2)
            if j == 1:
                fig.text(
                    XP[1][0] - 0.052,
                    hy + 0.004,
                    "CE"[i],
                    fontsize=12,
                    fontweight="bold",
                    ha="left",
                    va="bottom",
                    color=INK,
                )
            for _, r in sub.iterrows():
                ax.annotate(
                    format(int(r.n_rows), ","),
                    xy=(r.era_order, 0),
                    xycoords=("data", "axes fraction"),
                    xytext=(0, -17),
                    textcoords="offset points",
                    ha="center",
                    va="top",
                    fontsize=10,
                    color=GREY,
                )

    fig.text(
        0.5,
        0.038,
        "Matched rows in each era are printed beneath the "
        "axis.  Filled marker: 95% CI excludes 1.0.",
        ha="center",
        va="center",
        fontsize=10,
        color=GREY,
    )
    fig.text(
        0.002,
        0.982,
        "A",
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=INK,
    )

    stem = os.path.join(OUT, "Figure2")
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=400)
    plt.close(fig)
    print("  wrote %s.pdf and %s.png" % (stem, stem))


if __name__ == "__main__":
    main()
