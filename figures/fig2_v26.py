# -*- coding: utf-8 -*-
"""Figure 2 (v26, R9 visual-storytelling review): what changed, what it is made of,
and what the record codes.

A  Ratio of odds ratios, later era vs earlier era, from the same separate
   interaction models as the era-specific estimates (eTable 20B): income below
   $10 000 (navy) and Medicaid (purple). 1 = no change. Open marker: 95% CI
   includes 1.
B  COVID-19 only, in the classic attenuation layout (Lassale et al 2020, Fig. 1): for
   each wave, the odds ratio of the item fitted alone (base model + the item; tint) and
   with the other 5 social items (full colour), each with its 95% CI; filled markers
   exclude 1. Right: percent attenuation, 100 x (log OR alone - log OR joint) / log OR
   alone (Stringhini et al 2010), above 100% where the joint OR is below 1. Influenza
   is in eFigure 7.
C  Among COVID-19 matched participants who reported a social risk on the
   survey, the percentage with the corresponding Z code (dark) and with any
   Z55-Z65 code (light) dated before the index date, on a 0-100% scale
   (eTable 10). Income is shown below $10 000, with $35 000-99 999 for
   comparison (R11; 03z_zband.py, working/v25/platform_r11/zband_covid.csv).
   The education-specific count is 20 or fewer and is not shown.

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
    INCOME_TINT,
    INK,
    MEDICAID,
    MEDICAID_TINT,
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
TINT = {"income_lt10k": INCOME_TINT, "medicaid": MEDICAID_TINT}
LAB = {"income_lt10k": "Income <\\$10 000", "medicaid": "Medicaid"}
DARK = "#4D4D4D"
REF_TXT = "#666666"
# eTable 10. Income rows: 03z_zband.py (platform_r11/zband_covid.csv); other rows:
# 01d_zcode_capture.py. Counts of 20 or fewer are withheld.
ZROWS = [
    ("Income below \\$10 000", 1896, 14.3, "Z59", 21.7),
    ("Comparison: \\$35 000-99 999", 3548, 1.8, "Z59", 8.9),
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
                # withheld: reference group 20 or fewer cases (03x); one mark used in every figure
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
                    "withheld (\u226420)",
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
        "attenuated by the other 5 items",
        va="center",
        fontsize=PT_SMALL,
        color=REF_TXT,
    )
    ax.barh(1.35, kw, left=kx, height=0.22, color=DARK, zorder=2)
    ax.text(
        kx + kw + 0.02,
        1.35,
        "remaining after adjustment",
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


def sequential(
    ax,
    d,
    pathogen="COVID-19",
    eras=COVID_ERAS,
    xlim=(0.62, 2.6),
    ticks=(0.75, 1, 1.5, 2),
):
    """Classic attenuation display (as in Lassale et al 2020, Fig. 1): the odds ratio
    fitted with the item alone and with the other 5 items added, each with its 95% CI,
    and the percent attenuation 100 x (log OR alone - log OR joint) / log OR alone."""
    y, yt, yl = 0.0, [], []
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
        y -= 0.9
        for o, era in eras:
            s = d[(d.pathogen == pathogen) & (d.term == term) & (d.era_order == o)]
            a = s[s.model == "alone"].iloc[0]
            j = s[s.model == "joint"].iloc[0]
            yt.append(y - 0.2)
            yl.append(era)
            if pd.isna(a.aor) or pd.isna(j.aor):
                # withheld: reference group 20 or fewer cases (03x); same mark as every figure
                ax.text(
                    1.0,
                    y - 0.2,
                    "withheld (\u226420)",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color=REF_TXT,
                    zorder=3,
                    bbox=dict(fc="white", ec=REFG, ls=(0, (2, 2)), lw=0.8, pad=2),
                )
                y -= 1.15
                continue
            for r, yy, c in ((a, y, TINT[term]), (j, y - 0.4, COL[term])):
                ax.plot([r.lo, r.hi], [yy, yy], color=c, lw=1.1, zorder=2)
                f = sig(r.lo, r.hi)
                ax.plot(
                    r.aor,
                    yy,
                    "o",
                    ms=4.2,
                    mfc=c if f else "white",
                    mec=c,
                    mew=1.1,
                    zorder=3,
                )
            pct = 100 * (np.log(a.aor) - np.log(j.aor)) / np.log(a.aor)
            ax.text(
                1.03,
                y - 0.2,
                "%.0f%%" % pct,
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=PT_SMALL,
                color=INK,
            )
            y -= 1.15
        y -= 0.25
    ax.axvline(1, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.set_xscale("log")
    ax.set_xticks(ticks)
    ax.set_xticklabels(["%g" % t for t in ticks])
    ax.minorticks_off()
    ax.set_xlim(*xlim)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=PT_SMALL)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Odds ratio (95% CI, log scale)", fontsize=PT_BODY)
    ax.text(
        1.03,
        0.0,
        "Attenuated",
        transform=ax.get_yaxis_transform(),
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=REF_TXT,
    )
    # key, above the first group
    for yy, c, lab in (
        (1.75, REFG, "fitted alone (base model + the item)"),
        (1.15, DARK, "with the other 5 social items"),
    ):
        ax.plot([0.66, 0.74], [yy, yy], color=c if c == DARK else SHARED, lw=1.1)
        ax.plot(0.70, yy, "o", ms=4.2, color=c if c == DARK else SHARED)
        ax.text(
            0.78,
            yy,
            lab,
            va="center",
            fontsize=PT_SMALL,
            color=REF_TXT,
            bbox=dict(fc="white", ec="none", pad=0.3),
            zorder=4,
        )
    ax.set_ylim(y + 0.6, 2.2)


def zcodes(ax):
    for i, (lab, n, pz, code, pany) in enumerate(ZROWS):
        y = -i
        ax.barh(y, 100, height=0.62, color="white", edgecolor=RULE, lw=0.7, zorder=1)
        ax.barh(y, pany, height=0.62, color=SHARED, zorder=2)
        if pz is None:
            ax.text(
                pany + 1.5,
                y,
                "any Z55-Z65 %.1f%%;  %s: 20 or fewer" % (pany, code),
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
            color=REF_TXT if lab.startswith("Comparison") else INK,
        )
    ax.set_xlim(0, 100)
    ax.set_ylim(-len(ZROWS) + 0.4, 0.6)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(
        "% of COVID-19 matched participants reporting each circumstance",
        fontsize=PT_BODY,
    )


def main():
    apply_style()
    plt.rcParams.update({"xtick.labelsize": PT_SMALL, "ytick.labelsize": PT_SMALL})
    ror = pd.read_csv(os.path.join(OUT, "Figure2_ror_data.csv"))
    att = pd.read_csv(os.path.join(OUT, "Figure2_era_attenuation_data.csv"))
    fig = plt.figure(figsize=(180 * MM, 140 * MM))
    axA = fig.add_axes([0.15, 0.46, 0.25, 0.40])
    axB = fig.add_axes([0.62, 0.46, 0.29, 0.40])
    axC = fig.add_axes([0.33, 0.07, 0.59, 0.235])
    forest(axA, ror)
    sequential(axB, att)
    zcodes(axC)
    panel_title(
        fig,
        axA,
        "A",
        "What changed, beyond the other social items",
        "Medicaid fell in COVID-19; no narrowing of income was detected",
        dx=0.13,
    )
    panel_title(
        fig,
        axB,
        "B",
        "COVID-19: each item alone and with the other 5",
        "Medicaid's OR fell to about 1 after Delta; income's stayed near 1.5",
        dx=0.10,
    )
    panel_title(
        fig,
        axC,
        "C",
        "The record rarely codes the circumstances patients report",
        dx=0.31,
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure2." + ext), dpi=400)
    plt.close(fig)
    print("wrote Figure2 to", OUT)


if __name__ == "__main__":
    main()
