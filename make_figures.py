#!/usr/bin/env python3
"""
make_figures.py — regenerates Figures 3, 4, 5 from one shared style module.

Data sources (all transcribed from the manuscript / supplement, no re-run):
  Figure 3 : supplement eTable 10  (AoU vs MarketScan base model)
  Figure 4 : main text Table 3     (domain-specific vs joint SDoH)
  Figure 5a: supplement eTable 13  (wave-stratified income, domain-specific)
  Figure 5b: supplement eTable 12b (wave-stratified Black-race attenuation)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import numpy as np
from jamia_style import (apply_style, figsize, forest_row, ref_line, log_axis,
                         panel_label, save, sig_color,
                         C_RISK, C_PROT, C_NS, C_DOMAIN, C_JOINT, C_AOU, C_MS,
                         C_CONN, C_BAND, WONG, C_TXT1, C_TXT2, BAND_RIGHT)

apply_style()

# ============================================================ FIGURE 3
# Base model, AoU vs MarketScan (eTable 10). Grouped; MarketScan has no race.
FIG3 = [
    ("Demographics", [
        ("Female sex",            (0.74,0.68,0.80,"*"), (0.50,0.49,0.50,"*")),
        ("Age 45–54",        (1.08,0.96,1.21,""),  (1.46,1.44,1.48,"*")),
        ("Age 55–64",        (1.45,1.30,1.61,"*"), (1.78,1.75,1.81,"*")),
        ("Age ≥65",          (1.61,1.44,1.79,"*"), (1.73,1.51,1.98,"*")),
        ("Black race",            (2.30,2.10,2.52,"*"), None),
    ]),
    ("Vaccination and wave", [
        ("Vaccinated before index",(0.45,0.40,0.51,"*"),(0.48,0.47,0.50,"*")),
        ("Delta wave",            (1.24,1.12,1.38,"*"), (1.47,1.44,1.49,"*")),
        ("Omicron wave",          (1.04,0.96,1.13,""),  (0.47,0.47,0.48,"*")),
    ]),
    ("Comorbidities", [
        ("Renal, severe",         (1.29,1.12,1.48,"*"), (2.45,2.31,2.59,"*")),
        ("Liver, mod/severe",     (1.37,1.12,1.68,"*"), (1.43,1.31,1.56,"*")),
        ("Metastatic tumor",      (1.22,1.03,1.46,"*"), (1.68,1.59,1.77,"*")),
        ("Cerebrovascular",       (1.20,1.08,1.33,"*"), (0.86,0.83,0.89,"*")),
        ("CHF",                   (1.19,1.08,1.32,"*"), (1.36,1.31,1.41,"*")),
        ("Dementia",              (1.11,0.94,1.30,""),  (1.27,1.16,1.39,"*")),
        ("Malignancy",            (1.07,0.97,1.19,""),  (0.94,0.91,0.98,"*")),
        ("Renal, mild/mod",       (1.05,0.94,1.18,""),  (1.29,1.25,1.34,"*")),
        ("DM w/o complications",  (1.02,0.91,1.13,""),  (1.41,1.38,1.44,"*")),
        ("Hemiplegia/paraplegia", (1.02,0.86,1.21,""),  (1.71,1.59,1.83,"*")),
        ("DM w/ complications",   (0.96,0.86,1.06,""),  (1.46,1.42,1.50,"*")),
        ("HIV",                   (0.95,0.67,1.36,""),  (0.86,0.76,0.96,"*")),
        ("Peptic ulcer",          (0.94,0.82,1.08,""),  (0.79,0.73,0.84,"*")),
        ("Rheumatic disease",     (0.91,0.81,1.02,""),  (0.82,0.79,0.85,"*")),
        ("Chronic pulmonary",     (0.85,0.79,0.92,"*"), (0.86,0.84,0.87,"*")),
        ("AIDS",                  (0.76,0.57,1.02,""),  (1.27,1.03,1.58,"*")),
        ("Liver, mild",           (0.76,0.69,0.83,"*"), (0.78,0.76,0.81,"*")),
    ]),
]

def figure3():
    XMIN, XMAX = 0.40, 2.80
    OFF = 0.19
    rows, y = [], 0.0
    for gname, items in FIG3:
        rows.append(("h", gname, y)); y -= 1.0
        for it in items:
            rows.append(("r", it, y)); y -= 1.0
    fig, ax = plt.subplots(figsize=figsize("double", height=6.9))
    fig.subplots_adjust(left=0.255, right=0.735, top=0.955, bottom=0.085)
    tx = blended_transform_factory(ax.transAxes, ax.transData)

    tog, yy = True, 0.0
    for gname, items in FIG3:
        n = 1 + len(items)
        if tog:
            ax.add_patch(Rectangle((-0.345, yy - (n-1) - 0.5), BAND_RIGHT + 0.345, n,
                         transform=tx, facecolor=C_BAND, edgecolor="none",
                         zorder=0, clip_on=False))
        tog = not tog; yy -= n

    for kind, payload, yv in rows:
        if kind == "h":
            ax.text(-0.34, yv, payload, transform=tx, ha="left", va="center",
                    fontweight="bold", fontsize=7, clip_on=False)
            continue
        label, aou, ms = payload
        ax.text(-0.018, yv, label, transform=tx, ha="right", va="center",
                fontsize=6.5, clip_on=False)
        ya, ym = yv + OFF, yv - OFF
        forest_row(ax, ya, *aou[:3], C_AOU, XMIN, XMAX, marker="o", size=13,
                   filled=(aou[3] != ""))
        ax.text(1.02, ya, f"{aou[0]:.2f} ({aou[1]:.2f}–{aou[2]:.2f}){aou[3]}",
                transform=tx, ha="left", va="center", fontsize=5.6, color=C_TXT1, clip_on=False)
        if ms is None:
            ax.text(1.02, ym, "not available in claims", transform=tx, ha="left",
                    va="center", fontsize=5.6, color=C_TXT2, style="italic", clip_on=False)
        else:
            forest_row(ax, ym, *ms[:3], C_MS, XMIN, XMAX, marker="s", size=12,
                       filled=(ms[3] != ""))
            ax.text(1.02, ym, f"{ms[0]:.2f} ({ms[1]:.2f}–{ms[2]:.2f}){ms[3]}",
                    transform=tx, ha="left", va="center", fontsize=5.6, color=C_TXT2, clip_on=False)

    ref_line(ax)
    log_axis(ax, [0.5, 0.75, 1.0, 1.5, 2.0, 2.5], XMIN, XMAX)
    ax.set_ylim(y + 0.4, 1.1)
    ax.text(1.02, 1.008, "AOR (95% CI)", transform=ax.transAxes, ha="left",
            va="bottom", fontsize=6, fontweight="bold", color="#333333")
    h = [Line2D([0],[0], marker="o", color="none", markerfacecolor=C_AOU,
                markeredgecolor=C_AOU, markersize=4.5, label="All of Us (n = 19,920)"),
         Line2D([0],[0], marker="s", color="none", markerfacecolor=C_MS,
                markeredgecolor=C_MS, markersize=4.5, label="MarketScan (n = 693,682)"),
         Line2D([0],[0], marker="o", color="none", markerfacecolor="white",
                markeredgecolor="#666666", markersize=4.5,
                label="Open marker: not statistically significant")]
    ax.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, -0.105),
              ncol=3, fontsize=5.8, handletextpad=0.5, columnspacing=1.4)
    save(fig, "Figure3_base_model_AoU_vs_MarketScan"); plt.close(fig)

# ============================================================ FIGURE 4
FIG4 = [
    ("Income", "ref: $35,000–99,999", [
        ("<$10,000",         (1.46,1.29,1.65,"***"), (1.18,1.02,1.36,"*")),
        ("$10,000–24,999",(1.37,1.21,1.55,"***"),(1.18,1.04,1.35,"*")),
        ("$25,000–34,999",(1.19,1.02,1.38,"*"),  (1.12,0.96,1.31,"")),
        ("$100,000–149,999",(1.20,1.03,1.41,"*"),(1.24,1.06,1.46,"**")),
        ("$150,000–199,999",(1.19,0.96,1.48,""), (1.26,1.01,1.57,"*")),
        ("≥$200,000",   (1.10,0.90,1.34,""),    (1.15,0.93,1.41,"")),
    ]),
    ("Insurance", "ref: Employer", [
        ("Medicare",         (1.06,0.93,1.20,""),    (0.95,0.83,1.09,"")),
        ("Medicaid",         (1.59,1.43,1.77,"***"), (1.33,1.16,1.51,"***")),
        ("Other / none",     (1.31,1.13,1.52,"***"), (1.15,0.98,1.35,"")),
    ]),
    ("Education", "ref: College graduate or higher", [
        ("Below GED",        (1.35,1.18,1.53,"***"), (1.13,0.98,1.30,"")),
        ("GED / some college",(1.11,1.02,1.21,"*"),  (1.02,0.93,1.12,"")),
    ]),
    ("Employment", "ref: Employed", [
        ("Unemployed",       (1.41,1.28,1.56,"***"), (1.23,1.09,1.38,"***")),
        ("Student",          (1.61,1.24,2.09,"***"), (1.52,1.16,1.98,"**")),
        ("Retired / other",  (1.36,1.22,1.51,"***"), (1.26,1.12,1.42,"***")),
    ]),
    ("Housing", "ref: Own home", [
        ("Rent",             (1.28,1.17,1.39,"***"), (1.13,1.03,1.25,"*")),
        ("Other",            (0.99,0.86,1.13,""),    (0.86,0.74,1.00,"*")),
    ]),
    ("Housing stability", "ref: Stable", [
        ("Unstable",         (1.01,0.92,1.11,""),    (0.94,0.85,1.04,"")),
    ]),
    ("Disability", "ref: None", [
        ("Any disability",   (0.94,0.83,1.07,""),    (0.86,0.76,0.98,"*")),
    ]),
]

def figure4():
    XMIN, XMAX = 0.70, 2.25
    OFF = 0.185
    rows, y = [], 0.0
    for d, r, items in FIG4:
        rows.append(("h", (d, r), y)); y -= 1.0
        for it in items:
            rows.append(("r", it, y)); y -= 1.0
    fig, ax = plt.subplots(figsize=figsize("double", height=5.2))
    fig.subplots_adjust(left=0.30, right=0.775, top=0.94, bottom=0.115)
    tx = blended_transform_factory(ax.transAxes, ax.transData)

    tog, yy = True, 0.0
    for d, r, items in FIG4:
        n = 1 + len(items)
        if tog:
            ax.add_patch(Rectangle((-0.42, yy - (n-1) - 0.5), BAND_RIGHT + 0.42, n, transform=tx,
                         facecolor=C_BAND, edgecolor="none", zorder=0, clip_on=False))
        tog = not tog; yy -= n

    for kind, payload, yv in rows:
        if kind == "h":
            d, r = payload
            ax.text(-0.415, yv, d, transform=tx, ha="left", va="center",
                    fontweight="bold", fontsize=7, clip_on=False)
            # long domain names need the reference label pushed further right
            rx = -0.150 if len(d) <= 12 else -0.108
            ax.text(rx, yv, f"({r})", transform=tx, ha="left", va="center",
                    fontsize=5.9, style="italic", color="#555555", clip_on=False)
            continue
        label, dom, jnt = payload
        yd, yj = yv + OFF, yv - OFF
        xa = min(max(dom[0], XMIN*1.02), XMAX*0.98)
        xb = min(max(jnt[0], XMIN*1.02), XMAX*0.98)
        ax.plot([xa, xb], [yd, yj], color=C_CONN, lw=2.0, alpha=0.95,
                solid_capstyle="round", zorder=2)
        forest_row(ax, yd, *dom[:3], C_DOMAIN, XMIN, XMAX, marker="o", size=15,
                   filled=(dom[3] != ""))
        forest_row(ax, yj, *jnt[:3], C_JOINT, XMIN, XMAX, marker="s", size=14,
                   filled=(jnt[3] != ""))
        ax.text(-0.018, yv, label, transform=tx, ha="right", va="center",
                fontsize=6.5, clip_on=False)
        ax.text(1.025, yd, f"{dom[0]:.2f} ({dom[1]:.2f}–{dom[2]:.2f}){dom[3]}",
                transform=tx, ha="left", va="center", fontsize=5.7, color=C_TXT1, clip_on=False)
        ax.text(1.025, yj, f"{jnt[0]:.2f} ({jnt[1]:.2f}–{jnt[2]:.2f}){jnt[3]}",
                transform=tx, ha="left", va="center", fontsize=5.7, color=C_TXT2, clip_on=False)

    ref_line(ax)
    log_axis(ax, [0.8, 1.0, 1.25, 1.5, 2.0], XMIN, XMAX,
             label="Adjusted odds ratio (95% CI), log scale")
    ax.set_ylim(y + 0.4, 1.1)
    ax.text(1.025, 1.012, "AOR (95% CI)", transform=ax.transAxes, ha="left",
            va="bottom", fontsize=6, fontweight="bold", color="#333333")
    h = [Line2D([0],[0], marker="o", color="none", markerfacecolor=C_DOMAIN,
                markeredgecolor=C_DOMAIN, markersize=4.5,
                label="Domain-specific (base + one domain)"),
         Line2D([0],[0], marker="s", color="none", markerfacecolor=C_JOINT,
                markeredgecolor=C_JOINT, markersize=4.5,
                label="Joint (base + all six domains)"),
         Line2D([0],[0], marker="o", color="none", markerfacecolor="white",
                markeredgecolor="#666666", markersize=4.5,
                label="Open marker: not statistically significant"),
         Line2D([0],[0], color=C_CONN, lw=2.0,
                label="Grey bar: change under mutual adjustment")]
    ax.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, -0.145),
              ncol=2, fontsize=5.8, handletextpad=0.5, columnspacing=1.6)
    save(fig, "Figure4_domain_vs_joint"); plt.close(fig)

# ============================================================ FIGURE 5
INCOME_WAVE = {  # eTable 13, three lower-income strata
    "<$10,000":          [("Pre-Delta",1.49,1.21,1.82,"*"),("Delta",2.11,1.10,4.03,"*"),("Omicron",1.64,1.23,2.18,"*")],
    "$10,000–24,999":[("Pre-Delta",1.23,1.01,1.51,"*"),("Delta",1.98,0.99,3.97,""),("Omicron",1.46,1.10,1.94,"*")],
    "$25,000–34,999":[("Pre-Delta",0.97,0.76,1.25,""), ("Delta",1.52,0.76,3.05,""),("Omicron",1.21,0.86,1.69,"")],
}
RACE_WAVE = [  # eTable 12b
    ("Pre-Delta", 2087, 3.00,2.56,3.51, 2.64,2.23,3.13, 11.5),
    ("Delta",      644, 2.98,1.79,4.96, 2.17,1.21,3.89, 29.1),
    ("Omicron",   1333, 1.65,1.34,2.03, 1.42,1.12,1.79, 30.1),
]

def figure5():
    # Panels are stacked, not side by side: panel a carries nine rows plus a
    # full "AOR (95% CI)" column, which cannot fit in half a double-column
    # width without colliding with panel b's axis label.
    fig = plt.figure(figsize=figsize("double", height=6.15))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.80], hspace=0.40,
                          left=0.235, right=0.800, top=0.955, bottom=0.070)

    # ---- (a) wave-stratified income, grouped forest
    axa = fig.add_subplot(gs[0, 0])
    XMIN, XMAX = 0.60, 4.60
    rows, y = [], 0.0
    for strat, waves in INCOME_WAVE.items():
        rows.append(("h", strat, y)); y -= 1.0
        for w in waves:
            rows.append(("r", w, y)); y -= 1.0
    txa = blended_transform_factory(axa.transAxes, axa.transData)
    tog, yy = True, 0.0
    for strat, waves in INCOME_WAVE.items():
        n = 1 + len(waves)
        if tog:
            axa.add_patch(Rectangle((-0.30, yy-(n-1)-0.5), BAND_RIGHT + 0.30, n, transform=txa,
                          facecolor=C_BAND, edgecolor="none", zorder=0, clip_on=False))
        tog = not tog; yy -= n
    # Colour vocabulary is the paper-wide one (vermillion = significantly
    # elevated, grey = not significant); wave is encoded by row position, not hue.
    for kind, payload, yv in rows:
        if kind == "h":
            axa.text(-0.295, yv, payload, transform=txa, ha="left", va="center",
                     fontweight="bold", fontsize=6.5, clip_on=False)
            continue
        wname, aor, lo, hi, p = payload
        col = (C_RISK if aor > 1 else C_PROT) if p != "" else C_NS
        forest_row(axa, yv, aor, lo, hi, col, XMIN, XMAX, marker="o", size=15,
                   filled=(p != ""))
        axa.text(-0.02, yv, wname, transform=txa, ha="right", va="center",
                 fontsize=6.2, clip_on=False)
        star = "*" if p != "" else ""
        axa.text(1.02, yv, f"{aor:.2f} ({lo:.2f}\u2013{hi:.2f}){star}",
                 transform=txa, ha="left", va="center", fontsize=5.7,
                 color=(C_TXT1 if p != "" else C_TXT2), clip_on=False)
    axa.text(1.025, 1.03, "AOR (95% CI)", transform=axa.transAxes, ha="left",
             va="bottom", fontsize=6, fontweight="bold", color="#333333")
    ref_line(axa)
    log_axis(axa, [0.75, 1.0, 1.5, 2.0, 3.0, 4.0], XMIN, XMAX,
             label="Adjusted odds ratio (95% CI), log scale")
    axa.set_ylim(y + 0.4, 0.9)
    panel_label(axa, "a", x=-0.30, y=1.02)

    # ---- (b) race attenuation, before vs after SDoH adjustment
    axb = fig.add_subplot(gs[1, 0])
    xs = np.arange(len(RACE_WAVE))
    for i, (w, n, b, blo, bhi, j, jlo, jhi, att) in enumerate(RACE_WAVE):
        axb.plot([i, i], [j, b], color=C_CONN, lw=3.0, solid_capstyle="round", zorder=2)
        axb.plot([i-0.055, i+0.055], [b, b], color=C_RISK, lw=0.8, zorder=4)
        axb.plot([i, i], [blo, bhi], color=C_RISK, lw=0.8, alpha=0.85, zorder=3)
        axb.plot([i, i], [jlo, jhi], color=C_JOINT, lw=0.8, alpha=0.85, zorder=3)
        axb.scatter([i], [b], marker="o", s=17, facecolor=C_RISK, edgecolor=C_RISK,
                    linewidths=0.8, zorder=6)
        axb.scatter([i], [j], marker="s", s=16, facecolor=C_JOINT, edgecolor=C_JOINT,
                    linewidths=0.8, zorder=6)
        axb.annotate(f"−{att:.1f}%", xy=(i, np.sqrt(b*j)), xytext=(9, 0),
                     textcoords="offset points", fontsize=5.9, color="#444444",
                     va="center", ha="left")
    axb.axhline(1.0, color="#000000", lw=0.7, zorder=1)
    axb.set_yscale("log")
    axb.set_ylim(0.95, 6.2)   # top headroom leaves the upper-left corner free for the legend
    axb.set_yticks([1.0, 1.5, 2.0, 3.0, 4.0, 5.0])
    axb.set_yticklabels(["1.0", "1.5", "2.0", "3.0", "4.0", "5.0"])
    axb.minorticks_off()
    axb.set_xlim(-0.45, len(RACE_WAVE) - 0.35)
    axb.set_xticks(xs)
    axb.set_xticklabels([f"{w}\n(n = {n:,})" for w, n, *_ in RACE_WAVE], fontsize=6.2)
    axb.set_ylabel("Black-race adjusted odds ratio (95% CI)")
    for s in ("top", "right"):
        axb.spines[s].set_visible(False)
    hb = [Line2D([0],[0], marker="o", color="none", markerfacecolor=C_RISK,
                 markeredgecolor=C_RISK, markersize=4.5, label="Base model"),
          Line2D([0],[0], marker="s", color="none", markerfacecolor=C_JOINT,
                 markeredgecolor=C_JOINT, markersize=4.5,
                 label="After six-domain SDoH adjustment")]
    axb.legend(handles=hb, loc="upper left", fontsize=5.8, handletextpad=0.5,
               labelspacing=0.35, borderaxespad=0.3)
    panel_label(axb, "b", x=-0.075, y=1.02)
    save(fig, "Figure5_wave_stratified"); plt.close(fig)


if __name__ == "__main__":
    print("Regenerating figures with shared jamia_style:")
    figure3(); figure4(); figure5()
    print("done.")
