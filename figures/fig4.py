import sys; sys.path.insert(0,'/home/claude/figs')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import jamia_npg as J
J.apply_style()

D = [("Income","ref: $35,000–99,999",[
        ("<$10,000",(1.46,1.29,1.65,1),(1.18,1.02,1.36,1)),
        ("$10,000–24,999",(1.37,1.21,1.55,1),(1.18,1.04,1.35,1)),
        ("$25,000–34,999",(1.19,1.02,1.38,1),(1.12,0.96,1.31,0)),
        ("$100,000–149,999",(1.20,1.03,1.41,1),(1.24,1.06,1.46,1)),
        ("$150,000–199,999",(1.19,0.96,1.48,0),(1.26,1.01,1.57,1)),
        ("≥$200,000",(1.10,0.90,1.34,0),(1.15,0.93,1.41,0))]),
     ("Insurance","ref: Employer",[
        ("Medicare",(1.06,0.93,1.20,0),(0.95,0.83,1.09,0)),
        ("Medicaid",(1.59,1.43,1.77,1),(1.33,1.16,1.51,1)),
        ("Other or none",(1.31,1.13,1.52,1),(1.15,0.98,1.35,0))]),
     ("Education","ref: College graduate+",[
        ("Below GED",(1.35,1.18,1.53,1),(1.13,0.98,1.30,0)),
        ("GED or some college",(1.11,1.02,1.21,1),(1.02,0.93,1.12,0))]),
     ("Employment","ref: Employed",[
        ("Unemployed",(1.41,1.28,1.56,1),(1.23,1.09,1.38,1)),
        ("Student",(1.61,1.24,2.09,1),(1.52,1.16,1.98,1)),
        ("Retired or other",(1.36,1.22,1.51,1),(1.26,1.12,1.42,1))]),
     ("Housing tenure","ref: Own home",[
        ("Rent",(1.28,1.17,1.39,1),(1.13,1.03,1.25,1)),
        ("Other",(0.99,0.86,1.13,0),(0.86,0.74,1.00,1))]),
     ("Housing stability","ref: Stable",[
        ("Unstable",(1.01,0.92,1.11,0),(0.94,0.85,1.04,0))]),
     ("Disability","ref: No disability",[
        ("Any disability",(0.94,0.83,1.07,0),(0.86,0.76,0.98,1))])]

rows=[]
for g,ref,items in D:
    rows.append(("HDR",g,ref,None))
    for lab,d,j in items: rows.append(("ROW",lab,d,j))
n=len(rows)
fig=plt.figure(figsize=(J.DOUBLE, 0.215*n+0.72))
ax=fig.add_axes([0.255,0.068,0.435,0.905])

y=n
for kind,lab,d,j in rows:
    y-=1
    if kind=="HDR":
        ax.text(-0.012,y,lab,transform=ax.get_yaxis_transform(),ha="right",va="center",
                fontsize=7,fontweight="bold",color=J.INK)
        ax.text(1.03,y,d,transform=ax.get_yaxis_transform(),ha="left",va="center",
                fontsize=6,style="italic",color=J.GREY)
        continue
    ax.axhspan(y-0.5,y+0.5,color=J.BAND,lw=0,zorder=0)
    ax.text(-0.012,y,lab,transform=ax.get_yaxis_transform(),ha="right",va="center",
            fontsize=6.5,color=J.INK)
    # the grey connector is the change under mutual adjustment
    ax.plot([d[0],j[0]],[y,y],color=J.RULE,lw=2.6,solid_capstyle="round",zorder=1)
    J.forest_row(ax,y,d[0],d[1],d[2],J.CORAL if d[3] else J.GREY,d[3],marker="o",size=15)
    J.forest_row(ax,y,j[0],j[1],j[2],J.NAVY  if j[3] else J.GREY,j[3],marker="s",size=13)
    ax.text(1.03,y+0.20,f"{d[0]:.2f} ({d[1]:.2f}–{d[2]:.2f})",transform=ax.get_yaxis_transform(),
            ha="left",va="center",fontsize=6,color=J.CORAL if d[3] else J.GREY)
    ax.text(1.03,y-0.20,f"{j[0]:.2f} ({j[1]:.2f}–{j[2]:.2f})",transform=ax.get_yaxis_transform(),
            ha="left",va="center",fontsize=6,color=J.NAVY if j[3] else J.GREY)

ax.axvline(1.0,color=J.INK,lw=0.7,zorder=2)
J.log_x(ax,[0.8,1,1.25,1.5,2])
ax.set_xlim(0.72,2.25); ax.set_ylim(-0.6,n-0.4)
ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_xlabel("Adjusted odds ratio (95% CI), log scale")
ax.text(1.03,n-0.35,"AOR (95% CI)",transform=ax.get_yaxis_transform(),
        ha="left",va="center",fontsize=6.5,fontweight="bold")
leg=[Line2D([0],[0],marker="o",color="none",markerfacecolor=J.CORAL,markeredgecolor=J.CORAL,markersize=4.3,label="Domain-specific (base + one domain)"),
     Line2D([0],[0],marker="s",color="none",markerfacecolor=J.NAVY,markeredgecolor=J.NAVY,markersize=4.0,label="Joint (base + all six domains)"),
     Line2D([0],[0],color=J.RULE,lw=2.6,label="Change under mutual adjustment"),
     Line2D([0],[0],marker="o",color="none",markerfacecolor="white",markeredgecolor=J.GREY,markersize=4.3,label="Open marker: not significant")]
ax.legend(handles=leg,loc="upper left",bbox_to_anchor=(0.0,-0.05),ncol=2,
          handletextpad=0.4,columnspacing=1.6,borderpad=0)
J.save(fig,"Figure4","/home/claude/figs/out")
