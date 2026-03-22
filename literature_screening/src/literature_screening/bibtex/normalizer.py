from __future__ import annotations

import re
import unicodedata


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).lower().strip()
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
