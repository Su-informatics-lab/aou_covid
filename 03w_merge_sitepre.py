"""03w_merge_sitepre.py -- replace the EHR-site rows of sens_r6.csv with the refit
that takes site from visits before the index date (R7; Codex R8 asked that this
step be code, not a hand edit).

03w_sens.R's full run (SPART=ALL) wrote sens_r6.csv when site still came from all
visits. SPART=SITEPRE refits only the site rows, with the pre-index site, and writes
sens_r6_sitepre.csv. This swaps them in. Both files are screened aggregates.

  python3 03w_merge_sitepre.py <sens_r6.csv> <sens_r6_sitepre.csv> <out.csv>
"""

import sys

import pandas as pd

full, sitepre, out = sys.argv[1:4]
a = pd.read_csv(full)
b = pd.read_csv(sitepre)
assert set(b.analysis) == {"site"}, set(b.analysis)
keep = a[a.analysis != "site"]
pos = a.index[a.analysis == "site"].min()
b = b.assign(note="EHR site before the index date")
m = pd.concat([keep.loc[: pos - 1], b, keep.loc[pos:]], ignore_index=True)
assert len(m) == len(a) - (a.analysis == "site").sum() + len(b)
m.to_csv(out, index=False)
print("site rows replaced:", len(b))
