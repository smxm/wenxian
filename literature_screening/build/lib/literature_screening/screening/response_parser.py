from __future__ import annotations

import json

from literature_screening.core.exceptions import ResponseParseError


def parse_model_json(raw_text: str) -> dict:
    normalized = _strip_code_fences(raw_text.strip())
    try:
        return json.loads(normalized)
    except json.JSONDecodeError as exc:
        extracted = _extract_json_fragment(normalized)
        if extracted is not None:
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                pass
        raise ResponseParseError(f"Failed to parse model response as JSON: {exc}") from exc


def _strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _extract_json_fragment(text: str) -> str | None:
    start_positions = [index for index in (text.find("{"), text.find("[")) if index != -1]
    if not start_positions:
        return None

    start = min(start_positions)
    opening = text[start]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if char == '"' and not escaped:
                in_string = False
            escaped = char == "\\" and not escaped
            continue

        if char == '"':
            in_string = True
            escaped = False
            continue

        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None
