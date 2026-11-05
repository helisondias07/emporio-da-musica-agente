"""The chat page is the counter. It does not invent a model reply."""

from fastapi.testclient import TestClient

from emporio.web.server import SEM_CHAVE, create_app, frase_consulta


def test_frase_consulta_dedupes_catalog_lookups():
    assert frase_consulta(["search_products", "get_product"]) == "Olhei o catálogo."
    assert (
        frase_consulta(["lookup_order", "search_policies"])
        == "Olhei o pedido e o manual da loja."
    )
    assert frase_consulta([]) is None


def test_page_is_the_shop_chat_not_a_saas_skin():
    client = TestClient(create_app())
    page = client.get("/")
    assert page.status_code == 200
    assert "Empório da Música" in page.text
    assert "Sua música começa aqui." in page.text
    css = client.get("/static/chat.css")
    assert css.status_code == 200
    skin = page.text + css.text
    assert "Inter" not in skin
    assert "6366f1" not in skin.lower()
    assert "indigo" not in skin.lower()


def test_chat_without_a_key_does_not_invent_an_answer(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    client = TestClient(create_app())
    estado = client.get("/api/estado")
    assert estado.json()["pronto"] is False
    resposta = client.post("/api/mensagens", json={"texto": "Quanto custa o Takamine GD20?"})
    body = resposta.json()
    assert body["ok"] is False
    assert body["erro"] == "sem_chave"
    assert body["resposta"] == SEM_CHAVE
    assert "2.199" not in body["resposta"]
    limpar = client.post("/api/limpar")
    assert limpar.json()["ok"] is True
