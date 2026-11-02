"""Catalog tools: search, product detail, categories, and live promotions."""

from __future__ import annotations

import json
import re

from emporio.data import Product, Promotion, Store
from emporio.data.loader import load_store
from emporio.data.quality import description_conflicts
from emporio.money import PIX_FACTOR, as_decimal, format_brl, percent_number, quantize_brl
from emporio.text import fold, tokenize

AVAILABILITY_LABELS = {
    "available": "disponível",
    "out_of_stock": "esgotado",
    "coming_soon": "em breve",
    "discontinued": "descontinuado",
}

# Folded aliases the model is likely to pass. Values are category ids.
CATEGORY_ALIASES: dict[str, list[int]] = {
    "guitarra": [1],
    "guitarras": [1],
    "baixo": [2],
    "baixos": [2],
    "contrabaixo": [2],
    "bateria": [3],
    "baterias": [3],
    "percussao": [3],
    "teclado": [4],
    "teclados": [4],
    "piano": [4],
    "pianos": [4],
    "sintetizador": [4],
    "sintetizadores": [4],
    "violao": [5],
    "violoes": [5],
    "sopro": [6, 7],
    "madeiras": [6],
    "metais": [7],
    "violino": [8],
    "cordas orquestrais": [8],
    "ukulele": [9],
    "ukuleles": [9],
}

CATALOG_WARNING = (
    "A descrição livre cita uma marca diferente da do nome. "
    "Não descreva madeira, captador ou história da descrição. "
    "Informe nome, preço e disponibilidade e ofereça confirmar o detalhe técnico na loja."
)

SHARED_SPECS_WARNING = (
    "O bloco de specs deste produto é idêntico ao de outro SKU. "
    "Não cite esses specs como característica confirmada deste modelo."
)


def availability(product: Product) -> str:
    if product.status == "discontinued":
        return "discontinued"
    if product.status == "coming_soon":
        return "coming_soon"
    if product.stock_quantity <= 0:
        return "out_of_stock"
    if product.status == "active":
        return "available"
    return product.status


def sale_price(product: Product):
    promo = product.active_promotion
    if promo is None:
        return quantize_brl(product.list_price)
    factor = (100 - promo.discount_percent) / 100
    return quantize_brl(product.list_price * factor)


def pix_price(product: Product):
    if product.active_promotion is not None:
        return None
    return quantize_brl(product.list_price * PIX_FACTOR)


def search_products(
    query: str | None = None,
    category: str | None = None,
    max_price_brl: float | int | str | None = None,
    min_price_brl: float | int | str | None = None,
    in_stock_only: bool = False,
    on_promotion_only: bool = False,
    strings: str | None = None,
    limit: int = 15,
) -> dict:
    store = load_store()
    limit = max(1, min(int(limit), 40))
    category_ids, category_error = _resolve_categories(store, category)
    if category_error:
        return category_error

    max_price = as_decimal(max_price_brl) if max_price_brl is not None else None
    min_price = as_decimal(min_price_brl) if min_price_brl is not None else None
    wanted_strings = _normalize_strings(strings)
    if strings and wanted_strings is None:
        return {"error": "strings deve ser 'nylon' ou 'steel' (aço)."}

    tokens = tokenize(query or "")
    if _accessory_only(tokens) and category_ids is None:
        return {
            "count": 0,
            "total_matches": 0,
            "truncated": False,
            "out_of_scope": True,
            "filters": {"query": query},
            "message": (
                "A loja não vende acessórios (cordas avulsas, palhetas, cabos, cases, pedais ou amplificadores). "
                "Não ofereça um instrumento só porque a descrição cita captação ou cordas."
            ),
            "products": [],
        }
    matches = []
    for product in store.products:
        if category_ids is not None and product.category_id not in category_ids:
            continue
        if wanted_strings is not None and fold(str(product.specs.get("strings", ""))) != wanted_strings:
            continue
        price = sale_price(product)
        if max_price is not None and price > max_price:
            continue
        if min_price is not None and price < min_price:
            continue
        state = availability(product)
        if in_stock_only and state != "available":
            continue
        if on_promotion_only and product.active_promotion is None:
            continue
        score = _score(product, tokens)
        if tokens and score <= 0:
            continue
        payload = _payload(store, product, detailed=False)
        payload["_score"] = score if tokens else 1
        payload["_sale"] = price
        matches.append(payload)

    if max_price is not None and not tokens:
        matches.sort(key=lambda row: (row["_sale"], row["name"]))
    else:
        matches.sort(
            key=lambda row: (
                -row["_score"],
                0 if row["availability"] == "available" else 1,
                row["_sale"],
                row["name"],
            )
        )

    truncated = len(matches) > limit
    visible = matches[:limit]
    for row in visible:
        row.pop("_score", None)
        row.pop("_sale", None)

    return {
        "count": len(visible),
        "total_matches": len(matches),
        "truncated": truncated,
        "filters": {
            "query": query or None,
            "category": category,
            "max_price_brl": None if max_price is None else format_brl(max_price),
            "min_price_brl": None if min_price is None else format_brl(min_price),
            "in_stock_only": bool(in_stock_only),
            "on_promotion_only": bool(on_promotion_only),
            "strings": wanted_strings,
        },
        "products": visible,
    }


def get_product(product_id: int | str | None = None, name: str | None = None) -> dict:
    store = load_store()
    if product_id is not None and str(product_id).strip() != "":
        try:
            pid = int(product_id)
        except (TypeError, ValueError):
            return {"error": "product_id precisa ser numérico."}
        product = store.product_by_id.get(pid)
        if product is None:
            return {"error": f"Não há produto com id {pid}."}
        return {"product": _payload(store, product, detailed=True)}

    if not name or not str(name).strip():
        return {"error": "Informe product_id ou name."}

    tokens = tokenize(name)
    scored = []
    for product in store.products:
        score = _score(product, tokens)
        if score > 0:
            scored.append((score, product))
    scored.sort(key=lambda pair: (-pair[0], pair[1].name))
    if not scored:
        return {"error": f"Nenhum produto encontrado para '{name}'."}

    top_score, top = scored[0]
    second = scored[1][0] if len(scored) > 1 else -1
    clear_winner = len(scored) == 1 or top_score >= second + 8
    if clear_winner:
        return {"product": _payload(store, top, detailed=True)}

    return {
        "needs_disambiguation": True,
        "candidates": [_payload(store, product, detailed=False) for _, product in scored[:5]],
    }


def list_categories() -> dict:
    store = load_store()
    rows = []
    for category in sorted(store.categories.values(), key=lambda item: item.category_id):
        products = [product for product in store.products if product.category_id == category.category_id]
        rows.append(
            {
                "category_id": category.category_id,
                "name": category.name,
                "description": category.description,
                "products": len(products),
                "available": sum(1 for product in products if availability(product) == "available"),
            }
        )
    return {"categories": rows}


def list_active_promotions() -> dict:
    store = load_store()
    rows = []
    for product in store.products:
        promo = product.active_promotion
        if promo is None:
            continue
        payload = _payload(store, product, detailed=False)
        rows.append(payload)
    rows.sort(key=lambda row: row["name"])
    return {
        "count": len(rows),
        "note": "Somente promoções com is_active = 1. O desconto de PIX não acumula com estas.",
        "promotions": rows,
    }


def _payload(store: Store, product: Product, *, detailed: bool) -> dict:
    promo = product.active_promotion
    price = sale_price(product)
    pix = pix_price(product)
    conflict = description_conflicts(product)
    shared = store.specs_are_shared(product)
    payload: dict = {
        "product_id": product.product_id,
        "name": product.name,
        "category": product.category_name,
        "list_price_label": format_brl(product.list_price),
        "sale_price_label": format_brl(price),
        "promotion": _promo_dict(promo),
        "pix_price_label": None if pix is None else format_brl(pix),
        "pix_discount_applies": pix is not None,
        "stock_quantity": product.stock_quantity,
        "status": product.status,
        "availability": availability(product),
        "availability_label": AVAILABILITY_LABELS.get(availability(product), product.status),
        "description_conflicts_with_name": conflict,
        "specs_are_shared": shared,
    }
    if conflict:
        payload["catalog_warning"] = CATALOG_WARNING
    elif shared:
        payload["catalog_warning"] = SHARED_SPECS_WARNING
        payload["description"] = product.description
    else:
        payload["description"] = product.description
        if detailed:
            payload["specs"] = product.specs
    if detailed:
        payload["inactive_promotions"] = [_promo_dict(item) for item in product.inactive_promotions]
        if product.created_at is not None:
            payload["created_at"] = product.created_at.isoformat()
    return payload


def _promo_dict(promo: Promotion | None) -> dict | None:
    if promo is None:
        return None
    return {
        "promotion_id": promo.promotion_id,
        "name": promo.description,
        "discount_percent": percent_number(promo.discount_percent),
        "is_active": promo.is_active,
    }


def _score(product: Product, tokens: list[str]) -> int:
    if not tokens:
        return 0
    total = 0
    for token in tokens:
        hit = _token_score(product, token)
        if hit <= 0:
            return 0
        total += hit
    return total


def _token_score(product: Product, token: str) -> int:
    name = fold(product.name)
    name_words = re.findall(r"[a-z0-9]+", name)
    compact_name = re.sub(r"[^a-z0-9]", "", name)
    if token in name_words:
        return 12
    if len(token) >= 4 and token in compact_name:
        return 9
    if token in fold(product.category_name):
        return 4
    if token in fold(product.description):
        return 3
    specs = fold(json.dumps(product.specs, ensure_ascii=False))
    if token in specs:
        return 2
    return 0


def _resolve_categories(store: Store, category: str | None) -> tuple[set[int] | None, dict | None]:
    if category is None or str(category).strip() == "":
        return None, None
    text = str(category).strip()
    if text.isdigit():
        cid = int(text)
        if cid not in store.categories:
            return None, {"error": f"Categoria {cid} não existe.", "categories": _names(store)}
        return {cid}, None
    key = fold(text)
    if key in CATEGORY_ALIASES:
        return set(CATEGORY_ALIASES[key]), None
    hits = []
    for item in store.categories.values():
        name = fold(item.name)
        if key == name or key in name:
            hits.append(item.category_id)
    if hits:
        return set(hits), None
    return None, {
        "error": f"Não reconheci a categoria '{category}'.",
        "categories": _names(store),
    }


def _names(store: Store) -> list[str]:
    return [category.name for category in sorted(store.categories.values(), key=lambda item: item.category_id)]


def _accessory_only(tokens: list[str]) -> bool:
    blocked = {
        "ampli",
        "amplificador",
        "amplificadores",
        "amplis",
        "cabo",
        "cabos",
        "case",
        "cases",
        "corda",
        "cordas",
        "encordoamento",
        "encordoamentos",
        "palheta",
        "palhetas",
        "pedal",
        "pedais",
    }
    return bool(tokens) and all(token in blocked for token in tokens)


def _normalize_strings(value: str | None) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    key = fold(str(value))
    if key in {"nylon", "nailon"}:
        return "nylon"
    if key in {"steel", "aco"}:
        return "steel"
    return None
