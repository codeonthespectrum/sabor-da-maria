# ADR 0001 — Orçamento mede compra, CMV mede consumo

## Status

Aceito — 2026-11-14

## Contexto

O desafio define o CMV como `quantidade usada × custo unitário` e dá um orçamento de R$ 80 para complementos. Os dois números parecem falar da mesma coisa — "quanto custa o ingrediente" — mas medem grandezas diferentes:

- O **orçamento** é dinheiro que sai do bolso da Dona Maria hoje. Compra-se a embalagem inteira: se a receita usa 100 g de creme de leite, ela paga a caixinha de 200 g.
- O **CMV** é o custo do que vai na marmita: só a fração consumida.

Misturar os dois produz um dos dois erros: CMV inflado (preço de venda acima do necessário, perdendo competitividade) ou orçamento subestimado (o agente diz que sobrou dinheiro que não sobrou).

## Decisão

Dois livros-caixa separados, sempre:

1. Toda compra de complemento afeta o **orçamento** pelo preço cheio da(s) embalagem(ns) necessária(s).
2. Todo cálculo de **CMV** usa exclusivamente `quantidade usada × custo unitário`, conforme o enunciado.
3. A diferença entre os dois (a **sobra**) é mencionada na conversa ("vai sobrar meia caixinha") mas não é rastreada no sistema.

## Consequências

- A cesta de compras (orçamento) e o motor de CMV são módulos separados, com testes separados.
- O agente precisa explicar a distinção à Dona Maria quando ela aparecer — é didaticamente valioso.
- Se um dia quisermos controlar sobras como "novo estoque", a separação já está pronta para recebê-lo.
