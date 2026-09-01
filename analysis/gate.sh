#!/usr/bin/env bash
# The number gate. Asserts every figure the manuscript and its supplement print
# against the artifact it came from, then writes the ledger.
#
#   bash analysis/gate.sh check     # fails on the first drift
#   bash analysis/gate.sh ledger    # writes submission/CLAIM_LEDGER.md
#
# Both documents are flattened into one text blob, because a number in eTable 10
# must trace to the same artifact as the same number in Table 1, and asserting
# only against the main text would leave the supplement unchecked -- which is
# where eTable 14 published a null as significant.
set -uo pipefail
MODE="${1:-check}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="${MANUSCRIPT:-$ROOT/submission/02_manuscript.docx}"
SUP="${SUPPLEMENT:-$ROOT/submission/04_supplementary/JAMIA_supplementary.docx}"
TXT="$(mktemp -t aou_ms.XXXXXX).txt"

[ -f "$DOC" ] || { echo "gate: manuscript not found: $DOC" >&2; exit 2; }

python3 - "$TXT" "$DOC" "$SUP" <<'PY'
import os, sys
from docx import Document
out = []
for path in sys.argv[2:]:
    if not path or not os.path.exists(path):
        continue
    d = Document(path)
    out += [p.text for p in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            out.append("\t".join(c.text for c in r.cells))
# ledger.plain() strips LaTeX comments, so a bare "%" would delete the rest of
# the line -- and "95% CI 0.68-0.80" is the shape of every interval we assert.
# Escape it the way a .tex file would.
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out).replace("%", r"\%"))
PY

cd "$ROOT"
PYTHONPATH="$ROOT/analysis${PYTHONPATH:+:$PYTHONPATH}" \
  python3 analysis/ledger.py "$MODE" \
    --project . --manuscript "$TXT" \
    --validator analysis/validate_numbers.py
rc=$?
rm -f "$TXT"
exit $rc
