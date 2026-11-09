#!/bin/zsh
# Dois cliques: escolha a pasta _EqPress do livro; todas as equações são refeitas com a fonte nova.
# Depois, no InDesign, rode "EqPress - Vincular e alinhar equações".
cd "$(dirname "$0")"
PASTA=$(osascript -e 'POSIX path of (choose folder with prompt "Escolha a pasta _EqPress do livro")') || exit 0
.venv/bin/python -m eqpress reestilizar "$PASTA" --perguntar
