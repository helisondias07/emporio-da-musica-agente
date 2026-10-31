"""Order lookup. Customer phone and email leave this tool already masked."""

from __future__ import annotations

import re

from emporio.config import reference_today
from emporio.data.loader import load_store
from emporio.money import format_brl
from emporio.text import fold, tokenize
from emporio.tools.catalog import availability

PAYMENT_LABELS = {
    "pix": "PIX",
    "debit": "cartão de débito",
    "boleto": "boleto bancário",
    "credit_3x": "cartão de crédito em 3x",
    "credit_6x": "cartão de crédito em 6x",
    "credit_12x": "cartão de crédito em 12x",
}

STATUS_LABELS = {
    "pending": "pendente",
    "confirmed": "confirmado",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}


def lookup_order(
    order_id: int | str | None = None,
    tracking_code: str | None = None,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    customer_email: str | None = None,
) -> dict:
    store = load_store()
    if order_id is not None and str(order_id).strip() != "":
        try:
            oid = int(order_id)
        except (TypeError, ValueError):
            return {"error": "order_id precisa ser numérico."}
        order = store.order_by_id.get(oid)
        if order is None:
            return {"error": f"Não há pedido {oid}."}
        return {"orders": [_order_payload(store, order)]}

    if tracking_code and str(tracking_code).strip():
        needle = re.sub(r"\s+", "", str(tracking_code)).upper()
        found = [
            order
            for order in store.orders
            if order.tracking_code and order.tracking_code.upper() == needle
        ]
        if not found:
            return {"error": f"Nenhum pedido com rastreio {tracking_code}."}
        return {"orders": [_order_payload(store, order) for order in found]}

    customers = _match_customers(store, customer_name, customer_phone, customer_email)
    if isinstance(customers, dict):
        return customers
    if len(customers) == 0:
        return {"error": "Nenhum cliente encontrado com esses dados."}
    if len(customers) > 1:
        return {
            "needs_disambiguation": True,
            "message": "Mais de um cliente combina com a busca. Peça o número do pedido ou o telefone completo.",
            "customers": [_customer_hint(customer) for customer in customers],
        }

    customer = customers[0]
    orders = [order for order in store.orders if order.customer_id == customer.customer_id]
    orders.sort(key=lambda order: order.order_date, reverse=True)
    return {
        "customer": _customer_hint(customer),
        "orders": [_order_payload(store, order) for order in orders],
    }


def _match_customers(store, name, phone, email):
    if not any(value and str(value).strip() for value in (name, phone, email)):
        return {"error": "Informe order_id, tracking_code, customer_name, customer_phone ou customer_email."}

    chosen = list(store.customers)
    if email and str(email).strip():
        needle = str(email).strip().casefold()
        chosen = [customer for customer in chosen if customer.email.casefold() == needle]
    if phone and str(phone).strip():
        digits = re.sub(r"\D", "", str(phone))
        if len(digits) < 8:
            return {"error": "Informe o telefone com pelo menos 8 dígitos para não misturar clientes."}
        chosen = [customer for customer in chosen if re.sub(r"\D", "", customer.phone).endswith(digits)]
    if name and str(name).strip():
        tokens = tokenize(name)
        if not tokens:
            return {"error": "Nome de cliente vazio demais para buscar."}
        chosen = [
            customer
            for customer in chosen
            if all(token in fold(customer.name) for token in tokens)
        ]
    return chosen


def _customer_hint(customer) -> dict:
    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "city": customer.city,
        "phone_hint": _mask_phone(customer.phone),
        "email_hint": _mask_email(customer.email),
    }


def _mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    tail = digits[-4:] if len(digits) >= 4 else digits
    return f"final {tail}"


def _mask_email(email: str) -> str:
    user, _, domain = email.partition("@")
    prefix = user[:1] if user else ""
    return f"{prefix}***@{domain}" if domain else ""


def _order_payload(store, order) -> dict:
    customer = store.customer_by_id[order.customer_id]
    today = reference_today()
    items = []
    for item in order.items:
        product = store.product_by_id.get(item.product_id)
        items.append(
            {
                "product_id": item.product_id,
                "name": product.name if product else f"produto {item.product_id}",
                "quantity": item.quantity,
                "current_availability": availability(product) if product else "unknown",
            }
        )
    payload = {
        "order_id": order.order_id,
        "order_date": order.order_date.isoformat(),
        "status": order.status,
        "status_label": STATUS_LABELS.get(order.status, order.status),
        "total_label": format_brl(order.total),
        "payment_method": order.payment_method,
        "payment_label": PAYMENT_LABELS.get(order.payment_method, order.payment_method),
        "tracking_code": order.tracking_code,
        "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
        "notes": order.notes,
        "customer": _customer_hint(customer),
        "items": items,
        "reference_today": today.isoformat(),
        "channel_assumption": (
            "Pedidos desta base são tratados como venda à distância: a tabela tem frete, "
            "rastreio ou estimativa de entrega, e não há coluna de venda de balcão."
        ),
    }
    if order.estimated_delivery is not None:
        payload["days_from_estimated_delivery"] = (today - order.estimated_delivery).days
        payload["estimate_is_past"] = today > order.estimated_delivery and order.status not in {
            "delivered",
            "cancelled",
        }
    if order.status == "cancelled":
        payload["service_note"] = "Pedido cancelado. Não há produto em trânsito para devolver."
    elif order.status in {"pending", "confirmed"}:
        payload["service_note"] = (
            "Pedido ainda não enviado. Cancelamento com a loja é o caminho, não a devolução de 7 dias, "
            "que começa depois do recebimento."
        )
    elif order.status == "shipped":
        payload["service_note"] = (
            "Pedido enviado e ainda não marcado como entregue. Não assuma a data de recebimento."
        )
    return payload
