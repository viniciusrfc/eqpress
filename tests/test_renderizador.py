import json
import tempfile
import re
import shutil
from pathlib import Path

import pikepdf
import pytest

from eqpress import renderizador as R
from eqpress.lote import estilizar, renderizar_json

RAIZ = Path(__file__).parent.parent
SAMPLES = RAIZ / "samples"
PRESET = RAIZ / "spec/exemplos/exemplo_atual_v1.json"
PRESET_RES = RAIZ / "spec/exemplos/exemplo_resolucao_v1.json"
CORPUS = ["corpus_cn_questoes", "corpus_cn_resolucoes",
          "corpus_mt_questoes", "corpus_mt_resolucoes"]  # os 282 de FORMATO_DOCX_OLE §1


def _pronto():
    try:
        return not R.ferramentas_ausentes() and R.carregar_preset(PRESET) and R.preambulo(R.carregar_preset(PRESET))
    except R.ErroRender:
        return False


pytestmark = pytest.mark.skipif(not _pronto(), reason="tectonic/gs/inkscape ou fontes do preset ausentes")


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    if not SAMPLES.exists():
        pytest.skip("samples/ ausente")
    base = tmp_path_factory.mktemp("corpus")
    return {n: (estilizar(SAMPLES / f"{n}.docx", PRESET, base / n), base / n) for n in CORPUS}


def test_corpus_282_pdfs_e_relatorio(corpus):
    """CA-01: entrada = PDFs, sem divergência."""
    assert sum(rel["pdfs"] for rel, _ in corpus.values()) == 282
    for rel, _ in corpus.values():
        assert rel["status"] == "ok" and rel["divergencias"] == 0 and rel["com_erro"] == []


def test_corpus_separacao_100k_e_sobreimpressao(corpus):
    """CA-05/06/08: só `0 0 0 1 k/K`, overprint, nada raster; inkcov C = M = Y = 0."""
    p = R.carregar_preset(PRESET)
    pdfs = [f for _, pasta in corpus.values() for f in sorted((pasta / "equacoes").glob("*.pdf"))]
    assert [(f, e) for f in pdfs if (e := R.verificar_pdf(f, p))] == []
    cob = R.cobertura_tinta(*pdfs)
    assert len(cob) == 282
    assert all(c == m == y == 0 and k > 0 for c, m, y, k in cob)


def test_corpus_metricas(corpus):
    """Baseline (INDESIGN BL-02): toda equação tem métricas coerentes com a caixa do PDF."""
    for _, pasta in corpus.values():
        for j in (pasta / "equacoes").glob("*.json"):
            m = json.loads(j.read_text())["metricas"]
            with pikepdf.open(j.with_suffix(".pdf")) as d:
                x0, y0, x1, y1 = map(float, d.pages[0].MediaBox)
            assert m["largura_pt"] == pytest.approx(x1 - x0, abs=0.002)
            assert m["altura_pt"] == pytest.approx(y1 - y0, abs=0.002)
            assert 0 <= m["profundidade_pt"] <= m["altura_pt"]


def test_lote_e_individual_identicos(corpus, tmp_path):
    """P-01 / ED-21: o editor (renderizar NNNN.json) produz o mesmo PDF do lote, byte a byte."""
    _, pasta = corpus["corpus_mt_resolucoes"]
    for n in ("0005", "0046"):
        shutil.copy(pasta / "equacoes" / f"{n}.json", tmp_path)
        assert renderizar_json(tmp_path / f"{n}.json", PRESET).erro is None
        assert (tmp_path / f"{n}.pdf").read_bytes() == (pasta / "equacoes" / f"{n}.pdf").read_bytes()


def test_tinta_especial_pdf_eps_emf(tmp_path):
    """COMPORTAMENTO A.5 / CA-16: preset de resolução só na PANTONE; EPS e EMF ao lado."""
    p = R.carregar_preset(PRESET_RES)
    s = R.renderizar("EQ-0001", r"\frac{\left[ NO \right]^{4}}{2}=\Delta x", p, tmp_path)
    assert s.erro is None and R.verificar_pdf(s.pdf, p) == []
    for arq in (s.pdf, s.extras["eps"]):
        chapas = R.cobertura_chapas(arq)
        assert chapas["PANTONE 219 C"] > 0
        assert all(v == 0 for k, v in chapas.items() if k != "PANTONE 219 C")
    eps = s.extras["eps"].read_bytes()
    hires = [float(v) for v in re.search(rb"%%HiResBoundingBox: (.*)", eps)[1].split()]
    assert hires == pytest.approx([0, 0, s.largura_pt, s.altura_pt], abs=0.002)
    assert b"setoverprint" in eps and b"CreationDate" not in eps
    emf = s.extras["emf"].read_bytes()
    assert emf[40:44] == b" EMF"
    # quadro do EMF = caixa do PDF (senão Word/InDesign achatam a equação)
    import struct
    fx0, fy0, fx1, fy1 = struct.unpack_from("<4i", emf, 24)
    assert (fx1 - fx0) / 2540 * 72 == pytest.approx(s.largura_pt, abs=0.02)
    assert (fy1 - fy0) / 2540 * 72 == pytest.approx(s.altura_pt, abs=0.02)


def test_nunca_falha_em_silencio(tmp_path):
    """CA-13 / P-06: glifo ausente, vazia e LaTeX inválido viram erro só da própria equação."""
    p = R.carregar_preset(PRESET)
    ss, _ = R.renderizar_lote([("EQ-0001", "x=1"), ("EQ-0002", r"\text{⇌}"), ("EQ-0003", " "),
                               ("EQ-0004", r"\frac{1"), ("EQ-0005", "y")], p, tmp_path)
    e = {s.id: s.erro for s in ss}
    assert e["EQ-0001"] is None and e["EQ-0005"] is None
    assert "glifo ausente" in e["EQ-0002"]
    assert e["EQ-0003"] == "equação vazia"
    assert "não compila" in e["EQ-0004"]
    assert sorted(f.name for f in tmp_path.glob("*.pdf")) == ["0001.pdf", "0005.pdf"]


def test_pagina_de_conferencia(tmp_path):
    """`eqpress testar`: uma imagem por equação, cada uma na frase em que está no Word."""
    from eqpress.prova import gerar
    docx = SAMPLES / "corpus_cn_resolucoes.docx"
    if not docx.exists():
        pytest.skip("samples/ ausente")
    rel = estilizar(docx, PRESET, tmp_path)
    html = gerar(docx, tmp_path, rel).read_text()
    assert html.count('<img src="png/') == 56 and "nenhum problema" in html
    assert "por meio da relação <img" in html  # EQ-0002 no meio da frase
    assert len(list((tmp_path / "equacoes").glob("*.emf"))) == 56


def test_fontes_proibidas_e_ausentes(tmp_path):
    """P-02/P-07 (MT Extra recusada) e P-03 (fonte ausente para antes de renderizar)."""
    base = json.loads(PRESET.read_text())
    base["fonte_matematica"] = "MT Extra"
    (tmp_path / "a.json").write_text(json.dumps(base))
    with pytest.raises(R.ErroRender, match="proibida"):
        R.carregar_preset(tmp_path / "a.json")
    base = json.loads(PRESET.read_text())
    base["categorias"]["texto"]["familia"] = "Fonte Que Não Existe"
    with pytest.raises(R.ErroRender, match="ausente"):
        R.preambulo(base)


# --- F4: .docx pronto -----------------------------------------------------------------------------
def test_docx_pronto(corpus):
    """CA-01 / ID-01 / BL-01: entrada = imagens no .docx = PDFs; ID no texto alternativo, na ordem;
    w:position = profundidade arredondada a 0,5 pt; tamanho = métricas; nenhum OLE sobra."""
    import zipfile

    import docx as python_docx
    from lxml import etree

    from eqpress.docx_saida import WP
    from eqpress.extrator import NS, W, extrair
    for nome, (rel, pasta) in corpus.items():
        saida = pasta / rel["docx_saida"]
        assert rel["imagens_no_docx"] == rel["pdfs"] == rel["equacoes"] and rel["ole_mantidos"] == []
        with zipfile.ZipFile(saida) as z:
            assert z.testzip() is None
            assert not [n for n in z.namelist() if "oleObject" in n or n.endswith(".wmf")]
            assert '<Default Extension="emf"' in z.read("[Content_Types].xml").decode()
            xml = z.read("word/document.xml").decode()
        assert "xmlns:ns" not in xml  # prefixos do Word (wp, a, pic)
        raiz = etree.fromstring(xml.encode())
        docprs = raiz.findall(".//wp:docPr", {"wp": WP})
        ids = [d.get("descr") for d in docprs if (d.get("descr") or "").startswith("EQ-")]
        assert ids == [f"EQ-{i:04d}" for i in range(1, rel["equacoes"] + 1)]
        for d in docprs:
            if not d.get("descr", "").startswith("EQ-"):
                continue
            m = json.loads((pasta / "equacoes" / f"{d.get('descr')[3:]}.json").read_text())["metricas"]
            run = next(d.iterancestors(f"{{{W}}}r"))
            assert int(run.find("w:rPr/w:position", NS).get(f"{{{W}}}val")) == -round(m["profundidade_pt"] * 2)
            ext = d.getparent().find("wp:extent", {"wp": WP})
            assert int(ext.get("cx")) == round(m["largura_pt"] * 12700)
            assert int(ext.get("cy")) == round(m["altura_pt"] * 12700)
            assert 0 < int(d.get("id")) < 1 << 31
        assert extrair(saida).equacoes == []
        python_docx.Document(saida)


def test_docx_mantem_ole_da_equacao_com_erro(tmp_path):
    """Equação que não renderizou continua com o OLE original no .docx (nada se perde)."""
    import zipfile
    from eqpress.docx_saida import gerar
    from eqpress.extrator import extrair
    origem = SAMPLES / "corpus_cn_questoes.docx"
    if not origem.exists():
        pytest.skip("samples/ ausente")
    emf = tmp_path / "x.emf"
    emf.write_bytes(b"\x01" * 100)
    met = {"largura_pt": 10, "altura_pt": 5, "profundidade_pt": 1}
    saidas = {f"EQ-{i:04d}": {"emf": emf, "metricas": met} for i in range(1, 46) if i != 7}
    r = gerar(origem, tmp_path / "s.docx", saidas)
    assert r["mantidas"] == ["EQ-0007"] and len(r["trocadas"]) == 44
    restantes = extrair(tmp_path / "s.docx").equacoes
    assert len(restantes) == 1 and restantes[0].mtef  # o OLE e o MTEF da EQ-0007 continuam lá
    with zipfile.ZipFile(tmp_path / "s.docx") as z:
        assert sum("oleObject" in n for n in z.namelist()) == 1


def test_padrao_simplificado(tmp_path):
    """Fonte + corpo escolhidos pelo usuário viram um preset válido e mudam a fonte do render."""
    from eqpress import padrao
    p = padrao.criar("Arial", 9, italico=True)
    R.validar_fontes(p)
    pre, _ = R.preambulo(p)
    assert "arial" in pre.lower() and r"\fontsize{9}" in pre and "calibri" not in pre.lower()  # Windows: arial.ttf
    assert p["categorias"]["variavel"] == {"familia": "Arial", "italico": True}
    assert p["categorias"]["grego_min"]["familia"] == "Symbol"  # segunda camada, como no MathType
    s = R.renderizar("EQ-0001", r"x=\frac{1}{2}", p, tmp_path)
    assert s.erro is None and R.verificar_pdf(s.pdf, p) == []
    with pytest.raises(R.ErroRender, match="ausente"):
        padrao.criar("Fonte Que Não Existe", 10)


def test_docx_editavel_mantem_mathtype(corpus):
    """Cópia para passar adiante: o mesmo MTEF de entrada (editável no MathType), prévia nova do
    EqPress no tamanho das métricas, w:position da profundidade."""
    import zipfile

    from lxml import etree

    from eqpress.extrator import NS, W, extrair
    for nome, (rel, pasta) in corpus.items():
        entrada = extrair(SAMPLES / f"{nome}.docx").equacoes
        saida = pasta / rel["docx_editavel"]
        eqs = extrair(saida).equacoes
        assert [e.mtef for e in eqs] == [e.mtef for e in entrada]  # MathType intacto
        for e in eqs:
            m = json.loads((pasta / "equacoes" / f"{e.id[3:]}.json").read_text())["metricas"]
            assert e.previa.endswith(f"eqpress_{e.id[3:]}.emf")
            assert e.largura_pt == pytest.approx(m["largura_pt"], abs=0.01)
            assert e.altura_pt == pytest.approx(m["altura_pt"], abs=0.01)
            assert e.position_meio_pt == -round(m["profundidade_pt"] * 2)
        with zipfile.ZipFile(saida) as z:
            assert z.testzip() is None
            assert not [n for n in z.namelist() if n.endswith(".wmf")]  # prévias antigas saíram


def _symbol_antiga():
    """Um arquivo da Symbol do Windows (tabela antiga 3,0) neste computador, se houver."""
    import os
    for c in [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts/symbol.ttf",
              Path("/Applications/Microsoft Word.app/Contents/Resources/DFonts/symbol.ttf")]:
        if c.exists():
            return str(c)
    return None


@pytest.mark.skipif(_symbol_antiga() is None, reason="Symbol do Windows ausente")
def test_symbol_windows_por_glifo(monkeypatch, tmp_path):
    """Symbol só com a tabela 3,0 (a do Windows): setas e símbolos pelo número do glifo (P-08),
    nada faltando, e a ⇌ (que a Symbol não tem) na fonte matemática."""
    import collections

    from eqpress.padrao import criar
    arq = _symbol_antiga()
    original = R.arquivo_fonte
    monkeypatch.setattr(R, "arquivo_fonte", lambda idx, fam, negrito=False, italico=False:
                        (arq, 0) if fam.lower() == "symbol" else original(idx, fam, negrito, italico))
    monkeypatch.setattr(R, "_antiga", lambda a, n: False)  # no Mac, a do Office também tem tabela Unicode
    pre, _ = R.preambulo(criar("Arial", 10))
    assert "XeTeXglyph" in pre
    usos = {}
    for lx in (r"\Rightarrow", "=", r"\alpha", "a-b", r"x^{a\le b}", r"\rightleftharpoons"):
        pdf, res = R._compilar(pre, [("EQ-0001", lx)], Path(tempfile.mkdtemp(dir=tmp_path)))
        assert res[0][4] == [], lx  # nenhum glifo ausente
        with pikepdf.open(pdf) as doc:
            pg = doc.pages[0]
            fontes = {str(k): str(v.BaseFont).split("+")[-1] for k, v in pg.Resources.Font.items()}
            usos[lx] = collections.Counter(fontes[str(o[0])] for o, op in pikepdf.parse_content_stream(pg) if str(op) == "Tf")
    for lx in (r"\Rightarrow", "=", r"\alpha", "a-b", r"x^{a\le b}"):
        assert any("Symbol" in f for f in usos[lx]), (lx, usos[lx])
    assert not any("Symbol" in f for f in usos[r"\rightleftharpoons"])
