from __future__ import annotations

LITERATURE_CARD_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "LiteratureCard",
    "type": "object",
    "required": [
        "paper_id",
        "source_record",
        "screening_info",
        "content_summary",
        "classification",
        "reporting_flags",
    ],
    "properties": {
        "paper_id": {"type": "string", "minLength": 1},
        "source_record": {
            "type": "object",
            "required": ["title_en", "title_zh", "authors", "year", "journal", "doi", "abstract"],
            "properties": {
                "title_en": {"type": "string", "minLength": 1},
                "title_zh": {"type": ["string", "null"]},
                "authors": {"type": "array", "items": {"type": "string"}},
                "year": {"type": ["integer", "null"]},
                "journal": {"type": ["string", "null"]},
                "doi": {"type": ["string", "null"]},
                "abstract": {"type": ["string", "null"]},
            },
            "additionalProperties": False,
        },
        "screening_info": {
            "type": "object",
            "required": ["decision", "screen_stage", "reason", "confidence"],
            "properties": {
                "decision": {"type": "string", "enum": ["include", "exclude", "uncertain"]},
                "screen_stage": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "additionalProperties": False,
        },
        "content_summary": {
            "type": "object",
            "required": [
                "one_sentence_summary",
                "core_summary",
                "research_focus",
                "value_for_topic",
                "limitations",
            ],
            "properties": {
                "one_sentence_summary": {"type": "string", "minLength": 1},
                "core_summary": {"type": "string", "minLength": 1},
                "research_focus": {"type": "string", "minLength": 1},
                "value_for_topic": {"type": "string", "minLength": 1},
                "limitations": {"type": "string", "minLength": 1},
            },
            "additionalProperties": False,
        },
        "classification": {
            "type": "object",
            "required": [
                "primary_category",
                "secondary_category",
                "study_type",
                "application_context",
                "core_problem",
                "method_keywords",
                "domain_tags",
            ],
            "properties": {
                "primary_category": {"type": "string", "minLength": 1},
                "secondary_category": {"type": ["string", "null"]},
                "study_type": {"type": "string", "minLength": 1},
                "application_context": {"type": ["string", "null"]},
                "core_problem": {"type": "string", "minLength": 1},
                "method_keywords": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "domain_tags": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
        "reporting_flags": {
            "type": "object",
            "required": ["recommended_level", "is_key_paper"],
            "properties": {
                "recommended_level": {"type": "string", "enum": ["high", "medium", "low"]},
                "is_key_paper": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


FORMAL_REPORT_OVERVIEW_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "FormalReportOverviewPayload",
    "type": "object",
    "required": ["report_title", "overview", "category_overviews", "conclusion"],
    "properties": {
        "report_title": {"type": "string", "minLength": 1},
        "overview": {"type": "string", "minLength": 1},
        "category_overviews": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "category_name",
                    "category_summary",
                    "category_value",
                    "representative_paper_ids",
                ],
                "properties": {
                    "category_name": {"type": "string", "minLength": 1},
                    "category_summary": {"type": "string", "minLength": 1},
                    "category_value": {"type": "string", "minLength": 1},
                    "representative_paper_ids": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                    },
                },
                "additionalProperties": False,
            },
        },
        "conclusion": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

