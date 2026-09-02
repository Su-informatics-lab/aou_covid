# -*- coding: utf-8 -*-
"""Figure 3. Base-model adjusted odds ratios, All of Us against MarketScan.

Coefficients are transcribed from the frozen model outputs of the 2026-09-02
re-run; their provenance is in the round record. Run from the repository root:

    python3 figures/fig3_base_forest.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from jamia_forest import MM, NAVY, TEAL, apply_style, forest, save

OUT = sys.argv[1] if len(sys.argv) > 1 else "results/figures"
os.makedirs(OUT, exist_ok=True)

A = {  # All of Us, re-run base model
    "Female sex": (0.768, 0.709, 0.832),
    "Vaccinated before index": (0.427, 0.377, 0.484),
    "Age 45–54": (1.046, 0.930, 1.177),
    "Age 55–64": (1.328, 1.193, 1.480),
    "Age ≥65": (1.506, 1.350, 1.682),
    "Black race": (2.387, 2.175, 2.619),
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
M = {  # MarketScan, re-run base model
    "Female sex": (0.745, 0.736, 0.756),
    "Vaccinated before index": (0.503, 0.491, 0.515),
    "Age 45–54": (1.750, 1.721, 1.779),
    "Age 55–64": (2.394, 2.354, 2.434),
    "Age ≥65": (2.519, 2.164, 2.932),
    "Black race": None,
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
ORDER = list(A)

apply_style()
fig, ax = plt.subplots(figsize=(180 * MM, 165 * MM))
forest(
    ax,
    [(k, {"AoU": A[k], "MS": M[k]}) for k in ORDER],
    {"AoU": (NAVY, "o"), "MS": (TEAL, "s")},
    (0.35, 4.2),
    [0.5, 1, 2, 4],
    "Adjusted odds ratio (95% CI), log scale",
)
ax.legend(
    handles=[
        plt.Line2D(
            [],
            [],
            color=NAVY,
            marker="o",
            ms=3.4,
            lw=0.8,
            label="All of Us (n = 19,520)",
        ),
        plt.Line2D(
            [],
            [],
            color=TEAL,
            marker="s",
            ms=3.4,
            lw=0.8,
            label="MarketScan (n = 637,679)",
        ),
    ],
    frameon=False,
    loc="lower right",
    fontsize=6,
)
save(fig, os.path.join(OUT, "Figure3"))
print("  figure 3: %d rows" % len(ORDER))
