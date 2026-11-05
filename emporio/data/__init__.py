"""In-memory records loaded from the store CSVs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class Category:
    category_id: int
    name: str
    description: str


@dataclass
class Promotion:
    promotion_id: int
    product_id: int
    discount_percent: Decimal
    description: str
    is_active: bool


@dataclass
class Product:
    product_id: int
    name: str
    category_id: int
    category_name: str
    description: str
    list_price: Decimal
    stock_quantity: int
    status: str
    specs: dict
    created_at: date | None
    promotions: tuple[Promotion, ...] = ()

    @property
    def active_promotion(self) -> Promotion | None:
        active = [promo for promo in self.promotions if promo.is_active]
        if not active:
            return None
        return max(active, key=lambda promo: promo.discount_percent)

    @property
    def inactive_promotions(self) -> tuple[Promotion, ...]:
        return tuple(promo for promo in self.promotions if not promo.is_active)


@dataclass
class Customer:
    customer_id: int
    name: str
    phone: str
    email: str
    city: str


@dataclass
class OrderItem:
    order_id: int
    product_id: int
    quantity: int


@dataclass
class Order:
    order_id: int
    customer_id: int
    order_date: date
    status: str
    total: Decimal
    payment_method: str
    tracking_code: str | None
    estimated_delivery: date | None
    notes: str | None
    items: tuple[OrderItem, ...] = field(default_factory=tuple)


@dataclass
class Store:
    categories: dict[int, Category]
    products: list[Product]
    customers: list[Customer]
    orders: list[Order]
    promotions: list[Promotion]
    spec_counts: dict[str, int]

    def __post_init__(self) -> None:
        self.product_by_id = {product.product_id: product for product in self.products}
        self.customer_by_id = {customer.customer_id: customer for customer in self.customers}
        self.order_by_id = {order.order_id: order for order in self.orders}

    def specs_are_shared(self, product: Product) -> bool:
        return self.spec_counts.get(_spec_key(product.specs), 0) > 1


def _spec_key(specs: dict) -> str:
    import json

    return json.dumps(specs, sort_keys=True, ensure_ascii=False)
