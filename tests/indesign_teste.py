"""Teste de ponta a ponta no InDesign (manual: abre o InDesign; fora do pytest).

    .venv/bin/python tests/indesign_teste.py samples/X.docx [--app "Adobe InDesign 2024"]

Gera o _EqPress (Arial 10), cria um documento novo no InDesign, insere o .docx, roda
"Vincular e alinhar", mede a baseline (CA-04) e exporta PDF/X-1a para conferir as chapas (CA-06/07).
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from eqpress import padrao  # noqa: E402
from eqpress import renderizador as R  # noqa: E402
from eqpress.lote import estilizar  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--app", default="Adobe InDesign 2024")
    ap.add_argument("--familia", default="Arial")
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="eqpress-indd-"))
    docx = tmp / Path(args.docx).name
    shutil.copy(args.docx, docx)
    pasta = tmp / f"{docx.stem}_EqPress"
    pasta.mkdir()
    preset = pasta / "padrao.json"
    preset.write_text(json.dumps(padrao.criar(args.familia, 10)))
    rel = estilizar(docx, preset, pasta)
    T = {"docx": str(pasta / rel["docx_saida"]), "pasta": str(pasta / "equacoes"),
         "script": str(RAIZ / "indesign/EqPress - Vincular e alinhar equações.jsx"),
         "saida_pdf": str(tmp / "indesign.pdf"), "saida_json": str(tmp / "indesign.json")}
    js = f"$.global.EQPRESS_TESTE = {json.dumps(T)}; $.evalFile(File({json.dumps(str(RAIZ / 'indesign/teste_automatico.jsx'))}));"
    osa = f'with timeout of 900 seconds\ntell application "{args.app}" to do script {json.dumps(js)} language javascript\nend timeout'
    r = subprocess.run(["osascript", "-e", osa], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"InDesign: {r.stderr}")
    res = json.loads(Path(T["saida_json"]).read_text())
    med = res["medidas"]
    desvios = [abs(m["desvio"]) for m in med if not m["sozinha"]]
    sozinhas = [m for m in med if m["sozinha"]]
    print(f"pasta: {tmp}")
    print(f"gráficos no documento: {res['graficos_antes']} → tipos depois: {res['tipos']}")
    print(f"vinculadas: {res['vinculadas']}  erros: {res['erros']}  sem PDF: {res['faltando']}")
    print(f"equações medidas: {len(med)} de {rel['equacoes']} · PDF: {sum(m['tipo'] == 'PDF' for m in med)}")
    print(f"no meio do texto: {len(desvios)} · desvio de baseline máx {max(desvios):.4f} pt · acima de 0,1 pt: {sum(d > 0.1 for d in desvios)}")
    print(f"sozinhas na linha (apoiadas na própria baseline): {len(sozinhas)}")
    chapas = R.cobertura_chapas(T["saida_pdf"])
    print(f"chapas do PDF exportado (pixels com tinta): {chapas}")


if __name__ == "__main__":
    main()
