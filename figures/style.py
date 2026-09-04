# -*- coding: utf-8 -*-
"""Shared style for the v20 figures.

Type. OUP artwork guidance for its journals asks for Arial, nothing below
10 pt, axis labels and legends at 10 pt and in-figure text at 12 pt, a minimum
width of 168 mm and a white background. Arial is not installed here; Liberation
Sans is, and it is metrically identical to Arial, so a production substitution
will not reflow the labels. Fonts embed as type 42 so the text stays editable.

Colour, one rule for the whole set:

    WARM  = pathogen              COVID-19 deep brick, influenza amber
    COOL  = our own analysis      navy = the estimate the claim rests on,
                                  teal = the comparison it is read against
    COOL RAMP = ordered time      light to dark across pandemic eras
    GREY  = reference line, connectors, and anything not significant

So warm never means a model and cool never means a disease. A reader who learns
the key on one figure carries it to the next. Filled marker = interval excludes
1.0; open marker = it does not.
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
RULE = "#AAAAAA"
INK = "#222222"

SANS = ["Arial", "Liberation Sans", "Helvetica", "Nimbus Sans", "DejaVu Sans"]


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


def panel_labels(axes, letters="abcdefg", alpha=0.0, dy=0.010):
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
