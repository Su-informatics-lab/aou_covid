import sys; sys.path.insert(0, '/home/claude/figs')
import matplotlib.pyplot as plt, numpy as np
import jamia_npg as J
J.apply_style()

# eTable 10 (results/tables/eTable_S10_crosssite.csv) -- all 19 Charlson conditions
D = [("Demographics", [
        ("Female sex",  (0.74,0.68,0.80,1), (0.50,0.49,0.50,1)),
        ("Age 45–54",   (1.08,0.96,1.21,0), (1.46,1.44,1.48,1)),
        ("Age 55–64",   (1.45,1.30,1.61,1), (1.78,1.75,1.81,1)),
        ("Age ≥65",     (1.61,1.44,1.79,1), (1.73,1.51,1.98,1)),
        ("Asian race",  (1.33,1.00,1.78,0), None),
        ("Other race",  (1.41,1.17,1.70,1), None),
        ("Hispanic",    (0.97,0.81,1.17,0), None),
        ("Black race",  (2.30,2.10,2.52,1), None)]),
     ("Vaccination and pandemic wave", [
        ("Vaccinated before index", (0.45,0.40,0.51,1), (0.48,0.47,0.50,1)),
        ("Delta wave",   (1.24,1.12,1.38,1), (1.47,1.44,1.49,1)),
        ("Omicron wave", (1.04,0.96,1.13,0), (0.47,0.47,0.48,1))]),
     ("Charlson comorbidities", [
        ("Renal, severe",        (1.29,1.12,1.48,1), (2.45,2.31,2.59,1)),
        ("Liver, mod/severe",    (1.37,1.12,1.68,1), (1.43,1.31,1.56,1)),
        ("Metastatic tumour",    (1.22,1.03,1.46,1), (1.68,1.59,1.77,1)),
        ("Cerebrovascular",      (1.20,1.08,1.33,1), (0.86,0.83,0.89,1)),
        ("Congestive heart failure",(1.19,1.08,1.32,1),(1.36,1.31,1.41,1)),
        ("Dementia",             (1.11,0.94,1.30,0), (1.27,1.16,1.39,1)),
        ("Malignancy",           (1.07,0.97,1.19,0), (0.94,0.91,0.98,1)),
        ("Renal, mild/moderate", (1.05,0.94,1.18,0), (1.29,1.25,1.34,1)),
        ("Hemiplegia/paraplegia",(1.02,0.86,1.21,0), (1.71,1.59,1.83,1)),
        ("Diabetes, no complications",(1.02,0.91,1.13,0),(1.41,1.38,1.44,1)),
        ("Diabetes, complications",(0.96,0.86,1.06,0),(1.46,1.42,1.50,1)),
        ("HIV",                  (0.95,0.67,1.36,0), (0.86,0.76,0.96,1)),
        ("Peptic ulcer",         (0.94,0.82,1.08,0), (0.79,0.73,0.84,1)),
        ("Myocardial infarction",(0.93,0.83,1.05,0), (0.94,0.89,0.99,1)),
        ("Peripheral vascular",  (0.92,0.83,1.02,0), (0.86,0.83,0.89,1)),
        ("Rheumatic disease",    (0.91,0.81,1.02,0), (0.82,0.79,0.85,1)),
        ("Chronic pulmonary",    (0.85,0.79,0.92,1), (0.86,0.84,0.87,1)),
        ("AIDS",                 (0.76,0.57,1.02,0), (1.27,1.03,1.58,1)),
        ("Liver, mild",          (0.76,0.69,0.83,1), (0.78,0.76,0.81,1))])]

rows=[]
for g,(items) in D:
    rows.append(("HDR", g, None, None))
    for lab,a,m in items: rows.append(("ROW", lab, a, m))
n=len(rows)
fig = plt.figure(figsize=(J.DOUBLE, 0.185*n + 0.75))
ax  = fig.add_axes([0.255, 0.058, 0.435, 0.918])
XMIN, XMAX = 0.40, 2.9

y=n
for kind,lab,a,m in rows:
    y-=1
    if kind=="HDR":
        ax.text(-0.012, y, lab, transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=7, fontweight="bold", color=J.INK)
        continue
    ax.axhspan(y-0.5, y+0.5, color=J.BAND, lw=0, zorder=0)
    ax.text(-0.012, y, lab, transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=6.5, color=J.INK)
    if m is not None:
        J.forest_row(ax, y-0.19, m[0], m[1], m[2], J.TEAL if m[3] else J.GREY, m[3], marker="s", size=11)
    J.forest_row(ax, y+0.19, a[0], a[1], a[2], J.NAVY if a[3] else J.GREY, a[3], marker="o", size=13)
    # right-hand numeric column
    ax.text(1.03, y+0.19, f"{a[0]:.2f} ({a[1]:.2f}–{a[2]:.2f})", transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=6, color=J.INK if a[3] else J.GREY)
    txt = f"{m[0]:.2f} ({m[1]:.2f}–{m[2]:.2f})" if m is not None else "not available in claims"
    ax.text(1.03, y-0.19, txt, transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=6, style="normal" if m is not None else "italic",
            color=(J.INK if (m and m[3]) else J.GREY))

ax.axvline(1.0, color=J.INK, lw=0.7, zorder=1)
J.log_x(ax, [0.5, 0.75, 1, 1.5, 2, 2.5])
ax.set_xlim(XMIN, XMAX); ax.set_ylim(-0.6, n-0.4)
ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_xlabel("Adjusted odds ratio (95% CI), log scale")
ax.text(1.03, n-0.35, "AOR (95% CI)", transform=ax.get_yaxis_transform(),
        ha="left", va="center", fontsize=6.5, fontweight="bold")

from matplotlib.lines import Line2D
leg=[Line2D([0],[0],marker="o",color="none",markerfacecolor=J.NAVY,markeredgecolor=J.NAVY,markersize=4.2,label="All of Us (n = 19,920)"),
     Line2D([0],[0],marker="s",color="none",markerfacecolor=J.TEAL,markeredgecolor=J.TEAL,markersize=4.0,label="MarketScan (n = 693,682)"),
     Line2D([0],[0],marker="o",color="none",markerfacecolor="white",markeredgecolor=J.GREY,markersize=4.2,label="Open marker: not significant (P ≥ 0.05)")]
ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.0,-0.045), ncol=3,
          handletextpad=0.4, columnspacing=1.4, borderpad=0)
J.save(fig, "Figure3", "/home/claude/figs/out")
