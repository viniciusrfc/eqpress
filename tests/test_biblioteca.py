import json

import pytest

from eqpress import biblioteca as B
from eqpress import renderizador as R

pytestmark = pytest.mark.skipif(bool(R.ferramentas_ausentes()), reason="ferramentas ausentes")


@pytest.fixture
def biblioteca(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "PASTA", tmp_path / "Padrões")
    return tmp_path / "Padrões"


def test_semeia_salva_versoes_importa_exporta(biblioteca, tmp_path):
    lista = B.listar()  # primeira vez: os exemplos
    assert {p["nome"] for p in lista} == {"exemplo_atual", "exemplo_resolucao"}
    base = next(p for p in lista if p["nome"] == "exemplo_atual")
    campos = {**base, "nome": "Física 8º ano – Arial 10", "familia": "Arial", "corpo": 10}
    v1 = B.salvar(campos, base["arquivo"])
    assert v1["arquivo"].endswith("fisica_8o_ano_arial_10_v1.json") and v1["nome"] == "Física 8º ano – Arial 10"
    v2 = B.salvar({**v1, "corpo": 11}, v1["arquivo"])  # editar = versão nova (O3)
    assert v2["versao"] == 2 and v2["corpo"] == 11 and (biblioteca / "fisica_8o_ano_arial_10_v1.json").exists()
    p = R.carregar_preset(v2["arquivo"])  # schema válido
    assert p["categorias"]["simbolo"]["familia"] == "Symbol" and p["tamanhos"]["completo"] == "11pt"
    # tinta especial
    esp = B.salvar({**v2, "nome": "Resolução", "cor": "especial", "tinta": "PANTONE 219 C", "alternativa": [0, 90, 0, 0]})
    pe = R.carregar_preset(esp["arquivo"])
    assert pe["cores"]["padrao"] == "PANTONE 219 C" and pe["cores"]["definicoes"]["PANTONE 219 C"]["modelo"] == "especial"
    with pytest.raises(R.ErroRender, match="nome da tinta"):
        B.salvar({**v2, "cor": "especial", "tinta": " "})
    # exportar e importar em outro Mac (outra pasta)
    B.exportar(v2["arquivo"], tmp_path / "enviado.json")
    with pytest.raises(R.ErroRender, match="Já existe"):
        B.importar(tmp_path / "enviado.json")
    B.PASTA = tmp_path / "OutroMac"
    imp = B.importar(tmp_path / "enviado.json")
    assert imp["corpo"] == 11 and json.loads((tmp_path / "OutroMac" / "fisica_8o_ano_arial_10_v2.json").read_text())["titulo"]


def test_fonte_ausente_nao_grava(biblioteca):
    base = B.listar()[0]
    with pytest.raises(R.ErroRender, match="ausente"):
        B.salvar({**base, "nome": "x", "familia": "Fonte Que Não Existe"})
    assert not list(biblioteca.glob("x_v*.json"))
