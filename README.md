# Empório da Música — agente de atendimento

Agente de texto para o caso de AI Engineer da Artefact (Helison Dias). Responde clientes da Empório da Música, loja fictícia de instrumentos em Campo Grande, Mato Grosso do Sul. As respostas ao cliente são em português.

O agente consulta preço, estoque e pedido com ferramentas sobre os CSVs, e lê as regras da loja num índice de seções do manual. O histórico da conversa fica na sessão do CLI.

## Como rodar

Python 3.11 ou mais novo. O projeto foi verificado no 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Sem chave de API, para conferir a camada de dados:

```bash
python -m pytest
python -m emporio.demo
python main.py --demo
```

Conversa, depois de colocar a chave no `.env` ou no ambiente:

```bash
python main.py
python main.py --verbose
python main.py --once "Quanto custa o Takamine GD20?"
python -m emporio
```

Dentro do chat: `/limpar` zera a sessão, `/sair` encerra. Repetir `--once` monta uma conversa curta de vários turnos. O histórico vive no processo. Não é gravado em disco.

Se a chave faltar, o CLI sai com código 2 e aponta o demo e os testes.

## Provedor e modelo

Um cliente compatível com a API da OpenAI. O provedor segue a chave que estiver definida.

| Variável | Efeito |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI. Modelo padrão `gpt-4.1-mini`. |
| `OPENAI_BASE_URL` | Opcional. Aponta para outro gateway compatível. Ajuste `LLM_MODEL`. |
| `GEMINI_API_KEY` ou `GOOGLE_API_KEY` | Endpoint compatível do Gemini. Modelo padrão `gemini-3.8-flash`. |
| `GEMINI_BASE_URL` | Opcional. Padrão `https://generativelanguage.googleapis.com/v1beta/openai/`. |
| `LLM_PROVIDER` | `openai` ou `gemini`. Só é necessário quando as duas chaves existem. Se estiver vazio, usa OpenAI. |
| `LLM_MODEL` | Troca o nome do modelo padrão. |
| `EMPORIO_TODAY` | Relógio da loja. Vazio significa `2026-03-25`. |
| `EMPORIO_DATA_DIR` | Pasta alternativa para os CSVs e o PDF. |

`gpt-4.1-mini` é o padrão porque segue tool calling sem etapa de raciocínio, que é o que este loop precisa. A OpenAI marcou esse id como deprecated. Se a conta recusar o nome, use `LLM_MODEL=gpt-5-mini` ou `LLM_MODEL=gpt-4o-mini`. Para `gpt-5*` o cliente manda `reasoning_effort=low` e não manda `temperature`. Se a API recusar um desses campos, tenta de novo sem ele.

`gemini-3.8-flash` é o id que a documentação atual de compatibilidade da Google mostra. O Flash pode gastar tokens pensando. Se o turno ficar lento ou o loop de ferramenta travar, troque `LLM_MODEL` por outro flash que a sua chave aceite.

Não commite o `.env`. O `.env.example` só lista as variáveis.

Os arquivos em `examples/` não saíram de um modelo ao vivo. Não havia chave de API no ambiente em que o projeto foi montado. O texto foi escrito a partir da saída das ferramentas e é checado por `tests/test_examples.py`.

## Estrutura

```
main.py                     entrada do CLI (python main.py)
emporio/cli.py              argparse e loop da sessão
emporio/agent/prompts.py    persona e regras das ferramentas
emporio/agent/loop.py       loop de tool calling e histórico em memória
emporio/agent/llm.py        cliente OpenAI / Gemini
emporio/scope.py            aviso de acessório versus instrumento
emporio/tools/              catálogo, pedidos, pós-venda, schemas
emporio/retrieval/          seções do manual e busca BM25
emporio/data/loader.py      carga dos CSVs
emporio/demo.py             caminho offline, sem modelo
data/                       CSVs e PDF do manual
examples/                   cinco conversas
tests/                      testes offline
```

## Arquitetura

```
mensagem do cliente
    -> histórico da sessão
    -> aviso de acessório, quando a mensagem pede um
    -> LLM com tool calling
         search_products / get_product     produtos + promoções
         list_categories
         list_active_promotions
         lookup_order                      pedidos + clientes + itens
         evaluate_aftersales               prazos do manual, calculados
         search_policies                   seções do manual
    -> resposta em português
```

O loop é um tool loop simples, sem framework. No máximo seis rodadas de ferramenta por turno. O modelo vê o prompt de sistema, os turnos anteriores e o JSON de cada ferramenta. `--verbose` imprime o nome e os argumentos no stderr.

Por que este formato:

- Preço, estoque e status de pedido são linhas. Uma ferramenta que filtra isso é mais fácil de testar do que pedir ao modelo para ler o CSV, e ele não "lembra" um preço que não veio no resultado.
- O manual tem oito páginas e títulos estáveis. Índice de seções mais BM25 chega. Embedding pediria outra API e um banco vetorial, sem recuperar nada que o título da seção já não aponte. Se o manual crescer, as mesmas seções podem ser embedadas depois, sem trocar a ferramenta que o modelo chama.
- Prazo é conta de calendário. O modelo é instruído a não fazer essa conta. `evaluate_aftersales` devolve `within_time_window` e a data limite. O modelo ainda redige a frase, e ainda chama `search_policies` para a redação ficar presa ao manual.
- Pandas ou SQLite também serviriam. São 65 produtos e 20 pedidos. O loader usa o módulo `csv` da biblioteca padrão e `Decimal`, para `799.9` não virar float. Essa é a camada de dados inteira.

A persona segue a seção 7 do manual: informal e profissional, português do Brasil, "você", sem emoji, sem abertura de robô. A frase da casa é "Sua música começa aqui." O agente se apresenta como o atendimento da loja, não como nome de modelo.

## Dados

Os nomes dos arquivos foram encurtados. Os bytes são os do pacote do desafio.

| Neste repositório | Nome original |
| --- | --- |
| `data/products.csv` | `desafio_tecnico_ai_eng - products.csv` |
| `data/promotions.csv` | `desafio_tecnico_ai_eng - promotions.csv` |
| `data/customers.csv` | `desafio_tecnico_ai_eng - customers.csv` |
| `data/categories.csv` | `desafio_tecnico_ai_eng - categories.csv` |
| `data/order_items.csv` | `desafio_tecnico_ai_eng - order_items.csv` |
| `data/orders.csv` | `desafio_tecnico_ai_eng - orders.csv` |
| `data/politicas_da_loja.pdf` | `políticas_da_loja.pdf` |

O que o loader normaliza:

- Dinheiro fica em `Decimal`. Os rótulos usam o agrupamento brasileiro (`R$ 2.199,00`).
- `is_active` é `0` ou `1`. Só `1` muda o preço. Se dois descontos ativos caírem no mesmo SKU, vale o maior. Neste arquivo eles não se sobrepõem.
- O preço de venda é o de tabela depois do desconto ativo. Um filtro como "até R$ 1000" usa o preço de venda, que é o que o cliente pagaria.
- O PIX é 5% sobre o preço de tabela, e só quando não há promoção ativa (seção 6.2 do manual). A ferramenta devolve `pix_price_label: null` em preço promocional.
- `specs` é JSON. Se o parse falhar, a carga para.
- Disponibilidade é derivada, não está numa coluna: `active` com estoque acima de zero é disponível; `active` com estoque zero é esgotado; `coming_soon` não está à venda mesmo com estoque (produto 130, estoque 2); `discontinued` saiu do catálogo (produtos 113 e 136).
- O item do pedido não tem preço unitário. A ferramenta mostra o nome, a quantidade e o total cobrado. Não recalcula o pedido com o preço de hoje.
- Telefone e e-mail do cliente são mascarados antes de chegar ao modelo (`final 7821`, `a***@domain`). Um nome que casa com mais de um cliente devolve os nomes e as cidades, sem os pedidos.

### Linhas do catálogo que discordam de si

Seis produtos têm descrição de uma marca diferente da marca do nome: 135, 137, 139, 140, 142 e 144 (o baixo "Music Man", por exemplo, é descrito como um Fender Jazz Bass). Alguns blocos de spec também estão copiados entre SKUs (os três teclados compartilham o mesmo objeto). A ferramenta marca `description_conflicts_with_name` ou `specs_are_shared`, esconde o texto inseguro, e o prompt proíbe citá-lo. Preço, estoque, status e nome permanecem.

O nome é o título do SKU. A descrição não é corrigida no CSV, para o arquivo original ficar intacto.

### Relógio da loja

A data mais recente de pedido no arquivo é 22/03/2026. O relógio de um notebook em novembro de 2026 faria todo prazo de troca parecer vencido e todo pedido em aberto parecer abandonado. `EMPORIO_TODAY` vale `2026-03-25` por padrão, alguns dias depois desse recorte. Dá para sobrescrever e testar outras janelas. A ferramenta de pós-venda e o prompt de sistema usam essa data.

### Conflitos do manual, e a leitura deste projeto

O manual e as tabelas não fecham em tudo. O agente não discute isso com o cliente, a menos que perguntem.

| Conflito | Leitura adotada |
| --- | --- |
| A capa e a seção 1.2 listam (67) 3341-4444 como telefone e WhatsApp. A seção 7 nomeia o WhatsApp (67) 3321-4500. | 3341-4444 é o telefone da loja. 3321-4500 é o canal de WhatsApp. |
| A seção 1.2 imprime `contato@empóriodamusica.com.br`. A capa imprime `contato@emporiodamusica.com.br`. | O endereço da capa, sem acento. O domínio acentuado é tratado como erro de digitação. |
| A tabela de pagamento fala em crédito até 12x com parcela mínima de R$ 100. A seção 3.1 é mais fina: até 3x sem mínimo, exceto abaixo de R$ 50; 4x a 6x com mínimo de R$ 80; 7x a 12x com mínimo de R$ 100. | Vale a seção 3.1. A frase "abaixo de R$ 50" é citada como está. Não vira uma regra nova. |
| A seção 1 diz que o catálogo tem mais de 300 instrumentos. O CSV tem 65 produtos, e as categorias 6, 7 e 8 estão vazias. | O que pode ser vendido é o CSV. A frase dos 300 é texto institucional. |
| A seção 7.1 manda sugerir loja parceira para acessório. O pacote não traz essa lista. | Recusar o acessório. Não inventar nome de loja. Dizer que o balcão pode indicar. |
| A descrição da categoria 3 fala em peças avulsas de percussão. Não há esse SKU, e a seção 1 diz que a loja só vende instrumento. | Responder a partir das linhas de produto. |
| Os pedidos têm rastreio e previsão de entrega, e não têm marca de venda de balcão. Não há coluna de data de recebimento. | Todo pedido é tratado como venda à distância. Se o pedido está entregue e o cliente não diz quando recebeu, a previsão é usada e marcada como suposta. Caso contrário, o agente pergunta. Arrependimento: 7 dias corridos após o recebimento, prazo inclusive (`recebimento + 7`). Troca por defeito na loja: 30 dias após a data da compra. Garantia legal: 90 dias após o recebimento. |
| O exemplo de rastreio do manual tem cara de código dos Correios. A linha do pedido não diz a transportadora. | Informar o código. Dizer que dá para consultar nos Correios ou na Jadlog. Não escolher uma. |

Promoções inativas continuam em `get_product`, no campo `inactive_promotions`, para o agente poder dizer que uma oferta que o cliente lembra não está valendo. Elas não mudam `sale_price_label`. O Takamine GD20 (id 95) é o caso claro: tabela R$ 2.199,00, PIX R$ 2.089,05, oferta de 12% "Oferta Especial" com `is_active = 0`.

## Exemplos

| Arquivo | O que mostra |
| --- | --- |
| `examples/01_violao_ate_1000.md` | 12 violões em estoque até R$ 1.000, mais o esgotado e o descontinuado nessa faixa. O segundo turno indica nylon para iniciante. |
| `examples/02_endereco_e_horario.md` | Endereço, sábado, telefone e WhatsApp. |
| `examples/03_preco_takamine_gd20.md` | Preço do GD20, a oferta de 12% inativa, os dois violões que estão em promoção, e a Black Friday vencida do Woodstock. |
| `examples/04_arrependimento_pedido_7.md` | Política de troca no pedido 7, com recebimento em 17/02/2026. O arrependimento fechou. A garantia legal segue aberta até 18/05/2026. |
| `examples/05_pedido_8_e_acessorio.md` | O pedido 8 continua "enviado" 25 dias depois da previsão. Corda e amplificador são recusados. |

## Testes

`python -m pytest` carrega os CSVs e o PDF de verdade. Confere o filtro dos 12 violões, o preço do GD20, as quatro promoções ativas, o mascaramento do pedido, as janelas do pedido 7, as frases do manual no PDF e no índice, a trava de acessório, um turno falso de tool calling que guarda o histórico, e as frases em `examples/`. A suíte não chama API de modelo.

## Limitações, e o que eu faria depois

- O modelo ainda pode pular uma ferramenta e inventar uma frase. As travas são o prompt, o aviso de acessório, a recusa de busca só de acessório e a ferramenta de data. Em produção eu rejeitaria uma resposta com preço ou data que não apareceu no retorno da ferramenta.
- A consulta de pedido confia em quem digita o id. Mascarar o telefone não é autenticação. O passo seguinte é conferir o telefone ou o e-mail da ficha do cliente antes de falar o pedido.
- Não há API de rastreio ao vivo, nem cotação de frete, nem pagamento. Fora de Campo Grande a resposta fica em "o frete é calculado pelo CEP". O frete da região (grátis acima de R$ 500, senão R$ 35, 1 a 3 dias úteis) só é dito quando a ferramenta de política devolve esse texto.
- Reclamação para na frase das 24 horas úteis do manual. Não há fila nem passagem para uma pessoa.
- O índice de seções foi transcrito do PDF porque as tabelas extraem com colunas quebradas. `policy_alignment()` falha se uma frase-chave sumir do PDF ou do índice. Um manual maior deveria ser repartido de novo e, aí sim, embedado, com este índice como base.
- Várias descrições de guitarra, baixo, bateria e teclado são sintéticas e contradizem o nome. Eu devolveria essa lista para a loja e pararia de afirmar detalhe técnico nesses SKUs até a linha ser corrigida. O agente já se recusa a citá-las.
- A memória da sessão é o processo do CLI. Um canal de WhatsApp precisaria de um armazenamento por id da conversa, além da regra de cinco minutos da seção 7.
- Os ids de modelo padrão envelhecem. `LLM_MODEL` existe de propósito para isso.
- Isto não foi executado com chave ao vivo aqui, então a redação dos exemplos é a voz pretendida, não uma completion capturada. Com chave, o passo seguinte é um conjunto de avaliação das cinco conversas: se o rastro chamou a ferramenta e o id certos, e se a resposta trouxe o preço e o prazo certos.

## Uso de assistente de código

Um assistente de código (Cursor) foi usado para implementar este projeto. Helison dirigiu a abordagem, revisou as decisões e é o responsável pela entrega.
