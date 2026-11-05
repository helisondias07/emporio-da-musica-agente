"""Loader, money, and catalog quality."""

from decimal import Decimal

from emporio.data.loader import load_store
from emporio.data.quality import conflicting_product_ids
from emporio.money import format_brl


def test_tables_and_foreign_keys():
    store = load_store()
    assert len(store.products) == 65
    assert len(store.categories) == 9
    assert len(store.customers) == 50
    assert len(store.orders) == 20
    assert sum(len(order.items) for order in store.orders) == 22
    assert sum(promo.is_active for promo in store.promotions) == 4
    assert {product.status for product in store.products} == {"active", "discontinued", "coming_soon"}


def test_brand_conflicts_are_the_known_rows():
    store = load_store()
    assert conflicting_product_ids(store.products) == [135, 137, 139, 140, 142, 144]


def test_currency_labels():
    assert format_brl(Decimal("2199")) == "R$ 2.199,00"
    assert format_brl(Decimal("599.9")) == "R$ 599,90"
    assert format_brl(Decimal("2089.05")) == "R$ 2.089,05"
