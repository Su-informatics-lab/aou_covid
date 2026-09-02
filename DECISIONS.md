# Decisions

Append only. Numbered, dated, with the reason. Never edit an entry — the record
of what was replaced is most of the value. Supersede it with a new one.

---

## D1 — 2026-09-01 — Match on encounter density, not clinical severity

Patients with more health-system contact accumulate more recorded diagnoses, so
an SDoH association derived from EHR can be an artefact of differential
engagement rather than of social position. Matching on enrollment date,
diagnosis count and EHR length balances data availability directly.

Cost, accepted: diagnosis count may lie on the causal pathway, so the estimates
are conservative within-stratum associations rather than total effects. Stated
in Limitations.

## D2 — 2026-09-01 — Report domain-specific and joint models as complementary

An earlier draft implied the joint model superseded the domain-specific one. It
does not. The domain-specific estimate is the total association a domain
carries, which is the quantity a single-item screen would capture; the joint
estimate is what survives mutual adjustment. Both are reported for all six
domains, and Figure 4 shows them paired.

## D3 — 2026-09-01 — The profile contrast is an odds ratio, not a probability

`02_models.R` applied the inverse logit to a `clogit` linear predictor. That
predictor is centred on the covariate means and carries no intercept, so the
resulting 0.438 "baseline probability" was an artefact of the centring and the
1.31 "probability ratio" was compressed by the flatness of the logistic curve
near 0.5.

Replaced with the profile odds ratio — a linear combination of fitted
coefficients, so it also carries an exact delta-method interval. Point estimate
1.78 (= 1.33 × 1.18 × 1.13); the interval appears once the pipeline is re-run on
the Workbench. The Discussion argument that rested on 1.31 being "more modest
than multiplying separate AORs" was removed: 1.78 *is* that product. The
defensible comparison is joint 1.78 against domain-specific 2.79.

Supersedes the P0.4 block as written before this date.

## D4 — 2026-09-01 — Report the Delta wave

The temporal claim was built on two endpoints, 11.5% and 30.1%, while Figure 5b
printed a third annotation the text never mentioned. With Delta included the
series is 11.5% → 29.1% → 30.1%, and the Black-race base AOR is 3.00 → 2.98 →
1.65. The rise happens once, between pre-Delta and Delta, and the Delta interval
(1.79–4.96) makes the three attenuation values statistically indistinguishable.

All three waves are now reported in the Abstract, Results, Discussion,
Conclusions and both figure legends, with an explicit statement that no formal
test compared them.

## D5 — 2026-09-01 — State the income non-monotonicity in the Abstract

In the joint model $100,000–149,999 (1.24) and $150,000–199,999 (1.26) are
significant and larger than the lowest stratum (1.18). Writing "lower income" in
the Abstract while Table 3 shows this is a claim a reviewer falsifies by reading
one table. The Abstract and Conclusions now name the non-monotonicity.

Rejected alternative: leading with the collapsed <$35,000 result (S5, 1.16,
1.04–1.30), which is a clean low-income contrast. Rejected because it hides the
pattern rather than reporting it.

## D6 — 2026-09-01 — Table 2 blocks must partition the cohort

`04_tables.py::sdoh_section` counted the named levels and then `.isna()`, so any
value that was neither — an unmapped answer concept arriving as the literal
string "Missing" — was counted in no row. Housing tenure lost 1 case and 5
controls. Insurance, which passed "Missing" inside its level list, emitted the
row twice.

Missing is now defined as `~isin(levels)`, which captures NaN and unmapped
strings alike, and the function raises if a block does not sum to N. A silently
wrong table is worse than a failed build.

## D7 — 2026-09-01 — A number gate, and the ledger generated from it

Every defect found in the v18.5 audit was a transcription drift: the pipeline was
right and the document had fallen behind it. Nothing caught them because nothing
was checking.

`analysis/validate_numbers.py` asserts each printed number against the artifact
it came from and fails the build on drift; `analysis/gate.sh ledger` runs the
same assertions with the assertion replaced by a recorder and writes
`submission/CLAIM_LEDGER.md`, so the mapping is a byproduct of the test and the
two cannot disagree. Retired denominators go in `v.banned`, with legitimate
reuses recorded via `v.allow` rather than silently skipped.

## D8 — 2026-09-01 — 02c must verify its own outputs

`wave_stratified_race.csv`, `wave_stratified_insurance.csv` and
`wave_stratified_race_attenuation.csv` were declared by the script, absent from
the repository, and eTable 12b/12c depended on them — so those tables survived
only as hardcoded constants in `make_figures.py` and could not be reproduced
from the repository the Data Availability statement names.

`02c` now stops if any of the four wave outputs is missing.

**CLOSED 2026-09-02.** Not by re-running 02c. The four CSVs were still in the
Researcher Workbench 1.0 bucket, migrated intact to
`gs://rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7/`, and every value in
eTable 12b and 12c was read from them and matched to the printed precision. The
gap was never the bucket; nobody had pulled the outputs back into git. See
`reviews/2026-09-02_eTable12_VERIFIED.md`. What remains is committing the four
files, which is an export decision, not an analysis one.

## D9 — 2026-09-01 — One semantic colour grammar across all five figures

Navy = All of Us / joint / adjusted. Coral = domain-specific / base. Teal =
MarketScan. Grey + open marker = not significant. Wave uses one hue light to
dark because it is ordered. Significance is carried by fill as well as hue, so
the figures survive greyscale. Measured colourblind-safe (min ΔE 25.9 normal,
15.0 deuteranopia).

## D10 — 2026-09-02 — 这篇的贡献类型是 population signal

**背景。** D1–D9 全部是方法与报告决定；stage 3（Earn，"这篇买到了什么"）从未执行。
外包装同时在往两个方向走：`STUDY_DESIGN.md` 的 story arc 说的是 signal，而标题、摘要
两处和 Discussion 一节说的是 measurement。这篇没有做任何队列内的测量学比较，所以
measurement 那一侧没有证据。

**决定。** 贡献类型 = **reproducible population signal**：在一个富集了 underrepresented
人群的匹配队列里，六个自报社会域中哪些在互相调整后仍与 COVID-19 住院相关，哪些的表观
关联是与其他域共享的。

**不做。** 队列内 survey vs 结构化 EHR vs Z-code vs 区域指数的测量比较。它会是更强的
信息学贡献，但那是一个新分析，明确不在这篇的范围内。

**由此产生的措辞约束（已执行）。**
- 摘要不再声称 "survey linkage enabled measurement unavailable from structured EHR"，
  改为描述数据来源并归因到文献
- 摘要不再声称 "social risk dimensions health systems could screen for"；正文第 88 段
  本来就写着本设计不回答筛查决策问题，现在摘要与之一致
- 摘要不再出现 "respiratory-surge preparedness"

**仍待决定。** Discussion 小节标题 "The measurement case: why survey-linked EHR matters"
本身仍是一个 measurement 论断，建议改为 "Why the survey linkage was necessary"。

## D11 — 2026-09-02 — 波次差异要做正式的交互检验

**背景。** Introduction 问了三个问题，第三问（波次差异）在 Results 里被自己否掉
——"not compared formally"、"a hypothesis rather than a demonstrated trend"——却同时占着
Intro、摘要、Figure 5、Results 一节、Discussion 一节、Conclusions 六个位置。

**可行性（用现有的波次分层估计做的功效估算）。**

| 对比 | Δ log-AOR | SE | z | P |
|---|---|---|---|---|
| Black race，pre-Delta vs Omicron | 0.598 | 0.133 | **4.49** | **7e-06** |
| Black race，pre-Delta vs Delta | 0.007 | 0.272 | 0.02 | 0.98 |
| Income <$10k，pre-Delta vs Delta | 0.348 | 0.347 | 1.00 | 0.32 |
| Income <$10k，pre-Delta vs Omicron | 0.096 | 0.179 | 0.53 | 0.59 |

**结论：种族 × 波次有把握，收入 × 波次没有。** 而这两个结果都恰好支持稿子现在的说法
（种族关联收窄、收入关联持续），所以检验是在加固而不是推翻。

**做法。** `02d_wave_interaction.R`：单个合并模型加 `exposure:f.wave` 交互项，
主检验用 person_id 聚类稳健 Wald（与全文其他估计一致），LRT 仅作参考（它忽略对照复用）。
合并模型保留全部 strata，而波次分层模型会丢掉跨波的 stratum（Delta 只剩 301/644），
所以功效比上表估算的还高。

**约束。** 必须在修好 pre-index 泄漏之后跑；现在跑是在有偏的匹配集上做新检验。

## D12 — 2026-09-02 — WORKSPACE_BUCKET must be set explicitly before any re-run

Checked the environment variable inside a fresh AoU Jupyter app on Researcher
Workbench 2.0: `WORKSPACE_BUCKET` is **empty**.

Every upload block in this pipeline is guarded by `if (nchar(bucket) > 0)`, in
`01b_psm.R`, `02_models.R`, `02c_wave_stratified_race_insurance.R` and the new
`02d_wave_interaction.R`. An empty value therefore skips the upload **silently**
and the run's outputs live only on an ephemeral VM disk. That is one of the two
mechanisms that produced the eTable 12b/12c gap in the first place; the other is
that a bucket is not a repository.

Before any re-run:

    export WORKSPACE_BUCKET=gs://rw-migration-aou-rw-46c7ae9e

and after the run, pull the CSVs down and `git add` them. Do not treat "uploaded
to the bucket" as "saved".

Also recorded from the same session, because both were assumed and neither was
true: the workspace perimeter does **not** block github.com, pypi.org or
cloud.r-project.org (all returned 200), so `git clone` and CRAN installs work;
and a fresh clone lands on the default branch, where `notebooks/` does not
exist, so `git checkout review/v18.7-reconcile` is required.

## D13 — 2026-09-02 — 波次问题的报告方式：omnibus 与预先指定对比都要写

重跑后 `02d_wave_interaction.R` 的结果推翻了 D11 里我给的功效估计，也改变了波次故事该怎么讲。

| 交互 | df | Wald p |
|---|---|---|
| race × wave | 6 | 0.074 |
| income × wave | 14 | 0.218 |
| **insurance × wave** | 8 | **0.0027** |

**D11 的功效估计是错的。** 那里写的是 race × wave z≈4.5、p≈7e-06。错因：把三个**分别拟合**
的波次模型估计当独立样本做了 1 自由度差值检验，而实际跑的是 6 项联合 Wald；而且用的是
修复前的有泄漏估计。算术没错，算的不是那个检验。

**但那个 1 自由度对比本身是对的。** 合并模型给出的分波次 Black-race AOR 是
2.304 (2.011–2.641) / 2.239 (1.774–2.825) / 1.784 (1.520–2.093)，对比检验：

    pre-Delta vs Delta     AOR 之比 1.029   z=0.21   p=0.83
    pre-Delta vs Omicron   AOR 之比 1.292   z=2.39   p=0.017
    Delta     vs Omicron   AOR 之比 1.255   z=1.58   p=0.11

（保守：把两个估计当独立处理，真实 SE 更小。）

**这恰好就是稿子一直在说的那句话**——pre-Delta 到 Delta 没变，到 Omicron 收窄——
只是现在有检验了。6 自由度的 omnibus 不显著，是被 Asian 稀释的：Asian 的分波次估计
1.70 / 0.48 / 1.03，Delta 的 CI 宽到 0.14–1.65。

**决定。** 两个都报，不许挑：
1. omnibus race × wave，p = 0.074，不显著；
2. 预先指定的 Black-race pre-Delta vs Omicron 对比，p = 0.017，显著。
Introduction 问的本来就是第 2 个。只报其中一个都是选择性报告。

**收入。** income × wave p = 0.218。这不是"低收入关联消失了"，恰恰相反：稿子的说法是
"persisted"，而 persisted 的意思就是**没有**随波次变化。措辞要精确到位——不是"每一波都
显著"，而是"波次之间检不出差异"。

**保险。** insurance × wave p = 0.0027，是唯一通过检验的波次故事，而且和 eTable 12c 里
Medicaid 的 joint 估计在 Omicron 掉到 1.13 不显著自洽。这条此前没有被当作发现写出来。

## D14 — 2026-09-02 — 联合模型的叙述顺序要按新排序改

重跑后联合 SDoH 模型：

    失业        1.350 (1.198–1.521)   旧 1.23
    收入 <10k   1.211 (1.046–1.402)   旧 1.18
    收入 10–25k 1.205 (1.053–1.380)   旧 1.18
    Medicaid    1.193 (1.047–1.360)   旧 1.33
    租房        1.161 (1.054–1.279)   旧 1.13
    教育 <GED   1.060 (0.919–1.223)   p=0.42，仍不显著

方向和显著性全部保住，教育低于 GED 仍不显著——**核心论点毫发无损**。但排序变了：
**失业取代 Medicaid 成为最强的社会关联**，Medicaid 掉得最多。

Results 开篇的 "Medicaid coverage carried the largest insurance estimate" 与 Discussion
的叙述顺序都要按 失业 → 收入 → Medicaid ≈ 租房 重排。

顺带：`profile_odds_ratio_contrast.csv` 现在存在，组合对比是
**1.670 (1.403–1.988), p = 7.8e-09**（稿子印的是 1.78 且无区间）。D3 闭合。

## D15 — 2026-09-02 — 把种族衰减的分域分解写进稿子

`race_attenuation_table.csv` 一直有单域分解，从来没被用过。Black-race AOR 2.387 被各域
单独拉低的幅度：

    收入        11.7%        教育       4.8%
    住房         8.7%        就业       3.8%
    保险         6.2%        住房稳定性 0.1%
                             残疾       0.0%（七种口径全试过）
    六域联合    15.1%   （2.387 → 2.093）

**收入一个域吃掉总衰减的四分之三；残疾和住房稳定性一点贡献都没有。**

稿子现在只报总数 2.30→2.00。这张表信息量大得多，不需要任何新分析，而且直接回应
"哪些社会域真的承载了种族差异"这个问题。加进 eTable 12a 的正文叙述里。

## D16 — 2026-09-02 — CONSORT 计数必须从产物导出，且必须与 Table 1 对得上

重跑后 `consort_counts.csv` 说 **4,064 例 / 15,960 对照**，`table1_demographics.csv` 说
**3,997 / 15,523**。查到两个原因，都在 `05_figures.py`：

1. **六个整数是写死的**：`413457`、`25160`、`4064`、`21096`（AoU）与 `4423200`、`139489`
   （MarketScan）。它们在被敲进去的那天是对的，此后一直是对的——直到队列变了。
   `matched_observations` 更糟：`4064 + n_ctrl`，把一个写死的病例数和一个算出来的对照数相加。
2. **`n_ctrl` 取的是修剪之前的对照数**（`07b_control_reuse.csv` 的 `n_control_rows` = 15,960），
   而 Table 1 用的是模型真正拟合的那份（`08_regression_base.csv` = 15,523）。两个阶段混在了一起。

三个文件的真实关系：

    07_matched_cohort.csv    19,957 行 = 3,997 例 + 15,960 对照   MatchIt 的原始输出
    08_regression_base.csv   19,520 行 = 3,997 例 + 15,523 对照   模型实际拟合的
    table1_demographics.csv  3,997 / 15,523                       与后者一致 ✅
    consort_counts.csv       4,064 / 15,960                       两个阶段各取一半 ❌

**模型吃进去的是 `08_regression_base.csv`，所以论文的 N 就是 3,997 / 15,523。**
差额 15,960 − 15,523 = **437 个对照观测**因随访不足被剔除（旧稿是 388，队列变了）。

**已改。** `05_figures.py` 现在从 `01_covid_cohort.csv` 和 `08_regression_base.csv` 导出全部
计数，并额外输出 `cases_with_matching_vars`、`matched_strata`、
`control_observations_prematched`、`controls_dropped_followup`，让 Figure 1 能同时画出两个阶段。
只剩 `CDR_TOTAL_PARTICIPANTS = 413457` 一个常量——它是 CDR person 表的 COUNT，本地没有产物，
已加注释说明来源与何时必须更新。另加两条断言：severity 必须划分队列，strata 数必须等于病例数。

**gate 加了跨产物一致性检查**：`consort_counts.csv` 的 cases / control_observations /
matched_observations / matched_strata 必须与 Table 1 相符，不符即 fail。
两个文件各自内部自洽却互相矛盾，正是 v18.5 那个错换了张脸——旧的 gate 看不见它。

**`0.489` 进 banned 列表。** 它是修复前的诊断数 SMD，现在是 0.410。

**待你手改：Figure 1（draw.io）的排除框**从 388 改成 **437**，AoU 侧全部计数按新的
consort_counts 更新，`Enrollment date` 改成 `Survey date`。
