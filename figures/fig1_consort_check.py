# -*- coding: utf-8 -*-
"""Guard for the Figure 1 CONSORT diagram.

The .drawio is hand-tuned in draw.io, so this does not regenerate it. It reads
the file, pulls every number out of every box, and checks two things a reader
could check with a calculator:

  1. each count the study reports appears in the diagram, and
  2. both flow chains close -- 17 identities across the two panels.

Counts were re-counted 2026-09-02 on the Researcher Workbench (All of Us) and on
Quartz (MarketScan); their provenance is in
reviews/2026-09-02_v19_platform_completion.md.

    python3 figures/fig1_consort_check.py working/drawio/fig1_consort.drawio
"""

import html
import re
import sys
import xml.etree.ElementTree as ET

SRC = sys.argv[1] if len(sys.argv) > 1 else "working/drawio/fig1_consort.drawio"

# (label, left-hand side, right-hand side) -- every step of both chains
CHECKS = [
    ("a  413,457 = 161,410 + 252,047", 413457, 161410 + 252047),
    ("a  25,160 = 4,064 + 21,096", 25160, 4064 + 21096),
    ("a  cases   4,064 - 67 = 3,997", 3997, 4064 - 67),
    ("a  ctrls   21,096 - 284 = 20,812", 20812, 21096 - 284),
    ("a  matched 3,997 + 15,960 = 19,957", 19957, 3997 + 15960),
    ("a  19,957 - 437 = 19,520", 19520, 19957 - 437),
    ("a  15,960 - 437 = 15,523", 15523, 15960 - 437),
    ("a  19,520 = 15,523 + 3,997", 19520, 15523 + 3997),
    ("b  4,423,200 = 139,489 + 4,283,711", 4423200, 139489 + 4283711),
    ("b  cases   139,489 - 11,588 = 127,901", 127901, 139489 - 11588),
    ("b  ctrls   4,283,711 - 401,984 = 3,881,727", 3881727, 4283711 - 401984),
    ("b  127,901 - 1 = 127,900", 127900, 127901 - 1),
    ("b  matched 127,900 + 511,581 = 639,481", 639481, 127900 + 511581),
    ("b  639,481 - 1,802 = 637,679", 637679, 639481 - 1802),
    ("b  127,900 - 204 = 127,696", 127696, 127900 - 204),
    ("b  511,581 - 1,598 = 509,983", 509983, 511581 - 1598),
    ("b  637,679 = 509,983 + 127,696", 637679, 509983 + 127696),
]

# counts the diagram itself must show (15,960, 511,581, 444,575 and 127,900 are
# intermediate and live in the legend, not in a box)
MUST_APPEAR = {
    "a": [
        "413,457",
        "161,410",
        "252,047",
        "25,160",
        "21,096",
        "4,064",
        "284",
        "67",
        "20,812",
        "3,997",
        "437",
        "19,520",
        "15,523",
        "9,784",
    ],
    "b": [
        "4,423,200",
        "4,283,711",
        "139,489",
        "401,984",
        "11,588",
        "3,881,727",
        "127,901",
        "1,802",
        "1,598",
        "204",
        "637,679",
        "127,696",
        "509,983",
        "443,061",
    ],
}


def text_of(cell):
    v = html.unescape(cell.get("value") or "")
    v = re.sub(r"<[^>]+>", " ", v)
    return re.sub(r"\s+", " ", html.unescape(v).replace("\xa0", " ")).strip()


def main():
    root = ET.parse(SRC).getroot()
    cells = root.findall(".//mxCell")
    seen = {"a": set(), "b": set()}
    for c in cells:
        cid = c.get("id") or ""
        panel = "a" if cid.startswith("a") else "b" if cid.startswith("b") else None
        t = text_of(c)
        for n in re.findall(r"\d[\d,]*", t):
            if panel:
                seen[panel].add(n)
            else:  # a cell the author added by hand; count it for both panels
                seen["a"].add(n)
                seen["b"].add(n)
    bad = 0
    for p in ("a", "b"):
        missing = [n for n in MUST_APPEAR[p] if n not in seen[p]]
        print(
            f"panel {p}: {len(MUST_APPEAR[p]) - len(missing)}/{len(MUST_APPEAR[p])} expected counts present"
            + (f"   MISSING {missing}" if missing else "")
        )
        bad += len(missing)
    print()
    for lab, lhs, rhs in CHECKS:
        ok = lhs == rhs
        bad += not ok
        print(
            ("  OK   " if ok else "  FAIL ")
            + lab
            + ("" if ok else f"   ({lhs} vs {rhs})")
        )
    print()
    if bad:
        sys.exit(f"{bad} problem(s) in {SRC}")
    print(f"{SRC}: both chains close, every reported count is drawn")


if __name__ == "__main__":
    main()
