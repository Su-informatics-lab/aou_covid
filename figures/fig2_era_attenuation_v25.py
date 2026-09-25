# -*- coding: utf-8 -*-
"""Figure 2 (v25): attenuation by era. For each era, the domain fitted alone
(teal) and jointly with the other five (navy), joined by an arrow. The length
of the arrow is the part of the association the other social conditions
account for; where the navy mark sits is the part they do not.

What the reader should see: for income the arrow is short in every era and the
navy mark stays near 1.5; for Medicaid the navy mark sits above 1 in the first
era and at or below 1 afterwards, while the teal mark stays above 1 — the
economic part of the insurance association persisted and the rest went.

Reads results/figures/v25/Figure2_era_attenuation_data.csv. Colour rules follow
style.py: cool marks are the analysis (teal alone, navy joint); pathogen is a
warm keycap in the panel title.
"""

import os

import pandas as pd
from style import COVID, FLU, GREY, MM, NAVY, RULE, TEAL, apply_style, plt, sig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures", "v25")
DATA = os.path.join(OUT, "Figure2_era_attenuation_data.csv")
TERM = {"medicaid": "Medicaid", "income_lt10k": "income below $10 000"}


def panel(ax, sub, title, key, letter):
    ax.axhline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    for o in sorted(sub.era_order.unique()):
        a = sub[(sub.era_order == o) & (sub.model == "alone")].iloc[0]
        j = sub[(sub.era_order == o) & (sub.model == "joint")].iloc[0]
        xa, xj = o - 0.12, o + 0.12
        faint = 0.45 if a.era.startswith("Pandemic") else 1.0
        for x, r, col in ((xa, a, TEAL), (xj, j, NAVY)):
            ax.plot([x, x], [r.lo, r.hi], color=col, lw=1.4, alpha=faint, zorder=3)
            ax.plot(
                [x],
                [r.aor],
                marker="o",
                ms=6.5,
                color=col,
                mfc=col if sig(r.lo, r.hi) else "white",
                mew=1.6,
                alpha=faint,
                zorder=4,
            )
        ax.annotate(
            "",
            xy=(xj - 0.03, j.aor),
            xytext=(xa + 0.03, a.aor),
            arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.0, alpha=faint),
            zorder=2,
        )
    ax.set_yscale("log")
    ax.set_ylim(0.45, 5.5)
    ax.set_yticks([0.5, 0.75, 1, 1.5, 2, 3, 5])
    ax.set_yticklabels(["0.5", "0.75", "1", "1.5", "2", "3", "5"])
    ax.yaxis.set_minor_locator(plt.NullLocator())
    eras = sub.drop_duplicates("era_order").sort_values("era_order")
    ax.set_xticks(eras.era_order)
    ax.set_xticklabels(
        [e.replace(" ", "\n", 1) if len(e) > 12 else e for e in eras.era]
    )
    ax.set_xlim(0.5, 3.5)
    ax.text(
        -0.16,
        1.04,
        letter,
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
    )
    ax.text(
        0.0,
        1.04,
        title,
        transform=ax.transAxes,
        fontsize=10.5,
        fontweight="bold",
        va="bottom",
        color=COVID if key == "COVID-19" else FLU,
    )


def main():
    apply_style()
    d = pd.read_csv(DATA)
    fig, axes = plt.subplots(2, 2, figsize=(180 * MM, 150 * MM), sharey=True)
    k = 0
    for i, term in enumerate(["income_lt10k", "medicaid"]):
        for jj, pth in enumerate(["COVID-19", "Influenza"]):
            ax = axes[i, jj]
            panel(
                ax,
                d[(d.term == term) & (d.pathogen == pth)],
                "%s: %s" % (pth, TERM[term]),
                pth,
                "ABCD"[k],
            )
            k += 1
            if jj == 0:
                ax.set_ylabel("Adjusted odds ratio")
    fig.subplots_adjust(hspace=0.55, wspace=0.12)
    fig.text(
        0.5,
        -0.06,
        "Teal: the domain fitted alone.  Navy: fitted jointly with the other 5 social items.\n"
        "Arrow: from alone to jointly adjusted within an era (not change over time); its length is the part the other items account for.\n"
        "Filled: 95% CI excludes 1.  Faint: pandemic influenza seasons (817 rows).",
        ha="center",
        va="top",
        fontsize=8,
        color=GREY,
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "Figure2." + ext), dpi=300, bbox_inches="tight")
    print("wrote Figure2 to", OUT)


if __name__ == "__main__":
    main()
