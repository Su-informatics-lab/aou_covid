# 稿子还欠什么

**工作稿：** `working/ms_v191_rerun_WORKING.docx` · 更新至 2026-09-02（MarketScan 已接进来）
**提交版 `submission/02_manuscript.docx` 仍然没有动过** —— 它整篇是 v18.6，内部一致。
工作稿是新旧混合的，每一处旧数字都打了 `[STALE ...]`，**搜 "STALE" 就能全找到（14 处）**。

---

## 这一轮做完的：MarketScan 全链

Quartz job `10186336`，退出码 0。ETL（job `10186030`）带着 `coverage_span_days` 的
index 前限制，resume 脚本里的 guard 在续跑前**重新验了两个不变量**，没有相信上一份日志：
coverage-span SMD −0.3630（阈值 |SMD| ≥ 0.20）、Dementia 5,527（< 10,000）。

已经接进稿子的：

| 位置 | 内容 |
|---|---|
| Table 1 的 MarketScan 两列 | 30 行全换 · N 从 139,468/554,214 → **127,696/509,983** |
| Results cross-cohort 一段 | 整段重写（见下） |
| Discussion cross-cohort 一段 | 整段重写（见下） |
| Limitations | 加上 MarketScan 侧的排除数：11,571 例 / 401,608 对照 |
| Methods 方差那句 | 写明 MS 用模型方差的**原因**（exact 法没有 score residual），并加上 Efron 稳健重拟的结果 |
| Figure 1 图注 (b) | 整条 CONSORT 链重写 |
| Figure 3 图注 | n = 693,682 → **637,679** |
| Table 1 图注 | **新加 STALE**：AoU 两列仍是 v18.6，与正文的 3,997/15,523 对不上 |

`working/MS_SUPPLEMENT_UPDATES.md` 里是 eTable 8/9/10/11b/14 和 Figure 1 (b) 的
**逐格替换值**，都从产物文件抄的，不是从日志的散文里抄的。

### 这不只是换数字 —— 论点变了

v18.6 里 MarketScan 有**九个** Charlson 条目是显著反向的（chronic pulmonary 0.86、
rheumatic 0.82、peptic ulcer 0.79、mild liver 0.78、cerebrovascular 0.86、PVD 0.86、
HIV 0.86、MI 0.94、malignancy 0.94）。**九个全部翻回来了，修完之后没有一个低于 1.0**
（最低是 peptic ulcer 1.0063），其中七个显著为害。

而 All of Us 那两个（chronic pulmonary 0.90、mild liver 0.83）**修完还在**。

所以原来那句"反向关联是 encounter-density 匹配设计的后果"**只对了一半**：

- 在 claims 里，它几乎全部是数据构造错误 —— coverage span 按整个参保记录去量，
  index 之后还有一两年，**那根本是另一个变量**。修完就没了。
- 在 All of Us 里，同样的修复只让它们向 1.0 挪了约三分之一，**剩下的才是设计**。

机制在 Table 1 里直接看得见：**病例的合并症人数几乎没动，对照的患病率掉了五分之一到三分之一**
（chronic pulmonary 16.6% → 13.1%，mild liver 7.0% → 5.1%），因为配到的对照不再带着
更长的 index 前观察窗去攒诊断码。

**而且它在匹配后的平衡诊断里是看不见的** —— 修之前 |SMD| < 0.03，修之后 < 0.07，两次都"合格"。
这条写进 Discussion 了，它比原来那段有价值得多。

---

## 还欠的，按阻断程度排序

### 1. All of Us 的 base-model 向量 —— 现在唯一卡住 cross-cohort 的一件事

`base_model_coefficients.csv` 里的**波次与 19 个 comorbidity 的 AoU 估计**没有读出来。
少了它：

- eTable 10 的 AoU 列还是 v18.6
- "25 个可比估计里有几个方向不一致" 这句算不出来（v18.6 是 5 个）
- Omicron 的两边对比写不了（MS 侧已经有了：0.73, 0.70–0.76）
- Figure 3 两个系列都重画不了

**一条命令的事**，但要在 Workbench 里跑：重启 app，`python print_aou_stale.py`。

### 2. 其它需要从已有产物里再读出来的（不用重跑）

| 缺什么 | 在哪个文件 |
|---|---|
| 单域 SDoH 全部取值（Table 3 第一列、2.79 那个乘积） | `insurance_/income_/education_/employment_/housing_*_coefficients.csv` |
| 联合模型剩下的水平（student、non-employment、上中收入两档、disability、housing other） | `joint_sdoh_coefficients.csv` |
| 五项敏感性分析 | `sensitivity_S1..S5_*_coefficients.csv`、`eTable_S16_sensitivity.csv` |
| 分波次收入（eTable 13） | `eTable_S13_wave_income.csv` |
| 对照唯一人数、最大复用、有效样本量 | `07b_control_reuse.csv`、`07e_matchit_summary.txt` |
| 收入缺失的差异比例、Omicron 收敛警告 | `table2_sdoh.csv`、`02_models.R` 日志 |

**取的方式：在平台上打印，读出来。** 不要打包下载 —— 每一个值出平台前都要过 <20 检查
（`education_coefficients.csv` 里 "never attended school" 一档就是不足 20 人的）。

### 3. Table 1 的 AoU 两列 / Table 2 / Table 3 / 全部 eTable

**Table 1 的 MarketScan 两列已经是新的，AoU 两列还是 v18.6。**
这是目前稿子里最容易出事的一处：正文写 3,997 / 15,523，表里写 4,064 / 15,856。
已经在表注里打了 STALE，但**必须整列替换掉**，不能只改 N。

Table 2、Table 3 和补充材料里 16 张 eTable 全部是 v18.6，一张都没贴回去。

### 4. 图

`results/figures/` 里 Figure 3/4/5 要重画（Figure 3 卡在第 1 条上）。
**Figure 1 和 Figure 2 不要用脚本版**，那是 draw.io 原图。要手改的：

**panel (a)，AoU：**
- 排除框 **437**（不是 388）
- 匹配框第一项 `Enrollment date` → `Survey date`
- 计数：25,160 → 4,064 / 21,096；3,997 有完整匹配变量；19,520 观测 / 3,997 strata / 15,523 对照

**panel (b)，MarketScan —— 这是新增的，之前以为不用动：**
整条链都变了，不是改一个框。完整数字在 `MS_SUPPLEMENT_UPDATES.md` 最后一节。
panel (b) 的匹配框第一项 `Enrollment date` **是对的**，改名只适用于 panel (a)。

### 5. 最后才跑 gate

`bash analysis/gate.sh check` —— 等上面都齐了再跑，一次。
跑之前把断言更新到新产物，**绝不反过来改结果迁就断言**。

---

## 一句提醒

工作稿里那 14 个 `[STALE ...]` 是故意留在正文里的，不是待办清单的副本。
**它们必须在投稿前一个不剩地被真实数字替换掉。** 如果哪一处最后决定保留 v18.6 的值，
那也得是有意识的决定，并且在 `DECISIONS.md` 里写明理由——不能靠"忘了删标记"来通过。

---

## 附：字数超了 337 词

正文（INTRODUCTION 到 CONCLUSIONS，不含表注、图注、参考文献，`[STALE]` 标记不计）：

| 段 | 词数 |
|---|---|
| Introduction | 95 |
| Background and Significance | 383 |
| Methods | 846 |
| **Results** | **1,531** |
| **Discussion** | **1,392** |
| Conclusions | 90 |
| **合计** | **4,337** |

**JAMIA Research and Applications 上限 4,000。超 337。**

这一轮 MarketScan 接进来加了 415 词（¶77 +210、¶93 +97、¶97 +55、¶38 +36、¶45 +17），
接之前是 3,922，刚好在线内。**是我把它顶出去的**，所以先把可以砍的地方列清楚，
砍哪一处由你定 —— 这是编辑判断，不是算术。

候选，按"砍了不伤论证"排序：

1. **¶77 里的 coverage span 三个 SMD 只留两个**（−0.14 → −0.30，删掉"分析人群 −0.40"
   那半句，它在 eTable 8 里）。约 −25 词。
2. **¶77 的 Table 1 机制那句压缩**：两个百分比例子留一个。约 −20 词。
3. **¶93 的"not one phenomenon but two"那句可以合进前一句**。约 −30 词。
4. **¶38 的方差那句**：MS 用模型方差的技术原因可以整句挪到 eTable 11b 的 caption。约 −35 词。
5. **¶97 的排除比例**（1.6%/1.3%/8.3%/9.4%）挪进 eTable 8。约 −25 词。
6. Background and Significance 383 词里，Choi/Vaidya 两段的细节有约 60 词可以并。

**注意：还会再涨。** 现在这 4,337 是把 14 个 `[STALE]` 标记按零词算的，
它们换成真数字之后还要加一截。所以别只砍到 4,000 就停，留 100–150 词余量。
