"""Testes do fluxo de consultoria: fases, checklist de viabilidade e o
gate estrutural de aceitação (ADR 0002 — o gate mora no código, não no prompt).
"""

import tempfile
import unittest
from pathlib import Path

from agent_tools import basket, db, pantry, state


class BaseDB(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.set_db_path(Path(self.tmp.name) / "teste.db")
        pantry.cadastrar_complemento("creme de leite", 200, "g", 8.00)
        basket.definir_prato("Strogonoff", 4, [("creme de leite", 100, "g")])

    def tearDown(self):
        db.reset_db_path()
        self.tmp.cleanup()


class TestFases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.set_db_path(Path(self.tmp.name) / "teste.db")

    def tearDown(self):
        db.reset_db_path()
        self.tmp.cleanup()

    def test_comeca_no_briefing(self):
        self.assertEqual(state.get_phase(), "briefing")

    def test_avanca_e_retrocede(self):
        state.set_phase("viabilidade")
        self.assertEqual(state.get_phase(), "viabilidade")
        # não linear para a Dona Maria: pode voltar
        state.set_phase("descoberta")
        self.assertEqual(state.get_phase(), "descoberta")

    def test_fase_invalida_rejeitada(self):
        with self.assertRaises(ValueError):
            state.set_phase("fritura")


class TestChecklist(BaseDB):
    def test_checklist_comeca_pendente(self):
        c = state.get_checklist("Strogonoff")
        self.assertEqual(
            {k: v["status"] for k, v in c.items()},
            {"utensilios": "pendente", "tecnicas": "pendente",
             "restricoes_operacionais": "pendente"},
        )

    def test_registrar_resposta(self):
        state.record_checklist_item(
            "Strogonoff", "utensilios", "ok", "tem fogão de 4 bocas e panela grande"
        )
        c = state.get_checklist("Strogonoff")
        self.assertEqual(c["utensilios"]["status"], "ok")
        self.assertEqual(c["utensilios"]["detalhe"], "tem fogão de 4 bocas e panela grande")


class TestGateDeViabilidade(BaseDB):
    """ADR 0002: accept_dish recusa enquanto houver pendência ou impedimento."""

    def test_aceite_bloqueado_com_checklist_pendente(self):
        with self.assertRaises(state.ViabilidadePendente) as ctx:
            state.accept_dish("Strogonoff")
        # o erro devolve o que falta perguntar — o agente usa isso na conversa
        self.assertIn("utensilios", str(ctx.exception))
        # e o prato NÃO foi aceito nem reservou orçamento
        self.assertEqual(basket.cesta_atual()["reservado_total"], 0.0)

    def test_aceite_bloqueado_com_impedimento(self):
        state.record_checklist_item("Strogonoff", "utensilios", "ok", "tem tudo")
        state.record_checklist_item("Strogonoff", "tecnicas", "ok", "sabe fazer")
        state.record_checklist_item(
            "Strogonoff", "restricoes_operacionais", "impedimento", "gás acaba rápido"
        )
        with self.assertRaises(state.ViabilidadePendente):
            state.accept_dish("Strogonoff")

    def test_aceite_completo_reserva_orcamento(self):
        state.record_checklist_item("Strogonoff", "utensilios", "ok", "tem tudo")
        state.record_checklist_item("Strogonoff", "tecnicas", "ok", "sabe fazer")
        state.record_checklist_item(
            "Strogonoff", "restricoes_operacionais", "ok", "sem restrição"
        )
        cesta = state.accept_dish("Strogonoff")
        self.assertEqual(cesta["reservado_total"], 8.00)


if __name__ == "__main__":
    unittest.main()
