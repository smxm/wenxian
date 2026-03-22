# LiteratureCard 技术规格

## 1. 文档目的

本文档用于定义正式报告模块的核心中间数据对象 `LiteratureCard`。  
`LiteratureCard` 是连接“筛选模块”和“正式报告模块”的标准文献卡片结构，承担以下职责：

- 承接最终纳入文献的原始元数据
- 保存筛选阶段的关键判断信息
- 保存单篇文献的中文总结与分析
- 提供可聚合的分类标签，支撑自动归类
- 为 Markdown 正式报告、摘要报告和推荐列表提供统一数据来源

---

## 2. 设计目标

`LiteratureCard` 需要同时满足以下要求：

- 可读：适合人查看和人工抽查
- 可追溯：能回溯到原始文献信息与筛选结果
- 可分类：支持自动归类和后续章节生成
- 可渲染：适合直接映射到正式 Markdown 报告
- 可扩展：后续可以新增字段，但不破坏已有渲染逻辑

---

## 3. 结构总览

建议将 `LiteratureCard` 固定为以下五个分组：

1. `source_record`
2. `screening_info`
3. `content_summary`
4. `classification`
5. `reporting_flags`

顶层建议结构如下：

```json
{
  "paper_id": "paper_000001",
  "source_record": {},
  "screening_info": {},
  "content_summary": {},
  "classification": {},
  "reporting_flags": {}
}
```

---

## 4. 顶层字段定义

### 4.1 `paper_id`

- 类型：`string`
- 必填：是
- 含义：系统内部唯一文献 ID
- 示例：`paper_000001`
- 说明：用于将正式报告卡片与筛选结果、导出 BibTeX、日志文件进行关联

---

## 5. `source_record` 字段组

该字段组用于保存原始事实信息，不应被 AI 进行主观改写。

### 5.1 字段定义

`title_en`

- 类型：`string`
- 必填：是
- 含义：原始英文标题，若原始文献为中文题目，则保留原题

`title_zh`

- 类型：`string | null`
- 必填：否
- 含义：中文标题或中文译名
- 说明：若原始文献本身为中文标题，可与 `title_en` 相同；若为英文文献，则为准确中文译名

`authors`

- 类型：`string[]`
- 必填：是
- 含义：作者列表

`year`

- 类型：`integer | null`
- 必填：否
- 含义：发表年份

`journal`

- 类型：`string | null`
- 必填：否
- 含义：期刊、会议、学校或来源单位

`doi`

- 类型：`string | null`
- 必填：否
- 含义：DOI

`abstract`

- 类型：`string | null`
- 必填：否
- 含义：摘要正文

### 5.2 示例

```json
"source_record": {
  "title_en": "A bio-inspired helically driven self-burrowing robot",
  "title_zh": "一种仿生螺旋驱动自埋机器人",
  "authors": ["Bagheri, Hosain", "Marvi, Hamid"],
  "year": 2024,
  "journal": "Acta Geotechnica",
  "doi": "10.1007/s11440-023-01882-9",
  "abstract": "Autonomous subsurface applications have created a need for burrowing mechanisms and robots."
}
```

---

## 6. `screening_info` 字段组

该字段组用于保存筛选阶段的关键结果，主要供内部追溯和审计，不直接面向最终交付读者。

### 6.1 字段定义

`decision`

- 类型：`"include" | "exclude" | "uncertain"`
- 必填：是
- 说明：正式报告模块通常只处理 `include` 文献，但保留该字段有助于溯源

`screen_stage`

- 类型：`string`
- 必填：是
- 推荐值：`title_abstract`

`reason`

- 类型：`string`
- 必填：是
- 含义：筛选纳入原因简述

`confidence`

- 类型：`number`
- 必填：是
- 取值范围：`0` 到 `1`

### 6.2 示例

```json
"screening_info": {
  "decision": "include",
  "screen_stage": "title_abstract",
  "reason": "标题和摘要显示该研究直接关注自埋机器人及其推进机制。",
  "confidence": 0.95
}
```

---

## 7. `content_summary` 字段组

该字段组是正式报告正文的核心内容来源。  
建议由单篇总结型 prompt 生成，并保持格式统一。

### 7.1 字段定义

`one_sentence_summary`

- 类型：`string`
- 必填：是
- 含义：一句话概括文献核心内容
- 长度建议：30 到 60 字
- 用途：摘要版报告、推荐列表、总表展示

`core_summary`

- 类型：`string`
- 必填：是
- 含义：2 到 4 句的中文核心总结
- 用途：正式报告正文主段落

`research_focus`

- 类型：`string`
- 必填：是
- 含义：研究重点短语
- 示例：`推进机构设计与实验验证`

`value_for_topic`

- 类型：`string`
- 必填：是
- 含义：对当前主题的参考价值
- 说明：这是正式交付中最重要的字段之一，应从“委托人为什么值得看这篇”角度书写

`limitations`

- 类型：`string`
- 必填：是
- 含义：基于标题、摘要和关键词能识别的局限或待补充点
- 说明：不得假装读过全文

### 7.2 示例

```json
"content_summary": {
  "one_sentence_summary": "该研究提出了一种仿生螺旋驱动自埋机器人，并通过实验分析其推进性能与能耗表现。",
  "core_summary": "本文围绕颗粒介质中的自埋推进问题，设计了仿生螺旋驱动机构，并比较了不同结构参数对推进速度、能耗和阻力表现的影响。研究重点在于推进效率与机构优化之间的关系，并通过实验验证其可行性。",
  "research_focus": "推进机构设计与实验验证",
  "value_for_topic": "可为地下推进机器人机构设计、推进效率优化和能耗权衡提供直接参考。",
  "limitations": "基于摘要可见，研究主要集中于特定实验介质和样机条件，尚无法判断其在复杂地层中的适用性。"
}
```

---

## 8. `classification` 字段组

该字段组用于支撑自动归类、章节聚合和后续类别命名，是正式报告模块自动化能力的核心。

### 8.1 字段定义

`primary_category`

- 类型：`string`
- 必填：是
- 含义：主分类
- 要求：每篇文献必须且只能有一个主分类

`secondary_category`

- 类型：`string | null`
- 必填：否
- 含义：次级分类

`study_type`

- 类型：`string`
- 必填：是
- 含义：研究类型
- 推荐示例：
  - `实验研究`
  - `建模研究`
  - `方法设计`
  - `系统实现`
  - `综述研究`

`application_context`

- 类型：`string | null`
- 必填：否
- 含义：应用场景或研究环境

`core_problem`

- 类型：`string`
- 必填：是
- 含义：该文献主要解决的核心问题

`method_keywords`

- 类型：`string[]`
- 必填：是
- 数量建议：3 到 6 个

`domain_tags`

- 类型：`string[]`
- 必填：是
- 含义：更自由的领域标签
- 数量建议：3 到 6 个

### 8.2 示例

```json
"classification": {
  "primary_category": "螺旋驱动推进",
  "secondary_category": "仿生自埋机器人",
  "study_type": "实验研究",
  "application_context": "地下探测与颗粒介质环境",
  "core_problem": "如何提升颗粒介质中的推进效率并降低运动代价",
  "method_keywords": ["螺旋驱动", "自埋机器人", "颗粒介质", "推进性能"],
  "domain_tags": ["burrowing robot", "helical propulsion", "granular media"]
}
```

---

## 9. `reporting_flags` 字段组

该字段组用于正式交付阶段的呈现控制。

### 9.1 字段定义

`recommended_level`

- 类型：`"high" | "medium" | "low"`
- 必填：是
- 含义：推荐优先级

`is_key_paper`

- 类型：`boolean`
- 必填：是
- 含义：是否作为重点推荐文献

### 9.2 示例

```json
"reporting_flags": {
  "recommended_level": "high",
  "is_key_paper": true
}
```

---

## 10. 完整示例

```json
{
  "paper_id": "paper_000001",
  "source_record": {
    "title_en": "A bio-inspired helically driven self-burrowing robot",
    "title_zh": "一种仿生螺旋驱动自埋机器人",
    "authors": ["Bagheri, Hosain", "Marvi, Hamid"],
    "year": 2024,
    "journal": "Acta Geotechnica",
    "doi": "10.1007/s11440-023-01882-9",
    "abstract": "Autonomous subsurface applications have created a need for burrowing mechanisms and robots."
  },
  "screening_info": {
    "decision": "include",
    "screen_stage": "title_abstract",
    "reason": "标题和摘要显示该研究直接关注自埋机器人及其推进机制。",
    "confidence": 0.95
  },
  "content_summary": {
    "one_sentence_summary": "该研究提出了一种仿生螺旋驱动自埋机器人，并通过实验分析其推进性能与能耗表现。",
    "core_summary": "本文围绕颗粒介质中的自埋推进问题，设计了仿生螺旋驱动机构，并比较了不同结构参数对推进速度、能耗和阻力表现的影响。研究重点在于推进效率与机构优化之间的关系，并通过实验验证其可行性。",
    "research_focus": "推进机构设计与实验验证",
    "value_for_topic": "可为地下推进机器人机构设计、推进效率优化和能耗权衡提供直接参考。",
    "limitations": "基于摘要可见，研究主要集中于特定实验介质和样机条件，尚无法判断其在复杂地层中的适用性。"
  },
  "classification": {
    "primary_category": "螺旋驱动推进",
    "secondary_category": "仿生自埋机器人",
    "study_type": "实验研究",
    "application_context": "地下探测与颗粒介质环境",
    "core_problem": "如何提升颗粒介质中的推进效率并降低运动代价",
    "method_keywords": ["螺旋驱动", "自埋机器人", "颗粒介质", "推进性能"],
    "domain_tags": ["burrowing robot", "helical propulsion", "granular media"]
  },
  "reporting_flags": {
    "recommended_level": "high",
    "is_key_paper": true
  }
}
```

---

## 11. 字段生成建议

建议字段来源如下：

- `source_record`：来自原始文献记录
- `screening_info`：来自筛选模块输出
- `content_summary`：由单篇总结 prompt 生成
- `classification`：由单篇标签 prompt 生成
- `reporting_flags`：由单篇评估 prompt 或程序规则生成

---

## 12. 使用建议

正式报告模块建议采用以下链路：

1. 读取 `included` 文献
2. 生成 `LiteratureCard`
3. 基于 `classification.primary_category` 自动聚类
4. 生成类别概述
5. 渲染正式 Markdown 报告

---

## 13. 第一版实现建议

如果希望先做最小可行版本，建议优先实现以下字段：

- `paper_id`
- `source_record.title_en`
- `source_record.title_zh`
- `source_record.authors`
- `source_record.year`
- `source_record.journal`
- `source_record.doi`
- `source_record.abstract`
- `content_summary.one_sentence_summary`
- `content_summary.core_summary`
- `content_summary.value_for_topic`
- `content_summary.limitations`
- `classification.primary_category`
- `classification.study_type`
- `classification.domain_tags`
- `reporting_flags.recommended_level`

这些字段已经足够支撑：

- 正式 Markdown 报告
- 简版摘要报告
- 自动分类汇总
- 重点推荐文献列表
