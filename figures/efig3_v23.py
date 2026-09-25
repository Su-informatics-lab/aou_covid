# -*- coding: utf-8 -*-
"""eFigure 3 — Figure 1's manipulation under the missing-indicator specification.

The COVID-19 arm only, and the specification that is now sensitivity 1. It is
here so a reader can see that the qualitative result — insurance and education
lose their associations when the economic domains are in the same model — does
not depend on how missing survey answers were handled, and can see at the same
time what does depend on it: the size of the low-income estimates, and the
Medicaid estimate, which stays marginally above 1 here and crosses under
imputation.

Same encoding as Figure 1, so a reader who has learned it once carries it here:
teal is the domain fitted alone, navy is the same domain fitted with the others,
the arrow runs from one to the other, and a filled marker means the interval
excludes 1.

The income "missing" row exists only under this specification. It is the row
that motivated the change: at 1.49 jointly adjusted it is the largest income
estimate in the model, and what it carries is not poverty but the fact that
income was missing for 26.5% of cases against 19.0% of controls.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
import pandas as pd
from style import COVID, GREY, INK, MM, NAVY, RULE, TEAL, apply_style, sig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v23")
DATA = os.path.join(OUT, "eFigure3_data.csv")

ORDER = ["income", "employment", "housing", "stability", "insurance", "education"]
REFTEXT = {
    "income": "vs $35 000-99 999",
    "employment": "vs employed",
    "housing": "vs owns home",
    "stability": "vs stable",
    "insurance": "vs employer-sponsored",
    "education": "vs college graduate or higher",
}
XLIM, XTICKS = (0.78, 2.05), [0.8, 1.0, 1.2, 1.5, 2.0]
HEADH, DY, CONN = 0.90, 0.190, "#BFBFBF"


def main():
    apply_style()
    d = pd.read_csv(DATA)
    y, heads, rows = 0.0, [], []
    for dom in ORDER:
        sub = d[d.domain == dom]
        y += HEADH
        heads.append((dom, sub.domain_label.iloc[0], y))
        y += 0.30
        for _, r in sub.iterrows():
            y += 1.0
            rows.append((r, y))
        y += 0.35
    ymax = y + 0.35

    fig = plt.figure(figsize=(180 * MM, 152 * MM))
    ax_lab = fig.add_axes([0.004, 0.130, 0.300, 0.800])
    ax = fig.add_axes([0.320, 0.130, 0.668, 0.800])
    for a in (ax_lab, ax):
        a.set_ylim(0, ymax)
        a.invert_yaxis()
    ax_lab.set_xlim(0, 1)
    ax_lab.axis("off")

    ax.set_xscale("log")
    ax.set_xlim(*XLIM)
    ax.axvline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    for dom, lab, yy in heads:
        ax_lab.text(
            0.0,
            yy,
            lab,
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=INK,
        )
        ax.plot(XLIM, [yy + 0.16] * 2, color="#D8D8D8", lw=0.7, zorder=1)
        ax.text(
            XLIM[1],
            yy - 0.04,
            REFTEXT[dom],
            ha="right",
            va="center",
            fontsize=10,
            color=GREY,
        )
    for r, yy in rows:
        ax_lab.text(
            1.0, yy, r.level_label, ha="right", va="center", fontsize=10, color=INK
        )
        ax.annotate(
            "",
            xy=(r.joint_aor, yy + DY),
            xytext=(r.ds_aor, yy - DY),
            arrowprops=dict(
                arrowstyle="-|>",
                color=CONN,
                lw=0.9,
                shrinkA=3.2,
                shrinkB=4.4,
                mutation_scale=7,
            ),
            zorder=2,
        )
        for aor, lo, hi, col, off in (
            (r.ds_aor, r.ds_lo, r.ds_hi, TEAL, -DY),
            (r.joint_aor, r.joint_lo, r.joint_hi, NAVY, DY),
        ):
            ax.plot([lo, hi], [yy + off] * 2, color=col, lw=1.1, zorder=3)
            f = sig(lo, hi)
            ax.plot(
                [aor],
                [yy + off],
                marker="o",
                ms=4.8,
                color=col,
                mfc=col if f else "white",
                mew=1.2,
                zorder=4,
            )

    ax.set_xticks(XTICKS)
    ax.set_xticklabels(["%g" % t for t in XTICKS])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.set_yticks([])
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)

    fig.text(
        0.320,
        0.960,
        "COVID-19, missing-indicator specification",
        fontsize=11,
        fontweight="bold",
        color=COVID,
        ha="left",
    )
    ax.set_xlabel(
        "Adjusted odds ratio of hospitalization (95% CI, log scale)", labelpad=4
    )

    key = fig.add_axes([0.004, 0.010, 0.992, 0.036])
    key.set_xlim(0, 1)
    key.set_ylim(0, 1)
    key.axis("off")
    key.plot(
        [0.006], [0.5], marker="o", ms=4.8, color=TEAL, mfc=TEAL, mew=1.2, clip_on=False
    )
    key.annotate(
        "",
        xy=(0.070, 0.5),
        xytext=(0.014, 0.5),
        arrowprops=dict(arrowstyle="-|>", color=CONN, lw=0.9, mutation_scale=7),
    )
    key.plot(
        [0.078], [0.5], marker="o", ms=4.8, color=NAVY, mfc=NAVY, mew=1.2, clip_on=False
    )
    key.text(
        0.094,
        0.5,
        "the domain fitted on its own",
        ha="left",
        va="center",
        fontsize=10,
        color=TEAL,
    )
    key.text(0.392, 0.5, "→", ha="left", va="center", fontsize=10, color=GREY)
    key.text(
        0.418,
        0.5,
        "fitted with the others",
        ha="left",
        va="center",
        fontsize=10,
        color=NAVY,
    )
    key.plot(
        [0.606], [0.5], marker="o", ms=4.8, color=INK, mfc=INK, mew=1.2, clip_on=False
    )
    key.text(
        0.622,
        0.5,
        "95% CI excludes 1.0",
        ha="left",
        va="center",
        fontsize=10,
        color=INK,
    )
    key.plot(
        [0.842],
        [0.5],
        marker="o",
        ms=4.8,
        color=INK,
        mfc="white",
        mew=1.2,
        clip_on=False,
    )
    key.text(0.858, 0.5, "it does not", ha="left", va="center", fontsize=10, color=INK)

    stem = os.path.join(OUT, "eFigure3")
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=400)
    plt.close(fig)
    print("  wrote %s.pdf and %s.png" % (stem, stem))


if __name__ == "__main__":
    main()
