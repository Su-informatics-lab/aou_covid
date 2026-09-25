# -*- coding: utf-8 -*-
"""Figure 1 — what happens to each social domain when the others are in the
same model.

The figure performs one manipulation and nothing else. The people, the matched
sets, the outcome and the clinical covariates are held fixed; only the model
changes. Read each arrow from its teal tail to its navy head: teal is the
domain fitted on its own, navy is the same domain fitted with the other five
beside it. Medicaid enters at 1.54 and lands on 1.11; income and employment
lose magnitude and keep their intervals clear of 1. Panel C is the same
manipulation in a second pathogen and a second Curated Data Repository version,
so it replicates the manipulation rather than adding a second one.

Rows are ordered by what the manipulation does to them — survivors first,
collapsers last — so the eye travels down a gradient of evidence rather than
down an alphabet, and the arrows in the lower blocks visibly converge on the
dashed null.

Colour, following the set's rule:
    warm hue   = pathogen        brick COVID-19, amber influenza (titles only)
    warm wash  = what varies     the model, so zone C of the strip
    cool marks = our estimates   navy is the estimate the claim rests on,
                                 teal is the comparison it is read against
    filled marker = 95% CI excludes 1.0;  open = it does not
    grey square   = the reference level of that domain in that panel

Panels are lettered A, B, C in capitals, which is the JAMA Network convention;
the Nature-family lowercase form is wrong for this target. The journal's own
figure specification has not been read off its site, so the width is the safe
180 mm double-column measure and nothing is set below 10 pt.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
import pandas as pd
from style import COVID, FLU, GREY, INK, MM, NAVY, RULE, TEAL, apply_style, sig
from v23_strip import draw_strip

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "results", "figures", "v24", "Figure1_data.csv")
OUT = os.path.join(HERE, "..", "results", "figures", "v24")

BOTH = ("COVID-19", "Influenza")

#  (level key, row label, arms in which the level is estimated,
#                         arms in which the level IS the reference)
BLOCKS = [
    (
        "income",
        "Household income",
        [
            ("less_10k", "< $10,000", BOTH, ()),
            ("10k_25k", "$10,000–24,999", BOTH, ()),
            ("25k_35k", "$25,000–34,999", BOTH, ()),
            (None, "$35,000–99,999", (), BOTH),
            ("100k_150k", "$100,000–149,999", BOTH, ()),
            ("150k_200k", "$150,000–199,999", BOTH, ()),
            ("more_200k", "≥ $200,000", BOTH, ()),
        ],
    ),
    (
        "employment",
        "Employment",
        [
            ("Unemployed", "Unemployed", BOTH, ()),
            ("Others", "Other", BOTH, ()),
            ("Student", "Student", BOTH, ()),
        ],
    ),
    (
        "housing",
        "Housing tenure",
        [
            ("Rent", "Renting", BOTH, ()),
            ("Others", "Other arrangement", BOTH, ()),
        ],
    ),
    (
        "stability",
        "Housing stability",
        [
            ("Unstable", "Unstable", BOTH, ()),
        ],
    ),
    (
        "insurance",
        "Insurance",
        [
            ("Medicaid", "Medicaid", BOTH, ()),
            ("Other_None", "Other or none", BOTH, ()),
            ("Medicare", "Medicare", BOTH, ()),
            ("Missing", "Not administered", BOTH, ()),
        ],
    ),
    #  Education is the one domain the two Curated Data Repository versions
    #  code differently, so the block carries its own reference in each
    #  panel rather than a shared one.
    #
    #  A fourth level, "never attended school", is deliberately absent. It
    #  has fewer than 20 participants in the COVID-19 arm; Table 1 already
    #  suppresses that cell, and All of Us prohibits distributing aggregate
    #  statistics corresponding to fewer than 20 participants -- an odds
    #  ratio is such a statistic. The level stays in the model as a
    #  covariate; only its estimate is withheld. It does not occur at all
    #  in the influenza arm, so no influenza estimate was ever at issue.
    (
        "education",
        "Education",
        [
            ("Below_GED", "Below GED", BOTH, ()),
            ("GED_or_College", "GED or college", ("COVID-19",), ("Influenza",)),
            ("Advanced", "Advanced degree", ("Influenza",), ("COVID-19",)),
        ],
    ),
]

REFTEXT = {
    "income": {"COVID-19": "", "Influenza": ""},
    "employment": {"COVID-19": "vs employed", "Influenza": "vs employed"},
    "housing": {"COVID-19": "vs owns home", "Influenza": "vs owns home"},
    "stability": {"COVID-19": "vs stable", "Influenza": "vs stable"},
    "insurance": {
        "COVID-19": "vs employer-sponsored",
        "Influenza": "vs employer-sponsored",
    },
    "education": {"COVID-19": "", "Influenza": ""},
}

ARMS = [
    ("COVID-19", COVID, "3,997 cases  ·  15,523 controls"),
    ("Influenza", FLU, "1,672 case seasons  ·  6,616 controls"),
]

XLIM = (0.55, 2.75)
XTICKS = [0.6, 0.8, 1.0, 1.5, 2.0, 2.5]
XLABEL = "Adjusted odds ratio of hospitalization (95% CI, log scale)"
HEADH = 0.90
DY = 0.190
CONN = "#BFBFBF"
REFSQ = "#B4B4B4"


def layout():
    """y grows downward; the axes are inverted so the first block prints top."""
    y, heads, rows = 0.0, [], []
    for dom, title, levels in BLOCKS:
        y += HEADH
        heads.append((dom, title, y))
        y += 0.30
        for key, label, arms, refarms in levels:
            y += 1.0
            rows.append((dom, key, label, arms, refarms, y))
        y += 0.35
    return heads, rows, y + 0.35


def draw_panel(ax, d, arm, heads, rows, ymax):
    ax.set_xscale("log")
    ax.set_xlim(*XLIM)
    ax.set_ylim(0, ymax)
    ax.invert_yaxis()
    ax.axvline(1.0, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)

    for dom, title, y in heads:
        ax.plot(XLIM, [y + 0.16] * 2, color="#D8D8D8", lw=0.7, zorder=1, clip_on=False)
        if REFTEXT[dom][arm]:
            ax.text(
                XLIM[1],
                y - 0.04,
                REFTEXT[dom][arm],
                ha="right",
                va="center",
                fontsize=10,
                color=GREY,
            )

    sub = d[d.arm == arm]
    for dom, key, label, arms, refarms, y in rows:
        if arm in refarms:  # this level is the reference
            ax.plot(
                [1.0],
                [y],
                marker="s",
                ms=3.8,
                color=REFSQ,
                mec=REFSQ,
                zorder=4,
                clip_on=False,
            )
            continue
        if arm not in arms:  # level absent in this cohort
            continue
        hit = sub[(sub.domain == dom) & (sub.level == key)]
        if not len(hit):
            raise KeyError(
                "%s declares %s/%s for %s, but the source data has "
                "no such row" % (os.path.basename(DATA), dom, key, arm)
            )
        r = hit.iloc[0]
        ax.annotate(
            "",
            xy=(r.joint_aor, y + DY),
            xytext=(r.ds_aor, y - DY),
            arrowprops=dict(
                arrowstyle="-|>",
                color=CONN,
                lw=0.9,
                shrinkA=3.2,
                shrinkB=4.4,
                mutation_scale=7,
            ),
            annotation_clip=False,
            zorder=2,
        )
        for aor, lo, hi, col, yy in (
            (r.ds_aor, r.ds_lo, r.ds_hi, TEAL, y - DY),
            (r.joint_aor, r.joint_lo, r.joint_hi, NAVY, y + DY),
        ):
            ax.plot([lo, hi], [yy, yy], color=col, lw=1.1, zorder=3)
            f = sig(lo, hi)
            ax.plot(
                [aor],
                [yy],
                marker="o",
                ms=4.8,
                color=col,
                mfc=col if f else "white",
                mew=1.2,
                zorder=4,
            )

    ax.set_xticks(XTICKS)
    ax.set_xticklabels(["%g" % t for t in XTICKS])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.set_yticks([])
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def draw_labels(ax, heads, rows, ymax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, ymax)
    ax.invert_yaxis()
    ax.axis("off")
    for dom, title, y in heads:
        ax.text(
            0.0,
            y,
            title,
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=INK,
        )
    for dom, key, label, arms, refarms, y in rows:
        one_arm_only = len(arms) == 1 and not refarms
        ax.text(
            1.0,
            y,
            label,
            ha="right",
            va="center",
            fontsize=10,
            color=GREY if (key is None or one_arm_only) else INK,
        )


def draw_titles(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_legend(ax):
    """Two lines, laid out by measuring each fragment rather than by guessing
    offsets, so the key never overlaps itself when a word changes."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig = ax.figure
    fig.canvas.draw()
    inv = ax.transData.inverted()

    def txt(x, y, s_, color=INK, weight="normal", gap=0.012):
        t = ax.text(
            x,
            y,
            s_,
            ha="left",
            va="center",
            fontsize=10,
            color=color,
            fontweight=weight,
            clip_on=False,
        )
        fig.canvas.draw()
        bb = t.get_window_extent(fig.canvas.get_renderer())
        return inv.transform((bb.x1, bb.y1))[0] + gap

    def dot(x, y, color, filled, ms=4.8, marker="o"):
        ax.plot(
            [x],
            [y],
            marker=marker,
            ms=ms,
            color=color,
            mfc=color if filled else "white",
            mec=color,
            mew=1.2,
            clip_on=False,
            zorder=4,
        )
        return x + 0.017

    y1, y2 = 0.74, 0.22
    x = 0.006
    dot(x, y1, TEAL, True)
    ax.annotate(
        "",
        xy=(x + 0.070, y1),
        xytext=(x + 0.008, y1),
        arrowprops=dict(arrowstyle="-|>", color=CONN, lw=0.9, mutation_scale=7),
        annotation_clip=False,
    )
    x = dot(x + 0.078, y1, NAVY, True)
    x = txt(x, y1, "the domain fitted on its own", TEAL)
    x = txt(x, y1, "\u2192", GREY)
    x = txt(x, y1, "the same domain fitted with the others", NAVY)

    x = 0.006
    x = dot(x, y2, INK, True)
    x = txt(x, y2, "95% CI excludes 1.0", INK, gap=0.030)
    x = dot(x, y2, INK, False)
    x = txt(x, y2, "it does not", INK, gap=0.030)
    x = dot(x, y2, REFSQ, True, ms=3.8, marker="s")
    x = txt(x, y2, "reference level for that domain and cohort", GREY)


def main():
    apply_style()
    d = pd.read_csv(DATA)
    heads, rows, ymax = layout()

    fig = plt.figure(figsize=(180 * MM, 181 * MM))
    gs = fig.add_gridspec(
        4,
        3,
        height_ratios=[0.222, 0.059, 0.661, 0.058],
        width_ratios=[0.248, 0.376, 0.376],
        left=0.008,
        right=0.992,
        top=0.972,
        bottom=0.070,
        hspace=0.0,
        wspace=0.055,
    )

    ax_strip = fig.add_subplot(gs[0, :])
    draw_strip(ax_strip, "model")

    ax_lab = fig.add_subplot(gs[2, 0])
    draw_labels(ax_lab, heads, rows, ymax)

    axes = []
    for k, (arm, col, n) in enumerate(ARMS):
        ax_t = fig.add_subplot(gs[1, 1 + k])
        draw_titles(ax_t)
        ax_t.text(
            0.000,
            0.66,
            "BC"[k],
            ha="left",
            va="center",
            fontsize=12,
            fontweight="bold",
            color=INK,
        )
        ax_t.plot([0.072], [0.66], marker="s", ms=7, color=col, mec=col, clip_on=False)
        ax_t.text(
            0.104,
            0.66,
            arm,
            ha="left",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=col,
        )
        ax_t.text(0.000, 0.16, n, ha="left", va="center", fontsize=10, color=GREY)

        ax = fig.add_subplot(gs[2, 1 + k])
        draw_panel(ax, d, arm, heads, rows, ymax)
        axes.append(ax)

    #  the bottom band carries, in order, the tick labels drawn by the panels,
    #  one shared axis label, and the key
    ax_foot = fig.add_subplot(gs[3, :])
    ax_foot.set_xlim(0, 1)
    ax_foot.set_ylim(0, 1)
    ax_foot.axis("off")
    b0, b1 = axes[0].get_position(), axes[1].get_position()
    fb = ax_foot.get_position()
    xmid = ((b0.x0 + b1.x1) / 2 - fb.x0) / fb.width
    ax_foot.text(xmid, 0.16, XLABEL, ha="center", va="center", fontsize=10, color=INK)
    ax_key = fig.add_axes([b0.x0, 0.012, b1.x1 - b0.x0, 0.046])
    draw_legend(ax_key)

    bb = ax_strip.get_position()
    fig.text(
        0.002,
        bb.y1 + 0.006,
        "A",
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=INK,
    )

    #  Saved on a fixed canvas, not with bbox_inches="tight": several artists
    #  are drawn with clip_on=False so that markers sit on the axis line, and a
    #  tight box would silently grow the figure past the column width the
    #  layout was designed to.  The width below is the width that ships.
    stem = os.path.join(OUT, "Figure1")
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=400)
    plt.close(fig)
    print("  wrote %s.pdf and %s.png" % (stem, stem))


if __name__ == "__main__":
    main()
