# -*- coding: utf-8 -*-
"""eFigure 5 (v26, R9): the hospitalization phenotype decision tree.

The earlier eFigure 5 had no source in the repository; this script is now its
source of record. Same logic and wording as the earlier figure: from the data
domains, a COVID-19-positive participant is a case if admitted as an inpatient
or from the emergency department to inpatient care within 14 days; otherwise,
an emergency visit within 14 days with a recorded stay of at least 1 day is a
case, a same-day emergency visit is a control, and no emergency visit is a
control (outpatient). R10: the earlier label "case in 30-day sensitivity" named
an analysis the manuscript does not report and was removed.
Neutral colours: case and control are not a pathogen or a social variable.
Writes submission_v25/04_figures/supplement/eFigure2.{pdf,png}.
"""

import os

from matplotlib.patches import FancyBboxPatch, Polygon
from style import DARK, INK, MM, PT_BODY, PT_SMALL, apply_style, plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
EDGE_LAB = "#555555"
FILL = "#F2F2F2"


def box(ax, cx, cy, w, h, text, bold_first=False, strong=False):
    ax.add_patch(
        FancyBboxPatch(
            (cx - w / 2, cy - h / 2),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=1.6",
            facecolor="white" if not strong else FILL,
            edgecolor=INK,
            lw=1.6 if strong else 0.9,
            zorder=2,
        )
    )
    lines = text.split("\n")
    if bold_first:
        ax.text(
            cx,
            cy + h / 2 - 4.2,
            lines[0],
            ha="center",
            va="center",
            fontsize=PT_BODY,
            fontweight="bold",
            color=INK,
            zorder=3,
        )
        ax.text(
            cx,
            cy - 2.2,
            "\n".join(lines[1:]),
            ha="center",
            va="center",
            fontsize=PT_BODY,
            color=INK,
            linespacing=1.6,
            zorder=3,
        )
    else:
        ax.text(
            cx,
            cy,
            text,
            ha="center",
            va="center",
            fontsize=PT_BODY,
            color=INK,
            fontweight="bold" if strong else "normal",
            zorder=3,
        )


def diamond(ax, cx, cy, hw, hh, text):
    ax.add_patch(
        Polygon(
            [(cx - hw, cy), (cx, cy + hh), (cx + hw, cy), (cx, cy - hh)],
            closed=True,
            facecolor=FILL,
            edgecolor=DARK,
            lw=0.9,
            zorder=2,
        )
    )
    ax.text(
        cx, cy, text, ha="center", va="center", fontsize=PT_BODY, color=INK, zorder=3
    )


def arrow(ax, a, b, lab=None, lab_xy=None):
    ax.annotate(
        "",
        xy=b,
        xytext=a,
        arrowprops=dict(
            arrowstyle="-|>", color=INK, lw=0.9, mutation_scale=9, shrinkA=0, shrinkB=0
        ),
        zorder=1,
    )
    if lab:
        ax.text(
            *lab_xy, lab, fontsize=PT_SMALL, color=EDGE_LAB, ha="center", va="center"
        )


def main():
    apply_style()
    fig = plt.figure(figsize=(180 * MM, 92 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 92)
    ax.axis("off")
    Y1, Y2, Y3 = 62, 38, 13
    box(
        ax,
        20,
        Y1,
        34,
        26,
        "Data domains\nICD conditions\nVisit records\nLaboratory results",
        bold_first=True,
    )
    diamond(ax, 57, Y1, 15, 10, "COVID-19\npositive?")
    box(ax, 57, 85, 28, 7, "Excluded")
    diamond(ax, 104, Y1, 24, 10, "Inpatient or\nED-to-inpatient ≤14 d?")
    box(ax, 159, Y1, 36, 8, "Case (hospitalized)", strong=True)
    diamond(ax, 104, Y2, 17, 9, "Emergency\nvisit ≤14 d?")
    box(ax, 40, Y2, 40, 8, "Control (outpatient)", strong=True)
    diamond(ax, 104, Y3, 17, 9, "Recorded stay\n≥1 day?")
    box(ax, 40, Y3, 44, 10, "Control\n(same-day emergency visit)", strong=True)
    box(ax, 159, Y3, 36, 8, "Case (hospitalized)", strong=True)
    arrow(ax, (37, Y1), (42, Y1))
    arrow(ax, (57, Y1 + 10), (57, 81.5), "No", (60.5, 76.5))
    arrow(ax, (72, Y1), (80, Y1), "Yes", (76, Y1 + 2.8))
    arrow(ax, (128, Y1), (141, Y1), "Yes", (134.5, Y1 + 2.8))
    arrow(ax, (104, Y1 - 10), (104, Y2 + 9), "No", (107.5, (Y1 - 10 + Y2 + 9) / 2))
    arrow(ax, (87, Y2), (60, Y2), "No", (73.5, Y2 + 2.8))
    arrow(ax, (104, Y2 - 9), (104, Y3 + 9), "Yes", (108, (Y2 - 9 + Y3 + 9) / 2))
    arrow(ax, (87, Y3), (62, Y3), "No (same-day)", (74.5, Y3 + 2.8))
    arrow(ax, (121, Y3), (141, Y3), "Yes", (131, Y3 + 2.8))
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "eFigure2." + ext), dpi=400)
    plt.close(fig)
    print("wrote eFigure2 to", OUT)


if __name__ == "__main__":
    main()
