# -*- coding: utf-8 -*-
"""eFigure 4 — the shape of the income association under the two specifications.

The reason the primary specification was changed, drawn rather than asserted.

Under the missing-indicator coding the jointly adjusted income estimates do not
fall with income: the $100,000-149,999 and $150,000-199,999 bands sit above the
reference with intervals excluding 1, which reads as a U and invites a story
about the wealthy. Under multiple imputation they do not. What changed is not
the data but where the 26.5% of cases with a missing income answer were put: the
indicator coding gave them their own level, which carried case-control
information as well as social information, and the low bands lost magnitude to
it.

Only the COVID-19 arm is drawn. The influenza arm never showed the U under
either specification, which is itself part of the argument that the U was a
property of the coding.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from style import (
    DARK,
    INCOME,
    INK,
    MM,
    PT_BODY,
    PT_SMALL,
    RULE,
    TXT_GREY,
    apply_style,
    sig,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(
    HERE, "..", "results", "figures", "v25", "eFigure8_data.csv"
)  # imputation series: 03n R2 (current primary)
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
SENS = "#8C8C8C"  # sensitivity specification: neutral grey, square marker


def money(t):
    t = re.sub(r"(\d),(\d{3})", r"\1 \2", str(t)).replace("\u2013", "-")
    return t.replace("< $", "<$").replace("\u2265 $", "\u2265$")


XLIM, XTICKS = (0.80, 1.85), [0.8, 1.0, 1.2, 1.5, 1.8]
DY = 0.185


def main():
    apply_style()
    d = pd.read_csv(DATA)
    n = len(d)
    fig = plt.figure(figsize=(180 * MM, 104 * MM))
    ax = fig.add_axes([0.230, 0.250, 0.600, 0.720])
    ax.set_xscale("log")
    ax.set_xlim(*XLIM)
    ax.set_ylim(-0.7, n - 0.3)
    ax.invert_yaxis()
    ax.axvline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)

    for i, r in d.iterrows():
        if r.level == "ref":
            ax.plot([1.0], [i], marker="D", ms=3.6, color=TXT_GREY, zorder=4)
            ax.text(
                1.012,
                i,
                "reference",
                ha="left",
                va="center",
                fontsize=PT_SMALL,
                color=TXT_GREY,
            )
            continue
        for aor, lo, hi, col, off, mk in (
            (r.ind_aor, r.ind_lo, r.ind_hi, SENS, -DY, "s"),
            (r.mi_aor, r.mi_lo, r.mi_hi, INCOME, DY, "o"),
        ):
            if np.isnan(aor):
                continue
            ax.plot([lo, hi], [i + off] * 2, color=col, lw=1.2, zorder=3)
            f = sig(lo, hi)
            ax.plot(
                [aor],
                [i + off],
                marker=mk,
                ms=5.0 if mk == "o" else 4.6,
                color=col,
                mfc=col if f else "white",
                mew=1.2,
                zorder=4,
            )

    ax.set_yticks(range(n))
    ax.set_yticklabels([money(t) for t in d.label], fontsize=PT_BODY)
    ax.tick_params(axis="x", labelsize=PT_SMALL)
    ax.set_xticks(XTICKS)
    ax.set_xticklabels(["%g" % t for t in XTICKS])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_xlabel(
        "Adjusted odds ratio of hospitalization (95% CI, log scale)", fontsize=PT_BODY
    )

    #  the three highest bands: a bracket with the joint test under imputation
    bx = XLIM[1] * 1.02
    ax.plot(
        [bx, bx * 1.012, bx * 1.012, bx],
        [3.7, 3.7, 6.3, 6.3],
        color=DARK,
        lw=0.9,
        clip_on=False,
    )
    ax.text(
        bx * 1.03,
        5.0,
        "3 highest bands,\njoint test under\nimputation:\nP = .16",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=DARK,
    )

    key = fig.add_axes([0.230, 0.015, 0.740, 0.100])
    key.set_xlim(0, 1)
    key.set_ylim(0, 1)
    key.axis("off")
    key.plot([0.010], [0.75], marker="o", ms=5.0, color=INCOME, clip_on=False)
    key.text(
        0.028,
        0.75,
        "imputation, m = 40 (primary)",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )
    key.plot([0.010], [0.25], marker="s", ms=4.6, color=SENS, clip_on=False)
    key.text(
        0.028,
        0.25,
        "missing-indicator (sensitivity 1)",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )
    key.plot([0.480], [0.75], marker="o", ms=5.0, color=DARK, clip_on=False)
    key.text(
        0.498,
        0.75,
        "filled: 95% CI excludes 1",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )
    key.plot(
        [0.480],
        [0.25],
        marker="o",
        ms=5.0,
        color=DARK,
        mfc="white",
        mew=1.2,
        clip_on=False,
    )
    key.text(
        0.498,
        0.25,
        "open: 95% CI includes 1",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )

    stem = os.path.join(OUT, "eFigure8")
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=400)
    plt.close(fig)
    print("  wrote %s.pdf and %s.png" % (stem, stem))


if __name__ == "__main__":
    main()
