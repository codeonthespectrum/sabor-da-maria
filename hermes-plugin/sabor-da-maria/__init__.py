"""Plugin Sabor da Maria — registro das tools nativas."""

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)

_TOOLSET = "sabor"

_TOOLS = [
    (schemas.GET_PHASE, tools.get_phase),
    (schemas.SET_PHASE, tools.set_phase),
    (schemas.GET_PANTRY, tools.get_pantry),
    (schemas.TEM_NA_DESPENSA, tools.tem_na_despensa),
    (schemas.CADASTRAR_COMPLEMENTO, tools.cadastrar_complemento),
    (schemas.BUSCAR_RECEITAS, tools.buscar_receitas),
    (schemas.EXTRAIR_RECEITA, tools.extrair_receita),
    (schemas.EXTRAIR_TEXTO_BRUTO, tools.extrair_texto_bruto),
    (schemas.DEFINIR_PRATO, tools.definir_prato),
    (schemas.RECORD_CHECKLIST_ITEM, tools.record_checklist_item),
    (schemas.CHECKLIST_COMPLETO, tools.checklist_completo),
    (schemas.ACCEPT_DISH, tools.accept_dish),
    (schemas.CMV_POR_PORCAO, tools.cmv_por_porcao),
    (schemas.CENARIOS_DE_PRECO, tools.cenarios_de_preco),
    (schemas.REGISTRAR_PRECO_ESCOLHIDO, tools.registrar_preco_escolhido),
    (schemas.CESTA_ATUAL, tools.cesta_atual),
    (schemas.GERAR_CARDAPIO, tools.gerar_cardapio),
    (schemas.GERAR_PDF, tools.gerar_pdf),
]


def register(ctx):
    for schema, handler in _TOOLS:
        ctx.register_tool(name=schema["name"], toolset=_TOOLSET,
                          schema=schema, handler=handler)
    logger.info("sabor-da-maria: %d tools registradas (toolset '%s')",
                len(_TOOLS), _TOOLSET)
