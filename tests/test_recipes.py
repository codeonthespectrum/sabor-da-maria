"""Testes do parser de receitas (cascata: nível 2, JSON-LD determinístico —
ADR 0004). A camada HTTP é fina e não é testada aqui; o que tem lógica
(parse do JSON-LD e das linhas de ingrediente) é testado com fixtures.
"""

import unittest

from agent_tools import recipes

HTML_COM_JSONLD = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Strogonoff de Frango Simples",
  "recipeYield": "4 porções",
  "recipeIngredient": [
    "600 g de peito de frango em cubos",
    "1 caixa de creme de leite",
    "2 colheres de sopa de manteiga",
    "Sal a gosto"
  ]
}
</script>
</html>
"""

HTML_SEM_JSONLD = "<html><body><h1>Bolo de fubá</h1></body></html>"


class TestParseJsonLd(unittest.TestCase):
    def test_extrai_receita_do_jsonld(self):
        r = recipes.extrair_receita_de_html(HTML_COM_JSONLD)
        self.assertEqual(r["titulo"], "Strogonoff de Frango Simples")
        self.assertEqual(r["rendimento_porcoes"], 4)
        self.assertEqual(r["fonte"], "json-ld")
        self.assertEqual(len(r["ingredientes"]), 4)

    def test_linhas_de_ingrediente_estruturadas(self):
        r = recipes.extrair_receita_de_html(HTML_COM_JSONLD)
        frango = r["ingredientes"][0]
        self.assertEqual(frango["quantidade"], 600.0)
        self.assertEqual(frango["unidade"], "g")
        self.assertIn("frango", frango["nome"])
        manteiga = r["ingredientes"][2]
        self.assertEqual(manteiga["quantidade"], 2.0)
        self.assertEqual(manteiga["unidade"], "colheres de sopa")

    def test_ingrediente_sem_medida_fica_com_quantidade_none(self):
        r = recipes.extrair_receita_de_html(HTML_COM_JSONLD)
        sal = r["ingredientes"][3]
        self.assertIsNone(sal["quantidade"])

    def test_sem_jsonld_sinaliza_fallback_pro_luna(self):
        with self.assertRaises(recipes.SemJsonLd):
            recipes.extrair_receita_de_html(HTML_SEM_JSONLD)


if __name__ == "__main__":
    unittest.main()
