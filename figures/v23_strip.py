# -*- coding: utf-8 -*-
"""The design strip for the v23 (JAMA Network Open) figure set.

One drawing, three states. Every figure in the set carries it, and the reader
who has read it once thereafter only has to find the warm patch to know what
the figure below varies.

    highlight = "model"    one domain at a time, then all together   (Figure 1)
    highlight = "period"   the same model, fitted era by era         (Figure 2)
    highlight = None       the design itself, nothing varied

Where the warm wash sits is the message: zone A means the *cohort* was cut,
zone C means the *model* changed. Exactly one zone is ever warm.

Two warm channels, deliberately kept apart. A warm *hue* (brick, amber) always
means a pathogen and never anything else, so the strip's arms and the panel
titles below it carry the same key. A warm *wash* always means "this is what the
figure varies". Hue and field are different channels, so neither has to borrow
the other's meaning.

This is a different strip from `design_strip.py`, which belongs to the JAMIA
submission: that one carries MarketScan in zone A and names "wave" in zone C.
The v23 set has two All of Us arms and no claims cohort, so the strip was
rewritten rather than patched, and the old one is left intact for the archived
submission it documents.

Every fact in the strip is from the frozen Methods:
  - 1 case : 4 controls, nearest neighbour with replacement, 0.2 SD caliper
  - matched on first Basics Survey date, distinct diagnoses, length of record,
    each counted over records dated before the index date
  - influenza additionally exact-matched on season
  - outcome: hospitalization within 14 days of the index date, both arms
  - base model: sex, race, ethnicity, age and 19 Charlson conditions in both
    arms; the COVID-19 arm adds vaccination and pandemic wave. Influenza
    vaccination is not adjusted for, and season is constant inside an
    influenza matched set, so it drops out of the conditional likelihood.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from style import COVID, FLU, GREY, INK, MM, NAVY, apply_style, save

WARM_BG = "#FAE7E1"
COOL_BG = "#EFF2F5"
PAD = 0.013

#  three zones, left to right: who is compared, what they are matched on,
#  and the model that is fitted inside the matched sets
ZONES = {"A": (0.004, 0.268), "B": (0.286, 0.588), "C": (0.606, 0.996)}

HEAD, BODY, SMALL = 11, 10, 10


def person(ax, x, y, color, filled):
    ax.plot(
        [x],
        [y + 0.048],
        marker="o",
        ms=5.0,
        color=color,
        mfc=color if filled else "white",
        mew=1.3,
        zorder=5,
        clip_on=False,
    )
    ax.plot(
        [x, x],
        [y - 0.046, y + 0.012],
        color=color,
        lw=4.4 if filled else 1.5,
        solid_capstyle="round",
        zorder=5,
        clip_on=False,
    )


def wash(ax, key, warm):
    x0, x1 = ZONES[key]
    ax.add_patch(
        FancyBboxPatch(
            (x0, 0.02),
            x1 - x0,
            0.96,
            boxstyle="round,pad=0.004,rounding_size=0.014",
            facecolor=WARM_BG if warm else COOL_BG,
            edgecolor="none",
            zorder=0,
            clip_on=False,
        )
    )


def draw_strip(ax, highlight="model"):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax0, bx0, cx0 = (ZONES[k][0] + PAD for k in "ABC")
    T = []

    def put(zone, x, y, s, size=BODY, color=INK, weight="normal"):
        t = ax.text(
            x,
            y,
            s,
            ha="left",
            va="center",
            fontsize=size,
            color=color,
            fontweight=weight,
        )
        T.append((t, zone))
        return t

    # ---- zone A: who is compared with whom -------------------------------
    wash(ax, "A", highlight == "period")
    put("A", ax0, 0.930, "Matched sets", HEAD, INK, "bold")
    put("A", ax0, 0.822, "1 case : 4 controls", SMALL, GREY)
    for (name, col), yy in zip(
        [("COVID-19", COVID), ("Influenza", FLU)], [0.520, 0.185]
    ):
        put("A", ax0, yy + 0.115, name, BODY, col, "bold")
        person(ax, ax0 + 0.014, yy, col, True)
        for k in range(4):
            person(ax, ax0 + 0.058 + k * 0.032, yy, col, False)
    if highlight == "period":
        put("A", ax0, 0.060, "cut into eras", SMALL, INK, "bold")
    else:
        put("A", ax0, 0.060, "All of Us, one program", SMALL, GREY)

    # ---- zone B: what they are matched on --------------------------------
    wash(ax, "B", False)
    put("B", bx0, 0.930, "Matched on", HEAD, INK, "bold")
    for k, v in enumerate(
        ["first survey date", "distinct diagnoses", "length of record"]
    ):
        put("B", bx0, 0.775 - k * 0.125, "•  " + v)
    put("B", bx0, 0.395, "before the index date only", BODY, NAVY, "bold")
    put("B", bx0, 0.265, "influenza also exact on season", SMALL, GREY)
    put("B", bx0, 0.135, "social domains: not matched", SMALL, GREY)

    # ---- zone C: the model fitted inside the matched sets -----------------
    wash(ax, "C", highlight == "model")
    put("C", cx0, 0.930, "Conditional logistic model", HEAD, INK, "bold")
    #  The two arms do not carry an identical base model, and the strip says
    #  so rather than averaging over the difference: influenza vaccination is
    #  not adjusted for, and season is constant inside an influenza matched set
    #  so it drops out of the conditional likelihood.  Both are stated in the
    #  Methods; verified against 02_models.R and 03f_flu_mi40.R.
    put("C", cx0, 0.822, "base:  sex, race, ethnicity, age,")
    put("C", cx0 + 0.030, 0.722, "19 comorbidities")
    put("C", cx0 + 0.030, 0.622, "COVID-19 also: vaccination, wave", SMALL, GREY)
    mw = "bold" if highlight == "model" else "normal"
    #  five domain names, as the Methods names them; the housing domain
    #  contributes two items (tenure and stability), which Figure 1 shows as
    #  two blocks and the legend explains.  Kept to five here so the strip
    #  stays a schematic rather than a variable list.
    put("C", cx0, 0.478, "+  income, employment, housing,", BODY, INK, mw)
    put("C", cx0 + 0.024, 0.378, "insurance, education", BODY, INK, mw)
    put("C", cx0, 0.232, "outcome:  hospitalized \u2264 14 days", SMALL, GREY)
    ax.plot(
        [cx0, ZONES["C"][1] - 0.018],
        [0.158, 0.158],
        color="#C9B2AA" if highlight == "model" else "#C6CDD4",
        lw=0.8,
        zorder=2,
        clip_on=False,
    )

    TAIL = {
        None: ("the design, held fixed", GREY, "normal"),
        "model": ("one domain at a time, then all together", INK, "bold"),
        "period": ("the same model, fitted era by era", INK, "bold"),
    }
    tail, tcol, tw = TAIL[highlight]
    put("C", cx0, 0.078, tail, SMALL, tcol, tw)
    return T


def overflow(fig, ax, T):
    """Report any string that leaves the zone it was drawn in."""
    fig.canvas.draw()
    inv = ax.transData.inverted()
    bad = []
    for t, zone in T:
        bb = t.get_window_extent(fig.canvas.get_renderer())
        x1 = inv.transform((bb.x1, bb.y1))[0]
        lim = ZONES[zone][1] - 0.004
        if x1 > lim:
            bad.append((zone, round(x1 - lim, 4), t.get_text()))
    return bad


if __name__ == "__main__":
    apply_style()
    out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "results",
        "figures",
        "v23",
        "panels",
    )
    os.makedirs(out, exist_ok=True)
    problems = []
    for tag, hl in (
        ("F1_model", "model"),
        ("F2_period", "period"),
        ("F0_design", None),
    ):
        fig, ax = plt.subplots(figsize=(180 * MM, 44 * MM))
        fig.subplots_adjust(left=0.003, right=0.997, top=0.995, bottom=0.005)
        T = draw_strip(ax, hl)
        problems += [(tag,) + b for b in overflow(fig, ax, T)]
        save(fig, os.path.join(out, "strip_" + tag))
    print(
        "\nOVERFLOW" if problems else "\nno overflow: every string sits inside its zone"
    )
    for p in problems:
        print("  ", p)
