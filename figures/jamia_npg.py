"""JAMIA + NPG house style. One semantic colour grammar for all five figures."""
import matplotlib as mpl, matplotlib.pyplot as plt

# ---- the grammar (NPG hues, ggsci values; measured CVD-safe, min dE 25.9 / 15.0 deutan)
NAVY  = "#3C5488"   # All of Us | joint model | after SDoH adjustment  -> "adjusted"
CORAL = "#E64B35"   # domain-specific model | base model               -> "unadjusted"
TEAL  = "#00A087"   # MarketScan (external cohort)
GREY  = "#8491B4"   # not statistically significant
INK   = "#1A1A1A"
RULE  = "#B8BCC8"
BAND  = "#F2F3F6"   # alternating group band
WAVE  = ["#4DBBD5", "#4A7BA7", "#3C5488"]   # ordered: pre-Delta -> Delta -> Omicron

# JAMIA column widths (inches)
SINGLE, DOUBLE = 3.25, 6.875

def apply_style():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
        "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "axes.edgecolor": INK, "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "legend.frameon": False,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "figure.constrained_layout.use": False,
    })

def panel_label(ax, s, x=-0.02, y=1.02):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=8, fontweight="bold",
            va="bottom", ha="right", color=INK)

def save(fig, stem, outdir=".", tight=False):
    """Default keeps the canvas at its declared column width so every figure
    in the paper is reduced by the same factor at production."""
    import os
    base = os.path.join(outdir, stem)
    kw = dict(bbox_inches="tight", pad_inches=0.03) if tight else {}
    fig.savefig(base + ".pdf", format="pdf", **kw)
    fig.savefig(base + ".png", dpi=600, **kw)
    fig.savefig(base + ".tif", dpi=600, pil_kwargs={"compression": "tiff_lzw"}, **kw)
    print(f"  saved {stem}.pdf/.png/.tif")

def forest_row(ax, y, aor, lo, hi, colour, sig, marker="o", size=16, lw=0.9):
    """One horizontal CI with a point estimate. Open marker when not significant."""
    ax.plot([lo, hi], [y, y], color=colour, lw=lw, solid_capstyle="butt", zorder=2)
    for e in (lo, hi):
        ax.plot([e, e], [y - .13, y + .13], color=colour, lw=lw, zorder=2)
    ax.scatter([aor], [y], s=size, marker=marker, zorder=3,
               facecolor=colour if sig else "white",
               edgecolor=colour, linewidths=0.9)

def log_x(ax, ticks):
    ax.set_xscale("log")
    ax.set_xticks(ticks)
    ax.set_xticklabels([("%g" % t) for t in ticks])
    ax.minorticks_off()
