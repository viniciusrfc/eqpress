import json
import shutil
from pathlib import Path

import pytest

from eqpress import editor
from eqpress import renderizador as R
from eqpress.lote import estilizar

RAIZ = Path(__file__).parent.parent
DOCX = RAIZ / "samples/corpus_cn_questoes.docx"
pytestmark = pytest.mark.skipif(bool(R.ferramentas_ausentes()) or not DOCX.exists(),
                                reason="ferramentas ou samples/ ausentes")


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("ed")
    estilizar(DOCX, RAIZ / "spec/exemplos/exemplo_atual_v1.json", base)
    return base / "equacoes"


def test_abrir_e_previa(pasta):
    a = editor.abrir(pasta / "0005.json")
    assert a["id"] == "EQ-0005" and a["latex"] and Path(a["preset"]).name == "padrao.json"
    p = editor.previa(r"x=\frac{1}{2}", a["preset"])
    assert p["png"].startswith("data:image/png;base64,") and p["metricas"]["altura_pt"] > 0
    assert "erro" in editor.previa(r"\naoexiste", a["preset"])


def test_salvar(pasta, tmp_path):
    j = tmp_path / "equacoes" / "0005.json"
    shutil.copytree(pasta, j.parent)
    shutil.copy(pasta.parent / "padrao.json", tmp_path)
    pdf = j.with_suffix(".pdf").read_bytes()
    lx = json.loads(j.read_text())["fonte"]["latex"]
    assert editor.salvar(j, lx) == {"ok": True, "sem_mudancas": True}  # CA-E2
    assert j.with_suffix(".pdf").read_bytes() == pdf
    r = editor.salvar(j, r"V=\frac{18}{3}")
    assert r["ok"] and j.with_suffix(".pdf").read_bytes() != pdf
    reg = json.loads(j.read_text())
    assert reg["fonte"]["latex"] == r"V=\frac{18}{3}" and reg["metricas"] == r["metricas"] and reg["editado_em"]
    hist = sorted(p.suffix for p in (j.parent / ".historico").iterdir())
    assert ".json" in hist and ".pdf" in hist  # ED-16
    assert R.verificar_pdf(j.with_suffix(".pdf"), R.carregar_preset(tmp_path / "padrao.json")) == []
    assert "erro" in editor.salvar(j, r"\frac{1")  # LaTeX quebrado não grava
    assert json.loads(j.read_text())["fonte"]["latex"] == r"V=\frac{18}{3}"


def test_servidor_aberto_fora_do_terminal(pasta):
    """App aberto pelo Finder/InDesign recebe PATH mínimo; o núcleo precisa achar tectonic/gs."""
    import os
    import subprocess
    import sys
    q = json.dumps({"cmd": "previa", "latex": "x=1", "preset": str(pasta.parent / "padrao.json")})
    r = subprocess.run([sys.executable, "-m", "eqpress", "servidor"], input=q + "\n", capture_output=True,
                       text=True, cwd=RAIZ, env={"HOME": os.environ["HOME"], "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"})
    assert json.loads(r.stdout).get("png"), r.stdout[:300]


def test_ajuste_so_nesta_equacao_e_reestilizar(pasta, tmp_path):
    """Fonte/corpo de uma equação só (editor) e troca do padrão do livro inteiro (reestilizar),
    que refaz todas e mantém o ajuste individual."""
    from eqpress.lote import reestilizar
    from eqpress.padrao import aplicar
    shutil.copytree(pasta, tmp_path / "equacoes")
    shutil.copy(pasta.parent / "padrao.json", tmp_path)
    j5, j6 = tmp_path / "equacoes/0005.json", tmp_path / "equacoes/0006.json"
    lx = json.loads(j5.read_text())["fonte"]["latex"]
    largura_antes = json.loads(j5.read_text())["metricas"]["largura_pt"]
    r = editor.salvar(j5, lx, {"familia": "Times New Roman", "corpo": 12})
    assert r["ok"] and json.loads(j5.read_text())["ajustes"] == {"familia": "Times New Roman", "corpo": 12}
    assert r["metricas"]["largura_pt"] != largura_antes
    assert editor.abrir(j5)["ajustes"] == {"familia": "Times New Roman", "corpo": 12}
    # troca o livro inteiro para Arial 9: a 0006 muda, a 0005 continua Times 12
    pdf6 = j6.with_suffix(".pdf").read_bytes()
    atual = json.loads((tmp_path / "padrao.json").read_text())
    novo = tmp_path / "novo.json"
    novo.write_text(json.dumps({**aplicar(atual, "Arial", 9), "versao": 2}))
    rel = reestilizar(tmp_path, novo)
    assert rel["com_erro"] == [] and rel["refeitas"] == rel["equacoes"] == 45 and rel["ajustes_individuais"] == 1
    assert j6.with_suffix(".pdf").read_bytes() != pdf6
    assert json.loads(j6.read_text())["preset"].endswith("_v2")
    assert json.loads(j5.read_text())["metricas"]["largura_pt"] == pytest.approx(r["metricas"]["largura_pt"], abs=0.01)
    assert any(p.name.startswith("padrao-") for p in (tmp_path / "equacoes/.historico").iterdir())
    p = R.carregar_preset(tmp_path / "padrao.json")
    assert p["categorias"]["variavel"]["familia"] == "Arial" and p["tamanhos"]["completo"] == "9pt"

