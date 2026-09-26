# -*- coding: utf-8 -*-
"""Figure 2 (v25, R6 revision): what each association is made of, where the
income gradient sits, and how little of it the record holds.

What the eye should see in 3 seconds:
  A  For each era, a dumbbell from the domain fitted alone (teal) to the same
     domain fitted with the other 5 social items (navy, with its 95% CI). The
     label is the percent attenuation on the log scale. Income loses about a
     quarter in every era; Medicaid in COVID-19 loses half before Delta and
     all of it afterwards. (R5p drew this as stacked bars, which misdrew the
     shared part whenever the joint estimate fell below 1; replaced.)
  B  Crude hospitalization by income band: in COVID-19 the gradient is a step
     below $35 000 and flat above it; in influenza it continues modestly.
  C  The record rarely codes what participants report: % of participants with
     a self-reported social risk who carry the corresponding Z code, and any
     Z55-Z65 code (eTable 13).

Reads results/figures/v25/Figure2_era_attenuation_data.csv,
working/v25/platform_03u/{covid,flu}_crude.csv; panel C values are transcribed
from supplement eTable 13 (01d_zcode_capture.py output, screened at 20).
Writes results/figures/v25/Figure2.{pdf,png}.
Run from figures/:  ../.venv/bin/python fig2_decomp_v25.py
"""

import os

import numpy as np
import pandas as pd
from style import COVID, FLU, GREY, INK, MM, NAVY, RULE, TEAL, apply_style, plt, sig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v25")
DATA = os.path.join(OUT, "Figure2_era_attenuation_data.csv")
CRUDE = os.path.join(HERE, "..", "working", "v25", "platform_03u")
LIGHT = "#A9CCDC"
ERA_LAB = {
    "Pre-Delta": "Pre-\nDelta",
    "Delta": "Delta",
    "Omicron": "Omi-\ncron",
    "Before the pandemic": "Be-\nfore",
    "Pandemic seasons": "Pan-\ndemic",
    "After influenza returned": "After",
}
BANDS = ["<$10 000", "$10 000-24 999", "$25 000-34 999", "$35 000-99 999", ">=$100 000"]
BLAB = ["<10", "10-25", "25-35", "35-100", "≥100"]
#  eTable 13: participants reporting the risk, with the corresponding Z code, with any Z55-Z65
ZC = [
    ("Income below\n\\$25 000", 3817, 414, 713, "Z59"),
    ("Out of work or\nunable to work", 3608, 208, 736, "Z56"),
    ("Unstable\nhousing", 2309, 362, 555, "Z59"),
    ("Education\nbelow GED", 1487, None, 232, "Z55"),
]


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (c - h), 100 * (c + h)


def main():
    apply_style()
    d = pd.read_csv(DATA)
    fig = plt.figure(figsize=(180 * MM, 190 * MM))
    gs = fig.add_gridspec(
        2, 2, height_ratios=[1.15, 1], width_ratios=[1, 1.05], hspace=0.78, wspace=0.95
    )
    axA = fig.add_subplot(gs[0, :])

    # ---- A: dumbbells alone -> joint, percent attenuation
    x = 0
    ticks, labs, groups = [], [], []
    for term, tlab in (
        ("income_lt10k", "Income below \\$10 000"),
        ("medicaid", "Medicaid"),
    ):
        g0 = x
        for pth in ("COVID-19", "Influenza"):
            sub = d[(d.term == term) & (d.pathogen == pth)].sort_values("era_order")
            p0 = x
            for o in sorted(sub.era_order.unique()):
                a = sub[(sub.era_order == o) & (sub.model == "alone")].iloc[0]
                j = sub[(sub.era_order == o) & (sub.model == "joint")].iloc[0]
                al = 0.45 if a.era.startswith("Pandemic") else 1.0
                if pd.isna(a.aor) or pd.isna(j.aor):
                    # withheld: reference group below 20 cases (03x cell audit)
                    axA.text(
                        x,
                        1.3,
                        "withheld\n(<20 in\nreference)",
                        ha="center",
                        va="center",
                        fontsize=6.5,
                        color=GREY,
                        bbox=dict(fc="white", ec="none", pad=1.0),
                        zorder=6,
                    )
                    ticks.append(x)
                    labs.append(ERA_LAB[a.era])
                    x += 1.1
                    continue
                axA.plot(
                    [x, x],
                    [a.aor, j.aor],
                    color=LIGHT,
                    lw=7,
                    solid_capstyle="butt",
                    alpha=al,
                    zorder=2,
                )
                axA.plot(
                    [x + 0.14, x + 0.14],
                    [j.lo, j.hi],
                    color=NAVY,
                    lw=1.1,
                    alpha=al,
                    zorder=3,
                )
                axA.plot(
                    [x], [a.aor], marker="o", ms=6.5, color=TEAL, alpha=al, zorder=4
                )
                axA.plot(
                    [x],
                    [j.aor],
                    marker="o",
                    ms=6.5,
                    color=NAVY,
                    mfc=NAVY if sig(j.lo, j.hi) else "white",
                    mew=1.5,
                    alpha=al,
                    zorder=5,
                )
                att = 100 * (np.log(a.aor) - np.log(j.aor)) / np.log(a.aor)
                axA.text(
                    x,
                    max(a.aor, j.aor) * 1.09,
                    "%d%%" % round(att),
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                    color=INK,
                    alpha=al,
                )
                ticks.append(x)
                labs.append(ERA_LAB[a.era])
                x += 1.1
            axA.text(
                (p0 + x - 1.1) / 2,
                -0.21,
                pth,
                transform=axA.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=9,
                color=COVID if pth == "COVID-19" else FLU,
                fontweight="bold",
            )
            x += 0.6
        groups.append(((g0 + x - 1.7) / 2, tlab))
        x += 0.9
    axA.axhline(1, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    axA.set_yscale("log")
    axA.set_ylim(0.42, 5.4)
    axA.set_yticks([0.5, 0.75, 1, 1.5, 2, 3, 5])
    axA.set_yticklabels(["0.5", "0.75", "1", "1.5", "2", "3", "5"])
    axA.yaxis.set_minor_locator(plt.NullLocator())
    axA.set_xticks(ticks)
    axA.set_xticklabels(labs, fontsize=8)
    axA.tick_params(axis="x", length=0)
    axA.set_ylabel("Odds ratio (log scale)")
    for gx, gl in groups:
        axA.text(
            gx,
            5.4,
            gl,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=INK,
        )
    axA.text(
        -0.075,
        1.13,
        "A",
        transform=axA.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axA.text(
        0.0,
        1.13,
        "Each association fitted alone and with the other social items, by era",
        transform=axA.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )
    h = [
        plt.Line2D([], [], color=TEAL, marker="o", lw=0, label="Fitted alone"),
        plt.Line2D(
            [],
            [],
            color=NAVY,
            marker="o",
            lw=0,
            label="With the other 5 items (95% CI; open: includes 1)",
        ),
        plt.Line2D(
            [],
            [],
            color=LIGHT,
            lw=6,
            label="Part the other items account for; label = % attenuation",
        ),
    ]
    axA.legend(
        handles=h, loc="upper left", bbox_to_anchor=(-0.02, -0.29), ncol=3, fontsize=7.6
    )

    # ---- B: crude hospitalization by income band
    axB = fig.add_subplot(gs[1, 0])
    for arm, col, mk, lab, off in (
        ("covid", COVID, "o", "COVID-19", -0.08),
        ("flu", FLU, "D", "Influenza", 0.08),
    ):
        c = pd.read_csv(os.path.join(CRUDE, "%s_crude.csv" % arm))
        c = c[(c.variable == "income_band") & (c.era == "all")].set_index("level")
        ys = [c.loc[b, "pct"] for b in BANDS]
        ci = [wilson(c.loc[b, "hosp"], c.loc[b, "n"]) for b in BANDS]
        xs = np.arange(len(BANDS)) + off
        axB.plot(xs, ys, color=col, lw=1.2, zorder=2)
        for xx, (lo, hi) in zip(xs, ci):
            axB.plot([xx, xx], [lo, hi], color=col, lw=1.2, zorder=3)
        axB.plot(xs, ys, marker=mk, ms=5.5, lw=0, color=col, label=lab, zorder=4)
        m = c.loc["Missing"]
        lo, hi = wilson(m.hosp, m.n)
        axB.plot([5.7 + off] * 2, [lo, hi], color=col, lw=1.2, alpha=0.6)
        axB.plot(
            [5.7 + off],
            [m.pct],
            marker=mk,
            ms=5.5,
            color=col,
            mfc="white",
            mew=1.3,
            zorder=4,
        )
    axB.annotate(
        "COVID-19 flat\nabove \\$35 000",
        xy=(3.5, 11.9),
        xytext=(3.5, 4.5),
        ha="center",
        fontsize=7.8,
        color=GREY,
        arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7),
    )
    axB.set_xticks(list(range(5)) + [5.7])
    axB.set_xticklabels(BLAB + ["Miss-\ning"], fontsize=7.8, rotation=35, ha="right")
    axB.set_xlabel("Household income, \\$ thousands")
    axB.set_ylabel("Hospitalized, % of infected")
    axB.set_ylim(0, 32)
    axB.set_xlim(-0.5, 6.2)
    axB.legend(loc="upper right", fontsize=8)
    axB.text(
        -0.2,
        1.05,
        "B",
        transform=axB.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axB.text(
        0.0,
        1.05,
        "Crude hospitalization, by income",
        transform=axB.transAxes,
        fontsize=10.5,
        fontweight="bold",
        va="bottom",
    )

    # ---- C: Z-code capture of self-reported risk (COVID-19 matched cohort)
    axC = fig.add_subplot(gs[1, 1])
    y = np.arange(len(ZC))[::-1]
    for yy, (lab, n, zk, anyk, code) in zip(y, ZC):
        pa = 100 * anyk / n
        axC.barh(yy + 0.18, pa, height=0.34, color=LIGHT, zorder=2)
        axC.text(
            pa + 1, yy + 0.18, "%.0f%%" % pa, va="center", fontsize=7.5, color=GREY
        )
        if zk is None:
            axC.text(
                1,
                yy - 0.18,
                "%s: fewer than 20" % code,
                va="center",
                fontsize=7.5,
                color=INK,
            )
        else:
            pz = 100 * zk / n
            axC.barh(yy - 0.18, pz, height=0.34, color=NAVY, zorder=2)
            axC.text(
                pz + 1,
                yy - 0.18,
                "%.1f%% (%s)" % (pz, code),
                va="center",
                fontsize=7.5,
                color=INK,
            )
    axC.set_yticks(y)
    axC.set_yticklabels([z[0] for z in ZC], fontsize=8)
    axC.set_xlim(0, 40)
    axC.set_xlabel("% of those reporting the risk")
    h = [
        plt.Rectangle((0, 0), 1, 1, color=NAVY, label="Corresponding Z code"),
        plt.Rectangle((0, 0), 1, 1, color=LIGHT, label="Any Z55-Z65 code"),
    ]
    axC.legend(
        handles=h, loc="upper center", bbox_to_anchor=(0.4, -0.3), ncol=2, fontsize=7.2
    )
    axC.set_ylim(-0.65, 3.55)
    axC.text(
        -0.62,
        1.05,
        "C",
        transform=axC.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    axC.text(
        -0.45,
        1.05,
        "What the record codes",
        transform=axC.transAxes,
        fontsize=10.5,
        fontweight="bold",
        va="bottom",
    )

    fig.text(
        0.5,
        0.0,
        "Faint: pandemic influenza seasons (817 matched rows); Medicaid there withheld (reference <20 cases). Vertical bars in B: Wilson 95% CIs; open markers: "
        "income not reported.\nC: COVID-19 matched participants, Z codes dated before the index date (eTable 13).",
        ha="center",
        va="top",
        fontsize=7.8,
        color=GREY,
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure2." + ext), dpi=300, bbox_inches="tight")
    print("wrote Figure2 to", OUT)


if __name__ == "__main__":
    main()
