"""F1 — extrator: lista as equações MathType de um .docx.

Spec: spec/FORMATO_DOCX_OLE.md (R-DOCX-01..06, R-OLE-01). Uso:
    python -m eqpress.extrator arquivo.docx   # JSON no stdout
"""
import hashlib
import io
import json
import posixpath
import re
import struct
import sys
import zipfile
from dataclasses import asdict, dataclass, field

import olefile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {
    "w": W,
    "r": R,
    "o": "urn:schemas-microsoft-com:office:office",
    "v": "urn:schemas-microsoft-com:vml",
}
PROGID_EQUACAO = "Equation.DSMT4"  # R-DOCX-01
# R-DOCX-05: partes percorridas, nesta ordem (o corpo primeiro define EQ-0001…)
PARTES = re.compile(r"word/(document|footnotes|endnotes|header\d*|footer\d*)\.xml$")
# w:br e w:tab contam como espaço: parágrafo "quebra + equação" ainda é destacado (SPIKE:S0, 102/282)
CONTEUDO = {f"{{{W}}}{t}" for t in ("t", "sym", "drawing", "pict", "object")}


@dataclass
class Equacao:
    id: str
    parte: str
    local: str  # corpo | tabela | caixa_texto | nota | cabecalho | rodape; "+excluida" se em w:del
    paragrafo: int  # índice do w:p na parte
    destacada: bool  # R-DOCX-04: único conteúdo do parágrafo
    position_meio_pt: int | None  # R-DOCX-03
    largura_pt: float | None  # R-DOCX-02 (v:shape/@style)
    altura_pt: float | None
    dxa_orig: int | None
    dya_orig: int | None
    ole: str  # caminho no pacote
    previa: str | None
    mtef: bytes = field(repr=False)
    avisos: list[str] = field(default_factory=list)
    texto_antes: str = ""  # trecho do parágrafo antes/depois, para achar a equação no Word
    texto_depois: str = ""


@dataclass
class Extracao:
    arquivo: str
    equacoes: list[Equacao]
    outros_objetos: list[dict]  # w:object com outro ProgID ou sem OLE (R-DOCX-01)
    total_w_object: int


def _rels(z, parte):
    caminho = posixpath.join(posixpath.dirname(parte), "_rels", posixpath.basename(parte) + ".rels")
    if caminho not in z.namelist():
        return {}
    raiz = etree.fromstring(z.read(caminho))
    base = posixpath.dirname(parte)
    return {
        r.get("Id"): posixpath.normpath(posixpath.join(base, r.get("Target")))
        for r in raiz
        if r.get("TargetMode") != "External"
    }


def _local(obj, parte):
    nome = posixpath.basename(parte)
    local = (
        "nota" if nome.startswith(("footnotes", "endnotes"))
        else "cabecalho" if nome.startswith("header")
        else "rodape" if nome.startswith("footer")
        else "corpo"
    )
    tags = {etree.QName(a).localname for a in obj.iterancestors()}
    if "txbxContent" in tags:
        local = "caixa_texto"
    elif "tbl" in tags and local == "corpo":
        local = "tabela"
    if tags & {"del", "moveFrom"}:
        local += "+excluida"
    return local


def _destacada(obj, p):
    if p is None:
        return False
    return all(
        el is obj or (el.tag == f"{{{W}}}t" and not (el.text or "").strip())
        for el in p.iter(*CONTEUDO)
    )


def _contexto(obj, p, n=60):
    if p is None:
        return "", ""
    antes, depois = [], []
    lado = antes
    for el in p.iter(f"{{{W}}}t", f"{{{W}}}object"):
        if el is obj:
            lado = depois
        elif el.tag == f"{{{W}}}object":
            lado.append(" […] ")
        else:
            lado.append(el.text or "")
    antes, depois = "".join(antes).strip(), "".join(depois).strip()
    if not antes and not depois:  # equação destacada: usa o fim do parágrafo anterior com texto
        for q in p.itersiblings(f"{{{W}}}p", preceding=True):
            t = "".join(x.text or "" for x in q.iter(f"{{{W}}}t")).strip()
            if t:
                antes = t + " ¶"
                break
    if len(antes) > n:
        antes = "…" + antes[-n:].split(" ", 1)[-1]
    if len(depois) > n:
        depois = depois[:n].rsplit(" ", 1)[0] + "…"
    return antes, depois


def _mtef(dados):
    """R-OLE-01: devolve (mtef, avisos) a partir do oleObjectN.bin."""
    avisos = []
    ole = olefile.OleFileIO(io.BytesIO(dados))
    if not ole.exists("Equation Native"):
        return b"", ["sem stream 'Equation Native'"]
    s = ole.openstream("Equation Native").read()
    # cabeçalho: u16 tamanho, u32 versão, u16 formato, u32 tamanho do MTEF (offset 8)
    hdr_len = struct.unpack_from("<H", s, 0)[0]
    tam = struct.unpack_from("<I", s, 8)[0]
    if tam != len(s) - hdr_len:
        avisos.append(f"tamanho MTEF no cabeçalho ({tam}) ≠ stream − cabeçalho ({len(s) - hdr_len})")
    return s[hdr_len:], avisos


PT_POR = {"pt": 1, "in": 72, "cm": 72 / 2.54, "mm": 72 / 25.4, "pc": 12, "px": 0.75}


def _pt(style, chave):
    """Valor CSS do v:shape/@style em pt (o Word grava pt ou in, R-DOCX-02)."""
    m = re.search(rf"(?:^|;)\s*{chave}:\s*([\d.]+)(pt|in|cm|mm|pc|px)", style or "")
    return round(float(m.group(1)) * PT_POR[m.group(2)], 3) if m else None


def _int(v):
    return int(v) if v is not None else None


def extrair(caminho):
    equacoes, outros, total = [], [], 0
    with zipfile.ZipFile(caminho) as z:
        partes = sorted(
            (n for n in z.namelist() if PARTES.match(n)),
            key=lambda n: (not n.endswith("document.xml"), n),
        )
        for parte in partes:
            raiz = etree.fromstring(z.read(parte))
            rels = _rels(z, parte)
            paragrafos = {p: i for i, p in enumerate(raiz.iter(f"{{{W}}}p"))}
            for obj in raiz.iter(f"{{{W}}}object"):
                total += 1
                ole_el = obj.find("o:OLEObject", NS)
                progid = ole_el.get("ProgID") if ole_el is not None else None
                p = next(obj.iterancestors(f"{{{W}}}p"), None)
                if progid != PROGID_EQUACAO:
                    outros.append({"parte": parte, "paragrafo": paragrafos.get(p), "progid": progid})
                    continue
                ole = rels.get(ole_el.get(f"{{{R}}}id"))
                shape = obj.find("v:shape", NS)
                img = shape.find("v:imagedata", NS) if shape is not None else None
                pos = obj.getparent().find("w:rPr/w:position", NS)
                avisos = []
                if ole is None or ole not in z.namelist():
                    mtef, avisos = b"", [f"OLE não encontrado: {ole}"]
                else:
                    mtef, avisos = _mtef(z.read(ole))
                style = shape.get("style") if shape is not None else None
                antes, depois = _contexto(obj, p)
                equacoes.append(Equacao(
                    id=f"EQ-{len(equacoes) + 1:04d}",
                    parte=parte,
                    local=_local(obj, parte),
                    paragrafo=paragrafos.get(p),
                    destacada=_destacada(obj, p),
                    position_meio_pt=_int(pos.get(f"{{{W}}}val")) if pos is not None else None,
                    largura_pt=_pt(style, "width"),
                    altura_pt=_pt(style, "height"),
                    dxa_orig=_int(obj.get(f"{{{W}}}dxaOrig")),
                    dya_orig=_int(obj.get(f"{{{W}}}dyaOrig")),
                    ole=ole,
                    previa=rels.get(img.get(f"{{{R}}}id")) if img is not None else None,
                    mtef=mtef,
                    avisos=avisos,
                    texto_antes=antes,
                    texto_depois=depois,
                ))
    return Extracao(str(caminho), equacoes, outros, total)


def para_json(ex):
    d = asdict(ex)
    for e, orig in zip(d["equacoes"], ex.equacoes):
        e.pop("mtef")
        e["mtef_bytes"] = len(orig.mtef)
        e["mtef_sha256"] = hashlib.sha256(orig.mtef).hexdigest()
    return d


if __name__ == "__main__":
    for arq in sys.argv[1:]:
        print(json.dumps(para_json(extrair(arq)), ensure_ascii=False, indent=1))
