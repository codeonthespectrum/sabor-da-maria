# Roteiro de demo — Sabor da Maria

Gravação/apresentação do fluxo ponta a ponta no WhatsApp. O ambiente já está
preparado: fase `briefing`, despensa com 37 itens, zero pratos, sessão nova
(criada na primeira mensagem), gateway silencioso (nenhuma mensagem de
bastidor aparece no chat).

## O que demonstrar (ordem)

1. **Abertura + elicitação** — mande `oi`
   - Esperado: ela se apresenta como consultora, confirma a despensa e o
     orçamento de R$ 80 e começa a perguntar da cozinha (fogão, forno,
     panela de pressão, habilidades) — **sem sugerir prato nenhum**.
2. **Elicitação completa** — responda como a Dona Maria:
   - "Fogão de 4 bocas, tenho forno sim, panela de pressão tenho. Massa
     fresca não sei fazer. Consigo cozinhar umas 2 horas por dia."
   - Esperado: ela registra as respostas e só ENTÃO parte para as receitas.
3. **Descoberta** — ela busca receitas reais que aproveitam a despensa.
   - Se uma página não tiver receita estruturada, a extração é delegada ao
     subagente (Luna) — retorno em ~3s, invisível para a "cliente".
   - Esperado: 2-3 candidatas com pergunta de feedback ("gosta de fazer?").
4. **Viabilidade** — escolha uma candidata. Esperado: perguntas de
   confirmação específicas da receita (utensílio, técnica, tempo) antes de
   aceitar. Se faltar algo, ela propõe substituição em vez de descartar.
5. **Precificação** — após aceitar:
   - Esperado: custo por marmita explicado em linguagem simples, taxa de
     10% da plataforma, 2-3 cenários com a matemática visível (preço,
     quanto ela recebe, lucro) — e a decisão é DELA. Escolha um preço.
   - Repita para 2-3 pratos se quiser mostrar a cesta consolidando.
6. **Cardápio** — peça para fechar:
   - Esperado: PDF do cardápio de lançamento entregue no próprio WhatsApp,
     com pratos (nomes bonitos), custos, lista de compras e sobra do
     orçamento. Comentário sobre sobras de embalagem ("vai sobrar meia
     caixinha...").

## O que NÃO deve aparecer (checklist de bastidor)

- Nenhuma bolha técnica: "Working", "terminal", "gateway online", "Hermes
  is shutting down", "home channel", aviso de ocupado.
- Nenhum jargão na fala dela: "CMV", "checklist", "fase", "tool", "prompt".
- Nenhuma conta feita "de cabeça" — todos os números vêm das tools.

## Latências esperadas

- Respostas simples (elicitação): ~10-20s.
- Busca de receitas / precificação: ~30-90s (chamadas sequenciais de API).
- Delegação ao subagente: ~3s (invisível no fluxo).

## Reset para outra rodada

```bash
sqlite3 data/sabor.db "DELETE FROM precos WHERE origem='complemento'; \
  DELETE FROM checklist_viabilidade; DELETE FROM prato_ingredientes; \
  DELETE FROM pratos; UPDATE consultoria SET fase='briefing' WHERE rowid=1;"
hermes sessions list   # achar a sessão do WhatsApp (título 'Saudação amigável')
hermes sessions delete <id> --yes
hermes gateway restart
```
