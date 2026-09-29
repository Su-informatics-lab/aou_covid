# -*- coding: utf-8 -*-
"""eFigure 1 (v26, R9): participant flow, re-laid out for print width.

The draw.io layout (efig1_consort_render.py) was 389 mm wide, so its box text
printed at about 4.6 pt once the figure was scaled to a 180 mm page width. This
script keeps the draw.io file as the source of every box's text and redraws the
flow on a 180 mm canvas with 7 pt text: boxes are narrower, text is wrapped to
fit them, and exclusion boxes sit in side columns beside the connector they
leave from, so they add no rows. The counts live only in the draw.io file
(figures/efig1_consort_three_panel.drawio); this script holds the layout only.
The MarketScan panel shows no count below 11 (the unmatched case is pooled with the
cases excluded near the data cutoff), a common Merative data-use threshold.
Writes submission_v25/04_figures/supplement/eFigure1.{pdf,png}.
"""

import html
import os
import re
import xml.etree.ElementTree as ET

from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath
from style import INK, MM, apply_style, plt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "efig1_consort_three_panel.drawio")
OUT = os.path.join(HERE, "..", "submission_v25", "04_figures", "supplement")
FS = 7.0  # pt
LINE = FS * 1.2 * 25.4 / 72  # mm per text line
PADV, PADH = 0.8, 1.4  # mm
GAP = 2.4  # mm between stacked boxes
SPLIT = 4.4  # mm for a split connector
FP = FontProperties(family="Arial", size=FS)
# columns (centre, width) in mm on a 180 mm canvas
TRUNK = (90, 56)
LEFT = (61, 46)
RIGHT = (119, 46)
EXL = (18, 34)
EXR = (162, 34)
FULL = (90, 104)


def texts():
    root = ET.fromstring(open(SRC, encoding="utf-8").read())
    out = {}
    for c in root.iter("mxCell"):
        if c.get("vertex") != "1":
            continue
        v = re.sub(r"<br\s*/?>", "\n", c.get("value") or "")
        v = re.sub(r"</(div|p)>", "\n", v)
        v = html.unescape(re.sub(r"<[^>]+>", "", v)).replace("\xa0", " ")
        out[c.get("id")] = [ln.strip() for ln in v.strip().split("\n") if ln.strip()]
    return out


def width_mm(s):
    return TextPath((0, 0), s, prop=FP).get_extents().width * 25.4 / 72


def wrap(lines, w):
    out = []
    for ln in lines:
        cur = ""
        for word in ln.split(" "):
            t = (cur + " " + word).strip()
            if cur and width_mm(t) > w - 2 * PADH:
                out.append(cur)
                cur = word
            else:
                cur = t
        out.append(cur)
    return out


class Flow:
    def __init__(self, ax, T):
        self.ax, self.T = ax, T

    def size(self, key, col, left=False):
        lines = wrap(self.T[key], col[1])
        return lines, len(lines) * LINE + 2 * PADV

    def box(self, key, col, ytop, left=False):
        lines, h = self.size(key, col)
        cx, w = col
        self.ax.add_patch(
            Rectangle(
                (cx - w / 2, ytop), w, h, facecolor="white", edgecolor=INK, lw=0.7
            )
        )
        if left:
            self.ax.text(
                cx - w / 2 + PADH,
                ytop + PADV,
                "\n".join(lines),
                ha="left",
                va="top",
                fontsize=FS,
                linespacing=1.2,
                color=INK,
            )
        else:
            self.ax.text(
                cx,
                ytop + h / 2,
                "\n".join(lines),
                ha="center",
                va="center",
                fontsize=FS,
                linespacing=1.2,
                color=INK,
            )
        return ytop + h

    def exbox(self, key, col, ymid):
        """exclusion box centred vertically on ymid; returns (edge x toward trunk)."""
        lines, h = self.size(key, col)
        self.box(key, col, ymid - h / 2, left=True)
        return col[0] + (col[1] / 2 if col[0] < 90 else -col[1] / 2)

    def arrow(self, a, b):
        self.ax.annotate(
            "",
            xy=b,
            xytext=a,
            arrowprops=dict(
                arrowstyle="-|>",
                color=INK,
                lw=0.7,
                mutation_scale=6,
                shrinkA=0,
                shrinkB=0,
            ),
        )

    def line(self, xs, ys):
        self.ax.plot(xs, ys, color=INK, lw=0.7, solid_capstyle="butt")

    def split(self, y0, y1, xl, xr, xc=90):
        ym = (y0 + y1) / 2
        self.line([xc, xc], [y0, ym])
        self.line([xl, xr], [ym, ym])
        self.arrow((xl, ym), (xl, y1))
        self.arrow((xr, ym), (xr, y1))


def panel_a(f, y):
    top = y
    y1 = f.box("a_r1", TRUNK, y)
    f.arrow(
        (TRUNK[0] + TRUNK[1] / 2, (top + y1) / 2),
        (f.exbox("a_ex_top", EXR, (top + y1) / 2), (top + y1) / 2),
    )
    y = y1 + GAP
    f.arrow((90, y1), (90, y))
    y2 = f.box("a_r2", TRUNK, y)
    y = y2 + GAP
    f.arrow((90, y2), (90, y))
    y3 = f.box("a_r3", TRUNK, y)
    y = y3 + SPLIT
    f.split(y3, y, LEFT[0], RIGHT[0])
    yl = f.box("a_r4L", LEFT, y)
    yr = f.box("a_r4R", RIGHT, y)
    y4 = max(yl, yr)
    y = y4 + 2 * GAP
    mid = (y4 + y) / 2
    f.arrow((LEFT[0], yl), (LEFT[0], y))
    f.arrow((RIGHT[0], yr), (RIGHT[0], y))
    f.arrow((LEFT[0], mid), (f.exbox("a_ex_larm", EXL, mid), mid))
    f.arrow((RIGHT[0], mid), (f.exbox("a_ex_rarm", EXR, mid), mid))
    yl = f.box("a_r5L", LEFT, y)
    yr = f.box("a_r5R", RIGHT, y)
    y = max(yl, yr) + GAP
    f.arrow((LEFT[0], yl), (LEFT[0], y))
    f.arrow((RIGHT[0], yr), (RIGHT[0], y))
    yp = f.box("a_psm", FULL, y)
    y = yp + 2 * GAP
    mid = (yp + y) / 2
    f.arrow((90, yp), (90, y))
    f.arrow((90, mid), (f.exbox("a_ex_trim", EXR, mid), mid))
    y7 = f.box("a_r7", TRUNK, y)
    y = y7 + SPLIT
    f.split(y7, y, LEFT[0], RIGHT[0])
    return max(f.box("a_r8L", LEFT, y), f.box("a_r8R", RIGHT, y))


def panel_b(f, y):
    rows = [("b_r0", "b_ex_0"), ("b_r1", "b_ex_1"), ("b_r2", "b_ex_2"), ("b_r3", None)]
    prev, exb = None, y - 1.5  # exb: bottom of the last exclusion box drawn
    for key, ex in rows:
        if ex:
            # a tall exclusion box, centred on its trunk box, must clear the one above
            hb = f.size(key, TRUNK)[1]
            he = f.size(ex, EXR)[1]
            y = max(y, exb + 1.5 + (he - hb) / 2)
        if prev is not None:
            f.arrow((90, prev), (90, y))
        yb = f.box(key, TRUNK, y)
        if ex:
            mid = (y + yb) / 2
            f.arrow((TRUNK[0] + TRUNK[1] / 2, mid), (f.exbox(ex, EXR, mid), mid))
            exb = mid + he / 2
        prev, y = yb, yb + GAP
    y3 = prev
    y = y3 + SPLIT
    f.split(y3, y, LEFT[0], RIGHT[0])
    yl = f.box("b_r4L", LEFT, y)
    yr = f.box("b_r4R", RIGHT, y)
    y = max(yl, yr) + 2 * GAP
    mid = (max(yl, yr) + y) / 2
    f.arrow((LEFT[0], yl), (LEFT[0], y))
    f.arrow((RIGHT[0], yr), (RIGHT[0], y))
    f.arrow((RIGHT[0], mid), (f.exbox("b_ex_r", EXR, mid), mid))
    yp = f.box("b_psm", FULL, y)
    y = yp + GAP
    f.arrow((90, yp), (90, y))
    y7 = f.box("b_r7", TRUNK, y)
    y = y7 + SPLIT
    f.split(y7, y, LEFT[0], RIGHT[0])
    return max(f.box("b_r8L", LEFT, y), f.box("b_r8R", RIGHT, y))


def panel_c(f, y):
    y2 = f.box("c_r2", TRUNK, y)
    y = y2 + GAP
    f.arrow((90, y2), (90, y))
    y3 = f.box("c_r3", TRUNK, y)
    y = y3 + SPLIT
    f.split(y3, y, LEFT[0], RIGHT[0])
    yl = f.box("c_r4L", LEFT, y)
    yr = f.box("c_r4R", RIGHT, y)
    y4 = max(yl, yr)
    y = y4 + 2 * GAP
    mid = (y4 + y) / 2
    f.arrow((LEFT[0], yl), (LEFT[0], y))
    f.arrow((RIGHT[0], yr), (RIGHT[0], y))
    f.arrow((LEFT[0], mid), (f.exbox("c_ex_larm", EXL, mid), mid))
    f.arrow((RIGHT[0], mid), (f.exbox("c_ex_rarm", EXR, mid), mid))
    yl = f.box("c_r5L", LEFT, y)
    yr = f.box("c_r5R", RIGHT, y)
    y = max(yl, yr) + GAP
    f.arrow((LEFT[0], yl), (LEFT[0], y))
    f.arrow((RIGHT[0], yr), (RIGHT[0], y))
    yp = f.box("c_psm", FULL, y)
    y = yp + 2 * GAP
    mid = (yp + y) / 2
    f.arrow((90, yp), (90, y))
    f.arrow((90, mid), (f.exbox("c_ex_trim", EXR, mid), mid))
    y7 = f.box("c_r7", TRUNK, y)
    y = y7 + SPLIT
    f.split(y7, y, LEFT[0], RIGHT[0])
    return max(f.box("c_r8L", LEFT, y), f.box("c_r8R", RIGHT, y))


def main():
    apply_style()
    T = texts()
    H = 240.0  # provisional; the canvas is cropped to the drawn height below
    fig = plt.figure(figsize=(180 * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 180)
    ax.set_ylim(H, 0)
    ax.axis("off")
    f = Flow(ax, T)
    y = 4.5
    for letter, fn, title in (
        ("A", panel_a, "COVID-19, All of Us"),
        ("B", panel_b, "Influenza, All of Us"),
        ("C", panel_c, "COVID-19, MarketScan comparison cohort"),
    ):
        # the letter and title sit in the empty left column beside the first box
        ax.text(1, y, letter, fontsize=10, fontweight="bold", va="top", color=INK)
        ax.text(
            6,
            y + 0.3,
            title.replace(", ", ",\n", 1),
            fontsize=8,
            fontweight="bold",
            va="top",
            color=INK,
            linespacing=1.15,
        )
        y = fn(f, y) + 4.5
    used = y - 3.0
    ax.set_ylim(used, 0)
    fig.set_size_inches(180 * MM, used * MM)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, "eFigure1." + ext), dpi=400)
    plt.close(fig)
    print("wrote eFigure1 | canvas 180 x %.0f mm | text %.1f pt" % (used, FS))


if __name__ == "__main__":
    main()
