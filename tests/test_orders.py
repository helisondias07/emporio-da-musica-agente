"""Orders and the aftersales calendar."""

import json

from emporio.tools.aftersales import evaluate_aftersales
from emporio.tools.orders import lookup_order


def test_order_by_id_and_by_tracking():
    by_id = lookup_order(order_id=8)["orders"][0]
    by_code = lookup_order(tracking_code="brjl5544332br")["orders"][0]
    assert by_id["order_id"] == by_code["order_id"] == 8
    assert by_id["status"] == "shipped"
    assert by_id["tracking_code"] == "BRJL5544332BR"
    assert by_id["total_label"] == "R$ 349,90"
    assert by_id["items"][0]["name"] == "Kala KA-C Concert Mogno"
    assert by_id["days_from_estimated_delivery"] == 25
    assert by_id["estimate_is_past"] is True
    assert by_id["customer"]["email_hint"].startswith("a***@")
    assert "99654" not in json.dumps(by_id)


def test_ambiguous_customer_does_not_leak_orders():
    result = lookup_order(customer_name="Pedro")
    assert result["needs_disambiguation"] is True
    assert len(result["customers"]) >= 2
    blob = json.dumps(result)
    assert "orders" not in result
    assert "BRAB1234567BR" not in blob


def test_full_name_returns_that_customers_orders_only():
    result = lookup_order(customer_name="Ana Carolina")
    assert [order["order_id"] for order in result["orders"]] == [8]


def test_order_7_windows_on_the_reference_date():
    result = evaluate_aftersales(order_id=7, receipt_date="17/02/2026")
    assert result["order"]["status"] == "delivered"
    assert result["order"]["total_label"] == "R$ 159,90"
    assert result["order"]["items"][0]["name"] == "Shelby SU-21S Soprano Sunburst"
    assert result["regret"]["within_time_window"] is False
    assert result["regret"]["deadline"] == "2026-02-24"
    assert result["preference_exchange"]["within_time_window"] is False
    assert result["defect_exchange"]["within_time_window"] is False
    assert result["defect_exchange"]["deadline"] == "2026-03-05"
    assert result["legal_warranty"]["within_time_window"] is True
    assert result["legal_warranty"]["deadline"] == "2026-05-18"


def test_regret_window_open_the_day_after_receipt(monkeypatch):
    monkeypatch.setenv("EMPORIO_TODAY", "2026-02-18")
    result = evaluate_aftersales(order_id=7, receipt_date="2026-02-17")
    assert result["regret"]["within_time_window"] is True
    assert result["reference_today"] == "2026-02-18"


def test_in_store_regret_is_not_the_online_right():
    result = evaluate_aftersales(channel="in_store", receipt_date="2026-03-24", purchase_date="2026-03-24")
    assert result["regret"]["within_time_window"] is False
    assert "online" in result["regret"]["reason"]
