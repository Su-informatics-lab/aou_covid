# 怎么卖：从苏老师那篇 JAMIA 学套路

**对照物：** Gatz AE, Xiong C, Chen Y, 等. *Health disparities in the risk of severe
acidosis: real-world evidence from the All of Us cohort.* JAMIA 2024;31(12):2932–39.
（据 PubMed 检索到全文，[DOI](https://doi.org/10.1093/jamia/ocae256)）

**前提：** 统计不动、不加新分析。以下全部是**措辞与结构**，不改一个数字。

---

## 一、我们最强的卖点是现成的，只是没有被放到台面上

那篇的做法是**每个社会域单独进一个模型**，一共十二个模型，从头到尾没有把六个域放在
一起。它摘要里的 Medicaid 1.41、renters 1.41、unemployed 1.32、income <$25k 1.3–1.57，
全部是**单域估计**。

我们已经算出来：这些单域估计**互相重叠**。

> 三项组合（Medicaid + 收入 $10,000–24,999 + 租房）的单域乘积是 **2.79**，
> 互相调整之后是 **1.78**。**单域建模把这个组合高估了约三分之一。**

这一句是这篇论文最有卖相的一句话，而且完全是我们自己的，不需要任何新分析。
它现在藏在 Results 第 67 段和 Discussion 第 88 段的句末。

**建议：把 2.79 → 1.78 提到摘要 Results 的第一句，和 Discussion 的开头。**
它同时做到三件事：给一个具体数字、说明为什么要联合建模、并且暗示只做单域的工作
（包括那一篇）系统性高估。不点名任何人，只讲方法。

第二强的一句已经有了，同样没被抬头用：教育低于 GED 单域 1.35，联合后 1.13 不再显著
——**"教育的表观效应是收入和就业的影子"**。

---

## 二、那篇有、我们没有的四个动作

| 它的动作 | 原文 | 我们的现状 |
|---|---|---|
| **Discussion 里一节 "Return of value to communities"** | 专门讲这项研究还给 All of Us 社区什么 | 完全没有。All of Us 论文的审稿人期待这一节 |
| **图题是论断，不是标签** | "The base model **demonstrates** the associations of…" | 我们的是 "Base-model adjusted odds ratios for demographics, …"（清单） |
| **明说匹配设计买到了什么** | "The propensity score matching design **elucidates the barriers to accessing necessary healthcare** by disentangling and controlling the confounding effects related to patients' **willingness** to use healthcare services." | 我们只写了机制（informative presence bias），没写它换来了什么解释力 |
| **声明 STROBE** | "following the STROBE reporting guideline" | 一个字没提 |

第三条最值钱。我们的 encounter-density 匹配和它是同一个设计，但它把这个设计翻译成了
一句人话：**在"同样愿意看病、同样频繁看病"的人之间比较，剩下的差异就是拿不到服务，
不是不想去。** 我们的稿子里没有这句话，而这句话正是把一个统计选择变成一个论点的地方。

---

## 三、结尾的落点

它的结论段落到政策上，而且很硬：

> "…the systematic health barriers underlying the observed health disparities…
> **cannot be eliminated by health interventions and education but need changes in
> public health policies.**"

一个关联性研究敢这么落，而且过了 JAMIA。

我们现在的落点是：

> "Interpretation of these associations depends on survey timing and on overlap among
> the social domains."

这是一句**注意事项**，不是落点。谨慎是对的，但谨慎不该占最后一句。

**建议**（不改数字、不加声称）：把注意事项往前挪一句，最后一句留给论断本身——
六个自报社会域在互相调整后仍有四个成立，而它们的联合贡献比逐个相加小三分之一，
所以按单一社会指标筛查会同时高估个体风险、低估域间重叠。

这是我们的数据支持得住的最强表述，也没有跨进"可行动/可筛查"那条线。

---

## 四、可以现在就改的清单（都不碰数字）

排序按性价比。

1. **摘要 Results 首句换成 2.79 → 1.78。** 一句话，最大增益。
2. **Discussion 开头一段先讲联合建模的增量，再讲文献对比。** 现在是反的：第 79 段先花
   一整段讲别人做了什么，第 80 段才讲我们。
3. **加一节 "Return of value to communities"**（约 150 词）。All of Us 论文的规定动作。
4. **Methods 补一句 STROBE 声明**，并把 checklist 放进 supplement。
5. **把匹配设计的解释力写成一句人话**，放在 Methods 那段的末尾和 Discussion 的
   Strengths 里。
6. **五个图题改成论断句。** 例如 Figure 4 从 "Domain-specific versus joint associations
   of six survey-derived SDoH domains" 改成 "Mutual adjustment reduces four of six social
   domains and eliminates the education association"。
7. **Discussion 小节 "The measurement case: why survey-linked EHR matters" 改题**为
   "Why the survey linkage was necessary" —— 现在这个题目是一个我们没做检验的论断。
8. **Results 七个小节标题改成论点**（现在只有一个像论点）。

1–5 我可以直接做，都是加/换措辞。6–8 动到图题和结构，等你点头。

---

## 五、我们比它强在哪里（Strengths 段应该说出来，现在没说）

- 六域**联合**建模 vs 十二个单域模型
- 波次分层 + （即将有的）交互检验
- Black-race 系数衰减的分解
- 693,682 观测的跨队列临床模型比较，且**报告了五个方向不一致的估计**
- 五项敏感性分析
- 一个把每个印出来的数字锁到冻结产物上的 gate（117 条断言）

最后一条在 informatics 期刊是有分量的，现在只出现在仓库里，稿子里一个字没提。
**建议在 Methods 末尾加一句**：所有报告数值由自动断言对冻结分析产物校验，代码公开。
