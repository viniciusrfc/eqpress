import re
import zipfile
from pathlib import Path

import pytest

from eqpress.extrator import extrair, para_json

SAMPLES = Path(__file__).parent.parent / "samples"
# FORMATO_DOCX_OLE §1: (equações, destacadas)
CORPUS = {
    "corpus_cn_questoes.docx": (45, 7),
    "corpus_cn_resolucoes.docx": (56, 35),
    "corpus_mt_questoes.docx": (80, 12),
    "corpus_mt_resolucoes.docx": (101, 48),
}
pytestmark = pytest.mark.skipif(not SAMPLES.exists(), reason="samples/ ausente (não versionado)")


@pytest.mark.parametrize("nome", CORPUS)
def test_corpus(nome):
    ex = extrair(SAMPLES / nome)
    n, destacadas = CORPUS[nome]
    xml = zipfile.ZipFile(SAMPLES / nome).read("word/document.xml").decode()
    assert len(ex.equacoes) == n == ex.total_w_object == len(re.findall(r"<w:object[ >]", xml))
    assert ex.outros_objetos == []
    assert sum(e.destacada for e in ex.equacoes) == destacadas
    assert [e.id for e in ex.equacoes] == [f"EQ-{i:04d}" for i in range(1, n + 1)]
    for e in ex.equacoes:
        assert e.avisos == [] and e.local == "corpo"
        assert e.mtef[:5] == b"\x05\x01\x00\x07\x04"  # MTEF v5, Windows, MathType 7.4
        assert e.position_meio_pt < 0  # R-DOCX-03
        assert e.previa.endswith(".wmf")  # R-PREV-01
        # R-DOCX-02: exibido ≈ original (no corpus diferem ≤ 0,3 pt; style pode vir em pt ou in)
        assert abs(e.largura_pt - e.dxa_orig / 20) <= 0.5 and abs(e.altura_pt - e.dya_orig / 20) <= 0.5
    para_json(ex)  # serializável


def test_total_282():
    assert sum(len(extrair(SAMPLES / n).equacoes) for n in CORPUS) == 282


def test_sintetico_tabela_e_outro_progid(tmp_path):
    """R-DOCX-01/05: outro ProgID é reportado; equação em tabela tem local 'tabela'."""
    origem = SAMPLES / "corpus_cn_questoes.docx"
    destino = tmp_path / "sint.docx"
    with zipfile.ZipFile(origem) as zi, zipfile.ZipFile(destino, "w") as zo:
        for item in zi.infolist():
            dados = zi.read(item)
            if item.filename == "word/document.xml":
                xml = dados.decode()
                ini = [m.start() for m in re.finditer(r"<w:r[ >]", xml[: xml.index("<w:object")])][-1]
                fim = xml.index("</w:r>", xml.index("</w:object>")) + len("</w:r>")
                run = xml[ini:fim]
                tabela = f"<w:tbl><w:tr><w:tc><w:p>{run}</w:p></w:tc></w:tr></w:tbl>"
                outro = run.replace("Equation.DSMT4", "Excel.Sheet.12")
                corpo = xml.index("<w:body>") + len("<w:body>")
                xml = xml[:corpo] + tabela + f"<w:p>{outro}</w:p>" + xml[corpo:]
                dados = xml.encode()
            zo.writestr(item, dados)
    ex = extrair(destino)
    assert len(ex.equacoes) == 46 and ex.total_w_object == 47
    assert ex.equacoes[0].local == "tabela" and ex.equacoes[0].destacada
    assert ex.outros_objetos == [{"parte": "word/document.xml", "paragrafo": 1, "progid": "Excel.Sheet.12"}]
