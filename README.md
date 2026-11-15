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
├── agent_tools/                # Núcleo determinístico (regras de negócio)
│   ├── state.py                # Fases do fluxo + checklist de viabilidade (SQLite)
│   ├── pantry.py               # Ingestão do xlsx, consulta de estoque, preço unitário
│   ├── recipes.py              # Cascata de scraping: busca → JSON-LD → LLM
│   ├── conversions.py          # Tabela de conversão de unidades (colher, xícara...)
│   ├── basket.py               # Cesta de compras deduplicada + reserva de orçamento
│   ├── pricing.py              # CMV por porção + cenários de preço (determinístico)
│   └── menu.py                 # Geração do cardápio de lançamento (Markdown + PDF)
├── hermes-plugin/sabor-da-maria/  # Plugin Hermes: expõe o núcleo como 18 tools
│                                 # nativas sabor_* (o agente não escreve Python)
├── config/                     # Configuração do Hermes (modelos, subagentes, WhatsApp)
│   └── locales/                # Overlay que silencia mensagens de bastidor
├── ROTEIRO_DEMO.md             # Roteiro de gravação do fluxo ponta a ponta
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

# 3. Criar o ambiente virtual do projeto (deps: openpyxl, reportlab; pypdf p/ testes)
python3 -m venv .venv
.venv/bin/pip install openpyxl reportlab pypdf

# 4. Instalar o plugin de tools nativas (18 tools sabor_*)
ln -sfn "$PWD/hermes-plugin/sabor-da-maria" ~/.hermes/plugins/sabor-da-maria
hermes plugins enable sabor-da-maria
hermes config set platform_toolsets.whatsapp '["hermes-whatsapp", "sabor"]'

# 5. Silêncio de bastidor: overlay de locales + flag de notificações
cp config/locales/*.yaml ~/.hermes/locales/   # criar o diretório se preciso
hermes config set platforms.whatsapp.gateway_restart_notification false
# + HERMES_GATEWAY_BUSY_ACK_ENABLED=false no EnvironmentVariables do plist
#   (~/Library/LaunchAgents/ai.hermes.gateway.plist) — ver config/hermes.config.yaml

# 6. Rodar os testes do núcleo determinístico
.venv/bin/python -m unittest discover -s tests -v
```

O `AGENTS.md` deste repositório é o context file da consultora (persona,
regras invioláveis, fluxo por fases) — o Hermes o carrega automaticamente
como contexto do workspace.
