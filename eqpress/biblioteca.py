"""Biblioteca de padrões dos livros neste Mac (EDITOR §3.1, PRESET §8): criar, editar (nova
versão, nunca sobrescreve), importar e exportar. Cada padrão é um preset completo do schema; a
tela mostra só os campos que o colaborador ajusta.
"""
import json
import re
import shutil
import unicodedata

from . import padrao as PADRAO
from . import plataforma as P
from . import renderizador as R

PASTA = P.DADOS / "Padrões"
EXEMPLOS = [P.RECURSOS / "spec/exemplos/exemplo_atual_v1.json", P.RECURSOS / "spec/exemplos/exemplo_resolucao_v1.json"]
PRETO_100K = {"modelo": "cmyk", "valores": [0, 0, 0, 100]}


def _slug(texto):
    sem_acento = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", sem_acento).strip("_")
    return s or "padrao"


def _semear():
    """Primeira vez: a biblioteca começa com os padrões de exemplo."""
    PASTA.mkdir(parents=True, exist_ok=True)
    if not any(PASTA.glob("*.json")):
        for ex in EXEMPLOS:
            if ex.exists():
                (PASTA / ex.name).write_text(json.dumps(R.carregar_preset(ex), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def campos(p):
    """Preset → campos da tela."""
    defs, nome_cor = p["cores"]["definicoes"], p["cores"]["padrao"]
    cor = defs[nome_cor]
    return {
        "nome": p.get("titulo") or p["nome"], "versao": p["versao"],
        "familia": p["categorias"]["variavel"]["familia"],
        "corpo": float(p["tamanhos"]["completo"][:-2]),
        "italico": bool(p["categorias"]["variavel"].get("italico", False)),
        "simbolos": p["categorias"]["simbolo"]["familia"],
        "cor": "especial" if cor["modelo"] == "especial" else "preto",
        "tinta": cor.get("nome", ""), "alternativa": cor.get("alternativa_cmyk", [0, 100, 0, 0]),
        "sobreimpressao": bool(p["cores"].get("sobreimpressao", True)),
        "extras": p["saida"].get("extras", []),
    }


def montar(c, base=None):
    """Campos da tela → preset completo (a partir do padrão base ou do exemplo)."""
    p = json.loads(json.dumps(base or R.carregar_preset(EXEMPLOS[0])))
    p = PADRAO.aplicar(p, c["familia"], c["corpo"], bool(c.get("italico")))
    for cat in ("grego_min", "grego_mai", "simbolo"):
        p["categorias"][cat] = {"familia": c.get("simbolos") or "Symbol"}
    if c.get("cor") == "especial":
        nome = c["tinta"].strip()
        if not nome:
            raise R.ErroRender("Informe o nome da tinta especial, igual ao do InDesign (ex.: PANTONE 219 C).")
        cor = {"modelo": "especial", "nome": nome, "alternativa_cmyk": [float(v) for v in c["alternativa"]]}
        p["cores"] = {"definicoes": {nome: cor}, "padrao": nome, "destaque": nome,
                      "sobreimpressao": bool(c.get("sobreimpressao", True))}
    else:
        p["cores"] = {"definicoes": {"Preto 100K": PRETO_100K, "Destaque": {"modelo": "cmyk", "valores": [0, 100, 100, 0]}},
                      "padrao": "Preto 100K", "destaque": "Destaque", "sobreimpressao": bool(c.get("sobreimpressao", True))}
    p["saida"] = {**p["saida"], "formato": "pdf", "extras": sorted(set(c.get("extras") or []))}
    p.pop("baseado_em", None)
    titulo = c["nome"].strip() or f"{c['familia']} {c['corpo']:g} pt"
    p["nome"], p["titulo"] = _slug(titulo), titulo
    return p


def listar():
    _semear()
    itens = []
    for arq in sorted(PASTA.glob("*.json")):
        try:
            p = R.carregar_preset(arq)
            itens.append({"arquivo": str(arq), **campos(p)})
        except Exception as e:  # arquivo estranho na pasta: aparece com o erro, não some
            itens.append({"arquivo": str(arq), "nome": arq.stem, "erro": str(e)})
    return itens


def salvar(c, arquivo_base=None):
    """Grava uma versão nova (O3): editar `x_v2` cria `x_v3`; nada é sobrescrito."""
    _semear()
    base = R.carregar_preset(arquivo_base) if arquivo_base else None
    p = montar(c, base)
    versoes = [int(m[1]) for f in PASTA.glob(f"{p['nome']}_v*.json") if (m := re.search(r"_v(\d+)$", f.stem))]
    p["versao"] = max(versoes, default=0) + 1
    R.validar_fontes(p)
    R.preambulo(p)  # fontes existem neste Mac? (P-03) — erro antes de gravar
    destino = PASTA / f"{p['nome']}_v{p['versao']}.json"
    destino.write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"arquivo": str(destino), **campos(p)}


def importar(origem):
    p = R.carregar_preset(origem)  # valida antes de copiar
    _semear()
    destino = PASTA / f"{p['nome']}_v{p['versao']}.json"
    if destino.exists():
        raise R.ErroRender(f"Já existe um padrão {destino.stem} neste Mac.")
    shutil.copy(origem, destino)
    return {"arquivo": str(destino), **campos(p)}


def exportar(arquivo, destino):
    shutil.copy(arquivo, destino)
    return {"arquivo": str(destino)}


AMOSTRA = (r"\begin{array}{l}\displaystyle x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}\Rightarrow\Delta>0\\"
           r"\displaystyle v=v_{0}+\text{a}t\qquad 2\,\text{H}_{2}+\text{O}_{2}\rightleftharpoons 2\,\text{H}_{2}\text{O}\end{array}")
