# Sabor da Maria — Consultora de Cardápio e Precificação no WhatsApp

Agente de IA que conduz uma cozinheira iniciante **da despensa ao cardápio de
lançamento do seu delivery**, inteiramente pelo WhatsApp: entende o que ela tem
em casa, pesquisa receitas reais, valida se ela consegue executar cada prato,
calcula custos e preços com transparência e entrega o cardápio final em PDF —
sem que ela veja uma única mensagem técnica.

Construído sobre o [Hermes Agent](https://github.com/NousResearch/hermes-agent)
(Nous Research). Desafio técnico de AI Engineer — enunciado em
[`desafio-senior-ai-engineer.md`](desafio-senior-ai-engineer.md).

## Destaques

- **Regra de ouro: o LLM propõe, o código calcula.** Nenhuma aritmética de
  negócio (custo, orçamento, preço) passa por modelo de linguagem — um núcleo
  Python determinístico responde por toda conta, coberto por 38 testes.
- **Gate estrutural de viabilidade.** Nenhum prato entra no cardápio sem
  checklist completo de utensílios, técnicas e restrições operacionais —
  validado em código (SQLite), não em prompt. O agente não consegue contornar.
- **Roteamento dual de modelos.** Claude Sonnet 4.6 conduz a conversa; um
  subagente barato (Luna) faz extrações pontuais em ~3s (medido; requisito ≤5s).
- **Plugin Hermes com 18 tools nativas.** O agente chama `sabor_*` com schema
  tipado em vez de escrever Python livre — fim dos erros de assinatura que
  custavam latência a cada turn.
- **Bastidor 100% invisível.** Restart do gateway, avisos de sistema, progresso
  de tools: nada disso chega ao chat. Supressão em duas camadas (config +
  overlay de locales), validada em log.
- **Linguagem da Dona Maria, sempre.** Português coloquial e caloroso; siglas
  e jargões ("CMV", "checklist") existem no código, nunca na boca da consultora.

## Como funciona

O fluxo tem fases explícitas persistidas em SQLite — a conversa pode parar e
retomar dias depois de onde parou:

| Fase | O que acontece |
|---|---|
| **briefing** | Despensa (37 itens, ingerida de planilha) e orçamento de R$ 80 confirmados |
| **descoberta** | Busca de receitas **reais** na web que aproveitem o que ela já tem |
| **viabilidade** | Elicitação ativa: fogão, forno, panela de pressão, habilidades, tempo — antes de aceitar qualquer prato |
| **precificacao** | Custo por marmita explicado, taxa de 10% da plataforma, 2-3 cenários com a matemática visível — a decisão de preço é **dela** |
| **cardapio** | PDF de lançamento (pratos, custos, lista de compras, sobra do orçamento) entregue no próprio chat |

Se uma página de receita não tem dados estruturados (JSON-LD), uma cascata de
scraping delega a extração ao subagente. Se um prato não fecha (falta
equipamento, estoura o orçamento), o agente propõe substituição antes de
descartar.

**Veja funcionando:** [`docs/demo/demo.mp4`](docs/demo/demo.mp4) — vídeo de
~1min45 da sessão real, do `oi` ao PDF (a conversa aconteceu de verdade no
WhatsApp; o vídeo é uma renderização fiel da transcrição, que está integral em
[`docs/demo/DEMO.md`](docs/demo/DEMO.md) com o mapa dos bastidores). O cardápio
gerado está em [`docs/demo/cardapio_lancamento.pdf`](docs/demo/cardapio_lancamento.pdf).
Para reproduzir ao vivo, siga o [`ROTEIRO_DEMO.md`](ROTEIRO_DEMO.md).

## Testando ao vivo (qualquer número)

O bot está com **acesso aberto**: qualquer número de WhatsApp pode mandar
mensagem e conversar com a consultora — sem pareamento nem aprovação prévia.

Duas observações de escopo, por decisão de design:

- **Uma cliente por vez.** O desafio pede a jornada de *uma* cozinheira (a
  Dona Maria), então a consultoria é única e compartilhada: fase, pratos e
  preços vivem numa única linha de estado. Isolamento por número seria
  multi-tenancy — fora do que foi pedido.
- **Reset entre testadores.** Depois que alguém conclui (ou abandona) uma
  consultoria, rode `bash scripts/reset_demo.sh` para zerar fase, pratos e
  preços — a despensa de 37 itens permanece. A pessoa seguinte manda `oi` e
  começa do zero.

## Arquitetura

```
Dona Maria (WhatsApp)
        │
  Hermes Gateway ── Sonnet 4.6 (conversa, tom, condução do fluxo)
        │                    │
        │                    └─ delegação ≤5s ── Luna (extração de receitas,
        │                                           normalização fora da tabela)
        ▼
  Plugin sabor-da-maria (18 tools nativas, JSON em/pt-BR)
        ▼
  Núcleo determinístico (agent_tools/) ── SQLite
  state · pantry · recipes · conversions · basket · pricing · menu
```

Todas as decisões não-triviais estão justificadas em ADRs:

- [ADR 0001 — Orçamento mede compra, CMV mede consumo](docs/adr/0001-dois-livros-caixa.md)
- [ADR 0002 — Gate estrutural de viabilidade em código, não em prompt](docs/adr/0002-gate-estrutural-de-viabilidade.md)
- [ADR 0003 — Roteamento dual de modelos: Sonnet conversa, Luna executa](docs/adr/0003-roteamento-dual-de-modelos.md)
- [ADR 0004 — Cascata de scraping: busca interna → JSON-LD → LLM](docs/adr/0004-cascata-de-scraping.md)

O glossário do domínio (linguagem compartilhada, sem implementação) está em
[`CONTEXT.md`](CONTEXT.md); a persona e as regras invioláveis da consultora, em
[`AGENTS.md`](AGENTS.md).

## Stack

| Camada | Tecnologia |
|---|---|
| Agente / gateway | Hermes Agent (Nous Research), sessões persistentes |
| Modelos | Claude Sonnet 4.6 (conversa) · Luna (subagente) — via Nous Portal |
| Canal | WhatsApp (bridge Baileys) |
| Núcleo de negócio | Python 3, SQLite, stdlib + openpyxl + reportlab |
| Testes | unittest — 38 testes de regras de negócio |

## Estrutura do repositório

```
.
├── AGENTS.md                   # Persona, regras invioláveis e fluxo da consultora
├── CONTEXT.md                  # Glossário do domínio
├── ROTEIRO_DEMO.md             # Roteiro de gravação do fluxo ponta a ponta
├── docs/adr/                   # Architecture Decision Records
├── despensa_dona_maria.xlsx    # Dados de entrada (abas Despensa e Precos)
├── agent_tools/                # Núcleo determinístico (regras de negócio)
│   ├── state.py                # Fases do fluxo + checklist de viabilidade
│   ├── pantry.py               # Ingestão do xlsx, estoque, preço unitário
│   ├── recipes.py              # Cascata de scraping: busca → JSON-LD → LLM
│   ├── conversions.py          # Conversão de unidades (colher, xícara...)
│   ├── basket.py               # Cesta deduplicada + reserva de orçamento
│   ├── pricing.py              # CMV por porção + cenários de preço
│   └── menu.py                 # Cardápio de lançamento (Markdown + PDF)
├── hermes-plugin/sabor-da-maria/  # Plugin Hermes: 18 tools nativas sabor_*
├── config/                     # Config do Hermes (modelos, subagentes, WhatsApp)
│   └── locales/                # Overlay que silencia mensagens de bastidor
└── tests/                      # Testes das regras de negócio (cesta, CMV, gate)
```

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
mkdir -p ~/.hermes/locales && cp config/locales/*.yaml ~/.hermes/locales/
hermes config set platforms.whatsapp.gateway_restart_notification false
# + HERMES_GATEWAY_BUSY_ACK_ENABLED=false no EnvironmentVariables do plist
#   (~/Library/LaunchAgents/ai.hermes.gateway.plist) — ver config/hermes.config.yaml
```

## Testes

```bash
.venv/bin/python -m unittest discover -s tests -v   # 38 testes
```

Cobrem as regras de negócio do núcleo: conversão de unidades, ingestão da
planilha, cesta com deduplicação e reserva de orçamento, gate de viabilidade,
CMV e cenários de preço, e os artefatos finais (Markdown e PDF sem jargão).

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/demo/DEMO.md`](docs/demo/DEMO.md) | Transcrição de sessão real + PDF do cardápio gerado |
| [`CONTEXT.md`](CONTEXT.md) | Glossário do domínio (CMV, cesta, porção, gate...) |
| [`AGENTS.md`](AGENTS.md) | Persona e regras invioláveis da consultora |
| [`ROTEIRO_DEMO.md`](ROTEIRO_DEMO.md) | Roteiro de demonstração + reset entre rodadas |
| [`config/hermes.config.yaml`](config/hermes.config.yaml) | Toda a configuração do Hermes, comentada decisão a decisão |
| [`docs/adr/`](docs/adr/) | Porquês das decisões de arquitetura |
