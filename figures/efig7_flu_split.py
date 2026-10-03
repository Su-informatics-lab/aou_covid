# -*- coding: utf-8 -*-
"""eFigure 7 (v26, R9; R11 labels; 2026-09-29 classic layout): Figure 2B for influenza.

Each period's odds ratio fitted alone and with the other 5 social items, each with
its 95% CI, and the percent attenuation, as in Figure 2B. It is kept out
of the main figure because influenza does not show the COVID-19 pattern: the
attenuated Medicaid part is 0.34 before the pandemic and 0.61 after (log
scale). The pandemic-season Medicaid estimate is withheld (reference group of
20 or fewer cases).
Reads results/figures/v25/Figure2_era_attenuation_data.csv.
Writes submission_v25/04_figures/supplement/eFigure7.{pdf,png}.
"""

import os

import pandas as pd
from fig2_v26 import sequential
from style import MM, PT_BODY, PT_HEAD, PT_SMALL, apply_style, plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(
    HERE, "..", "results", "figures", "v25", "Figure2_era_attenuation_data.csv"
)
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
ERAS = ((1, "Pre-pandemic"), (2, "Pandemic"), (3, "Post-pandemic"))


def main():
    apply_style()
    plt.rcParams.update({"xtick.labelsize": PT_SMALL, "ytick.labelsize": PT_SMALL})
    d = pd.read_csv(DATA)
    fig = plt.figure(figsize=(180 * MM, 105 * MM))
    ax = fig.add_axes([0.22, 0.12, 0.64, 0.74])
    sequential(
        ax,
        d,
        pathogen="Influenza",
        eras=ERAS,
        xlim=(0.42, 4.6),
        ticks=(0.5, 0.75, 1, 1.5, 2, 3, 4),
    )
    ax.xaxis.label.set_size(PT_BODY)
    fig.text(
        0.03,
        0.95,
        "Influenza: each item alone and jointly adjusted",
        fontsize=PT_HEAD,
        fontweight="bold",
        va="top",
    )
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "eFigure7." + ext), dpi=400)
    plt.close(fig)
    print("wrote eFigure7 to", OUT)


if __name__ == "__main__":
    main()
