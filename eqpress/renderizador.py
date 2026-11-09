"""F3 — LaTeX + preset → PDF (cor do preset, texto em contorno) + métricas; EPS/EMF opcionais.

Specs: PRESET.md, COMPORTAMENTO §A, INDESIGN §4 (métricas), CRITERIOS CA-05/06/08,
spikes/RESULTADOS.md S5 (o driver do TeX intercala `0 g`: a cor é normalizada depois).
Motor: tectonic (XeTeX) + unicode-math; contorno e EPS: Ghostscript; EMF: Inkscape.
"""
import functools
import hashlib
import os
import shutil
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
import pikepdf
import logging

from fontTools.ttLib import TTCollection, TTFont

logging.getLogger("fontTools").setLevel(logging.ERROR)

from . import plataforma as P

RAIZ = P.RAIZ
SCHEMA = json.loads((P.RECURSOS / "spec/PRESET_SCHEMA.json").read_text(encoding="utf-8"))
PROIBIDAS = re.compile(r"mt\s*extra|euclid|mathtype", re.I)  # P-02, P-07
DIRS_FONTES = P.PASTAS_FONTES
CACHE_FONTES = P.CACHE / "fontes.json"
NOMES_FONTES = {}  # família minúscula → nome como a fonte declara (preenchido por indice_fontes)

# letras, números e grego: o unicode-math só aceita faixa por alfabeto (teste F3); a família
# precisa cobrir o alfabeto inteiro, senão ele fica com a fonte_matematica (aviso, P-06)
ALFABETOS = {
    "variavel": ("up/{latin,Latin}", [*range(0x41, 0x5B), *range(0x61, 0x7B)]),
    "numero": ("up/num", list(range(0x30, 0x3A))),
    "grego_min": ("up/greek", [*range(0x3B1, 0x3C2), *range(0x3C3, 0x3CA)]),
    "grego_mai": ("up/Greek", [*range(0x391, 0x3A2), *range(0x3A3, 0x3AA)]),
}
# símbolos e pontuação: faixa por código, só os que a família tem (o resto: fonte_matematica)
FAIXAS = {
    "simbolo": [ord(c) for c in "+=<>−⋅·×÷±∓→←↔⇒⇐⇔↑↓↦≤≥≠≈≡≅∼∝≪≫≃∞∴∵•°∈∉⊂⊃⊆⊇∪∩∅∀∃¬∧∨∂∇′″∠⊥∥…⋯∘△ℓ"],
    # pontuação digitada (MathType: estilo função); ( ) [ ] { } | ficam na fonte matemática,
    # senão \left/\right não crescem (teste F3)
    "funcao": [ord(c) for c in ",.;:!?'/%$"],
}
# Codificação Symbol (fonte "Symbol" do Windows, a que o MathType usa): Unicode → posição. Fonte:
# tabela pública de correspondência da Adobe Symbol Encoding (Unicode Consortium, SYMBOL.TXT).
# Na fonte do Windows o código c fica em U+F000+c (cmap 3,0). PRESET P-08.
CODIFICACAO_SYMBOL = {
    **{ord(c): ord(c) for c in "!#%&()+,./0123456789:;<=>?[]_{|}"},
    0x2200: 0x22, 0x2203: 0x24, 0x220B: 0x27, 0x2217: 0x2A, 0x2212: 0x2D, 0x2245: 0x40,
    **dict(zip(map(ord, "ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ"), range(0x41, 0x5B))),
    0x2234: 0x5C, 0x22A5: 0x5E,
    **dict(zip(map(ord, "αβχδεφγηιϕκλμνοπθρστυϖωξψζ"), range(0x61, 0x7B))),
    0x223C: 0x7E, 0x03D2: 0xA1, 0x2032: 0xA2, 0x2264: 0xA3, 0x2044: 0xA4, 0x221E: 0xA5,
    0x2194: 0xAB, 0x2190: 0xAC, 0x2191: 0xAD, 0x2192: 0xAE, 0x2193: 0xAF, 0x00B0: 0xB0,
    0x00B1: 0xB1, 0x2033: 0xB2, 0x2265: 0xB3, 0x00D7: 0xB4, 0x221D: 0xB5, 0x2202: 0xB6,
    0x2022: 0xB7, 0x00F7: 0xB8, 0x2260: 0xB9, 0x2261: 0xBA, 0x2248: 0xBB, 0x2026: 0xBC,
    0x2135: 0xC0, 0x2297: 0xC4, 0x2295: 0xC5, 0x2205: 0xC6, 0x2229: 0xC7, 0x222A: 0xC8,
    0x2283: 0xC9, 0x2287: 0xCA, 0x2284: 0xCB, 0x2282: 0xCC, 0x2286: 0xCD, 0x2208: 0xCE,
    0x2209: 0xCF, 0x2220: 0xD0, 0x2207: 0xD1, 0x00AC: 0xD8, 0x2227: 0xD9, 0x2228: 0xDA,
    0x21D4: 0xDB, 0x21D0: 0xDC, 0x21D1: 0xDD, 0x21D2: 0xDE, 0x21D3: 0xDF, 0x22C5: 0xD7,
}
# classe matemática (TeX): 3 relação, 2 binário, 6 pontuação, 0 o resto
RELACAO_TEX = set("=<>≤≥≠≈≡∼≅∝→←↔↑↓⇒⇐⇔⇑⇓∈∉∋⊂⊃⊆⊇⊄⊥")
BINARIO_TEX = set("+−±×÷⋅•∩∪∧∨⊕⊗∗")

# parâmetros do preset com tradução direta no TeX; o resto é listado como aproximado (PRESET §4)
ESPACOS_TRADUZIDOS = {"linespace", "matrixcol", "fractthick", "fractthick2", "operspacing", "nonoperspacing"}


class ErroRender(Exception):
    pass


@dataclass
class Saida:
    id: str
    pdf: Path | None = None
    largura_pt: float = 0.0
    altura_pt: float = 0.0
    profundidade_pt: float = 0.0
    extras: dict = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    erro: str | None = None

    def metricas(self):
        return {"largura_pt": self.largura_pt, "altura_pt": self.altura_pt,
                "profundidade_pt": self.profundidade_pt}


# --- preset -------------------------------------------------------------------------------------
def _mesclar(base, filho):
    r = dict(base)
    for k, v in filho.items():
        r[k] = _mesclar(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return r


def carregar_preset(caminho):
    """Lê, aplica `baseado_em` (um nível, PRESET §8), valida no schema e checa P-02."""
    caminho = Path(caminho)
    p = json.loads(caminho.read_text(encoding="utf-8"))
    if p.get("baseado_em"):
        base = json.loads((caminho.parent / f"{p['baseado_em']}.json").read_text(encoding="utf-8"))
        p = _mesclar(base, p)
    jsonschema.validate(p, SCHEMA)
    validar_fontes(p)
    return p


def sha1_preset(p):
    return hashlib.sha1(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validar_fontes(p):
    nomes = [c["familia"] for c in p["categorias"].values()] + [p.get("fonte_matematica", "STIX Two Math")]
    proibidas = [n for n in nomes if PROIBIDAS.search(n)]
    if proibidas:
        raise ErroRender(f"fonte proibida no preset (P-02/P-07): {sorted(set(proibidas))}")


# --- fontes ---------------------------------------------------------------------------------------
def _ler_nomes(path):
    fontes = TTCollection(path, lazy=True).fonts if path.suffix.lower() in (".ttc", ".otc") else \
        [TTFont(path, lazy=True)]
    out = []
    for i, f in enumerate(fontes):
        nm = f["name"]
        fam = nm.getDebugName(16) or nm.getDebugName(1)
        sub = (nm.getDebugName(17) or nm.getDebugName(2) or "").lower()
        sel = f["OS/2"].fsSelection if "OS/2" in f else 0
        negrito = bool(sel & 0x20) or "bold" in sub
        italico = bool(sel & 0x01) or "italic" in sub or "oblique" in sub
        if fam:
            out.append([fam, sub, negrito, italico, str(path), i])
    return out


def indice_fontes():
    """{família minúscula: [(subfamília, negrito, itálico, arquivo, índice)]}, com cache por mtime."""
    cache = {}
    try:
        cache = json.loads(CACHE_FONTES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    novo, idx = {}, {}
    for d in DIRS_FONTES:
        if not d.is_dir():
            continue
        for path in d.iterdir():
            if path.suffix.lower() not in (".ttf", ".otf", ".ttc", ".otc"):
                continue
            chave = f"{path}|{path.stat().st_mtime}"
            if chave not in cache:
                try:
                    cache[chave] = _ler_nomes(path)
                except Exception:
                    cache[chave] = []
            novo[chave] = cache[chave]
            for fam, sub, b, i, arq, n in cache[chave]:
                idx.setdefault(fam.lower(), []).append((sub, b, i, arq, n))
                NOMES_FONTES.setdefault(fam.lower(), fam)
    if novo != cache:
        CACHE_FONTES.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FONTES.write_text(json.dumps(novo), encoding="utf-8")
    return idx


def arquivo_fonte(idx, familia, negrito=False, italico=False):
    """(arquivo, índice) da face pedida; P-03: família ausente = erro antes de renderizar."""
    faces = idx.get(familia.lower())
    if not faces:
        raise ErroRender(f"fonte ausente no Mac (P-03): {familia}")
    exatas = [f for f in faces if f[1] == negrito and f[2] == italico]
    if not exatas:
        raise ErroRender(f"{familia} não tem a face {'negrito ' if negrito else ''}{'itálico' if italico else 'normal'}")
    # preferir a face "regular"/"bold" pura (sem Light…) e as pastas do sistema às dos apps (DIRS_FONTES)
    ordem = {str(d): k for k, d in enumerate(DIRS_FONTES)}
    exatas.sort(key=lambda f: (f[0] not in ("regular", "bold", "italic", "bold italic", "normal"),
                               # "Symbol": a do Windows (a do MathType) vence a do macOS (escolha do usuário, 2026-10-16)
                               familia.lower() == "symbol" and not _antiga(f[3], f[4]),
                               ordem.get(str(Path(f[3]).parent), 99), f[3]))
    return exatas[0][3], exatas[0][4]


@functools.lru_cache(maxsize=None)
def _antiga(arq, n):
    """Fonte com codificação antiga de símbolos (glifos em U+F0xx) que o XeTeX consegue usar?
    Precisa ter as posições F0xx numa tabela Unicode (0,x ou 3,1), como a Symbol do Office; uma
    cópia só com a tabela 3,0 (ex.: ~/Library/Fonts/symbol.ttf) dá "Missing character" no XeTeX."""
    f = TTCollection(arq, lazy=True).fonts[n] if arq.lower().endswith((".ttc", ".otc")) else TTFont(arq, lazy=True)
    return any((t.platformID == 0 or (t.platformID, t.platEncID) == (3, 1)) and 0xF0AE in t.cmap
               for t in f["cmap"].tables)


def _cmap(arq, n):
    f = TTCollection(arq, lazy=True).fonts[n] if arq.lower().endswith((".ttc", ".otc")) else TTFont(arq, lazy=True)
    # só tabelas Unicode (plataforma 0, ou 3,1/3,10); a tabela 1,0 (Mac Roman) e a 3,0 (símbolos)
    # não valem para o XeTeX — contá-las mandava caracteres para a Symbol do Windows sem achá-los
    return {c for t in f["cmap"].tables if t.cmap and (t.platformID == 0 or (t.platformID, t.platEncID) in ((3, 1), (3, 10)))
            for c in t.cmap}


# As fontes entram no TeX por caminho RELATIVO (subpasta eqfontes/ ao lado do .tex): no XeTeX
# "[arquivo:n]" usa ":" para o número da face, e o "C:" dos caminhos do Windows quebra a leitura.
PASTA_TEX = "eqfontes"
_ORIGEM = {}  # nome local → arquivo original


def _local(arq):
    p = Path(arq)
    nome = f"{hashlib.sha1(str(p).encode()).hexdigest()[:8]}-{p.name}"
    _ORIGEM[nome] = p
    return nome


def _fontspec(arq, n, extra=""):
    opc = [f"Path={PASTA_TEX}/"] + ([f"FontIndex={n}"] if n else []) + ([extra] if extra else [])
    return "{" + _local(arq) + "}[" + ",".join(opc) + "]"


def _preparar_fontes(pre, pasta):
    """Põe em <pasta>/eqfontes as fontes citadas no preâmbulo: link a partir de um espelho no cache
    (cópia só na primeira vez; link evita copiar megabytes a cada prévia)."""
    espelho = P.CACHE / "fontes-tex"
    espelho.mkdir(parents=True, exist_ok=True)
    destino = pasta / PASTA_TEX
    destino.mkdir(exist_ok=True)
    for nome in set(re.findall(rf"(?:\{{|\[{PASTA_TEX}/)([0-9a-f]{{8}}-[^}}\]:\"]+)", pre)):
        origem = _ORIGEM[nome]
        copia = espelho / nome
        if not copia.exists() or copia.stat().st_size != origem.stat().st_size:
            shutil.copyfile(origem, copia)  # só o conteúdo: fontes do sistema têm atributos de proteção
        alvo = destino / nome
        if not alvo.exists():
            try:
                os.link(copia, alvo)
            except OSError:  # outro volume ou sem suporte a link
                shutil.copyfile(copia, alvo)


# --- documento TeX ------------------------------------------------------------------------------
def _medida(v, completo):
    n = float(v[:-2] if v.endswith("pt") else v[:-1])
    return n if v.endswith("pt") else n * completo / 100


def preambulo(p):
    """Preâmbulo do preset + avisos de nível de preset (parâmetros aproximados)."""
    idx = indice_fontes()
    cat = p["categorias"]
    avisos = []

    def face(nome):
        c = cat.get(nome) or cat["texto"]
        return arquivo_fonte(idx, c["familia"], c.get("peso") == "negrito", c.get("italico", False))

    t = p["tamanhos"]
    S = _medida(t["completo"], 0)
    sub, sub2 = _medida(t["subscrito"], S), _medida(t["sub_subscrito"], S)
    if sub2 < 4:
        avisos.append(f"sub_subscrito = {sub2:g} pt (pendência D-03)")
    mat = arquivo_fonte(idx, p.get("fonte_matematica", "STIX Two Math"))
    if p.get("fonte_matematica") and "MATH" not in TTFont(mat[0], lazy=True, fontNumber=mat[1]):
        raise ErroRender(f"fonte_matematica sem tabela MATH: {p['fonte_matematica']}")
    linhas = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb,mathtools,cancel,xcolor,array}",
        r"\usepackage[math-style=upright,bold-style=upright]{unicode-math}",
        r"\setmainfont" + _fontspec(*face("texto")),
        r"\setmathfont" + _fontspec(*mat),
        r"\setmathrm" + _fontspec(*face("funcao")),
        r"\newfontfamily\eqvetor" + _fontspec(*face("vetor_matriz")),
    ]
    # P-08: fonte de codificação antiga (Symbol do Windows). Duas formas de usá-la:
    #  "antiga": as posições U+F0xx estão numa tabela Unicode (Symbol do Office para Mac) → \Umathcode
    #  "glifo": só a tabela 3,0 (Symbol do Windows) → o desenho é pedido pelo número interno (glifo)
    antigas, glifos = {}, {}  # arquivo → {unicode: código | número do glifo}
    for nome in ("grego_min", "grego_mai", "simbolo"):
        arq, n = face(nome)
        cods = ALFABETOS[nome][1] if nome in ALFABETOS else FAIXAS[nome]
        if _antiga(arq, n):
            cm = _cmap(arq, n)
            antigas.setdefault((arq, n), {}).update(
                {u: CODIFICACAO_SYMBOL[u] for u in cods if u in CODIFICACAO_SYMBOL and 0xF000 + CODIFICACAO_SYMBOL[u] in cm})
        elif mapa := _glifos_simbolo(arq, n):  # tem a tabela antiga (3,0): tudo por glifo
            glifos.setdefault((arq, n), {}).update({u: mapa[u] for u in cods if u in mapa})
    for nome, (alfabeto, cods) in ALFABETOS.items():
        arq, n = face(nome)
        if (arq, n) in antigas or (arq, n) in glifos:
            continue
        if set(cods) <= _cmap(arq, n):
            linhas.append(r"\setmathfont" + _fontspec(arq, n, "range={" + alfabeto + "}"))
        else:
            avisos.append(f"{nome}: {cat[nome]['familia']} não cobre o alfabeto; usada a fonte_matematica")
    for nome, cods in FAIXAS.items():
        arq, n = face(nome)
        if (arq, n) in antigas or (arq, n) in glifos:
            continue
        tem = sorted(set(cods) & _cmap(arq, n))
        if tem:
            faixa = ",".join(f'"{c:X}' for c in tem)
            linhas.append(r"\setmathfont" + _fontspec(arq, n, "range={" + faixa + "}"))
    for k, ((arq, n), mapa) in enumerate(antigas.items()):
        linhas += _familia_antiga(k, arq, n, mapa, (S, sub, max(sub2, 1)))
    for k, ((arq, n), mapa) in enumerate(glifos.items()):
        linhas += _familia_glifos(k, arq, n, mapa, (S, sub, max(sub2, 1)))
    linhas += [
        rf"\DeclareMathSizes{{{S:g}}}{{{S:g}}}{{{sub:g}}}{{{sub2:g}}}",
        r"\AtBeginDocument{\renewcommand\mathbf[1]{\text{\eqvetor#1}}}",
        r"\tracinglostchars=2",
    ]
    esp = p.get("espacamentos", {})
    if "linespace" in esp:
        L = _medida(esp["linespace"], S)
        extra = f"{max(0, L - 1.2 * S):.3f}pt"
        linhas += [rf"\renewcommand\arraystretch{{{L / (1.2 * S):.4f}}}", rf"\setlength\jot{{{extra}}}",
                   rf"\setlength\extrarowheight{{{extra}}}"]
    if "matrixcol" in esp:
        linhas.append(rf"\setlength\arraycolsep{{{_medida(esp['matrixcol'], S) / 2:.3f}pt}}")
    # FracBox do MTEF: numerador e denominador em tamanho cheio → \frac com estilo display (0)
    def esp_pt(*nomes):
        v = next((esp[n] for n in nomes if n in esp), None)
        return f"{_medida(v, S):.3f}pt" if v else ""  # "" = espessura padrão da fonte
    linhas.append(r"\AtBeginDocument{\renewcommand\frac[2]{\genfrac{}{}{%s}{0}{#1}{#2}}"
                  r"\renewcommand\tfrac[2]{\genfrac{}{}{%s}{1}{#1}{#2}}}"
                  % (esp_pt("fractthick"), esp_pt("fractthick2", "fractthick")))
    for nome, regs in (("operspacing", (r"\medmuskip", r"\thickmuskip")), ("nonoperspacing", (r"\thinmuskip",))):
        if nome in esp:
            k = float(esp[nome][:-1]) / 100 if esp[nome].endswith("%") else 1
            base = {r"\thinmuskip": (3, 0, 0), r"\medmuskip": (4, 2, 4), r"\thickmuskip": (5, 0, 5)}
            for r in regs:
                a, b, c = (x * k for x in base[r])
                linhas.append(rf"\AtBeginDocument{{{r}={a:g}mu plus {b:g}mu minus {c:g}mu}}")
    aprox = sorted(set(esp) - ESPACOS_TRADUZIDOS)
    if aprox:
        avisos.append("espaçamentos aproximados pela fonte matemática: " + ", ".join(aprox))
    avisos.append("tamanhos simbolo/sub_simbolo aproximados pela fonte matemática")
    if p["saida"]["formato"] != "pdf":
        avisos.append(f"saida.formato={p['saida']['formato']}: PDF/X ainda não aplicado, gerado PDF simples")
    if any(c.get("cor") for c in cat.values()):
        raise ErroRender("cor por categoria (categorias.*.cor) ainda não implementada")
    linhas += [
        r"\newcommand\eqpressitem[2]{\setbox0\hbox{$\displaystyle #2$}%",
        r"\typeout{EQPRESS|#1|\the\wd0|\the\ht0|\the\dp0}%",
        r"\pdfpagewidth=\wd0 \pdfpageheight=\dimexpr\ht0+\dp0\relax",
        r"\shipout\vbox{\box0}}",
        r"\hoffset=-1in \voffset=-1in",
        r"\begin{document}",
        rf"\fontsize{{{S:g}}}{{{1.2 * S:g}}}\selectfont",
    ]
    return "\n".join(linhas) + "\n", avisos


def _familia_antiga(k, arq, n, mapa, tamanhos):
    """Família matemática com uma fonte de codificação antiga: cada caractere (e o comando do
    LaTeX que o produz) aponta para a posição U+F000+código dessa fonte."""
    from .conversor import GREGO, SIMBOLOS
    comandos = {}
    for ch, cmd in {**SIMBOLOS, **GREGO}.items():
        if re.fullmatch(r"\\[A-Za-z]+", cmd):
            comandos.setdefault(ord(ch), set()).add(cmd)
    for cmd, ch in {r"\leq": "≤", r"\geq": "≥", r"\neq": "≠", r"\to": "→", r"\gets": "←"}.items():
        comandos.setdefault(ord(ch), set()).add(cmd)
    nome = "eqant" + "abcdefgh"[k]
    caminho = f"{PASTA_TEX}/{_local(arq)}" + (f":{n}" if n else "")
    linhas = [rf'\font\{nome}{t}="[{caminho}]" at {s:g}pt' for t, s in zip("ABC", tamanhos)]
    # número fixo alto: com \newfam o \mathrm (alocado depois, sob demanda) caía na mesma família
    linhas.append(rf"\chardef\{nome}fam={250 - k}")
    defs = [rf"\textfont\{nome}fam=\{nome}A \scriptfont\{nome}fam=\{nome}B \scriptscriptfont\{nome}fam=\{nome}C"]
    for u, cod in sorted(mapa.items()):
        ch = chr(u)
        classe = 3 if ch in RELACAO_TEX else 2 if ch in BINARIO_TEX else 0
        alvo = rf'"{classe} \{nome}fam "{0xF000 + cod:X}'
        defs.append(rf'\Umathcode"{u:X}={alvo}')
        if u == 0x2212:
            defs.append(rf'\Umathcode"2D={alvo}')  # o "-" do LaTeX é o sinal de menos
        defs += [rf"\Umathchardef{c}={alvo}" for c in sorted(comandos.get(u, ()))]
    return linhas + [r"\AtBeginDocument{" + "%\n".join(defs) + "}"]


@functools.lru_cache(maxsize=None)
def _glifos_simbolo(arq, n):
    """{unicode: número do glifo} pela tabela 3,0 (U+F000+código da codificação Symbol)."""
    f = TTCollection(arq, lazy=True).fonts[n] if arq.lower().endswith((".ttc", ".otc")) else TTFont(arq, lazy=True)
    t30 = next((t for t in f["cmap"].tables if (t.platformID, t.platEncID) == (3, 0)), None)
    if t30 is None:
        return {}
    mapa = {}
    for u, cod in CODIFICACAO_SYMBOL.items():
        nome = t30.cmap.get(0xF000 + cod) or t30.cmap.get(cod)
        if nome:
            mapa[u] = f.getGlyphID(nome)
    return mapa


def _comandos_latex():
    """{unicode: {comandos LaTeX que produzem o caractere}} (tabelas do conversor + aliases)."""
    from .conversor import GREGO, SIMBOLOS
    comandos = {}
    for ch, cmd in {**SIMBOLOS, **GREGO}.items():
        if re.fullmatch(r"\\[A-Za-z]+", cmd):
            comandos.setdefault(ord(ch), set()).add(cmd)
    for cmd, ch in {r"\leq": "≤", r"\geq": "≥", r"\neq": "≠", r"\to": "→", r"\gets": "←"}.items():
        comandos.setdefault(ord(ch), set()).add(cmd)
    return comandos


def _familia_glifos(k, arq, n, mapa, tamanhos):
    r"""Symbol do Windows (só tabela 3,0): cada símbolo vira uma caixa com o glifo pedido pelo
    número interno (\XeTeXglyph), na classe matemática certa e nos três tamanhos. O caractere
    digitado (⇒) fica ativo em modo matemático; os comandos (\Rightarrow) apontam para a mesma caixa."""
    nome = "eqglf" + "abcdefgh"[k]
    caminho = f"{PASTA_TEX}/{_local(arq)}" + (f":{n}" if n else "")
    linhas = [rf'\font\{nome}{t}="[{caminho}]" at {s:g}pt' for t, s in zip("ABC", tamanhos)]
    comandos = _comandos_latex()
    defs = []
    for u, gid in sorted(mapa.items()):
        ch = chr(u)
        classe = r"\mathrel" if ch in RELACAO_TEX else r"\mathbin" if ch in BINARIO_TEX else r"\mathord"
        caixa = lambda t: rf"\hbox{{\{nome}{t}\XeTeXglyph{gid}\relax}}"  # noqa: E731
        corpo = rf"{classe}{{\mathchoice{{{caixa('A')}}}{{{caixa('A')}}}{{{caixa('B')}}}{{{caixa('C')}}}}}"
        # nome de comando no TeX só tem letras: os dígitos hexadecimais viram letras (0→g … F→v)
        macro = rf"\{nome}u" + "".join("ghijklmnopqrstuv"[int(c, 16)] for c in f"{u:X}")
        defs.append(rf"\def{macro}{{{corpo}}}")
        # caractere literal: só os de até 255 podem ficar ativos em modo matemático (\mathcode"8000);
        # os demais chegam sempre como comando (o conversor e o editor escrevem \Rightarrow, \alpha…)
        alvos = [0x2D] if u == 0x2212 else [u] if u <= 0xFF else []  # o "-" do LaTeX é o sinal de menos
        for a in alvos:
            defs.append(rf'\mathcode"{a:X}="8000 \begingroup\lccode`\~="{a:X}\lowercase{{\endgroup\let~}}{macro}')
        defs += [rf"\let{c}{macro}" for c in sorted(comandos.get(u, ()))]
    return linhas + [r"\AtBeginDocument{" + "%\n".join(defs) + "}"]


# --- execução --------------------------------------------------------------------------------------
def _exe(nome):
    caminho = P.ferramenta(nome)
    if not caminho:
        raise ErroRender(f"{nome} não encontrado neste computador (reinstale o EqPress)")
    return caminho


def _rodar(cmd, **kw):
    cmd = [_exe(cmd[0]) if cmd[0] in ("gs", "tectonic", "inkscape") else cmd[0], *cmd[1:]]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **P.SEM_JANELA, **kw)
    if r.returncode:
        raise ErroRender(f"{Path(cmd[0]).name} falhou: {(r.stderr or r.stdout)[-800:]}")
    return r


def _compilar(pre, itens, pasta):
    """Um documento, uma página por equação. Devolve (pdf, [(id, wd, ht, dp, avisos)])."""
    tex = pasta / "eq.tex"
    _preparar_fontes(pre, pasta)
    tex.write_text(pre + "".join(rf"\eqpressitem{{{i}}}{{{lx}}}" + "\n" for i, lx in itens) + r"\end{document}" + "\n", encoding="utf-8")
    extra_env, extra_args = P.ambiente_tectonic()
    r = subprocess.run([_exe("tectonic"), "-X", "compile", "--keep-logs", *extra_args, "--outdir", str(pasta), str(tex)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, **extra_env}, **P.SEM_JANELA)
    log = (pasta / "eq.log").read_text(errors="replace", encoding="utf-8") if (pasta / "eq.log").exists() else r.stderr
    if r.returncode:
        # a linha "! …" do TeX (e a seguinte, com o trecho) é o que interessa a quem edita
        linhas = log.splitlines()
        msg = [f"{x[2:].strip()} {linhas[k + 1].strip()}" for k, x in enumerate(linhas[:-1]) if x.startswith("! ")]
        raise ErroRender("; ".join(msg[:2]) or f"tectonic falhou: {r.stderr[-300:]}")
    res, faltando = [], []
    for linha in log.splitlines():
        m = re.match(r"EQPRESS\|(.+?)\|([\d.]+)pt\|([\d.]+)pt\|([\d.]+)pt", linha)
        if m:
            res.append((m[1], float(m[2]), float(m[3]), float(m[4]), faltando))
            faltando = []
        elif linha.startswith("Missing character") and "(U+0020)" not in linha:
            # P-06: glifo ausente nunca em silêncio. O espaço (U+0020) é exceção: a Symbol do
            # Windows só o tem na posição antiga, o XeTeX o procura ao carregá-la, e em fórmula
            # espaço nunca é desenhado
            faltando.append(linha.strip())
    if len(res) != len(itens):
        raise ErroRender(f"{len(res)} de {len(itens)} equações compiladas")
    return pasta / "eq.pdf", res


def _bboxes(pdf):
    r = _rodar(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=bbox", str(pdf)])
    return [tuple(map(float, m)) for m in re.findall(r"%%HiResBoundingBox: (\S+) (\S+) (\S+) (\S+)", r.stderr)]


# --- cor ------------------------------------------------------------------------------------------
OPS_COR = {"g": 1, "G": 1, "rg": 3, "RG": 3, "k": 4, "K": 4, "sc": None, "SC": None, "scn": None, "SCN": None}


def _e_preto(vals):
    if len(vals) == 1:
        return True
    if len(vals) == 3:
        return max(vals) - min(vals) < 1e-3
    return max(vals[:3]) < 1e-3


def _ops_cor(cor, contorno, nome_cs):
    """Operadores PDF para a cor do preset (PRESET §5). contorno=True → versão maiúscula (traço)."""
    if cor["modelo"] == "cmyk":
        return [([round(v / 100, 4) for v in cor["valores"]], "K" if contorno else "k")]
    if cor["modelo"] == "cinza":
        return [([1 - cor["valor"] / 100], "G" if contorno else "g")]
    t = cor.get("tinta", 100) / 100
    return [([pikepdf.Name(nome_cs)], "CS" if contorno else "cs"), ([t], "SCN" if contorno else "scn")]


def _cs_especial(pdf, cor):
    alt = [v / 100 for v in cor["alternativa_cmyk"]]
    func = pdf.make_indirect(pikepdf.Dictionary(FunctionType=2, Domain=[0, 1], C0=[0, 0, 0, 0], C1=alt, N=1))
    return pikepdf.Array([pikepdf.Name.Separation, pikepdf.Name("/" + cor["nome"]), pikepdf.Name.DeviceCMYK, func])


def _normalizar(pdf, conteudo, p, avisos):
    """Reescreve toda cor do stream na cor do preset; preto → padrao, outra → destaque."""
    defs = p["cores"]["definicoes"]
    padrao = defs[p["cores"]["padrao"]]
    destaque = defs.get(p["cores"].get("destaque", ""), padrao)
    novos = []
    for operandos, op in pikepdf.parse_content_stream(conteudo):
        nome = str(op)
        if nome in ("cs", "CS"):
            continue  # o espaço de cor é decidido por nós
        if nome in ("sh", "BI", "ID", "EI"):
            raise ErroRender(f"operador {nome} (sombreado/imagem) no PDF da equação (CA-05)")
        if nome in OPS_COR:
            vals = [float(v) for v in operandos if not isinstance(v, pikepdf.Name)]
            if len(vals) not in (1, 3, 4):
                raise ErroRender(f"cor não reconhecida: {operandos} {nome}")
            cor = padrao if _e_preto(vals) else destaque
            if cor is destaque and destaque is padrao:
                avisos.append("cor de origem ignorada (preset sem 'destaque')")
            contorno = nome.isupper()
            ncs = "/CSEq" + ("D" if cor is destaque and destaque is not padrao else "P")
            novos += [(o, pikepdf.Operator(x)) for o, x in _ops_cor(cor, contorno, ncs)]
            continue
        novos.append((operandos, op))
    return pikepdf.unparse_content_stream(novos)


def _finalizar(origem, n, p, w, h, d, caixa_tinta, destino):
    """Página n do PDF em contorno → PDF da equação: cor, sobreimpressão, caixa, sem metadados."""
    src = pikepdf.open(origem)
    out = pikepdf.new()
    out.pages.append(src.pages[n])
    pg = out.pages[0]
    avisos = []
    recursos = pg.obj.get("/Resources", pikepdf.Dictionary())
    for nome, xo in list(recursos.get("/XObject", {}).items()):
        if xo.get("/Subtype") == "/Image":
            raise ErroRender("imagem raster no PDF da equação (CA-05)")
        xo.write(_normalizar(out, xo, p, avisos))
    conteudo = _normalizar(out, pg.obj, p, avisos)
    defs = p["cores"]["definicoes"]
    cs = pikepdf.Dictionary()
    for chave, nome_cor in (("/CSEqP", p["cores"]["padrao"]), ("/CSEqD", p["cores"].get("destaque"))):
        if nome_cor and defs[nome_cor]["modelo"] == "especial":
            cs[chave] = _cs_especial(out, defs[nome_cor])
    if len(cs):
        recursos["/ColorSpace"] = cs
    if p["cores"].get("sobreimpressao", True):
        if "/ExtGState" not in recursos:
            recursos["/ExtGState"] = pikepdf.Dictionary()
        recursos.ExtGState["/GSEq"] = pikepdf.Dictionary(Type=pikepdf.Name.ExtGState, OP=True, op=True, OPM=1)
        conteudo = b"/GSEq gs\n" + conteudo
    pg.obj["/Resources"] = recursos
    pg.obj["/Contents"] = out.make_stream(conteudo)
    # caixa = caixa do TeX ∪ tinta (glifo que vaza da caixa não pode ser cortado)
    x0, y0, x1, y1 = caixa_tinta or (0, 0, w, h + d)
    caixa = [min(0, x0), min(0, y0), max(w, x1), max(h + d, y1)]
    caixa = [round(v, 3) for v in caixa]
    for b in ("/MediaBox", "/CropBox", "/TrimBox"):
        pg.obj[b] = pikepdf.Array(caixa)
    for k in ("/Metadata", "/PieceInfo"):
        if k in out.Root:
            del out.Root[k]
    if "/Info" in out.trailer:
        del out.trailer["/Info"]
    out.save(destino, deterministic_id=True, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.disable)
    largura = caixa[2] - caixa[0]
    profundidade = d - caixa[1]  # baseline em y = dp
    return largura, caixa[3] - caixa[1], profundidade, sorted(set(avisos))


# --- extras ---------------------------------------------------------------------------------------
def _eps(pdf, destino):
    _rodar(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dNoOutputFonts", "-sDEVICE=eps2write",
            "-sColorConversionStrategy=LeaveColorUnchanged", f"-sOutputFile={destino}", str(pdf)])
    # a BoundingBox do eps2write é a da tinta; volta para a caixa do PDF (baseline = métricas)
    with pikepdf.open(pdf) as d:
        x0, y0, x1, y1 = [float(v) for v in d.pages[0].MediaBox]
    dados = Path(destino).read_bytes()
    dados = re.sub(rb"%%(CreationDate|Invocation):[^\n]*\n", b"", dados)  # P-01: sem data/caminho
    dados = re.sub(rb"%%BoundingBox: [^\n]*", b"%%%%BoundingBox: %d %d %d %d" % (
        int(x0 // 1), int(y0 // 1), -int(-x1 // 1), -int(-y1 // 1)), dados, count=1)
    dados = re.sub(rb"%%HiResBoundingBox: [^\n]*", b"%%%%HiResBoundingBox: %.6f %.6f %.6f %.6f" % (x0, y0, x1, y1), dados, count=1)
    Path(destino).write_bytes(dados)


def _emf(pares):
    """[(pdf, emf)] numa única execução do Inkscape (um processo por arquivo é lento)."""
    if not pares:
        return
    acoes = "".join(f"file-open:{Path(pdf).as_posix()};export-filename:{Path(emf).as_posix()};export-do;file-close;"
                    for pdf, emf in pares)
    _rodar(["inkscape", "--pdf-poppler", f"--actions={acoes}"])
    faltam = [str(e) for _, e in pares if not Path(e).exists()]
    if faltam:
        raise ErroRender(f"Inkscape não gerou: {faltam[:3]}")
    for pdf, emf in pares:
        _corrigir_quadro_emf(pdf, emf)


def _corrigir_quadro_emf(pdf, emf):
    """O Inkscape grava no cabeçalho do EMF um quadro maior que o desenho (≈ +2 pt na altura);
    Word e InDesign esticam o quadro até o tamanho da imagem e a equação sai achatada.
    Regrava rclBounds (unidades do dispositivo) e rclFrame (0,01 mm) com a caixa do PDF."""
    import struct
    with pikepdf.open(pdf) as d:
        x0, y0, x1, y1 = [float(v) for v in d.pages[0].MediaBox]
    dados = bytearray(Path(emf).read_bytes())
    dev_x, dev_y, mm_x, mm_y = struct.unpack_from("<4i", dados, 72)
    w, h = x1 - x0, y1 - y0
    por_pt_x, por_pt_y = dev_x / mm_x * 25.4 / 72, dev_y / mm_y * 25.4 / 72
    struct.pack_into("<4i", dados, 8, 0, 0, round(w * por_pt_x), round(h * por_pt_y))
    struct.pack_into("<4i", dados, 24, 0, 0, round(w / 72 * 2540), round(h / 72 * 2540))
    Path(emf).write_bytes(bytes(dados))


# --- API --------------------------------------------------------------------------------------------
def renderizar_lote(itens, p, pasta_saida):
    """itens: [(id, latex)]. Grava <pasta>/<NNNN>.pdf (+ extras). Nunca falha em silêncio:
    equação com problema volta com `erro` preenchido e as demais seguem."""
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pre, avisos_preset = preambulo(p)
    saidas = {i: Saida(i) for i, _ in itens}
    validos = []
    for i, lx in itens:
        if not lx or not lx.strip():
            saidas[i].erro = "equação vazia"
        else:
            validos.append((i, lx))
    with tempfile.TemporaryDirectory(prefix="eqpress-") as tmp:
        tmp = Path(tmp)
        try:
            pdf, res = _compilar(pre, validos, tmp)
            grupos = [(validos, pdf, res)]
        except ErroRender:
            # isola as equações com erro de TeX compilando uma a uma
            grupos = []
            for k, (i, lx) in enumerate(validos):
                sub = tmp / f"u{k}"
                sub.mkdir()
                try:
                    pdf1, res1 = _compilar(pre, [(i, lx)], sub)
                    grupos.append(([(i, lx)], pdf1, res1))
                except ErroRender as e:
                    saidas[i].erro = f"LaTeX não compila: {e}"
        for itens_g, pdf, res in grupos:
            contorno = pdf.with_name(pdf.stem + "_c.pdf")
            _rodar(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dNoOutputFonts", "-sDEVICE=pdfwrite",
                    "-sColorConversionStrategy=LeaveColorUnchanged", "-dAutoRotatePages=/None",
                    f"-sOutputFile={contorno}", str(pdf)])
            caixas = _bboxes(contorno)
            for n, ((i, _), (_, w, h, d, faltando)) in enumerate(zip(itens_g, res)):
                s = saidas[i]
                if faltando:
                    s.erro = "glifo ausente nas fontes do preset (P-06): " + "; ".join(faltando)
                    continue
                destino = pasta_saida / f"{i.removeprefix('EQ-')}.pdf"
                try:
                    tinta = caixas[n] if n < len(caixas) and caixas[n][2] > caixas[n][0] else None
                    # a caixa de tinta do gs tem origem no canto da página: já no sistema do TeX
                    s.largura_pt, s.altura_pt, s.profundidade_pt, av = _finalizar(
                        contorno, n, p, w * 72 / 72.27, h * 72 / 72.27, d * 72 / 72.27, tinta, destino)
                    s.avisos += av
                    s.pdf = destino
                    if "eps" in p["saida"].get("extras", []):
                        _eps(destino, destino.with_suffix(".eps"))
                        s.extras["eps"] = destino.with_suffix(".eps")
                except ErroRender as e:
                    s.erro = str(e)
    if "emf" in p["saida"].get("extras", []):
        prontas = [s for s in saidas.values() if s.pdf]
        _emf([(s.pdf, s.pdf.with_suffix(".emf")) for s in prontas])
        for s in prontas:
            s.extras["emf"] = s.pdf.with_suffix(".emf")
    for s in saidas.values():
        s.largura_pt, s.altura_pt, s.profundidade_pt = (round(v, 3) for v in (s.largura_pt, s.altura_pt, s.profundidade_pt))
    return [saidas[i] for i, _ in itens], avisos_preset


def renderizar(id_, latex, p, pasta_saida):
    """Uma equação (editor, `eqpress renderizar`): mesmo caminho do lote (ED-21, P-01)."""
    (s,), _ = renderizar_lote([(id_, latex)], p, pasta_saida)
    return s


# --- QA (CA-06 / CA-08 / CA-05) -----------------------------------------------------------------------
def verificar_pdf(pdf, p):
    """Erros de separação: só os operadores da cor do preset, sobreimpressão, nada raster."""
    erros = []
    doc = pikepdf.open(pdf)
    defs = p["cores"]["definicoes"]
    permitidas = {nome for nome in (p["cores"]["padrao"], p["cores"].get("destaque")) if nome}
    esperado = set()
    for nome in permitidas:
        c = defs[nome]
        if c["modelo"] == "cmyk":
            esperado |= {("k", tuple(round(v / 100, 4) for v in c["valores"])), ("K", tuple(round(v / 100, 4) for v in c["valores"]))}
        elif c["modelo"] == "cinza":
            esperado |= {(o, (round(1 - c["valor"] / 100, 4),)) for o in "gG"}
        else:
            esperado |= {(o, (round(c.get("tinta", 100) / 100, 4),)) for o in ("scn", "SCN")}
    pg = doc.pages[0]
    streams = [pg.obj] + [x for x in pg.Resources.get("/XObject", {}).values()]
    for st in streams:
        if st.get("/Subtype") == "/Image":
            erros.append("imagem raster")
            continue
        for operandos, op in pikepdf.parse_content_stream(st):
            o = str(op)
            if o in OPS_COR:
                vals = tuple(round(float(v), 4) for v in operandos if not isinstance(v, pikepdf.Name))
                if (o, vals) not in esperado:
                    erros.append(f"cor fora do preset: {vals} {o}")
    if p["cores"].get("sobreimpressao", True):
        gs_ = pg.Resources.get("/ExtGState", {}).get("/GSEq")
        if gs_ is None or not (gs_.OP and gs_.op and gs_.OPM == 1):
            erros.append("sobreimpressão ausente (CA-08)")
    return sorted(set(erros))


def cobertura_tinta(*arquivos):
    """Ghostscript inkcov: [(C, M, Y, K)] por página, de todos os arquivos (CA-06, segunda checagem)."""
    r = _rodar(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=inkcov", "-o", "-", *map(str, arquivos)])
    return [tuple(map(float, m)) for m in re.findall(r"^\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+CMYK", r.stdout, re.M)]


def cobertura_chapas(arquivo):
    """Ghostscript tiffsep: {chapa: nº de pixels com tinta} (CA-06/CA-16, inclui tintas especiais)."""
    with tempfile.TemporaryDirectory(prefix="eqpress-sep-") as tmp:
        _rodar(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dEPSCrop", "-sDEVICE=tiffsep", "-r300",
                f"-sOutputFile={tmp}/s.tif", str(arquivo)])
        from PIL import Image
        res = {}
        for f in Path(tmp).glob("s(*).tif"):
            h = Image.open(f).convert("L").histogram()
            res[f.name[2:-5]] = sum(h) - h[255]  # 255 = sem tinta
        return res


def ferramentas_ausentes():
    return [x for x in ("tectonic", "gs", "inkscape") if not P.ferramenta(x)]


if __name__ == "__main__":
    import sys

    preset = carregar_preset(sys.argv[1])
    s = renderizar("EQ-0001", sys.argv[2], preset, Path(sys.argv[3]))
    print(json.dumps({**s.metricas(), "pdf": str(s.pdf), "avisos": s.avisos, "erro": s.erro}, ensure_ascii=False))
    sys.exit(0 if s.erro is None else 1)
