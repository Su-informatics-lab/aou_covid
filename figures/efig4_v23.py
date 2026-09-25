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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from style import GREY, INK, MM, NAVY, RULE, TEAL, apply_style, sig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v23")
DATA = os.path.join(OUT, "eFigure4_data.csv")
XLIM, XTICKS = (0.80, 1.85), [0.8, 1.0, 1.2, 1.5, 1.8]
DY = 0.185


def main():
    apply_style()
    d = pd.read_csv(DATA)
    n = len(d)
    fig = plt.figure(figsize=(180 * MM, 104 * MM))
    ax = fig.add_axes([0.265, 0.290, 0.720, 0.680])
    ax.set_xscale("log")
    ax.set_xlim(*XLIM)
    ax.set_ylim(-0.7, n - 0.3)
    ax.invert_yaxis()
    ax.axvline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)

    for i, r in d.iterrows():
        if r.level == "ref":
            ax.plot(
                [1.0], [i], marker="s", ms=3.8, color="#B4B4B4", mec="#B4B4B4", zorder=4
            )
            continue
        for aor, lo, hi, col, off in (
            (r.ind_aor, r.ind_lo, r.ind_hi, TEAL, -DY),
            (r.mi_aor, r.mi_lo, r.mi_hi, NAVY, DY),
        ):
            if np.isnan(aor):
                continue
            ax.plot([lo, hi], [i + off] * 2, color=col, lw=1.2, zorder=3)
            f = sig(lo, hi)
            ax.plot(
                [aor],
                [i + off],
                marker="o",
                ms=5.0,
                color=col,
                mfc=col if f else "white",
                mew=1.2,
                zorder=4,
            )

    ax.set_yticks(range(n))
    ax.set_yticklabels(d.label, fontsize=10)
    ax.set_xticks(XTICKS)
    ax.set_xticklabels(["%g" % t for t in XTICKS])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_xlabel("Adjusted odds ratio of hospitalization (95% CI, log scale)")

    #  the three bands the argument turns on, marked in the margin rather than
    #  annotated inside the panel, where the intervals already reach 1.7
    for i in (4, 5, 6):
        ax.plot(
            [XLIM[1] * 0.995],
            [i],
            marker="|",
            ms=9,
            color=GREY,
            mew=1.4,
            clip_on=False,
            zorder=5,
        )

    key = fig.add_axes([0.265, 0.020, 0.720, 0.175])
    key.set_xlim(0, 1)
    key.set_ylim(0, 1)
    key.axis("off")
    key.plot(
        [0.010],
        [0.80],
        marker="o",
        ms=5.0,
        color=TEAL,
        mfc=TEAL,
        mew=1.2,
        clip_on=False,
    )
    key.text(
        0.028,
        0.80,
        "missing-indicator (sensitivity 1)",
        ha="left",
        va="center",
        fontsize=10,
        color=TEAL,
    )
    key.plot(
        [0.010],
        [0.47],
        marker="o",
        ms=5.0,
        color=NAVY,
        mfc=NAVY,
        mew=1.2,
        clip_on=False,
    )
    key.text(
        0.028,
        0.47,
        "imputation, m = 40 (primary)",
        ha="left",
        va="center",
        fontsize=10,
        color=NAVY,
    )
    key.plot(
        [0.520], [0.80], marker="o", ms=5.0, color=INK, mfc=INK, mew=1.2, clip_on=False
    )
    key.text(
        0.538,
        0.80,
        "95% CI excludes 1.0",
        ha="left",
        va="center",
        fontsize=10,
        color=INK,
    )
    key.plot(
        [0.520],
        [0.47],
        marker="o",
        ms=5.0,
        color=INK,
        mfc="white",
        mew=1.2,
        clip_on=False,
    )
    key.text(0.538, 0.47, "it does not", ha="left", va="center", fontsize=10, color=INK)
    key.plot([0.010], [0.13], marker="|", ms=9, color=GREY, mew=1.4, clip_on=False)
    key.text(
        0.028,
        0.13,
        "the 3 highest bands, jointly indistinguishable from "
        "the reference under imputation",
        ha="left",
        va="center",
        fontsize=10,
        color=GREY,
    )

    stem = os.path.join(OUT, "eFigure4")
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=400)
    plt.close(fig)
    print("  wrote %s.pdf and %s.png" % (stem, stem))


if __name__ == "__main__":
    main()
