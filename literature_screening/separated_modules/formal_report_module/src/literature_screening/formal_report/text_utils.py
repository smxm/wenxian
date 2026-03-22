from __future__ import annotations

import html
import re
import unicodedata


COMMON_REPLACEMENTS = {
    "鈥檚": "'s",
    "鈥?": "'",
    "鈥�": '"',
    "锟�": "",
    "漏 ": "",
}


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    text = html.unescape(value)
    text = unicodedata.normalize("NFKC", text)
    for source, target in COMMON_REPLACEMENTS.items():
        text = text.replace(source, target)

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = _strip_noise_suffix(text)
    return text or None


def split_sentences(text: str) -> list[str]:
    if not text:
        return []

    normalized = normalize_text(text) or ""
    parts = re.split(r"(?<=[。！？.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _strip_noise_suffix(text: str) -> str:
    patterns = [
        r"©.*$",
        r"Published by .*?$",
        r"All rights reserved.*$",
        r"including those for text and data mining.*$",
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned
