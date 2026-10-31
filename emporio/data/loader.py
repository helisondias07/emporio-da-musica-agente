"""Load the CSVs into a Store. Parsing is strict: bad money or JSON fails fast."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from emporio.config import data_dir, parse_date
from emporio.data import Category, Customer, Order, OrderItem, Product, Promotion, Store, _spec_key
from emporio.money import parse_decimal

_CACHE: Store | None = None


def load_store(*, force: bool = False) -> Store:
    global _CACHE
    if _CACHE is None or force:
        _CACHE = _read_store(data_dir())
    return _CACHE


def _read_store(folder) -> Store:
    categories = {
        row.category_id: row
        for row in (_category(raw) for raw in _rows(folder / "categories.csv"))
    }
    promotions = [_promotion(raw) for raw in _rows(folder / "promotions.csv")]
    by_product: dict[int, list[Promotion]] = {}
    for promo in promotions:
        by_product.setdefault(promo.product_id, []).append(promo)

    products = []
    for raw in _rows(folder / "products.csv"):
        product = _product(raw, categories)
        product.promotions = tuple(by_product.get(product.product_id, []))
        products.append(product)

    customers = [_customer(raw) for raw in _rows(folder / "customers.csv")]
    items_by_order: dict[int, list[OrderItem]] = {}
    for raw in _rows(folder / "order_items.csv"):
        item = _item(raw)
        items_by_order.setdefault(item.order_id, []).append(item)

    orders = []
    for raw in _rows(folder / "orders.csv"):
        order = _order(raw)
        order.items = tuple(items_by_order.get(order.order_id, []))
        orders.append(order)

    spec_counts: dict[str, int] = {}
    for product in products:
        key = _spec_key(product.specs)
        spec_counts[key] = spec_counts.get(key, 0) + 1

    store = Store(
        categories=categories,
        products=products,
        customers=customers,
        orders=orders,
        promotions=promotions,
        spec_counts=spec_counts,
    )
    _check_references(store)
    return store


def _rows(path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _category(raw: dict[str, str]) -> Category:
    return Category(
        category_id=int(raw["category_id"]),
        name=raw["name"].strip(),
        description=raw["description"].strip(),
    )


def _promotion(raw: dict[str, str]) -> Promotion:
    flag = raw["is_active"].strip()
    if flag not in {"0", "1"}:
        raise ValueError(f"is_active inválido na promoção {raw['promotion_id']}: {flag}")
    return Promotion(
        promotion_id=int(raw["promotion_id"]),
        product_id=int(raw["product_id"]),
        discount_percent=parse_decimal(raw["discount_percent"]),
        description=raw["description"].strip(),
        is_active=flag == "1",
    )


def _product(raw: dict[str, str], categories: dict[int, Category]) -> Product:
    category_id = int(raw["category_id"])
    category = categories.get(category_id)
    if category is None:
        raise ValueError(f"Produto {raw['product_id']} aponta para categoria {category_id} inexistente.")
    try:
        specs = json.loads(raw["specs"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"specs inválido no produto {raw['product_id']}") from exc
    created = raw["created_at"].strip()
    return Product(
        product_id=int(raw["product_id"]),
        name=raw["name"].strip(),
        category_id=category_id,
        category_name=category.name,
        description=raw["description"].strip(),
        list_price=parse_decimal(raw["price_brl"]),
        stock_quantity=int(raw["stock_quantity"]),
        status=raw["status"].strip().lower(),
        specs=specs,
        created_at=datetime.strptime(created, "%Y-%m-%d").date() if created else None,
    )


def _customer(raw: dict[str, str]) -> Customer:
    return Customer(
        customer_id=int(raw["customer_id"]),
        name=raw["name"].strip(),
        phone=raw["phone"].strip(),
        email=raw["email"].strip(),
        city=raw["city"].strip(),
    )


def _item(raw: dict[str, str]) -> OrderItem:
    return OrderItem(
        order_id=int(raw["order_id"]),
        product_id=int(raw["product_id"]),
        quantity=int(raw["quantity"]),
    )


def _order(raw: dict[str, str]) -> Order:
    tracking = raw["tracking_code"].strip()
    estimate = raw["estimated_delivery"].strip()
    notes = raw["notes"].strip()
    return Order(
        order_id=int(raw["order_id"]),
        customer_id=int(raw["customer_id"]),
        order_date=parse_date(raw["order_date"]),
        status=raw["status"].strip().lower(),
        total=parse_decimal(raw["total_brl"]),
        payment_method=raw["payment_method"].strip(),
        tracking_code=tracking or None,
        estimated_delivery=parse_date(estimate) if estimate else None,
        notes=notes or None,
    )


def _check_references(store: Store) -> None:
    for promo in store.promotions:
        if promo.product_id not in store.product_by_id:
            raise ValueError(f"Promoção {promo.promotion_id} aponta para produto {promo.product_id} inexistente.")
    for order in store.orders:
        if order.customer_id not in store.customer_by_id:
            raise ValueError(f"Pedido {order.order_id} aponta para cliente {order.customer_id} inexistente.")
        for item in order.items:
            if item.product_id not in store.product_by_id:
                raise ValueError(
                    f"Pedido {order.order_id} aponta para produto {item.product_id} inexistente."
                )
