# ADR 0004 — Cascata de scraping: busca interna → JSON-LD → LLM

## Status

Aceito — 2026-11-14

## Contexto

O desafio exige pesquisa de receitas reais na internet. As opções eram: API de busca paga/freemium (Tavily, Brave), scraping de buscador genérico (DuckDuckGo), ou scraping direto de sites de receita.

Restrições que pesaram: preferência da desenvolvedora por scraping (experiência prévia com a mesma arquitetura em scraping de shoppings), nenhuma conta externa nova, e custo zero. Além disso, sites grandes de receita (TudoGostoso, Panelinha, Receitas Nestlé) embem `schema.org/Recipe` em JSON-LD para SEO — ingredientes, quantidades e rendimento já vêm estruturados.

## Decisão

Cascata de três níveis, cada um com fallback essencial:

1. **Descoberta**: busca interna do site de receitas (URL de busca com os ingredientes da despensa). Fallback: scraping de buscador genérico.
2. **Extração determinística**: parse do JSON-LD `schema.org/Recipe` da página. Sem LLM, sem custo, exato.
3. **Extração por LLM (Luna)**: apenas quando a página não tem JSON-LD ou ele vem quebrado.

## Consequências

- Zero dependência de API externa e zero custo de busca; fragilidade concentrada em poucos parsers de sites conhecidos.
- O caminho determinístico cobre a maioria dos casos reais; o LLM entra só como rede de segurança.
- Risco aceito: sites podem mudar estrutura ou bloquear scraping — mitigado pelo fallback e por cachear receitas já extraídas.
