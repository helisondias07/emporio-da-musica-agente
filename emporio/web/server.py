"""Chat no navegador, no mesmo agente. A página é o balcão, não um site."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from emporio.agent.llm import MissingCredentials, build_client, resolve_llm
from emporio.agent.loop import AgentSession
from emporio.config import reference_today

STATIC = Path(__file__).resolve().parent / "static"

CONSULTA = {
    "search_products": "o catálogo",
    "get_product": "o catálogo",
    "list_categories": "as categorias",
    "list_active_promotions": "as promoções",
    "lookup_order": "o pedido",
    "evaluate_aftersales": "os prazos de troca",
    "search_policies": "o manual da loja",
}

SEM_CHAVE = (
    "O balcão está aqui, mas o modelo não está configurado neste servidor. "
    "Falta OPENAI_API_KEY ou GEMINI_API_KEY."
)


class MensagemIn(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


@dataclass
class HeldSession:
    session: AgentSession
    sid: str
    lock: threading.Lock = field(default_factory=threading.Lock)


def frase_consulta(nomes: list[str]) -> str | None:
    partes: list[str] = []
    for nome in nomes:
        rotulo = CONSULTA.get(nome)
        if rotulo and rotulo not in partes:
            partes.append(rotulo)
    if not partes:
        return None
    if len(partes) == 1:
        return f"Olhei {partes[0]}."
    return "Olhei " + ", ".join(partes[:-1]) + " e " + partes[-1] + "."


def create_app() -> FastAPI:
    app = FastAPI(title="Empório da Música")
    app.state.sessions = {}
    app.state.runtime = None
    app.state.sessions_lock = threading.Lock()

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/estado")
    def estado():
        runtime = _runtime(app)
        hoje = reference_today().strftime("%d/%m/%Y")
        if runtime is None:
            return {"pronto": False, "modelo": None, "hoje": hoje}
        config, _client = runtime
        return {"pronto": True, "modelo": f"{config.provider}/{config.model}", "hoje": hoje}

    @app.post("/api/mensagens")
    def mensagens(body: MensagemIn, request: Request):
        texto = body.texto.strip()
        if not texto:
            raise HTTPException(status_code=400, detail="Escreva uma mensagem.")
        runtime = _runtime(app)
        if runtime is None:
            return JSONResponse(
                {"ok": False, "erro": "sem_chave", "resposta": SEM_CHAVE, "consulta": None, "ferramentas": []}
            )
        config, client = runtime
        held = _session_for(app, request, client, config.model)
        try:
            with held.lock:
                resposta = held.session.run_turn(texto)
                ferramentas = list(held.session.tools_used)
        except Exception as exc:
            print(f"modelo: {type(exc).__name__}")
            return JSONResponse(
                status_code=502,
                content={
                    "ok": False,
                    "erro": "modelo",
                    "resposta": "Não consegui completar a consulta agora. Tenta de novo daqui a pouco.",
                    "consulta": None,
                    "ferramentas": [],
                },
            )
        response = JSONResponse(
            {
                "ok": True,
                "resposta": resposta,
                "consulta": frase_consulta(ferramentas),
                "ferramentas": ferramentas,
            }
        )
        _stamp(response, held)
        return response

    @app.post("/api/limpar")
    def limpar(request: Request):
        sid = request.cookies.get("emporio_sess")
        held = app.state.sessions.get(sid) if sid else None
        if held is not None:
            with held.lock:
                held.session.reset()
        return {"ok": True}

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def _runtime(app: FastAPI):
    if app.state.runtime is not None:
        return app.state.runtime
    try:
        config = resolve_llm()
    except MissingCredentials:
        return None
    app.state.runtime = (config, build_client(config))
    return app.state.runtime


def _session_for(app: FastAPI, request: Request, client, model: str) -> HeldSession:
    sid = request.cookies.get("emporio_sess")
    with app.state.sessions_lock:
        held = app.state.sessions.get(sid) if sid else None
        if held is None:
            sid = str(uuid.uuid4())
            held = HeldSession(AgentSession(client, model), sid)
            app.state.sessions[sid] = held
    return held


def _stamp(response: JSONResponse, held: HeldSession) -> None:
    response.set_cookie(
        "emporio_sess",
        held.sid,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 12,
    )


def serve(host: str = "0.0.0.0", port: int = 4721) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)
