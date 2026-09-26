# -*- coding: utf-8 -*-
"""Render eFigure 1 (participant flow, both arms) from its draw.io source with
matplotlib, because draw.io is not installed here and diagrams.net is not
reachable from the build environment. The .drawio file stays the source of
record; this reproduces its boxes, text, and arrows from the stored geometry
(boxes: mxGeometry x/y/width/height; arrows: explicit source/target points;
orthogonal arrows: down to the midpoint, across, down).

Run from figures/:  ../.venv/bin/python efig1_consort_render.py
"""

import html
import os
import re
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(
    HERE, "efig1_consort_three_panel.drawio"
)  # source of record, in the repository
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
PX = 0.01  # inches per draw.io pixel
PT = PX * 72  # points per pixel
FONT = 1.12  # the most the box text can grow before the narrowest box overflows (R9)


def text_of(v):
    v = re.sub(r"<br\s*/?>", "\n", v or "")
    v = re.sub(r"</(div|p)>", "\n", v)
    v = re.sub(r"<[^>]+>", "", v)
    return html.unescape(v).strip()


def fsize(v, default=12):
    m = re.search(r"font-size:\s*(\d+)px", v or "")
    return float(m.group(1)) if m else default


def style(s):
    return dict(
        kv.split("=", 1) if "=" in kv else (kv, "1")
        for kv in (s or "").split(";")
        if kv
    )


root = ET.fromstring(open(SRC, encoding="utf-8").read())
cells = list(root.iter("mxCell"))
xs, ys = [], []
for c in cells:
    g = c.find("mxGeometry")
    if c.get("vertex") == "1" and g is not None:
        x, y, w, h = (float(g.get(k, 0)) for k in ("x", "y", "width", "height"))
        xs += [x, x + w]
        ys += [y, y + h]
W, H = max(xs) + 20, max(ys) + 20
fig = plt.figure(figsize=(W * PX, H * PX))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")

for c in cells:
    g = c.find("mxGeometry")
    st = style(c.get("style"))
    if c.get("vertex") == "1" and g is not None:
        x, y, w, h = (float(g.get(k, 0)) for k in ("x", "y", "width", "height"))
        is_text = "text" in st
        if not is_text:
            ax.add_patch(
                Rectangle(
                    (x, y),
                    w,
                    h,
                    facecolor=st.get("fillColor", "#FFFFFF"),
                    edgecolor=st.get("strokeColor", "#000000"),
                    linewidth=1.0,
                )
            )
        t = text_of(c.get("value"))
        v = c.get("value") or ""
        if t:
            left = st.get("align") == "left"
            ax.text(
                x + (4 if left else w / 2),
                y + (2 if is_text else h / 2),
                t,
                ha="left" if left else "center",
                va="top" if is_text else "center",
                fontsize=fsize(v) * PT * FONT,
                family="Arial",
                fontweight="bold" if (is_text and "<b>" in v) else "normal",
                wrap=False,
            )
    elif c.get("edge") == "1" and g is not None:
        p = {
            q.get("as"): (float(q.get("x")), float(q.get("y")))
            for q in g.findall("mxPoint")
        }
        if "sourcePoint" not in p or "targetPoint" not in p:
            continue
        (x0, y0), (x1, y1) = p["sourcePoint"], p["targetPoint"]
        head = st.get("endArrow", "classic") != "none"
        if st.get("edgeStyle") == "orthogonalEdgeStyle" and x0 != x1 and y0 != y1:
            ym = (y0 + y1) / 2
            ax.plot(
                [x0, x0, x1], [y0, ym, ym], color="black", lw=1.2, solid_capstyle="butt"
            )
            x0, y0 = x1, ym
        ax.add_patch(
            FancyArrowPatch(
                (x0, y0),
                (x1, y1),
                arrowstyle="-|>" if head else "-",
                mutation_scale=8,
                color="black",
                lw=1.2,
                shrinkA=0,
                shrinkB=0,
            )
        )

os.makedirs(OUT, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(
        os.path.join(OUT, "eFigure1_drawio_superseded." + ext),
        dpi=300,
        facecolor="white",
    )
print("wrote eFigure1 to", OUT, "| canvas", W, "x", H)
