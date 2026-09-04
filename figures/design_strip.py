# -*- coding: utf-8 -*-
"""The recurring design strip that heads every figure.

One drawing, five states. Each figure passes the axis it varies; that zone is
washed warm and the element that changed is drawn warm, while everything else
stays cool or grey. A reader who has read the strip once thereafter only has to
find the warm patch to know which story the figure below is telling.

    highlight = None        the design itself                  (Figure 1)
    highlight = "domains"   the five domains entered together  (Figure 2, Test 1)
    highlight = "eras"      the same model within each era     (Figure 3, Test 2)
    highlight = "pathogen"  the same design, second pathogen   (Figure 4, Test 3)
    highlight = "race"      race against the social domains    (Figure 5, Test 4)

Where the warm wash sits is itself informative: zone A means the cohort changed,
zone C means the model changed.

The strip carries no data, and every term in it is defined in Methods. Person
glyphs are drawn from a marker and a line segment rather than from patches, so
they stay upright and circular whatever aspect ratio the strip is rendered at.
Nothing is set below 10 pt, which is the OUP floor the rest of the set observes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from style import ERA, FLU, GREY, INK, MM, NAVY, TEAL, apply_style, save

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "figures"
)
WARM_BG = "#FAE7E1"
COOL_BG = "#EFF2F5"
PAD = 0.013

#  Three zones, left to right: who is compared, what they are matched on, and
#  the model.  Widths are set by the longest string each zone has to carry.
ZONES = {"A": (0.004, 0.230), "B": (0.248, 0.560), "C": (0.578, 0.996)}

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


def draw_strip(ax, highlight=None):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    warm = FLU if highlight == "pathogen" else "#B2352A"
    ax0 = ZONES["A"][0] + PAD
    bx0 = ZONES["B"][0] + PAD
    cx0 = ZONES["C"][0] + PAD
    T = []  # (artist, zone) for the overflow check

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

    def chain(zone, x, y, parts, size=BODY):
        """Lay coloured fragments end to end on one line, each placed at the
        measured right edge of the one before it, so a word inside a sentence
        can be recoloured without hand-tuned offsets."""
        fig = ax.figure
        inv = ax.transData.inverted()
        cx = x
        for frag, col, wgt in parts:
            t = put(zone, cx, y, frag, size, col, wgt)
            fig.canvas.draw()
            bb = t.get_window_extent(fig.canvas.get_renderer())
            cx = inv.transform((bb.x1, bb.y1))[0]

    # ---------------- zone A: who is compared with whom
    wash(ax, "A", highlight == "pathogen")
    put("A", ax0, 0.945, "Matched sets", HEAD, INK, "bold")
    put("A", ax0, 0.845, "1 case : 4 controls", SMALL, GREY)
    cohorts = [("All of Us", NAVY), ("MarketScan", TEAL)]
    if highlight == "pathogen":
        cohorts = cohorts + [("All of Us, influenza", FLU)]
    slots = {2: [0.555, 0.215], 3: [0.640, 0.395, 0.150]}[len(cohorts)]
    for (name, col), yy in zip(cohorts, slots):
        put("A", ax0, yy + 0.098, name, BODY, col, "bold")
        person(ax, ax0 + 0.013, yy, col, True)
        for k in range(4):
            person(ax, ax0 + 0.052 + k * 0.028, yy, col, False)

    # ---------------- zone B: what they are matched on
    wash(ax, "B", False)
    put("B", bx0, 0.945, "Matched on", HEAD, INK, "bold")
    for k, v in enumerate(
        ["survey or enrolment date", "distinct diagnoses", "length of record"]
    ):
        put("B", bx0, 0.770 - k * 0.128, "•  " + v)
    put("B", bx0, 0.330, "pre-index records only", BODY, NAVY, "bold")
    put("B", bx0, 0.195, "social domains: not matched", SMALL, GREY)

    # ---------------- zone C: the model, and the window it predicts
    wash(ax, "C", highlight in ("domains", "eras", "race"))
    put("C", cx0, 0.945, "Conditional logistic model", HEAD, INK, "bold")
    #  race sits in the base model of every fit.  Figure 5 asks what the social
    #  domains take away from it, so there and only there the word is warm.
    rc, rw = (warm, "bold") if highlight == "race" else (INK, "normal")
    chain(
        "C",
        cx0,
        0.795,
        [
            ("base:  sex,", INK, "normal"),
            (" race", rc, rw),
            (", ethnicity, age, wave,", INK, "normal"),
        ],
    )
    put("C", cx0 + 0.030, 0.685, "vaccination, 19 comorbidities")
    dom = highlight == "domains"
    dcol, dw = (warm, "bold") if dom else (INK, "normal")
    put("C", cx0, 0.525, "+  insurance, income, education,", BODY, dcol, dw)
    put("C", cx0 + 0.022, 0.415, "employment, housing", BODY, dcol, dw)

    y0 = 0.255
    if highlight == "eras":
        for k, (x0, x1) in enumerate(
            [(cx0, cx0 + 0.072), (cx0 + 0.072, cx0 + 0.136), (cx0 + 0.136, cx0 + 0.218)]
        ):
            ax.add_patch(
                Rectangle(
                    (x0, y0 - 0.042),
                    x1 - x0,
                    0.084,
                    facecolor=ERA[k],
                    edgecolor="white",
                    lw=0.8,
                    zorder=3,
                )
            )
    else:
        ax.add_patch(
            Rectangle(
                (cx0, y0 - 0.042),
                0.218,
                0.084,
                facecolor="0.87",
                edgecolor="none",
                zorder=3,
            )
        )
    put("C", cx0 + 0.230, y0, "study period", SMALL, GREY)

    #  one line, always in the same place, saying what this figure varies
    TAIL = {
        None: ("outcome: hospitalization ≤14 days of index", GREY, "normal"),
        "domains": ("all five together, or one at a time", warm, "bold"),
        "eras": ("the same model, fitted era by era", warm, "bold"),
        "pathogen": ("the same design, a second pathogen", warm, "bold"),
        "race": ("what the domains absorb of race", warm, "bold"),
    }
    tail, tcol, tw = TAIL[highlight]
    put("C", cx0, 0.095, tail, SMALL, tcol, tw)
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
    os.makedirs(os.path.join(OUT, "panels"), exist_ok=True)
    problems = []
    for tag, hl in (
        ("F1_design", None),
        ("F2_domains", "domains"),
        ("F3_eras", "eras"),
        ("F4_pathogen", "pathogen"),
        ("F5_race", "race"),
    ):
        fig, ax = plt.subplots(figsize=(180 * MM, 62 * MM))
        fig.subplots_adjust(left=0.003, right=0.997, top=0.995, bottom=0.005)
        T = draw_strip(ax, hl)
        problems += [(tag,) + b for b in overflow(fig, ax, T)]
        save(fig, os.path.join(OUT, "panels", "strip_" + tag))
        plt.close(fig)
    if problems:
        print("\nOVERFLOW")
        for p in problems:
            print("  ", p)
    else:
        print("\nno overflow: every string sits inside its zone")
