# -*- coding: utf-8 -*-
"""eFigure 6 (v25; the former Figure 1, moved to the supplement after the
R5p review): the income gradient and the Medicaid association on one
calendar axis, influenza before and after the pandemic and COVID-19 in between,
with the federal measures that acted on coverage and on income beneath.

The argument the figure carries: the income line does not move; the Medicaid
line steps down. Measures acting on coverage ran for about three years; income
support came as one-off payments, 2 spells of supplemental unemployment benefit,
and 6 months of advance child tax credit, and the income line did not move
through any of them.
The figure shows timing. It does not estimate a policy effect, and the legend
says so.

2026-09-28: panel C now shares the calendar axis of A and B (same limits, same
horizontal extent, ticks aligned), so each estimate's era reads straight down to
the measures in force. A strip above A names the COVID-19 waves (definitions as
in Methods: pre-Delta to June 30, 2021; Delta July 1 to December 18, 2021;
Omicron December 19, 2021 to the July 1, 2022 cutoff), and thin dashed lines at
the 2 wave boundaries and the cutoff run through A-C. The COVID-19 shading ends
at the cutoff. Influenza periods are unchanged.

2026-09-29 (R12): the wave boundaries follow the CDC COVID-NET variant-predominance
periods (Taylor et al, MMWR 2022;71:466-473): Delta from July 1, 2021 and Omicron
from December 19, 2021 (previously June 15 and December 15, 2021, without a source).
The 2 era-test P values printed in A and B are literals, updated from the rerun
(platform_r12/jno_v24/R2_wave_tests.csv: income x wave P = .74, insurance x wave
P = .003; influenza unchanged).

Reads results/figures/v25/Figure1_timeline_data.csv (every value traces to a
frozen run; see the source column). Writes
submission_v25/04_figures/supplement/eFigure6.{pdf,png}.
Run from figures/:  ../.venv/bin/python efig6_calendar.py
"""

import os
from datetime import date, timedelta

import matplotlib.dates as mdates
import pandas as pd
from style import COVID, FLU, GREY, INK, MM, RULE, TXT_GREY, apply_style, plt, sig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(
    HERE, "..", "results", "figures", "v25", "Figure1_timeline_data.csv"
)
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")

#  Federal measures (each date checked 2026-09-29 against the source cited in the
#  eFigure 6 legend; eReferences e38-e48):
#    Medicaid continuous enrollment: enrolled "as of or after March 18, 2020"
#      (42 CFR 433.400(c)(2)); condition ended March 31, 2023 (CMS SHO# 23-002,
#      CAA 2023 section 5131).
#    Federally purchased vaccine: first EUA December 11, 2020 (Oliver et al, MMWR
#      2020;69:1922-1924); bivalent mRNA vaccines no longer authorized as of
#      September 11, 2023, with vaccines moving from federal procurement to the
#      commercial market in fall 2023 (Regan et al, MMWR 2023;72:1140-1146).
#    Emergency paid sick leave: operational April 1, 2020, expired December 31,
#      2020 (DOL WHD temporary rule, 85 FR 19326).
#    FPUC $600: first payable week the week ending April 4, 2020, so weeks of
#      unemployment from March 29; not payable for any week ending after July 31,
#      2020 (UIPL 15-20). FPUC $300: weeks beginning after December 26, 2020
#      (Continued Assistance Act) and ending on or before September 6, 2021 (ARPA
#      section 9013; UIPL 15-20 Change 4).
#    Economic impact payments: IRS began issuing round 1 on April 10, 2020, and
#      issued round 2 on December 29, 2020 (TIGTA 2021-46-034); round 3 began
#      processing Friday, March 12, 2021 (Treasury press release JY0063).
#    Advance child tax credit: payments July 15 to December 15, 2021 (IRS
#      Publication 5537).
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
PCOL = {"coverage": "#8C8C8C", "income": "#8C8C8C"}  # R9: grey, timing only
X0, X1 = date(2018, 9, 1), date(2024, 6, 1)
CUTOFF = date(2022, 7, 1)  # COVID-19 arm data cutoff (CDR v7)
COVID_SPAN = (date(2020, 3, 1), CUTOFF)
#  COVID-19 waves, as defined in Methods (the data file's era spans agree)
WAVES = [
    ("COVID-19, pre-Delta", date(2020, 3, 1), date(2021, 6, 30)),
    ("Delta", date(2021, 7, 1), date(2021, 12, 18)),
    ("Omicron", date(2021, 12, 19), CUTOFF),
]
#  dashed lines: start of Delta, start of Omicron, and the data cutoff
BOUNDS = [
    (date(2021, 7, 1), "Jul 1\n2021"),
    (date(2021, 12, 19), "Dec 19\n2021"),
    (CUTOFF, "Jul 1, 2022\n(cutoff)"),
]
FLU_LAB = [(date(2019, 7, 16), "influenza"), (date(2023, 7, 16), "influenza")]
SHADE = "#F4E4E1"
#  the pandemic-season influenza marker (and the withheld box) sits left of its
#  period's midpoint so it clears the COVID-19 markers; 130 days also keeps the
#  box and the marker clear of the July 1, 2021 wave line
PAND_OFFSET = 130
WAVE_LINE = dict(color=COVID, lw=0.6, ls=(0, (2.5, 2)), alpha=0.7, zorder=0.5)
PANEL = {
    "income_lt10k": "Household income below $10 000, adjusted for the other 5 social items",
    "medicaid": "Medicaid coverage beyond income and the other 4 social items",
}
PTEST = {
    #  2 lines, top right: on the shared axis 1 line would cross the cutoff line
    "income_lt10k": ("Income × era:\nCOVID-19 P = .74;  influenza P = .91"),
    "medicaid": ("Insurance × era:\nCOVID-19 P = .003;  influenza P = .01*"),
}


def mid(a, b):
    return a + (b - a) / 2


def panel(ax, d, term, letter, title_ax=None):
    sub = d[d.term == term]
    ax.axvspan(*COVID_SPAN, color=SHADE, zorder=0, lw=0)
    for x, _ in BOUNDS:
        ax.axvline(x, **WAVE_LINE)
    ax.axhline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    for _, r in sub.iterrows():
        a, b = r.start.date(), r.end.date()
        col = COVID if r.pathogen == "COVID-19" else FLU
        x = mid(a, b) - (
            timedelta(days=PAND_OFFSET)
            if (r.pathogen == "Influenza" and r.era.startswith("2 pandemic"))
            else timedelta(0)
        )
        if pd.isna(r.aor):
            # withheld: reference group 20 or fewer cases (03x); one mark used in every figure
            xm = mid(a, b) - timedelta(days=PAND_OFFSET)
            ax.add_patch(
                plt.Rectangle(
                    (mdates.date2num(xm) - 75, 0.78),
                    150,
                    0.52,
                    fill=False,
                    ls=(0, (2, 2)),
                    lw=0.8,
                    edgecolor=GREY,
                    zorder=3,
                )
            )
            ax.text(
                xm,
                1.0,
                "withheld\n(\u226420)",
                ha="center",
                va="center",
                fontsize=6.5,
                color=TXT_GREY,
                zorder=4,
            )
            continue
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
    tax = title_ax if title_ax is not None else ax
    tax.text(
        -0.075,
        1.06 if title_ax is not None else 1.02,
        letter,
        transform=tax.transAxes,
        fontsize=10,
        fontweight="bold",
        va="bottom",
    )
    tax.text(
        0.0,
        1.06 if title_ax is not None else 1.02,
        PANEL[term],
        transform=tax.transAxes,
        fontsize=9,
        fontweight="bold",
        va="bottom",
    )
    ax.text(
        0.995,
        0.97,
        PTEST[term],
        transform=ax.transAxes,
        ha="right",
        va="top",
        linespacing=1.3,
        fontsize=7,
        color=TXT_GREY,
    )


def mm_axes(fig, H, y0, h):
    """Axes at a fixed height in mm; every panel spans the same x extent."""
    return fig.add_axes([0.09, y0 / H, 0.88, h / H])


def wave_strip(ax):
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.axvspan(*COVID_SPAN, color=SHADE, zorder=0, lw=0)
    for x, lab in BOUNDS:
        ax.axvline(x, **WAVE_LINE)
        ax.text(
            x + timedelta(days=9),
            0.30,
            lab,
            ha="left",
            va="center",
            fontsize=6.5,
            color=TXT_GREY,
            linespacing=1.05,
        )
    for lab, a, b in WAVES:
        ax.text(
            mid(a, b), 0.78, lab, ha="center", va="center", fontsize=7.5, color=COVID
        )
    for x, lab in FLU_LAB:
        ax.text(x, 0.78, lab, ha="center", va="center", fontsize=7.5, color=FLU)


def main():
    apply_style()
    d = pd.read_csv(DATA, parse_dates=["start", "end"])
    H = 184.0
    fig = plt.figure(figsize=(180 * MM, H * MM))
    # one calendar axis for A, B and C: same limits, same horizontal extent
    axA = mm_axes(fig, H, 115, 44)
    axW = mm_axes(fig, H, 159, 11)  # wave strip, directly on top of A
    axB = mm_axes(fig, H, 62, 44)
    axC = mm_axes(fig, H, 9, 37)
    for ax in (axW, axB, axC):
        ax.sharex(axA)
    wave_strip(axW)
    panel(axA, d, "income_lt10k", "A", title_ax=axW)
    panel(axB, d, "medicaid", "B")
    axB.text(
        0.005,
        0.97,
        "At or below 1: no excess beyond\nthe other social items (not protection)",
        transform=axB.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        color=TXT_GREY,
        style="italic",
    )
    for ax in (axB, axC):
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axA.tick_params(axis="x", labelbottom=False)
    axW.tick_params(axis="x", labelbottom=False)
    axB.tick_params(axis="x", labelbottom=True)
    axC.tick_params(axis="x", labelbottom=True)
    for ax in (axA, axB, axC):
        ax.tick_params(labelsize=7.5)
        ax.yaxis.label.set_size(8)
    for x, _ in BOUNDS:
        axC.axvline(x, **WAVE_LINE)

    for i, (lab, spans, kind) in enumerate(POLICY):
        y = len(POLICY) - i
        for sp in spans:
            if isinstance(sp, tuple):
                axC.plot(
                    list(sp),
                    [y, y],
                    color=PCOL[kind],
                    lw=5,
                    solid_capstyle="butt",
                    zorder=2,
                )
            else:
                axC.plot(
                    [sp], [y], marker="|", ms=9, mew=2.2, color=PCOL[kind], zorder=2
                )
        a = spans[0][0] if isinstance(spans[0], tuple) else spans[0]
        axC.text(
            a - timedelta(days=25),
            y,
            lab,
            va="center",
            ha="right",
            fontsize=7,
            color=INK,
            zorder=3,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.6),
        )
    axC.set_ylim(0.3, len(POLICY) + 0.7)
    axC.set_yticks([])
    axC.spines["left"].set_visible(False)
    axC.text(
        -0.075,
        1.02,
        "C",
        transform=axC.transAxes,
        fontsize=10,
        fontweight="bold",
        va="bottom",
    )
    axC.text(
        0.0,
        1.02,
        "Dates of selected federal measures (timing only)",
        transform=axC.transAxes,
        fontsize=9,
        fontweight="bold",
        va="bottom",
    )
    axA.set_xlim(X0, X1)  # shared by the strip, B and C
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "eFigure6." + ext), dpi=400)
    print("wrote eFigure6 to", OUT)


if __name__ == "__main__":
    main()
