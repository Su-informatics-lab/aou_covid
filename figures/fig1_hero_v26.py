# -*- coding: utf-8 -*-
"""Figure 1 (v26, R9 visual-storytelling review): the income gap that did not thin.

A (setup)  Crude percentage hospitalized within 14 days by household income band,
           all eras, COVID-19 and influenza, with Wilson 95% CIs. The 2 bands the
           hero compares are named in their colours on the axis.
B (hero)   For each era, a floating bar from the crude percentage hospitalized at
           $35 000-99 999 (grey floor) to the percentage below $10 000 (navy top).
           Its height is the crude difference, printed inside; the thin line beside
           each bar spans the 95% CI of that difference, drawn from the floor. Eras
           are equally spaced, not on a calendar, so no era lines up with a policy
           date. The 2 pandemic influenza seasons (817 matched rows) are hatched.

Drawn at the final print width (180 mm). Nothing sits outside the axes grid,
and the canvas is saved as set, so the size cannot drift.
Reads working/v25/platform_03u/{covid,flu}_crude.csv.
Writes results/figures/v25/Figure1.{pdf,png}.
"""

import os

import matplotlib.patches as mpatches
import pandas as pd
from style import (
    COVID,
    FLU,
    INCOME,
    INCOME_TINT,
    MM,
    PT_BODY,
    PT_HEAD,
    PT_SMALL,
    REFG,
    apply_style,
    plt,
)

HERE = os.path.dirname(os.path.abspath(__file__))
CRUDE = os.path.join(HERE, "..", "working", "v25", "platform_03u")
OUT = os.path.join(HERE, "..", "results", "figures", "v25")
REF_TXT = "#666666"
LOW, REF = "<$10 000", "$35 000-99 999"
BANDS = ["<$10 000", "$10 000-24 999", "$25 000-34 999", "$35 000-99 999", ">=$100 000"]
BAND_LAB = ["<10", "10-25", "25-35", "35-100", "≥100"]
ERAS = {
    "flu": [
        ("1_pre", "2 seasons\nbefore"),
        ("2_pandemic", "2 pandemic\nseasons"),
        ("3_post", "2 seasons\nafter"),
    ],
    "covid": [
        ("1_pre_delta", "Pre-Delta"),
        ("2_delta", "Delta"),
        ("3_omicron", "Omicron"),
    ],
}
YMAX = 32


def row(d, era, level, var="income_band"):
    r = d[(d.variable == var) & (d.era == era) & (d.level == level)]
    assert len(r) == 1 and not bool(r.iloc[0].suppressed), (era, level)
    return r.iloc[0]


def setup_panel(ax, crude):
    for arm, col, mk in (("flu", FLU, "D"), ("covid", COVID, "o")):
        d = crude[arm]
        ys = [row(d, "all", b) for b in BANDS]
        x = list(range(len(BANDS)))
        ax.plot(x, [r.pct for r in ys], color=col, lw=1.4, zorder=2)
        for xi, r in zip(x, ys):
            ax.plot([xi, xi], [r.lo, r.hi], color=col, lw=1.0, zorder=2)
        ax.plot(x, [r.pct for r in ys], ls="none", marker=mk, ms=5, color=col, zorder=3)
        m = row(d, "all", "Missing")
        xm = 5.15 if arm == "flu" else 5.45
        ax.plot([xm, xm], [m.lo, m.hi], color=col, lw=1.0)
        ax.plot(
            [xm],
            [m.pct],
            marker="D" if arm == "flu" else "o",
            ms=4.5,
            color=col,
            mfc=col,
            zorder=3,
        )
    ax.text(
        1.3,
        28.6,
        "Influenza",
        color=FLU,
        fontsize=PT_BODY,
        fontweight="bold",
        ha="left",
        va="center",
    )
    ax.text(
        0.3,
        13.2,
        "COVID-19",
        color=COVID,
        fontsize=PT_BODY,
        fontweight="bold",
        ha="left",
        va="center",
    )
    ax.set_xticks(list(range(len(BANDS))) + [5.3])
    ax.set_xticklabels(BAND_LAB + ["Not\nreported"], fontsize=PT_SMALL)
    for i, t in enumerate(ax.get_xticklabels()):
        if i == 0:
            t.set_color(INCOME)
            t.set_fontweight("bold")
        elif i == 3:
            t.set_color(REF_TXT)
            t.set_fontweight("bold")
    ax.set_xlim(-0.5, 5.8)
    ax.set_xlabel("Household income, $ thousands", fontsize=PT_BODY)
    ax.set_ylabel("Hospitalized within 14 days, % of infected", fontsize=PT_BODY)


def hero_facet(ax, d, eras, title, tcol):
    w = 0.5
    for x, (era, lab) in enumerate(eras):
        lo, hi = row(d, era, REF), row(d, era, LOW)
        weak = era == "2_pandemic"
        floor, top, gap = lo.pct, hi.pct, hi.rd
        if weak:
            ax.add_patch(
                mpatches.Rectangle(
                    (x - w / 2, floor),
                    w,
                    gap,
                    facecolor="white",
                    edgecolor=INCOME_TINT,
                    hatch="////",
                    lw=0,
                    zorder=1,
                )
            )
        else:
            ax.add_patch(
                mpatches.Rectangle(
                    (x - w / 2, floor),
                    w,
                    gap,
                    facecolor=INCOME_TINT,
                    edgecolor="none",
                    zorder=1,
                )
            )
        ls = (0, (3, 2)) if weak else "-"
        ax.plot(
            [x - w / 2, x + w / 2], [top, top], color=INCOME, lw=2.0, ls=ls, zorder=3
        )
        ax.plot(
            [x - w / 2, x + w / 2], [floor, floor], color=REFG, lw=2.0, ls=ls, zorder=3
        )
        xw = x + w / 2 + 0.1
        ax.plot(
            [xw, xw],
            [floor + hi.rd_lo, floor + hi.rd_hi],
            color=INCOME,
            lw=0.9,
            zorder=2,
        )
        for yy in (floor + hi.rd_lo, floor + hi.rd_hi):
            ax.plot([xw - 0.04, xw + 0.04], [yy, yy], color=INCOME, lw=0.9, zorder=2)
        ax.text(
            x,
            floor + gap / 2,
            "%.1f" % gap,
            ha="center",
            va="center",
            color=INCOME,
            fontsize=PT_HEAD + 1,
            fontweight="normal" if weak else "bold",
            zorder=4,
        )
        ax.text(
            x,
            top + 0.6,
            "%.1f%%" % top,
            ha="center",
            va="bottom",
            color=INCOME,
            fontsize=PT_SMALL,
        )
        ax.text(
            x,
            floor - 0.6,
            "%.1f%%" % floor,
            ha="center",
            va="top",
            color=REF_TXT,
            fontsize=PT_SMALL,
        )
        if weak:
            ax.text(
                x,
                floor - 2.4,
                "few data: %d and\n%d person-seasons" % (hi.n, lo.n),
                ha="center",
                va="top",
                color=REF_TXT,
                fontsize=PT_SMALL,
                style="italic",
            )
    ax.set_xticks(range(len(eras)))
    ax.set_xticklabels([lab for _, lab in eras], fontsize=PT_SMALL)
    ax.set_xlim(-0.6, len(eras) - 0.3)
    ax.tick_params(axis="x", length=0)
    ax.set_title(title, color=tcol, fontsize=PT_HEAD, fontweight="bold", pad=4)


def main():
    apply_style()
    plt.rcParams.update({"xtick.labelsize": PT_SMALL, "ytick.labelsize": PT_SMALL})
    crude = {
        a: pd.read_csv(os.path.join(CRUDE, "%s_crude.csv" % a))
        for a in ("covid", "flu")
    }
    fig = plt.figure(figsize=(180 * MM, 96 * MM))
    gs = fig.add_gridspec(
        1,
        3,
        width_ratios=[1.0, 1.0, 1.0],
        wspace=0.18,
        left=0.075,
        right=0.99,
        top=0.80,
        bottom=0.15,
    )
    axA = fig.add_subplot(gs[0])
    axF = fig.add_subplot(gs[1])
    axC = fig.add_subplot(gs[2], sharey=axF)
    setup_panel(axA, crude)
    hero_facet(axF, crude["flu"], ERAS["flu"], "Influenza", FLU)
    hero_facet(axC, crude["covid"], ERAS["covid"], "COVID-19", COVID)
    om_lo, om_hi = row(crude["covid"], "3_omicron", REF), row(
        crude["covid"], "3_omicron", LOW
    )
    axC.set_xlim(-0.6, 3.5)
    axC.text(
        2.47,
        om_hi.pct,
        "Income\n<\\$10 000",
        color=INCOME,
        fontsize=PT_SMALL,
        fontweight="bold",
        va="center",
    )
    axC.text(
        2.47,
        om_lo.pct,
        "\\$35 000-\n99 999",
        color=REF_TXT,
        fontsize=PT_SMALL,
        fontweight="bold",
        va="center",
    )
    axC.text(
        2.47,
        (om_lo.pct + om_hi.pct) / 2,
        "gap, with\nits 95% CI",
        color=INCOME,
        fontsize=PT_SMALL,
        va="center",
    )
    for ax in (axA, axF, axC):
        ax.set_ylim(0, YMAX)
        ax.set_yticks([0, 10, 20, 30])
    plt.setp(axC.get_yticklabels(), visible=False)
    axC.tick_params(axis="y", length=0)
    axC.spines["left"].set_visible(False)
    fig.subplots_adjust(wspace=0.18)
    # shift the hero pair right to open a gap after the setup panel
    for ax, dx in ((axF, 0.035), (axC, 0.0)):
        p = ax.get_position()
        ax.set_position(
            [p.x0 + dx, p.y0, p.width - (0.035 if ax is axF else 0), p.height]
        )
    pa, pf, pc = axA.get_position(), axF.get_position(), axC.get_position()
    fig.text(pa.x0 - 0.06, 0.965, "A", fontsize=10, fontweight="bold", va="top")
    fig.text(
        pa.x0,
        0.965,
        "Crude hospitalization by income",
        fontsize=PT_HEAD,
        fontweight="bold",
        va="top",
    )
    fig.text(pf.x0 - 0.035, 0.965, "B", fontsize=10, fontweight="bold", va="top")
    fig.text(
        pf.x0,
        0.965,
        "The crude gap stayed 10 to 12 points in every era",
        fontsize=PT_HEAD,
        fontweight="bold",
        va="top",
    )
    fig.text(
        pf.x0,
        0.905,
        "while the middle-income level ranged from 7.2% to 16.2%",
        fontsize=PT_BODY,
        color=REF_TXT,
        va="top",
    )
    os.makedirs(OUT, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure1." + ext), dpi=400)
    plt.close(fig)
    print("wrote Figure1 to", OUT)


if __name__ == "__main__":
    main()
