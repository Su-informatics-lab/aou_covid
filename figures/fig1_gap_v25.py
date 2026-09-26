# -*- coding: utf-8 -*-
"""Figure 1 (v25, R5p redesign): the absolute income gap, and the two adjusted
associations on one axis.

What the eye should see in 3 seconds:
  A  In every era and in both viruses, infected participants with household
     income below $10 000 were hospitalized about 10 percentage points more
     often than those with $35 000 to $99 999, while the level of risk itself
     moved (crude proportions, eTable 21).
  B  Adjusted for the other social items, the income association stayed near
     1.5 while the Medicaid association fell to or below 1 after the Delta wave
     began (joint-model AORs; eTable 8 and the influenza within-period refits);
     in COVID-19 the 2 era contrasts differed in 1 model (eTable 22).

The former Figure 1, with the federal-measures timeline, is eFigure 7.
Colour follows style.py: cool = our estimates (navy = lowest income; teal =
middle income in A); Medicaid, a second estimate on the same axis, is purple;
pathogen is the marker (circle COVID-19, diamond influenza) and the shaded
field is the COVID-19 period. Filled marker in B: 95% CI excludes 1.

Reads results/figures/v25/Figure1_timeline_data.csv (era spans and AORs) and
working/v25/platform_03u/{covid,flu}_crude.csv. Writes results/figures/v25/Figure1.{pdf,png}.
Run from figures/:  ../.venv/bin/python fig1_gap_v25.py
"""

import os
from datetime import date, timedelta

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from style import COVID, FLU, GREY, INK, MM, NAVY, RULE, TEAL, apply_style, plt, sig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v25")
SPANS = os.path.join(OUT, "Figure1_timeline_data.csv")
CRUDE = os.path.join(HERE, "..", "working", "v25", "platform_03u")
PURPLE = "#7B5EA7"
X0, X1 = date(2018, 9, 1), date(2024, 6, 1)
COVID_SPAN = (date(2020, 3, 1), date(2022, 6, 17))
ERA_KEY = {
    ("COVID-19", "Pre-Delta"): "1_pre_delta",
    ("COVID-19", "Delta"): "2_delta",
    ("COVID-19", "Omicron"): "3_omicron",
    ("Influenza", "2 seasons before the pandemic"): "1_pre",
    ("Influenza", "2 pandemic seasons"): "2_pandemic",
    ("Influenza", "2 seasons after influenza returned"): "3_post",
}


def mid(a, b):
    return a + (b - a) / 2


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (c - h), 100 * (c + h)


def shade(ax):
    ax.axvspan(*COVID_SPAN, color="#F4E4E1", zorder=0, lw=0)
    ax.set_xlim(X0, X1)


def main():
    apply_style()
    sp = pd.read_csv(SPANS, parse_dates=["start", "end"])
    crude = {
        a: pd.read_csv(os.path.join(CRUDE, "%s_crude.csv" % a))
        for a in ("covid", "flu")
    }
    fig = plt.figure(figsize=(180 * MM, 205 * MM))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 0.75, 1.0], hspace=0.42)
    axA = fig.add_subplot(gs[0])
    axG = fig.add_subplot(gs[1], sharex=axA)
    axB = fig.add_subplot(gs[2], sharex=axA)

    # ---- A: crude proportions, lowest vs middle income, with the gap labelled
    shade(axA)
    eras = sp[sp.term == "income_lt10k"]
    for _, e in eras.iterrows():
        a, b = e.start.date(), e.end.date()
        arm = "covid" if e.pathogen == "COVID-19" else "flu"
        c = crude[arm]
        key = ERA_KEY[(e.pathogen, e.era)]
        mk = "o" if arm == "covid" else "D"
        faint = e.n_rows < 1000
        al = 0.45 if faint else 1.0
        x = mid(a, b) - (timedelta(days=40) if faint else timedelta(0))
        vals = {}
        for lev, col in (("<$10 000", NAVY), ("$35 000-99 999", TEAL)):
            r = c[
                (c.variable == "income_band") & (c.era == key) & (c.level == lev)
            ].iloc[0]
            lo, hi = wilson(r.hosp, r.n)
            vals[lev] = r.pct
            axA.plot(
                [a, b],
                [r.pct, r.pct],
                color=col,
                lw=2.2,
                alpha=0.3 * al,
                solid_capstyle="butt",
                zorder=2,
            )
            axA.plot([x, x], [lo, hi], color=col, lw=1.3, alpha=al, zorder=3)
            axA.plot(
                [x], [r.pct], marker=mk, ms=6.5, color=col, mew=1.2, alpha=al, zorder=4
            )
        g = vals["<$10 000"] - vals["$35 000-99 999"]
        if faint:
            continue  # pandemic influenza: points shown faint, gap not labelled (817 rows)
        axA.annotate(
            "",
            xy=(x + timedelta(days=22), vals["<$10 000"]),
            xytext=(x + timedelta(days=22), vals["$35 000-99 999"]),
            arrowprops=dict(arrowstyle="-", color=GREY, lw=1.0, alpha=al),
        )
        axA.text(
            x + timedelta(days=32),
            (vals["<$10 000"] + vals["$35 000-99 999"]) / 2,
            "+%.1f" % g,
            va="center",
            ha="left",
            fontsize=9,
            color=INK,
            alpha=al,
            fontweight="bold",
        )
    axA.set_ylim(0, 34)
    axA.set_ylabel("Hospitalized, % of infected")
    axA.text(
        -0.075,
        1.03,
        "A",
        transform=axA.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axA.text(
        0.0,
        1.03,
        "Crude hospitalization: the gap between income groups stays near 10 points",
        transform=axA.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )
    axA.text(
        mid(*COVID_SPAN),
        31.5,
        "COVID-19 in All of Us (CDR v7)",
        ha="center",
        fontsize=9,
        color=COVID,
    )
    axA.text(date(2019, 7, 15), 31.5, "influenza", ha="center", fontsize=9, color=FLU)
    axA.text(date(2023, 7, 15), 31.5, "influenza", ha="center", fontsize=9, color=FLU)
    h = [
        plt.Line2D(
            [], [], color=NAVY, marker="o", lw=0, label=r"Income below \$10 000"
        ),
        plt.Line2D(
            [], [], color=TEAL, marker="o", lw=0, label=r"Income \$35 000 to \$99 999"
        ),
        plt.Line2D([], [], color=GREY, lw=1.0, label="Gap, percentage points"),
    ]
    axA.legend(
        handles=h, loc="lower left", ncol=3, fontsize=8.5, bbox_to_anchor=(0.0, -0.02)
    )
    plt.setp(axA.get_xticklabels(), visible=False)

    # ---- B: the crude gaps themselves, income vs insurance
    shade(axG)
    axG.axhline(0, color=RULE, lw=0.9, zorder=1)
    goff = {"income": -timedelta(days=18), "insurance": timedelta(days=18)}
    for _, e in eras.iterrows():
        a, b = e.start.date(), e.end.date()
        arm = "covid" if e.pathogen == "COVID-19" else "flu"
        c = crude[arm]
        key = ERA_KEY[(e.pathogen, e.era)]
        mk = "o" if arm == "covid" else "D"
        faint = e.n_rows < 1000
        al = 0.45 if faint else 1.0
        for var, lev, col in (
            ("income_band", "<$10 000", NAVY),
            ("insurance", "Medicaid", PURPLE),
        ):
            r = c[(c.variable == var) & (c.era == key) & (c.level == lev)].iloc[0]
            if pd.isna(r.rd):
                continue  # reference cell suppressed (influenza insurance, before and pandemic seasons)
            x = (
                mid(a, b)
                + goff["income" if var == "income_band" else "insurance"]
                - (timedelta(days=40) if faint else timedelta(0))
            )
            axG.plot(
                [a, b],
                [r.rd, r.rd],
                color=col,
                lw=2.2,
                alpha=0.3 * al,
                solid_capstyle="butt",
                zorder=2,
            )
            axG.plot([x, x], [r.rd_lo, r.rd_hi], color=col, lw=1.3, alpha=al, zorder=3)
            axG.plot([x], [r.rd], marker=mk, ms=6.5, color=col, alpha=al, zorder=4)
    axG.set_ylim(-1, 21)
    axG.set_ylabel("Gap, points")
    axG.text(
        -0.075,
        1.03,
        "B",
        transform=axG.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axG.text(
        0.0,
        1.03,
        "Crude gaps: income holds, the Medicaid-employer gap narrows",
        transform=axG.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )
    h = [
        plt.Line2D(
            [],
            [],
            color=NAVY,
            marker="o",
            lw=0,
            label=r"Income below \$10 000 minus \$35 000 to \$99 999",
        ),
        plt.Line2D(
            [],
            [],
            color=PURPLE,
            marker="o",
            lw=0,
            label="Medicaid minus employer insurance",
        ),
    ]
    axG.legend(handles=h, loc="upper right", ncol=1, fontsize=8.5)
    plt.setp(axG.get_xticklabels(), visible=False)

    # ---- C: joint-model AORs, income and Medicaid on one log axis
    shade(axB)
    axB.axhline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    off = {"income_lt10k": -timedelta(days=18), "medicaid": timedelta(days=18)}
    for term, col in (("income_lt10k", NAVY), ("medicaid", PURPLE)):
        for _, r in sp[sp.term == term].iterrows():
            a, b = r.start.date(), r.end.date()
            faint = r.n_rows < 1000
            al = 0.45 if faint else 1.0
            x = mid(a, b) + off[term] - (timedelta(days=40) if faint else timedelta(0))
            mk = "o" if r.pathogen == "COVID-19" else "D"
            if pd.isna(r.aor):
                # withheld: employer reference below 20 cases (03x cell audit)
                axB.text(
                    x,
                    3.4,
                    "Medicaid withheld (<20)",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color=col,
                    alpha=0.9,
                )
                continue
            axB.plot(
                [a, b],
                [r.aor, r.aor],
                color=col,
                lw=2.2,
                alpha=0.3 * al,
                solid_capstyle="butt",
                zorder=2,
            )
            axB.plot([x, x], [r.lo, r.hi], color=col, lw=1.3, alpha=al, zorder=3)
            f = sig(r.lo, r.hi)
            axB.plot(
                [x],
                [r.aor],
                marker=mk,
                ms=6.5,
                color=col,
                mfc=col if f else "white",
                mew=1.4,
                alpha=al,
                zorder=4,
            )
    axB.set_yscale("log")
    axB.set_ylim(0.4, 20)
    axB.set_yticks([0.5, 0.75, 1, 1.5, 2, 3, 4])
    axB.set_yticklabels(["0.5", "0.75", "1", "1.5", "2", "3", "4"])
    axB.yaxis.set_minor_locator(plt.NullLocator())
    axB.set_ylabel("Adjusted odds ratio (log scale)")
    axB.text(
        -0.075,
        1.03,
        "C",
        transform=axB.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axB.text(
        0.0,
        1.03,
        "Adjusted for the other social items: income holds, Medicaid falls",
        transform=axB.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )
    axB.text(
        0.99,
        0.76,
        "COVID-19, from 1 model with both era interactions (not the plotted\n"
        "estimates): income ROR / Medicaid ROR, Omicron vs pre-Delta, 2.27 (95% CI, 1.38-3.74)",
        transform=axB.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        color=INK,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RULE, lw=0.6),
    )
    axB.text(
        0.995,
        0.03,
        "Medicaid at or below 1: no excess beyond the other social items (not protection)",
        transform=axB.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=GREY,
        style="italic",
    )
    h = [
        plt.Line2D(
            [], [], color=NAVY, marker="o", lw=0, label=r"Income below \$10 000"
        ),
        plt.Line2D(
            [], [], color=PURPLE, marker="o", lw=0, label="Medicaid (vs employer)"
        ),
        plt.Line2D([], [], color=GREY, marker="o", lw=0, label="COVID-19"),
        plt.Line2D([], [], color=GREY, marker="D", lw=0, label="Influenza"),
        plt.Line2D(
            [],
            [],
            color=GREY,
            marker="o",
            lw=0,
            mfc="white",
            label="Open: 95% CI includes 1",
        ),
    ]
    axB.legend(
        handles=h, loc="upper left", ncol=3, fontsize=8.2, bbox_to_anchor=(0.0, 1.0)
    )
    axB.xaxis.set_major_locator(mdates.YearLocator())
    axB.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.text(
        0.5,
        0.005,
        "Horizontal band: the calendar span of each era. Vertical bars: 95% CIs.\n"
        "Faint: pandemic influenza seasons (fewer than 1000 matched rows). B omits influenza insurance gaps whose employer reference cell is suppressed; C withholds pandemic-season influenza Medicaid (reference <20 cases).",
        ha="center",
        fontsize=8,
        color=GREY,
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure1." + ext), dpi=300, bbox_inches="tight")
    print("wrote Figure1 to", OUT)


if __name__ == "__main__":
    main()
