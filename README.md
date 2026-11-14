# Sabor da Maria — Consultora de Cardápio e Precificação

Agente Hermes (Nous Research) customizado para conduzir a Dona Maria da despensa ao cardápio de lançamento do seu delivery.

> Desafio técnico — AI Engineer. Enunciado em `desafio-senior-ai-engineer.md`.

## Decisões de arquitetura

Todas as decisões não-triviais estão justificadas em `docs/adr/`:

- [ADR 0001 — Orçamento mede compra, CMV mede consumo](docs/adr/0001-dois-livros-caixa.md)
- [ADR 0002 — Gate estrutural de viabilidade em código, não em prompt](docs/adr/0002-gate-estrutural-de-viabilidade.md)
- [ADR 0003 — Roteamento dual de modelos: Sonnet conversa, Luna executa](docs/adr/0003-roteamento-dual-de-modelos.md)
- [ADR 0004 — Cascata de scraping: busca interna → JSON-LD → LLM](docs/adr/0004-cascata-de-scraping.md)

O glossário do domínio (linguagem compartilhada, sem implementação) está em `CONTEXT.md`.

## Estrutura

```
.
├── CONTEXT.md                  # Glossário do domínio
├── docs/adr/                   # Architecture Decision Records
├── despensa_dona_maria.xlsx    # Dados de entrada (abas Despensa e Precos)
├── agent_tools/                # Tools customizadas registradas no Hermes
│   ├── state.py                # Fases do fluxo + checklist de viabilidade (SQLite)
│   ├── pantry.py               # Ingestão do xlsx, consulta de estoque, preço unitário
│   ├── recipes.py              # Cascata de scraping: busca → JSON-LD → LLM
│   ├── conversions.py          # Tabela de conversão de unidades (colher, xícara...)
│   ├── basket.py               # Cesta de compras deduplicada + reserva de orçamento
│   ├── pricing.py              # CMV por porção + cenários de preço (determinístico)
│   └── menu.py                 # Geração do cardápio de lançamento (Markdown)
├── config/                     # Configuração do Hermes (modelos, subagentes, WhatsApp)
└── tests/                      # Testes das regras de negócio (cesta, CMV, gate)
```

## Regra de ouro

**LLM propõe, código calcula.** Nenhuma aritmética de negócio (CMV, orçamento, preço)
passa por modelo de linguagem. Ver ADR 0003.

## Setup

```bash
# 1. Instalar o Hermes Agent e autenticar no Nous Portal (OAuth, sem API keys)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes setup --portal   # login via navegador; requer assinatura/créditos
                        # em https://portal.nousresearch.com/billing
hermes config set model.default anthropic/claude-sonnet-4.6
hermes config set model.provider nous

# 2. Parear o WhatsApp (use um NÚMERO SECUNDÁRIO — bridge não-oficial)
hermes whatsapp         # exibe QR code; escanear com o WhatsApp do número secundário
hermes gateway start

# 3. Rodar os testes do núcleo determinístico
python -m unittest discover -s tests -v
```

O `AGENTS.md` deste repositório é o context file da consultora (persona,
regras invioláveis, fluxo por fases) — o Hermes o carrega automaticamente
como contexto do workspace.
