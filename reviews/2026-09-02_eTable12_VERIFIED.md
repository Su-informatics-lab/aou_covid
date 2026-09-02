# eTable 12b / 12c — 已核实（不再是 UNVERIFIED）

**日期：** 2026-09-02 · **在 All of Us Researcher Workbench 2.0（Verily）上直接读取原始产物核对**

---

## 一、产物在哪里

不在这个 Verily workspace 自己的桶里，在 **Researcher Workbench 1.0 迁移过来的桶**：

```
gs://rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7/
```

七个文件全部完好：

```
wave_stratified_race.csv                     wave_joint_sdoh_pre_delta_coefficients.csv
wave_stratified_insurance.csv                wave_joint_sdoh_delta_coefficients.csv
wave_stratified_race_attenuation.csv         wave_joint_sdoh_omicron_coefficients.csv
wave_stratified_income.csv
```

**缺口从来不在桶里，在 git。** `02c` 建文件那一版就有 `gsutil` 上传（我先前说它没有，是核错了，
已在 `reviews/2026-09-01_eTable12_forensics.md` 更正）。上传到桶 ≠ 进仓库，没有人把它们拉回来
`git add`，所以 Data Availability 指向的仓库里复现不出来。

---

## 二、逐值核对：全中

### eTable 12b — 分波次 Black race（`wave_stratified_race_attenuation.csv`）

| 波次 | 模型 | 产物读出 | 稿子印的 | |
|---|---|---|---|---|
| pre-Delta | Base | 2.996604 (2.560217–3.507374) | 3.00 (2.56–3.51) | ✅ |
| pre-Delta | Joint | 2.641924 (2.226911–3.134280)，衰减 **11.5** | 2.64 (2.23–3.13)，11.5% | ✅ |
| Delta | Base | 2.983820 (1.793310–4.964663) | 2.98 (1.79–4.96) | ✅ |
| Delta | Joint | 2.170306 (1.209863–3.893190)，衰减 **29.1** | 2.17 (1.21–3.89)，29.1% | ✅ |
| Omicron | Base | 1.647304 (1.335005–2.032661) | 1.65 (1.34–2.03) | ✅ |
| Omicron | Joint | 1.417410 (1.123046–1.788929)，衰减 **30.1** | 1.42 (1.12–1.79)，30.1% | ✅ |

衰减百分比是 CSV 里 `pct_attenuation` 列直接带的，不是我重算的——上一轮取证只能靠公式反推，
现在是原始输出对上了。

### eTable 12c — 分波次 Medicaid，单域模型（`wave_stratified_insurance.csv`）

| 波次 | 产物读出 | 稿子印的 | |
|---|---|---|---|
| pre-Delta | 1.712777 (1.428809–2.053182)，p 5.95e-09 | 1.71 (1.43–2.05) | ✅ |
| Delta | 2.237963 (1.216201–4.118131)，p 9.62e-03 | 2.24 (1.22–4.12) | ✅ |
| Omicron | 1.463253 (1.151145–1.859981)，p 1.87e-03 | 1.46 (1.15–1.86) | ✅ |

### eTable 13 抽查（`wave_stratified_income.csv`）

pre-Delta，收入 <$10,000：**1.485131 (1.210599–1.821921)**，p 1.49e-04 → 稿子 1.49 (1.21–1.82) ✅

---

## 三、结论

**`DECISIONS.md` D8 里那句"单项最大未闭合问题"可以划掉了。** 数字是真的，来源找到了，
逐位对得上。上一轮那份取证报告的三项间接检验（衰减公式、CI 对数对称、SE 按 1/√n 缩放）
方向全对，现在有了直接证据。

**还差最后一步：把这四个 CSV 提交进 git。** 它们是聚合模型系数（无个体级数据、无 <20 的单元格），
与已发表的 eTable 12b/12c 内容相同。是否导出由你和 All of Us 的数据政策决定，我不替你做这个决定。

---

## 四、顺带查到的、会影响重跑的三件事

1. **`WORKSPACE_BUCKET` 在这个 app 环境里是空的。**
   `01b_psm.R`、`02_models.R`、`02c` 的上传块都是 `if (nchar(bucket) > 0)` 守卫的，
   **空值会让上传被静默跳过**——这正是当初文件只活在临时机器上的机制之一。重跑前必须
   `export WORKSPACE_BUCKET=gs://rw-migration-aou-rw-46c7ae9e`（或新桶）。

2. **perimeter 没有挡网络。** github.com、pypi.org、cloud.r-project.org 全部返回 200，
   `git clone` 成功。所以 R 装包和拉代码都不需要走桶。

3. **clone 下来默认在主分支，`notebooks/` 只在 `review/v18.7-reconcile` 上。**
   要先 `git checkout review/v18.7-reconcile`。

---

## 五、环境记录

| | |
|---|---|
| Workspace | `AUD_MH_Genomics_v7_v2` / `aou-rw-46c7ae9e` |
| GCP 项目 | `wb-gleaming-coffee-3314` |
| CDR | `C2022Q4R13`（cdrv7，version-bound）— 与 `STUDY_DESIGN.md` 一致 |
| App | AoU Jupyter，n1-highmem-4（4 vCPU / 26 GB），100 GB 盘 |
| 费用 | 运行 $0.24/小时；盘 $5.60/月（默认 500 GB 已改为 100 GB） |
| 自动停机 | 闲置 4 小时 |
| 代码位置 | `~/covid/repo`（已 clone） |
| 已恢复的 CSV | `~/covid/results/aou_v7/wave_*.csv` |
