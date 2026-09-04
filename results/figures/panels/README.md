# Main-text figure panels

Every main-text figure is assembled from files in this directory: a design
strip on top, then the panels that carry that figure's data. Each panel is a
separate PDF (submission) and PNG (drafting) so the figures can be laid out by
hand without re-running anything.

## The strip

`design_strip.py` draws one picture in five states. The three zones are always
the same — who is compared with whom, what they are matched on, and the model —
so a reader meets the design once, in Figure 1, and thereafter only has to find
the warm patch to know what the figure below is varying.

| Strip | Warm zone | What it says varies |
|---|---|---|
| `strip_F1_design` | none | nothing; this is the design itself |
| `strip_F2_domains` | model | all five domains together, or one at a time |
| `strip_F3_eras` | model | the same model, fitted era by era |
| `strip_F4_pathogen` | cohort | the same design, a second pathogen |
| `strip_F5_race` | model | what the domains absorb of race |

Where the wash sits is itself informative: zone A means the **cohort** changed,
zone C means the **model** changed. Within zone C the element that changed is
also warm — the five domains in Figure 2, the word *race* in Figure 5. Ordered
time keeps the cool era ramp in Figure 3, because that ramp is the same
vocabulary the data panel below uses.

## The assembly

| Figure | Panel (a) | Panel (b) | Panel (c) | Argument |
|---|---|---|---|---|
| 1 | `strip_F1_design` | `F1b_balance` | `F1c_concordance` | the design, that the matching worked, and that the clinical model behaves |
| 2 | `strip_F2_domains` | `F2b_domain_vs_joint` | — | Test 1 |
| 3 | `strip_F3_eras` | `F3b_eras` | — | Test 2 |
| 4 | `strip_F4_pathogen` | `F4b_covid_vs_flu` | — | Test 3 |
| 5 | `strip_F5_race` | `F5b_race_attenuation` | — | Test 4 |

`F4b` and `F5b` carry their own internal `b` / `c` letters, because each is two
side-by-side panels. `F2b` and `F3b` are single panels and carry no letter;
add `b` when assembling.

Strips are 180 × 62 mm. Data panels are drawn at the width they should be
placed at; do not scale them, or the type will no longer be 10 pt.

## Regenerating

```
python figures/design_strip.py          # the five strips
python figures/fig1_panels.py           # F1b, F1c  (and eFigure 5)
python figures/fig1_domain_vs_joint.py  # F2b
python figures/fig2_era.py              # F3b
python figures/fig3_covid_vs_flu.py     # F4b
python figures/fig4_race_attenuation.py # F5b
python figures/export_source_data.py    # Figure1_data.csv … Figure5_data.csv
```

`design_strip.py` measures every string it draws and fails loudly if one leaves
its zone, so the strip cannot silently overflow when a word is changed. All
type is 10 pt or larger, which is the OUP floor the rest of the set observes.

Source data for each figure is one directory up, named for the figure it
belongs to. No participant counts appear in any of it; see
`results/SCREENING.md`.
