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

    def test_texto_bruto_remove_tags_e_scripts(self):
        html = (
            "<html><head><style>body{color:red}</style>"
            "<script>var x=1;</script></head>"
            "<body><h1>Bolo de Fubá</h1><p>2 xícaras de fubá</p>"
            "<nav>menu do site</nav><!-- comentário --></body></html>"
        )
        from unittest.mock import patch
        with patch.object(recipes, "_get", return_value=html):
            texto = recipes.extrair_texto_bruto("http://exemplo.com/r")
        self.assertIn("Bolo de Fubá", texto)
        self.assertIn("2 xícaras de fubá", texto)
        self.assertNotIn("color:red", texto)
        self.assertNotIn("var x", texto)
        self.assertNotIn("menu do site", texto)
        self.assertNotIn("comentário", texto)
        self.assertNotIn("<", texto)

    def test_sem_jsonld_carrega_url_pro_fallback(self):
        from unittest.mock import patch
        with patch.object(recipes, "_get", return_value=HTML_SEM_JSONLD):
            with self.assertRaises(recipes.SemJsonLd) as ctx:
                recipes.extrair_receita("http://exemplo.com/receita-x")
        self.assertEqual(ctx.exception.url, "http://exemplo.com/receita-x")


if __name__ == "__main__":
    unittest.main()
