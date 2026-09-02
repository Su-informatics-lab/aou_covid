# D22 — 2026-09-02 — 敏感性重跑接进稿子；补充材料从平台补齐；三张与正文打架的表

## 零、这一轮最要紧的一件事：平台可以完全程序化操作了

之前四次试出"打字进得去、回车进不去"，所以每条命令都要你按一下回车。
这一轮换了路子：JupyterLab 是嵌在 `workbench.verily.com` 里的**跨域 iframe**，
所以父页面的 JS 够不到它。直接把浏览器导航到 iframe 自己的域
（`https://<app-id>.workbench-app-prod.verily.com/lab`），JupyterLab 就成了顶层文档，
`/api/kernels` 与 `_xsrf` 同源可用。于是：REST 建一个 kernel → websocket 发
`execute_request` → 收 iopub 输出。**完全不碰键盘，回车问题消失。**
用完把 kernel 关掉了（DELETE 204）。

## 一、敏感性重跑

`03_sensitivity.R` 跑在 `results/aou_v7/08_regression_base.csv`（19,521 行，修正后）上。
事先立的证伪标准是 **S3 的 `f.incomeless_10k` 必须不再是 1.1293**；变了，24 行全变。
每行过对数尺度对称性检验，P 由区间反推并与"区间是否含 1"自洽。
反推程序验过：S5 折叠收入我算 0.0070，脚本印 0.0069。

**eTable 13 全部重建。**两处跨过 1：S3 收入 <$10,000 = 1.16 (0.99–1.36)；
S1 Medicaid = 1.15 (0.999–1.32), P=0.051。失业在五个设定里都最大（1.31–1.39），
租房五个都显著（1.12–1.20）。

### 脚本自己印的 PRIMARY 那一行来自哪里 —— 查清楚了

`03_sensitivity.R:468` 读 `results/aou_v7/joint_sdoh_coefficients.csv`。
那个文件由 `02_models.R:351` 写。**本地那份是 v18.6**（Medicaid 1.3257、失业 1.2305），
而同目录的 `08_regression_base.csv` 是修正后的。也就是说：**输入是新的，模型产物是旧的**——
`02_models.R` 从来没在这台机器上重跑过，01:41 的时间戳是从桶里同步下来的。

**这是第四次"路径对、内容错"，而且这次连时间戳都是新的。**

## 二、补充材料这一轮补齐了六张表

全部先打指纹再用（base: 女性 0.768 / Black 2.387 / pulmonary 0.904；joint: Medicaid 1.193 / 失业 1.350）。

| 表 | 补了什么 | 来源 |
|---|---|---|
| eTable 6 | 配对前三个匹配变量的中位数与 IQR（6 格） | `06_matching_variables.csv`，24,809 人 |
| eTable 7(a) | 配对后同上（6 格） | 与 `08_regression_base.csv` 合并，3,997 / 15,523 |
| eTable 10b Panel A | 整张重跑，32 行全给 | 重跑 `02b_variance_sensitivity.R aou_v7` |
| eTable 11a | 整张重跑 | 桶里的 `race_attenuation_table.csv` |
| eTable 11b | 每一波的 strata 数 | 由冻结文件算出并用 `survival::clogit` 复核 |
| eTable 11c | strata 数 + 联合 Medicaid AOR 与 P（9 格） | `wave_joint_sdoh_*_coefficients.csv` |

**只剩 eTable 10b Panel B 一处 [STALE]**：MarketScan 的方差比较要在 Quartz 上跑
`Rscript 02b_variance_sensitivity.R ms`，这台机器上没有 MarketScan 数据。

### 顺带纠正的三处

- **eTable 6 的 caption 写着 SMD = 0.489**，是修正前的值；表自己的 SMD 列写的是 0.410，
  正文 ¶42 也是 0.410。**caption 和自己的表打架。**已改。
- **eTable 10b Panel A 原来说"一处推断翻转（Asian race）"。重跑后是零处翻转。**
  正文 ¶38 那句跟着改：现在写"用 Efron 近似重拟合以取得聚类稳健方差，P = 0.05 处无推断改变"。
  MarketScan 那半句只保留方法事实（exact 方法下没有 score residuals），不再声称翻转数。
- **eTable 11b 的 note 写 "644 cases, 301 valid strata"**，表里同一行是 638，strata 那格是空的。
  重算后 Delta 是 638 cases / **282** strata。note 里的两个数删掉，strata 填进表里。

## 三、¶67 那个 11.7% —— 是重跑值，不是抄来的

`race_attenuation_table.csv`（桶里，修正后）第一行 `B_income` 就是 **11.7**，
housing **8.7**、insurance **6.2**、education 4.8、employment 3.8、joint **15.1**。
和 ¶67、摘要一字不差。**旧表也印 11.7 是巧合**（收入在两个版本里都主导）。摘要不用动。

## 四、一个真正新的结果：Medicaid 的分波次联合估计

eTable 11c 的联合列原来是空的，现在填上了：

| 波次 | 单域 | 联合 |
|---|---|---|
| Pre-Delta | 1.74 (1.45–2.09) | **1.52 (1.22–1.90)** P<0.001 |
| Delta | 1.46 (0.83–2.57) | 0.92 (0.43–1.99) P=0.84 |
| Omicron | 1.36 (1.06–1.73) | 0.99 (0.73–1.34) P=0.93 |

原来 ¶73 写"Medicaid 在每一波都升高、除 Delta 外显著"——那是**单域**列的描述。
**联合调整之后，Medicaid 只在 Delta 之前升高。**已改写，并且这与文中已有的
"insurance 是唯一波次交互显著的暴露（P = 0.003）"互相印证，是加强不是削弱。

## 五、图 3–5：图重画过了，但稿子里嵌的还是旧图

`figs19/` 里 19:12 的新图从来没换进 docx，嵌入的还是旧的（4125 px 宽、旧长宽比）。已换。
三条图注也和图对不上：

- **Figure 3** 说"17 个 Charlson，MI 和 PVD 因版面省略"——新图 19 个全画了。已改。
- **Figure 4** 说有灰色连接条、右侧列出估计值——两样都没有。右侧那句改成指向 Table 3；
  **灰色连接条我加进图里了**，Medicaid 1.54 → 1.19 那条最长，是这张图的论点。
- **Figure 4** 还印着 "never attended school" 的 3.35 / 2.85，正文 ¶60 明说"不报告"。已删。
- **Figure 5** 说 (b) 画了调整前后两组，新图只有一组。改成如实描述。

## 六、正文其他改动

- ¶75 换成真话（五个设定、失业最大、两处跨过 1、S5 折叠收入 1.17 (1.04–1.31)）。
- ¶95 不再等有效样本量：直接写"15,523 条对照观测来自 9,784 名不同参与者（eTable 10）"。
  平台上复核过：unique 9,784、最大复用 10、中位 1、IQR 1–2，与 eTable 10 完全一致。
- ¶45 的 chronic pulmonary 下限 0.84 → **0.83**，与 eTable 9 一致。
  eTable 9 是从文件生成的，正文那个是手打的；**改稿子去迁就产物，不是反过来。**
- Table 3 的 $100,000–149,999 下限印成 1.002（原来印 1.00，旁边却有星号）。

正文 **3,968 词**（上限 4,000，余 32），摘要 250。

## 七、校验

| 检查 | 结果 |
|---|---|
| 对数区间对称性（容差按印刷精度算） | 正文 68、补充 127，**1 处告警** |
| 那 1 处 | ¶20 引用的 meta 分析 1.87 (1.69–2.04)：**算术尺度**对称，不是我们的估计 |
| Table 3 星号 vs 区间 | 38 格 0 处不一致 |
| eTable 11a / 11b 的衰减百分比 vs 自己的 AOR | 全部落在两位小数取整能解释的范围内 |
| eTable 11b vs 11c 的 N cases / N strata | 三行完全一致 |
| ¶67 vs eTable 11a、¶73 vs eTable 11c | 全部对上 |
| 补充表编号闭环 | 19 处引用全部解析 |
| strata 数 | pandas 与 `survival::clogit` 两条路算出同一组 1,868 / 282 / 1,132 |

**容差按印刷精度算 `(u/2)(2/a + 1/lo + 1/hi)`，这个检验才第一次能跑全文。**
固定 3% 阈值会报 85 处假警。

## 八、还欠什么

**只有你能做：**
1. draw.io 两个面板（数字见 `working/MS_SUPPLEMENT_UPDATES.md`）。仓库里没有 .drawio 源文件，
   在你自己电脑别处。
2. 通读一遍。
3. **Workbench 的 app 还开着，$0.24/hr，用完点 Stop。**

**要在 Quartz 上跑一次：** `Rscript 02b_variance_sensitivity.R ms` → eTable 10b Panel B。
这是补充材料里最后一处 [STALE]。

**公开仓库历史：** `results/` 已从 `main` 的 tip 移除（`8c0b56d`），但 blob 还在 60 个 commit 的历史里。
清历史要 rewrite + force-push，是实验室的决定。

---

## 九、补记：eTable 10b Panel B —— 不用重跑，它早就跑好了

用 Desktop Commander 从你的 Mac ssh 到 Quartz（`~/.ssh/config` 里的 `quartz` 别名、
`id_ed25519`，key 认证，没有密码），发现 **Panel B 根本不需要重跑**：
`results/ms/variance_sensitivity_etable11b.csv` 的时间是 **Sep 1 23:01**，
就在 `01b_psm.R` 写出修正后的 `08_regression_base.csv`（22:59）两分钟之后。
02b 那一步当时没失败，**只是结果从来没被取回来过**——你 Mac 上那份是 Jun 7 的。

按内容验过才用：

- 输入 `results/ms/08_regression_base.csv`：637,679 观测 / 127,696 例 / 509,983 对照 /
  127,696 strata / 443,061 名不同对照 / 最大复用 21。Figure 1b 的四个不变量加 eTable 10 的两个，全对。
- 输出的系数与修正后的 MarketScan 基础模型一致：女性 0.75、接种 0.50、Delta 1.11、
  Omicron 0.73、severe renal 3.31、AIDS 1.69。

**结果：38 个模型项，CI 比值中位数 1.00，一处推断改变** —— consumer-directed 计划类型，
exact 0.99–1.42 对 cluster-robust 1.01–1.39。我另外用"exact 区间是否含 1"与
"robust 区间是否含 1"独立复算了一遍翻转，只有这一项，与文件里的 `flip` 列一致。

所以 ¶38 现在写：两个队列都用 Efron 重拟过，**All of Us 零处改变，MarketScan 一处，
而且是计划类型这个协变量，不是暴露**。这比原来那句（"每个队列各一处"）和上一版
（"AoU 一处、MS 零处"）都准，而且两个 panel 现在同属一个版本。

`ms_variance_sensitivity.sbatch` 留在仓库里没删——将来要重跑还是它，
而且它那段按内容拒绝错误输入的 guard 正是这一轮反复用到的做法。

**补充材料现在零处 [STALE]。**正文 3,979 词（上限 4,000，**余 21**）。
