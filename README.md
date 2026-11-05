# Empório da Música — customer agent

Text agent for the Artefact AI Engineer case (Helison Dias). It answers customers of Empório da Música, a fictional instrument shop in Campo Grande, Mato Grosso do Sul. Customer-facing replies are in Portuguese. This README is in English.

The agent looks up price, stock, and orders with tools over the CSVs, and reads store rules from a section index of the policy manual. It keeps the chat history for the CLI session.

## Run it

Python 3.11 or newer. The project was checked on 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Offline, no API key. This is the path to confirm the data layer:

```bash
python -m pytest
python -m emporio.demo
python main.py --demo
```

Chat, once a key is in `.env` or the environment:

```bash
python main.py
python main.py --verbose
python main.py --once "Quanto custa o Takamine GD20?"
python -m emporio
```

Commands inside the chat: `/limpar` clears the session, `/sair` quits. Repeat `--once` to script a short multi-turn conversation. History lives in the process. It is not written to disk.

If the key is missing, the CLI exits with code 2 and points at the demo and the tests.

## Provider and model

One OpenAI-compatible client. Pick a provider with the key you have.

| Env | Effect |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI. Default model `gpt-4.1-mini`. |
| `OPENAI_BASE_URL` | Optional. Point this at any OpenAI-compatible gateway and set `LLM_MODEL`. |
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Gemini's OpenAI-compatible endpoint. Default model `gemini-3.8-flash`. |
| `GEMINI_BASE_URL` | Optional. Default `https://generativelanguage.googleapis.com/v1beta/openai/`. |
| `LLM_PROVIDER` | `openai` or `gemini`. Needed only when both keys are set. If both are set and this is empty, OpenAI is used. |
| `LLM_MODEL` | Overrides the default model name. |
| `EMPORIO_TODAY` | Store clock. Unset means `2026-03-25`. |
| `EMPORIO_DATA_DIR` | Alternate folder for the CSVs and the PDF. |

`gpt-4.1-mini` is the default because it follows tool calls without a reasoning step, which is what this loop needs. OpenAI has marked it deprecated. If an account rejects the name, set `LLM_MODEL=gpt-5-mini` or `LLM_MODEL=gpt-4o-mini`. For `gpt-5*` the client sends `reasoning_effort=low` and drops `temperature`; if the API rejects either field, it retries once without it.

`gemini-3.8-flash` is the model id in Google's current OpenAI-compatibility docs. Gemini Flash may spend tokens on thinking. If a turn is slow or the tool loop stalls, switch `LLM_MODEL` to another flash model your key can call.

Do not commit `.env`. `.env.example` lists the variables and nothing else.

The examples in `examples/` were not produced by a live model. No API key was available in the environment where this project was built. They were written from the tool output and checked by `tests/test_examples.py`.

## Layout

```
main.py                     CLI entry (python main.py)
emporio/cli.py              argparse, session loop
emporio/agent/prompts.py    Portuguese persona and tool rules
emporio/agent/loop.py       tool-calling loop, in-memory history
emporio/agent/llm.py        OpenAI / Gemini client
emporio/scope.py            accessory vs instrument hint
emporio/tools/              catalog, orders, aftersales, tool schemas
emporio/retrieval/          policy sections and BM25 lookup
emporio/data/loader.py      CSV load
emporio/demo.py             offline scripted path
data/                       CSVs, policy PDF
examples/                   five conversations
tests/                      offline tests
```

## Architecture

```
customer message
    -> session history
    -> accessory hint, when the message asks for one
    -> LLM with tool calling
         search_products / get_product     products + promotions
         list_categories
         list_active_promotions
         lookup_order                      orders + customers + items
         evaluate_aftersales               policy windows, computed
         search_policies                   manual sections
    -> Portuguese reply
```

The loop is a plain tool loop, not a framework. Up to six tool rounds per turn. The model sees the system prompt, the prior turns, and the JSON from each tool. `--verbose` prints the tool name and arguments on stderr.

Why this shape:

- Prices, stock, and order status are rows. A tool that filters them is easier to test than asking the model to read a CSV, and it cannot "remember" a price that is not in the result.
- The manual is eight pages with stable headings. A section index plus BM25 is enough. Embeddings would add a second API, a vector store, and nothing to retrieve that the headings do not already name. If the manual grew past a few dozen pages, the same sections could be embedded later without changing the tool the model calls.
- Deadline questions are date arithmetic. The model is told not to do that math. `evaluate_aftersales` returns `within_time_window` and a deadline. The model still has to phrase the answer, and it still calls `search_policies` so the wording stays tied to the manual.
- Pandas or SQLite would also work. The tables are 65 products and 20 orders. The loader uses the stdlib `csv` module and `Decimal` so `799.9` does not become a float. That is the whole data layer.

The persona follows section 7 of the manual: informal but professional, Brazilian Portuguese, "você", no emoji, no robotic opener. The tagline is "Sua música começa aqui." The agent says it is the store's virtual attendant, not a model name.

## Data

File names were shortened. The bytes match the challenge pack.

| In this repo | Original name |
| --- | --- |
| `data/products.csv` | `desafio_tecnico_ai_eng - products.csv` |
| `data/promotions.csv` | `desafio_tecnico_ai_eng - promotions.csv` |
| `data/customers.csv` | `desafio_tecnico_ai_eng - customers.csv` |
| `data/categories.csv` | `desafio_tecnico_ai_eng - categories.csv` |
| `data/order_items.csv` | `desafio_tecnico_ai_eng - order_items.csv` |
| `data/orders.csv` | `desafio_tecnico_ai_eng - orders.csv` |
| `data/politicas_da_loja.pdf` | `políticas_da_loja.pdf` |

What the loader normalizes:

- Money is `Decimal`. Labels use Brazilian grouping (`R$ 2.199,00`).
- `is_active` is `0` or `1`. Only `1` changes a price. If two active discounts ever land on one SKU, the larger one wins. In this file they do not overlap.
- Sale price is the list price after the active discount. A filter such as "até R$ 1000" uses the sale price, which is what the customer would pay.
- PIX is 5% off the list price and only when there is no active promotion (manual section 6.2). The tool returns `pix_price_label: null` on a promotional price.
- `specs` is parsed JSON. A failed parse aborts the load.
- Availability is derived, not stored: `active` and stock above zero is `disponível`; `active` and stock zero is `esgotado`; `coming_soon` is not for sale even if stock is above zero (product 130, stock 2); `discontinued` is out of the catalog (products 113 and 136).
- Order lines have no unit price. The tool shows the product name, the quantity, and the order total as charged. It does not reprice the order from today's catalog.
- Phone and email on a customer record are masked before they reach the model (`final 7821`, `a***@domain`). A name that matches more than one customer returns the names and cities and no orders.

### Catalog rows that disagree with themselves

Six products have a description whose brand is not the brand in the name: 135, 137, 139, 140, 142, 144 (for example the "Music Man" bass is described as a Fender Jazz Bass). Several spec blobs are also copied across SKUs (the three keyboards share one spec object). The tool sets `description_conflicts_with_name` or `specs_are_shared`, drops the unsafe text, and the prompt forbids quoting it. Price, stock, status, and the name stay.

The name is the SKU title. The description is not repaired in the CSV, so the original file stays intact.

### Store clock

The latest order date in the file is 22/03/2026. A laptop clock of November 2026 would make every return window look closed and every open order look abandoned. `EMPORIO_TODAY` defaults to 25/03/2026, a few days after that snapshot. Override it to test other windows. The aftersales tool and the system prompt both use this date.

### Policy conflicts, and the reading this project uses

The manual and the tables do not fully agree. The agent does not debate these with the customer unless asked.

| Conflict | Reading used |
| --- | --- |
| Cover and section 1.2 list (67) 3341-4444 as phone and WhatsApp. Section 7 names WhatsApp (67) 3321-4500. | 3341-4444 is the store phone. 3321-4500 is the WhatsApp channel. |
| Section 1.2 prints `contato@empóriodamusica.com.br`. The cover prints `contato@emporiodamusica.com.br`. | The cover address, without the accent. An accented domain is treated as a typo. |
| The payment table says credit in up to 12 installments with a R$ 100 minimum installment. Section 3.1 is finer: up to 3x with no minimum except under R$ 50, 4x–6x with a R$ 80 minimum, 7x–12x with a R$ 100 minimum. | Section 3.1 wins. The "under R$ 50" sentence is quoted as written. It is not turned into a new rule. |
| Section 1 says the catalog has more than 300 instruments. The CSV has 65 products, and categories 6, 7, and 8 have none. | What can be sold is the CSV. The "300" line is institutional copy. |
| Section 7.1 says to suggest a partner shop for accessories. No partner list is in the pack. | Decline the accessory. Do not invent a shop name. Say the counter team can suggest one. |
| Category 3's blurb mentions loose percussion pieces. There is no such SKU, and section 1 says instruments only. | Answer from the product rows. |
| Orders have tracking and a delivery estimate, and no in-store flag. There is no received-at column. | Every order is treated as a distance sale. For a delivered order with no receipt date from the customer, the estimate is used and flagged as assumed. Otherwise the agent asks. Regret is 7 calendar days after receipt, deadline inclusive (`receipt + 7`). Defect exchange at the store is 30 days after the purchase date. Legal warranty is 90 days after receipt. |
| The manual's tracking example is a Correios-style code. The order row does not name the carrier. | Give the code. Say it can be checked on Correios or Jadlog. Do not pick one. |

Inactive promotions stay in `get_product` under `inactive_promotions` so the agent can say an offer the customer remembers is not live. They never change `sale_price_label`. The Takamine GD20 (id 95) is the clear case: list price R$ 2.199,00, PIX R$ 2.089,05, a 12% "Oferta Especial" with `is_active = 0`.

## Examples

| File | What it shows |
| --- | --- |
| `examples/01_violao_ate_1000.md` | 12 in-stock violões at or under R$ 1.000, plus the out-of-stock and discontinued rows in that cap. Second turn recommends beginner nylon models. |
| `examples/02_endereco_e_horario.md` | Address, Saturday hours, phone, and WhatsApp. |
| `examples/03_preco_takamine_gd20.md` | GD20 price, the inactive 12% offer, the two violões that are actually on promotion, and the expired Woodstock Black Friday. |
| `examples/04_arrependimento_pedido_7.md` | Return policy applied to order 7 and a receipt date of 17/02/2026. Regret is closed. Legal warranty is open until 18/05/2026. |
| `examples/05_pedido_8_e_acessorio.md` | Order 8 is still "enviado" 25 days after the estimate. Strings and an amplifier are refused. |

## Tests

`python -m pytest` loads the real CSVs and the real PDF. It checks the 12-guitar filter, the GD20 price, the four active promotions, order masking, the order 7 windows, policy phrases present in both the PDF and the section index, the accessory guard, a fake tool-calling turn that keeps history, and the strings in `examples/`. Nothing in the suite calls a model API.

## Limitations, and what I would do next

- The model can still skip a tool and invent a sentence. The guardrails are the prompt, the accessory hint, the accessory-only search refusal, and the date tool. A production version would reject replies that contain a price or a date not present in the tool payload.
- Order lookup trusts whoever types the order id. Masking the phone is not authentication. Next step is a check against the phone or email on the customer row before any order detail is spoken.
- There is no live tracking API, no freight quote, and no payment. Other cities stay at "the freight is calculated from the postal code." Campo Grande metro shipping (free above R$ 500, otherwise R$ 35, 1 to 3 business days) is only stated when the policy tool returns it.
- Complaint handling stops at the manual's "24 business hours" line. There is no ticket queue and no human handoff.
- The section index was transcribed from the PDF because the tables extract with broken columns. `policy_alignment()` fails the build if a key sentence disappears from either the PDF or the index. A larger manual should be re-split, then embedded, with this index kept as the baseline.
- Several guitar, bass, drum, and keyboard descriptions are synthetic and contradict the name. I would send that list back to the store and stop selling technical claims on those SKUs until the row is fixed. The agent already refuses to quote them.
- Session memory is the CLI process. A WhatsApp channel would need a store keyed by the chat id, plus the five-minute response rule in section 7.
- Default model ids go stale. `LLM_MODEL` is the escape hatch on purpose.
- This was not run against a live key here, so the example wording is the intended voice, not a captured completion. With a key, the next step is a small eval set: the five conversations above, scored on whether the tool trace contains the right ids and whether the reply contains the right prices and deadlines.

## AI assistance

A coding assistant (Cursor) was used to implement this project. Helison directed the approach, reviewed the decisions, and owns the submission.
