# Example 5 — A shipped order, and two products the store does not sell

**Scenario:** order lookup by id, a delivery estimate that is already late on the store clock, and an accessory request in the same message. The agent reports the recorded status and does not invent a carrier or a new delivery date. Strings and amplifiers are declined because the store sells instruments only, and the manual's "suggest a partner shop" line has no partner list behind it.

**Tools:** `lookup_order(order_id=8)`. The accessory refusal is a scope rule plus section 1 and section 7.1 of the manual. No catalog search for the amp or the strings.

**Source:** Written from the repository data and the policy manual (tool output). This is not a transcript of a live model call — no API key was available when the examples were prepared.

**Reference date:** 25/03/2026. Order 8: Ana Carolina Ferreira, Campo Grande, placed 15/02/2026, status shipped, total R$ 349,90 on debit, item Kala KA-C Concert Mogno, tracking BRJL5544332BR, estimated delivery 28/02/2026. That estimate is 25 days in the past and the status is still "enviado".

## Conversation

**Cliente:** Oi, consegue ver o pedido 8? Queria saber se já saiu para entrega. Ah, e vocês têm corda de aço e um amplificador pequeno?

**Empório da Música:** Consigo sim. O pedido 8 está no nome de Ana Carolina Ferreira, aqui de Campo Grande. Já saiu pra entrega, mas ainda não consta como entregue.

É um Kala KA-C Concert Mogno. Ficou R$ 349,90 no débito. O rastreio é BRJL5544332BR, com previsão de 28/02/2026.

Essa data já passou faz 25 dias e o pedido continua como enviado. Daqui eu não tenho outra data, nem o nome de quem levou. Dá pra olhar o código no site dos Correios ou da Jadlog. Se estiver parado, liga no (67) 3341-4444 ou chama no WhatsApp (67) 3321-4500 que a gente vê isso com você.

Corda de aço e amplificador a gente não vende. A loja é só de instrumento, então corda avulsa, palheta, cabo, case, pedal e amplificador ficam de fora. Não tenho uma loja parceira anotada aqui pra te passar. Quem está no balcão costuma indicar um lugar aqui em Campo Grande.

Se quiser ukulele ou violão, eu olho o que tem.
