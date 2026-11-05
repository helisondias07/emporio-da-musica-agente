"""Reais em Decimal, do CSV até o rótulo R$ 1.234,56."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal("0.01")
PIX_FACTOR = Decimal("0.95")


def parse_decimal(value: str) -> Decimal:
    text = value.strip().replace(" ", "")
    if not text:
        raise ValueError("Valor numérico vazio.")
    return Decimal(text)


def as_decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    text = value.strip().replace("R$", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return Decimal(text)


def quantize_brl(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def format_brl(value: Decimal) -> str:
    quantized = quantize_brl(value)
    sign = "-" if quantized < 0 else ""
    cents = int(abs(quantized) * 100)
    whole, fraction = divmod(cents, 100)
    body = f"{whole:,}".replace(",", ".")
    return f"{sign}R$ {body},{fraction:02d}"


def percent_number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)
    return float(value)
