# Session state

**Updated:** 2026-09-01 · **Branch:** `review/v18.7-reconcile` · **Stage:** 6 → 7
**Next action:** internal review of the branch, then re-run `02c` on the Workbench.

---

## Where the project is

Stages 1–5 were done long ago; stage 8 was being attempted. **Stage 6 had never
been done**, and that is the whole story of this round: `orient.py` found no
frozen run, no claim ledger and no gate script, and the v18.5 audit then found
the manuscript disagreeing with this repository in 29 cells of Table 1, in every
pre-matching SMD, and in eTable 14 — where a P of 0.068 was printed as 0.03.

None of those were analysis errors. All were transcription drift, and a
five-line assertion would have caught each one. That gate now exists.

## Done this round

**Code (3 real faults, all fixed on this branch)**

| File | Fault | Fix |
|---|---|---|
| `02_models.R` | inverse logit applied to a centred `clogit` linear predictor; "1.31-fold predicted probability" was not a probability | profile odds ratio with a delta-method interval; writes `profile_odds_ratio_contrast.csv` |
| `04_tables.py` | `sdoh_section` counted named levels + `.isna()`, dropping unmapped values; insurance emitted `Missing` twice | Missing is `~isin(levels)`; the block now raises unless it partitions the cohort |
| `02c_…R` | declared three outputs, wrote none that reached the repo | stops if any of the four wave outputs is missing |

**Gate (stage 6)** — `analysis/{ledger.py, validate_numbers.py, gate.sh}`.
Runs green: **117 assertions against 8 frozen sources, 0 failing.**
`submission/CLAIM_LEDGER.md` is generated from the same assertions.

**Documents** — manuscript and supplement corrected against the repository;
five figures redrawn on one semantic colour grammar; JAMIA submission package
assembled. See `V18.6_changelog.md` and `submission/`.

## Open, in priority order

1. **eTable 12b / 12c are UNVERIFIED.** Re-run `Rscript
   02c_wave_stratified_race_insurance.R aou_v7` on the Workbench, commit the
   four `wave_stratified_*.csv`, then add their assertions to
   `validate_numbers.py` (a placeholder comment marks the spot). Until then the
   Delta-wave numbers trace only to constants in `make_figures.py`.
2. **Re-run `02_models.R`** for `profile_odds_ratio_contrast.csv`, then put the
   interval into the Results sentence that currently gives 1.78 bare.
3. **Re-run `04_tables.py`** and re-paste Table 2. Housing tenure Missing goes
   169 → 170 (cases) and 571 → 576 (controls); insurance loses its duplicate row.
4. **`Background and Significance` section is missing.** JAMIA requires it for
   Research and Applications. Desk-reject risk. ~250–350 words, most liftable
   from the second half of the Introduction.
5. **Length.** Main text 5,506 against 4,000; abstract 315 against 250.
6. **Table 1 is 49 rows**; JAMIA moves tables over two pages online-only. Split
   it or accept that.
7. Reference author counts (15 refs list 4–6; JAMIA wants 3 then et al.);
   refs 35 and 45 are preprints cited with inconsistent years.

## How to run the gate

```bash
bash analysis/gate.sh check     # fails on the first drift
bash analysis/gate.sh ledger    # regenerates submission/CLAIM_LEDGER.md
```

Both documents are flattened together, because a number in eTable 10 must trace
to the same artifact as the same number in Table 1. Put `check` in CI before the
next submission.

## What the gate does not do

It proves the manuscript still says what the artifact says. It does **not** prove
the artifact is right. The direction check between Table 1 crude rates and
eTable 10 odds ratios is the one coherence test written so far; more are worth
adding, especially for any statistic derived from other reported statistics.

---

# 2026-09-01 追加：Zhang 内审 — 匹配变量存在 pre-index 泄漏（BLOCKING）

内审第一条成立，而且比本轮之前发现的任何问题都严重。**结论：这个分支不能投，必须重跑。**

`01_aou_etl.py` STEP 6 的匹配变量在 2026-09-01 之前没有任何 index-date 限制：

- `num_diagnosis` = `COUNT(DISTINCT condition_concept_id)`，含 index 之后的诊断
- `ehr_length_days` = `MAX(condition_start_date) − MIN(...)`，跨越 index
- `enrollment_ord` 实为首次 Basics Survey 日期，稿子却写成 "All of Us enrollment date"

决定性对照：**同一文件第 1019 行，Charlson 写着 `co.condition_start_date < e.covid_index_date`。**
团队知道要做 pre-index 限制，匹配变量这里漏了。这是 bug，不是设计选择。

后果不是抽象的。`num_diagnosis` 是倾向评分里最强的变量（pre-match SMD 0.489）。
住院病例在住院期间产生大量诊断码，所以匹配部分地匹配在结局的产物上 —— 正是
encounter-density 设计要防的那个偏倚。对照被选成"诊断码一样多但没住院"的人，
也就是本身病得更重的人。这很可能就是 chronic pulmonary 0.85、mild liver 0.76
这些反向估计的真正来源；稿子目前把它们解释为匹配策略的正常后果，那个解释可能是错的。

## 逐条核实（不是全部成立）

| 指控 | 结论 | 处理 |
|---|---|---|
| AoU `num_diagnosis` 含 post-index | **成立** | 已加 `CASE WHEN condition_start_date < covid_index_date` |
| AoU `ehr_length_days` 含 post-index | **成立** | 同上 |
| AoU `enrollment_ord` 命名错误 | **成立** | 改名 `survey_ord`；稿子措辞待改 |
| MS `num_diagnosis` 含 post-index | **不成立** | `dx_long` 建表时已 `WHERE dx_date < covid_index_date`，未改动 |
| MS `coverage_span_days` 含 post-index | 技术成立 | 已截断至 index；保险覆盖结束日受住院影响小，预计影响轻微 |

## 这些改动没有被执行过

BigQuery 和 MarketScan 都不在这台机器上。SQL 改成了复用 `charlson_sql` 里
已验证的 `covid_idx` CTE，Python 语法通过，但**整段没有跑过**。
在 Workbench 上先单独验证 `match_vars` 查询返回的行数与 `covid_cohort` 一致，
再往下走。

## 重跑顺序

1. `python 01_aou_etl.py <version>` 并核对 `06_matching_variables.csv` 的
   `num_diagnosis` 分布是否明显下降（应该会）
2. `python 01_ms_etl.py`
3. `Rscript 01b_psm.R aou_<version>` — 匹配集会变，SMD 会变
4. `Rscript 02_models.R` / `02b` / `02c` / `03_sensitivity.R`
5. `python 04_tables.py` / `06_supplement.py`
6. `python make_figures.py`
7. `bash analysis/gate.sh check` — **会大面积失败，这是预期的**。逐条把
   `validate_numbers.py` 里的期望值更新为新结果，不要反过来改结果去迁就断言。

重跑之前，稿子里所有效应量都应视为过时。

---

## 2026-09-02 — Workbench 2.0 上的重跑（进行中）

### 环境

| | |
|---|---|
| Workspace | `AUD_MH_Genomics_v7_v2` / `aou-rw-46c7ae9e`（COVID 分析当年就跑在这里，不是独立 workspace） |
| GCP 项目 | `wb-gleaming-coffee-3314` |
| CDR | `C2022Q4R13`（cdrv7，version-bound）— 与 `STUDY_DESIGN.md` 一致，`COHORT=aou_v7` |
| App | `AoU_Jupyter_ComputeEngine_20260901`，n1-highmem-4，100 GB 盘，$0.24/hr，闲置 4h 自动停 |
| 代码 | `~/covid/repo`，分支 `review/v18.7-reconcile` |
| 日志 | `~/covid/run.log` |
| 旧产物 | `gs://rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7/` |
| **备份** | `gs://rw-migration-aou-rw-46c7ae9e/backup_20260902/`（86 文件 / 31 MB，重跑前所有产物） |

### 已完成

- **eTable 12b/12c 核实完毕**，12 个值逐位对上，D8 关闭。见
  `reviews/2026-09-02_eTable12_VERIFIED.md`。
- 备份完成，重跑可逆。
- 管线已启动（`nohup`，后台）：
  `01_aou_etl` → `01b_psm` → `02_models` → `02b` → `02c` → `02d` → `01c` → `03` → `04_tables`
- `01_aou_etl.py` 已跑完；`01b_psm.R` 正在装 MatchIt（从源码编译）。

### 下一个人（或下一次会话）要看的三件事

按顺序，任一不过就停下：

1. **队列规模**
   `grep -E "Complete matching|Cases with matching" ~/covid/run.log`
   修复后 `ehr_length_days` 会出现 NA（index 之前没有诊断记录的人），`dropna` 会剔掉他们。
   剔了多少必须记下来 —— Figure 1 的流程图和 Table 1 的 N 都要跟着改。旧值：cases 4,064。

2. **泄漏是否真的修好了**（最关键）
   `head -5 ~/covid/repo/results/aou_v7/07c_smd_pre_matching.csv`
   `num_diagnosis` 的 pre-match SMD **旧值 0.489，必须明显变小**。没变 = `CASE WHEN` 没生效，
   后面全部作废。

3. **反向估计是否翻转**
   `grep -E "Pulmonary|Liver_Disease_Mild" ~/covid/repo/results/aou_v7/base_model_coefficients.csv`
   旧值 chronic pulmonary 0.85、mild liver 0.76。若转向 1 或转正，Discussion 里把它们解释成
   "encounter-density 匹配的正常后果" 那一段**必须删掉** —— 泄漏才是原因。

### 跑完之后

- `wave_interaction_tests.csv` / `wave_interaction_contrasts.csv`（D11 的交互检验，新增）
- `profile_odds_ratio_contrast.csv` —— 正文里 1.78 至今没有区间
- 把 `results/` 拉回本地 `git add`。**桶不是仓库**，这正是 eTable 12b 当初丢失的机制。
- `bash analysis/gate.sh check` 会大面积失败，这是对的：逐条把断言更新为新产物，
  绝不反过来改结果迁就断言。

### 已知的环境坑（见 D12）

- `WORKSPACE_BUCKET` 在新 app 里默认为空，会让所有 `gsutil` 上传静默跳过。本次已显式
  `export WORKSPACE_BUCKET=gs://rw-migration-aou-rw-46c7ae9e`。
- perimeter 不挡 github / PyPI / CRAN（均 200）。
- 新 clone 落在默认分支，`notebooks/` 只在 `review/v18.7-reconcile` 上。
