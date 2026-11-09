"""Diagnóstico do computador (plano Windows, W3): ferramentas, fontes e um render de teste.
O colaborador copia o texto e manda; no CI ele responde se a Symbol do Windows funciona (risco 1).

    python -m eqpress diagnostico [--familia Arial]
"""
import json
import platform
import subprocess
import tempfile
from pathlib import Path

from . import plataforma as P
from . import renderizador as R

TESTE = r"x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}\Rightarrow v\rightarrow 2\cdot\alpha\le\Delta\rightleftharpoons"


def _versao(nome, *args):
    exe = P.ferramenta(nome)
    if not exe:
        return None
    r = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", **P.SEM_JANELA)
    return {"caminho": exe, "versao": (r.stdout or r.stderr).strip().splitlines()[0][:80] if (r.stdout or r.stderr) else ""}


def completo(familia, d):
    """PDF, EPS e EMF de verdade numa pasta temporária, com a conferência de cor (CA-06)."""
    from .padrao import criar
    p = criar(familia, 10)
    p["saida"] = {**p["saida"], "extras": ["eps", "emf"]}
    with tempfile.TemporaryDirectory(prefix="eqpress-diag-") as tmp:
        s = R.renderizar("EQ-0001", TESTE, p, tmp)
        d["completo"] = {"erro": s.erro, "metricas": s.metricas(),
                         "arquivos": {x.suffix: x.stat().st_size for x in Path(tmp).iterdir()},
                         "separacao": R.verificar_pdf(s.pdf, p) if s.pdf else None}
    return d["completo"]["erro"] is None and set(d["completo"]["arquivos"]) >= {".pdf", ".eps", ".emf"} \
        and not d["completo"]["separacao"]


def diagnostico(familia="Calibri"):
    d = {"sistema": f"{platform.system()} {platform.release()} {platform.machine()}",
         "ferramentas": {"tectonic": _versao("tectonic", "--version"), "ghostscript": _versao("gs", "--version"),
                         "inkscape": _versao("inkscape", "--version")},
         "pastas_fontes": [str(p) for p in P.PASTAS_FONTES if p.is_dir()]}
    idx = R.indice_fontes()
    fontes = {}
    for nome in (familia, "Calibri", "Arial", "Symbol", "STIX Two Math"):
        try:
            arq, n = R.arquivo_fonte(idx, nome)
            fontes[nome] = {"arquivo": arq, "symbol_windows_utilizavel": R._antiga(arq, n) if nome == "Symbol" else None}
        except R.ErroRender as e:
            fontes[nome] = {"erro": str(e)}
    d["fontes"] = fontes
    # render de teste com a fonte pedida: quais fontes o PDF usou (antes do contorno)
    try:
        from .padrao import criar
        p = criar(familia, 10)
        pre, avisos = R.preambulo(p)
        with tempfile.TemporaryDirectory(prefix="eqpress-diag-") as tmp:
            pdf, res = R._compilar(pre, [("EQ-0001", TESTE)], Path(tmp))
            import pikepdf
            with pikepdf.open(pdf) as doc:
                usadas = sorted({str(f.BaseFont).split("+")[-1] for f in doc.pages[0].Resources.Font.values()})
        d["render"] = {"ok": not res[0][4], "fontes_usadas": usadas, "faltando": res[0][4][:3]}
    except Exception as e:
        d["render"] = {"ok": False, "erro": f"{type(e).__name__}: {e}"}
    return d


if __name__ == "__main__":
    print(json.dumps(diagnostico(), ensure_ascii=False, indent=1))
