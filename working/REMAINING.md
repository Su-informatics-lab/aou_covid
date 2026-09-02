# 稿子还欠什么

**工作稿：** `working/ms_v191_rerun_WORKING.docx` · 2026-09-02
**提交版 `submission/02_manuscript.docx` 没有动过** —— 它整篇是 v18.6，内部一致。
工作稿是新旧混合的，每一处旧数字都打了 `[STALE ...]`，**搜 "STALE" 就能全找到（16 处）**。

---

## 已经改完的（全部基于重跑后核实过的产物）

| 位置 | 内容 |
|---|---|
| 摘要 | 全部重写，250/250 词。故事换成：失业最强、四个域保住、种族衰减 15.1% 里收入占 11.7、保险×波次显著而种族/收入不显著、种族的预先指定对比 P=0.017 |
| Results 参与者 | 3,997 / 15,523 / 19,520 / 3,997 strata / 剔除 437 / 3.88 每例 / SMD 0.410 |
| Results 基础模型 | 女性 0.77、疫苗 0.43、65+ 1.51、Black 2.39；**pulmonary 0.90 / mild liver 0.83 那段改写了**——泄漏占约三分之一，剩下的是匹配设计，两条都写出来 |
| Results 联合模型 | 按新排序重写：失业 1.35 → 收入 1.21/1.21 → Medicaid 1.19 → 租房 1.16；教育 1.06 不显著。并写明**排序对倾向模型的设定不稳健，但"哪些域仍相关"是稳健的** |
| Results 种族衰减 | 2.39→2.09，15.1%，**加上分域分解**（收入 11.7、住房 8.7、保险 6.2、教育 4.8、就业 3.8、住房稳定 0.1、残疾 0.0） |
| Results profile | 1.67 (1.40–1.99)，**终于有区间** |
| Results 波次 | 整段重写：合并交互模型、omnibus P=0.07 被 Asian 稀释、预先指定对比 P=0.017、pre-Delta→Delta P=0.83、保险×波次 P=0.003 |
| Discussion 四处 | 按新排序与新检验重写；temporal shift 那段从"假设"改成有检验支撑的陈述 |
| Limitations | 加了"67 例因无 index 前诊断记录无法匹配，其排除本身可能与社会位置相关" |
| Figure 1 / 3 / 5 图注 | 新计数、437、n=19,520、波次估计与检验 |
| Table 2 caption | 3,997 / 15,523 |

---

## 还欠的，按阻断程度排序

### 1. MarketScan 整个没有重跑 —— 最大的一块

它在 **Quartz HPC** 上，不在 Workbench。`01_ms_etl.py` 里把 `coverage_span_days`
截断到 index 之前的修复**一次没跑过**。

受影响：Table 1 的整个 MarketScan 列、Figure 3 的 teal 系列、eTable 8/9/10/14、
Results 的 cross-cohort 一段、Discussion 的 cross-cohort 一段、Figure 1 的 (b) 面板。

```bash
python  01_ms_etl.py
Rscript 01b_psm.R ms
Rscript 02_models.R ms
python  04_tables.py ms
```

### 2. 需要从已有产物里再读出来的（不用重跑，只是我没读）

这些文件已经在 Workbench 上生成好了，只是当时没打印：

| 缺什么 | 在哪个文件 |
|---|---|
| 波次与各 comorbidity 的 base-model 估计 | `base_model_coefficients.csv` |
| 单域 SDoH 全部取值（Table 3 第一列、2.79 那个乘积） | `insurance_/income_/education_/employment_/housing_*_coefficients.csv` |
| 联合模型剩下的水平（student、non-employment、上中收入两档、disability、housing other） | `joint_sdoh_coefficients.csv` |
| 五项敏感性分析 | `sensitivity_S1..S5_*_coefficients.csv`、`eTable_S16_sensitivity.csv` |
| 分波次收入（eTable 13） | `eTable_S13_wave_income.csv` |
| 分波次种族衰减百分比、Medicaid 分波次（eTable 12b/12c） | `wave_stratified_*.csv`（已重跑覆盖） |
| 对照唯一人数、最大复用、有效样本量 | `07b_control_reuse.csv`、`07e_matchit_summary.txt` |
| 收入缺失的差异比例、Omicron 收敛警告 | `table2_sdoh.csv`、`02_models.R` 日志 |

**取的方式：在平台上打印，读出来。** 不要打包下载 —— 每一个值出平台前都要过 <20 检查
（`education_coefficients.csv` 里 "never attended school" 一档就是不足 20 人的）。

### 3. Table 1 / 2 / 3 与全部 eTable

CSV 都已生成，但**没有一张被贴回 docx**。稿子里的三张表和补充材料里的 16 张 eTable
全部是 v18.6。

### 4. 图

`results/figures/` 里 Figure3/4/5 已按新数据重画。**Figure1 和 Figure2 不要用脚本版**，
那是 draw.io 原图。你手改的两处：
- AoU 侧排除框 **437**（不是 388）
- 匹配框第一项 `Enrollment date` → `Survey date`
- AoU 侧全部计数按 `consort_counts.csv`：25,160 → 4,064 / 21,096；3,997 有完整匹配变量；
  19,520 观测 / 3,997 strata / 15,523 对照

### 5. 最后才跑 gate

`bash analysis/gate.sh check` —— 等上面都齐了再跑，一次。
它现在跑只会告诉我们"稿子还没改完"，那个我们已经知道。
跑之前记得把断言更新到新产物，**绝不反过来改结果迁就断言**。

---

## 一句提醒

工作稿里那 16 个 `[STALE ...]` 是故意留在正文里的，不是待办清单的副本。
**它们必须在投稿前一个不剩地被真实数字替换掉。** 如果哪一处最后决定保留 v18.6 的值，
那也得是有意识的决定，并且在 `DECISIONS.md` 里写明理由——不能靠"忘了删标记"来通过。
