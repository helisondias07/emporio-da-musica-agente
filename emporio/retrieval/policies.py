"""Busca nas seções do manual e checagem contra o PDF."""

from __future__ import annotations

import math
from pathlib import Path

from emporio.config import data_dir
from emporio.retrieval.policy_sections import KEY_PHRASES, OPERATIONAL_INTERPRETATION, SECTIONS
from emporio.text import fold, normalize_ws, tokenize

TOPIC_SECTIONS = {
    "about": ["capa", "1", "1.1", "1.2"],
    "address": ["capa", "1.2"],
    "hours": ["2"],
    "payment": ["3", "3.1", "6.2"],
    "returns": ["4", "4.1", "4.2", "4.3", "4.4"],
    "shipping": ["5", "5.1", "5.2", "5.3"],
    "promotions": ["6", "6.1", "6.2", "7.3"],
    "whatsapp": ["7", "7.1", "7.2", "7.3", "2"],
    "warranty": ["8", "8.1", "8.2", "8.3", "4.2"],
    "privacy": ["9"],
    "scope": ["1", "7.1"],
}

# Short queries ("endereço", "horário") need a nudge or BM25 under-ranks them.
BOOSTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("endereco", "cep", "cnpj", "onde fica", "localizacao"), ("capa", "1.2")),
    (("horario", "funcionamento", "sabado", "domingo", "feriado", "abre"), ("2",)),
    (("pix", "boleto", "parcela", "parcelamento", "cartao", "pagamento", "debito"), ("3", "3.1", "6.2")),
    (("arrepend", "devolv", "reembol", "troca", "defeito"), ("4", "4.1", "4.2", "4.3", "4.4")),
    (("frete", "entrega", "sedex", "jadlog", "correio", "rastre"), ("5", "5.1", "5.2", "5.3")),
    (("promoc", "desconto", "black friday", "cumulativ"), ("6", "6.1", "6.2", "7.3")),
    (("whatsapp", "atendimento"), ("7", "7.1", "2")),
    (("garantia",), ("8", "8.1", "8.2", "8.3")),
    (("privacidade", "lgpd", "dados pessoais"), ("9",)),
    (("acessorio", "palheta", "amplificador", "pedal"), ("1", "7.1")),
)


class _BM25:
    def __init__(self, docs: list[list[str]]) -> None:
        self.docs = docs
        self.k1 = 1.4
        self.b = 0.6
        self.n = len(docs)
        self.avgdl = sum(len(doc) for doc in docs) / self.n
        df: dict[str, int] = {}
        for doc in docs:
            for token in set(doc):
                df[token] = df.get(token, 0) + 1
        self.idf = {
            token: math.log(1 + (self.n - freq + 0.5) / (freq + 0.5))
            for token, freq in df.items()
        }

    def score(self, query: list[str], index: int) -> float:
        doc = self.docs[index]
        frequencies: dict[str, int] = {}
        for token in doc:
            frequencies[token] = frequencies.get(token, 0) + 1
        total = 0.0
        length = len(doc) or 1
        for token in query:
            freq = frequencies.get(token)
            if not freq:
                continue
            denominator = freq + self.k1 * (1 - self.b + self.b * length / self.avgdl)
            total += self.idf.get(token, 0.0) * (freq * (self.k1 + 1)) / denominator
        return total


_DOCS = [tokenize(section["heading"] + " " + section["text"]) for section in SECTIONS]
_BM25_INDEX = _BM25(_DOCS)
_BY_ID = {section["id"]: section for section in SECTIONS}


def search_policies(query: str | None = None, topic: str | None = None, limit: int = 3) -> dict:
    limit = max(1, min(int(limit), 6))
    if topic:
        key = fold(topic).replace(" ", "")
        aliases = {
            "endereco": "address",
            "horario": "hours",
            "pagamento": "payment",
            "troca": "returns",
            "devolucao": "returns",
            "frete": "shipping",
            "entrega": "shipping",
            "promocao": "promotions",
            "garantia": "warranty",
            "privacidade": "privacy",
            "escopo": "scope",
            "sobre": "about",
        }
        key = aliases.get(key, key)
        if key not in TOPIC_SECTIONS:
            return {
                "error": f"Tópico '{topic}' não existe.",
                "topics": sorted(TOPIC_SECTIONS),
            }
        chosen = [_BY_ID[section_id] for section_id in TOPIC_SECTIONS[key]]
        return _result(query or topic, chosen[:limit], by_topic=key)

    tokens = tokenize(query or "")
    if not tokens:
        return {"error": "Informe query ou topic."}

    folded_query = fold(query or "")
    scored: list[tuple[float, dict]] = []
    for index, section in enumerate(SECTIONS):
        score = _BM25_INDEX.score(tokens, index)
        heading_tokens = set(tokenize(section["heading"]))
        score += 1.5 * sum(1 for token in tokens if token in heading_tokens)
        for needles, section_ids in BOOSTS:
            if section["id"] in section_ids and any(needle in folded_query for needle in needles):
                score += 3.5
        if score > 0:
            scored.append((score, section))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    top = [section for _, section in scored[:limit]]
    if not top:
        return {
            "query": query,
            "sections": [],
            "message": "Nenhuma seção do manual cobre essa pergunta.",
        }
    return _result(query or "", top, by_topic=None)


def corpus_text() -> str:
    return normalize_ws("\n".join(section["text"] for section in SECTIONS))


def extract_pdf_text(path: Path | None = None) -> str:
    import pymupdf

    pdf_path = path or (data_dir() / "politicas_da_loja.pdf")
    document = pymupdf.open(pdf_path)
    try:
        return "\n".join(page.get_text("text") for page in document)
    finally:
        document.close()


def policy_alignment() -> dict:
    pdf_norm = normalize_ws(extract_pdf_text()).casefold()
    corpus_norm = corpus_text().casefold()
    missing_pdf = [phrase for phrase in KEY_PHRASES if normalize_ws(phrase).casefold() not in pdf_norm]
    missing_corpus = [phrase for phrase in KEY_PHRASES if normalize_ws(phrase).casefold() not in corpus_norm]
    return {
        "phrases": len(KEY_PHRASES),
        "missing_from_pdf": missing_pdf,
        "missing_from_index": missing_corpus,
        "ok": not missing_pdf and not missing_corpus,
    }


def _result(query: str, sections: list[dict], by_topic: str | None) -> dict:
    return {
        "query": query,
        "topic": by_topic,
        "operational_interpretation": OPERATIONAL_INTERPRETATION,
        "sections": [
            {"id": section["id"], "heading": section["heading"], "text": section["text"]}
            for section in sections
        ],
    }
