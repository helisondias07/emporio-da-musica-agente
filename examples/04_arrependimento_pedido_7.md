# Exemplo 4 — Arrependimento e a política de troca no pedido 7

**Cenário:** o cliente quer desfazer a compra. O agente lê a política de devolução e aplica num pedido real e numa data de recebimento, em vez de dizer sim para todo arrependimento.

**Ferramentas:** `search_policies` sobre trocas, `lookup_order(order_id=7)`, `evaluate_aftersales(order_id=7, receipt_date="2026-02-17")`.

**Fonte:** Escrito a partir dos dados do repositório e do manual de políticas (saída das ferramentas). Isto não é a transcrição de uma chamada ao vivo de um modelo — não havia chave de API quando os exemplos foram preparados.

**Data de referência:** 25/03/2026. O pedido 7 foi feito em 03/02/2026, status entregue, total R$ 159,90 no crédito em 3x, item Shelby SU-21S Soprano Sunburst, rastreio BRKR1122334BR, previsão de entrega 17/02/2026. O cliente confirma essa data de recebimento.

Prazos que a ferramenta devolve:
- arrependimento e troca por preferência: fecharam em 24/02/2026 (36 dias após o recebimento)
- troca na loja por defeito: fechou em 05/03/2026 (30 dias após a compra)
- garantia legal: ainda aberta até 18/05/2026

## Conversa

**Cliente:** Me arrependi da minha compra. Posso devolver meu pedido?

**Empório da Música:** Se a compra foi pelo site e o instrumento chegou faz até 7 dias, pode devolver sim, sem precisar explicar o motivo. Ele tem que estar sem uso, na caixa, com o manual. O dinheiro volta do mesmo jeito que você pagou, em até 10 dias úteis, e o frete da volta é por nossa conta.

Me passa o número do pedido e o dia que ele chegou na sua casa, que eu olho o seu caso.

**Cliente:** É o pedido 7. Comprei pelo site e recebi no dia 17 de fevereiro.

**Empório da Música:** Achei o pedido 7, no nome de Mariana Costa Santos. Está entregue: ukulele Shelby SU-21S Soprano Sunburst, R$ 159,90 no cartão em 3x, rastreio BRKR1122334BR. O dia que você falou, 17/02/2026, é o mesmo da previsão de entrega.

Hoje é 25/03/2026. Já fazem 36 dias, então a devolução por arrependimento não rola mais. Os 7 dias fecharam em 24/02. Troca por outro modelo, outra cor ou outro tamanho também era até esse dia.

Troca aqui na loja por defeito de fábrica vale 30 dias depois da compra. A sua foi em 03/02, então esse prazo fechou em 05/03.

O que ainda está aberto é a garantia legal de 90 dias, se for defeito de fabricação. Ela vai até 18/05/2026. Depois dos 30 dias quem responde é o fabricante, e a gente intermedia se você quiser. O prazo da própria Shelby está no certificado que veio na caixa. Eu não chuto esse número. Em geral fica entre 6 meses e 2 anos.

Queda, umidade, mau uso ou conserto feito fora não entram.

Se o ukulele deu problema, me conta o que aconteceu que eu deixo anotado pra equipe. Eles te retornam em até 24 horas úteis. Se foi só arrependimento, nesse pedido o prazo já passou.
