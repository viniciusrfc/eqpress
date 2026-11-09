#!/bin/zsh
# Dois cliques no Finder: escolha um .docx e a página de conferência abre no navegador.
cd "$(dirname "$0")"
ARQ=$(osascript -e 'POSIX path of (choose file with prompt "Escolha o .docx com as equações MathType" of type {"org.openxmlformats.wordprocessingml.document"})') || exit 0
.venv/bin/python -m eqpress testar "$ARQ" --perguntar
