#!/usr/bin/env python3
# Vendored from the `haining-research` skill (scripts/ledger.py) so this
# repository can run its own number gate without the skill installed.
# Do not edit here; edit the skill and re-vendor.
"""The number gate, and the claim ledger generated from it.

Write the validator; generate the ledger from it.

A hand-written claim ledger drifts from the manuscript within days, because
keeping it current is voluntary. A validator that asserts each number against the
frozen artifact it came from cannot drift -- it fails the build -- but a reader
only sees that it exited zero, not the mapping it enforced, and a reproducibility
auditor asks for the mapping.

So the validator runs twice. Once asserting, and once with `require` replaced by a
recorder, which captures every assertion with the validator's own label for it.
The ledger becomes a byproduct of the test, and the two cannot disagree, because
they are the same code.

The second half is the part people skip. Every number the manuscript prints that
the validator does NOT assert gets listed too, because an unchecked number and a
checked one look identical until someone looks. Those are arithmetic the text does
itself, figures from cited papers, or things nobody has checked.

The project supplies the assertions, in `analysis/validate_numbers.py`:

    from ledger import Validator

    def assertions(v: Validator, text: str) -> None:
        f = v.frame("artifacts/pilot_v0.1/final/cross-cohort-summary.csv")
        row = v.one(f, outcome="mortality", exposure="withdrawal_2plus")
        v.require(text, v.fmt(row["risk"], 1), "standardised risk, two or more stopped")
        v.interval(text, row["rr"], row["lo"], row["hi"], "gradient, two or more")
        v.banned(text, "487", "superseded analysed-set denominator")
        v.figure("figures/cohort_flow.pdf", "manuscript/cohort_flow.pdf")

Then:

    python ledger.py check  --project . --manuscript manuscript.tex
    python ledger.py ledger --project . --manuscript manuscript.tex

`check` belongs in the build. `ledger` runs before submission.

No third-party dependencies. A pandas DataFrame may be passed to `one()` if the
project already uses pandas; a plain CSV path works without it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- text normalising

# Lancet and several other journals print a midline dot for the decimal separator.
# Thousands are separated by a thin space, a normal space, or a comma depending on
# house style. All of that has to collapse before a printed value can be compared
# to a computed one.
MIDLINE = "\u00b7"
THIN_SPACES = "\u2009\u202f\u00a0"


def plain(text: str) -> str:
    """Strip LaTeX so numbers can be found in the prose a reader sees.

    The order here is load-bearing. A midline decimal is written `2$\\cdot$8`, and
    a thousands separator is written `205\\,794`; if the generic command strip runs
    first, both numbers are torn in half and every assertion against them fails for
    a reason that has nothing to do with the analysis.
    """
    # Preamble carries no claims, and stripping its commands leaves their
    # arguments behind as stray words.
    body = re.split(r"\\begin\{document\}", text, maxsplit=1)
    text = body[1] if len(body) > 1 else text

    text = re.sub(r"(?<!\\)%.*$", "", text, flags=re.M)           # comments
    text = re.sub(r"\$?\\cdot\$?|\{\\cdot\}", MIDLINE, text)      # midline decimal
    text = re.sub(r"(?<=\d)\\[,.;:!\s](?=\d)", "", text)          # 205\,794
    text = text.replace("\\%", "%").replace("\\&", "&").replace("\\_", "_")
    text = text.replace("---", "-").replace("--", "-")

    text = re.sub(r"\\(?:label|ref|cite[a-z]*|input|include|documentclass|usepackage)"
                  r"(?:\[[^]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", text)
    text = re.sub(r"\$([^$]*)\$", r"\1", text)                    # inline math
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)                   # remaining commands
    text = text.replace("{", " ").replace("}", " ").replace("~", " ")
    for ch in THIN_SPACES:
        text = text.replace(ch, " ")
    return re.sub(r"[ \t]+", " ", text)


def canon(value: str) -> str:
    """Canonical form of a printed number: midline dot to point, separators gone."""
    s = str(value).strip()
    s = s.replace(MIDLINE, ".")
    for ch in THIN_SPACES:
        s = s.replace(ch, "")
    s = re.sub(r"(?<=\d)[ ,](?=\d\d\d\b)", "", s)   # thousands separator
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    return s


def canon_text(text: str) -> str:
    return canon(plain(text))


NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")


def find_numbers(text: str) -> list[str]:
    """Every number a reader could check, in the order printed."""
    return NUMBER.findall(canon_text(text))


def sentence_for(text: str, value: str, width: int = 160) -> str:
    """The sentence a value appears in, for the ledger's third column."""
    flat = re.sub(r"\s+", " ", canon_text(text))
    hit = re.search(rf"(?<![\w.]){re.escape(canon(value))}(?![\w.])", flat)
    if not hit:
        return ""
    start = flat.rfind(". ", 0, hit.start())
    start = 0 if start < 0 else start + 2
    end = flat.find(". ", hit.end())
    end = len(flat) if end < 0 else end + 1
    return flat[start:end].strip()[:width]


# ---------------------------------------------------------------- tiny frames

class Row(dict):
    """A row that supports both row['x'] and row.x, so either style reads well."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class Frame:
    """A CSV, as a list of Rows. Enough for selection; no dependency."""

    def __init__(self, rows: list[Row], source: str):
        self.rows = rows
        self.source = source

    def __len__(self):
        return len(self.rows)

    def select(self, **keys) -> list[Row]:
        out = []
        for row in self.rows:
            if all(str(row.get(k, "")).strip() == str(v).strip() for k, v in keys.items()):
                out.append(row)
        return out


# ---------------------------------------------------------------- the validator

class Drift(AssertionError):
    """A number in the manuscript does not match the frozen artifact."""


class Validator:
    """Assertions in `check` mode; a recorder in `record` mode.

    Same object, same calls, same project code. The mode only changes whether a
    failure raises or is written down -- which is what keeps the ledger and the
    gate from ever describing different things.
    """

    def __init__(self, project: Path, mode: str = "check"):
        if mode not in {"check", "record"}:
            raise ValueError("mode must be 'check' or 'record'")
        self.project = Path(project).resolve()
        self.mode = mode
        self.records: list[dict] = []      # every assertion, with its label
        self.failures: list[str] = []
        self.sources: set[str] = set()
        self.allows: list[tuple[str, str]] = []

    # -- loading -------------------------------------------------------------

    def frame(self, relpath: str) -> Frame:
        path = (self.project / relpath).resolve()
        self.sources.add(relpath)
        if not path.exists():
            self._fail(f"missing frozen artifact: {relpath}")
            return Frame([], relpath)
        with path.open(newline="", encoding="utf-8") as fh:
            rows = [Row(r) for r in csv.DictReader(fh)]
        return Frame(rows, relpath)

    def one(self, frame, **keys) -> Row:
        """Exactly one row, or a failure.

        Raising on several matches is deliberate. A selection that silently takes
        the first of two is how a manuscript ends up quoting the wrong subgroup.
        """
        if hasattr(frame, "select"):
            rows = frame.select(**keys)
        else:                                    # a pandas DataFrame
            mask = None
            for k, v in keys.items():
                m = frame[k].eq(v)
                mask = m if mask is None else (mask & m)
            sub = frame if mask is None else frame.loc[mask]
            rows = [Row(r) for r in sub.to_dict("records")]
        if len(rows) != 1:
            self._fail(f"expected one row for {keys}; found {len(rows)}")
            return Row()
        return rows[0]

    # -- formatting ----------------------------------------------------------

    @staticmethod
    def fmt(value, dp: int = 2, midline: bool = False) -> str:
        """Format a computed value the way the manuscript prints it."""
        out = f"{float(value):.{dp}f}"
        return out.replace(".", MIDLINE) if midline else out

    # -- assertions ----------------------------------------------------------

    def require(self, text: str, value, label: str, source: str | None = None) -> None:
        """This value, printed somewhere in the manuscript."""
        target = canon(value)
        present = bool(re.search(rf"(?<![\w.]){re.escape(target)}(?![\w.])",
                                 canon_text(text)))
        self.records.append({
            "value": str(value), "label": label, "kind": "value",
            "source": source or self._last_source(), "present": present,
            "sentence": sentence_for(text, value) if present else "",
        })
        if not present:
            self._fail(f"{label}: {value} not found in the manuscript")

    def interval(self, text: str, est, lo, hi, label: str, dp: int = 2,
                 midline: bool = False, source: str | None = None) -> None:
        """The estimate and both bounds, each present.

        Checked as a triple under one label rather than as three unrelated
        values, because the failure this catches is an interval that came from a
        different run than its point estimate. Each number does appear somewhere
        when that happens; what is wrong is the grouping.
        """
        parts = [self.fmt(est, dp, midline), self.fmt(lo, dp, midline), self.fmt(hi, dp, midline)]
        flat = canon_text(text)
        missing = [p for p in parts
                   if not re.search(rf"(?<![\w.]){re.escape(canon(p))}(?![\w.])", flat)]
        for part, role in zip(parts, ("estimate", "lower bound", "upper bound")):
            self.records.append({
                "value": part, "label": f"{label} ({role})", "kind": "interval",
                "source": source or self._last_source(),
                "present": part not in missing,
                "sentence": sentence_for(text, part) if part not in missing else "",
            })
        if missing:
            self._fail(f"{label}: interval incomplete, missing {missing} "
                       f"(printed as {parts[0]} [{parts[1]}-{parts[2]}])")

    def coherent(self, est, lo, hi, label: str, scale: str = "log",
                 p_value: float | None = None, tol: float = 0.08) -> None:
        """Is this statistic internally consistent with its own interval?

        Everything else here checks transcription: does the manuscript still say
        what the artifact says. This checks the artifact itself, which is a
        different failure and one the provenance gate will happily certify.

        A real instance: a validation study froze kappa 0.908 (0.869-0.945)
        alongside sensitivity 0.937 and specificity 0.884. Cohen's kappa cannot
        exceed 0.824 at any prevalence given those two, so the headline number was
        unreachable -- it was raw percent agreement in the kappa column. The number
        gate matched it to the CSV and reported it as the one defensible result.
        The gate was right and the answer was wrong.

        Three cheap tests catch a large share of that class: the estimate sits
        inside its interval, the interval is roughly symmetric about it on the
        stated scale, and any p-value agrees with the interval's implied standard
        error. None of them proves a statistic correct. They catch the partial
        update -- a point estimate changed while its interval and p were left
        behind -- which is the commonest way an artifact goes quietly wrong.

        Bootstrap percentile and profile-likelihood intervals are legitimately
        asymmetric, so raise `tol` for those rather than dropping the check; the
        p-value test is independent of the symmetry test and usually catches a
        partial update on its own.
        """
        import math
        est, lo, hi = float(est), float(lo), float(hi)
        problems = []

        if not (lo <= est <= hi):
            problems.append(f"estimate {est} lies outside [{lo}, {hi}]")
        elif scale == "log" and lo > 0 and hi > 0:
            centre = math.sqrt(lo * hi)
            if abs(math.log(est) - math.log(centre)) > tol:
                problems.append(
                    f"interval [{lo}, {hi}] is log-centred on {centre:.4g}, not {est}")
        else:
            centre = (lo + hi) / 2
            span = (hi - lo) or 1.0
            if abs(est - centre) / span > tol:
                problems.append(f"interval [{lo}, {hi}] is centred on {centre:.4g}, not {est}")

        if p_value is not None and lo > 0 and hi > 0 and scale == "log":
            se = (math.log(hi) - math.log(lo)) / 3.9199
            if se > 0:
                z = abs(math.log(est)) / se
                implied = math.erfc(z / math.sqrt(2))
                if implied > 0 and p_value > 0:
                    if abs(math.log10(implied) - math.log10(p_value)) > 0.5:
                        problems.append(
                            f"p={p_value} disagrees with the interval, which implies p≈{implied:.2g}")

        self.records.append({
            "value": f"{est} [{lo}, {hi}]", "label": f"coherence: {label}",
            "kind": "coherence", "source": self._last_source(),
            "present": not problems, "sentence": "; ".join(problems),
        })
        if problems:
            self._fail(f"{label} is not internally consistent: " + "; ".join(problems))

    def banned(self, text: str, value, reason: str) -> None:
        """A retired denominator that must not appear.

        Matching against the small set of numbers the study has carried and
        dropped is far more reliable than trying to parse every sentence for a
        count, because the sentence around a stale number usually changed too.
        """
        target = canon(value)
        flat = canon_text(text)
        hits = [m.start() for m in
                re.finditer(rf"(?<![\w.]){re.escape(target)}(?![\w.])", flat)]
        excused = [h for h in hits
                   if any(re.search(pat, flat[max(0, h - 120):h + 120])
                          for pat, _ in self.allows)]
        live = len(hits) - len(excused)
        self.records.append({
            "value": str(value), "label": f"banned: {reason}", "kind": "banned",
            "source": "-", "present": live == 0,
            "sentence": "" if live == 0 else sentence_for(text, value),
        })
        if live:
            self._fail(f"banned value {value} appears {live}x ({reason})")

    def allow(self, pattern: str, reason: str) -> None:
        """Exempt a legitimate reuse of a banned value, on the record.

        An exception that is written down is a decision; an exception that is
        silently skipped is a hole.
        """
        self.allows.append((pattern, reason))

    def figure(self, source: str, copy: str) -> None:
        """A figure in the manuscript still hashes to the pipeline's product.

        A figure in a manuscript is a copy, and copies go stale. This is the only
        check that catches a display whose numbers changed while its totals did
        not.
        """
        src, cpy = self.project / source, self.project / copy
        if not src.exists() or not cpy.exists():
            missing = source if not src.exists() else copy
            self.records.append({"value": "-", "label": f"figure {copy}",
                                 "kind": "figure", "source": source,
                                 "present": False, "sentence": f"missing {missing}"})
            self._fail(f"figure check: missing {missing}")
            return
        same = self._md5(src) == self._md5(cpy)
        self.records.append({"value": self._md5(src)[:8], "label": f"figure {copy}",
                             "kind": "figure", "source": source,
                             "present": same, "sentence": ""})
        if not same:
            self._fail(f"figure {copy} does not match {source} — the copy is stale")

    # -- internals -----------------------------------------------------------

    @staticmethod
    def _md5(path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _last_source(self) -> str:
        return sorted(self.sources)[-1] if self.sources else "-"

    def _fail(self, message: str) -> None:
        self.failures.append(message)
        if self.mode == "check":
            raise Drift(message)


# ---------------------------------------------------------------- driving it

def load_assertions(project: Path, module_path: Path):
    spec = importlib.util.spec_from_file_location("project_validator", module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(project))
    spec.loader.exec_module(module)
    if not hasattr(module, "assertions"):
        raise SystemExit(f"{module_path} defines no assertions(v, text) function")
    return module.assertions


def run(project: Path, manuscript: Path, validator_path: Path, mode: str) -> Validator:
    text = manuscript.read_text(errors="ignore")
    v = Validator(project, mode=mode)
    assertions = load_assertions(project, validator_path)
    if mode == "check":
        assertions(v, text)                       # raises on the first drift
    else:
        try:
            assertions(v, text)
        except Drift:
            pass                                  # recorded, not fatal, in record mode
    return v


def write_ledger(v: Validator, text: str, out_md: Path, out_csv: Path) -> tuple[int, int]:
    asserted = {canon(r["value"]) for r in v.records if r["kind"] != "figure"}
    printed = find_numbers(text)
    unasserted = [n for n in dict.fromkeys(printed) if n not in asserted]

    rows = []
    for r in v.records:
        rows.append({
            "value": r["value"],
            "checked_as": r["label"],
            "source": r["source"],
            "status": "asserted" if r["present"] else "FAILING",
            "sentence": r["sentence"],
        })
    for n in unasserted:
        rows.append({
            "value": n, "checked_as": "*not asserted*", "source": "-",
            "status": "unchecked", "sentence": sentence_for(text, n),
        })

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["value", "checked_as", "source", "status", "sentence"])
        w.writeheader()
        w.writerows(rows)

    n_asserted = len(v.records)
    n_printed = len(set(printed))
    md = [
        "# Claim ledger",
        "",
        f"The manuscript prints **{n_printed}** distinct numbers a reader could check. "
        f"The validator makes **{n_asserted}** assertions, each against the frozen "
        f"artifact the value came from, and fails the build when one does not hold.",
        "",
        "This file is a map, not a test. The validator is the test; what is printed "
        "here is the mapping it enforces, with the validator's own label for each "
        "check, so the correspondence can be read rather than taken on trust.",
        "",
        "A number listed as *not asserted* is one of three things: arithmetic the "
        "text does itself, a figure from a cited paper, or something nobody has "
        "checked. They look identical until someone looks, which is why they are "
        "listed rather than omitted.",
        "",
        "Regenerate with `python ledger.py ledger --project . --manuscript <file>`.",
        "",
        "## Frozen sources",
        "",
    ]
    md += [f"- `{s}`" for s in sorted(v.sources)] or ["- none declared"]
    md += ["", "## Mapping", "", "| Value | Checked as | Source | Status | Sentence |",
           "|---|---|---|---|---|"]
    for row in rows:
        sentence = row["sentence"].replace("|", "\\|")
        md.append(f"| {row['value']} | {row['checked_as']} | `{row['source']}` | "
                  f"{row['status']} | {sentence} |")

    if v.failures:
        md += ["", "## Failing assertions", ""]
        md += [f"- {f}" for f in v.failures]

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md) + "\n")
    return n_asserted, len(unasserted)


def main() -> int:
    ap = argparse.ArgumentParser(description="The number gate and its ledger.")
    ap.add_argument("mode", choices=["check", "ledger"])
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--manuscript", type=Path, required=True)
    ap.add_argument("--validator", type=Path, default=None,
                    help="default: <project>/analysis/validate_numbers.py")
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("--out-csv", type=Path, default=None)
    args = ap.parse_args()

    project = args.project.expanduser().resolve()
    manuscript = (project / args.manuscript if not args.manuscript.is_absolute()
                  else args.manuscript)
    validator = args.validator or (project / "analysis" / "validate_numbers.py")

    if not manuscript.exists():
        print(f"No manuscript at {manuscript}", file=sys.stderr)
        return 2
    if not validator.exists():
        print(f"No validator at {validator}. See the module docstring for its shape.",
              file=sys.stderr)
        return 2

    if args.mode == "check":
        try:
            v = run(project, manuscript, validator, "check")
        except Drift as exc:
            print(f"FAIL  {exc}", file=sys.stderr)
            return 1
        print(f"OK    {len(v.records)} assertions hold "
              f"against {len(v.sources)} frozen source(s).")
        return 0

    v = run(project, manuscript, validator, "record")
    out_md = args.out_md or (project / "submission" / "CLAIM_LEDGER.md")
    out_csv = args.out_csv or (project / "submission" / "claim_ledger.csv")
    n_asserted, n_unchecked = write_ledger(
        v, manuscript.read_text(errors="ignore"), out_md, out_csv)
    print(f"Wrote {out_md} and {out_csv}")
    print(f"  {n_asserted} assertions, {n_unchecked} printed numbers unasserted, "
          f"{len(v.failures)} failing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
