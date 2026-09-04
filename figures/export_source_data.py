"""Write one source-data CSV per figure, from the figure scripts themselves.

Each figure script carries its plotted values as module-level literals, so the
CSV emitted here is by construction the numbers the figure draws. Run it after
any change to a figure script:

    python figures/export_source_data.py

Every value written is an odds ratio, a confidence bound, a percentage, a test
statistic or a visit count. No participant counts are written, and none is
derivable from what is: see results/SCREENING.md.
"""

import csv
import os
import runpy

import matplotlib

matplotlib.use("Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "figures")


def write(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def run(script):
    return runpy.run_path(os.path.join(HERE, script), run_name="__export__")


def efigure5():
    ns = run("efig5_clinical_check.py")
    rows = []
    for series, d in (("All of Us", ns["A"]), ("MarketScan", ns["M"])):
        for lab, v in d.items():
            if v is None:
                rows.append([series, lab, "not captured in MarketScan", "", ""])
            else:
                rows.append([series, lab] + [f"{x:.3f}" for x in v])
    write("eFigure5_data.csv", ["cohort", "variable", "aor", "lo", "hi"], rows)


def figure1():
    ns = run("fig1_domain_vs_joint.py")
    rows = []
    for dom, levels in ns["GROUPS"]:
        for lab, ds, jt in levels:
            rows.append(
                [dom, lab] + [f"{x:.3f}" for x in ds] + [f"{x:.3f}" for x in jt]
            )
    write(
        "Figure1_data.csv",
        [
            "domain",
            "level",
            "domain_specific_aor",
            "domain_specific_lo",
            "domain_specific_hi",
            "joint_aor",
            "joint_lo",
            "joint_hi",
        ],
        rows,
    )


def figure4():
    ns = run("fig4_race_attenuation.py")
    rows = [
        ["a", lab, f"{v[0]:.3f}", f"{v[1]:.3f}", f"{v[2]:.3f}", ""]
        for lab, v, _c, _m in ns["SEQ"]
    ]
    rows += [["b", lab, "", "", "", f"{pct:.1f}"] for lab, pct in ns["DECOMP"]]
    rows.append(["b", "All five domains jointly", "", "", "", f"{ns['JOINT_PCT']:.1f}"])
    write(
        "Figure4_data.csv",
        ["panel", "model_or_domain", "black_race_aor", "lo", "hi", "attenuation_pct"],
        rows,
    )


def figure2():
    ns = run("fig2_era.py")
    waves = ns["WAVES"]
    rows = []
    for block, test, _verdict, _flag, levels in ns["GROUPS"]:
        for item in levels:
            lab, series = item[0], item[1:]
            for wave, v in zip(waves, series):
                rows.append(
                    [block, lab, wave]
                    + [f"{x:.3f}" for x in v]
                    + [" ".join(test.split())]
                )
    write(
        "Figure2_data.csv",
        ["block", "level", "wave", "aor", "lo", "hi", "omnibus_interaction"],
        rows,
    )


def figure3():
    ns = run("fig3_covid_vs_flu.py")
    rows = []
    for dom, lev, lab in ns["ORDER"]:
        for pathogen, r in ns["D"][(dom, lev)].items():
            rows.append([lab, pathogen, r["aor"], r["lo"], r["hi"], r["sig"]])
    write(
        "Figure3_data_panel_a.csv",
        ["level", "pathogen", "aor", "lo", "hi", "significant"],
        rows,
    )


def efigure2():
    ns = run("efig2_balance.py")
    rows = [
        ["All of Us", lab, f"{pre:.3f}", f"{post:.3f}"] for lab, pre, post in ns["AOU"]
    ]
    rows += [
        ["MarketScan", lab, f"{pre:.3f}", f"{post:.3f}"] for lab, pre, post in ns["MS"]
    ]
    write(
        "eFigure2_data.csv", ["cohort", "variable", "abs_smd_pre", "abs_smd_post"], rows
    )


def efigure3():
    ns = run("efig3_visits.py")
    rows = [[d, n, "yes" if 0 <= d <= 14 else "no"] for d, n in sorted(ns["N"].items())]
    write(
        "eFigure3_data.csv",
        ["days_from_index", "qualifying_visits", "counted_by_phenotype"],
        rows,
    )


if __name__ == "__main__":
    for fn in (figure1, figure2, figure3, figure4, efigure2, efigure3, efigure5):
        fn()
