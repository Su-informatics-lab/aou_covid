# Zhang 内审 — 逐条处理记录

**收到：** 2026-09-01 · **审稿意见：do not submit this ZIP yet** · **我们的结论：同意**
**分支：** `review/v18.7-reconcile`

处理状态四档：
**FIXED** 本轮已改并提交 · **CONFIRMED–BLOCKED** 已核实成立，但依赖重跑
**PARTIAL** 部分成立，见说明 · **DEFER** 同意方向，但应在重跑之后再决定

---

## 1. 匹配变量含 index 之后的信息 — **PARTIAL（4 条里 3 条成立），已改，重跑前阻断**

逐条到源码核实，不是全部成立。

| 指控 | 核实结果 | 处理 |
|---|---|---|
| AoU `num_diagnosis` 无 index 限制 | **成立** | `CASE WHEN condition_start_date < covid_index_date` |
| AoU `ehr_length_days` 无 index 限制 | **成立** | 同上 |
| AoU `enrollment_ord` 实为 survey date | **成立** | 改名 `survey_ord`；正文措辞待改 |
| MS `num_diagnosis` 无 index 限制 | **不成立** | `dx_long` 建表即带 `WHERE dx_date < covid_index_date`，本来就是 pre-index。未改动，加注释记录已查 |
| MS `coverage_span_days` 无 index 限制 | 技术成立 | 已截断至 index。保险到期日受住院影响小，预计变化轻微 |

**决定性证据：** 同一文件第 1019 行，Charlson 早就写着
`co.condition_start_date < e.covid_index_date`。团队知道要做这个限制，匹配变量漏了。
是 bug，不是设计选择。

**为什么严重：** `num_diagnosis` 是倾向评分里最强的项（pre-match SMD 0.489）。住院病例在
住院期间累积诊断码，所以设计部分地匹配在结局的产物上——正是 encounter-density 要防的
偏倚。对照被选成"码一样多但没住院"的人，也就是本身更病的人。

**由此推翻一个现有解释：** 稿子把 chronic pulmonary 0.85 和 mild liver 0.76 解释为
"匹配平衡的是就诊密度而非临床严重度的正常后果"。更可能的解释是这个 bug。重跑之前，
那句解释不能保留。

**未执行：** BigQuery 与 MarketScan 都不在这台机器上。SQL 改为复用 `charlson_sql` 里
已验证的 `covid_idx` CTE，两个文件语法通过，但查询一次没跑过。Workbench 上要先单独
验证 `match_vars` 返回行数与 `covid_cohort` 一致。

**提交：** `223f715`

---

## 2. 以 pre-index 调查为主分析 — **DEFER（同意方向，顺序有异议）**

S3 里 income <$10,000 降到 1.13 (0.97–1.32)、renting 降到 1.09 (0.98–1.21)，而摘要说它们
"persisted"。这个矛盾成立，我们上一轮也标过（措辞已改为"点估计向无效移动，不是样本量"）。

**但顺序上有一点不同意见：S3 用的是同一个有泄漏的匹配集。** 现在把主分析换成 S3，是在
错误的基础上换主分析。正确顺序是先修泄漏重跑，届时 S3 与全样本的差距可能变大也可能消失，
再决定哪个做主分析。

重跑后若 S3 仍不显著，则接受审稿人的处置：要么 S3 做主分析，要么删掉
"risk"、"persisted"、"screenable"、preparedness 这类需要时序支撑的措辞。

---

## 3. 波次分析的溯源与样本标注 — **FIXED（溯源）+ DEFER（交互检验）**

**已做：**
- 取证报告 `reviews/2026-09-01_eTable12_forensics.md`。三个 CSV 从未进过 git，`02c` 也不做
  `gsutil` 同步（`01b`、`02` 都做），所以只在临时 Workbench 机器上活过一次。更进一步：
  `06_supplement.py` 根本没有生成 12b/12c 的代码，两张表是手工做的。
- 但数字是真的：衰减公式三波都能重算到 0.14 个百分点内、CI 在对数尺度对称到 0.003、
  SE 按 `1/√n` 缩放（pre-Delta 与 Omicron 比值都是 1.00）。反证：若真用 644 例，Delta 的
  SE 应为 0.139，实测 0.260。
- `02c` 现在缺任一输出即 `stop()`。
- **N cases / N strata 的误导**审稿人和我们独立发现的是同一件事。正文已改成
  "1,913, 301, and 1,105 strata rather than 2,087, 644, and 1,333 cases"。**表头已改**：
  eTable 12b/12c 的两列现在是 `N cases in wave` 与 `N strata in model`，两张表的 Note 都加了
  一句说明模型样本量是后者，且 Delta 损失最大。

**未做（DEFER）：** 波次交互检验、或按波重新匹配。同意"一个波显著一个不显著不构成变化的
证据"。但这要重跑之后做，否则是在旧匹配集上做新检验。若重跑后交互项不显著，整个波次故事
移入 supplement，并从标题、摘要、结论中删除。

---

## 4. informatics 贡献不足 + 与自己 2024 JAMIA 论文重叠 — **CONFIRMED，我们漏了**

审稿人指出 Gatz et al. JAMIA 2024 用的是同一个 All of Us 队列、同样的 encounter-density
匹配、同样的社会域、同样的条件逻辑回归框架，只是结局换成 severe acidosis。

**这条我们前几轮全部漏掉了。** 更难堪的是：supplement eTable 5 自己写着 SDoH concept ID
"identical to Gatz et al. (2024)"，eTable 4 写着 Charlson "identical to Gatz et al."。
证据就在文件里，我们审了三轮没把它当作 novelty 问题。

**已做：** cover letter 增加自我重叠披露段落。查 PubMed 核实了共同作者是三位——熊晨曦、
李笑春、苏老师（Gatz et al. 作者表：Gatz, Xiong, Chen, Jiang, Nguyen, Song, Li, Zhang,
Eadon, Su），披露里点名到人。重叠部分：队列、按 EHR 可得性而非临床特征匹配、六个社会域、
条件逻辑回归框架，以及 eTable 4/5 复用的 concept set。不重叠部分：结局、六域联合建模、
波次分层、Black-race 衰减分析、MarketScan 跨队列比较。

**还要说一句不好听的：** Gatz 那篇的摘要里写着 Medicaid 1.41、renters 1.41、unemployed
1.32、income <$25k 1.3–1.57、education 负相关。和我们的方向、量级几乎一一对应。这不是
巧合，是同一批人在同一个队列上换了个结局。novelty 站不站得住，编辑会自己判断——所以
cover letter 里我写的是"把共用的方法说清楚，增量请编辑自行判断"，没有替他们下结论。

**DEFER：** 审稿人建议的队列内测量学比较（survey 覆盖率 vs 结构化 EHR / Z-code vs
区域指数）是把这篇变成真正 informatics 论文的最强升级。这是一个**新分析**，不是改写。
是否做需要你和苏老师定，因为它决定重跑后这篇的定位。

---

## 5. estimand 定义与措辞 — **FIXED（措辞）+ DEFER（DAG）**

同意。教育、就业、收入、保险、住房不是可交换的独立暴露，其中几个可能在彼此的通路上。

**已改：**
- "total association" → "association carried by that domain when it is the only social
  factor in the model"
- "independent pathway" / "independent signal" → "association that remains after the other
  measured social factors are included"
- "the quantity a single-item screen would capture" → 删除（这需要有校准、区分度和决策效用
  的预测分析才能说）
- "shared signal" → "overlap with"

**DEFER：** 因果/测量示意图。等重跑后定稿再画，否则图要跟着结论改两次。

---

## 6. 缺失机制：结构性未施测 vs 条目未作答 — **FIXED，我们也漏了**

审稿人说得对，而且这条我们更不该漏：`aou-sdoh-etl` skill 里白纸黑字写着
"65% of participants did not answer the disability question 是错的——大多数人根本没被问过"，
我们读过那个 skill，Table 2 脚注却仍写着 "Skip or Prefer-not-to-answer"。

**已改：** Table 2 脚注、eMethod、Methods 正文现在区分两种机制——收入/教育/就业/住房是
**拒答**（每个人都被问了），残疾与保险是**未施测**（ACS-6 于 2020-11-10 才加入问卷，保险
条目在入组开始后才加），并说明 missing-indicator 只避免了完整病例分析，并没有消除缺失偏倚。

**DEFER：** 按问卷版本做 IPW 或多重插补。属于新分析，重跑后再定。

---

## 7. MarketScan 降级 — **DEFER**

同意它无法验证核心结论（没有种族、没有个体社会变量、住院定义不同），也同意
"25 条里 20 条方向一致"没有预设标准。

但把 Figure 3 / Table 1 的 MarketScan 列移入 supplement 是**结构性改动**，重跑后 Table 1
本来就要重做。合并成一次改，避免做两遍。

---

## 8. 标题去掉 "preparedness" — **FIXED**

同意，理由充分：数据到 2022 年 7 月，单一病原体，没有评估任何干预措施。

新标题：**Survey-linked EHR measurement of social factors associated with COVID-19
hospitalization in the All of Us Research Program**（正文、cover letter 都已同步）

结论段里的 preparedness 措辞同步删除。

---

## 9. 提交格式 — **FIXED（本轮全部执行完毕）**

上一版这一节的对勾是计划，不是事实。现在逐条做完并核对过：

| 项 | 状态 |
|---|---|
| 双倍行距 | 179 段全部 `line_spacing = 2.0`；表格保持单倍 |
| 致谢/作者贡献/资助段的黄色高亮 | 7 处 run 已清空，全文剩 0 |
| title page：通信地址、电话、字数、MeSH 关键词 | 已在 v18.6 补齐，本轮复核无误 |
| 参考文献 3 作者 + et al. | 15 条已改（6, 10, 11, 15, 17, 22, 24, 27, 33, 36, 37, 38, 39, 45, 46） |
| 两条 preprint | 查 PubMed 核实**至今仍是 preprint，没有期刊版**。两条都标 `Preprint.`，年份统一按首次挂出的 2024（DOI 前缀 2024.10.xx）；46 的 `[published Online First: 20250418]` 改成 `[revised 18 April 2025]`，因为"Online First"会被读成已见刊 |
| All of Us 授权声明 | 新增 `ETHICS AND DATA USE` 一节，放在 `DATA AVAILABILITY` 前 |
| alt text | 5 条全部重写 |
| Table 2 住房 Missing 169→170 / 571→576 | **需重跑 `04_tables.py`**，不能手改，未动 |

**关于伦理声明的措辞，按你的要求做了取舍。** 你说不需要 IRB，我就没有写任何"本院 IRB
判定豁免"之类的话——那是我们手上没有的东西。写进去的只有能站住的四件事：All of Us 项目
自身有 IRB 批准、参与者签过知情同意、我们持 Controlled Tier 授权并完成培训、工作在注册
workspace 里按 DUA 和 Data User Code of Conduct 进行。MarketScan 按 Merative 许可使用
去标识数据。如果内审觉得还是要一句本院的话，那句得由你或苏老师提供。

**alt text 为什么要重写。** 原来的五条把正文数值又抄了一遍，最长的 177 词。屏幕阅读器
用户读到的是一串数字，读不到图长什么样。现在只描述视觉结构——坐标轴、参考线、行的排列、
标记形状与配色、误差棒、填充与空心的含义——数值留在 legend 和表里。核对过：**claim ledger
里 117 条断言的取值，没有一条因为改 alt text 而在文档里消失**（脚本比对了 v190 与 v191
的全文数字集合）。

## 我们没有做、也不打算在重跑前做的

审稿人给的新标题、新 objective、新 Results storyline、新 conclusion、新 cover letter 开头，
都写得比现在的好。但它们描述的是**重跑之后**的论文。现在照抄，等于用新话术包装旧数字。

标题和 preparedness 措辞例外——那两条与数字无关，已改。

---

## 重跑后的检查清单

- [ ] `match_vars` 查询在 Workbench 上单独跑通，行数与 `covid_cohort` 一致
- [ ] `06_matching_variables.csv` 的 `num_diagnosis` 分布明显下降（应该会）
- [ ] 全链重跑：`01` → `01b` → `02` / `02b` / `02c` / `03` → `04` / `06` → `make_figures`
- [ ] `bash analysis/gate.sh check` **会大面积失败，这是对的**——逐条把断言更新为新结果，
      不要反过来改结果去迁就断言
- [ ] 重跑后 chronic pulmonary / mild liver 是否仍为反向。若转为正向，说明泄漏就是原因，
      现有那段解释必须删掉
- [ ] 重跑后 S3 与全样本的差距，决定主分析用哪个
- [ ] 波次交互检验，决定波次故事留正文还是进 supplement
