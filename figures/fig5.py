import sys; sys.path.insert(0,'/home/claude/figs')
import matplotlib.pyplot as plt, numpy as np
from matplotlib.lines import Line2D
import jamia_npg as J
J.apply_style()

# (a) eTable 13 -- three lowest income strata by wave
INC = [("<$10,000",       [("Pre-Delta",1.49,1.21,1.82,1),("Delta",2.11,1.10,4.03,1),("Omicron",1.64,1.23,2.18,1)]),
       ("$10,000–24,999", [("Pre-Delta",1.23,1.01,1.51,1),("Delta",1.98,0.99,3.97,0),("Omicron",1.46,1.10,1.94,1)]),
       ("$25,000–34,999", [("Pre-Delta",0.97,0.76,1.25,0),("Delta",1.52,0.76,3.05,0),("Omicron",1.21,0.86,1.69,0)])]
# (b) eTable 12b
RACE = [("Pre-Delta",2087,3.00,2.56,3.51,2.64,2.23,3.13,11.5),
        ("Delta",     644,2.98,1.79,4.96,2.17,1.21,3.89,29.1),
        ("Omicron",  1333,1.65,1.34,2.03,1.42,1.12,1.79,30.1)]

fig=plt.figure(figsize=(J.DOUBLE,5.5))
axa=fig.add_axes([0.245,0.600,0.445,0.350])
axb=fig.add_axes([0.245,0.093,0.445,0.350])

# ---------- panel a ----------
rows=[]
for lab,ws in INC:
    rows.append(("HDR",lab,None)); rows += [("ROW",w,v) for w,*v in [(w,a,lo,hi,s) for w,a,lo,hi,s in ws]]
n=len(rows); y=n
for kind,lab,v in rows:
    y-=1
    if kind=="HDR":
        axa.text(-0.012,y,lab,transform=axa.get_yaxis_transform(),ha="right",va="center",
                 fontsize=6.8,fontweight="bold",color=J.INK); continue
    a,lo,hi,sig=v
    c=J.WAVE[["Pre-Delta","Delta","Omicron"].index(lab)]
    axa.text(-0.012,y,lab,transform=axa.get_yaxis_transform(),ha="right",va="center",
             fontsize=6.5,color=J.INK)
    J.forest_row(axa,y,a,lo,hi,c if sig else J.GREY,sig,marker="o",size=15)
    axa.text(1.03,y,f"{a:.2f} ({lo:.2f}–{hi:.2f})",transform=axa.get_yaxis_transform(),
             ha="left",va="center",fontsize=6,color=J.INK if sig else J.GREY)
axa.axvline(1.0,color=J.INK,lw=0.7)
J.log_x(axa,[0.75,1,1.5,2,3,4]); axa.set_xlim(0.68,4.6); axa.set_ylim(-0.6,n-0.4)
axa.set_yticks([]); axa.spines["left"].set_visible(False)
axa.set_xlabel("Adjusted odds ratio (95% CI), log scale")
axa.text(1.03,n-0.35,"AOR (95% CI)",transform=axa.get_yaxis_transform(),ha="left",va="center",
         fontsize=6.5,fontweight="bold")
axa.text(0.0,1.045,"Household income, by pandemic wave (reference $35,000–99,999)",
         transform=axa.transAxes,fontsize=6.8,color=J.GREY)
J.panel_label(axa,"a",x=-0.30,y=1.02)
axa.legend(handles=[Line2D([0],[0],marker="o",color="none",markerfacecolor=J.WAVE[i],
           markeredgecolor=J.WAVE[i],markersize=4.3,label=w) for i,w in
           enumerate(["Pre-Delta","Delta","Omicron"])]+
          [Line2D([0],[0],marker="o",color="none",markerfacecolor="white",
           markeredgecolor=J.GREY,markersize=4.3,label="Open: not significant")],
          loc="upper left",bbox_to_anchor=(0,-0.16),ncol=4,handletextpad=0.4,
          columnspacing=1.2,borderpad=0)

# ---------- panel b ----------
x=np.arange(3)
for i,(w,nc,b,bl,bh,j,jl,jh,att) in enumerate(RACE):
    axb.plot([i,i],[bl,bh],color=J.CORAL,lw=0.9,zorder=2)
    axb.plot([i+0.13,i+0.13],[jl,jh],color=J.NAVY,lw=0.9,zorder=2)
    axb.plot([i,i+0.13],[b,j],color=J.RULE,lw=2.6,solid_capstyle="round",zorder=1)
    axb.scatter([i],[b],s=22,marker="o",color=J.CORAL,zorder=3)
    axb.scatter([i+0.13],[j],s=19,marker="s",color=J.NAVY,zorder=3)
    axb.annotate(f"−{att}%",xy=(i+0.20,(b+j)/2),fontsize=6.5,color=J.INK,va="center",ha="left")
axb.axhline(1.0,color=J.INK,lw=0.7)
axb.set_yscale("log"); axb.set_yticks([1,1.5,2,3,4,5])
axb.set_yticklabels(["1.0","1.5","2.0","3.0","4.0","5.0"]); axb.minorticks_off()
axb.set_xticks(x); axb.set_xticklabels([f"{w}\n(n = {nc:,})" for w,nc,*_ in RACE])
axb.set_xlim(-0.45,2.75); axb.set_ylim(0.95,5.6)
axb.set_ylabel("Black-race adjusted odds ratio (95% CI)")
axb.text(0.0,1.045,"Black-race association before and after six-domain SDoH adjustment",
         transform=axb.transAxes,fontsize=6.8,color=J.GREY)
J.panel_label(axb,"b",x=-0.30,y=1.02)
axb.legend(handles=[Line2D([0],[0],marker="o",color="none",markerfacecolor=J.CORAL,
           markeredgecolor=J.CORAL,markersize=4.3,label="Base model"),
           Line2D([0],[0],marker="s",color="none",markerfacecolor=J.NAVY,
           markeredgecolor=J.NAVY,markersize=4.0,label="After six-domain SDoH adjustment"),
           Line2D([0],[0],color=J.RULE,lw=2.6,label="Coefficient attenuation")],
          loc="upper left",bbox_to_anchor=(0,-0.13),ncol=3,handletextpad=0.4,
          columnspacing=1.4,borderpad=0)
J.save(fig,"Figure5","/home/claude/figs/out")
