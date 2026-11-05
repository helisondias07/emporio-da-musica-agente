# Submission note — Empório da Música agent

Helison Dias. Artefact AI Engineer case. This is the written companion to the repository. The operational detail, including every conflict between the manual and the CSVs, is in `README.md`.

## What was built

A Python text agent that answers customers of Empório da Música, the fictional instrument shop in Campo Grande/MS. The interface is a chat (`python main.py --web`) on the same process and the same tool loop. The CLI (`python main.py`) stays as a fallback. Customer replies are in Portuguese, in the voice the store's own manual asks for: informal, professional, and specific. The page is the conversation, not a marketing site. Without a model key it opens and says so, instead of inventing a catalog answer.

The agent can filter the catalog (violões up to R$ 1.000, a named model, what is actually on promotion), look up an order by id, tracking code, or customer, and apply the return, shipping, warranty, hours, and privacy rules from the policy manual. It declines strings, picks, cables, cases, pedals, and amplifiers, which the store does not sell.

## Architecture

Hybrid, on purpose.

Structured questions go through tools over the CSVs. `search_products`, `get_product`, `list_categories`, and `list_active_promotions` read products, categories, and promotions. `lookup_order` joins orders, items, and customers. Money is `Decimal`. A sale price already includes the active discount, and the "up to R$ 1.000" filter uses that price. PIX at 5% is returned only when no promotion is active, which is what section 6.2 of the manual says.

Policy questions go through `search_policies`. The PDF is split into the sections of the manual (hours, payments, regret, freight, warranty, WhatsApp, privacy, and the rest). Ranking is BM25 over those sections, with a small boost so that "endereço" or "horário" hits the right heading, plus a topic argument when the model already knows which block it wants. I did not add embeddings. The manual is eight pages and the headings are stable. An embedding index would need another API and would not answer a question the section text cannot answer. The tool boundary stays the same if the manual later grows and the index moves to vectors.

`evaluate_aftersales` is the piece I did not want to leave to the model. "Can I return this?" depends on the receipt date, the purchase date, and the store's clock. The tool returns whether each window is still open, and the deadline. The model is instructed to call it instead of doing the calendar math, and to call `search_policies` in the same turn so the explanation stays in the manual's words.

The loop is a short tool loop, six rounds at most. No agent framework. The session list is the history, so a follow-up ("sou iniciante, quero nylon") still sees the list from the previous turn.

An accessory hint is attached when the message asks for strings, an amp, and so on, including when the message also asks for an instrument. A catalog search whose tokens are only accessory words returns an out-of-scope result, so a preamp mentioned in a guitar description is not offered as an amplifier.

## Design choices

**Store clock.** The order file ends on 22/03/2026. Using the machine date would make every deadline look expired. The reference date is 25/03/2026 unless `EMPORIO_TODAY` is set. Order 7, received on 17/02/2026, is then a real policy case: the 7-day regret window and the 30-day defect exchange are closed, and the 90-day legal warranty is still open until 18/05/2026.

**Orders are distance sales.** The table has tracking and delivery estimates and no counter-sale flag. Regret, which the manual limits to online purchases, applies to these rows. There is no received-at column, so the agent asks. If the customer does not know and the status is delivered, the estimate is used and marked as assumed.

**Dirty catalog rows stay dirty.** Products 135, 137, 139, 140, 142, and 144 have a description from a different brand than the name (a "Music Man" bass described as a Fender, a Yamaha drum kit described as a Pearl, and others). Some spec JSON is copied across SKUs. The loader does not rewrite the CSV. The tool hides the conflicting description and the shared specs, and the prompt says to talk about name, price, and stock only. I would rather admit the row is inconsistent than invent a wood or a pickup.

**Contacts when the manual disagrees with itself.** Store phone (67) 3341-4444, from the cover and section 1.2. WhatsApp (67) 3321-4500, from section 7, which is the only place that describes the remote channel. Email `contato@emporiodamusica.com.br` from the cover. The accented address in section 1.2 is treated as a typo. Installment detail follows section 3.1, which is more specific than the summary table. The "more than 300 instruments" sentence is not the stock count. The CSV has 65 products, and that is what can be sold.

**Inactive promotions are visible and not applicable.** The Takamine GD20 is R$ 2.199,00, PIX R$ 2.089,05, five in stock. A 12% offer sits on that SKU with `is_active = 0`. The detail payload includes it so the agent can tell a customer the offer is over, and the sale price ignores it.

**Privacy of the prototype.** Phone and email are masked before the model sees them. An ambiguous name (two Pedros, several Camilas) returns no orders. This is not identity verification. Anyone who knows an order id can hear the status. A real channel would confirm the phone on the customer row first.

**Model.** `gpt-4.1-mini` by default when `OPENAI_API_KEY` is set, because it calls tools without a reasoning step. It is a deprecated id, so `LLM_MODEL` overrides it (`gpt-5-mini` and `gpt-4o-mini` are the documented fallbacks). `GEMINI_API_KEY` uses `gemini-3.8-flash` through Google's OpenAI-compatible endpoint. One client, two providers, no second SDK.

**No pandas.** The brief allows pandas or SQL. Sixty-five products do not need either. The csv module plus `Decimal` keeps `799.9` exact and the dependency list short.

## Example scenarios

All five files in `examples/` were written from tool output, not from a live completion. No API key was present in the build environment. `tests/test_examples.py` checks that the transcripts still contain the prices, the address, the tracking codes, and the warranty date.

1. **Violões até R$ 1.000.** Twelve instruments in stock, cheapest first, none of them on promotion, so PIX applies. The Giannini GF-3D in the same price band is out of stock, and the Shelby SN-7C is discontinued. The second turn recommends three beginner nylon models from that list.
2. **Address and hours.** Rua 14 de Maio, 3200, Centro. Weekdays 09:00–18:00, Saturday 09:00–13:00, closed Sunday and holidays. Phone and WhatsApp as resolved above.
3. **Takamine GD20.** Current price and PIX. The 12% offer is refused because it is inactive. The violões actually on promotion are the Crafter HT-100 (18%, R$ 1.967,18) and the Taylor 110e (8%, R$ 5.519,08). The Woodstock Black Friday of 30% is also inactive. Its price is R$ 899,00, PIX R$ 854,05.
4. **Regret on order 7.** The rule is stated first, then applied. Receipt 17/02/2026, store date 25/03/2026. Regret and preference exchange closed on 24/02/2026. Defect exchange at the store closed on 05/03/2026. Legal warranty open until 18/05/2026. The manufacturer term is not invented.
5. **Order 8 and accessories.** Status is still shipped. Tracking `BRJL5544332BR`. The estimate of 28/02/2026 is 25 days past and no new date is invented. The carrier is not in the row, so the reply points at Correios or Jadlog. Strings and an amplifier are declined, with no made-up partner shop.

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
python -m emporio.demo
```

The demo and the tests need no key. They load the CSVs and the PDF.

For the chat, copy `.env.example` to `.env`, set `OPENAI_API_KEY` or `GEMINI_API_KEY`, and run `python main.py --web` (http://127.0.0.1:4721). The terminal agent is `python main.py`. Optional: `LLM_MODEL`, `LLM_PROVIDER`, `EMPORIO_TODAY`.

## Limitations

The model can ignore a tool. I would block customer-facing prices and dates that did not appear in a tool result. Order lookup needs a real identity check. Freight outside Campo Grande needs a quote API the pack does not include. Complaints need a handoff, not only the 24-business-hour sentence. The policy index is a reviewed transcription of a PDF whose tables extract badly, guarded by a phrase check against the PDF. The contradictory product descriptions should be fixed by the store, not by the agent. Session memory is the chat process (a cookie) or the CLI process. The default model names will age, which is why they are environment variables.

With more time I would add a scored eval over the five conversations (did the trace hit the right tool and the right id, does the reply contain the right price and the right deadline), a WhatsApp transport with history keyed by chat, and a human queue for complaints.

## AI assistance

A coding assistant (Cursor) was used to implement this project. Helison directed the approach, reviewed the decisions, and owns the submission.
