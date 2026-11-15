"""Schemas das tools — o que o modelo vê.

Descrições em português, na linguagem do domínio (CONTEXT.md): a tool diz
QUANDO usar e O QUE devolve, para o modelo não precisar adivinhar assinatura
nenhuma — o erro de Python que custava 1-2 chamadas de API por turn morre aqui.
"""

_FASES = "briefing | descoberta | viabilidade | precificacao | cardapio"

GET_PHASE = {
    "name": "sabor_get_phase",
    "description": (
        "Retorna a fase atual da consultoria (" + _FASES + "). "
        "SEMPRE chame antes de qualquer outra coisa ao receber mensagem — "
        "é ela que diz onde a conversa parou."
    ),
    "parameters": {"type": "object", "properties": {}},
}

SET_PHASE = {
    "name": "sabor_set_phase",
    "description": (
        "Atualiza a fase da consultoria. Chame ao concluir cada etapa: "
        "orçamento confirmado → 'descoberta'; candidatas escolhidas → "
        "'viabilidade'; prato aceito → 'precificacao'; preços escolhidos "
        "→ 'cardapio'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "fase": {"type": "string",
                     "description": "Uma de: " + _FASES},
        },
        "required": ["fase"],
    },
}

GET_PANTRY = {
    "name": "sabor_get_pantry",
    "description": (
        "Lista a despensa da Dona Maria: ingredientes e quantidades que ela "
        "JÁ TEM (não precisa comprar). Use na descoberta para propor receitas "
        "que aproveitem o que existe."
    ),
    "parameters": {"type": "object", "properties": {}},
}

TEM_NA_DESPENSA = {
    "name": "sabor_tem_na_despensa",
    "description": (
        "Verifica se há quantidade suficiente de um ingrediente na despensa. "
        "Devolve {tem: true/false, disponivel_na_base}."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ingrediente": {"type": "string"},
            "quantidade": {"type": "number"},
            "unidade": {"type": "string",
                        "description": "kg, g, L, ml, un, xícara, colher de sopa…"},
        },
        "required": ["ingrediente", "quantidade", "unidade"],
    },
}

CADASTRAR_COMPLEMENTO = {
    "name": "sabor_cadastrar_complemento",
    "description": (
        "Cadastra o preço de um ingrediente que NÃO está na despensa e "
        "precisa ser comprado (ex.: creme de leite). Sem preço cadastrado o "
        "cálculo de custo não fecha. O preço vem da conversa ou da busca."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ingrediente": {"type": "string"},
            "qtd_embalagem": {"type": "number",
                              "description": "Conteúdo da embalagem (ex.: 200)"},
            "unidade": {"type": "string",
                        "description": "Embalagem: 'un 200g', 'caixa 1L', 'g', 'ml'…"},
            "preco_embalagem": {"type": "number",
                                "description": "Preço da embalagem inteira em R$"},
        },
        "required": ["ingrediente", "qtd_embalagem", "unidade", "preco_embalagem"],
    },
}

BUSCAR_RECEITAS = {
    "name": "sabor_buscar_receitas",
    "description": (
        "Busca receitas reais na web que usem os ingredientes informados. "
        "Só use DEPOIS de conhecer os utensílios e habilidades da Dona Maria "
        "(elicitação) — nunca antes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ingredientes": {"type": "array", "items": {"type": "string"}},
            "max_resultados": {"type": "integer", "default": 5},
        },
        "required": ["ingredientes"],
    },
}

EXTRAIR_RECEITA = {
    "name": "sabor_extrair_receita",
    "description": (
        "Extrai ingredientes e rendimento de uma página de receita (JSON-LD). "
        "Se devolver erro 'sem_json_ld', chame sabor_extrair_texto_bruto na "
        "mesma URL e delege a extração ao subagente (Luna)."
    ),
    "parameters": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
}

EXTRAIR_TEXTO_BRUTO = {
    "name": "sabor_extrair_texto_bruto",
    "description": (
        "Baixa o texto visível de uma página (sem HTML). Use como insumo "
        "para o subagente quando extrair_receita devolve 'sem_json_ld'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "max_chars": {"type": "integer", "default": 12000},
        },
        "required": ["url"],
    },
}

DEFINIR_PRATO = {
    "name": "sabor_definir_prato",
    "description": (
        "Registra um prato candidato com a receita (ingredientes já na "
        "quantidade da receita inteira). O nome pode ser livre ('Escondidinho "
        "de Batata') — a exibição é embelezada automaticamente."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "nome": {"type": "string"},
            "rendimento_porcoes": {"type": "integer",
                                   "description": "Quantas marmitas a receita rende"},
            "ingredientes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "quantidade": {"type": "number"},
                        "unidade": {"type": "string"},
                    },
                    "required": ["nome", "quantidade", "unidade"],
                },
            },
        },
        "required": ["nome", "rendimento_porcoes", "ingredientes"],
    },
}

RECORD_CHECKLIST_ITEM = {
    "name": "sabor_record_checklist_item",
    "description": (
        "Registra UMA confirmação de viabilidade de um prato, na fala da "
        "Dona Maria. dimensao: 'utensilios', 'tecnicas' ou "
        "'restricoes_operacionais'. status: 'ok', 'falta' ou 'nao_sabe'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prato": {"type": "string"},
            "dimensao": {"type": "string",
                         "enum": ["utensilios", "tecnicas", "restricoes_operacionais"]},
            "status": {"type": "string", "enum": ["ok", "falta", "nao_sabe"]},
            "detalhe": {"type": "string",
                        "description": "O que ela disse, em linguagem simples"},
        },
        "required": ["prato", "dimensao", "status", "detalhe"],
    },
}

CHECKLIST_COMPLETO = {
    "name": "sabor_checklist_completo",
    "description": (
        "Diz se o checklist de viabilidade de um prato está completo e o que "
        "ainda falta perguntar. Consulte antes de aceitar o prato."
    ),
    "parameters": {
        "type": "object",
        "properties": {"prato": {"type": "string"}},
        "required": ["prato"],
    },
}

ACCEPT_DISH = {
    "name": "sabor_accept_dish",
    "description": (
        "Aceita um prato para o cardápio: valida o checklist e reserva o "
        "orçamento de R$ 80. Se recusar (viabilidade_pendente ou "
        "orcamento_estourado), NÃO insista — pergunte o que falta ou proponha "
        "substituição."
    ),
    "parameters": {
        "type": "object",
        "properties": {"prato": {"type": "string"}},
        "required": ["prato"],
    },
}

CMV_POR_PORCAO = {
    "name": "sabor_cmv_por_porcao",
    "description": (
        "Custo da receita e de cada marmita de um prato aceito, item a item. "
        "Na conversa, chame de 'custo por marmita' — nunca use siglas."
    ),
    "parameters": {
        "type": "object",
        "properties": {"prato": {"type": "string"}},
        "required": ["prato"],
    },
}

CENARIOS_DE_PRECO = {
    "name": "sabor_cenarios_de_preco",
    "description": (
        "Custo por marmita + preço mínimo sem prejuízo + 3 cenários de preço "
        "com a matemática visível (preço, quanto ela recebe após a taxa de "
        "10% da plataforma, lucro). Apresente e deixe ELA escolher."
    ),
    "parameters": {
        "type": "object",
        "properties": {"prato": {"type": "string"}},
        "required": ["prato"],
    },
}

REGISTRAR_PRECO_ESCOLHIDO = {
    "name": "sabor_registrar_preco_escolhido",
    "description": "Grava o preço que a Dona Maria escolheu para o prato.",
    "parameters": {
        "type": "object",
        "properties": {
            "prato": {"type": "string"},
            "preco": {"type": "number"},
        },
        "required": ["prato", "preco"],
    },
}

CESTA_ATUAL = {
    "name": "sabor_cesta_atual",
    "description": (
        "Cesta de compras consolidada dos pratos aceitos: o que falta na "
        "despensa, quantas embalagens, custo total e sobra do orçamento."
    ),
    "parameters": {"type": "object", "properties": {}},
}

GERAR_CARDAPIO = {
    "name": "sabor_gerar_cardapio",
    "description": (
        "Gera o Markdown do cardápio de lançamento (artefato interno de "
        "conferência). Devolve o caminho absoluto do arquivo."
    ),
    "parameters": {"type": "object", "properties": {}},
}

GERAR_PDF = {
    "name": "sabor_gerar_pdf",
    "description": (
        "Gera o PDF do cardápio de lançamento — o artefato final entregue à "
        "Dona Maria. Devolve o caminho absoluto; envie o arquivo com "
        "MEDIA:<caminho> na resposta."
    ),
    "parameters": {"type": "object", "properties": {}},
}
