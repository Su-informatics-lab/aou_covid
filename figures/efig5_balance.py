# -*- coding: utf-8 -*-
"""eFigure 5. Propensity score matching balance for the encounter-density proxies.

Panels: A, All of Us COVID-19; B, All of Us influenza; C, MarketScan.
COVID-19 values are transcribed from the MatchIt summaries of the frozen run
(eTable 18, carried from the v19 supplement); MarketScan values from the
corrected pre-index run (Quartz job 10186336, 07c_smd_pre_matching.csv, as
recorded in commit 617f59a working/MS_SUPPLEMENT_UPDATES.md). Influenza values
are read from working/v25/tables/eTable5_flu_balance.csv (eTable 18, influenza
arm), rows "Matching variables". Standardized mean differences use the
treated-group standard deviation, as MatchIt reports them; absolute values are
plotted.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import DARK, INK, MM, PT_BODY, PT_HEAD, PT_SMALL, RULE, apply_style

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "submission_v25",
    "04_figures",
    "supplement",
)

AOU = [
    ("First survey date", 0.095, 0.015),
    ("Number of diagnoses", 0.410, 0.003),
    ("Length of medical history", 0.041, 0.012),
]
FLU_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "working",
    "v25",
    "tables",
    "eTable5_flu_balance.csv",
)
#  same row labels as panel A, in the csv's row order
FLU_LABELS = {
    "First survey date": "First survey date",
    "Number of distinct diagnoses": "Number of diagnoses",
    "Length of medical history": "Length of medical history",
}


def flu_rows():
    out = []
    with open(FLU_CSV, newline="") as f:
        for r in csv.DictReader(f):
            if r["section"] != "Matching variables":
                continue
            lab = next(v for k, v in FLU_LABELS.items() if r["label"].startswith(k))
            out.append((lab, abs(float(r["pre_smd"])), abs(float(r["post_smd"]))))
    assert [r[0] for r in out] == list(FLU_LABELS.values()), out
    return out


FLU = flu_rows()
MS = [
    ("Enrollment date", 0.241, 0.063),
    ("Number of diagnoses", 0.199, 0.012),
    ("Coverage span", 0.400, 0.045),
]

apply_style()
plt.rcParams.update(
    {
        "xtick.labelsize": PT_SMALL,
        "ytick.labelsize": PT_SMALL,
        "axes.labelsize": PT_BODY,
    }
)
fig, (ax, bx, cx) = plt.subplots(
    3,
    1,
    figsize=(172 * MM, 128 * MM),
    sharex=True,
    gridspec_kw=dict(hspace=0.62, left=0.22, right=0.97, top=0.92, bottom=0.155),
)


def panel(a, rows, title_n):
    y = list(range(len(rows)))[::-1]
    for yi, (lab, pre, post) in zip(y, rows):
        a.plot(
            [pre, post],
            [yi, yi],
            color="0.80",
            lw=2.0,
            solid_capstyle="round",
            zorder=1,
        )
        a.plot([pre], [yi], marker="^", ms=6.5, color="#A6A6A6", zorder=3)
        a.plot([post], [yi], marker="o", ms=6.0, color=DARK, zorder=3)
    a.axvline(0.10, color=RULE, lw=1.0, ls=(0, (4, 3)), zorder=0)
    a.set_yticks(y)
    a.set_yticklabels([r[0] for r in rows])
    a.set_ylim(-0.7, len(rows) - 0.3)
    a.set_xlim(-0.012, 0.52)
    a.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    a.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.5"])
    a.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        a.spines[s].set_visible(False)
    a.text(
        -0.28,
        1.06,
        title_n,
        transform=a.transAxes,
        fontsize=PT_HEAD,
        fontweight="bold",
        color=INK,
        va="bottom",
    )


panel(ax, AOU, "A   All of Us, COVID-19")
panel(bx, FLU, "B   All of Us, influenza")
panel(cx, MS, "C   MarketScan")
cx.set_xlabel("Absolute standardized mean difference")

fig.legend(
    handles=[
        Line2D(
            [],
            [],
            color="#A6A6A6",
            marker="^",
            ms=6.5,
            lw=0,
            label="Before matching",
        ),
        Line2D([], [], color=DARK, marker="o", ms=6.0, lw=0, label="After matching"),
        Line2D([], [], color=RULE, lw=1.0, ls=(0, (4, 3)), label="|SMD| = 0.10"),
    ],
    loc="lower center",
    bbox_to_anchor=(0.55, 0.0),
    ncol=3,
    fontsize=PT_SMALL,
    columnspacing=2.4,
    handletextpad=0.6,
    frameon=False,
)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "eFigure5." + ext), dpi=400)
print("wrote eFigure5")
