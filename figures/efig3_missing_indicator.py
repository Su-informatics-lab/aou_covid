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
import re

import matplotlib.pyplot as plt
import pandas as pd
from style import (
    COVID,
    DARK,
    INCOME,
    INCOME_TINT,
    INK,
    MEDICAID,
    MEDICAID_TINT,
    MM,
    PT_BODY,
    PT_HEAD,
    PT_SMALL,
    RULE,
    TXT_GREY,
    apply_style,
    sig,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "results", "figures", "v25", "eFigure3_data.csv")
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
LIGHT = "#B5B5B5"


def colors(r):
    """v26 key: hue = variable (income navy, Medicaid purple, others dark grey);
    tint = fitted alone, full = fitted with the other items."""
    if r.domain == "income":
        return INCOME_TINT, INCOME
    if r.level == "Medicaid":
        return MEDICAID_TINT, MEDICAID
    return LIGHT, DARK


def money(t):
    t = re.sub(r"(\d),(\d{3})", r"\1 \2", str(t)).replace("\u2013", "-")
    return t.replace("< $", "<$").replace("\u2265 $", "\u2265$")


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
HEADH, DY, CONN = 0.90, 0.190, "#9A9A9A"


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
            fontsize=PT_HEAD,
            fontweight="bold",
            color=INK,
        )
        ax.plot(XLIM, [yy + 0.22] * 2, color="#D8D8D8", lw=0.7, zorder=1)
        ax.text(
            XLIM[1],
            yy - 0.12,
            money(REFTEXT[dom]),
            ha="right",
            va="center",
            fontsize=PT_SMALL,
            color=TXT_GREY,
        )
    for r, yy in rows:
        ax_lab.text(
            1.0,
            yy,
            money(
                {"Unemployed": "Out of work or unable to work"}.get(
                    r.level_label, r.level_label
                )
            ),
            ha="right",
            va="center",
            fontsize=PT_BODY,
            color=INK,
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
        c_alone, c_joint = colors(r)
        for aor, lo, hi, col, off in (
            (r.ds_aor, r.ds_lo, r.ds_hi, c_alone, -DY),
            (r.joint_aor, r.joint_lo, r.joint_hi, c_joint, DY),
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
        fontsize=PT_HEAD,
        fontweight="bold",
        color=COVID,
        ha="left",
    )
    ax.set_xlabel(
        "Adjusted odds ratio of hospitalization (95% CI, log scale)",
        labelpad=4,
        fontsize=PT_BODY,
    )
    ax.tick_params(axis="x", labelsize=PT_SMALL)

    key = fig.add_axes([0.004, 0.006, 0.992, 0.060])
    key.set_xlim(0, 1)
    key.set_ylim(0, 1)
    key.axis("off")
    # line 1: alone -> with the other items
    key.plot([0.330], [0.72], marker="o", ms=4.8, color=LIGHT, clip_on=False)
    key.annotate(
        "",
        xy=(0.378, 0.72),
        xytext=(0.338, 0.72),
        arrowprops=dict(arrowstyle="-|>", color=CONN, lw=0.9, mutation_scale=7),
    )
    key.plot([0.386], [0.72], marker="o", ms=4.8, color=DARK, clip_on=False)
    key.text(
        0.398,
        0.72,
        "light: alone  \u2192  full color: jointly adjusted"
        "  (navy, income; pink, Medicaid)",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )
    # line 2: filled vs open
    key.plot([0.330], [0.22], marker="o", ms=4.8, color=DARK, clip_on=False)
    key.text(
        0.342,
        0.22,
        "filled: 95% CI excludes 1",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )
    key.plot(
        [0.520],
        [0.22],
        marker="o",
        ms=4.8,
        color=DARK,
        mfc="white",
        mew=1.2,
        clip_on=False,
    )
    key.text(
        0.532,
        0.22,
        "open: 95% CI includes 1",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )

    stem = os.path.join(OUT, "eFigure3")
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=400)
    plt.close(fig)
    print("  wrote %s.pdf and %s.png" % (stem, stem))


if __name__ == "__main__":
    main()
