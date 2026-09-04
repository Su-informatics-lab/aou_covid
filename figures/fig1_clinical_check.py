# -*- coding: utf-8 -*-
"""Figure 1. The clinical model: what the pre-index correction did, and how the
corrected model compares with All of Us.

Panel (a) MarketScan before and after restricting the matching variables to
records dated before the index date. "Before" values are the superseded
2026-08 run, transcribed from the v18.6 supplement eTable 10; "after" values
are the frozen 2026-09-02 re-run.
Panel (b) All of Us against the corrected MarketScan model.

No value is recomputed here.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import (
    ERA,
    GREY,
    INK,
    MM,
    NAVY,
    RULE,
    TEAL,
    apply_style,
    log_axis,
    panel_labels,
    save,
    sig,
)

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "figures"
)
PALE = ERA[0]  # light end of the cool ramp: the superseded run

# All of Us, frozen 2026-09-02 re-run
A = {
    "Female sex": (0.768, 0.709, 0.832),
    "Age 45–54": (1.046, 0.930, 1.177),
    "Age 55–64": (1.328, 1.193, 1.480),
    "Age ≥65": (1.506, 1.350, 1.682),
    "Black race": (2.387, 2.175, 2.619),
    "Vaccinated before index": (0.427, 0.377, 0.484),
    "Delta wave": (1.234, 1.109, 1.373),
    "Omicron wave": (1.000, 0.919, 1.088),
    "Myocardial infarction": (1.060, 0.938, 1.198),
    "Congestive heart failure": (1.193, 1.075, 1.325),
    "Peripheral vascular disease": (0.961, 0.866, 1.067),
    "Cerebrovascular disease": (1.193, 1.075, 1.324),
    "Dementia": (1.135, 0.962, 1.339),
    "Chronic pulmonary disease": (0.904, 0.835, 0.980),
    "Rheumatic disease": (1.038, 0.920, 1.171),
    "Peptic ulcer disease": (0.964, 0.840, 1.106),
    "Liver disease, mild": (0.827, 0.752, 0.908),
    "Liver disease, mod./severe": (1.464, 1.190, 1.800),
    "Diabetes w/o complications": (1.098, 0.983, 1.226),
    "Diabetes w/ complications": (1.154, 1.039, 1.281),
    "Hemiplegia or paraplegia": (1.364, 1.143, 1.628),
    "Renal disease, mild/mod.": (1.122, 1.000, 1.258),
    "Renal disease, severe": (1.488, 1.289, 1.716),
    "HIV": (1.107, 0.770, 1.590),
    "Metastatic solid tumor": (1.295, 1.082, 1.550),
    "Malignancy": (1.102, 0.995, 1.220),
    "AIDS": (0.770, 0.572, 1.035),
}
# MarketScan, corrected: matching variables restricted to pre-index records
M = {
    "Female sex": (0.745, 0.736, 0.756),
    "Age 45–54": (1.750, 1.721, 1.779),
    "Age 55–64": (2.394, 2.354, 2.434),
    "Age ≥65": (2.519, 2.164, 2.932),
    "Black race": None,
    "Vaccinated before index": (0.503, 0.491, 0.515),
    "Delta wave": (1.112, 1.059, 1.167),
    "Omicron wave": (0.729, 0.696, 0.763),
    "Myocardial infarction": (1.048, 0.993, 1.105),
    "Congestive heart failure": (1.657, 1.594, 1.721),
    "Peripheral vascular disease": (1.058, 1.019, 1.098),
    "Cerebrovascular disease": (1.061, 1.018, 1.105),
    "Dementia": (1.607, 1.455, 1.774),
    "Chronic pulmonary disease": (1.164, 1.141, 1.187),
    "Rheumatic disease": (1.091, 1.047, 1.136),
    "Peptic ulcer disease": (1.006, 0.937, 1.081),
    "Liver disease, mild": (1.060, 1.030, 1.091),
    "Liver disease, mod./severe": (1.990, 1.809, 2.189),
    "Diabetes w/o complications": (1.806, 1.771, 1.843),
    "Diabetes w/ complications": (2.019, 1.961, 2.078),
    "Hemiplegia or paraplegia": (2.176, 2.023, 2.340),
    "Renal disease, mild/mod.": (1.583, 1.526, 1.642),
    "Renal disease, severe": (3.313, 3.112, 3.527),
    "HIV": (1.247, 1.111, 1.399),
    "Metastatic solid tumor": (2.626, 2.476, 2.785),
    "Malignancy": (1.222, 1.179, 1.267),
    "AIDS": (1.686, 1.338, 2.123),
}
# MarketScan, superseded run: matching variables measured over the whole
# enrollment record.  v18.6 supplement, eTable 10.
B = {
    "Female sex": (0.50, 0.49, 0.50),
    "Age 45–54": (1.46, 1.44, 1.48),
    "Age 55–64": (1.78, 1.75, 1.81),
    "Age ≥65": (1.73, 1.51, 1.98),
    "Black race": None,
    "Vaccinated before index": (0.48, 0.47, 0.50),
    "Delta wave": (1.47, 1.44, 1.49),
    "Omicron wave": (0.47, 0.47, 0.48),
    "Myocardial infarction": (0.94, 0.89, 0.99),
    "Congestive heart failure": (1.36, 1.31, 1.41),
    "Peripheral vascular disease": (0.86, 0.83, 0.89),
    "Cerebrovascular disease": (0.86, 0.83, 0.89),
    "Dementia": (1.27, 1.16, 1.39),
    "Chronic pulmonary disease": (0.86, 0.84, 0.87),
    "Rheumatic disease": (0.82, 0.79, 0.85),
    "Peptic ulcer disease": (0.79, 0.73, 0.84),
    "Liver disease, mild": (0.78, 0.76, 0.81),
    "Liver disease, mod./severe": (1.43, 1.31, 1.56),
    "Diabetes w/o complications": (1.41, 1.38, 1.44),
    "Diabetes w/ complications": (1.46, 1.42, 1.50),
    "Hemiplegia or paraplegia": (1.71, 1.59, 1.83),
    "Renal disease, mild/mod.": (1.29, 1.25, 1.34),
    "Renal disease, severe": (2.45, 2.31, 2.59),
    "HIV": (0.86, 0.76, 0.96),
    "Metastatic solid tumor": (1.68, 1.59, 1.77),
    "Malignancy": (0.94, 0.91, 0.98),
    "AIDS": (1.27, 1.03, 1.58),
}

GROUPS = [
    (
        "Demographics and vaccination",
        [
            "Female sex",
            "Age 45–54",
            "Age 55–64",
            "Age ≥65",
            "Black race",
            "Vaccinated before index",
        ],
    ),
    ("Pandemic wave", ["Delta wave", "Omicron wave"]),
    (
        "Charlson comorbidities",
        [
            "Myocardial infarction",
            "Congestive heart failure",
            "Peripheral vascular disease",
            "Cerebrovascular disease",
            "Dementia",
            "Chronic pulmonary disease",
            "Rheumatic disease",
            "Peptic ulcer disease",
            "Liver disease, mild",
            "Liver disease, mod./severe",
            "Diabetes w/o complications",
            "Diabetes w/ complications",
            "Hemiplegia or paraplegia",
            "Renal disease, mild/mod.",
            "Renal disease, severe",
            "HIV",
            "Metastatic solid tumor",
            "Malignancy",
            "AIDS",
        ],
    ),
]

apply_style()
fig, (ax, bx) = plt.subplots(
    1,
    2,
    sharey=True,
    figsize=(184 * MM, 200 * MM),
    gridspec_kw=dict(width_ratios=[1, 1], wspace=0.09),
)

# rows top to bottom, with a gap before each group heading
y, rows, headers = [], [], []
cur = 0.0
for gi, (gname, labs) in enumerate(GROUPS):
    cur += 1.9 if gi else 0.9
    headers.append((gname, cur))
    cur += 1.05
    for lab in labs:
        rows.append(lab)
        y.append(cur)
        cur += 1.0
bottom = cur - 1.0
y = [bottom - v for v in y]
headers = [(g, bottom - v) for g, v in headers]

XLIM = (0.33, 4.6)
OFF = 0.21

# ── panel a: the pre-index correction inside MarketScan ──
for yi, lab in zip(y, rows):
    before, after = B[lab], M[lab]
    if before is None or after is None:
        continue
    if before[2] < 1.0 and after[0] >= 1.0:  # significantly inverse, then not
        ax.axhspan(yi - 0.5, yi + 0.5, color="0.55", alpha=0.10, lw=0, zorder=0)
    ax.plot(
        [before[0], after[0]],
        [yi + OFF, yi - OFF],
        color="0.78",
        lw=1.8,
        solid_capstyle="round",
        zorder=1.4,
    )
    for v, col, mk, off in ((before, PALE, "^", OFF), (after, TEAL, "s", -OFF)):
        a, lo, hi = v
        ax.plot(
            [lo, hi],
            [yi + off, yi + off],
            color=col,
            lw=1.4,
            solid_capstyle="butt",
            zorder=2,
        )
        ax.plot(
            [a],
            [yi + off],
            marker=mk,
            ms=5.8,
            color=col,
            zorder=3,
            mfc=col if sig(lo, hi) else "white",
            mew=1.2,
        )

# ── panel b: All of Us against the corrected MarketScan model ──
for yi, lab in zip(y, rows):
    for key, src, col, mk in (("AoU", A, NAVY, "o"), ("MS", M, TEAL, "s")):
        v = src[lab]
        if v is None:
            continue
        a, lo, hi = v
        yy = yi + (OFF if key == "AoU" else -OFF)
        bx.plot([lo, hi], [yy, yy], color=col, lw=1.4, solid_capstyle="butt", zorder=2)
        bx.plot(
            [a],
            [yy],
            marker=mk,
            ms=5.8,
            color=col,
            zorder=3,
            mfc=col if sig(lo, hi) else "white",
            mew=1.2,
        )
    if M[lab] is None:
        bx.text(
            XLIM[0] * 1.05,
            yi - OFF,
            "not captured in MarketScan",
            fontsize=9,
            color=GREY,
            va="center",
            ha="left",
            style="italic",
        )

for a_ in (ax, bx):
    log_axis(a_, XLIM, [0.5, 1, 2, 4], "Adjusted odds ratio (95% CI), log scale")
ax.set_yticks(y)
ax.set_yticklabels(rows)
ax.set_ylim(min(y) - 1.0, max(headers, key=lambda h: h[1])[1] + 0.9)

# group headings sit in the left panel's label gutter; each rule spans its own panel
for gname, gy in headers:
    ax.text(
        -0.68,
        gy,
        gname,
        transform=ax.get_yaxis_transform(),
        ha="left",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )
    for a_ in (ax, bx):
        a_.plot(
            [0.0, 1.0],
            [gy, gy],
            transform=a_.get_yaxis_transform(),
            color=RULE,
            lw=0.7,
            zorder=0,
            clip_on=False,
        )

ax.legend(
    handles=[
        Line2D(
            [],
            [],
            color=PALE,
            marker="^",
            ms=5.8,
            lw=1.4,
            label="Before correction (superseded)",
        ),
        Line2D(
            [],
            [],
            color=TEAL,
            marker="s",
            ms=5.8,
            lw=1.4,
            label="After correction (n = 637,679)",
        ),
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.055),
    ncol=1,
    handletextpad=0.5,
)
bx.legend(
    handles=[
        Line2D(
            [],
            [],
            color=NAVY,
            marker="o",
            ms=5.8,
            lw=1.4,
            label="All of Us (n = 19,520)",
        ),
        Line2D(
            [],
            [],
            color=TEAL,
            marker="s",
            ms=5.8,
            lw=1.4,
            label="MarketScan, corrected (n = 637,679)",
        ),
        Line2D(
            [],
            [],
            color=GREY,
            marker="o",
            ms=5.8,
            lw=0,
            mfc="white",
            mew=1.2,
            label="open marker: not significant",
        ),
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.055),
    ncol=1,
    handletextpad=0.5,
)
panel_labels([ax, bx], alpha=1.0)
save(fig, os.path.join(OUT, "Figure1"))
print("  rows:", len(rows))
