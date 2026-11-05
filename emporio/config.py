"""Caminhos, data da loja e leitura de datas."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

# Último pedido da base: 22/03/2026. O relógio da máquina deixaria
# todo prazo de troca vencido. EMPORIO_TODAY troca o "hoje" da loja.
DEFAULT_REFERENCE_DATE = date(2026, 3, 25)


def data_dir() -> Path:
    load_dotenv(REPO_ROOT / ".env")
    override = os.getenv("EMPORIO_DATA_DIR", "").strip()
    if override:
        return Path(override)
    return REPO_ROOT / "data"


def parse_date(value: str) -> date:
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Data inválida. Use AAAA-MM-DD ou DD/MM/AAAA.")


def reference_today() -> date:
    load_dotenv(REPO_ROOT / ".env")
    raw = os.getenv("EMPORIO_TODAY", "").strip()
    if not raw:
        return DEFAULT_REFERENCE_DATE
    return parse_date(raw)
