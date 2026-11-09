"""Página de conferência (O5 simplificado): cada equação nova dentro da frase onde ela está no Word,
alinhada pela baseline calculada, com links para PDF/EPS/EMF e os problemas em destaque."""
import html
import json
import subprocess
from pathlib import Path

from . import renderizador as R
from .extrator import extrair

ZOOM = 1.6  # tamanho na tela em relação ao impresso
DPI = 300


def _png(pdfs, pasta):
    """Uma chamada do Ghostscript para todos os PDFs: png/0001.png, 0002.png… na mesma ordem."""
    pasta.mkdir(exist_ok=True)
    if pdfs:
        subprocess.run([R._exe("gs"), "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pngalpha", f"-r{DPI}",
                        f"-sOutputFile={pasta}/%04d.png", *map(str, pdfs)], check=True, **R.P.SEM_JANELA)
    return {pdf.stem: f"png/{k + 1:04d}.png" for k, pdf in enumerate(pdfs)}


def gerar(docx, pasta, rel):
    pasta = Path(pasta)
    eqs = extrair(docx).equacoes
    regs = {e.id: json.loads((pasta / "equacoes" / f"{e.id[3:]}.json").read_text(encoding="utf-8")) for e in eqs}
    pdfs = [pasta / "equacoes" / f"{e.id[3:]}.pdf" for e in eqs if (pasta / "equacoes" / f"{e.id[3:]}.pdf").exists()]
    pngs = _png(pdfs, pasta / "png")
    linhas = []
    for e in eqs:
        r, n = regs[e.id], e.id[3:]
        if r["erro"]:
            eq = f'<span class="erro">⚠ {html.escape(r["erro"])}</span>'
        else:
            m = r["metricas"]
            eq = (f'<img src="{pngs[n]}" alt="{e.id}" style="width:{m["largura_pt"] * ZOOM:.1f}pt;'
                  f'height:{m["altura_pt"] * ZOOM:.1f}pt;vertical-align:-{m["profundidade_pt"] * ZOOM:.1f}pt">')
        arquivos = " ".join(f'<a href="equacoes/{n}.{x}">{x.upper()}</a>'
                            for x in ("pdf", "eps", "emf") if (pasta / "equacoes" / f"{n}.{x}").exists())
        avisos = "".join(f'<div class="aviso">{html.escape(a)}</div>' for a in r["avisos"])
        frase = f'{html.escape(e.texto_antes)} {eq} {html.escape(e.texto_depois)}'
        linhas.append(f'<tr class="{"ruim" if r["erro"] else ""}"><td class="n">{e.id}</td>'
                      f'<td class="frase">{"<br>" if e.destacada else ""}{frase}{avisos}</td>'
                      f'<td class="arq">{arquivos}</td></tr>')
    ok = rel["pdfs"]
    ruins = len(rel["com_erro"])
    resumo = (f"Padrão: <b>{html.escape(rel['preset'])}</b> · <b>{rel['equacoes']}</b> equações no Word · <b>{ok}</b> prontas"
              + (f' · <b class="erro">{ruins} com problema</b>' if ruins else " · nenhum problema"))
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>EqPress — {html.escape(Path(docx).name)}</title>
<style>
:root {{ color-scheme: light; }}
body {{ font: 15px/1.6 -apple-system, sans-serif; margin: 24px; background: #fff; color: #222; }}
h1 {{ font-size: 20px; margin: 0 0 4px; }}
.resumo {{ margin: 0 0 18px; color: #444; }}
table {{ border-collapse: collapse; width: 100%; }}
td {{ border-bottom: 1px solid #e5e5e5; padding: 10px 8px; vertical-align: middle; }}
td.n {{ color: #888; font-size: 12px; white-space: nowrap; }}
td.frase {{ font-family: Calibri, sans-serif; font-size: {10 * ZOOM:g}pt; line-height: 2.2; }}
td.arq a {{ font-size: 12px; margin-right: 6px; }}
tr.ruim {{ background: #fff3f3; }}
.erro {{ color: #b00020; }}
a.word {{ display: inline-block; margin: 8px 0; padding: 6px 12px; background: #1a5fb4; color: #fff;
  border-radius: 6px; text-decoration: none; font-weight: 600; }}
a.word.editavel {{ background: #2e7d32; margin-left: 8px; }}
.aviso {{ font: 12px -apple-system, sans-serif; color: #8a6d00; }}
img {{ background: #fffbe0; }}
</style></head><body>
<h1>{html.escape(Path(docx).name)}</h1>
<p class="resumo">{resumo}<br>
<a class="word" href="{html.escape(rel.get('docx_saida', ''))}">Word para o InDesign</a>
<a class="word editavel" href="{html.escape(rel.get('docx_editavel', ''))}">Word editável (MathType)</a><br>Cada equação aparece na frase em que está no Word (fundo amarelo = área da
imagem). Clique em PDF/EPS/EMF para abrir o arquivo.</p>
<table>{"".join(linhas)}</table></body></html>"""
    destino = pasta / "conferir.html"
    destino.write_text(pagina, encoding="utf-8")
    return destino
