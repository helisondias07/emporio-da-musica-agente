"""Scope guard, tool dispatch, and the agent loop without a network call."""

import json

import pytest

from emporio.agent.loop import AgentSession
from emporio.cli import main
from emporio.scope import analyze_scope
from emporio.tools.registry import dispatch


class _Function:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.function = _Function(name, arguments)


class _Message:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Response:
    def __init__(self, message):
        self.choices = [type("Choice", (), {"message": message})()]


class _Completions:
    def __init__(self, steps):
        self.steps = steps
        self.seen = []

    def create(self, **kwargs):
        self.seen.append([dict(message) for message in kwargs["messages"]])
        return self.steps.pop(0)


class _Client:
    def __init__(self, completions):
        self.chat = type("Chat", (), {"completions": completions})()


def test_scope_separates_strings_for_sale_from_a_steel_string_guitar():
    accessory = analyze_scope("vocês têm corda de aço e um amplificador?")
    assert accessory.kind == "accessory"
    assert "cordas" in accessory.accessories
    assert "amplificador" in accessory.accessories

    guitar = analyze_scope("quero um violão de cordas de aço até 1000")
    assert guitar.kind == "in_scope"
    assert guitar.accessories == ()

    mixed = analyze_scope("quero um violão e um cabo")
    assert mixed.kind == "mixed"
    assert mixed.accessories == ("cabo",)

    assert analyze_scope("vocês têm cordas orquestrais?").kind == "in_scope"


def test_dispatch_coerces_tool_arguments():
    result = dispatch(
        "search_products",
        json.dumps({"category": "violao", "max_price_brl": "1000", "in_stock_only": "true", "limit": "5"}),
    )
    assert result["count"] == 5
    assert result["total_matches"] == 12
    assert dispatch("nope", {})["error"].startswith("Ferramenta desconhecida")


def test_loop_runs_a_tool_and_keeps_history():
    completions = _Completions(
        [
            _Response(
                _Message(
                    content=None,
                    tool_calls=[_ToolCall("call_1", "get_product", json.dumps({"name": "Takamine GD20"}))],
                )
            ),
            _Response(_Message(content="O Takamine GD20 está R$ 2.199,00, com 5 em estoque.")),
            _Response(_Message(content="No PIX fica R$ 2.089,05.")),
        ]
    )
    session = AgentSession(_Client(completions), model="gpt-4.1-mini", verbose=False)
    first = session.run_turn("Quanto custa o Takamine GD20?")
    assert "2.199,00" in first
    assert session.tools_used == ["get_product"]
    tool_payload = completions.seen[1][-1]["content"]
    assert "R$ 2.199,00" in tool_payload
    assert "R$ 2.089,05" in tool_payload

    second = session.run_turn("e no PIX?")
    assert "2.089,05" in second
    history = completions.seen[-1]
    assert any(message["role"] == "user" and "Takamine" in message["content"] for message in history)


def test_cli_help_and_missing_key(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert main(["--once", "oi"]) == 2
    captured = capsys.readouterr()
    assert "OPENAI_API_KEY" in captured.err
    assert "emporio.demo" in captured.err
