# ADR 0003 — Roteamento dual de modelos: Sonnet conversa, Luna executa

## Status

Aceito — 2026-11-14

## Contexto

A consultoria tem duas cargas de trabalho muito diferentes:

1. **Conversa multi-turno em pt-BR informal** com elicitação sutil de restrições — exige o melhor modelo de diálogo disponível.
2. **Tarefas delimitadas e repetitivas** — extrair ingredientes estruturados de HTML raspado, normalizar unidades ("1 xícara" → gramas), classificar técnicas — onde um modelo barato e rápido basta.

Usar um modelo frontier para tudo paga preço de conversa em tarefa de extração; usar um modelo barato para tudo arrisca o requisito mais importante (a elicitação).

## Decisão

- **Claude Sonnet (Anthropic)** dirige toda a conversa com a Dona Maria.
- **GPT-5.6 Luna (OpenAI)** executa as tarefas delimitadas como subagente (o Hermes suporta provider/modelo separado para subagentes nativamente).
- **Nenhum LLM faz aritmética de negócio**: CMV, cesta de compras, orçamento e cenários de preço são código Python determinístico. Regra: *LLM propõe, código calcula.*

## Consequências

- Duas chaves de API e dois providers para configurar no Hermes — complexidade operacional pequena, aceita.
- O custo por sessão de demonstração cai para centavos, permitindo iterar muito durante o desenvolvimento.
- Se o Luna falhar numa extração, o fallback é o próprio Sonnet (mais caro, mas a conversa não para).
