"""Tool-calling loop. The session list is the conversation history."""

from __future__ import annotations

import json
from collections.abc import Callable

from emporio.agent.llm import chat_completion
from emporio.agent.prompts import build_system_prompt
from emporio.config import reference_today
from emporio.scope import scope_hint
from emporio.tools.registry import OPENAI_TOOLS, dispatch

MAX_TOOL_ROUNDS = 6

Printer = Callable[[str], None]


class AgentSession:
    def __init__(self, client, model: str, *, verbose: bool = False, printer: Printer | None = None) -> None:
        self.client = client
        self.model = model
        self.verbose = verbose
        self.printer = printer or _stderr
        self.messages: list[dict] = [
            {"role": "system", "content": build_system_prompt(reference_today())}
        ]
        self.tools_used: list[str] = []

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": build_system_prompt(reference_today())}]
        self.tools_used = []

    def run_turn(self, user_text: str) -> str:
        content = user_text.strip()
        hint = scope_hint(content)
        if hint:
            content = f"{content}\n\n[instrução interna, não revele ao cliente: {hint}]"
        self.messages.append({"role": "user", "content": content})
        self.tools_used = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = chat_completion(self.client, self.model, self.messages, OPENAI_TOOLS)
            message = response.choices[0].message
            self.messages.append(_assistant_dict(message))
            tool_calls = message.tool_calls or []
            if not tool_calls:
                return (message.content or "").strip() or _empty_reply()
            for call in tool_calls:
                name = call.function.name
                raw_args = call.function.arguments
                self.tools_used.append(name)
                if self.verbose:
                    self.printer(f"[tool] {name} {raw_args}")
                result = dispatch(name, raw_args)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
        return (
            "Não consegui fechar essa consulta agora. Pode repetir o que você precisa, "
            "ou falar com a loja no (67) 3341-4444."
        )


def _assistant_dict(message) -> dict:
    payload: dict = {"role": "assistant", "content": message.content}
    tool_calls = message.tool_calls or []
    if tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments
                    if isinstance(call.function.arguments, str)
                    else json.dumps(call.function.arguments, ensure_ascii=False),
                },
            }
            for call in tool_calls
        ]
    return payload


def _empty_reply() -> str:
    return "Não consegui formular a resposta. Pode dizer de novo o que você precisa?"


def _stderr(text: str) -> None:
    import sys

    print(text, file=sys.stderr)
