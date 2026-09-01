#!/usr/bin/env python3
"""
Figure 4 (reconceived): Domain-specific vs joint SDoH associations with
COVID-19 hospitalization. Paired dumbbell / connected-dot forest plot.

Data source: Table 3 of JAMIA_manuscript_v17. Point estimates and 95% CIs
are transcribed directly from the manuscript (no model re-run required).

Encoding:
  - Vermillion circle  = domain-specific model (base + that one SDoH domain)
  - Blue square        = joint model (base + all six SDoH domains)
  - Filled marker      = statistically significant (P < 0.05)
  - Open marker        = not statistically significant
  - Grey connector bar = the change in weight from domain-specific to joint
                         (i.e., the socioeconomic signal shared with other domains)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import numpy as np

# ---------------------------------------------------------------- style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 11,
    "axes.linewidth": 1.0,
    "pdf.fonttype": 42, "ps.fonttype": 42,   # editable text in vector output
})
VERM = "#D55E00"   # Okabe-Ito vermillion  -> domain-specific
BLUE = "#0072B2"   # Okabe-Ito blue        -> joint
CONN = "#BFBFBF"   # connector bar
BAND = "#EFEFEF"   # alternating domain band
GRID = "#000000"

# ---------------------------------------------------------------- data (Table 3)
# level, dom(aor,lo,hi,pstr), joint(aor,lo,hi,pstr)
DOMAINS = [
    ("Income", "ref: $35–100K", [
        ("<$10K",          (1.46,1.29,1.65,"***"), (1.18,1.02,1.36,"*")),
        ("$10–25K",   (1.37,1.21,1.55,"***"), (1.18,1.04,1.35,"*")),
        ("$25–35K",   (1.19,1.02,1.38,"*"),   (1.12,0.96,1.31,"")),
        ("$100–150K", (1.20,1.03,1.41,"*"),   (1.24,1.06,1.46,"**")),
        ("$150–200K", (1.19,0.96,1.48,""),    (1.26,1.01,1.57,"*")),
        (">$200K",         (1.10,0.90,1.34,""),    (1.15,0.93,1.41,"")),
    ]),
    ("Insurance", "ref: Employer", [
        ("Medicare",       (1.06,0.93,1.20,""),    (0.95,0.83,1.09,"")),
        ("Medicaid",       (1.59,1.43,1.77,"***"), (1.33,1.16,1.51,"***")),
        ("Other/None",     (1.31,1.13,1.52,"***"), (1.15,0.98,1.35,"")),
    ]),
    ("Education", "ref: College+", [
        ("Never attended", (3.35,1.66,6.78,"***"), (2.85,1.40,5.82,"**")),
        ("Below GED",      (1.35,1.18,1.53,"***"), (1.13,0.98,1.30,"")),
        ("GED/some college",(1.11,1.02,1.21,"*"),  (1.02,0.93,1.12,"")),
    ]),
    ("Employment", "ref: Employed", [
        ("Unemployed",     (1.41,1.28,1.56,"***"), (1.23,1.09,1.38,"***")),
        ("Student",        (1.61,1.24,2.09,"***"), (1.52,1.16,1.98,"**")),
        ("Retired/other",  (1.36,1.22,1.51,"***"), (1.26,1.12,1.42,"***")),
    ]),
    ("Housing", "ref: Own", [
        ("Rent",           (1.28,1.17,1.39,"***"), (1.13,1.03,1.25,"*")),
        ("Other",          (0.99,0.86,1.13,""),    (0.86,0.74,1.00,"*")),
    ]),
    ("Housing stability", "ref: Stable", [
        ("Unstable",       (1.01,0.92,1.11,""),    (0.94,0.85,1.04,"")),
    ]),
    ("Disability", "ref: None", [
        ("Any disability", (0.94,0.83,1.07,""),    (0.86,0.76,0.98,"*")),
    ]),
]

# ---------------------------------------------------------------- layout
XMIN, XMAX = 0.70, 2.40
OFF = 0.17          # vertical offset of the two sub-rows within a level
row_h = 1.0

# assign y positions top->down
rows = []           # (kind, payload, y)
y = 0.0
for dname, dref, levels in DOMAINS:
    rows.append(("header", (dname, dref), y)); y -= row_h
    for lv in levels:
        rows.append(("level", lv, y)); y -= row_h
y_bottom = y

fig, ax = plt.subplots(figsize=(12.4, 9.6))
fig.subplots_adjust(left=0.30, right=0.775, top=0.93, bottom=0.075)
tx = blended_transform_factory(ax.transAxes, ax.transData)   # x=axes frac, y=data

# alternating domain background bands (span labels + plot + annotations)
band_toggle = True
yy = 0.0
for dname, dref, levels in DOMAINS:
    n = 1 + len(levels)
    top = yy + 0.5
    bot = yy - (n - 1) * row_h - 0.5
    if band_toggle:
        ax.add_patch(Rectangle((-0.46, bot), 2.03, top - bot, transform=tx,
                               facecolor=BAND, edgecolor="none", zorder=0, clip_on=False))
    band_toggle = not band_toggle
    yy -= n * row_h

def marker_for(ax, x, ylev, aor, lo, hi, pstr, color, shape):
    """Draw one estimate (CI + marker), clamping off-scale to an arrow."""
    sig = pstr != ""
    face = color if sig else "white"
    # CI whisker (clamp to axis; arrow if beyond)
    clo, chi = max(lo, XMIN*1.001), min(hi, XMAX*0.999)
    ax.plot([clo, chi], [ylev, ylev], color=color, lw=1.4, alpha=0.75,
            solid_capstyle="butt", zorder=3)
    for cx, beyond in [(clo, lo < XMIN), (chi, hi > XMAX)]:
        if beyond:
            ax.plot(cx, ylev, marker=(3, 0, 90 if cx==chi else -90), ms=7,
                    color=color, alpha=0.75, zorder=3)
        else:
            ax.plot([cx, cx], [ylev-0.12, ylev+0.12], color=color, lw=1.2,
                    alpha=0.75, zorder=3)
    # point marker (clamp)
    px = min(max(aor, XMIN*1.02), XMAX*0.985)
    ax.scatter([px], [ylev], marker=shape, s=64, facecolor=face,
               edgecolor=color, linewidths=1.6, zorder=5,
               clip_on=False)
    if aor > XMAX:   # off-scale point: little arrow past the marker
        ax.annotate("", xy=(XMAX*0.999, ylev), xytext=(XMAX*0.955, ylev),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4), zorder=6)

for kind, payload, yv in rows:
    if kind == "header":
        dname, dref = payload
        ax.text(-0.455, yv, dname, transform=tx, ha="left", va="center",
                fontweight="bold", fontsize=11.5, clip_on=False)
        ax.text(-0.455 + 0.001, yv, "", transform=tx)
        ax.text(-0.20, yv, f"({dref})", transform=tx, ha="left", va="center",
                fontsize=10, style="italic", color="#444444", clip_on=False)
        continue
    label, dom, jnt = payload
    yd, yj = yv + OFF, yv - OFF
    # connector bar between the two point estimates
    ax.plot([min(max(dom[0],XMIN*1.02),XMAX*0.985),
             min(max(jnt[0],XMIN*1.02),XMAX*0.985)], [yd, yj],
            color=CONN, lw=3.2, alpha=0.9, solid_capstyle="round", zorder=2)
    # estimates
    marker_for(ax, None, yd, dom[0], dom[1], dom[2], dom[3], VERM, "o")
    marker_for(ax, None, yj, jnt[0], jnt[1], jnt[2], jnt[3], BLUE, "s")
    # level label (right-aligned, just left of plot)
    ax.text(-0.02, yv, label, transform=tx, ha="right", va="center",
            fontsize=10.5, clip_on=False)
    # right annotations, colour-matched to sub-row
    def ann(txt):
        return txt
    ax.text(1.035, yd, f"{dom[0]:.2f} ({dom[1]:.2f}–{dom[2]:.2f}){dom[3]}",
            transform=tx, ha="left", va="center", fontsize=9.2, color=VERM, clip_on=False)
    ax.text(1.035, yj, f"{jnt[0]:.2f} ({jnt[1]:.2f}–{jnt[2]:.2f}){jnt[3]}",
            transform=tx, ha="left", va="center", fontsize=9.2, color=BLUE, clip_on=False)

# reference line at AOR = 1
ax.axvline(1.0, color=GRID, lw=1.2, zorder=1)

# x axis (log)
ax.set_xscale("log")
ax.set_xlim(XMIN, XMAX)
ticks = [0.8, 1.0, 1.25, 1.5, 2.0]
ax.set_xticks(ticks)
ax.set_xticklabels([f"{t:g}" for t in ticks])
ax.minorticks_off()
ax.set_ylim(y_bottom + 0.4, 0.9)
ax.set_yticks([])
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_bounds(XMIN, XMAX)
ax.set_xlabel("Adjusted odds ratio (95% CI), log scale", fontsize=11.5)

# column headers for the annotation block
ax.text(1.035, 1.05, "Domain-specific", transform=ax.transAxes, ha="left",
        va="bottom", fontsize=9.6, fontweight="bold", color=VERM)
ax.text(1.035, 1.01, "Joint (6 domains)", transform=ax.transAxes, ha="left",
        va="bottom", fontsize=9.6, fontweight="bold", color=BLUE)

# legend
handles = [
    Line2D([0],[0], marker="o", color="none", markerfacecolor=VERM,
           markeredgecolor=VERM, markersize=9, label="Domain-specific model (base + one domain)"),
    Line2D([0],[0], marker="s", color="none", markerfacecolor=BLUE,
           markeredgecolor=BLUE, markersize=9, label="Joint model (base + all six domains)"),
    Line2D([0],[0], marker="o", color="none", markerfacecolor="white",
           markeredgecolor="#555555", markersize=9, label="Open marker = not significant (P ≥ 0.05)"),
    Line2D([0],[0], color=CONN, lw=3.2, label="Bar = shift attributable to shared signal"),
]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.135),
          ncol=2, frameon=False, fontsize=9.6, handletextpad=0.6,
          columnspacing=1.8, borderaxespad=0)

out = "results/figures"
fig.savefig(f"{out}/Figure4_domain_vs_joint.png", dpi=300, bbox_inches="tight")
fig.savefig(f"{out}/Figure4_domain_vs_joint.pdf", bbox_inches="tight")
print("saved PNG + PDF")
