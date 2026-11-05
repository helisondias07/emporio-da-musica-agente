# Exemplo 3 — Preço do Takamine GD20 e quais descontos valem

**Cenário:** um produto pelo nome, uma oferta vencida que o cliente lembra, e as promoções que estão ativas de fato. Este é o caso não trivial do catálogo: a "Oferta Especial" de 12% no GD20 está na tabela de promoções com `is_active = 0`, então não pode ser anunciada como preço.

**Ferramentas:** `get_product(name="Takamine GD20")`, `get_product` do Tagima Woodstock, `list_active_promotions`.

**Fonte:** Escrito a partir dos dados do repositório e do manual de políticas (saída das ferramentas). Isto não é a transcrição de uma chamada ao vivo de um modelo — não havia chave de API quando os exemplos foram preparados.

**Data de referência:** 25/03/2026. O PIX é 5% sobre o preço de tabela e não acumula com promoção ativa (seção 6.2 do manual).

## Conversa

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
