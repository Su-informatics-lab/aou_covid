# -*- coding: utf-8 -*-
"""Figure 4. Domain-specific against jointly adjusted SDoH associations.

The grey connector is the point of the figure: its length is what mutual
adjustment costs each estimate.

Coefficients are transcribed from the frozen model outputs of the 2026-09-02
re-run; their provenance is in the round record. Run from the repository root:

    python3 figures/fig4_sdoh_forest.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from jamia_forest import CORAL, MM, NAVY, apply_style, forest, save

OUT = sys.argv[1] if len(sys.argv) > 1 else "results/figures"
os.makedirs(OUT, exist_ok=True)

S = [
    ("Income <$10,000", (1.505, 1.326, 1.708), (1.211, 1.046, 1.402)),
    ("$10,000–24,999", (1.409, 1.244, 1.596), (1.205, 1.053, 1.380)),
    ("$25,000–34,999", (1.176, 1.012, 1.367), (1.096, 0.939, 1.280)),
    ("$100,000–149,999", (1.170, 1.002, 1.368), (1.213, 1.035, 1.421)),
    ("$150,000–199,999", (1.206, 0.971, 1.498), (1.258, 1.008, 1.569)),
    ("≥$200,000", (1.088, 0.887, 1.336), (1.147, 0.930, 1.415)),
    ("Medicare", (1.152, 1.014, 1.309), (0.982, 0.855, 1.128)),
    ("Medicaid", (1.536, 1.380, 1.710), (1.193, 1.047, 1.360)),
    ("Other or no insurance", (1.328, 1.146, 1.538), (1.108, 0.946, 1.298)),
    ("Below GED", (1.290, 1.130, 1.474), (1.060, 0.919, 1.223)),
    ("GED or some college", (1.107, 1.015, 1.206), (1.011, 0.920, 1.110)),
    ("Unemployed", (1.547, 1.398, 1.711), (1.350, 1.198, 1.521)),
    ("Student", (1.478, 1.140, 1.917), (1.368, 1.050, 1.782)),
    ("Retired or other", (1.398, 1.254, 1.557), (1.284, 1.142, 1.443)),
    ("Renting", (1.282, 1.175, 1.400), (1.161, 1.054, 1.279)),
    ("Housing tenure, other", (1.129, 0.980, 1.300), (0.979, 0.841, 1.138)),
    ("Housing instability", (1.002, 0.908, 1.105), (0.909, 0.819, 1.008)),
    ("Any disability", (1.025, 0.900, 1.168), (0.924, 0.808, 1.056)),
]


apply_style()
fig, ax = plt.subplots(figsize=(180 * MM, 115 * MM))
forest(
    ax,
    [(l, {"joint": j, "dom": d}) for l, d, j in S],
    {"joint": (NAVY, "s"), "dom": (CORAL, "o")},
    (0.75, 2.1),
    [0.8, 1, 1.5, 2],
    "Adjusted odds ratio (95% CI), log scale",
    top_first=True,
    connect=True,
)
ax.legend(
    handles=[
        plt.Line2D(
            [],
            [],
            color=NAVY,
            marker="s",
            ms=3.4,
            lw=0.8,
            label="Joint model (all six domains)",
        ),
        plt.Line2D(
            [],
            [],
            color=CORAL,
            marker="o",
            ms=3.4,
            lw=0.8,
            label="Domain-specific model",
        ),
        plt.Line2D(
            [], [], color="0.72", lw=1.6, label="Change after mutual adjustment"
        ),
    ],
    frameon=False,
    loc="lower right",
    fontsize=6,
)
save(fig, os.path.join(OUT, "Figure4"))
print("  figure 4: %d rows" % len(S))
