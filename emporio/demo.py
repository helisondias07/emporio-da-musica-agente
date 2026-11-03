"""Offline demo. Runs the real tools and the PDF check. No API key."""

from __future__ import annotations

from emporio.config import reference_today
from emporio.data.loader import load_store
from emporio.data.quality import conflicting_product_ids
from emporio.retrieval.policies import policy_alignment, search_policies
from emporio.tools.aftersales import evaluate_aftersales
from emporio.tools.catalog import get_product, list_active_promotions, search_products
from emporio.tools.orders import lookup_order
from emporio.scope import analyze_scope


def main() -> int:
    store = load_store()
    today = reference_today().isoformat()
    alignment = policy_alignment()
    guitars = search_products(category="violao", max_price_brl=1000, in_stock_only=True)
    gaps = search_products(category="violao", max_price_brl=1000, in_stock_only=False)
    takamine = get_product(name="Takamine GD20")["product"]
    promotions = list_active_promotions()["promotions"]
    order_8 = lookup_order(order_id=8)["orders"][0]
    windows = evaluate_aftersales(order_id=7, receipt_date="2026-02-17")
    address = search_policies(topic="address")
    hours = search_policies(topic="hours")

    print("Empório da Música — offline demo (no LLM call)")
    print(f"Reference date: {today}")
    print(
        f"Rows: {len(store.products)} products, {len(store.orders)} orders, "
        f"{len(store.customers)} customers, {sum(promo.is_active for promo in store.promotions)} active promotions"
    )
    print(f"Description/name brand conflicts: {conflicting_product_ids(store.products)}")
    print(f"Policy phrases aligned with the PDF: {alignment['ok']}")
    if not alignment["ok"]:
        print(alignment)
        return 1

    print("\n1. Available violões up to R$ 1.000,00")
    print(f"   {guitars['count']} instruments")
    for product in guitars["products"]:
        print(f"   - {product['sale_price_label']:>14}  stock {product['stock_quantity']:<2}  {product['name']}")
    print("   Not for sale inside the same price cap:")
    for product in gaps["products"]:
        if product["availability"] != "available":
            print(f"   - {product['availability']:<13} {product['sale_price_label']:>14}  {product['name']}")

    print("\n2. Address and hours")
    for section in address["sections"] + hours["sections"]:
        print(f"   [{section['id']}] {section['heading']}")

    print("\n3. Takamine GD20")
    print(f"   id {takamine['product_id']}  sale {takamine['sale_price_label']}  PIX {takamine['pix_price_label']}")
    print(f"   stock {takamine['stock_quantity']}  active promo {takamine['promotion']}")
    print(f"   inactive promos {takamine['inactive_promotions']}")

    print("\n4. Active promotions")
    for product in promotions:
        promo = product["promotion"]
        print(
            f"   - {product['name']}: {product['list_price_label']} -> {product['sale_price_label']} "
            f"({promo['discount_percent']}% {promo['name']})"
        )

    print("\n5. Order 7 aftersales, receipt 2026-02-17")
    for key in ("regret", "preference_exchange", "defect_exchange", "legal_warranty"):
        window = windows[key]
        print(
            f"   {key}: within={window['within_time_window']} deadline={window['deadline']} "
            f"days={window['days_since_anchor']}"
        )

    print("\n6. Order 8")
    print(
        f"   {order_8['status_label']}  {order_8['tracking_code']}  "
        f"estimate {order_8['estimated_delivery']}  "
        f"days_from_estimate {order_8['days_from_estimated_delivery']}  "
        f"total {order_8['total_label']}  {order_8['items'][0]['name']}"
    )

    accessory = analyze_scope("vocês têm corda de aço e um amplificador?")
    instrument = analyze_scope("quero um violão de cordas de aço até 1000")
    print("\n7. Scope")
    print(f"   accessory message -> {accessory.kind} {accessory.accessories}")
    print(f"   steel-string guitar -> {instrument.kind} {instrument.accessories}")

    checks = [
        guitars["count"] == 12,
        takamine["sale_price_label"] == "R$ 2.199,00",
        takamine["pix_price_label"] == "R$ 2.089,05",
        takamine["promotion"] is None,
        len(promotions) == 4,
        windows["regret"]["within_time_window"] is False,
        windows["legal_warranty"]["within_time_window"] is True,
        windows["legal_warranty"]["deadline"] == "2026-05-18",
        order_8["tracking_code"] == "BRJL5544332BR",
        order_8["days_from_estimated_delivery"] == 25,
        accessory.kind == "accessory",
        instrument.kind == "in_scope",
        alignment["ok"],
    ]
    if not all(checks):
        print("\nDemo self-check failed.")
        return 1
    print("\nDemo self-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
