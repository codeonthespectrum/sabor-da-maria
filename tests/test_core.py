"""Testes das regras de negócio determinísticas (ADR 0001: orçamento mede
compra, CMV mede consumo; ADR 0003: LLM não calcula).

Roda com:  python -m unittest discover -s tests -v
"""

import tempfile
import unittest
from pathlib import Path

from agent_tools import basket, conversions, db, pantry, pricing

XLSX_REAL = Path(__file__).resolve().parent.parent / "despensa_dona_maria.xlsx"


class BaseDB(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.set_db_path(Path(self.tmp.name) / "teste.db")

    def tearDown(self):
        db.reset_db_path()
        self.tmp.cleanup()


class TestConversoes(unittest.TestCase):
    def test_unidades_basicas(self):
        self.assertEqual(conversions.para_unidade_base(600, "g"), (0.6, "kg"))
        self.assertEqual(conversions.para_unidade_base(2, "colheres de sopa"), (0.03, "L"))
        self.assertEqual(conversions.para_unidade_base(1, "xícara"), (0.24, "L"))
        self.assertEqual(conversions.para_unidade_base(30, "un"), (30.0, "un"))

    def test_ignora_acento_e_caixa(self):
        self.assertEqual(conversions.para_unidade_base(1, "XÍCARA"), (0.24, "L"))
        self.assertEqual(conversions.para_unidade_base(1, "Colher de Chá"), (0.005, "L"))

    def test_desconhecida_devolve_none(self):
        self.assertIsNone(conversions.para_unidade_base(1, "punhado"))

    def test_decompor_embalagem(self):
        self.assertEqual(conversions.decompor_embalagem("balde 2kg"), ("kg", 2.0))
        self.assertEqual(conversions.decompor_embalagem("un 500ml"), ("L", 0.5))
        self.assertEqual(conversions.decompor_embalagem("un 400g"), ("kg", 0.4))
        self.assertEqual(conversions.decompor_embalagem("un"), ("un", 1.0))
        self.assertEqual(conversions.decompor_embalagem("kg"), ("kg", 1.0))
        # medidas simples também são "embalagens": 1 g = 0,001 kg na base
        self.assertEqual(conversions.decompor_embalagem("g"), ("kg", 0.001))
        self.assertEqual(conversions.decompor_embalagem("ml"), ("L", 0.001))

    def test_nome_bonito(self):
        self.assertEqual(
            conversions.nome_bonito("escondidinho_de_batata"),
            "Escondidinho de Batata")
        self.assertEqual(
            conversions.nome_bonito("carne_de_panela_com_batata"),
            "Carne de Panela com Batata")
        # nome já bonito passa quase intacto
        self.assertEqual(
            conversions.nome_bonito("Espaguete à Bolonhesa"),
            "Espaguete à Bolonhesa")


class TestPantry(BaseDB):
    def test_ingestao_planilha_real(self):
        resumo = pantry.ingest_xlsx(str(XLSX_REAL))
        self.assertEqual(resumo["itens"], 37)
        self.assertEqual(resumo["sem_preco"], [])

    def test_preco_unitario_cruzamento_das_abas(self):
        pantry.ingest_xlsx(str(XLSX_REAL))
        # Frango: R$ 28,00 / 2 kg = R$ 14,00/kg
        self.assertAlmostEqual(pantry.preco_unitario("Peito de frango"), 14.00)
        # Alcaparras: "balde 2kg" por R$ 82 → R$ 41,00/kg
        self.assertAlmostEqual(pantry.preco_unitario("Alcaparras"), 41.00)
        # Azeite: "un 500ml" por R$ 30,99 → R$ 61,98/L
        self.assertAlmostEqual(pantry.preco_unitario("Azeite de oliva extra virgem"), 61.98)

    def test_tem_na_despensa_com_conversao(self):
        pantry.ingest_xlsx(str(XLSX_REAL))
        tem, disponivel = pantry.tem_na_despensa("peito de frango", 600, "g")
        self.assertTrue(tem)
        self.assertAlmostEqual(disponivel, 2.0)
        tem, disponivel = pantry.tem_na_despensa("ovos", 35, "un")
        self.assertFalse(tem)
        self.assertAlmostEqual(disponivel, 30.0)


class TestBasket(BaseDB):
    """O cenário da sessão de design: strogonofe + mousse dividindo o
    creme de leite (ADR 0001 — orçamento mede compra, embalagem inteira)."""

    def setUp(self):
        super().setUp()
        pantry.cadastrar_complemento("creme de leite", 200, "g", 8.00)  # caixinha
        basket.definir_prato("Strogonoff", 4, [("creme de leite", 100, "g")])
        basket.definir_prato("Mousse", 6, [("creme de leite", 150, "g")])

    def test_reserva_na_aceitacao(self):
        cesta = basket.reservar("Strogonoff")
        self.assertEqual(cesta["reservado_total"], 8.00)
        self.assertEqual(cesta["orcamento_restante"], 72.00)

    def test_item_compartilhado_soma_e_deduplica(self):
        basket.reservar("Strogonoff")
        cesta = basket.reservar("Mousse")
        # 100g + 150g = 250g → 2 caixinhas de 200g = R$ 16, não R$ 16 em duas reservas separadas
        self.assertEqual(cesta["reservado_total"], 16.00)
        self.assertEqual(len(cesta["itens"]), 1)
        self.assertEqual(cesta["itens"][0]["embalagens"], 2)

    def test_desistencia_libera_reserva(self):
        basket.reservar("Strogonoff")
        basket.reservar("Mousse")
        cesta = basket.liberar("Strogonoff")
        # Sobrou só o mousse: 150g → 1 caixinha = R$ 8
        self.assertEqual(cesta["reservado_total"], 8.00)
        self.assertEqual(cesta["orcamento_restante"], 72.00)

    def test_estouro_de_orcamento_rejeita_aceite(self):
        basket.definir_prato("Banquete", 10, [("creme de leite", 20, "kg")])
        with self.assertRaises(basket.OrcamentoEstourado):
            basket.reservar("Banquete")
        # O prato NÃO ficou aceito após o estouro
        self.assertEqual(basket.cesta_atual()["reservado_total"], 0.0)

    def test_aceite_sem_preco_cadastrado_falha(self):
        basket.definir_prato("Sushi", 4, [("salmão", 500, "g")])
        with self.assertRaises(ValueError):
            basket.reservar("Sushi")

    def test_despensa_abate_a_necessidade(self):
        pantry.ingest_xlsx(str(XLSX_REAL))
        basket.definir_prato("Frango simples", 4, [("peito de frango", 600, "g")])
        cesta = basket.reservar("Frango simples")
        # 600g de frango cabem nos 2kg da despensa: nada a comprar
        self.assertEqual(cesta["reservado_total"], 0.0)


class TestPricing(BaseDB):
    def setUp(self):
        super().setUp()
        pantry.ingest_xlsx(str(XLSX_REAL))
        # O exemplo da sessão: strogonoff com 600g de frango + 100g de mussarela
        basket.definir_prato("Strogonoff", 4, [
            ("peito de frango", 600, "g"),
            ("queijo mussarela", 100, "g"),
        ])

    def test_cmv_mede_consumo_nao_compra(self):
        r = pricing.cmv_por_porcao("Strogonoff")
        # Frango: 0,6 kg × R$ 14,00 = 8,40 | Mussarela: 0,1 kg × R$ 40,00 = 4,00
        self.assertEqual(r["cmv_receita"], 12.40)
        self.assertEqual(r["cmv_porcao"], 3.10)
        origens = {i["ingrediente"]: i["origem"] for i in r["itens"]}
        self.assertEqual(origens["Peito de frango"], "despensa")

    def test_preco_minimo(self):
        self.assertEqual(pricing.preco_minimo(3.10), 3.44)

    def test_cenarios_respeitam_minimo_e_matematica(self):
        cenarios = pricing.cenarios_de_preco(3.10)
        self.assertEqual(len(cenarios), 3)
        for c in cenarios:
            self.assertGreaterEqual(c["preco"], pricing.preco_minimo(3.10))
            self.assertAlmostEqual(c["repasse"], round(0.9 * c["preco"], 2))
            self.assertAlmostEqual(c["lucro"], round(c["repasse"] - 3.10, 2))
        # Equilibrado: 3,10 / (0,9 - 0,5) = 7,75 → arredonda para 8,00
        equilibrado = cenarios[1]
        self.assertEqual(equilibrado["preco"], 8.00)
        self.assertEqual(equilibrado["lucro"], 4.10)

    def test_cmv_sem_preco_falha_com_lista(self):
        basket.definir_prato("Sushi", 4, [("salmão", 500, "g")])
        with self.assertRaises(pricing.SemPrecoCadastrado):
            pricing.cmv_por_porcao("Sushi")


if __name__ == "__main__":
    unittest.main()
