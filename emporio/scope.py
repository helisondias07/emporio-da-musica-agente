"""Separa pedido de acessório de pedido de instrumento.

"Violão de cordas de aço" é violão. "Vocês têm corda de aço?" é acessório.
O aviso vai para o modelo. A busca de catálogo não atende esses itens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from emporio.text import fold

_ACCESSORIES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("palheta", re.compile(r"\bpalhetas?\b")),
    ("cabo", re.compile(r"\bcabos?\b")),
    ("case", re.compile(r"\bcases?\b")),
    ("pedal", re.compile(r"\bpedal\b|\bpedais\b")),
    ("amplificador", re.compile(r"\bamplificador(?:es)?\b|\bampli\b|\bamplis\b")),
    ("encordoamento", re.compile(r"\bencordoamento(?:s)?\b|\bjogo de cordas\b|\bcorda avulsa\b|\bcordas avulsas\b")),
)

_STRINGS = re.compile(r"\bcordas?\b")
_ORCHESTRAL = re.compile(r"\bcordas? orquestrais\b")
# "violão de cordas de aço" describes the instrument. "cordas de aço para violão" does not.
_STRING_SPEC = re.compile(
    r"\b(violao|guitarra|baixo|ukulele|cavaquinho)\b(?:\s+\w+){0,3}\s+de\s+cordas?\s+de\s+(aco|nylon|nailon)\b"
)
_INSTRUMENT = re.compile(
    r"\b(violao|guitarra|baixo|contrabaixo|ukulele|bateria|teclado|piano|saxofone|flauta|violino|instrumento)\b"
)


@dataclass(frozen=True)
class Scope:
    accessories: tuple[str, ...]
    mentions_instrument: bool

    @property
    def kind(self) -> str:
        if self.accessories and self.mentions_instrument:
            return "mixed"
        if self.accessories:
            return "accessory"
        return "in_scope"


def analyze_scope(message: str) -> Scope:
    folded = fold(message)
    found: list[str] = []
    for label, pattern in _ACCESSORIES:
        if pattern.search(folded):
            found.append(label)
    if _STRINGS.search(folded) and not _ORCHESTRAL.search(folded) and not _STRING_SPEC.search(folded):
        found.append("cordas")
    mentions_instrument = _INSTRUMENT.search(folded) is not None
    return Scope(accessories=tuple(dict.fromkeys(found)), mentions_instrument=mentions_instrument)


def scope_hint(message: str) -> str | None:
    scope = analyze_scope(message)
    if not scope.accessories:
        return None
    items = ", ".join(scope.accessories)
    if scope.kind == "mixed":
        return (
            f"A mensagem pede acessório ({items}) e também instrumento. "
            "Recuse só o acessório, sem buscar produto para ele, e atenda o instrumento."
        )
    return (
        f"A mensagem pede acessório que a loja não vende ({items}). "
        "Recuse com educação. Não chame search_products para esses itens e não invente loja parceira."
    )
