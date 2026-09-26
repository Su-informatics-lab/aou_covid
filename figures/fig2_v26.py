# -*- coding: utf-8 -*-
"""Figure 2 (v26, R9 visual-storytelling review): what changed, what it is made of,
and what the record codes.

A  Ratio of odds ratios, later era vs earlier era, from the same separate
   interaction models as the era-specific estimates (eTable 20B): income below
   $10 000 (navy) and Medicaid (purple). 1 = no change. Open marker: 95% CI
   includes 1.
B  COVID-19 only. Each wave's jointly adjusted log odds ratio split into the
   part shared with the other 5 social items (grey; log OR alone minus log OR
   jointly) and the part not shared (the term's colour; log OR jointly), with
   the joint 95% CI beneath. Axis in odds-ratio units on a log scale. Influenza
   is not drawn here because its shared Medicaid part is not constant
   (eFigure 8).
C  Among COVID-19 matched participants who reported a social risk on the
   survey, the percentage with the corresponding Z code (dark) and with any
   Z55-Z65 code (light) dated before the index date, on a 0-100% scale
   (eTable 13). The education-specific count is below 20 and is not shown.

Drawn at the final print width (180 mm); nothing sits outside the axes grid.
Reads results/figures/v25/{Figure2_ror_data.csv, Figure2_era_attenuation_data.csv}.
Writes results/figures/v25/Figure2.{pdf,png}.
"""

import os
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd
from style import (
    INCOME,
    INK,
    MEDICAID,
    MM,
    PT_BODY,
    PT_HEAD,
    PT_SMALL,
    REFG,
    RULE,
    SHARED,
    apply_style,
    plt,
    sig,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v25")
COL = {"income_lt10k": INCOME, "medicaid": MEDICAID}
LAB = {"income_lt10k": "Income <\\$10 000", "medicaid": "Medicaid"}
DARK = "#4D4D4D"
REF_TXT = "#666666"
# eTable 13 (01d_zcode_capture.py output, screened at 20)
ZROWS = [
    ("Income below \\$25 000", 3817, 10.8, "Z59", 18.7),
    ("Out of work or unable to work", 3608, 5.8, "Z56", 20.4),
    ("Unstable housing", 2309, 15.7, "Z59", 24.0),
    ("Education below GED", 1487, None, "Z55", 15.6),
]


def q2(v):
    return str(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def panel_title(fig, ax, letter, title, sub=None, dx=0.05):
    p = ax.get_position()
    top = 0.075 if sub else 0.035
    fig.text(p.x0 - dx, p.y1 + top, letter, fontsize=10, fontweight="bold", va="bottom")
    fig.text(
        p.x0 - dx + 0.028,
        p.y1 + top,
        title,
        fontsize=PT_HEAD,
        fontweight="bold",
        va="bottom",
    )
    if sub:
        fig.text(
            p.x0 - dx + 0.028,
            p.y1 + 0.045,
            sub,
            fontsize=PT_BODY,
            color=REF_TXT,
            va="bottom",
        )


def forest(ax, d):
    groups = [
        ("COVID-19", "Delta vs pre-Delta"),
        ("COVID-19", "Omicron vs pre-Delta"),
        ("Influenza", "after vs before"),
    ]
    y, yt, yl = 0, [], []
    for pth, con in groups:
        ax.text(
            0.0,
            y,
            "%s, %s" % (pth, con),
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=PT_SMALL,
            fontweight="bold",
            color=INK,
        )
        y -= 1
        for term in ("income_lt10k", "medicaid"):
            r = d[
                (d.pathogen == pth)
                & (d.contrast.str.lower() == con.lower())
                & (d.term == term)
            ].iloc[0]
            c = COL[term]
            ax.plot([r.lo, r.hi], [y, y], color=c, lw=1.3, zorder=2)
            ax.plot(
                [r.ror],
                [y],
                marker="o",
                ms=5.5,
                color=c,
                mfc=c if sig(r.lo, r.hi) else "white",
                mew=1.4,
                zorder=3,
            )
            ax.text(
                1.02,
                y,
                "%s (%s-%s)" % (q2(r.ror), q2(r.lo), q2(r.hi)),
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=PT_SMALL,
                color=c,
            )
            yt.append(y)
            yl.append(LAB[term])
            y -= 1
        y -= 0.4
    ax.axvline(1, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(0.4, 2.2)
    ax.set_xticks([0.5, 0.75, 1, 1.5, 2])
    ax.set_xticklabels(["0.5", "0.75", "1", "1.5", "2"])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=PT_SMALL)
    for t, lab in zip(ax.get_yticklabels(), yl):
        t.set_color(INCOME if lab.startswith("Income") else MEDICAID)
    ax.set_ylim(y + 0.6, 0.6)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(
        "Ratio of odds ratios, later / earlier era (log scale)", fontsize=PT_BODY
    )
    ax.text(
        1, 0.62, "no change", ha="center", va="bottom", fontsize=PT_SMALL, color=REF_TXT
    )


COVID_ERAS = ((1, "Pre-Delta"), (2, "Delta"), (3, "Omicron"))


def split(
    ax,
    d,
    pathogen="COVID-19",
    eras=COVID_ERAS,
    xlim=(0.68, 2.3),
    ticks=(0.75, 1, 1.25, 1.5, 2),
):
    y, yt, yl = 0, [], []
    for term in ("income_lt10k", "medicaid"):
        ax.text(
            0.0,
            y,
            LAB[term],
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=PT_SMALL,
            fontweight="bold",
            color=COL[term],
        )
        y -= 1
        ax.plot(
            [0, 0], [y + 0.5, y - 2.6], color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1
        )
        for o, era in eras:
            s = d[(d.pathogen == pathogen) & (d.term == term) & (d.era_order == o)]
            a = s[s.model == "alone"].iloc[0]
            j = s[s.model == "joint"].iloc[0]
            yt.append(y)
            yl.append(era)
            if pd.isna(a.aor) or pd.isna(j.aor):
                # withheld: reference group below 20 cases (03x); one mark used in every figure
                ax.add_patch(
                    plt.Rectangle(
                        (np.log(0.9), y - 0.3),
                        np.log(1.25) - np.log(0.9),
                        0.6,
                        fill=False,
                        ls=(0, (2, 2)),
                        lw=0.8,
                        edgecolor=REFG,
                        zorder=2,
                    )
                )
                ax.text(
                    np.log(1.06),
                    y,
                    "withheld (<20)",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color=REF_TXT,
                    bbox=dict(fc="white", ec="none", pad=0.5),
                    zorder=3,
                )
                y -= 1
                continue
            la, lj = np.log(a.aor), np.log(j.aor)
            ax.barh(y, la - lj, left=lj, height=0.56, color=SHARED, zorder=2)
            ax.barh(y, lj, left=0, height=0.30, color=COL[term], zorder=3)
            ax.plot(
                [np.log(j.lo), np.log(j.hi)],
                [y - 0.42, y - 0.42],
                color=COL[term],
                lw=0.9,
                zorder=3,
            )
            y -= 1
        y -= 0.4
    ax.set_xticks(np.log(ticks))
    ax.set_xticklabels(["%g" % t for t in ticks])
    ax.set_xlim(np.log(xlim[0]), np.log(xlim[1]))
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=PT_SMALL)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Odds ratio (log scale)", fontsize=PT_BODY)
    # key, above the first group
    kx, kw = np.log(xlim[0]) + 0.02, 0.07
    ax.barh(1.9, kw, left=kx, height=0.40, color=SHARED, zorder=2)
    ax.text(
        kx + kw + 0.02,
        1.9,
        "shared with the other 5 items",
        va="center",
        fontsize=PT_SMALL,
        color=REF_TXT,
    )
    ax.barh(1.35, kw, left=kx, height=0.22, color=DARK, zorder=2)
    ax.text(
        kx + kw + 0.02,
        1.35,
        "not shared (adjusted OR)",
        va="center",
        fontsize=PT_SMALL,
        color=REF_TXT,
    )
    ax.plot([kx, kx + kw], [0.8, 0.8], color=DARK, lw=0.9)
    ax.text(
        kx + kw + 0.02,
        0.8,
        "95% CI of the adjusted OR",
        va="center",
        fontsize=PT_SMALL,
        color=REF_TXT,
    )
    ax.set_ylim(y + 0.6, 2.25)


def zcodes(ax):
    for i, (lab, n, pz, code, pany) in enumerate(ZROWS):
        y = -i
        ax.barh(y, 100, height=0.62, color="white", edgecolor=RULE, lw=0.7, zorder=1)
        ax.barh(y, pany, height=0.62, color=SHARED, zorder=2)
        if pz is None:
            ax.text(
                pany + 1.5,
                y,
                "any Z55-Z65 %.1f%%;  %s: fewer than 20" % (pany, code),
                ha="left",
                va="center",
                fontsize=PT_SMALL,
                color=INK,
            )
        else:
            ax.barh(y, pz, height=0.62, color=DARK, zorder=3)
            ax.text(
                pany + 1.5,
                y,
                "%s %.1f%%;  any Z55-Z65 %.1f%%" % (code, pz, pany),
                ha="left",
                va="center",
                fontsize=PT_SMALL,
                color=INK,
            )
        ax.text(
            -1.5,
            y,
            "%s (n = %s)" % (lab, "{:,}".format(n)),
            ha="right",
            va="center",
            fontsize=PT_SMALL,
        )
    ax.set_xlim(0, 100)
    ax.set_ylim(-len(ZROWS) + 0.4, 0.6)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(
        "% of COVID-19 matched participants reporting the risk", fontsize=PT_BODY
    )


def main():
    apply_style()
    plt.rcParams.update({"xtick.labelsize": PT_SMALL, "ytick.labelsize": PT_SMALL})
    ror = pd.read_csv(os.path.join(OUT, "Figure2_ror_data.csv"))
    att = pd.read_csv(os.path.join(OUT, "Figure2_era_attenuation_data.csv"))
    fig = plt.figure(figsize=(180 * MM, 140 * MM))
    axA = fig.add_axes([0.15, 0.46, 0.25, 0.40])
    axB = fig.add_axes([0.64, 0.46, 0.31, 0.40])
    axC = fig.add_axes([0.30, 0.08, 0.62, 0.19])
    forest(axA, ror)
    split(axB, att)
    zcodes(axC)
    panel_title(
        fig,
        axA,
        "A",
        "What changed, beyond the other social items",
        "Medicaid fell in COVID-19; income showed no detected change",
        dx=0.13,
    )
    panel_title(
        fig,
        axB,
        "B",
        "COVID-19: the part shared with the other items",
        "Medicaid's own part fell to about zero; income's did not",
        dx=0.10,
    )
    panel_title(
        fig,
        axC,
        "C",
        "The record rarely codes the social risk patients report",
        dx=0.28,
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure2." + ext), dpi=400)
    plt.close(fig)
    print("wrote Figure2 to", OUT)


if __name__ == "__main__":
    main()
