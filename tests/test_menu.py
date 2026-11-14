"""Testes do cardápio de lançamento: o artefato final consolida pratos
aceitos, CMV, cenários de preço e a cesta de compras (CONTEXT.md)."""

import tempfile
import unittest
from pathlib import Path

from agent_tools import basket, db, menu, pantry, state

XLSX_REAL = Path(__file__).resolve().parent.parent / "despensa_dona_maria.xlsx"


class TestCardapio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.set_db_path(Path(self.tmp.name) / "teste.db")
        pantry.ingest_xlsx(str(XLSX_REAL))
        pantry.cadastrar_complemento("creme de leite", 200, "g", 8.00)
        basket.definir_prato("Strogonoff de Frango", 4, [
            ("peito de frango", 600, "g"),
            ("creme de leite", 100, "g"),
        ])
        for dim in ("utensilios", "tecnicas", "restricoes_operacionais"):
            state.record_checklist_item("Strogonoff de Frango", dim, "ok", "confirmado")
        state.accept_dish("Strogonoff de Frango")
        basket.registrar_preco_escolhido("Strogonoff de Frango", 15.00)

    def tearDown(self):
        db.reset_db_path()
        self.tmp.cleanup()

    def test_cardapio_consolida_prato_aceito(self):
        saida = Path(self.tmp.name) / "cardapio.md"
        caminho = menu.gerar_cardapio(str(saida))
        texto = Path(caminho).read_text(encoding="utf-8")
        # prato com preço escolhido pela Dona Maria
        self.assertIn("Strogonoff de Frango", texto)
        self.assertIn("R$ 15,00", texto)
        # CMV: frango 0,6kg × 14 = 8,40; creme 0,1kg × 40 = 4,00 → 12,40 / 4 = 3,10
        self.assertIn("R$ 12,40", texto)
        self.assertIn("R$ 3,10", texto)

    def test_cardapio_inclui_cesta_consolidada(self):
        saida = Path(self.tmp.name) / "cardapio.md"
        texto = Path(menu.gerar_cardapio(str(saida))).read_text(encoding="utf-8")
        # cesta: 100g de creme de leite → 1 caixinha de R$ 8,00; restam R$ 72
        self.assertIn("creme de leite", texto.lower())
        self.assertIn("R$ 8,00", texto)
        self.assertIn("R$ 72,00", texto)

    def test_candidato_nao_entra_no_cardapio(self):
        basket.definir_prato("Mousse de Chocolate", 6, [("leite integral", 200, "ml")])
        saida = Path(self.tmp.name) / "cardapio.md"
        texto = Path(menu.gerar_cardapio(str(saida))).read_text(encoding="utf-8")
        self.assertNotIn("Mousse", texto)


class TestCardapioPdf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.set_db_path(Path(self.tmp.name) / "teste.db")
        pantry.ingest_xlsx(str(XLSX_REAL))
        pantry.cadastrar_complemento("creme de leite", 200, "g", 8.00)
        basket.definir_prato("Strogonoff de Frango", 4, [
            ("peito de frango", 600, "g"),
            ("creme de leite", 100, "g"),
        ])
        for dim in ("utensilios", "tecnicas", "restricoes_operacionais"):
            state.record_checklist_item("Strogonoff de Frango", dim, "ok", "confirmado")
        state.accept_dish("Strogonoff de Frango")
        basket.registrar_preco_escolhido("Strogonoff de Frango", 15.00)

    def tearDown(self):
        db.reset_db_path()
        self.tmp.cleanup()

    def test_pdf_valido(self):
        saida = Path(self.tmp.name) / "cardapio.pdf"
        caminho = menu.gerar_pdf(str(saida))
        dados = Path(caminho).read_bytes()
        self.assertTrue(dados.startswith(b"%PDF"))
        self.assertIn(b"%%EOF", dados[-2048:])
        self.assertGreater(len(dados), 2000)

    def test_pdf_sem_jargao_cmv(self):
        # o PDF é o artefato entregue à Dona Maria: nada de "CMV" impresso
        from pypdf import PdfReader
        saida = Path(self.tmp.name) / "cardapio.pdf"
        menu.gerar_pdf(str(saida))
        texto = "".join(pag.extract_text() for pag in PdfReader(str(saida)).pages)
        self.assertNotIn("CMV", texto)
        # em linguagem simples: custo por marmita e preço escolhido presentes
        self.assertIn("custo por marmita", texto)
        self.assertIn("Strogonoff de Frango", texto)
        self.assertIn("15,00", texto)


if __name__ == "__main__":
    unittest.main()
