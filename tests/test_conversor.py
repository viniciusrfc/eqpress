import json
import shutil
import subprocess
from pathlib import Path

import pytest
from lxml import etree

from eqpress.conversor import EMBELEZ, converter
from eqpress.extrator import extrair

RAIZ = Path(__file__).parent.parent
SAMPLES = RAIZ / "samples"
VERIFICAR = RAIZ / "ferramentas/web/verificar.js"
TEM_WEB = shutil.which("node") and (RAIZ / "ferramentas/web/node_modules/katex").exists()


def renderiza(latex):
    """CA-17: [{katex, mathjax}] (None = ok). Requer `npm install` em ferramentas/web."""
    out = subprocess.run(["node", str(VERIFICAR)], input=json.dumps(latex),
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def assert_renderiza(latex):
    if not TEM_WEB:
        pytest.skip("node/KaTeX/MathJax ausentes (npm install em ferramentas/web)")
    falhas = [(s, r) for s, r in zip(latex, renderiza(latex)) if r["katex"] or r["mathjax"]]
    assert falhas == []


# --- construtor de MTEF sintético (DOC-PUBLICA:MTEF5) -----------------------------------------
def car(ch, tf=3, emb=()):
    b = bytes([2, 1 if emb else 0, tf + 128]) + ord(ch).to_bytes(2, "little")
    return b + b"".join(bytes([6, 0, e]) for e in emb) + b"\0" if emb else b


def L(*objs):
    return bytes([1, 0]) + b"".join(objs) + b"\0"


NULA = bytes([1, 1])


def T(sel, var, *objs):
    return bytes([3, 0, sel, var, 0]) + b"".join(objs) + b"\0"


def eq(*objs, raiz=None):
    return bytes([5, 1, 0, 7, 4]) + b"DSMT7\0\0" + bytes([10]) + (raiz or L(*objs)) + b"\0"


X, Y = L(car("x")), L(car("y"))
FENCE = lambda e, d: (car(e, 22), car(d, 22))  # noqa: E731

# (seletor, variação, sub-objetos, LaTeX esperado) — um caso por seletor 0–37 (R-MTEF-05)
SELETORES = [
    (0, 3, (X, *FENCE("⟨", "⟩")), r"\left\langle x \right\rangle"),
    (1, 3, (X, *FENCE("(", ")")), r"\left( x \right)"),
    (2, 1, (X, car("{", 22)), r"\left\{ x \right."),
    (3, 3, (X, *FENCE("[", "]")), r"\left[ x \right]"),
    (4, 3, (X, *FENCE("|", "|")), r"\left| x \right|"),
    (5, 3, (X, *FENCE("‖", "‖")), r"\left\| x \right\|"),
    (6, 3, (X, *FENCE("⌊", "⌋")), r"\left\lfloor x \right\rfloor"),
    (7, 3, (X, *FENCE("⌈", "⌉")), r"\left\lceil x \right\rceil"),
    (8, 3, (X, *FENCE("⟦", "⟧")), r"\left[\!\left[ x \right]\!\right]"),
    (9, 0x12, (X, *FENCE("[", ")")), r"\left[ x \right)"),
    (10, 0, (X, NULA), r"\sqrt{x}"),
    (10, 1, (X, L(car("3", 8))), r"\sqrt[3]{x}"),
    (11, 0, (X, Y), r"\frac{x}{y}"),
    (12, 0, (X,), r"\underline{x}"),
    (13, 1, (X,), r"\overline{\overline{x}}"),
    (14, 0x2E, (X, Y, car("⇀", 22), car("↽", 22)), r"\xrightleftharpoons[y]{x}"),
    (15, 0x03, (X, Y, L(car("0", 8)), car("∫", 6)), r"\int\nolimits_{0}^{y} x"),
    (16, 0x43, (X, Y, L(car("i")), car("∑", 6)), r"\sum\limits_{i}^{y} x"),
    (17, 0x43, (X, Y, L(car("i")), car("∏", 6)), r"\prod\limits_{i}^{y} x"),
    (18, 0x43, (X, NULA, NULA, car("∐", 6)), r"\coprod\limits x"),
    (19, 0x41, (X, NULA, L(car("i")), car("⋃", 6)), r"\bigcup\limits_{i} x"),
    (20, 0x41, (X, NULA, L(car("i")), car("⋂", 6)), r"\bigcap\limits_{i} x"),
    (21, 0x01, (X, NULA, L(car("C")), car("∮", 6)), r"\oint\nolimits_{C} x"),
    (22, 0x41, (X, NULA, L(car("i")), car("⨁", 6)), r"\bigoplus\limits_{i} x"),
    (23, 0, (L(car("l", 2), car("i", 2), car("m", 2)), L(car("x"), car("→", 6), car("0", 8)), NULA),
     r"\mathop{\mathrm{lim}}\limits_{x\rightarrow0}"),
    (24, 0, (X, Y, car("⏟", 22)), r"\underbrace{x}_{y}"),
    (24, 1, (X, Y, car("⏞", 22)), r"\overbrace{x}^{y}"),
    (25, 0, (X, Y, car("⎵", 22)), r"\underset{y}{\underline{x}}"),
    (26, 1, (X, Y), r"\left)\overset{y}{\overline{x}}\right."),
    (27, 0, (X, NULA), r"{}_{x}"),
    (28, 0, (NULA, X), r"{}^{x}"),
    (29, 0, (X, Y), r"{}_{x}^{y}"),
    (30, 3, (X, Y), r"\left\langle x\middle|y\right\rangle"),
    (31, 2, (X,), r"\overrightarrow{x}"),
    (31, 0x0A, (X,), r"\overset{\rightharpoonup}{x}"),
    (32, 0, (X,), r"\widetilde{x}"),
    (33, 0, (X,), r"\widehat{x}"),
    (34, 0, (X,), r"\overset{\frown}{x}"),
    (35, 0, (X,), r"\overline{x\,|}"),
    (36, 6, (X,), r"\xcancel{x}"),
    (37, 0x1E, (X,), r"\boxed{x}"),
]


def test_exemplo_doc_publica():
    """Fórmula de Bhaskara, bytes 0–291 do exemplo de DOC-PUBLICA:MTEF5."""
    hexa = (
        "05 01 00 04 00 44 53 4D 54 34 00 00"
        " 13 57 69 6E 41 6C 6C 42 61 73 69 63 43 6F 64 65 50 61 67 65 73 00"
        " 11 05 54 69 6D 65 73 20 4E 65 77 20 52 6F 6D 61 6E 00 11 03 53 79 6D 62 6F 6C 00"
        " 11 05 43 6F 75 72 69 65 72 20 4E 65 77 00 11 04 4D 54 20 45 78 74 72 61 00"
        " 12 00 08 21 2F 45 8F 44 2F 41 50 F4 10 0F 47 5F 41 50 F2 1F"
        " 1E 41 50 F4 15 0F 41 00 F4 45 F4 25 F4 8F 42 5F 41 00 F4 10 0F 43 5F 41 00 F4 8F"
        " 45 F4 2A 5F 48 F4 8F 41 00 F4 10 0F 40 F4 8F 41 7F 48 F4 10 0F 41 2A 5F 44 5F 45 F4"
        " 5F 45 F4 5F 41 0F"
        " 0C 01 00 01 00 01 02 02 02 02 00 02 00 01 01 01 00 03 00 01 00 04 00 00"
        " 0A 01 00 03 00 0B 00 00 01 00 02 04 86 12 22 2D 02 00 83 62 00 02 04 86 B1 00 B1"
        " 03 00 0A 00 00 01 00 02 00 83 62 00 03 00 1C 00 00 0B 01 01 01 00 02 00 88 32 00 00 00"
        " 0A 02 04 86 12 22 2D 02 00 88 34 00 02 00 83 61 00 02 00 83 63 00 00"
        " 0B 01 01 00 00 0A 01 00 02 00 88 32 00 02 00 83 61 00 00 00 00 00"
    )
    r = converter(bytes.fromhex(hexa))
    assert r.erro is None and r.avisos == []
    assert r.latex == r"\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}"
    raiz = etree.fromstring(r.mathml)
    assert raiz.tag.endswith("math") and raiz.find(".//{*}mfrac") is not None


@pytest.mark.parametrize("sel,var,objs,esperado", SELETORES, ids=[f"sel{s[0]}_var{s[1]:x}" for s in SELETORES])
def test_seletor(sel, var, objs, esperado):
    r = converter(eq(T(sel, var, *objs)))
    assert r.erro is None
    assert r.latex == esperado
    etree.fromstring(r.mathml)


def test_seletores_cobrem_0_a_37_e_renderizam():
    assert {s[0] for s in SELETORES} == set(range(38))
    assert_renderiza([converter(eq(T(*s[:2], *s[2]))).latex for s in SELETORES])


@pytest.mark.parametrize("e", sorted(EMBELEZ))
def test_embelezamento(e):
    r = converter(eq(car("x", emb=(e,))))
    assert r.erro is None and "x" in r.latex
    etree.fromstring(r.mathml)


def test_embelezamentos_renderizam():
    assert sorted(EMBELEZ) == list(range(2, 38))
    assert_renderiza([converter(eq(car("x", emb=(e,)))).latex for e in EMBELEZ])


def test_pilha_relacional_e_matriz_com_particoes():
    pilha = bytes([4, 0, 4, 1]) + L(car("x"), car("=", 6), car("1", 8)) + L(car("y"), car("<", 6), car("2", 8)) + b"\0"
    assert converter(eq(raiz=pilha)).latex == r"\begin{aligned}x&=1\\y&<2\end{aligned}"
    # 2×2, linhas: topo sólido, meio tracejado, base nenhuma; colunas: meio sólido
    matriz = bytes([5, 0, 1, 2, 1, 2, 2, 0b00_10_01, 0b00_01_00]) + X + Y + Y + X + b"\0"
    r = converter(eq(matriz))
    assert r.latex == r"\begin{array}{c|c}\hline \displaystyle x&\displaystyle y\\\hdashline \displaystyle y&\displaystyle x\end{array}"
    assert_renderiza([r.latex, converter(eq(raiz=pilha)).latex])


def test_virgula_decimal_texto_e_funcao():
    r = converter(eq(car("1", 8), car(",", 2), car("5", 8), car(" ", 1), car("k", 1), car("m", 1),
                     car("s", 2), car("e", 2), car("n", 2), car("ã", 3), car("o", 3)))
    assert r.latex == r"1{,}5\ \text{km}\mathrm{sen}\text{ão}"
    funcao = bytes([2, 2, 130]) + ord("s").to_bytes(2, "little")  # FUNC_START
    r = converter(eq(funcao, car("e", 2), car("n", 2), car("x")))
    assert r.latex == r"\mathrm{sen}x"  # letra colada: sem espaçamento de operador
    r = converter(eq(funcao, car("e", 2), car("n", 2), car(" ", 1), car("x")))
    assert r.latex == r"\operatorname{sen}\ x"


def test_nunca_falha_em_silencio():
    """CA-13 / R-MTEF-01/02/05/06."""
    assert "versão 4" in converter(bytes([4]) + eq(X)[1:]).erro
    assert "seletor 38" in converter(eq(T(38, 0, X))).erro
    assert "registro desconhecido 50" in converter(eq(bytes([50]))).erro
    assert "fim inesperado" in converter(eq(X)[:-3]).erro
    r = converter(eq(car("", 6)))
    assert r.latex == r"\boxed{?}" and any("U+E123" in a for a in r.avisos)
    r = converter(eq(bytes([2, 0, 24 + 128]) + (0xEF05).to_bytes(2, "little")))
    assert r.latex == r"\," and r.avisos


def test_nudge_futuro_e_cor():
    nudge = bytes([2, 0x08, 130, 140, 131]) + ord("x").to_bytes(2, "little")  # dx=2, dy=3
    futuro = bytes([100, 3, 9, 9, 9])
    cor = bytes([16, 0, 0xE8, 0x03, 0, 0, 0, 0, 15, 1])  # COLOR_DEF RGB(1000,0,0) + COLOR 1
    r = converter(eq(nudge, futuro, cor, car("y")))
    assert r.erro is None and r.latex == r"x\textcolor{red}{y}"


# --- corpus -------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def corpus():
    if not SAMPLES.exists():
        pytest.skip("samples/ ausente (não versionado)")
    nomes = ["corpus_cn_questoes", "corpus_cn_resolucoes",
             "corpus_mt_questoes", "corpus_mt_resolucoes"]  # corpus de 282
    return [(f"{n}.docx", e.id, converter(e.mtef)) for n in nomes for e in extrair(SAMPLES / f"{n}.docx").equacoes]


def test_corpus_282_sem_erro(corpus):
    assert len(corpus) == 282
    assert [(a, b, r.erro) for a, b, r in corpus if r.erro] == []
    avisos = [(a, b, r.avisos) for a, b, r in corpus if r.avisos]
    # única fonte explícita do corpus (MTEF.md §4: "−1 fonte explícita: texto, com aviso")
    assert avisos == [("corpus_cn_questoes.docx", "EQ-0012",
                       ["fonte explícita (Times New Roman) tratada como texto"])]
    for *_, r in corpus:
        assert etree.fromstring(r.mathml).tag == "{http://www.w3.org/1998/Math/MathML}math"


def test_corpus_renderiza_katex_mathjax(corpus):
    """CA-17 (parte web; o LuaLaTeX entra no F3)."""
    assert_renderiza([r.latex for *_, r in corpus])


def test_corpus_amostras(corpus):
    por_id = {(a[:-5], b): r.latex for a, b, r in corpus}
    assert por_id["corpus_cn_resolucoes", "EQ-0005"] == r"\Delta V=\frac{18}{6}=3\ \text{V}"
    assert por_id["corpus_cn_resolucoes", "EQ-0012"] == (
        r"\underbrace{N_{2}(g)\ \ +\ \ 3H_{2}(g)\ \ }_{4V}\rightleftharpoons\ \ \underbrace{2NH_{3}(g)}_{2V}")
    assert por_id["corpus_mt_resolucoes", "EQ-0092"] == (
        r"\left| z \right|=\sqrt{5^{2}+\left( -12 \right)^{2}}=\sqrt{25+144}=\sqrt{169}=13.")
