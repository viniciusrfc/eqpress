"""Lote: .docx → equacoes/NNNN.{json,pdf[,eps,emf]} + relatorio.json (F1+F2+F3).

JSON da equação: EDITOR §2. Relatório: CA-01 (contagens) e CA-13 (nada some em silêncio).
"""
import hashlib
import json
import shutil
from pathlib import Path

from . import renderizador as R
from .conversor import converter
from .docx_saida import gerar as gerar_docx
from .extrator import extrair


def _json(caminho, dados):
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def estilizar(docx, preset_path, pasta):
    """Converte e renderiza todas as equações do .docx. Devolve o relatório (também gravado)."""
    docx, pasta = Path(docx), Path(pasta)
    p = R.carregar_preset(preset_path)
    if p["saida"].get("imagem_docx", "emf") != "emf":
        raise R.ErroRender("saida.imagem_docx: só 'emf' está implementado (SPIKE S1)")
    # a imagem do .docx é o EMF (F4), mesmo que o preset não peça EMF como extra
    p = {**p, "saida": {**p["saida"], "extras": sorted(set(p["saida"].get("extras", [])) | {"emf"})}}
    ref_preset = f"{p['nome']}_v{p['versao']}"
    pasta.mkdir(parents=True, exist_ok=True)
    if Path(preset_path).resolve() != (pasta / "padrao.json").resolve():
        shutil.copy(preset_path, pasta / "padrao.json")
    destino = pasta / "equacoes"
    destino.mkdir(parents=True, exist_ok=True)
    ex = extrair(docx)
    conv = {e.id: converter(e.mtef) for e in ex.equacoes}
    itens = [(i, c.latex) for i, c in conv.items() if c.erro is None]
    saidas, avisos_preset = R.renderizar_lote(itens, p, destino)
    por_id = {s.id: s for s in saidas}
    linhas = []
    for e in ex.equacoes:
        c, s = conv[e.id], por_id.get(e.id)
        erro = c.erro and f"não suportada: {c.erro}" or (s.erro if s else None)
        reg = {
            "id": e.id,
            "fonte": {"latex": c.latex, "mathml": c.mathml},
            "origem": {"docx": docx.name, "ole": e.ole, "mtef_sha1": hashlib.sha1(e.mtef).hexdigest()},
            "preset": ref_preset,
            "preset_sha1": R.sha1_preset(p),
            "metricas": s.metricas() if s and s.pdf else None,
            "destacada": e.destacada,
            "avisos": c.avisos + (s.avisos if s else []),
            "erro": erro,
        }
        _json(destino / f"{e.id.removeprefix('EQ-')}.json", reg)
        linhas.append({k: reg[k] for k in ("id", "avisos", "erro")})
    pdfs = sorted(destino.glob("*.pdf"))
    docx_out = pasta / f"{docx.stem}_EqPress.docx"
    prontas = {s.id: {"emf": s.extras["emf"], "metricas": s.metricas()} for s in saidas if s.pdf}
    troca = gerar_docx(docx, docx_out, prontas)
    # cópia editável: objetos MathType mantidos, só a aparência nova (para passar adiante)
    docx_editavel = pasta / f"{docx.stem}_EqPress_editavel.docx"
    gerar_docx(docx, docx_editavel, prontas, manter_ole=True)
    rel = {
        "docx": docx.name,
        "preset": ref_preset,
        "w_object_total": ex.total_w_object,
        "equacoes": len(ex.equacoes),
        "outros_objetos": ex.outros_objetos,
        "pdfs": len(pdfs),
        "docx_saida": docx_out.name,
        "docx_editavel": docx_editavel.name,
        "imagens_no_docx": len(troca["trocadas"]),
        "ole_mantidos": troca["mantidas"],
        "com_erro": [x for x in linhas if x["erro"]],
        "com_aviso": [x for x in linhas if x["avisos"] and not x["erro"]],
        "avisos_preset": avisos_preset,
    }
    # CA-01: toda equação de entrada tem PDF, ou aparece em com_erro
    rel["divergencias"] = (ex.total_w_object - len(pdfs) - len(rel["com_erro"]) - len(ex.outros_objetos)
                           + abs(len(pdfs) - len(troca["trocadas"])))
    rel["status"] = "ok" if not rel["com_erro"] and not rel["divergencias"] else "com divergências"
    _json(pasta / "relatorio.json", rel)
    return rel


def renderizar_json(json_path, preset_path):
    """`eqpress renderizar NNNN.json` (EDITOR ED-21): regrava o PDF ao lado e atualiza as métricas."""
    json_path = Path(json_path)
    reg = json.loads(json_path.read_text(encoding="utf-8"))
    p = R.carregar_preset(preset_path)
    s = R.renderizar(reg["id"], reg["fonte"]["latex"], p, json_path.parent)
    reg.update(preset=f"{p['nome']}_v{p['versao']}", preset_sha1=R.sha1_preset(p),
               metricas=s.metricas() if s.pdf else None, erro=s.erro)
    _json(json_path, reg)
    return s


def reestilizar(pasta, preset_novo):
    """Troca o padrão de um livro já montado (INDESIGN §6, F7): refaz todas as equações da pasta
    no lugar, a partir do LaTeX de cada JSON (com as edições e os ajustes individuais). No InDesign
    basta rodar "Vincular e alinhar": os vínculos são atualizados e a baseline é refeita."""
    import datetime
    import os
    import tempfile

    from . import padrao as PADRAO

    pasta = Path(pasta)
    eqdir = pasta / "equacoes"
    novo = R.carregar_preset(preset_novo)
    novo = {**novo, "saida": {**novo["saida"], "extras": sorted(set(novo["saida"].get("extras", [])) | {"emf"})}}
    hist = eqdir / ".historico"
    hist.mkdir(exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if (pasta / "padrao.json").exists():
        shutil.copy2(pasta / "padrao.json", hist / f"padrao-{carimbo}.json")  # O3: nada se perde
    if Path(preset_novo).resolve() != (pasta / "padrao.json").resolve():
        shutil.copy(preset_novo, pasta / "padrao.json")
    regs = {}
    for j in sorted(eqdir.glob("*.json")):
        reg = json.loads(j.read_text(encoding="utf-8"))
        if reg.get("fonte", {}).get("latex"):
            regs[j] = reg
    # equações com o mesmo ajuste individual são renderizadas juntas (um lote por ajuste)
    grupos = {}
    for j, reg in regs.items():
        grupos.setdefault(json.dumps(reg.get("ajustes") or {}, sort_keys=True), []).append(j)
    ref = f"{novo['nome']}_v{novo['versao']}"
    erros, avisos_preset = [], []
    for chave, js in grupos.items():
        a = json.loads(chave)
        p = PADRAO.aplicar(novo, a.get("familia"), a.get("corpo"), a.get("italico")) if a else novo
        with tempfile.TemporaryDirectory(prefix="eqpress-reest-", dir=eqdir) as tmp:
            saidas, av = R.renderizar_lote([(regs[j]["id"], regs[j]["fonte"]["latex"]) for j in js], p, tmp)
            avisos_preset = avisos_preset or av
            for j, s in zip(js, saidas):
                reg = regs[j]
                if s.erro:
                    erros.append({"id": reg["id"], "erro": s.erro})  # fica o PDF anterior
                    continue
                for arq in Path(tmp).glob(f"{j.stem}.*"):  # troca atômica (ED-22)
                    os.replace(arq, eqdir / arq.name)
                reg.update(metricas=s.metricas(), preset=ref, preset_sha1=R.sha1_preset(p), avisos=s.avisos, erro=None)
                _json(j, reg)
    rel = {"pasta": str(pasta), "preset": ref, "equacoes": len(regs), "refeitas": len(regs) - len(erros),
           "com_erro": erros, "avisos_preset": avisos_preset,
           "ajustes_individuais": sum(len(js) for k, js in grupos.items() if k != "{}")}
    _json(pasta / "relatorio_reestilizar.json", rel)
    return rel
