# eTable 12b / 12c 取证：这些数字从哪来，能不能信

**日期：** 2026-09-01 · **分支：** `review/v18.7-reconcile` · **结论：可信，但不可溯源，必须重跑**

---

## 一、文件确实没了，而且是三重丢失

| 检查 | 结果 |
|---|---|
| `wave_stratified_race.csv` 在 git 全部历史中被加入过几次 | **0** |
| `wave_stratified_insurance.csv` | **0** |
| `wave_stratified_race_attenuation.csv` | **0** |
| `wave_joint_sdoh_*_coefficients.csv` | **0** |
| 本地磁盘上是否存在 | 否，`results/aou_v7/` 下只有 `wave_stratified_income.csv` |
| 是否有 R 运行日志（`.Rout` / `.log` / `nohup.out` / `.Rhistory`） | 无 |
| `02c` 是否把输出同步到 Workspace bucket | **否**。`gsutil` 只出现在 `01b_psm.R` 和 `02_models.R`，`02c` 没有 |

第三条是致命的一条。`01b` 和 `02` 都会 `gsutil cp` 到 `WORKSPACE_BUCKET`，`02c` 不会。Workbench 的虚拟机是临时的，所以这四个文件只在当时那台机器的本地磁盘上活过一次。

## 二、更严重的一层：eTable 12b/12c 根本没有生成脚本

`06_supplement.py` 只用 `race_attenuation_table.csv` 生成 **eTable_S12**（整体衰减表）。全文没有任何生成 12b 或 12c 的代码。

也就是说这两张表是**手工做的**。它们的数字目前唯一的存放处，是 `make_figures.py` 里的常量 `RACE_WAVE` 和 `INCOME_WAVE` —— 而 `make_figures.py` 在本次提交之前从未被 git 跟踪。

## 三、但数字本身经得起检验

文件丢了不等于数字是编的。三项独立检验：

**1. 衰减百分比与 AOR 精确吻合**

| 波次 | 表中声称 | 按 `1 − ln(joint)/ln(base)` 重算 | 差 |
|---|---|---|---|
| Pre-Delta | 11.5% | 11.63% | +0.14 pp |
| Delta | 29.1% | 29.05% | −0.05 pp |
| Omicron | 30.1% | 29.97% | −0.12 pp |

三个差值都在取整误差内，且符号不一致（一正两负），符合"用未取整系数算完再取整"的特征。若是编造，很难同时满足三个波次。

**2. 置信区间在对数尺度上高度对称**

| 波次 | base 偏离中心 | joint 偏离中心 |
|---|---|---|
| Pre-Delta | 0.0008 | 0.0007 |
| Delta | 0.0001 | 0.0002 |
| Omicron | 0.0004 | 0.0029 |

这是 Wald 区间 `exp(β ± 1.96·SE)` 的指纹。手填的数字不会有这种对称性。

**3. 标准误与 strata 数的关系吻合**

以 pre-Delta 为基准，SE 应按 `1/√n` 缩放：

| 波次 | N strata | 实测 SE | 按 1/√n 预测 | 比值 |
|---|---|---|---|---|
| Pre-Delta | 1,913 | 0.0805 | 0.0805 | 1.00 |
| **Omicron** | **1,105** | **0.1060** | **0.1059** | **1.00** |
| Delta | 301 | 0.2600 | 0.2030 | 1.28 |

Omicron 吻合到小数点后三位。Delta 偏大 1.28 倍是合理的：该波 Black race 的病例数更少，信息量比单纯的 strata 计数更低。

**反证更有力：** 如果模型真的用了 644 例（N cases 那一列），Delta 的 SE 应该是 **0.139**，实测是 **0.260**，差 **1.87 倍**。这从数据侧独立证明了模型实际只用了约 301 个 strata。

## 四、代码验证了我写进稿子的机制

`02c_wave_stratified_race_insurance.R` 第 185–201 行：

```r
df_w <- reg_sdoh[reg_sdoh$pandemic_wave == w, ]        # 逐行按波次过滤
strata_ok <- df_w %>% group_by(stratum) %>%
  summarise(has_case = any(Treatment == 1),
            has_ctrl = any(Treatment == 0), .groups = "drop") %>%
  filter(has_case & has_ctrl) %>% pull(stratum)         # 丢弃缺 case 或缺 control 的 stratum
```

过滤是**逐观测行**的，不是按 case 的波次。所以一个 case 在 Delta、但四个 control 的 index date 落在 pre-Delta 的 stratum，会因为 `has_ctrl == FALSE` 被整个丢掉。Delta 是最短的一个波（六个月），control 更容易落在别的波，所以它损失最重——**644 例中只有 301 个 stratum 进模型（46.7%）**。

我在 v18.6 里写进 Results 的那句解释因此是正确的，代码可以佐证。

## 五、由此发现的一个新问题

**eTable 12b 和 12c 的 "N cases" 列有误导性。** 代码里 `n_cases_w` 是 stratum 过滤**之前**的波内病例数（2,087 / 644 / 1,333），而 "N strata" 是过滤**之后**的（1,913 / 301 / 1,105）。两列并排放，读者会以为 Delta 模型用了 644 例，实际只有 301 例。

**建议：** 把表头改成 `N cases in wave` 和 `N strata in model`，并加脚注说明模型样本量是后者。正文我已经写清楚了，但表还没改。

## 六、结论与待办

- 数字**可信**：三项独立检验都通过，且与代码逻辑自洽。不是编造，也不是串号。
- 数字**不可溯源**：没有任何committed artifact 支持它们。Data Availability 指向的仓库里，这两张表无法复现。
- 因此 eTable 12b/12c 在 `analysis/validate_numbers.py` 里仍标为 **UNVERIFIED**，`RUN.json` 的 `unverified` 字段也记着。

**闭合它需要在 Workbench 上做三件事：**

1. `Rscript 02c_wave_stratified_race_insurance.R aou_v7`
   （脚本现在缺任一输出就 `stop()`，不会再静默产生这个缺口）
2. 提交四个 `wave_stratified_*.csv`
3. 把断言补进 `validate_numbers.py` —— 文件末尾的注释标了位置

顺带把 `02c` 加进 `gsutil` 同步列表，和 `01b`、`02` 一致，否则下次仍然只活在临时机器上。
