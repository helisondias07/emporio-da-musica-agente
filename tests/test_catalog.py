"""Catalog search against the real product CSV."""

from emporio.tools.catalog import get_product, list_active_promotions, search_products


def test_violao_budget_returns_the_twelve_available_models():
    result = search_products(category="violões", max_price_brl=1000, in_stock_only=True)
    ids = [product["product_id"] for product in result["products"]]
    assert ids == [83, 85, 89, 88, 81, 84, 87, 86, 107, 82, 91, 112]
    assert result["products"][0]["sale_price_label"] == "R$ 429,90"
    assert result["products"][-1]["sale_price_label"] == "R$ 999,00"


def test_same_price_cap_surfaces_out_of_stock_and_discontinued():
    result = search_products(category="violao", max_price_brl=1000, in_stock_only=False)
    by_id = {product["product_id"]: product for product in result["products"]}
    assert by_id[96]["availability"] == "out_of_stock"
    assert by_id[113]["availability"] == "discontinued"
    assert 96 not in {row["product_id"] for row in search_products(category="violao", max_price_brl=1000, in_stock_only=True)["products"]}


def test_coming_soon_is_not_for_sale_even_with_stock():
    result = search_products(query="KA-ABP-CTG", in_stock_only=False)
    product = result["products"][0]
    assert product["product_id"] == 130
    assert product["availability"] == "coming_soon"
    assert product["stock_quantity"] == 2
    stocked = search_products(query="KA-ABP-CTG", in_stock_only=True)
    assert stocked["total_matches"] == 0


def test_takamine_gd20_price_pix_and_inactive_offer():
    product = get_product(name="Takamine GD20")["product"]
    assert product["product_id"] == 95
    assert product["sale_price_label"] == "R$ 2.199,00"
    assert product["pix_price_label"] == "R$ 2.089,05"
    assert product["stock_quantity"] == 5
    assert product["promotion"] is None
    assert product["inactive_promotions"][0]["discount_percent"] == 12
    assert product["inactive_promotions"][0]["is_active"] is False
    assert product["description_conflicts_with_name"] is False


def test_active_promotions_are_only_the_live_four():
    rows = list_active_promotions()["promotions"]
    assert {(row["product_id"], row["promotion"]["discount_percent"], row["sale_price_label"]) for row in rows} == {
        (90, 18, "R$ 1.967,18"),
        (127, 10, "R$ 323,10"),
        (121, 20, "R$ 439,20"),
        (94, 8, "R$ 5.519,08"),
    }
    crafter = next(row for row in rows if row["product_id"] == 90)
    assert crafter["pix_price_label"] is None
    assert crafter["pix_discount_applies"] is False


def test_conflicting_description_is_withheld():
    product = get_product(product_id=135)["product"]
    assert product["description_conflicts_with_name"] is True
    assert "description" not in product
    assert "specs" not in product
    assert "Fender" not in str(product)


def test_shared_specs_are_not_quoted():
    product = get_product(product_id=91)["product"]
    assert product["specs_are_shared"] is True
    assert "specs" not in product


def test_unknown_category_explains_itself():
    result = search_products(category="pandeiro")
    assert "error" in result
    assert "Violões" in result["categories"]


def test_accessory_word_does_not_invent_a_product():
    result = search_products(query="amplificador")
    assert result["total_matches"] == 0
    assert result["out_of_scope"] is True


def test_orchestral_strings_stay_in_the_catalog():
    result = search_products(query="cordas orquestrais")
    assert result.get("out_of_scope") is not True
