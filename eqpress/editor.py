"""Núcleo do editor (F6): prévia real e salvar, chamados pelo app Tauri por um processo que fica
aberto (`python -m eqpress servidor`: uma linha JSON por pedido, uma por resposta).

Spec: EDITOR §2 (NNNN.json), ED-04 (LaTeX portátil), ED-11 (prévia = render real), ED-15 (confere
a separação ao salvar), ED-16 (histórico), ED-21 (mesmo núcleo do lote), ED-22 (troca atômica),
CA-E2 (abrir e salvar sem mudar não altera o PDF).
"""
import base64
import datetime
import functools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import VERSAO
from . import biblioteca as BIB
from . import padrao as PADRAO
from . import plataforma as P
from . import renderizador as R

VERIFICAR = P.RECURSOS / "ferramentas/web/verificar.js"


def preset_da_equacao(json_path):
    """O lote grava o padrão usado em <pasta _EqPress>/padrao.json, ao lado de equacoes/."""
    p = Path(json_path).resolve().parent.parent / "padrao.json"
    if not p.exists():
        raise R.ErroRender(f"padrão do livro não encontrado: {p}")
    return p


@functools.lru_cache(maxsize=8)
def _preset(caminho, mtime):
    return R.carregar_preset(caminho)


def _carregar(caminho):
    caminho = Path(caminho)
    return _preset(str(caminho), caminho.stat().st_mtime)


def _limpar(ajustes):
    """Ajuste de uma equação só: {"familia", "corpo", "italico"}; campos vazios saem."""
    return {k: v for k, v in (ajustes or {}).items() if v is not None and v != ""}


def efetivo(preset, ajustes=None):
    """Padrão do livro + o ajuste desta equação (se houver)."""
    p = _carregar(preset)
    a = _limpar(ajustes)
    return PADRAO.aplicar(p, a.get("familia"), a.get("corpo"), a.get("italico")) if a else p


def portavel(latex):
    """ED-04: (erro ou None, MathML). Sem node/KaTeX/MathJax instalados: (None, None) com o
    teste pulado — o render real continua sendo a prova principal."""
    if not shutil.which("node") or not (VERIFICAR.parent / "node_modules/katex").exists():
        return None, None
    r = subprocess.run(["node", str(VERIFICAR)], input=json.dumps([latex]), capture_output=True, text=True, encoding="utf-8", errors="replace")
    (res,) = json.loads(r.stdout)
    erro = res["katex"] or res["mathjax"]
    return (f"fora do LaTeX portátil (KaTeX/MathJax): {erro[:200]}" if erro else None), res["mathml"]


def _png(pdf):
    r = subprocess.run([R._exe("gs"), "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pngalpha", "-r400",
                        "-sOutputFile=-", str(pdf)], capture_output=True, check=True, **P.SEM_JANELA)
    return "data:image/png;base64," + base64.b64encode(r.stdout).decode()


def previa(latex, preset, ajustes=None):
    """Render real com o padrão do livro (+ ajuste) → PNG (data URI) + métricas. Não grava nada."""
    p = {**efetivo(preset, ajustes)}
    p["saida"] = {**p["saida"], "extras": []}
    with tempfile.TemporaryDirectory(prefix="eqpress-previa-") as tmp:
        s = R.renderizar("EQ-0000", latex, p, tmp)
        if s.erro:
            return {"erro": s.erro}
        return {"png": _png(s.pdf), "metricas": s.metricas(), "avisos": s.avisos}


def abrir(json_path):
    reg = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return {"id": reg["id"], "latex": reg["fonte"]["latex"], "preset": str(preset_da_equacao(json_path)),
            "preset_nome": reg.get("preset"), "metricas": reg.get("metricas"),
            "ajustes": reg.get("ajustes") or {},
            "cor": _carregar(preset_da_equacao(json_path))["cores"]["padrao"],
            "padrao_livro": _resumo(_carregar(preset_da_equacao(json_path)))}


def _resumo(p):
    """Fonte e corpo do padrão do livro, para o editor mostrar o que vale sem ajuste."""
    v = p["categorias"]["variavel"]
    return {"familia": v["familia"], "corpo": float(p["tamanhos"]["completo"][:-2]),
            "italico": bool(v.get("italico", False))}


def salvar(json_path, latex, ajustes=None, mathml=None):
    """mathml: vem do app, que já conferiu o LaTeX no KaTeX/MathJax; sem ele, confere pelo node."""
    json_path = Path(json_path).resolve()
    reg = json.loads(json_path.read_text(encoding="utf-8"))
    ajustes = _limpar(ajustes)
    if latex == reg["fonte"]["latex"] and ajustes == (reg.get("ajustes") or {}) \
            and json_path.with_suffix(".pdf").exists():
        return {"ok": True, "sem_mudancas": True}  # CA-E2: o PDF não é tocado
    if mathml is None:
        erro, mathml = portavel(latex)
        if erro:
            return {"erro": erro}
    preset = preset_da_equacao(json_path)
    p = efetivo(preset, ajustes)
    n = json_path.stem
    with tempfile.TemporaryDirectory(prefix="eqpress-salvar-", dir=json_path.parent) as tmp:
        s = R.renderizar(reg["id"], latex, p, tmp)
        if s.erro:
            return {"erro": s.erro}
        erros = R.verificar_pdf(s.pdf, p)  # ED-15: separação antes de gravar
        if erros:
            return {"erro": "separação: " + "; ".join(erros)}
        hist = json_path.parent / ".historico"
        hist.mkdir(exist_ok=True)
        carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        for ext in ("json", "pdf", "eps", "emf"):
            antigo = json_path.with_suffix("." + ext)
            if antigo.exists():
                shutil.copy2(antigo, hist / f"{n}-{carimbo}.{ext}")
        for arq in Path(tmp).iterdir():  # ED-22: troca atômica no mesmo volume
            os.replace(arq, json_path.parent / f"{n}{arq.suffix}")
    reg["fonte"] = {"latex": latex, "mathml": mathml}
    if ajustes:
        reg["ajustes"] = ajustes
    else:
        reg.pop("ajustes", None)
    reg["metricas"] = s.metricas()
    reg["avisos"] = s.avisos
    reg["erro"] = None
    reg["editado_em"] = datetime.datetime.now().isoformat(timespec="seconds")
    json_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"ok": True, "metricas": s.metricas()}


def preparar(docx, padrao_arquivo):
    """Tela Início › Preparar um Word: o mesmo que o Testar EqPress.command."""
    from .lote import estilizar
    from .prova import gerar
    docx = Path(docx)
    pasta = docx.with_name(docx.stem + "_EqPress")
    rel = estilizar(docx, padrao_arquivo, pasta)
    pagina = gerar(docx, pasta, rel)
    return {"pasta": str(pasta), "conferir": str(pagina), "word": str(pasta / rel["docx_saida"]),
            "editavel": str(pasta / rel["docx_editavel"]), "equacoes": rel["equacoes"], "pdfs": rel["pdfs"],
            "com_erro": rel["com_erro"], "status": rel["status"]}


def trocar(pasta, padrao_arquivo):
    """Tela Início › Trocar o padrão de um livro (reestilizar)."""
    from .lote import reestilizar
    pasta = Path(pasta)
    if pasta.name == "equacoes":
        pasta = pasta.parent
    if not (pasta / "equacoes").is_dir():
        return {"erro": "Escolha a pasta _EqPress do livro (a que tem a pasta equacoes dentro)."}
    return reestilizar(pasta, padrao_arquivo)


def atender(q):
    """Um pedido do app ({"cmd": …}) → resposta; erro vira {"erro": …}, nunca exceção."""
    try:
        if q["cmd"] == "previa":
            r = previa(q["latex"], q["preset"], q.get("ajustes"))
        elif q["cmd"] == "familias":
            r = {"familias": PADRAO.familias()}
        elif q["cmd"] == "padroes":
            r = {"padroes": BIB.listar()}
        elif q["cmd"] == "padrao_salvar":
            r = BIB.salvar(q["campos"], q.get("base"))
        elif q["cmd"] == "padrao_importar":
            r = BIB.importar(q["origem"])
        elif q["cmd"] == "padrao_exportar":
            r = BIB.exportar(q["arquivo"], q["destino"])
        elif q["cmd"] == "padrao_prova":
            base = R.carregar_preset(q["base"]) if q.get("base") else None
            p = BIB.montar(q["campos"], base)
            p["saida"]["extras"] = []
            with tempfile.TemporaryDirectory(prefix="eqpress-padrao-") as tmp:
                s = R.renderizar("EQ-0000", BIB.AMOSTRA, p, tmp)
                r = {"erro": s.erro} if s.erro else {"png": _png(s.pdf), "metricas": s.metricas()}
        elif q["cmd"] == "diagnostico":
            from .diagnostico import completo, diagnostico
            d = diagnostico(q.get("familia") or "Calibri")
            d["tudo_ok"] = bool(d["render"].get("ok") and completo(q.get("familia") or "Calibri", d))
            d["versao"] = VERSAO
            d["registro"] = REGISTRO.read_text(encoding="utf-8").splitlines()[-40:] if REGISTRO.exists() else []
            r = d
        elif q["cmd"] == "instalar_scripts":
            r = instalar_scripts()
        elif q["cmd"] == "preparar":
            r = preparar(q["docx"], q["padrao"])
        elif q["cmd"] == "trocar":
            r = trocar(q["pasta"], q["padrao"])
        elif q["cmd"] == "mostrar":  # abre no app padrão do Mac (ou revela no Finder)
            (P.mostrar if q.get("finder") else P.abrir)(q["caminho"])
            r = {"ok": True}
        elif q["cmd"] == "abrir":
            r = abrir(q["json"])
        elif q["cmd"] == "salvar":
            r = salvar(q["json"], q["latex"], q.get("ajustes"), q.get("mathml"))
        else:
            r = {"erro": f"comando desconhecido: {q['cmd']}"}
    except R.ErroRender as e:
        r = {"erro": str(e)}
    except Exception as e:  # o app mostra o erro; o processo continua vivo
        r = {"erro": f"{type(e).__name__}: {e}"}
    return r


def instalar_scripts():
    """Copia os scripts do EqPress para o painel Scripts de cada InDesign instalado (Usuário)."""
    import shutil
    scripts = sorted((P.RECURSOS / "indesign").glob("EqPress - *.jsx"))
    pastas = P.pastas_scripts_indesign()
    if not pastas:
        return {"erro": "Não achei o InDesign neste computador. Abra o InDesign uma vez e tente de novo."}
    for pasta in pastas:
        for s in scripts:
            shutil.copy(s, pasta / s.name)
    versoes = sorted({p.parts[-4] for p in pastas})  # "Version 19.0"…
    return {"ok": True, "versoes": versoes, "scripts": [s.stem for s in scripts]}


REGISTRO = P.CACHE / "registro.txt"


def servidor():
    """Laço do app: uma linha JSON por pedido, uma por resposta. Sempre UTF-8: no Windows o padrão
    do pipe é cp1252 e qualquer acento ("Padrões", "equações.jsx") derrubava a conversa."""
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    P.CACHE.mkdir(parents=True, exist_ok=True)
    for linha in sys.stdin:
        t = time.time()
        q = json.loads(linha)
        r = atender(q)
        sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
        sys.stdout.flush()
        # registro para o diagnóstico (o colaborador manda; daqui não vemos o PC dele)
        with REGISTRO.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%d/%m %H:%M:%S')} {q.get('cmd')} {time.time() - t:.1f}s {str(r.get('erro', 'ok')).replace(chr(10), ' ')}\n")
