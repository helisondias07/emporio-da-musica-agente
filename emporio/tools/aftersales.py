"""Deterministic exchange, regret, and warranty windows.

The model is not asked to do the calendar math. Dates follow the Civil Code
convention used in the manual's wording: the start day is excluded and the
deadline day counts, which is the same as anchor + N days, inclusive.
"""

from __future__ import annotations

from datetime import date, timedelta

from emporio.config import parse_date, reference_today
from emporio.data.loader import load_store
from emporio.tools.orders import lookup_order

REGRET_DAYS = 7
PREFERENCE_DAYS = 7
DEFECT_DAYS = 30
LEGAL_WARRANTY_DAYS = 90


def evaluate_aftersales(
    order_id: int | str | None = None,
    receipt_date: str | None = None,
    purchase_date: str | None = None,
    channel: str | None = None,
) -> dict:
    today = reference_today()
    order_payload = None
    assumed_channel = False
    purchase: date | None = None
    receipt: date | None = None
    receipt_assumed = False
    errors = []

    if purchase_date:
        try:
            purchase = parse_date(purchase_date)
        except ValueError as exc:
            errors.append(str(exc))
    if receipt_date:
        try:
            receipt = parse_date(receipt_date)
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        return {"error": " ".join(errors)}

    if order_id is not None and str(order_id).strip() != "":
        looked = lookup_order(order_id=order_id)
        if "error" in looked:
            return looked
        order_payload = looked["orders"][0]
        if purchase is None:
            purchase = parse_date(order_payload["order_date"])
        if channel is None:
            channel = "online"
            assumed_channel = True
        if receipt is None and order_payload["status"] == "delivered" and order_payload["estimated_delivery"]:
            receipt = parse_date(order_payload["estimated_delivery"])
            receipt_assumed = True

    channel_key = (channel or "").strip().lower()
    if channel_key in {"loja", "presencial", "in_store", "balcao", "balcão"}:
        channel_key = "in_store"
    elif channel_key in {"online", "site", "distancia", "distância", "whatsapp"}:
        channel_key = "online"
    elif channel_key == "":
        channel_key = ""

    result = {
        "reference_today": today.isoformat(),
        "order": _order_brief(order_payload),
        "channel": channel_key or None,
        "channel_assumed_from_order_table": assumed_channel,
        "purchase_date": purchase.isoformat() if purchase else None,
        "receipt_date": receipt.isoformat() if receipt else None,
        "receipt_date_assumed_from_estimate": receipt_assumed,
        "regret": _regret(today, receipt, channel_key, order_payload),
        "preference_exchange": _preference(today, receipt, purchase, channel_key),
        "defect_exchange": _defect(today, purchase, order_payload),
        "legal_warranty": _warranty(today, receipt),
        "always_mention": [
            "Produto sem uso, na embalagem original, com manuais.",
            "Mau uso, queda, umidade e modificação não autorizada ficam de fora.",
            "Instrumento personalizado ou de liquidação com aviso de venda final não entra em troca por preferência.",
            "Boquilha de sopro não entra em troca, por higiene.",
        ],
    }
    if order_payload and order_payload["status"] == "cancelled":
        result["blocked_reason"] = order_payload.get("notes") or "Pedido cancelado."
    return result


def _order_brief(order: dict | None) -> dict | None:
    if order is None:
        return None
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "status_label": order["status_label"],
        "order_date": order["order_date"],
        "total_label": order["total_label"],
        "payment_label": order["payment_label"],
        "items": order["items"],
    }


def _window(today: date, anchor: date | None, days: int, assumed: bool, rule: str, missing: list[str]) -> dict:
    if anchor is None:
        return {
            "within_time_window": None,
            "deadline": None,
            "anchor_date": None,
            "anchor_is_assumed": False,
            "days_since_anchor": None,
            "rule": rule,
            "missing": missing,
        }
    deadline = anchor + timedelta(days=days)
    return {
        "within_time_window": today <= deadline,
        "deadline": deadline.isoformat(),
        "anchor_date": anchor.isoformat(),
        "anchor_is_assumed": assumed,
        "days_since_anchor": (today - anchor).days,
        "rule": rule,
        "missing": [],
    }


def _regret(today, receipt, channel, order) -> dict:
    rule = (
        "Arrependimento: compras online, até 7 dias corridos após o recebimento, "
        "sem precisar justificar. Reembolso na mesma forma de pagamento em até 10 dias úteis. "
        "O frete da devolução é da loja."
    )
    if order and order["status"] == "cancelled":
        return {**_window(today, None, REGRET_DAYS, False, rule, []), "within_time_window": False, "reason": "Pedido cancelado."}
    if order and order["status"] in {"pending", "confirmed"}:
        return {
            **_window(today, None, REGRET_DAYS, False, rule, ["receipt_date"]),
            "reason": "Pedido ainda não enviado. O prazo de 7 dias só começa no recebimento.",
        }
    if channel == "in_store":
        return {
            "within_time_window": False,
            "deadline": None,
            "anchor_date": None,
            "anchor_is_assumed": False,
            "days_since_anchor": None,
            "rule": rule,
            "missing": [],
            "reason": "O manual concede o direito de arrependimento sem justificativa às compras online, não à compra de balcão.",
        }
    if channel not in {"online", ""}:
        return _window(today, None, REGRET_DAYS, False, rule, ["channel"])
    missing = []
    if not channel:
        missing.append("channel")
    if receipt is None:
        missing.append("receipt_date")
    if missing:
        base = _window(today, None, REGRET_DAYS, False, rule, missing)
        return base
    return _window(today, receipt, REGRET_DAYS, False, rule, [])


def _preference(today, receipt, purchase, channel) -> dict:
    rule = (
        "Troca por preferência (cor, modelo, tamanho): até 7 dias, produto perfeito na embalagem original, "
        "se o modelo desejado estiver disponível. Diferença de valor é cobrada ou devolvida."
    )
    if channel == "in_store":
        anchor, assumed = purchase, False
        missing = ["purchase_date"] if purchase is None else []
    elif channel == "online":
        anchor, assumed = receipt, False
        missing = ["receipt_date"] if receipt is None else []
    else:
        anchor = receipt or purchase
        assumed = False
        missing = ["channel"]
        if anchor is None:
            missing.append("receipt_date")
    if missing and anchor is None:
        return _window(today, None, PREFERENCE_DAYS, assumed, rule, missing)
    return _window(today, anchor, PREFERENCE_DAYS, assumed, rule, [] if anchor else missing)


def _defect(today, purchase, order) -> dict:
    rule = (
        "Defeito de fabricação: a loja troca em até 30 dias corridos após a compra. "
        "Depois disso o cliente aciona o fabricante, e a loja pode intermediar."
    )
    if purchase is None:
        return _window(today, None, DEFECT_DAYS, False, rule, ["purchase_date"])
    window = _window(today, purchase, DEFECT_DAYS, False, rule, [])
    if order and order["status"] == "cancelled":
        window["within_time_window"] = False
        window["reason"] = "Pedido cancelado."
    elif not window["within_time_window"]:
        window["next_step"] = "Acionar a garantia do fabricante. A loja pode intermediar se o cliente pedir."
    return window


def _warranty(today, receipt) -> dict:
    rule = (
        "Garantia legal: 90 dias contra defeito de fabricação, contados do recebimento. "
        "A garantia de fabricante varia de 6 meses a 2 anos e está no certificado; não invente o prazo de uma marca."
    )
    if receipt is None:
        return _window(today, None, LEGAL_WARRANTY_DAYS, False, rule, ["receipt_date"])
    return _window(today, receipt, LEGAL_WARRANTY_DAYS, False, rule, [])
