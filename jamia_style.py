"""
jamia_style.py — single source of truth for all figures in the AoU COVID/SDoH paper.

Every figure imports from here so that fonts, palette, line weights, marker
sizes, reference-line style, and export settings are identical across
Figures 3-5 and the eFigures. This is what was missing before: Figure 4 was
drawn standalone and drifted from the others.

JAMIA column widths (not Nature's 89/183 mm):
    single = 3.25 in, one-half = 5.0 in, double = 6.875 in
Colorblind-safe Wong/Okabe-Ito palette; type-42 font embedding.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---------------------------------------------------------------- palette
WONG = {
    "black":     "#000000",
    "orange":    "#E69F00",
    "sky":       "#56B4E9",
    "green":     "#009E73",
    "yellow":    "#F0E442",
    "blue":      "#0072B2",
    "vermillion":"#D55E00",
    "purple":    "#CC79A7",
}
# Semantic roles — fixed for the whole paper. Never reassign.
C_RISK   = WONG["vermillion"]   # elevated odds, significant
C_PROT   = WONG["blue"]         # lower odds, significant
C_NS     = "#9A9A9A"            # not statistically significant
C_DOMAIN = WONG["vermillion"]   # domain-specific model
C_JOINT  = WONG["blue"]         # joint model
C_MS     = WONG["orange"]       # MarketScan cohort
C_AOU    = WONG["blue"]         # All of Us cohort
C_CONN   = "#C8C8C8"            # dumbbell connector / attenuation gap
C_BAND   = "#F2F2F2"            # alternating group band
C_REF    = "#000000"            # reference line at AOR = 1
# Right-hand numeric annotations stay black. The markers already carry series
# identity through hue, so repeating hue in the text only adds noise; the two
# stacked rows are separated by lightness instead.
C_TXT1   = "#000000"            # first annotation row  (domain-specific / AoU)
C_TXT2   = "#707070"            # second annotation row (joint / MarketScan)
# Alternating band must stop at the plot's right edge (axes fraction 1.0) so it
# never runs underneath the numeric column.
BAND_RIGHT = 1.0

WIDTHS = {"single": 3.25, "one-half": 5.0, "double": 6.875}


def apply_style():
    mpl.rcParams.update({
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 7,
        "axes.labelsize": 7, "axes.titlesize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
        "legend.fontsize": 6, "legend.frameon": False, "legend.borderpad": 0.3,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.direction": "out", "ytick.direction": "out",
        "lines.linewidth": 0.9, "lines.markersize": 3.5,
        "axes.grid": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.dpi": 600, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def figsize(cols="double", height=None, ratio=0.75):
    w = WIDTHS[cols]
    return (w, height if height is not None else w * ratio)


def sig_color(aor, pstr, ns=C_NS):
    """Vermillion if significantly elevated, blue if significantly lower, grey if NS."""
    if pstr == "":
        return ns
    return C_RISK if aor > 1 else C_PROT


def forest_row(ax, y, aor, lo, hi, color, xmin, xmax, marker="o", size=16,
               filled=True, lw=0.9, capsize=0.10, zorder=5):
    """One estimate: CI whisker with end caps, clamped to axis with arrows if off-scale."""
    clo, chi = max(lo, xmin * 1.001), min(hi, xmax * 0.999)
    ax.plot([clo, chi], [y, y], color=color, lw=lw, solid_capstyle="butt", zorder=zorder - 1)
    if hi > xmax:
        ax.annotate("", xy=(xmax, y), xytext=(xmax * 0.955, y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw), zorder=zorder - 1)
    else:
        ax.plot([chi, chi], [y - capsize, y + capsize], color=color, lw=lw * 0.9, zorder=zorder - 1)
    if lo < xmin:
        ax.annotate("", xy=(xmin, y), xytext=(xmin * 1.045, y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw), zorder=zorder - 1)
    else:
        ax.plot([clo, clo], [y - capsize, y + capsize], color=color, lw=lw * 0.9, zorder=zorder - 1)
    px = min(max(aor, xmin * 1.02), xmax * 0.98)
    ax.scatter([px], [y], marker=marker, s=size,
               facecolor=color if filled else "white",
               edgecolor=color, linewidths=0.8, zorder=zorder, clip_on=False)


def ref_line(ax, x=1.0):
    ax.axvline(x, color=C_REF, lw=0.7, zorder=1)


def log_axis(ax, ticks, xmin, xmax, label="Adjusted odds ratio (95% CI)"):
    ax.set_xscale("log")
    ax.set_xlim(xmin, xmax)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.minorticks_off()
    ax.set_xlabel(label)
    ax.spines["bottom"].set_bounds(xmin, xmax)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def panel_label(ax, letter, x=-0.02, y=1.02):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=8,
            fontweight="bold", va="bottom", ha="right")


def save(fig, stem, outdir=None):
    """Write PDF + PNG. Defaults to <repo>/results/figures; override with FIG_OUT."""
    import os
    if outdir is None:
        outdir = os.environ.get(
            "FIG_OUT",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "figures"),
        )
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(f"{outdir}/{stem}.pdf")
    fig.savefig(f"{outdir}/{stem}.png", dpi=600)
    print(f"  saved {stem}.pdf + .png")
