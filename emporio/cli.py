"""Command-line chat. History lasts for this process only."""

from __future__ import annotations

import argparse
import os
import sys

from emporio import __version__
from emporio.agent.llm import MissingCredentials, build_client, resolve_llm
from emporio.agent.loop import AgentSession
from emporio.config import reference_today


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Empório da Música — atendimento virtual (CLI)."
    )
    parser.add_argument("--version", action="version", version=f"emporio {__version__}")
    parser.add_argument(
        "--once",
        action="append",
        default=[],
        metavar="TEXT",
        help="Send one customer message and exit. Repeat for a short scripted chat.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print tool calls to stderr.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the offline demo (catalog, orders, policies). No API key.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Sobe o chat no navegador. O CLI continua disponível sem esta flag.",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("EMPORIO_HOST", "0.0.0.0"),
        help="Host do chat. Padrão 0.0.0.0.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("EMPORIO_PORT", "4721")),
        help="Porta do chat. Padrão 4721.",
    )
    args = parser.parse_args(argv)

    if args.web:
        from emporio.web.server import serve

        serve(host=args.host, port=args.port)
        return 0

    if args.demo:
        from emporio.demo import main as demo_main

        return demo_main()

    try:
        config = resolve_llm()
    except MissingCredentials as exc:
        print(str(exc), file=sys.stderr)
        return 2

    client = build_client(config)
    session = AgentSession(client, config.model, verbose=args.verbose)
    today = reference_today().strftime("%d/%m/%Y")
    print(
        "Empório da Música — atendimento virtual\n"
        f"Modelo: {config.provider} / {config.model}. Data de referência da loja: {today}.\n"
        "O histórico vale só nesta sessão. Comandos: /sair, /limpar, /ajuda."
    )

    if args.once:
        for text in args.once:
            _print_turn(session, text)
        return 0

    if not sys.stdin.isatty():
        for line in sys.stdin:
            text = line.strip()
            if not text:
                continue
            if _handle_command(session, text):
                break
            _print_turn(session, text)
        return 0

    while True:
        try:
            text = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté a próxima.")
            return 0
        if not text:
            continue
        if _handle_command(session, text):
            return 0
        reply = session.run_turn(text)
        print(f"\nEmpório: {reply}")


def _print_turn(session: AgentSession, text: str) -> None:
    print(f"\nVocê: {text}")
    print(f"\nEmpório: {session.run_turn(text)}")


def _handle_command(session: AgentSession, text: str) -> bool:
    command = text.casefold()
    if command in {"/sair", "/exit", "/quit"}:
        print("Até a próxima. Sua música começa aqui.")
        return True
    if command in {"/limpar", "/reset"}:
        session.reset()
        print("Histórico limpo.")
        return False
    if command in {"/ajuda", "/help"}:
        print("Escreva como cliente. /limpar zera a conversa. /sair encerra.")
        return False
    return False


if __name__ == "__main__":
    raise SystemExit(main())
