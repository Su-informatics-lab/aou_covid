# -*- coding: utf-8 -*-
"""eFigure 9 (2026-09-29, Jing Su on Figure 2A): income below $10 000 and Medicaid overlap.

A  Area-proportional Euler diagrams of matched participants who reported income, COVID-19
   and influenza: income below $10 000, Medicaid, and both (distinct participants, observed
   values). Only the all-participant counts are drawn; the case rows are not displayed
   because, for influenza, they could be differenced against Table 1 (platform_r12/lisu).
B  COVID-19 joint categories against 1 reference ($35 000-99 999 and employer insurance),
   as recommended by Knol & VanderWeele (Int J Epidemiol 2012): adjusted odds ratios by
   wave from the joint model plus an income-below-$10 000-and-Medicaid indicator with wave
   interactions (03ab_li_su.R, PART=JOINT4; model-based variance). The category income below
   $10 000 with employer insurance holds 20 or fewer cases in every wave and is withheld, as
   is the $35 000-99 999 Medicaid estimate in Delta.
Reads working/v25/platform_r12/lisu/{xtab_covid,xtab_flu,joint4_covid_model}.csv.
Writes submission_v25/04_figures/supplement/eFigure9.{pdf,png}.
"""

import os

import numpy as np
import pandas as pd
from matplotlib.patches import Circle
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
    apply_style,
    plt,
    sig,
)

HERE = os.path.dirname(os.path.abspath(__file__))
LISU = os.path.join(HERE, "..", "working", "v25", "platform_r12", "lisu")
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
REF_TXT = "#666666"
JOINT = "#6E4C8F"


def lens(r1, r2, d):
    """Area of the intersection of 2 circles with radii r1, r2 and centre distance d."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    b = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    c = 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    return a + b - c


def euler(ax, x0, y0, n_low, n_mcd, n_both, n_all, title, scale):
    r1, r2 = np.sqrt(n_low / np.pi) * scale, np.sqrt(n_mcd / np.pi) * scale
    target = n_both * scale**2
    lo, hi = abs(r1 - r2), r1 + r2
    for _ in range(80):  # bisection: overlap area decreases with distance
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if lens(r1, r2, mid) > target else (lo, mid)
    d = (lo + hi) / 2
    c1, c2 = (x0 - d / 2, y0), (x0 + d / 2, y0)
    ax.add_patch(Circle(c1, r1, fc=INCOME, alpha=0.30, ec=INCOME, lw=1.0))
    ax.add_patch(Circle(c2, r2, fc=MEDICAID, alpha=0.30, ec=MEDICAID, lw=1.0))
    ax.text(
        x0,
        y0 + max(r1, r2) + 0.10,
        title,
        ha="center",
        va="bottom",
        fontsize=PT_BODY,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        c1[0] - r1 - 0.04,
        y0,
        "Income\n<\\$10 000\n%s" % f"{n_low:,}",
        ha="right",
        va="center",
        fontsize=PT_SMALL,
        color=INCOME,
    )
    ax.text(
        c2[0] + r2 + 0.04,
        y0,
        "Medicaid\n%s" % f"{n_mcd:,}",
        ha="left",
        va="center",
        fontsize=PT_SMALL,
        color=MEDICAID,
    )
    ax.text(
        (c1[0] + r1 + c2[0] - r2) / 2,
        y0,
        "both\n%s" % f"{n_both:,}",
        ha="center",
        va="center",
        fontsize=PT_SMALL,
        color=INK,
    )
    ax.text(
        x0,
        y0 - max(r1, r2) - 0.08,
        "%d%% of those below \\$10 000 had Medicaid;\n%d%% of Medicaid enrollees were below \\$10 000\n(of %s who reported income)"
        % (round(100 * n_both / n_low), round(100 * n_both / n_mcd), f"{n_all:,}"),
        ha="center",
        va="top",
        fontsize=PT_SMALL,
        color=REF_TXT,
    )


def main():
    apply_style()
    plt.rcParams.update({"xtick.labelsize": PT_SMALL, "ytick.labelsize": PT_SMALL})
    x = {
        a: pd.read_csv(os.path.join(LISU, "xtab_%s.csv" % a)) for a in ("covid", "flu")
    }
    j = pd.read_csv(os.path.join(LISU, "joint4_covid_model.csv"))
    fig = plt.figure(figsize=(180 * MM, 110 * MM))
    axA = fig.add_axes([0.02, 0.04, 0.40, 0.84])
    axA.set_xlim(0, 1)
    axA.set_ylim(0, 1.25)
    axA.set_aspect("equal")
    axA.axis("off")
    for arm, y0, title in (("covid", 0.93, "COVID-19"), ("flu", 0.33, "Influenza")):
        r = x[arm][x[arm].group == "all matched participants"].iloc[0]
        low = int(r.below10k_and_medicaid) + int(r.below10k_not_medicaid)
        mcd = int(r.below10k_and_medicaid) + int(r.medicaid_not_below10k)
        euler(
            axA,
            0.5,
            y0,
            low,
            mcd,
            int(r.below10k_and_medicaid),
            int(r.reported_income),
            title,
            scale=0.0042,
        )

    axB = fig.add_axes([0.58, 0.22, 0.27, 0.64])
    groups = (
        ("<$10k, Medicaid", "Income <\\$10 000 and Medicaid", JOINT),
        ("$35-99k, Medicaid", "\\$35 000-99 999 and Medicaid", MEDICAID),
        ("<$10k, employer", "Income <\\$10 000 and employer", INCOME),
    )
    eras = (("pre_delta", "Pre-Delta"), ("delta", "Delta"), ("omicron", "Omicron"))
    y, yt, yl = 0.0, [], []
    for q, lab, col in groups:
        axB.text(
            0.0,
            y,
            lab,
            transform=axB.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=PT_SMALL,
            fontweight="bold",
            color=col,
            bbox=dict(fc="white", ec="none", pad=0.5),
            zorder=4,
        )
        y -= 0.8
        if q == "<$10k, employer":
            yt.append(y)
            yl.append("every wave")
            axB.text(
                1.0,
                y,
                "withheld (\u226420 cases)",
                ha="center",
                va="center",
                fontsize=6.5,
                color=REF_TXT,
                bbox=dict(fc="white", ec=REFG, ls=(0, (2, 2)), lw=0.8, pad=1.5),
            )
            y -= 0.8
            continue
        for e, elab in eras:
            s = j[(j.quantity == q) & (j.era == e)].iloc[0]
            yt.append(y)
            yl.append(elab)
            if pd.isna(s["or"]):
                axB.text(
                    1.0,
                    y,
                    "withheld (≤20 cases)",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color=REF_TXT,
                    bbox=dict(fc="white", ec=REFG, ls=(0, (2, 2)), lw=0.8, pad=1.5),
                )
            else:
                f = sig(s.lo, s.hi)
                axB.plot([s.lo, s.hi], [y, y], color=col, lw=1.1)
                axB.plot(
                    s["or"], y, "o", ms=4.2, mfc=col if f else "white", mec=col, mew=1.1
                )
                axB.text(
                    1.03,
                    y,
                    "%.2f (%.2f-%.2f)" % (s["or"], s.lo, s.hi),
                    transform=axB.get_yaxis_transform(),
                    ha="left",
                    va="center",
                    fontsize=PT_SMALL,
                    color=INK,
                )
            y -= 0.8
        y -= 0.3
    axB.axvline(1, color=RULE, lw=0.9, ls=(0, (4, 3)))
    axB.set_xscale("log")
    axB.set_xticks((0.5, 0.75, 1, 1.5, 2, 3))
    axB.set_xticklabels(["0.5", "0.75", "1", "1.5", "2", "3"])
    axB.minorticks_off()
    axB.set_xlim(0.45, 3.4)
    axB.set_yticks(yt)
    axB.set_yticklabels(yl, fontsize=PT_SMALL)
    axB.tick_params(axis="y", length=0)
    axB.spines["left"].set_visible(False)
    axB.set_ylim(y + 0.5, 0.6)
    axB.set_xlabel(
        "Odds ratio vs \\$35 000-99 999 and employer (log scale)", fontsize=PT_BODY
    )
    r1 = j[
        (j.quantity == "Medicaid ROR, within $35-99k") & (j.era == "omicron/pre_delta")
    ].iloc[0]
    r2 = j[
        (j.quantity == "income <$10k ROR, within Medicaid")
        & (j.era == "omicron/pre_delta")
    ].iloc[0]
    fig.text(
        0.47,
        0.02,
        "Omicron / pre-Delta: Medicaid vs employer within \\$35 000-99 999, %.2f (%.2f-%.2f);\n"
        "income <\\$10 000 vs \\$35 000-99 999 within Medicaid, %.2f (%.2f-%.2f)"
        % (r1["or"], r1.lo, r1.hi, r2["or"], r2.lo, r2.hi),
        fontsize=PT_SMALL,
        color=REF_TXT,
        va="bottom",
    )
    fig.text(0.02, 0.96, "A", fontsize=10, fontweight="bold", va="top")
    fig.text(
        0.05,
        0.96,
        "Overlap among matched participants",
        fontsize=PT_HEAD,
        fontweight="bold",
        va="top",
    )
    fig.text(0.53, 0.96, "B", fontsize=10, fontweight="bold", va="top")
    fig.text(
        0.56,
        0.96,
        "COVID-19: joint categories, by wave",
        fontsize=PT_HEAD,
        fontweight="bold",
        va="top",
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "eFigure9." + ext), dpi=400)
    plt.close(fig)
    print("wrote eFigure9 to", OUT)


if __name__ == "__main__":
    main()
