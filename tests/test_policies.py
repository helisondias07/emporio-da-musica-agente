"""Policy index stays aligned with the PDF and answers the brief's questions."""

from emporio.retrieval.policies import policy_alignment, search_policies


def test_index_matches_pdf_phrases():
    alignment = policy_alignment()
    assert alignment["missing_from_pdf"] == []
    assert alignment["missing_from_index"] == []


def test_address_hours_returns_and_whatsapp():
    address = search_policies("qual o endereço da loja")
    assert address["sections"][0]["id"] in {"capa", "1.2"}
    assert "Rua 14 de Maio, 3200" in address["sections"][0]["text"]

    hours = search_policies(topic="hours")
    assert hours["sections"][0]["id"] == "2"
    assert "09:00 às 13:00" in hours["sections"][0]["text"]
    assert "09:00 às 18:00" in hours["sections"][0]["text"]

    regret = search_policies("me arrependi posso devolver")
    joined = " ".join(section["text"] for section in regret["sections"])
    assert "7 (sete) dias corridos após o recebimento" in joined

    whatsapp = search_policies("qual o whatsapp")
    assert any("(67) 3321-4500" in section["text"] for section in whatsapp["sections"])

    shipping = search_policies(topic="shipping", limit=4)
    joined_shipping = " ".join(section["text"] for section in shipping["sections"])
    assert "Frete grátis para pedidos acima de R$ 500,00." in joined_shipping
    assert "taxa fixa de R$ 35,00" in joined_shipping
