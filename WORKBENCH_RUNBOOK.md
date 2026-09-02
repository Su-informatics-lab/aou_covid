# Workbench 重跑清单

**分支：** `review/v18.7-reconcile` · **写于** 2026-09-01
**为什么要跑：** `01_aou_etl.py` STEP 6 的匹配变量原来没有 index 日期限制，
`num_diagnosis` 和 `ehr_length_days` 把 index 之后的记录也数进去了。已在 `223f715` 修好，
一次没跑过。

按顺序做。每一步都写了「要看什么」——**看的比跑的重要**，因为这一轮的目的是确认修复生效，
不是拿到新数字就用。

---

## 0. 先探 bucket，可能省掉一整步（2 分钟）

```bash
gsutil ls $WORKSPACE_BUCKET/data/covid_sdoh/aou_v7/wave_stratified_*
gsutil ls $WORKSPACE_BUCKET/data/covid_sdoh/aou_v7/wave_joint_sdoh_*
```

`02c` 建文件那一版就带 `gsutil` 上传（我上一轮说它没有，是我核错了）。
如果这四个 CSV 还在 bucket 里，**eTable 12b/12c 的 UNVERIFIED 立刻可以闭合**，不用重跑：

```bash
gsutil -m cp $WORKSPACE_BUCKET/data/covid_sdoh/aou_v7/wave_stratified_*.csv results/aou_v7/
```

拉下来后先对一遍：`wave_stratified_race_attenuation.csv` 里的 11.5 / 29.1 / 30.1
和 strata 数 1913 / 301 / 1105 要和 eTable 12b 对得上。对得上就 `git add`。

**注意：** 这是旧匹配集的产物，闭合的是「可溯源」，不是「已更新」。第 4 步重跑后要再来一次。

---

## 1. 单独验证修好的匹配变量查询（跑全链之前）

不要直接 `python 01_aou_etl.py v7`。先把 STEP 6 的 `match_sql` 单独跑一次：

```python
# 在 notebook 里，从 01_aou_etl.py 复制 STEP 6 的 match_sql
mv = pd.read_gbq(match_sql, dialect="standard")
print(len(mv), mv.person_id.nunique())
print(mv[["num_diagnosis", "ehr_length_days"]].describe())
```

**要看什么：**

| 检查 | 期望 |
|---|---|
| 行数 / person_id 唯一数 | 相等（每人一行） |
| 与 `covid_cohort.person_id` 的交集 | 应覆盖绝大多数；差太多说明 `covid_idx` CTE 的 join 有问题 |
| `num_diagnosis` 中位数 | **明显低于旧值**（旧的病例中位数 114）。如果没降，说明 `CASE WHEN ... < i.covid_index_date` 没生效 |
| `num_diagnosis` 是否出现 0 | 会出现。index 之前没有任何诊断的人，旧版被 index 后的码顶上去了 |
| `ehr_length_days` 是否出现 NaN | 会出现（index 前只有一条或没有 condition 记录时 `DATE_DIFF` 为 NULL）。**下一步 `dropna` 会把这些人剔掉，要记下剔掉多少** |

最后一条是这次修复最可能带来的意外：**队列会缩小**。缩多少必须记录，因为 Figure 1 的
flowchart 和 Table 1 的 N 都要跟着改。

---

## 2. AoU 全链

```bash
python  01_aou_etl.py v7                 # ← STEP 6 已改；注意 06_matching_variables.csv 现在是 survey_ord
Rscript 01b_psm.R aou_v7                 # ← MATCH_COVS 已改为 survey_ord
Rscript 02_models.R aou_v7
Rscript 02b_variance_sensitivity.R aou_v7
Rscript 02c_wave_stratified_race_insurance.R aou_v7
python  01c_sensitivity_etl.py v7
Rscript 03_sensitivity.R aou_v7
python  04_tables.py aou_v7
```

**列名这一轮改过。** `enrollment_ord` → `survey_ord`（只有 AoU；MarketScan 那边确实是首次
参保日期，名字没错）。同步改了 `01_aou_etl.py:1430`、`01b_psm.R:88`、`05b_love.R`、
`README.md`。改之前 `01_aou_etl.py` 会在最后一步 `KeyError: 'enrollment_ord'` 直接崩——
上一轮只改了一半。

**每一步之后要看什么：**

- `01b_psm.R`：`07c_smd_pre_matching.csv` 里 `num_diagnosis` 的 SMD。旧值 **0.489**。
  修复后应该**变小**（index 后的码是病例独有的，去掉后两组更接近）。若仍在 0.48 上下，
  停下来查 SQL。
- `01b_psm.R`：匹配到的对照数 / 每例。旧值 3.90。
- `02_models.R`：**chronic pulmonary（旧 0.85）和 mild liver（旧 0.76）**。稿子现在把这两个
  反向估计解释成「匹配平衡的是就诊密度而非临床严重度的正常后果」。如果它们现在转向 1 或
  转正，**那段解释必须删掉**，泄漏才是原因。
- `02_models.R`：确认写出了 `profile_odds_ratio_contrast.csv`。正文里 1.78 至今没有区间。
- `02c`：脚本现在缺任一输出即 `stop()`。跑完把四个 CSV **拉回本地 `git add`**——
  bucket 里有不等于仓库里有，这正是上次的缺口。
- `04_tables.py`：Table 2 住房 Missing 应为 **170 例 / 576 对照**（旧稿是 169 / 571）。
  脚本现在若不满足划分会直接报错。

---

## 3. MarketScan（在 Quartz HPC，不在 Workbench）

```bash
python  01_ms_etl.py                     # coverage_span_days 已截断至 index
Rscript 01b_psm.R ms
Rscript 02_models.R ms
python  04_tables.py ms
```

MS 的 `num_diagnosis` 没改——`dx_long` 建表时就带 `WHERE d.dx_date < c.covid_index_date`，
本来就是 pre-index，代码里加了注释记录已查。只有 `coverage_span_days` 变了，
保险到期日受住院影响小，预计 Table 1 的 MS 列变化轻微。

---

## 4. 图与补充材料

```bash
python 05_figures.py
python 06_supplement.py
python make_figures.py                   # Figures 3–5（NPG）
Rscript 05b_love.R                       # eFigure 1；标签现在是 "Basics Survey date (ordinal)"
```

**不要重画 Figure 1 和 Figure 2。** 那两张是 draw.io 原图，按你的要求保留。
但 Figure 1 里有两处要你在 draw.io 里手改：

1. AoU 那一栏写着 `enrollment date · diagnosis count · EHR length`，
   **第一项应为 `survey date`**（MarketScan 那栏的 `enrollment date` 是对的，不用改）。
2. 缺 `388 controls excluded`（随访不足）那个框；legend 里写了，图上没有。

第 1 步如果队列缩小了，Figure 1 的所有计数也要改。

---

## 5. 回写与提交

```bash
gsutil -m cp $WORKSPACE_BUCKET/data/covid_sdoh/aou_v7/*.csv results/aou_v7/
git add results/ && git commit -m "data: re-run with pre-index matching variables"
```

---

## 6. 更新断言（最后一步，也是最容易做错的一步）

```bash
bash analysis/gate.sh check
```

**它会大面积失败，这是对的。** 逐条把 `analysis/validate_numbers.py` 里的断言更新为新结果。

**方向不能反。** 断言是用来发现稿子和产物不一致的；发现不一致时改的是稿子，不是断言的
容差。唯一该改断言的情形是产物本身变了（这次就是），那就把断言指向新产物的新值。

`RETIRED DENOMINATORS` 那一段（`v.banned`）要加新条目：这一轮所有被替换掉的旧数字
——4,064、15,856、0.489、2.30、2.00 等等——如果重跑后变了，旧值要进 banned 列表，
否则下次从旧文件重建稿子时不会有人发现。

跑完生成新的 ledger：

```bash
bash analysis/gate.sh ledger
```

---

## 重跑之后才能定的三件事

1. **chronic pulmonary / mild liver 是否仍反向。** 若转正，删掉 Discussion 里那段解释。
2. **S3（pre-index 调查）与全样本的差距。** 若 S3 仍不显著，主分析用哪个要重新决定。
3. **波次故事留正文还是进 supplement。** 取决于交互检验做不做、结果如何。

这三件都不要现在改措辞，改了要改两遍。
