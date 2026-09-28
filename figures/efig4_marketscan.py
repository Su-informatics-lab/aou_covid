# -*- coding: utf-8 -*-
"""eFigure 6 - the clinical base model in All of Us against MarketScan.

The claim this figure carries is narrow and it is a claim about direction, not
about magnitude, so the display is a scatter and not a forest plot. Each point
is one term of the clinical base model, its All of Us adjusted odds ratio on
the horizontal axis and its MarketScan adjusted odds ratio on the vertical,
both on a log scale. A point in a shaded quadrant is a term the two cohorts put
on the same side of 1.0.

Twenty of the 26 comparable terms agree. The six that do not are named on the
figure, and three of those six have an All of Us interval that includes 1.0, so
they are terms All of Us does not resolve rather than terms the two cohorts
contradict each other on.

MarketScan intervals are drawn but are narrower than the marker at this scale;
n = 637,679 matched observations there against 19,520 in All of Us. That is a
property of the sample size, not of the agreement, and is the reason the
figure is read by quadrant and not by overlap.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
import pandas as pd
from style import DARK, INK, MM, PT_BODY, PT_SMALL, RULE, apply_style

GREY = "#9A9A9A"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "results", "figures", "v25", "eFigure4_data.csv")
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")

LIM = (0.355, 2.90)
TICKS = [0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5]
SHADE = "#EFEFEF"

# Every term whose two cohorts disagree is named, with a leader line, because
# four of the six sit inside one small patch and cannot be labelled in place.
# Values are data coordinates for the text anchor and the horizontal alignment.
LABELS = {
    "Myocardial infarction": (0.90, 0.945, "right"),
    "Malignancy": (1.42, 0.960, "left"),
    "Cerebrovascular disease": (1.42, 0.868, "left"),
    "Rheumatic disease": (1.42, 0.790, "left"),
    "Omicron": (1.30, 0.474, "left"),
    "AIDS": (0.60, 1.42, "right"),
}


def main():
    apply_style()
    d = pd.read_csv(DATA)

    fig = plt.figure(figsize=(150 * MM, 148 * MM))
    ax = fig.add_axes([0.115, 0.115, 0.865, 0.800])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*LIM)
    ax.set_ylim(*LIM)
    ax.set_aspect("equal", adjustable="box")

    # the two quadrants in which the cohorts agree
    ax.add_patch(
        plt.Rectangle(
            (LIM[0], LIM[0]),
            1 - LIM[0],
            1 - LIM[0],
            transform=ax.transData,
            facecolor=SHADE,
            edgecolor="none",
            zorder=0,
        )
    )
    ax.add_patch(
        plt.Rectangle(
            (1, 1),
            LIM[1] - 1,
            LIM[1] - 1,
            transform=ax.transData,
            facecolor=SHADE,
            edgecolor="none",
            zorder=0,
        )
    )
    ax.plot(LIM, LIM, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.axvline(1, color=RULE, lw=0.9, zorder=1)
    ax.axhline(1, color=RULE, lw=0.9, zorder=1)

    for _, r in d.iterrows():
        agree = bool(r.agree)
        col = DARK if agree else GREY
        ax.plot(
            [r.aou_lo, r.aou_hi],
            [r.ms_aor] * 2,
            color=col,
            lw=0.9,
            zorder=2,
            alpha=0.85,
        )
        ax.plot(
            [r.aou_aor] * 2, [r.ms_lo, r.ms_hi], color=col, lw=0.9, zorder=2, alpha=0.85
        )
        ax.plot(
            r.aou_aor,
            r.ms_aor,
            "o" if agree else "s",
            ms=5.0 if agree else 4.6,
            zorder=3,
            mfc=col,
            mec=col,
        )
        if r.term in LABELS:
            lx, ly, ha = LABELS[r.term]
            pad = 0.985 if ha == "left" else 1.015
            ax.annotate(
                "",
                xy=(r.aou_aor, r.ms_aor),
                xytext=(lx * pad, ly),
                arrowprops=dict(
                    arrowstyle="-", color=RULE, lw=0.7, shrinkA=1.0, shrinkB=4.0
                ),
                zorder=2,
            )
            ax.text(
                lx,
                ly,
                r.term,
                fontsize=PT_SMALL,
                color=INK,
                ha=ha,
                va="center",
                zorder=4,
            )

    for a in (ax.xaxis, ax.yaxis):
        a.set_minor_formatter(plt.NullFormatter())
        a.set_minor_locator(plt.NullLocator())
    ax.set_xticks(TICKS)
    ax.set_xticklabels(["%g" % t for t in TICKS])
    ax.set_yticks(TICKS)
    ax.set_yticklabels(["%g" % t for t in TICKS])
    ax.set_xlabel("All of Us, adjusted odds ratio (log scale)", fontsize=PT_BODY)
    ax.set_ylabel("MarketScan, adjusted odds ratio (log scale)", fontsize=PT_BODY)
    ax.tick_params(labelsize=PT_SMALL)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    for s in ax.spines.values():
        s.set_linewidth(0.8)

    n_agree = int(d.agree.sum())
    ax.text(
        0.02,
        0.975,
        "%d of %d terms agree in direction" % (n_agree, len(d)),
        transform=ax.transAxes,
        fontsize=PT_BODY,
        va="top",
        color=INK,
    )
    h = [
        plt.Line2D(
            [],
            [],
            ls="",
            marker="o",
            ms=5.0,
            mfc=DARK,
            mec=DARK,
            label="Same direction",
        ),
        plt.Line2D(
            [],
            [],
            ls="",
            marker="s",
            ms=4.6,
            mfc=GREY,
            mec=GREY,
            label="Different direction",
        ),
    ]
    ax.legend(
        handles=h,
        loc="lower right",
        fontsize=PT_SMALL,
        borderpad=0.2,
        handletextpad=0.4,
    )

    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "eFigure4." + ext), dpi=400)
    print("wrote eFigure4  |  %d of %d agree" % (n_agree, len(d)))


if __name__ == "__main__":
    main()
