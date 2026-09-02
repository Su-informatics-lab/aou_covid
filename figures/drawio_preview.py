# -*- coding: utf-8 -*-

"""Preview renderer for a plain mxGraphModel: boxes, elbow/straight arrows, HTML text.
Not a draw.io replacement -- enough to see overlaps, overflow and misrouted arrows.

Needs matplotlib, so it runs in the analysis container rather than on the laptop."""

import html
import re
import sys
import xml.etree.ElementTree as ET

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

matplotlib.use("Agg")

SRC = sys.argv[1] if len(sys.argv) > 1 else "fig1_consort.drawio"
root = ET.parse(SRC).getroot()
gm = root.find(".//mxGraphModel")
W, Hc = int(gm.get("pageWidth")), int(gm.get("pageHeight"))


def sty(s):
    d = {}
    for kv in (s or "").split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            d[k] = v
    return d


def lines_of(v):
    t = html.unescape(v or "")
    t = t.replace("<br>", "\n")
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\xa0", " ")
    return [l.rstrip() for l in t.split("\n")]


def bold_spans(v):
    return bool(re.search(r"<b>", v or ""))


DPI = 110
fig = plt.figure(figsize=(W / DPI, Hc / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(Hc, 0)
ax.axis("off")
ax.add_patch(Rectangle((0, 0), W, Hc, fc="white", ec="none"))

cells = gm.findall(".//mxCell")
warn = []
boxes = []
for c in cells:
    g = c.find("mxGeometry")
    if g is None:
        continue
    st = sty(c.get("style"))
    if c.get("vertex") == "1":
        x, y = float(g.get("x", 0)), float(g.get("y", 0))
        w, h = float(g.get("width", 0)), float(g.get("height", 0))
        if st.get("fillColor"):
            ax.add_patch(Rectangle((x, y), w, h, fc="white", ec="black", lw=1.4))
            boxes.append((c.get("id"), x, y, w, h))
        ls = [l for l in lines_of(c.get("value")) if l.strip() != ""]
        align = st.get("align", "center")
        n = len(ls)
        fs = 16 if "16px" in (c.get("value") or "") else 12
        fs_pt = fs * 72 / DPI * (DPI / 72) * 0.62  # rough visual match
        for i, l in enumerate(ls):
            ty = y + h / 2 - (n - 1) * 7.5 + i * 15 if st.get("fillColor") else y + 12
            tx = x + 8 if align == "left" else x + w / 2
            ha = "left" if align == "left" else "center"
            ax.text(
                tx,
                ty,
                l,
                ha=ha,
                va="center",
                fontsize=fs_pt,
                family="DejaVu Sans",
                fontweight="bold" if fs == 16 else "normal",
            )
            if st.get("fillColor"):
                est = len(l) * fs * 0.52 + 16
                if est > w:
                    warn.append(
                        f"OVERFLOW {c.get('id')}: {l[:44]!r} ~{est:.0f}px in {w:.0f}px"
                    )
    else:
        pts = g.findall("mxPoint")
        d = {p.get("as"): (float(p.get("x")), float(p.get("y"))) for p in pts}
        if "sourcePoint" not in d or "targetPoint" not in d:
            continue
        (x0, y0), (x1, y1) = d["sourcePoint"], d["targetPoint"]
        if "orthogonalEdgeStyle" in (c.get("style") or "") and x0 != x1 and y0 != y1:
            ym = (y0 + y1) / 2
            ax.plot([x0, x0], [y0, ym], color="black", lw=1.4)
            ax.plot([x0, x1], [ym, ym], color="black", lw=1.4)
            ax.annotate(
                "",
                xy=(x1, y1),
                xytext=(x1, ym),
                arrowprops=dict(
                    arrowstyle="-|>", color="black", lw=1.4, mutation_scale=11
                ),
            )
        else:
            ax.annotate(
                "",
                xy=(x1, y1),
                xytext=(x0, y0),
                arrowprops=dict(
                    arrowstyle="-|>", color="black", lw=1.4, mutation_scale=11
                ),
            )

# overlap check
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        a, b = boxes[i], boxes[j]
        if (
            a[1] < b[1] + b[3]
            and b[1] < a[1] + a[3]
            and a[2] < b[2] + b[4]
            and b[2] < a[2] + a[4]
        ):
            warn.append(f"OVERLAP {a[0]} / {b[0]}")
fig.savefig("preview.png", dpi=DPI)
print(f"boxes {len(boxes)}  canvas {W}x{Hc}")
print("\n".join(warn) if warn else "no overflow or overlap detected")
