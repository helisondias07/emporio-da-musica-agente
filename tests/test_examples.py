"""The example chats stay tied to the numbers the tools actually return."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*.md"))

SOURCE_LINE = (
    "This is not a transcript of a live model call — no API key was available "
    "when the examples were prepared."
)


def test_there_are_between_three_and_five_conversations():
    assert 3 <= len(EXAMPLES) <= 5
    for path in EXAMPLES:
        text = path.read_text(encoding="utf-8")
        assert SOURCE_LINE in text
        assert "**Cliente:**" in text
        assert "**Empório da Música:**" in text


def test_examples_quote_the_live_catalog_and_the_manual():
    blob = "\n".join(path.read_text(encoding="utf-8") for path in EXAMPLES)
    for snippet in (
        "12 violões",
        "R$ 429,90",
        "Rua 14 de Maio, 3200",
        "09:00 às 18:00",
        "09:00 às 13:00",
        "(67) 3341-4444",
        "(67) 3321-4500",
        "contato@emporiodamusica.com.br",
        "R$ 2.199,00",
        "R$ 2.089,05",
        "R$ 1.967,18",
        "R$ 5.519,08",
        "R$ 854,05",
        "is_active = 0",
        "18/05/2026",
        "BRKR1122334BR",
        "BRJL5544332BR",
        "25 dias",
        "amplificador",
        "Shelby SU-21S",
        "Kala KA-C Concert Mogno",
    ):
        assert snippet in blob, snippet
