#!/bin/bash
# Reseta o Sabor da Maria para uma nova pessoa testar do zero.
# Uso: bash scripts/reset_demo.sh
set -e
cd "$(dirname "$0")/.."

sqlite3 data/sabor.db "
DELETE FROM precos WHERE origem='complemento';
DELETE FROM checklist_viabilidade;
DELETE FROM prato_ingredientes;
DELETE FROM pratos;
UPDATE consultoria SET fase='briefing' WHERE rowid=1;
"
rm -f cardapio_lancamento.md cardapio_lancamento.pdf

echo "✓ Estado resetado: fase=briefing, 0 pratos, despensa intacta"
echo "  (a pessoa pode mandar 'oi' no WhatsApp e começar do zero)"
