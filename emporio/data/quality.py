"""Marca produto cuja descrição cita outra marca que não a do nome."""

from __future__ import annotations

from emporio.data import Product
from emporio.text import fold

# Longer names first so "Music Man" wins over a shorter token.
BRANDS = (
    "Music Man",
    "Takamine",
    "Giannini",
    "Yamaha",
    "Tagima",
    "Fender",
    "Gibson",
    "Ibanez",
    "Crafter",
    "Shelby",
    "Rozini",
    "Kalani",
    "Martin",
    "Taylor",
    "Roland",
    "Ohana",
    "Pearl",
    "Tama",
    "Korg",
    "Nord",
    "Kala",
    "PRS",
)


def brands_in(text: str) -> set[str]:
    padded = f" {fold(text)} "
    found: set[str] = set()
    for brand in sorted(BRANDS, key=len, reverse=True):
        if f" {fold(brand)} " in padded:
            found.add(brand)
    return found


def description_conflicts(product: Product) -> bool:
    name_brands = brands_in(product.name)
    description_brands = brands_in(product.description)
    if not name_brands or not description_brands:
        return False
    return name_brands.isdisjoint(description_brands)


def conflicting_product_ids(products: list[Product]) -> list[int]:
    return [product.product_id for product in products if description_conflicts(product)]
