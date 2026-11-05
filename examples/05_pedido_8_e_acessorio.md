# Exemplo 5 — Pedido enviado e dois produtos que a loja não vende

**Cenário:** consulta de pedido pelo id, uma previsão de entrega que já passou no relógio da loja, e um pedido de acessório na mesma mensagem. O agente informa o status que está gravado e não inventa transportadora nem data nova. Corda e amplificador são recusados porque a loja só vende instrumento, e a frase do manual sobre indicar loja parceira não tem lista de parceiros.

**Ferramentas:** `lookup_order(order_id=8)`. A recusa do acessório é a regra de escopo mais as seções 1 e 7.1 do manual. Não há busca no catálogo por amplificador nem por corda.

**Fonte:** Escrito a partir dos dados do repositório e do manual de políticas (saída das ferramentas). Isto não é a transcrição de uma chamada ao vivo de um modelo — não havia chave de API quando os exemplos foram preparados.

**Data de referência:** 25/03/2026. Pedido 8: Ana Carolina Ferreira, Campo Grande, feito em 15/02/2026, status enviado, total R$ 349,90 no débito, item Kala KA-C Concert Mogno, rastreio BRJL5544332BR, previsão de entrega 28/02/2026. Essa previsão está 25 dias no passado e o status continua "enviado".

## Conversa

**Cliente:** Oi, consegue ver o pedido 8? Queria saber se já saiu para entrega. Ah, e vocês têm corda de aço e um amplificador pequeno?

**Empório da Música:** Consigo sim. O pedido 8 está no nome de Ana Carolina Ferreira, aqui de Campo Grande. Já saiu pra entrega, mas ainda não consta como entregue.

É um Kala KA-C Concert Mogno. Ficou R$ 349,90 no débito. O rastreio é BRJL5544332BR, com previsão de 28/02/2026.

Essa data já passou faz 25 dias e o pedido continua como enviado. Daqui eu não tenho outra data, nem o nome de quem levou. Dá pra olhar o código no site dos Correios ou da Jadlog. Se estiver parado, liga no (67) 3341-4444 ou chama no WhatsApp (67) 3321-4500 que a gente vê isso com você.

Corda de aço e amplificador a gente não vende. A loja é só de instrumento, então corda avulsa, palheta, cabo, case, pedal e amplificador ficam de fora. Não tenho uma loja parceira anotada aqui pra te passar. Quem está no balcão costuma indicar um lugar aqui em Campo Grande.

Se quiser ukulele ou violão, eu olho o que tem.
