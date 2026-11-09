"""Padrão do livro simplificado (até a tela do editor, EDITOR §3.1): fonte + corpo + itálico.

A fonte escolhida vale para texto, função, variável, número, vetor e extra; grego e símbolos
continuam na Symbol e o resto na fonte matemática (PRESET §2.1, três camadas, como no MathType).
"""
import json
import re
import subprocess

from . import plataforma as P
from . import renderizador as R

BASE = P.RECURSOS / "spec/exemplos/exemplo_atual_v1.json"
ULTIMO = P.DADOS / "ultimo_padrao.json"
FAVORITAS = ["Arial", "Calibri", "Helvetica", "Helvetica Neue", "Times New Roman", "Myriad Pro",
             "Minion Pro", "Avenir Next", "Georgia", "Verdana"]
DA_FONTE = ("texto", "funcao", "variavel", "numero", "vetor_matriz", "extra")


def familias():
    """Famílias com face normal, favoritas primeiro (as proibidas pelo P-02 ficam de fora)."""
    idx = R.indice_fontes()
    nomes = sorted((R.NOMES_FONTES[k] for k, faces in idx.items()
                    if any(not b and not i for _, b, i, _, _ in faces)
                    and not R.PROIBIDAS.search(k) and not k.startswith((".", "#"))), key=str.lower)
    favs = [n for f in FAVORITAS for n in nomes if n.lower() == f.lower()]
    return favs + [n for n in nomes if n not in favs]


def aplicar(p, familia=None, corpo=None, italico=None):
    """Cópia do padrão com fonte/corpo/itálico trocados (só o que vier preenchido).
    Usada para o padrão novo do livro e para o ajuste de uma equação só."""
    p = json.loads(json.dumps(p))
    idx = R.indice_fontes()
    if familia:
        R.arquivo_fonte(idx, familia)  # P-03: existe?
        tem_negrito = any(b and not i for _, b, i, _, _ in idx[familia.lower()])
        ital = p["categorias"]["variavel"].get("italico", False)
        for c in DA_FONTE:
            p["categorias"][c] = {"familia": familia}
        p["categorias"]["variavel"]["italico"] = ital
        if tem_negrito:
            p["categorias"]["vetor_matriz"]["peso"] = "negrito"
    if italico is not None:
        if italico:
            R.arquivo_fonte(idx, p["categorias"]["variavel"]["familia"], italico=True)
        p["categorias"]["variavel"]["italico"] = bool(italico)
    if corpo:
        p["tamanhos"]["completo"] = f"{float(corpo):g}pt"
        p["tamanhos"]["subscrito"] = "70%"  # 7 pt em 10 pt, como no padrão das amostras
    return p


def criar(familia, corpo, italico=False):
    """Preset a partir do exemplo, trocando fonte e corpo. Erro claro se faltar face."""
    p = aplicar(json.loads(BASE.read_text(encoding="utf-8")), familia, corpo, italico)
    p["nome"] = re.sub(r"[^a-z0-9]+", "_", f"{familia} {corpo:g}pt".lower()).strip("_")
    p["versao"] = 1
    p.pop("colecao", None)
    return p


def _osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return None if r.returncode else r.stdout.strip()


def _q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def perguntar():
    """Três diálogos do macOS; devolve (familia, corpo, italico) ou None se cancelar."""
    try:
        ult = json.loads(ULTIMO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ult = {"familia": "Calibri", "corpo": 10, "italico": False}
    fams = familias()
    padrao = ult["familia"] if ult["familia"] in fams else fams[0]
    fam = _osa(f"choose from list {{{', '.join(map(_q, fams))}}} with title \"EqPress\" "
               f"with prompt \"Fonte das equações (a mesma do texto do livro):\" default items {{{_q(padrao)}}}")
    if not fam or fam == "false":
        return None
    corpo = _osa(f'text returned of (display dialog "Corpo das equações, em pt:" with title "EqPress" '
                 f'default answer {_q(f"{ult["corpo"]:g}")})')
    if corpo is None:
        return None
    try:
        corpo = float(corpo.replace(",", "."))
    except ValueError:
        _osa(f'display alert "Corpo inválido: {corpo}"')
        return None
    botao = "Sim" if ult["italico"] else "Não"
    ital = _osa(f'button returned of (display dialog "Variáveis (x, y, a, b…) em itálico?" with title "EqPress" '
                f'buttons {{"Não", "Sim"}} default button "{botao}")')
    if ital is None:
        return None
    escolha = {"familia": fam, "corpo": corpo, "italico": ital == "Sim"}
    ULTIMO.parent.mkdir(parents=True, exist_ok=True)
    ULTIMO.write_text(json.dumps(escolha, ensure_ascii=False), encoding="utf-8")
    return fam, corpo, ital == "Sim"
