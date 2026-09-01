import sys; sys.path.insert(0,'/home/claude/figs')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import jamia_npg as J
J.apply_style()

def box(ax,cx,cy,w,h,lines,accent,fill="white",fs=6.0):
    ax.add_patch(FancyBboxPatch((cx-w/2,cy-h/2),w,h,
        boxstyle="round,pad=0.006,rounding_size=0.010",lw=0.7,
        edgecolor=accent,facecolor=fill,zorder=2))
    step=h/(len(lines)+0.4)
    for i,t in enumerate(lines):
        ax.text(cx,cy+h/2-step*(i+0.7),t,ha="center",va="center",fontsize=fs,zorder=3,
                fontweight="bold" if i==0 else "normal",color=J.INK)

def arw(ax,p,q,c=J.INK):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle="-|>",mutation_scale=5.5,lw=0.7,
                color=c,shrinkA=0,shrinkB=0,zorder=1))

fig=plt.figure(figsize=(J.DOUBLE,2.75))
MX, MW = 0.300, 0.590          # main column centre / width
EX, EW = 0.800, 0.360          # exclusion column centre / width
Y = dict(t1=.945, t2=.845, t3=.745, split=.618, psm=.455, out=.255)

PANELS = [
 (J.NAVY,"#EEF1F7","All of Us (CDR v7)",
  [(Y["t1"],["413,457 All of Us participants"]),
   (Y["t2"],["252,047 with diagnosis and survey data"]),
   (Y["t3"],["25,160 COVID-19 positive"])],
  ("21,096 outpatient","4,064 hospitalized ≤14 d"),
  ["Propensity score matching","enrollment date · diagnosis count · EHR length"],
  ["19,920 matched observations, 4,064 strata",
   "4,064 cases · 15,856 control obs.","from 9,691 unique individuals"],
  [(.895,["161,410 excluded","No diagnosis data or no survey"]),
   (.355,["388 control obs. excluded","Incomplete follow-up near cutoff"])]),
 (J.TEAL,"#E8F5F2","MarketScan Commercial Claims (2020–2023)",
  [(Y["t1"],["4,423,200 COVID-19 positive"])],
  ("4,283,728 outpatient","139,472 hospitalized ≤14 d"),
  ["Propensity score matching","enrollment date · diagnosis count · coverage span"],
  ["693,682 matched observations, 139,468 strata",
   "139,468 cases · 554,214 control obs.","from 465,670 unique individuals"],
  [(.845,["393 excluded","Missing matching variables"]),
   (.355,["4 strata excluded","All controls lost to the trim"])]),
]

for k,(acc,tint,title,tops,split,psm,out,excl) in enumerate(PANELS):
    ax=fig.add_axes([0.005+0.5*k,0.01,0.49,0.90]); ax.set_xlim(0,1); ax.set_ylim(0.175,1.005); ax.axis("off")
    ax.text(0.5,1.045,title,ha="center",va="center",fontsize=7,fontweight="bold",color=acc)
    ax.text(0.0,1.045,"ab"[k],ha="left",va="center",fontsize=8,fontweight="bold",color=J.INK)
    prev=None
    for y,lines in tops:
        box(ax,MX,y,MW,0.062,lines,acc)
        if prev is not None: arw(ax,(MX,prev-0.031),(MX,y+0.031))
        prev=y
    box(ax,MX-0.163,Y["split"],0.315,0.050,[split[0]],acc)
    box(ax,MX+0.163,Y["split"],0.315,0.050,[split[1]],acc)
    arw(ax,(MX,prev-0.031),(MX-0.163,Y["split"]+0.026))
    arw(ax,(MX,prev-0.031),(MX+0.163,Y["split"]+0.026))
    box(ax,MX,Y["psm"],MW,0.098,psm,acc,tint)
    arw(ax,(MX-0.163,Y["split"]-0.026),(MX-0.09,Y["psm"]+0.049))
    arw(ax,(MX+0.163,Y["split"]-0.026),(MX+0.09,Y["psm"]+0.049))
    box(ax,MX,Y["out"],MW,0.115,out,acc,tint)
    arw(ax,(MX,Y["psm"]-0.049),(MX,Y["out"]+0.058))
    for ey,lines in excl:
        box(ax,EX,ey,EW,0.070,lines,J.GREY,"#F6F6F9",fs=5.6)
        ax.plot([MX,EX-EW/2-0.03],[ey,ey],color=J.GREY,lw=0.6,zorder=1)
        arw(ax,(EX-EW/2-0.045,ey),(EX-EW/2-0.004,ey),J.GREY)
J.save(fig,"Figure1","/home/claude/figs/out")
