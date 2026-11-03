"""OpenAI-style tool schemas and the dispatcher the agent loop calls."""

from __future__ import annotations

import json

from emporio.retrieval.policies import search_policies
from emporio.tools.aftersales import evaluate_aftersales
from emporio.tools.catalog import get_product, list_active_promotions, list_categories, search_products
from emporio.tools.orders import lookup_order

_SEARCH_PRODUCTS = {
    "name": "search_products",
    "description": (
        "Busca instrumentos no catálogo (preço de venda, estoque, categoria, promoção ativa). "
        "Use para listas, filtros e disponibilidade. Não use para acessório."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Marca, modelo ou termo. Ex.: 'Takamine', 'iniciante'."},
            "category": {
                "type": "string",
                "description": "violao, guitarra, baixo, bateria, teclado, ukulele, sopro ou o nome da categoria.",
            },
            "max_price_brl": {"type": "number", "description": "Preço máximo de venda, em reais."},
            "min_price_brl": {"type": "number", "description": "Preço mínimo de venda, em reais."},
            "in_stock_only": {
                "type": "boolean",
                "description": "True quando o cliente pediu opções disponíveis para comprar agora.",
            },
            "on_promotion_only": {"type": "boolean", "description": "True para listar só o que tem promoção ativa."},
            "strings": {"type": "string", "enum": ["nylon", "steel"], "description": "nylon ou steel (aço)."},
            "limit": {"type": "integer", "description": "Máximo de itens, até 40."},
        },
        "additionalProperties": False,
    },
}

_GET_PRODUCT = {
    "name": "get_product",
    "description": "Detalhe de um instrumento: preço, PIX, estoque, promoção ativa e promoções inativas.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {"type": "integer"},
            "name": {"type": "string", "description": "Nome ou modelo, ex. 'Takamine GD20'."},
        },
        "additionalProperties": False,
    },
}

_LIST_CATEGORIES = {
    "name": "list_categories",
    "description": "Lista as categorias da loja e quantos instrumentos estão disponíveis em cada uma.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

_LIST_PROMOTIONS = {
    "name": "list_active_promotions",
    "description": "Promoções com is_active verdadeiro. Não inclui campanha vencida.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

_LOOKUP_ORDER = {
    "name": "lookup_order",
    "description": (
        "Status de pedido por id, código de rastreio ou cliente. "
        "Telefone e e-mail voltam mascarados. Se o nome for ambíguo, não devolve pedidos."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "integer"},
            "tracking_code": {"type": "string"},
            "customer_name": {"type": "string"},
            "customer_phone": {"type": "string"},
            "customer_email": {"type": "string"},
        },
        "additionalProperties": False,
    },
}

_AFTERSALES = {
    "name": "evaluate_aftersales",
    "description": (
        "Calcula se o prazo de arrependimento, troca por preferência, troca por defeito "
        "e garantia legal ainda está aberto. Use sempre que a pergunta for 'posso devolver'. "
        "Não faça essa conta você mesmo."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "integer"},
            "receipt_date": {"type": "string", "description": "Data em que o cliente recebeu. AAAA-MM-DD ou DD/MM/AAAA."},
            "purchase_date": {"type": "string", "description": "Data da compra, se não houver order_id."},
            "channel": {"type": "string", "description": "online ou in_store. Pedido da base é tratado como online."},
        },
        "additionalProperties": False,
    },
}

_POLICIES = {
    "name": "search_policies",
    "description": (
        "Trechos do manual de políticas: horário, endereço, pagamento, troca, frete, garantia, "
        "WhatsApp, privacidade. Use antes de explicar uma regra."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Pergunta do cliente, com as palavras dele."},
            "topic": {
                "type": "string",
                "enum": [
                    "about",
                    "address",
                    "hours",
                    "payment",
                    "returns",
                    "shipping",
                    "promotions",
                    "whatsapp",
                    "warranty",
                    "privacy",
                    "scope",
                ],
            },
            "limit": {"type": "integer"},
        },
        "additionalProperties": False,
    },
}

TOOL_SPECS = [
    _SEARCH_PRODUCTS,
    _GET_PRODUCT,
    _LIST_CATEGORIES,
    _LIST_PROMOTIONS,
    _LOOKUP_ORDER,
    _AFTERSALES,
    _POLICIES,
]

OPENAI_TOOLS = [{"type": "function", "function": spec} for spec in TOOL_SPECS]

_FUNCTIONS = {
    "search_products": search_products,
    "get_product": get_product,
    "list_categories": list_categories,
    "list_active_promotions": list_active_promotions,
    "lookup_order": lookup_order,
    "evaluate_aftersales": evaluate_aftersales,
    "search_policies": search_policies,
}

_SCHEMAS = {spec["name"]: spec for spec in TOOL_SPECS}


def dispatch(name: str, arguments: dict | str | None) -> dict:
    if name not in _FUNCTIONS:
        return {"error": f"Ferramenta desconhecida: {name}"}
    raw = _load_args(arguments)
    if isinstance(raw, dict) and "error" in raw and len(raw) == 1:
        return raw
    try:
        cleaned = _coerce(name, raw)
        return _FUNCTIONS[name](**cleaned)
    except TypeError as exc:
        return {"error": f"Argumentos inválidos para {name}: {exc}"}
    except ValueError as exc:
        return {"error": str(exc)}


def _load_args(arguments: dict | str | None) -> dict:
    if arguments is None or arguments == "":
        return {}
    if isinstance(arguments, dict):
        return arguments
    try:
        loaded = json.loads(arguments)
    except json.JSONDecodeError:
        return {"error": "Argumentos da ferramenta não são JSON válido."}
    if not isinstance(loaded, dict):
        return {"error": "Argumentos da ferramenta precisam ser um objeto JSON."}
    return loaded


def _coerce(name: str, arguments: dict) -> dict:
    properties = _SCHEMAS[name]["parameters"].get("properties", {})
    cleaned: dict = {}
    for key, value in arguments.items():
        if key not in properties or value is None:
            continue
        expected = properties[key].get("type")
        if isinstance(value, str) and value.strip() == "" and expected == "string":
            continue
        if expected == "boolean" and isinstance(value, str):
            value = value.strip().lower() in {"1", "true", "yes", "sim"}
        elif expected == "integer" and isinstance(value, str) and value.strip().lstrip("-").isdigit():
            value = int(value.strip())
        elif expected == "number" and isinstance(value, str):
            value = float(value.strip().replace(",", "."))
        cleaned[key] = value
    return cleaned
