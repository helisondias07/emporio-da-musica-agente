# Example 3 — Price of the Takamine GD20, and which discounts are real

**Scenario:** a named product, an expired offer the customer remembers, and the promotions that are actually active. This is the non-trivial catalog case: the 12% "Oferta Especial" on the GD20 is in the promotions table with `is_active = 0`, so it must not be quoted as a price.

**Tools:** `get_product(name="Takamine GD20")`, `get_product` for the Tagima Woodstock, `list_active_promotions`.

**Source:** Written from the repository data and the policy manual (tool output). This is not a transcript of a live model call — no API key was available when the examples were prepared.

**Reference date:** 25/03/2026. PIX is 5% off the list price and does not stack with an active promotion (manual section 6.2).

## Conversation

**Cliente:** Quanto custa o Takamine GD20?

**Empório da Música:** O Takamine GD20 Dreadnought Natural está R$ 2.199,00. Tem 5 na loja. No PIX sai R$ 2.089,05, os 5% em cima do preço de tabela. Ele não está em promoção.

É aço, tampo de cedro sólido, fundo e lateral de sapele, sem captador. Se quiser, eu ponho outro dreadnought do lado pra comparar.

**Cliente:** Eu tinha visto uma oferta de 12% nele. Ainda vale?

**Empório da Música:** Essa de 12% (a Oferta Especial) não está valendo mais. O preço hoje segue R$ 2.199,00, ou R$ 2.089,05 no PIX.

**Cliente:** Entendi. E qual violão está em promoção de verdade? Vi também uma Black Friday do Woodstock.

**Empório da Música:** Em violão, agora só dois estão com desconto. Nesses o PIX não entra por cima:

O Crafter HT-100 Folk Aço Natural saía R$ 2.399,00 e está R$ 1.967,18, 18% no Desconto Exclusivo. Tem 3.

O Taylor 110e Dreadnought Natural saía R$ 5.999,00 e está R$ 5.519,08, 8%. Tem 4, e esse tem captador.

A Black Friday de 30% do Tagima Woodstock Dreadnought Natural já acabou. Ele está R$ 899,00, com 11 na loja. Nesse o PIX vale, fica R$ 854,05.

Me fala o que você toca que eu te digo qual dos dois faz mais sentido.
