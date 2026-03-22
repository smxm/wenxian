from __future__ import annotations

RUN_CONFIG_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "RunConfig",
    "type": "object",
    "required": ["project", "input", "screening", "criteria", "model", "report"],
    "properties": {
        "project": {
            "type": "object",
            "required": ["name", "output_dir"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "output_dir": {"type": "string", "minLength": 1},
                "save_raw_response": {"type": "boolean", "default": True},
                "save_intermediate_files": {"type": "boolean", "default": True},
            },
            "additionalProperties": False,
        },
        "input": {
            "type": "object",
            "required": ["input_files"],
            "properties": {
                "input_files": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "bib_files": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "encoding": {"type": "string", "default": "utf-8"},
            },
            "additionalProperties": False,
        },
        "dedup": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "strict_doi_match": {"type": "boolean", "default": True},
                "normalized_title_exact_match": {"type": "boolean", "default": True},
                "fuzzy_title_match": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
        "screening": {
            "type": "object",
            "required": ["batch_size", "target_include_count", "stop_when_target_reached"],
            "properties": {
                "batch_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                "target_include_count": {"type": "integer", "minimum": 1},
                "stop_when_target_reached": {"type": "boolean", "default": True},
                "allow_uncertain": {"type": "boolean", "default": True},
                "retry_times": {"type": "integer", "minimum": 0, "maximum": 10, "default": 2},
                "request_timeout_seconds": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 600,
                    "default": 120,
                },
            },
            "additionalProperties": False,
        },
        "criteria": {
            "type": "object",
            "required": ["topic", "inclusion", "exclusion"],
            "properties": {
                "topic": {"type": "string", "minLength": 1},
                "inclusion": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "exclusion": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
            },
            "additionalProperties": False,
        },
        "model": {
            "type": "object",
            "required": ["provider", "model_name", "api_base_url", "api_key_env"],
            "properties": {
                "provider": {"type": "string", "enum": ["kimi", "deepseek"]},
                "model_name": {"type": "string", "minLength": 1},
                "api_base_url": {"type": "string", "minLength": 1},
                "api_key_env": {"type": "string", "minLength": 1},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.2},
                "max_tokens": {"type": "integer", "minimum": 256, "maximum": 32768, "default": 8192},
                "min_request_interval_seconds": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 60,
                    "default": 0,
                },
            },
            "additionalProperties": False,
        },
        "report": {
            "type": "object",
            "properties": {
                "export_included_ris": {"type": "boolean", "default": True},
                "export_excluded_ris": {"type": "boolean", "default": False},
                "export_unused_ris": {"type": "boolean", "default": True},
                "export_included_bib": {"type": "boolean", "default": False},
                "export_excluded_bib": {"type": "boolean", "default": False},
                "export_unused_bib": {"type": "boolean", "default": False},
                "included_report_format": {"type": "string", "enum": ["md", "json"], "default": "md"},
                "excluded_report_format": {"type": "string", "enum": ["md", "json"], "default": "md"},
                "summary_format": {"type": "string", "enum": ["json"], "default": "json"},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}

BATCH_SCREENING_RESPONSE_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "BatchScreeningResponse",
    "type": "object",
    "required": ["batch_id", "results"],
    "properties": {
        "batch_id": {"type": "string", "minLength": 1},
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["paper_id", "decision", "reason", "evidence", "confidence"],
                "properties": {
                    "paper_id": {"type": "string", "minLength": 1},
                    "decision": {"type": "string", "enum": ["include", "exclude", "uncertain"]},
                    "reason": {"type": "string", "minLength": 1},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["title", "abstract", "keywords", "year", "journal", "doi", "other"],
                        },
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
