# -*- coding: utf-8 -*-
"""Figure 3. Test 4. The same design applied to influenza.

(a) pairs each social exposure's jointly adjusted estimate across the two
    pathogens. Six of seven agree; the one that does not is Medicaid.
(b) shows why that is not a coincidence: insurance is also the only domain
    whose association moves with time, and it is that in BOTH pathogens.

Reads working/flu/csv/, which is gitignored: the aggregate estimates stay
local and are never pushed.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import COVID, FLU, GREY, MM, apply_style, log_axis, panel_labels, save

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "results", "figures", "flu")
OUT = os.path.join(HERE, "..", "results", "figures")


def rd(name):
    with open(os.path.join(CSV, name)) as f:
        return list(csv.DictReader(f))


joint = rd("csv_06_covid_vs_flu_joint.csv")
inter = rd("csv_04_flu_interaction_tests.csv")
f = float

#  Each level is against a reference, and the figure says which: without it a
#  reader cannot tell what "1.5" is 1.5 times.  The domain is Insurance and the
#  level is Medicaid; the row label used to say "Medicaid coverage" while panel
#  (c) said "Insurance", which read as two different things in one figure.
#
#  domain, level key, level name, short reference (for the tick), full reference
ORDER = [
    ("employment", "Unemployed", "Unemployed", "employed", "employed"),
    ("income", "less_10k", "Income <$10,000", "$35–99k", "$35,000–99,999"),
    ("income", "10k_25k", "Income $10,000–24,999", "$35–99k", "$35,000–99,999"),
    ("housing", "Rent", "Renting", "owns home", "owns home"),
    ("insurance_type", "Medicaid", "Medicaid", "employer", "employer insurance"),
    ("education", "Below_GED", "Below GED", "higher", "higher attainment"),
    (
        "housing_stability",
        "Unstable",
        "Housing instability",
        "stable",
        "stable housing",
    ),
]


def tick(o):
    """Tick label for a row.  Dollars are escaped: two unescaped "$" in one
    string turn the text between them into mathtext, and the label renders as
    "Income <10, 000"."""
    return ("%s (vs %s)" % (o[2], o[3])).replace("$", chr(92) + "$")


D = {}
for r in joint:
    D.setdefault((r["domain"], r["level"]), {})[r["pathogen"]] = r

apply_style()
fig, (ax, bx) = plt.subplots(
    1,
    2,
    figsize=(180 * MM, 100 * MM),
    gridspec_kw={"width_ratios": [1.62, 1.0], "wspace": 0.88},
)

# ── panel a ──
ys = list(range(len(ORDER)))[::-1]
for yi, (dom, lev, lab, _rs, _rf) in zip(ys, ORDER):
    d = D[(dom, lev)]
    c, fl = d["COVID-19"], d["Influenza"]
    sc, sf = c["sig"] == "True", fl["sig"] == "True"
    if sc != sf:  # band the row that disagrees
        ax.axhspan(yi - 0.5, yi + 0.5, color="0.55", alpha=0.10, lw=0, zorder=0)
    ax.plot(
        [f(c["aor"]), f(fl["aor"])],
        [yi + 0.22, yi - 0.22],
        color="0.78",
        lw=2.0,
        solid_capstyle="round",
        zorder=1.4,
    )
    for v, col, mk, off, s in ((c, COVID, "o", 0.22, sc), (fl, FLU, "s", -0.22, sf)):
        a, lo, hi = f(v["aor"]), f(v["lo"]), f(v["hi"])
        ax.plot(
            [lo, hi],
            [yi + off, yi + off],
            color=col,
            lw=1.5,
            solid_capstyle="butt",
            zorder=2,
        )
        ax.plot(
            [a],
            [yi + off],
            marker=mk,
            ms=6.2,
            color=col,
            zorder=3,
            mfc=col if s else "white",
            mew=1.2,
        )

log_axis(
    ax,
    (0.72, 2.72),
    [0.8, 1, 1.25, 1.6, 2, 2.5],
    "Adjusted odds ratio (95% CI), log scale",
)
ax.set_yticks(ys)
ax.set_yticklabels([tick(o) for o in ORDER])
ax.set_ylim(-0.75, len(ORDER) - 0.25)
ax.spines["bottom"].set_bounds(0.72, 2.55)

# ── panel b ──
DOMS = [
    ("insurance_type", "Insurance"),
    ("income", "Income"),
    ("employment", "Employment"),
    ("housing", "Housing (ownership)"),
    ("education", "Education"),
    ("housing_stability", "Housing (stability)"),
]
pmap = {}
for r in inter:
    pmap.setdefault(r["domain"], {})[r["pathogen"]] = f(r["p"])

yb = list(range(len(DOMS)))[::-1]
for yi, (dom, lab) in zip(yb, DOMS):
    d = pmap.get(dom, {})
    for path, col, mk, off in (
        ("COVID-19", COVID, "o", 0.18),
        ("Influenza", FLU, "s", -0.18),
    ):
        if path not in d:
            continue
        p = d[path]
        bx.plot(
            [p],
            [yi + off],
            marker=mk,
            ms=6.2,
            color=col,
            mfc=col if p < 0.05 else "white",
            mew=1.2,
            zorder=3,
        )
bx.axvline(0.05, color="0.45", lw=1.0, ls=(0, (4, 3)), zorder=1)
bx.set_xscale("log")
#  the COVID-19 insurance interaction is P = 0.00128, the strongest result the
#  panel has; the old lower limit of 0.0016 clipped it off the axis entirely.
bx.set_xlim(0.0006, 1.5)
#  decade ticks; 0.05 is carried by the dashed line rather than a tick, which
#  would sit too close to 0.01 to read
bx.set_xticks([0.001, 0.01, 0.1, 1])
bx.set_xticklabels(["0.001", "0.01", "0.1", "1"])
import matplotlib as mpl

bx.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
bx.xaxis.set_minor_locator(mpl.ticker.NullLocator())
bx.set_yticks(yb)
bx.set_yticklabels([d[1] for d in DOMS])
bx.set_ylim(-0.75, len(DOMS) - 0.25)
bx.set_xlabel("P, domain × time interaction")
bx.tick_params(axis="y", length=0)
for s in ("top", "right", "left"):
    bx.spines[s].set_visible(False)

fig.legend(
    handles=[
        Line2D(
            [],
            [],
            color=COVID,
            marker="o",
            ms=6.2,
            lw=1.5,
            label="COVID-19  (CDR v7, 2020–2022)",
        ),
        Line2D(
            [],
            [],
            color=FLU,
            marker="s",
            ms=6.2,
            lw=1.5,
            label="Influenza  (CDR v9, 2018–2024)",
        ),
        Line2D(
            [],
            [],
            color=GREY,
            marker="o",
            ms=6.2,
            lw=0,
            mfc="white",
            mew=1.2,
            label="open marker: not significant",
        ),
    ],
    loc="lower center",
    bbox_to_anchor=(0.5, -0.13),
    ncol=3,
    columnspacing=2.2,
    handletextpad=0.5,
    frameon=False,
)
#  the design strip is panel (a) of every figure in the main text, so the two
#  data panels here are (b) and (c).
panel_labels([ax, bx], letters="bc", alpha=1.0)
os.makedirs(os.path.join(OUT, "panels"), exist_ok=True)
save(fig, os.path.join(OUT, "panels", "F4b_covid_vs_flu"))
print("  panel a rows: %d | panel b domains: %d" % (len(ORDER), len(DOMS)))
