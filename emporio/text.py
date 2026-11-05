"""Text folding used by search and by the policy index."""

from __future__ import annotations

import re
import unicodedata

_STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "ate",
    "com",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "no",
    "o",
    "os",
    "para",
    "por",
    "pra",
    "que",
    "se",
    "um",
    "uma",
}


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.casefold()


def tokenize(value: str) -> list[str]:
    parts = re.findall(r"[a-z0-9]+", fold(value))
    return [part for part in parts if part not in _STOPWORDS and (len(part) > 1 or part.isdigit())]


def normalize_ws(value: str) -> str:
    cleaned = value.replace("\u200b", "").replace("\u00ad", "")
    return re.sub(r"\s+", " ", cleaned).strip()
