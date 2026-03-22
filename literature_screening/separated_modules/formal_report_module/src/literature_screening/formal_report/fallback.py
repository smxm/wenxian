from __future__ import annotations

from collections import Counter

from literature_screening.core.models import PaperRecord
from literature_screening.core.models import ScreeningDecision
from literature_screening.formal_report.models import CardScreeningInfo
from literature_screening.formal_report.models import CategoryOverview
from literature_screening.formal_report.models import ClassificationInfo
from literature_screening.formal_report.models import ContentSummary
from literature_screening.formal_report.models import LiteratureCard
from literature_screening.formal_report.models import ReportOverviewPayload
from literature_screening.formal_report.models import ReportingFlags
from literature_screening.formal_report.models import SourceRecord
from literature_screening.formal_report.text_utils import contains_cjk
from literature_screening.formal_report.text_utils import normalize_text
from literature_screening.formal_report.text_utils import split_sentences


def build_fallback_literature_cards(
    included_rows: list[tuple[PaperRecord, ScreeningDecision]],
) -> list[LiteratureCard]:
    cards: list[LiteratureCard] = []
    for paper, decision in included_rows:
        clean_title = normalize_text(paper.title) or paper.title
        clean_abstract = normalize_text(paper.abstract)
        combined_text = f"{clean_title} {clean_abstract or ''}".lower()

        study_type = _infer_study_type(combined_text)
        primary_category = _infer_primary_category(combined_text, study_type)
        method_keywords = _pick_keywords(paper.keywords, combined_text)
        domain_tags = _pick_domain_tags(combined_text, method_keywords)
        application_context = _infer_application_context(combined_text)
        focus_phrase = _build_focus_phrase(primary_category, method_keywords)

        cards.append(
            LiteratureCard(
                paper_id=paper.paper_id,
                source_record=SourceRecord(
                    title_en=clean_title,
                    title_zh=clean_title if contains_cjk(clean_title) else None,
                    authors=paper.authors,
                    year=paper.year,
                    journal=normalize_text(paper.journal),
                    doi=paper.doi,
                    abstract=clean_abstract,
                ),
                screening_info=CardScreeningInfo(
                    decision=decision.decision,
                    screen_stage=decision.screen_stage,
                    reason=normalize_text(decision.reason) or decision.reason,
                    confidence=decision.confidence,
                ),
                content_summary=ContentSummary(
                    one_sentence_summary=_build_one_sentence_summary(clean_title, clean_abstract, focus_phrase),
                    core_summary=_build_core_summary(clean_title, clean_abstract, study_type, focus_phrase),
                    research_focus=_build_research_focus(study_type, focus_phrase),
                    value_for_topic=_build_value_for_topic(clean_title, decision.reason, primary_category),
                    limitations=_build_limitations(clean_abstract),
                ),
                classification=ClassificationInfo(
                    primary_category=primary_category,
                    secondary_category=_infer_secondary_category(combined_text, primary_category),
                    study_type=study_type,
                    application_context=application_context,
                    core_problem=_build_core_problem(clean_title, clean_abstract, focus_phrase),
                    method_keywords=method_keywords,
                    domain_tags=domain_tags,
                ),
                reporting_flags=ReportingFlags(
                    recommended_level=_infer_recommended_level(decision.confidence),
                    is_key_paper=decision.confidence >= 0.9,
                ),
            )
        )
    return cards


def build_fallback_report_overview(
    cards: list[LiteratureCard],
    project_topic: str,
) -> ReportOverviewPayload:
    grouped: dict[str, list[LiteratureCard]] = {}
    for card in cards:
        grouped.setdefault(card.classification.primary_category, []).append(card)

    sorted_groups = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    category_names = [name for name, _ in sorted_groups]

    category_overviews: list[CategoryOverview] = []
    for category_name, category_cards in sorted_groups:
        study_types = Counter(card.classification.study_type for card in category_cards)
        top_study_types = "、".join(study_type for study_type, _ in study_types.most_common(3))
        top_contexts = [card.classification.application_context for card in category_cards if card.classification.application_context]
        context_text = ""
        if top_contexts:
            common_context = Counter(top_contexts).most_common(1)[0][0]
            context_text = f"相关讨论多落在{common_context}等场景。"

        category_overviews.append(
            CategoryOverview(
                category_name=category_name,
                category_summary=(
                    f"这一方向的文献主要围绕{category_name}展开，常见研究路径包括{top_study_types}。"
                    f"相关讨论通常聚焦于核心机制、干预策略、实验验证或证据整合等方面。{context_text}"
                ).strip(),
                category_value=(
                    f"就{project_topic}而言，这一方向能够帮助梳理相关机制的代表思路、典型技术路线以及后续值得优先比对的问题。"
                ),
                representative_paper_ids=[card.paper_id for card in _pick_representative_cards(category_cards, limit=3)],
            )
        )

    major_categories = "、".join(category_names[:4]) if category_names else "若干相关方向"
    overview = (
        f"围绕“{project_topic}”这一主题，现有文献主要可归纳为{major_categories}等方向。"
        "从研究形态来看，既包括机制阐释与实验验证，也包括干预策略评估、模型研究以及综述性整理。"
        "整体上，这批文献能够较好地反映该主题当前较受关注的研究切入点与证据积累方向。"
    )
    conclusion = (
        f"综合来看，{project_topic}相关研究已经形成一定的方向分化，不同文献在研究对象、实验介质与评价指标上各有侧重。"
        "后续如需进一步深入，建议优先结合重点文献阅读全文，重点比较不同研究路径的证据强度、机制完整性与应用可行性。"
    )

    return ReportOverviewPayload(
        report_title=f"{project_topic}文献整理报告",
        overview=overview,
        category_overviews=category_overviews,
        conclusion=conclusion,
    )


def _build_one_sentence_summary(title: str, abstract: str | None, focus_phrase: str) -> str:
    sentences = split_sentences(abstract or "")
    if sentences and contains_cjk(sentences[0]):
        return _trim_sentence(sentences[0], 90)
    problem_summary = _summarize_problem_from_text(f"{title} {abstract or ''}".lower(), focus_phrase)
    return f"该文献围绕{problem_summary}展开，可作为后续阅读全文与方案比较时的参考。"


def _build_core_summary(title: str, abstract: str | None, study_type: str, focus_phrase: str) -> str:
    sentences = split_sentences(abstract or "")
    if sentences and contains_cjk(" ".join(sentences[:2])):
        leading = " ".join(sentences[:2])
        return (
            f"该研究主要围绕{focus_phrase}展开。"
            f"从摘要可见，作者采用{study_type}的路径讨论相关问题，核心内容主要涉及{leading}"
        )
    problem_summary = _summarize_problem_from_text(f"{title} {abstract or ''}".lower(), focus_phrase)
    application_context = _infer_application_context(f"{title} {abstract or ''}".lower())
    context_clause = f"并将讨论放在{application_context}中展开" if application_context else "并结合具体应用或实验环境进行讨论"
    return (
        f"该研究主要围绕{problem_summary}展开，整体上属于{study_type}路径。"
        f"就现有题目与摘要信息而言，文章重点更偏向于{focus_phrase}，{context_clause}。"
    )


def _build_research_focus(study_type: str, focus_phrase: str) -> str:
    return f"{study_type}；重点关注{focus_phrase}"


def _build_value_for_topic(title: str, reason: str, primary_category: str) -> str:
    clean_reason = normalize_text(reason)
    if clean_reason:
        return f"这篇文献之所以值得保留，主要在于{clean_reason}"
    return f"这篇文献与{primary_category}直接相关，可作为该方向中用于补充机制理解和方案比较的参考材料。"


def _build_limitations(abstract: str | None) -> str:
    if abstract:
        return "以下整理主要基于题目、摘要与关键词形成，具体实验设置、参数范围、结果边界及方法细节仍需阅读全文后进一步核实。"
    return "当前可用信息主要来自题目和有限元数据，因此对于方法细节、实验结果与适用边界的判断仍较为有限。"


def _build_core_problem(title: str, abstract: str | None, focus_phrase: str) -> str:
    sentences = split_sentences(abstract or "")
    if sentences and contains_cjk(sentences[0]):
        return _trim_sentence(sentences[0], 120)
    return _summarize_problem_from_text(f"{title} {abstract or ''}".lower(), focus_phrase)


def _infer_study_type(text: str) -> str:
    if any(token in text for token in ["review", "survey", "overview"]):
        return "综述研究"
    if any(token in text for token in ["simulation", "numerical", "finite element", "dem", "model", "analysis"]):
        return "建模研究"
    if any(token in text for token in ["experiment", "experimental", "test", "validation", "prototype"]):
        return "实验研究"
    if any(token in text for token in ["design", "system", "robot", "mechanism", "algorithm", "control"]):
        return "方法与系统设计"
    return "相关研究"


def _infer_primary_category(text: str, study_type: str) -> str:
    if any(token in text for token in ["review", "survey", "overview", "scoping review", "narrative review"]):
        return "综述与证据整合"
    if any(token in text for token in ["microbiota", "microbiome", "gut bacteria", "gut microbiota", "microbial", "microbiome"]):
        return "肠道菌群与代谢调控"
    if any(
        token in text
        for token in [
            "adipocyte differentiation",
            "adipogenesis",
            "lipid metabolism",
            "lipogenic",
            "lipolysis",
            "adipocyte",
            "fat accumulation",
        ]
    ):
        return "脂肪细胞分化与脂质代谢"
    if any(
        token in text
        for token in [
            "macrophage",
            "inflammation",
            "immune",
            "adipose tissue",
            "microglia",
            "tissue microenvironment",
        ]
    ):
        return "免疫炎症与组织微环境"
    if any(
        token in text
        for token in [
            "metabolome",
            "metabolomic",
            "metabolomics",
            "oxidative",
            "antioxidative",
            "secretory profile",
            "proteomic",
            "transcriptomic",
        ]
    ):
        return "代谢组学与机制分析"
    if any(
        token in text
        for token in [
            "extract",
            "supplementation",
            "supplement",
            "polysaccharide",
            "propolis",
            "compound",
            "dietary",
            "fish oil",
            "coffee",
            "nutrient",
            "natural product",
        ]
    ):
        return "天然产物与营养干预"
    if any(
        token in text
        for token in [
            "lncrna",
            "mirna",
            "gene",
            "signaling",
            "pi3k/akt",
            "akt",
            "ppard",
            "pathway",
            "molecular",
        ]
    ):
        return "分子机制与信号通路"
    if any(token in text for token in ["impact", "penetrator", "penetration", "projectile", "mole", "hammer"]):
        return "冲击与贯入机制"
    if any(token in text for token in ["drill", "drilling", "auger", "screw", "helical", "rotational penetration"]):
        return "钻进与螺旋推进"
    if any(token in text for token in ["earthworm", "razor clam", "bio-inspired", "soft robot", "seed", "burrowing soft"]):
        return "仿生与软体掘进"
    if any(token in text for token in ["granular", "sand", "soil", "regolith", "substrate", "media"]):
        return "介质响应与相互作用"
    if any(token in text for token in ["control", "positioning", "path planning", "compensation", "recognition", "imu", "vision"]):
        return "机器人控制与作业辅助"
    if study_type == "建模研究":
        return "建模与机理分析"
    if study_type == "实验研究":
        return "实验与性能验证"
    return "相关机制研究"


def _infer_secondary_category(text: str, primary_category: str) -> str | None:
    if primary_category == "综述与证据整合":
        if "clinical" in text:
            return "机制与临床证据综述"
        return "主题综述"
    if primary_category == "肠道菌群与代谢调控":
        return "微生物-代谢物调控"
    if primary_category == "脂肪细胞分化与脂质代谢":
        if "adipocyte differentiation" in text:
            return "脂肪细胞分化调控"
        return "脂质代谢调控"
    if primary_category == "免疫炎症与组织微环境":
        return "脂肪组织微环境"
    if primary_category == "代谢组学与机制分析":
        return "多组学或代谢组分析"
    if primary_category == "天然产物与营养干预":
        return "天然活性成分干预"
    if primary_category == "分子机制与信号通路":
        return "基因与信号轴调控"
    if primary_category == "冲击与贯入机制":
        if "lunar" in text or "mars" in text or "planetary" in text:
            return "行星表面穿透"
        return "高速度贯入"
    if primary_category == "钻进与螺旋推进":
        if "dual" in text and "auger" in text:
            return "双螺旋钻进"
        if "self-burrowing" in text or "burrowing" in text:
            return "自埋推进"
    if primary_category == "仿生与软体掘进":
        if "earthworm" in text:
            return "蚯蚓仿生"
        if "razor clam" in text:
            return "蛏类仿生"
    return None


def _infer_application_context(text: str) -> str | None:
    if any(token in text for token in ["clinical", "patient", "human", "participants"]):
        return "临床与人群研究"
    if any(token in text for token in ["in vitro", "cell", "cells", "adipocyte", "preadipocyte"]):
        return "细胞与体外实验"
    if any(token in text for token in ["mouse", "mice", "rat", "rats", "murine", "bovine", "chicken", "elegans"]):
        return "动物或模式生物研究"
    if any(token in text for token in ["review", "survey", "overview", "scoping review"]):
        return "综述与证据整理"
    if any(token in text for token in ["moon", "lunar", "mars", "planetary"]):
        return "行星表面与月壤环境"
    if any(token in text for token in ["coal mine", "underground mine", "drill pipe"]):
        return "地下矿井作业"
    if any(token in text for token in ["deep-sea", "marine", "ocean"]):
        return "海底地层环境"
    if any(token in text for token in ["sand", "soil", "granular", "regolith"]):
        return "颗粒介质环境"
    return None


def _build_focus_phrase(primary_category: str, method_keywords: list[str]) -> str:
    if method_keywords:
        return f"{primary_category}及{'、'.join(method_keywords[:3])}等问题"
    return primary_category


def _pick_keywords(keywords: list[str], text: str) -> list[str]:
    cleaned_keywords = [normalize_text(keyword) for keyword in keywords if normalize_text(keyword)]
    if cleaned_keywords:
        return cleaned_keywords[:6]

    ordered_candidates = [
        ("obesity", "肥胖"),
        ("adipose", "脂肪组织"),
        ("adipocyte", "脂肪细胞"),
        ("adipogenesis", "脂肪生成"),
        ("lipid metabolism", "脂质代谢"),
        ("metabolome", "代谢组"),
        ("metabolomics", "代谢组"),
        ("microbiota", "肠道菌群"),
        ("inflammation", "炎症"),
        ("macrophage", "巨噬细胞"),
        ("lncrna", "lncRNA"),
        ("mirna", "miRNA"),
        ("pi3k", "PI3K/AKT"),
        ("akt", "PI3K/AKT"),
        ("extract", "提取物干预"),
        ("polysaccharide", "多糖干预"),
        ("drilling", "钻进"),
        ("drill", "钻进"),
        ("screw", "螺旋推进"),
        ("auger", "螺旋钻进"),
        ("helical", "螺旋机构"),
        ("penetration", "贯入"),
        ("penetrator", "穿透器"),
        ("impact", "冲击"),
        ("granular", "颗粒介质"),
        ("sand", "砂土"),
        ("soil", "土壤"),
        ("regolith", "月壤"),
        ("robot", "机器人"),
        ("control", "控制"),
        ("path planning", "路径规划"),
    ]
    selected: list[str] = []
    for token, label in ordered_candidates:
        if token in text and label not in selected:
            selected.append(label)
    return selected[:6] or ["相关机制", "系统设计"]


def _pick_domain_tags(text: str, method_keywords: list[str]) -> list[str]:
    tags = list(method_keywords[:4])
    for token, label in [
        ("lunar", "月壤"),
        ("mars", "火星"),
        ("planetary", "行星探测"),
        ("deep-sea", "海底钻探"),
        ("coal mine", "煤矿作业"),
        ("bio-inspired", "仿生"),
        ("soft robot", "软体机器人"),
        ("self-burrowing", "自埋机器人"),
    ]:
        if token in text and label not in tags:
            tags.append(label)
    return tags[:6] or method_keywords[:4]


def _pick_representative_cards(cards: list[LiteratureCard], limit: int) -> list[LiteratureCard]:
    return sorted(cards, key=_recommended_sort_key)[:limit]


def _recommended_sort_key(card: LiteratureCard) -> tuple[int, int, str]:
    level_order = {"high": 0, "medium": 1, "low": 2}
    return (
        level_order.get(card.reporting_flags.recommended_level, 3),
        -(card.source_record.year or 0),
        card.source_record.title_en,
    )


def _infer_recommended_level(confidence: float) -> str:
    if confidence >= 0.9:
        return "high"
    if confidence >= 0.75:
        return "medium"
    return "low"


def _trim_sentence(text: str, limit: int) -> str:
    cleaned = normalize_text(text) or ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _summarize_problem_from_text(text: str, focus_phrase: str) -> str:
    aspects: list[str] = []
    candidates = [
        (["drill", "drilling", "auger", "screw", "helical"], "钻进机构设计与推进稳定性"),
        (["impact", "penetrat", "projectile", "mole"], "贯入阻力、冲击响应与穿透效率"),
        (["granular", "sand", "soil", "regolith", "substrate"], "颗粒介质中的相互作用与阻力变化"),
        (["control", "positioning", "path planning", "compensation", "recognition"], "机器人控制精度与作业辅助能力"),
        (["bio-inspired", "earthworm", "seed", "root", "soft robot", "clam"], "仿生推进策略与软体掘进结构"),
        (["sampling", "coring"], "取样与作业执行能力"),
    ]
    for tokens, label in candidates:
        if any(token in text for token in tokens) and label not in aspects:
            aspects.append(label)
    if aspects:
        return "、".join(aspects[:2])
    return focus_phrase
