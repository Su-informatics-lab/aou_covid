# -*- coding: utf-8 -*-
"""Shared style for the figures (v26 palette, R9 visualization review).

Type. Arial, embedded as type 42 so the text stays editable (Liberation Sans
is the metric-identical fallback). The figures are drawn at their final print
width (180 mm for two-column figures) and nothing is placed outside the axes
grid, so `bbox_inches="tight"` cannot widen the canvas. JAMA Network Open
re-creates accepted figures in house style; its font and width minimums were
not verified from the author instructions (see working/v25/reviews_R9viz/).

Colour, one key for the whole set:

    HUE = the variable        INCOME navy (income below $10 000),
                              MEDICAID reddish purple (Okabe-Ito #CC79A7,
                              separable from navy under deuteranopia),
                              REFG grey (the reference group, and the part
                              of an association shared with the other items)
    LIGHTNESS = the model     a tint of the hue = fitted alone,
                              the full hue = jointly adjusted
    WARM = the virus only     COVID-19 brick, influenza amber; never a model,
                              never a policy
    HATCH/OUTLINE = weak or withheld (pandemic influenza seasons; <20 cells)

Open marker = the 95% CI includes 1, and nothing else.
"""

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

MM = 1 / 25.4

COVID = "#B2352A"  # warm, deep brick
FLU = "#E8873A"  # warm, amber
NAVY = "#2C4B7C"  # cool, dark   — primary / adjusted / joint
TEAL = "#3B9AB2"  # cool, mid    — comparison / base / domain-specific
ERA = ("#9CC3D5", "#3D7FA6", "#14395C")  # ordered: pre-Delta, Delta, Omicron
GREY = "#8C8C8C"
# v26 key (R9): hue = variable, tint = fitted alone, warm = virus only
INCOME = "#1F3A68"
INCOME_TINT = "#9FB0CC"
MEDICAID = "#CC79A7"
MEDICAID_TINT = "#E3AFCD"
REFG = "#9A9A9A"
SHARED = "#C9C9C9"
COVID_TINT = "#E3B4AE"
FLU_TINT = "#F6D2B2"
TXT_GREY = "#666666"  # informative grey text (contrast about 5.7:1); lighter greys for rules only
DARK = "#4D4D4D"
RULE = "#AAAAAA"
INK = "#222222"

SANS = ["Arial", "Liberation Sans", "Helvetica", "Nimbus Sans", "DejaVu Sans"]
PT_SMALL, PT_BODY, PT_HEAD = 7, 8, 9  # in-figure text at 180 mm print width


def apply_style():
    r = mpl.rcParams
    r["pdf.fonttype"] = r["ps.fonttype"] = 42
    r["svg.fonttype"] = "none"
    r["font.family"] = "sans-serif"
    r["font.sans-serif"] = SANS
    r["font.size"] = 10
    r["axes.labelsize"] = 10
    r["axes.titlesize"] = 11
    r["xtick.labelsize"] = r["ytick.labelsize"] = 10
    r["legend.fontsize"] = 10
    r["text.color"] = r["axes.labelcolor"] = INK
    r["xtick.color"] = r["ytick.color"] = INK
    r["axes.edgecolor"] = INK
    r["axes.linewidth"] = 0.8
    r["xtick.major.width"] = r["ytick.major.width"] = 0.8
    r["xtick.major.size"] = 3.5
    r["lines.linewidth"] = 1.3
    r["legend.frameon"] = False
    r["legend.handlelength"] = 1.5
    r["legend.labelspacing"] = 0.35
    r["axes.grid"] = False
    r["axes.spines.top"] = r["axes.spines.right"] = False
    r["figure.facecolor"] = r["savefig.facecolor"] = "white"
    r["mathtext.default"] = "regular"


def sig(lo, hi):
    return lo > 1 or hi < 1


def log_axis(ax, xlim, xticks, xlabel, ref=1.0):
    ax.axvline(ref, color=RULE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.set_xticks(xticks)
    ax.set_xticklabels(["%g" % t for t in xticks])
    ax.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def panel_labels(axes, letters="ABCDEFG", alpha=0.0, dy=0.010):
    """Panel letters sit at the top-left of each panel's own tight bounding
    box, so they clear the row labels rather than floating over the plot.
    Single-panel figures call this with the default alpha=0: the space is
    reserved but nothing prints. Pass alpha=1.0 for a multi-panel figure."""
    fig = axes[0].figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    for ax, lab in zip(axes, letters):
        bb = ax.get_tightbbox(rend).transformed(inv)
        fig.text(
            bb.x0,
            bb.y1 + dy,
            lab,
            fontsize=12,
            fontweight="bold",
            ha="left",
            va="bottom",
            alpha=alpha,
            color=INK,
        )


def save(fig, stem):
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.png", dpi=400, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {stem}.pdf and {stem}.png")
