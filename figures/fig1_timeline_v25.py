# -*- coding: utf-8 -*-
"""Figure 1 (v25): the income gradient and the Medicaid association on one
calendar axis, influenza before and after the pandemic and COVID-19 in between,
with the federal measures that acted on coverage and on income beneath.

The argument the figure carries: the income line does not move; the Medicaid
line steps down. Measures acting on coverage ran for about three years; income
support came as one-off payments, 2 spells of supplemental unemployment benefit,
and 6 months of advance child tax credit, and the income line did not move
through any of them.
The figure shows timing. It does not estimate a policy effect, and the legend
says so.

Reads results/figures/v25/Figure1_timeline_data.csv (every value traces to a
frozen run; see the source column). Writes Figure1.pdf/.png beside it.
Run from figures/:  ../.venv/bin/python fig1_timeline_v25.py
"""

import os
from datetime import date, timedelta

import matplotlib.dates as mdates
import pandas as pd
from style import COVID, FLU, GREY, INK, MM, RULE, apply_style, plt, sig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v25")
DATA = os.path.join(OUT, "Figure1_timeline_data.csv")

#  Federal measures. Coverage: FFCRA (Pub L 116-127); Consolidated Appropriations
#  Act, 2023; federally purchased vaccine until commercialization. Income: Treasury
#  (Economic Impact Payments; advance Child Tax Credit) and DOL (Federal Pandemic
#  Unemployment Compensation) official pages, accessed September 2026.
POLICY = [
    (
        "Medicaid continuous enrollment",
        [(date(2020, 3, 18), date(2023, 3, 31))],
        "coverage",
    ),
    (
        "Federally purchased COVID-19 vaccine",
        [(date(2020, 12, 11), date(2023, 9, 11))],
        "coverage",
    ),
    ("Emergency paid sick leave", [(date(2020, 4, 1), date(2020, 12, 31))], "income"),
    (
        "Supplemental unemployment benefit",
        [
            (date(2020, 3, 29), date(2020, 7, 31)),
            (date(2020, 12, 27), date(2021, 9, 6)),
        ],
        "income",
    ),
    (
        "Economic impact payments",
        [date(2020, 4, 10), date(2020, 12, 29), date(2021, 3, 12)],
        "income",
    ),
    ("Advance child tax credit", [(date(2021, 7, 15), date(2021, 12, 15))], "income"),
]
PCOL = {"coverage": "#5B7FA8", "income": "#B2352A"}
X0, X1 = date(2018, 9, 1), date(2024, 6, 1)
COVID_SPAN = (date(2020, 3, 1), date(2022, 6, 17))
PANEL = {
    "income_lt10k": "Household income below $10 000, adjusted for the other 5 social items",
    "medicaid": "Medicaid coverage beyond income and the other 4 social items",
}
PTEST = {
    "income_lt10k": ("Income × era:  COVID-19 P = .59;  influenza P = .91"),
    "medicaid": ("Insurance × era:  COVID-19 P = .002;  influenza P = .01"),
}


def mid(a, b):
    return a + (b - a) / 2


def panel(ax, d, term, letter):
    sub = d[d.term == term]
    ax.axvspan(*COVID_SPAN, color="#F4E4E1", zorder=0, lw=0)
    ax.axhline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    for _, r in sub.iterrows():
        a, b = r.start.date(), r.end.date()
        col = COVID if r.pathogen == "COVID-19" else FLU
        x = mid(a, b) - (
            timedelta(days=40)
            if (r.pathogen == "Influenza" and r.era.startswith("2 pandemic"))
            else timedelta(0)
        )
        faint = r.n_rows < 1000
        alpha = 0.45 if faint else 1.0
        ax.plot(
            [a, b],
            [r.aor, r.aor],
            color=col,
            lw=2.2,
            alpha=0.35 * alpha,
            solid_capstyle="butt",
            zorder=2,
        )
        ax.plot([x, x], [r.lo, r.hi], color=col, lw=1.4, alpha=alpha, zorder=3)
        f = sig(r.lo, r.hi)
        ax.plot(
            [x],
            [r.aor],
            marker="o",
            ms=6.5,
            color=col,
            mfc=col if f else "white",
            mew=1.6,
            alpha=alpha,
            zorder=4,
        )
    ax.set_yscale("log")
    ax.set_ylim(0.4, 4.6)
    ax.set_yticks([0.5, 0.75, 1, 1.5, 2, 3, 4])
    ax.set_yticklabels(["0.5", "0.75", "1", "1.5", "2", "3", "4"])
    ax.yaxis.set_minor_locator(plt.NullLocator())
    ax.set_ylabel("Adjusted odds ratio")
    ax.set_xlim(X0, X1)
    ax.text(
        -0.075,
        1.02,
        letter,
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    ax.text(
        0.0,
        1.02,
        PANEL[term],
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )
    ax.text(
        0.995,
        0.04,
        PTEST[term],
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=GREY,
    )


def main():
    apply_style()
    d = pd.read_csv(DATA, parse_dates=["start", "end"])
    fig = plt.figure(figsize=(180 * MM, 165 * MM))
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 0.72], hspace=0.38)
    axA = fig.add_subplot(gs[0])
    axB = fig.add_subplot(gs[1], sharex=axA)
    axC = fig.add_subplot(gs[2], sharex=axA)
    panel(axA, d, "income_lt10k", "A")
    panel(axB, d, "medicaid", "B")
    axB.text(
        0.005,
        0.97,
        "At or below 1: no excess beyond\nthe other social items (not protection)",
        transform=axB.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=GREY,
        style="italic",
    )
    for ax in (axA, axB):
        plt.setp(ax.get_xticklabels(), visible=False)
    axA.text(
        mid(*COVID_SPAN),
        3.9,
        "COVID-19 in All of Us (CDR v7)",
        ha="center",
        fontsize=9,
        color=COVID,
    )
    axA.text(date(2019, 7, 15), 3.9, "influenza", ha="center", fontsize=9, color=FLU)
    axA.text(date(2023, 7, 15), 3.9, "influenza", ha="center", fontsize=9, color=FLU)

    for i, (lab, spans, kind) in enumerate(POLICY):
        y = len(POLICY) - i
        for sp in spans:
            if isinstance(sp, tuple):
                axC.plot(
                    list(sp), [y, y], color=PCOL[kind], lw=5, solid_capstyle="butt"
                )
            else:
                axC.plot([sp], [y], marker="|", ms=9, mew=2.2, color=PCOL[kind])
        a = spans[0][0] if isinstance(spans[0], tuple) else spans[0]
        axC.text(
            a - timedelta(days=25),
            y,
            lab,
            va="center",
            ha="right",
            fontsize=8.5,
            color=INK,
        )
    axC.set_ylim(0.3, len(POLICY) + 0.7)
    axC.set_yticks([])
    axC.spines["left"].set_visible(False)
    axC.text(
        -0.075,
        1.02,
        "C",
        transform=axC.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axC.text(
        0.0,
        1.02,
        "Federal measures acting on coverage (blue) and on income (red)",
        transform=axC.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )
    axC.xaxis.set_major_locator(mdates.YearLocator())
    axC.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.text(
        0.5,
        0.005,
        "Filled marker: 95% CI excludes 1.0. Horizontal band: the calendar span of the era. "
        "Faint: fewer than 1000 matched rows. Ticks: payment dates.",
        ha="center",
        fontsize=8.5,
        color=GREY,
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure1." + ext), dpi=300, bbox_inches="tight")
    print("wrote Figure1 to", OUT)


if __name__ == "__main__":
    main()
