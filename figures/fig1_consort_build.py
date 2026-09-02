# -*- coding: utf-8 -*-
"""Rebuild fig1_consort.drawio as a two-arm CONSORT flowchart, in the file's own
visual language: white boxes, 1.5 pt black rules, Arial 12 px, bold counts,
16 px bold panel letters, block-arrow connectors.

Per panel: a centre spine for the whole cohort, two arms after the case/control
split, and every loss in a box beside the stream it came from -- left of the
control arm, right of the case arm.  The panels are stacked so each gets the
full canvas width; side by side there is no room for the arms.

Counts re-counted 2026-09-02 on the Researcher Workbench (All of Us) and on
Quartz (MarketScan).  Every addition and subtraction is asserted below; the
script refuses to write a file whose arithmetic does not close.
"""

import html as H
import sys

W_CANVAS, H_CANVAS = 1600, 900
COL = dict(
    lside=(40, 250),
    larm=(330, 280),
    spine=(640, 280),
    rarm=(950, 280),
    rside=(1270, 290),
)
PSM_X, PSM_W = 330, 900
ROW = dict(lab=2, r1=26, r2=76, r3=126, r4=176, r5=232, psm=284, r7=356, r8=406)
H_BOX, H_PSM, H_TALL = 28, 46, 44
PANEL_Y = dict(a=0, b=440)

BOX = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;"
BOXL = BOX + "align=left;spacingLeft=8;"
ARROW = "strokeColor=#000000;strokeWidth=1.5;endArrow=block;endFill=1;"
ELBOW = "edgeStyle=orthogonalEdgeStyle;strokeColor=#000000;strokeWidth=1.5;endArrow=block;endFill=1;rounded=0;curved=0;"
LABEL = "text;html=1;align=left;verticalAlign=top;"

cells = []


def box(cid, col, y, w, h, lines, style=BOX, x=None):
    x = COL[col][0] if x is None else x
    w = COL[col][1] if w is None else w
    v = f'<font style="font-size:12px;font-family:Arial;">{"<br>".join(lines)}</font>'
    cells.append(
        f'        <mxCell id="{cid}" value="{H.escape(v, quote=True)}" style="{style}" vertex="1" parent="1">\n'
        f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n'
        f"        </mxCell>"
    )


def arrow(cid, p0, p1, style=ARROW):
    cells.append(
        f'        <mxCell id="{cid}" style="{style}" edge="1" parent="1">\n'
        f'          <mxGeometry relative="1" as="geometry">\n'
        f'            <mxPoint x="{p0[0]}" y="{p0[1]}" as="sourcePoint" />\n'
        f'            <mxPoint x="{p1[0]}" y="{p1[1]}" as="targetPoint" />\n'
        f"          </mxGeometry>\n        </mxCell>"
    )


def cx(col):
    return COL[col][0] + COL[col][1] / 2


def b(n):
    return f"<b>{n}</b>"


def panel(p, Y, spine_rows, arms, excl, psm, analytic):
    lab = f'<b><font style="font-size:16px;font-family:Arial;">{p}</font></b>'
    y_lab = Y + ROW[spine_rows[0][0]] - 24
    cells.append(
        f'        <mxCell id="{p}_lab" value="{H.escape(lab, quote=True)}" style="{LABEL}" vertex="1" parent="1">\n'
        f'          <mxGeometry x="20" y="{y_lab}" width="30" height="25" as="geometry" />\n        </mxCell>'
    )
    for row, lines in spine_rows:
        box(f"{p}_{row}", "spine", Y + ROW[row], None, H_BOX, lines)
    keys = [r for r, _ in spine_rows]
    for i in range(len(keys) - 1):
        arrow(
            f"{p}_e_{keys[i]}_{keys[i+1]}",
            (cx("spine"), Y + ROW[keys[i]] + H_BOX),
            (cx("spine"), Y + ROW[keys[i + 1]]),
        )
    if "top" in excl:
        lines, h = excl["top"]
        ytop = Y + ROW[keys[0]]
        box(f"{p}_ex_top", "rside", ytop, None, h, lines, BOXL)
        arrow(
            f"{p}_e_extop",
            (COL["spine"][0] + COL["spine"][1], ytop + H_BOX / 2),
            (COL["rside"][0], ytop + H_BOX / 2),
        )
    yl = Y + ROW[keys[-1]] + H_BOX
    for col in ("larm", "rarm"):
        arrow(f"{p}_e_split_{col}", (cx("spine"), yl), (cx(col), Y + ROW["r4"]), ELBOW)
    for row in ("r4", "r5"):
        L, R = arms[row]
        box(f"{p}_{row}L", "larm", Y + ROW[row], None, H_BOX, L)
        box(f"{p}_{row}R", "rarm", Y + ROW[row], None, H_BOX, R)
    for col in ("larm", "rarm"):
        arrow(
            f"{p}_e_{col}45", (cx(col), Y + ROW["r4"] + H_BOX), (cx(col), Y + ROW["r5"])
        )
    ymid = Y + (ROW["r4"] + H_BOX + ROW["r5"]) / 2
    for side, tocol in (("larm", "lside"), ("rarm", "rside")):
        if side not in excl:
            continue
        lines, h = excl[side]
        box(f"{p}_ex_{side}", tocol, ymid - h / 2, None, h, lines, BOXL)
        edge = COL[tocol][0] + COL[tocol][1] if tocol == "lside" else COL[tocol][0]
        arrow(f"{p}_e_ex{side}", (cx(side), ymid), (edge, ymid))
    box(f"{p}_psm", "spine", Y + ROW["psm"], PSM_W, H_PSM, psm, BOX, x=PSM_X)
    for col in ("larm", "rarm"):
        arrow(
            f"{p}_e_{col}psm",
            (cx(col), Y + ROW["r5"] + H_BOX),
            (cx(col), Y + ROW["psm"]),
        )
    box(f"{p}_r7", "spine", Y + ROW["r7"], None, H_BOX, analytic["total"])
    arrow(
        f"{p}_e_psm7",
        (cx("spine"), Y + ROW["psm"] + H_PSM),
        (cx("spine"), Y + ROW["r7"]),
    )
    if "trim" in excl:
        lines, h = excl["trim"]
        ymid2 = Y + (ROW["psm"] + H_PSM + ROW["r7"]) / 2
        box(f"{p}_ex_trim", "rside", ymid2 - h / 2 + 6, None, h, lines, BOXL)
        arrow(f"{p}_e_extrim", (cx("spine"), ymid2), (COL["rside"][0], ymid2))
    box(f"{p}_r8L", "larm", Y + ROW["r8"], None, H_TALL, analytic["ctrl"])
    box(f"{p}_r8R", "rarm", Y + ROW["r8"], None, H_TALL, analytic["case"])
    for col in ("larm", "rarm"):
        arrow(
            f"{p}_e_78{col}",
            (cx("spine"), Y + ROW["r7"] + H_BOX),
            (cx(col), Y + ROW["r8"]),
            ELBOW,
        )


INCOMPLETE = ["&nbsp; &nbsp; Incomplete pre-index", "&nbsp; &nbsp; matching variables"]
PSM_HEAD = "Propensity score matching &#8212; 1:4 nearest neighbour, with replacement, 0.2 SD caliper"

panel(
    "a",
    PANEL_Y["a"],
    spine_rows=[
        ("r1", [f'{b("413,457")} All of Us participants (v7)']),
        ("r2", [f'{b("252,047")} Included']),
        ("r3", [f'{b("25,160")} COVID-19 positive']),
    ],
    arms={
        "r4": (
            [f'{b("21,096")} Outpatient only'],
            [f'{b("4,064")} Hospitalized &#8804;14 days'],
        ),
        "r5": ([f'{b("20,812")} Eligible controls'], [f'{b("3,997")} Eligible cases']),
    },
    excl={
        "top": (
            [
                f'{b("161,410")} Excluded',
                "&nbsp; &nbsp; No diagnosis data",
                "&nbsp; &nbsp; No Basics Survey",
            ],
            62,
        ),
        "larm": ([f'{b("284")} Controls excluded'] + INCOMPLETE, 62),
        "rarm": ([f'{b("67")} Cases excluded'] + INCOMPLETE, 62),
        "trim": (
            [
                f'{b("437")} Control observations excluded',
                "&nbsp; &nbsp; Incomplete follow-up near data cutoff",
            ],
            48,
        ),
    },
    psm=[
        PSM_HEAD,
        "Survey date &#183; Number of diagnoses &#183; Length of medical history",
    ],
    analytic={
        "total": [f'{b("19,520")} Observations in {b("3,997")} strata'],
        "ctrl": [
            f'{b("15,523")} Control observations',
            "9,784 individuals, with replacement",
        ],
        "case": [f'{b("3,997")} Cases'],
    },
)

panel(
    "b",
    PANEL_Y["b"],
    spine_rows=[
        ("r2", ["MarketScan Commercial Claims, 2020&#8211;2023"]),
        ("r3", [f'{b("4,423,200")} COVID-19 positive']),
    ],
    arms={
        "r4": (
            [f'{b("4,283,711")} Outpatient only'],
            [f'{b("139,489")} Hospitalized &#8804;14 days'],
        ),
        "r5": (
            [f'{b("3,881,727")} Eligible controls'],
            [f'{b("127,901")} Eligible cases'],
        ),
    },
    excl={
        "larm": ([f'{b("401,984")} Controls excluded'] + INCOMPLETE, 62),
        "rarm": ([f'{b("11,588")} Cases excluded'] + INCOMPLETE, 62),
        "trim": (
            [
                f'{b("1")} Case excluded &#8212; no match in caliper',
                f'{b("1,802")} Excluded near data cutoff',
                "&nbsp; &nbsp; 1,598 control observations, 204 cases",
            ],
            62,
        ),
    },
    psm=[
        PSM_HEAD,
        "Enrollment date &#183; Number of diagnoses &#183; Length of insurance coverage",
    ],
    analytic={
        "total": [f'{b("637,679")} Observations in {b("127,696")} strata'],
        "ctrl": [
            f'{b("509,983")} Control observations',
            "443,061 individuals, with replacement",
        ],
        "case": [f'{b("127,696")} Cases'],
    },
)

CHECKS = [
    ("a  413,457 = 161,410 + 252,047", 413457, 161410 + 252047),
    ("a  25,160 = 4,064 + 21,096", 25160, 4064 + 21096),
    ("a  4,064 - 67 = 3,997", 3997, 4064 - 67),
    ("a  21,096 - 284 = 20,812", 20812, 21096 - 284),
    ("a  3,997 + 15,960 = 19,957 matched", 19957, 3997 + 15960),
    ("a  19,957 - 437 = 19,520", 19520, 19957 - 437),
    ("a  15,960 - 437 = 15,523", 15523, 15960 - 437),
    ("a  19,520 = 15,523 + 3,997", 19520, 15523 + 3997),
    ("b  4,423,200 = 139,489 + 4,283,711", 4423200, 139489 + 4283711),
    ("b  139,489 - 11,588 = 127,901", 127901, 139489 - 11588),
    ("b  4,283,711 - 401,984 = 3,881,727", 3881727, 4283711 - 401984),
    ("b  127,901 - 1 = 127,900", 127900, 127901 - 1),
    ("b  127,900 + 511,581 = 639,481 matched", 639481, 127900 + 511581),
    ("b  639,481 - 1,802 = 637,679", 637679, 639481 - 1802),
    ("b  127,900 - 204 = 127,696", 127696, 127900 - 204),
    ("b  511,581 - 1,598 = 509,983", 509983, 511581 - 1598),
    ("b  637,679 = 509,983 + 127,696", 637679, 509983 + 127696),
]
bad = [c for c in CHECKS if c[1] != c[2]]
for lab_, a_, b_ in CHECKS:
    print(
        ("  OK  " if a_ == b_ else "  FAIL")
        + " "
        + lab_
        + ("" if a_ == b_ else f"   ({a_} vs {b_})")
    )
if bad:
    raise SystemExit("refusing to write: arithmetic does not close")

XML = (
    f'<mxfile host="app.diagrams.net" agent="Claude">\n'
    f'  <diagram name="CONSORT" id="consort-flow">\n'
    f'    <mxGraphModel dx="1414" dy="790" grid="1" gridSize="10" guides="1" tooltips="1" connect="1"'
    f' arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W_CANVAS}" pageHeight="{H_CANVAS}" math="0" shadow="0">\n'
    f'      <root>\n        <mxCell id="0" />\n        <mxCell id="1" parent="0" />\n'
    + "\n".join(cells)
    + "\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n"
)

import xml.etree.ElementTree as ET

ET.fromstring(XML)
P = sys.argv[1] if len(sys.argv) > 1 else "working/fig1_consort.drawio"
open(P, "w", encoding="utf-8").write(XML)
nb = XML.count(chr(118) + 'ertex="1"')
ne = XML.count('edge="1"')
print(f"\nwrote {P}: {nb} boxes, {ne} connectors, {W_CANVAS}x{H_CANVAS}")
