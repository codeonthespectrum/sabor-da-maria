# Demo — conversa real no WhatsApp

Transcrição **integral e não editada** de uma sessão real (15/11/2026), do
`oi` ao cardápio em PDF. Só aparecem as mensagens trocadas no chat; as 45
chamadas de tools que aconteceram nos bastidores estão resumidas fase a fase
no final. O artefato entregue está nesta pasta:
[`cardapio_lancamento.pdf`](cardapio_lancamento.pdf).

> Modelo da conversa: Claude Sonnet 4.6 · extrações delegadas: Luna ·
> núcleo de cálculo: `agent_tools/` (determinístico, zero aritmética no LLM)

---

## 1. Abertura — confirmação do briefing

*O que demonstra: o agente consulta a fase antes de qualquer resposta
(`get_phase` → `briefing`), confirma despensa e orçamento de R$ 80, e se
apresenta como consultora — nunca como "assistente de IA".*

**Dona Maria:** oi

**Consultora:**
Oi, dona Maria! Que alegria ter você por aqui! 🎉

Sou a consultora que vai te ajudar a montar o cardápio do *Sabor da Maria* —
do começo ao fim, com tudo certinho: receitas reais, custos calculados,
preços que fazem sentido e um cardápinho bonito pra você lançar seu delivery!

Já vi aqui que você tem uma despensa com vários ingredientes carregados, e
vamos trabalhar com um orçamento de **R$ 80** pra compras do que faltar.
Isso tá certinho pra você?

Me conta: tá animada pra começar? 😄

**Dona Maria:** Estou sim!

**Consultora:**
Que ótimo! Vamos lá, dona Maria! 🍳

Já dei uma olhadinha na sua despensa e você tem muita coisa boa por aí! Olha
só o que já temos:

🥩 *Carnes e proteínas:*
- Peito de frango (2 kg), carne moída patinho (1,5 kg), acém (1 kg), alcatra
  (0,8 kg), bacon (500 g), ovos (30 unidades)

🍚 *Grãos e massas:*
- Arroz (5 kg), feijão carioca (3 kg), feijão preto (1 kg), macarrão espaguete
  (1 kg), polenta/fubá (1 kg)

🥔 *Legumes e verduras:*
- Batata (3 kg), tomate (2 kg), cebola (1 kg), couve, salsinha, alho

🧀 *Laticínios:*
- Leite (2 L), manteiga, mussarela, parmesão, chantilly

🧂 *Temperos e extras:*
- Óleo, sal, açúcar, açafrão, caldo de carne, azeite, entre outros

Uma despensa bem recheada! 😄

Agora, antes de eu sugerir qualquer prato, preciso entender melhor a sua
cozinha pra garantir que tudo vai fluir bem no dia a dia do delivery.

Me conta: *quantas bocas tem seu fogão?* E tem forno? Panela de pressão? 🍲

---

## 2. Elicitação — o coração do desafio

*O que demonstra: nenhuma receita é sugerida antes de conhecer utensílios,
técnicas e restrições operacionais. As perguntas são ativas — resposta
espontânea não basta. Cada resposta vira um item registrado no checklist de
viabilidade (`record_checklist_item`).*

**Dona Maria:** Tenho fogão de 6 bocas, uma geladeira, um freezer, panela de
pressão grande, forno elétrico e forno a gás e uma airfryer

**Consultora:**
Uau, dona Maria, que cozinha equipada! 😍 Fogão de 6 bocas, dois fornos,
airfryer, panela de pressão... você tem tudo que uma cozinha de delivery
precisa!

Anotei tudo aqui. Agora preciso entender um pouquinho sobre o que você
*gosta e sabe fazer*. Isso é super importante pra gente montar um cardápio
que você consiga tocar sem estresse.

Me conta: *o que você mais gosta de cozinhar?* Tem mais habilidade com
comida caseira, massas, grelhados, assados? Sabe fazer fritura bem feita?
Tem alguma coisa que prefere evitar na cozinha? 👩‍🍳

**Dona Maria:** sou muito boa com comida caseira com massas e doces tipo pudim

**Consultora:**
Perfeito, anotado! 👏 Comida caseira, massas e doces — combinação imbatível
pra delivery!

Agora me conta sobre o dia a dia: *quanto tempo você tem disponível pra
cozinhar por dia?* E vai trabalhar sozinha ou tem alguém pra te ajudar?
Pretende entregar todos os dias ou só em certos dias da semana? 🗓️

**Dona Maria:** eu tenho disponibilidade de 6h por dia e posso de segunda a sexta

**Consultora:**
6 horas por dia, de segunda a sexta — tá ótimo, dá pra montar uma operação
bem organizada! 🕕

Agora tenho tudo que preciso pra começar a pesquisar os pratos certos pra
você. Deixa eu buscar receitas que aproveitem bem o que você já tem na
despensa e que se encaixem no seu jeito de cozinhar — comida caseira
gostosa, massas e aquele docinho no final! 🍮

Um segundinho enquanto eu pesquiso... 🔍

---

## 3. Descoberta — receitas reais, da despensa

*O que demonstra: as candidatas vêm de busca real na web (`buscar_receitas` +
`extrair_receita`), filtradas pelo que a despensa já cobre e pelo perfil
elicita­do (comida caseira, massas, doces). Nada foi inventado de cabeça.*

**Consultora:**
Achei três candidatas bem bacanas pra você, dona Maria! 😄 Olha só o que eu
trouxe:

🍗 *1. Frango cremoso com batata (10 porções)*
Filé de frango, batata em rodelas, cebola, leite, mussarela... vai pro forno
e fica aquele corte lindo. Precisa comprar: sopa de cebola, creme de leite e
requeijão.

🍝 *2. Macarrão com carne moída e queijo (8 porções)*
Macarrão, carne moída, molho de tomate, creme de leite e mussarela. Clássico
que todo mundo ama no delivery! Precisa comprar: molho de tomate e creme de
leite.

🍮 *3. Pudim de leite (10 porções)*
Leite condensado, leite, ovos e açúcar — bem no seu estilo de doce! Precisa
comprar: leite condensado.

O que você acha dessas três? Tem alguma que te anima mais? Alguma que você
não gostaria de fazer? Me fala que a gente afina o cardápio! 😊

**Dona Maria:** algum desses eu preciso comprar mais alguma coisa?

**Consultora:**
Olha dona Maria, fiz a conferência certinha com tudo que você já tem! 🔍

🍗 *Frango cremoso com batata*
✅ Frango, batata, cebola, leite, mussarela, sal — tudo em casa!
🛒 Precisa comprar: *sopa de cebola* (1 pacote), *creme de leite*
(1 caixinha), *requeijão* (1 copo)
💡 Margarina pode trocar pela manteiga que você já tem!

🍝 *Macarrão com carne moída e queijo*
✅ Macarrão, carne moída, mussarela — tudo em casa!
🛒 Precisa comprar: *creme de leite* (1 caixinha)
💡 O molho de tomate dá pra fazer na hora com o tomate fresco que você tem!

🍮 *Pudim de leite*
✅ Açúcar, leite, ovos — tudo em casa!
🛒 Precisa comprar: *leite condensado* (1 lata)

A boa notícia é que falta pouquinha coisa! O *creme de leite* aparece em
duas receitas, então se você fizer as três, compra de uma vez só.

Essas três receitas te animam pra começar? Ou tem alguma que prefere deixar
de fora? 😊

---

## 4. Orçamento — a cesta consolida e deduplica

*O que demonstra: ao aceitar os pratos (`accept_dish`), o núcleo cruza
receita × despensa × preços e monta a cesta deduplicada — o creme de leite
de duas receitas vira uma compra só. Orçamento mede **compra**; CMV mede
**consumo** (ADR 0001). Total: R$ 23,00 de R$ 80,00.*

**Dona Maria:** podemos começar com essas!

**Consultora:**
Ótima notícia, dona Maria! Os três pratos estão aprovados e cabem no
orçamento de R$ 80 com folga! 🎉

Pra montar os três pratos, você vai precisar comprar:

🛒 *Lista de compras (tudo junto):*
- 2x Creme de leite (caixinha) → R$ 8,00
- 1x Requeijão (copo) → R$ 7,00
- 1x Sopa de cebola (pacote) → R$ 2,50
- 1x Leite condensado (lata) → R$ 5,50

*Total das compras: R$ 23,00* — sobram R$ 57,00 do orçamento! 💚

💡 O creme de leite aparece nas duas receitas salgadas, então uma caixinha
serve pra cada uma.

Agora vamos falar de preço! Vou calcular o custo de cada porção e te mostrar
quanto cobrar pelo seu delivery. Um instantinho... 🧮

Posso já apresentar os cenários de preço pra cada prato, dona Maria? 😊

---

## 5. Precificação — matemática visível, decisão dela

*O que demonstra: custo por porção calculado em código (`cmv_por_porcao`),
taxa de 10% da plataforma explicada em linguagem simples, três cenários com
preço / repasse / lucro (`cenarios_de_preco`). O agente apresenta — quem
decide é ela. Nenhuma palavra técnica ("CMV") aparece.*

**Dona Maria:** sim, por favor

**Consultora:**
Boa, dona Maria! Fiz a conta certinha pra cada prato. Veja bem 👇

🍗 *Frango cremoso com batata* (10 porções)
_Custo dos ingredientes por porção: R$ 4,52_
A plataforma fica com 10% do preço — o que você recebe de verdade é 90%.

| Cenário | Preço | Você recebe | Lucro por marmita |
|--|--|--|--|
| 💚 Econômico | R$ 9,50 | R$ 8,55 | R$ 4,03 |
| ⭐ Equilibrado | R$ 11,50 | R$ 10,35 | R$ 5,83 |
| 👑 Premium | R$ 15,50 | R$ 13,95 | R$ 9,43 |

🍝 *Macarrão com carne moída e queijo* (8 porções)
_Custo dos ingredientes por porção: R$ 4,37_

| Cenário | Preço | Você recebe | Lucro por marmita |
|--|--|--|--|
| 💚 Econômico | R$ 9,00 | R$ 8,10 | R$ 3,73 |
| ⭐ Equilibrado | R$ 11,00 | R$ 9,90 | R$ 5,53 |
| 👑 Premium | R$ 15,00 | R$ 13,50 | R$ 9,13 |

🍮 *Pudim de leite* (10 porções)
_Custo dos ingredientes por porção: R$ 1,27_

| Cenário | Preço | Você recebe | Lucro por porção |
|--|--|--|--|
| 💚 Econômico | R$ 3,00 | R$ 2,70 | R$ 1,43 |
| ⭐ Equilibrado | R$ 3,50 | R$ 3,15 | R$ 1,88 |
| 👑 Premium | R$ 4,50 | R$ 4,05 | R$ 2,78 |

💡 O pudim tem um custo baixinho — você pode vender como sobremesa avulsa
ou dar de brinde pra fidelizar cliente!

A decisão é sua, dona Maria! Qual cenário te agrada mais em cada prato?
Pode misturar — frango premium e macarrão equilibrado, por exemplo! 😄

---

## 6. Entrega — o cardápio em PDF no próprio chat

*O que demonstra: preços gravados (`registrar_preco_escolhido`), artefato
final gerado pelo núcleo (`gerar_pdf`) e entregue como anexo no WhatsApp.
O PDF traz pratos, custos, cenários e a lista de compras — em linguagem
simples e sem siglas.*

**Dona Maria:** vamos manter todos no equilibrado

**Consultora:**
Perfeito, dona Maria! Preços registrados e cardápio gerado! 🎉

Aqui está o seu cardápio de lançamento do *Sabor da Maria*:

📎 `cardapio_lancamento.pdf` *(anexo enviado no chat — arquivo nesta pasta)*

Resumo do que a gente montou juntas:

🍗 *Frango cremoso com batata* — R$ 11,50
🍝 *Macarrão com carne moída e queijo* — R$ 11,00
🍮 *Pudim de leite* — R$ 3,50

🛒 *Lista de compras (R$ 23,00):*
- 2x Creme de leite
- 1x Requeijão
- 1x Sopa de cebola
- 1x Leite condensado

Sobra R$ 57,00 do orçamento — um bom colchão pra imprevistos! 💚

Parabéns pelo seu primeiro cardápio, dona Maria! O *Sabor da Maria* vai
fazer muito sucesso! 🌟

---

## Nos bastidores — o que o chat não mostra

45 chamadas de tools, zero mensagens de sistema no chat. Sequência real por
fase (esta rodada ainda usava `python -c`; hoje são as tools nativas
`sabor_*` do plugin — mesma sequência, sem latência de terminal):

| Fase | Tools acionadas |
|---|---|
| Abertura | `get_phase` → `briefing`; leitura da despensa |
| Elicitação | 6× `record_checklist_item` (utensílios, técnicas, rotina) + `set_phase` |
| Descoberta | 3× `buscar_receitas`, 2× `extrair_receita`, `definir_prato` |
| Orçamento | 4× `accept_dish` (3 pratos + 1 retentativa guiada após `cadastrar_complemento`) |
| Precificação | 5× `cmv_por_porcao` + `cenarios_de_preco`, `registrar_preco_escolhido` |
| Entrega | `gerar_cardapio` (conferência interna) + `gerar_pdf` (entrega) |

O que a Dona Maria **nunca** viu: nome de tool, traceback, "Working...",
aviso de restart do gateway, ou a palavra "CMV".
