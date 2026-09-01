import sys; sys.path.insert(0,'/home/claude/figs')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import jamia_npg as J
J.apply_style()

fig=plt.figure(figsize=(J.DOUBLE,2.85))
ax=fig.add_axes([0.01,0.02,0.98,0.96]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")

def rect(cx,cy,w,h,lines,acc,fill="white",fs=6.2):
    ax.add_patch(FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0.005,rounding_size=0.012",
                 lw=0.75,edgecolor=acc,facecolor=fill,zorder=2))
    st=h/(len(lines)+0.4)
    for i,t in enumerate(lines):
        ax.text(cx,cy+h/2-st*(i+0.7),t,ha="center",va="center",fontsize=fs,zorder=3,
                fontweight="bold" if i==0 else "normal",color=J.INK)

def dia(cx,cy,w,h,text,fs=6.2):
    ax.add_patch(Polygon([[cx,cy+h/2],[cx+w/2,cy],[cx,cy-h/2],[cx-w/2,cy]],closed=True,
                 lw=0.75,edgecolor=J.NAVY,facecolor="#EEF1F7",zorder=2))
    ax.text(cx,cy,text,ha="center",va="center",fontsize=fs,zorder=3,color=J.INK)

def arw(p,q,lab=None,c=J.INK,dx=0,dy=0.028):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle="-|>",mutation_scale=5.5,lw=0.7,color=c,
                 shrinkA=0,shrinkB=0,zorder=1))
    if lab:
        ax.text((p[0]+q[0])/2+dx,(p[1]+q[1])/2+dy,lab,ha="center",va="center",
                fontsize=5.8,color=J.GREY,zorder=3)

rect(0.085,0.72,0.155,0.30,["Data domains","ICD conditions","Visit records","Laboratory results"],J.GREY,"#F6F6F9",fs=5.9)
dia(0.285,0.72,0.155,0.20,"COVID-19\npositive?")
dia(0.520,0.72,0.205,0.20,"Inpatient or\nED-to-inpatient ≤14 d?")
dia(0.520,0.365,0.165,0.20,"Emergency\nvisit ≤14 d?")
dia(0.520,0.095,0.165,0.17,"Recorded stay\n≥1 day?")
rect(0.815,0.72,0.185,0.085,["Case (hospitalized)"],J.CORAL,"#FDF0EE")
rect(0.815,0.095,0.185,0.085,["Case (hospitalized)"],J.CORAL,"#FDF0EE")
rect(0.190,0.365,0.185,0.085,["Control (outpatient)"],J.NAVY,"#EEF1F7")
rect(0.190,0.095,0.185,0.105,["Control","(case in 30-day sensitivity)"],J.NAVY,"#EEF1F7",fs=5.9)
rect(0.285,0.965,0.155,0.062,["Excluded"],J.GREY,"#F6F6F9")

arw((0.163,0.72),(0.207,0.72))
arw((0.285,0.82),(0.285,0.934),"No",dx=0.028,dy=0)
arw((0.363,0.72),(0.417,0.72),"Yes")
arw((0.623,0.72),(0.722,0.72),"Yes")
arw((0.520,0.62),(0.520,0.465),"No",dx=0.026,dy=0)
arw((0.437,0.365),(0.283,0.365),"No")
arw((0.520,0.265),(0.520,0.180),"Yes",dx=0.028,dy=0)
arw((0.603,0.095),(0.722,0.095),"Yes")
arw((0.437,0.095),(0.283,0.095),"No (same-day)")
J.save(fig,"Figure2","/home/claude/figs/out")
