# CONTEXT — Sabor da Maria

Glossário do domínio. Somente linguagem de negócio — nada de implementação.

## Pessoas

- **Dona Maria** — cozinheira e dona do delivery *Sabor da Maria*. Usuária do agente. Não é técnica: não se assume que saiba o que é uma planilha ou arquivo.
- **Agente (a Consultora)** — o assistente de IA que conduz a Dona Maria da despensa ao cardápio de lançamento.

## Ingredientes e dinheiro

- **Despensa** — conjunto de ingredientes que a Dona Maria já possui, com quantidade e unidade. Fonte inicial: a planilha entregue por ela.
- **Preço unitário** — quanto custa uma unidade de medida de um ingrediente (ex.: R$/kg). Derivado de `preço total pago ÷ quantidade comprada`, cruzando as duas abas da planilha.
- **Orçamento de complementos** — o dinheiro que ela ainda pode gastar comprando o que falta. Valor inicial: R$ 80,00.
- **Complemento** — ingrediente necessário a um prato que não existe (ou não basta) na despensa e precisa ser comprado.
- **Sobra** — parte de uma embalagem comprada que não é consumida pela receita (ex.: meia caixinha de creme de leite). É mencionada na conversa, mas não é rastreada formalmente.

## Os dois livros-caixa

Regra central do domínio: orçamento e CMV medem coisas diferentes e nunca se misturam.

- **Orçamento mede compra** — o dinheiro que sai do bolso hoje, pelo preço cheio da embalagem. Não se compra meia caixinha.
- **CMV mede consumo** — o custo do que vai dentro da marmita: `quantidade usada × preço unitário`, somado sobre todos os ingredientes da receita, incluindo os complementos comprados.

## Receitas e pratos

- **Receita candidata** — receita real encontrada na internet que aproveita a despensa, ainda não validada com a Dona Maria.
- **Checklist de viabilidade** — as três verificações obrigatórias antes de aceitar um prato: **utensílios/equipamentos**, **técnicas/habilidades** e **restrições operacionais** (energia, gás, espaço, tempo). Cada item está pendente até a Dona Maria responder — o agente pergunta o que ela não mencionar espontaneamente.
- **Prato aceito** — receita candidata que a Dona Maria aprovou **e** cujo checklist de viabilidade está completo. Aceite com pendência no checklist não existe: é bloqueado.
- **Cesta de compras** — o conjunto deduplicado de complementos de todos os pratos aceitos. Itens repetidos somam quantidades; a quantidade total determina quantas embalagens comprar.
- **Reserva de orçamento** — o valor comprometido do orçamento no momento em que um prato é aceito, calculado a partir da cesta. Desistir de um prato recalcula a cesta e libera a reserva correspondente.

## Venda

- **Porção (marmita)** — unidade de venda do delivery.
- **Rendimento** — quantas porções uma receita produz. Vem da receita ou da Dona Maria.
- **CMV por porção** — CMV da receita ÷ rendimento. É a base do preço.
- **Taxa da plataforma** — 10% sobre o preço de venda. Se o preço é P, a Dona Maria recebe 0,90·P.
- **Preço mínimo** — `CMV por porção ÷ 0,90`. Abaixo disso, ela perde dinheiro em cada venda.
- **Cenário de preço** — uma proposta de preço com margem definida, apresentada com a matemática visível. O agente propõe 2–3 cenários; **a decisão é sempre da Dona Maria**.
- **Cardápio de lançamento** — o artefato final: a lista de pratos aceitos, cada um com ingredientes, CMV por porção, cenários de preço e o preço escolhido por ela.

## Fluxo

- **Fases da consultoria** — `briefing → descoberta → viabilidade → precificação → cardápio`. A conversa pode retroceder (ela pode mudar de ideia), mas o agente nunca perde de vista em que fase está.
- **Substituição** — quando um prato não fecha (falta equipamento, estoura orçamento), o agente primeiro propõe adaptar a receita usando a despensa; só descarta se não houver alternativa. Todo descarte registra o motivo.
