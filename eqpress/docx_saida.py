"""F4 — .docx pronto: cada equação MathType vira imagem EMF inline com o ID no texto alternativo.

Specs: FORMATO_DOCX_OLE (ordem = EQ-NNNN, R-DOCX-03 w:position), INDESIGN ID-01 (docPr/@descr),
BL-01 (w:position arredondado a 0,5 pt), SPIKE S1 (EMF), S2, S3.
Equação com erro fica com o OLE original (nada se perde) e vai para o relatório.
"""
import posixpath
import zipfile

from lxml import etree

from .extrator import NS, PARTES, PROGID_EQUACAO, R, W

WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
TIPO_IMAGEM = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
EMU_POR_PT = 12700


def _el(ns, tag, pai=None, **at):
    el = etree.Element(f"{{{ns}}}{tag}") if pai is None else etree.SubElement(pai, f"{{{ns}}}{tag}")
    for k, v in at.items():
        el.set(k, str(v))
    return el


def _desenho(eq_id, rid, docpr_id, larg_pt, alt_pt):
    cx, cy = round(larg_pt * EMU_POR_PT), round(alt_pt * EMU_POR_PT)
    # prefixos usuais do Word (lxml inventaria ns0, ns1… se a raiz não os declarar)
    d = etree.Element(f"{{{W}}}drawing", nsmap={"wp": WP, "a": A, "pic": PIC})
    inl = _el(WP, "inline", d, distT=0, distB=0, distL=0, distR=0)
    _el(WP, "extent", inl, cx=cx, cy=cy)
    _el(WP, "effectExtent", inl, l=0, t=0, r=0, b=0)
    _el(WP, "docPr", inl, id=docpr_id, name=eq_id, descr=eq_id)  # ID-01
    _el(A, "graphicFrameLocks", _el(WP, "cNvGraphicFramePr", inl), noChangeAspect=1)
    gd = _el(A, "graphicData", _el(A, "graphic", inl), uri=PIC)
    pic = _el(PIC, "pic", gd)
    nv = _el(PIC, "nvPicPr", pic)
    _el(PIC, "cNvPr", nv, id=0, name=f"{eq_id}.emf")
    _el(PIC, "cNvPicPr", nv)
    bf = _el(PIC, "blipFill", pic)
    _el(A, "blip", bf).set(f"{{{R}}}embed", rid)
    _el(A, "fillRect", _el(A, "stretch", bf))
    sp = _el(PIC, "spPr", pic)
    xf = _el(A, "xfrm", sp)
    _el(A, "off", xf, x=0, y=0)
    _el(A, "ext", xf, cx=cx, cy=cy)
    _el(A, "avLst", _el(A, "prstGeom", sp, prst="rect"))
    return d


def _position(run, prof_pt):
    """BL-01: w:position em meios-pontos = profundidade arredondada a 0,5 pt (negativa = desce)."""
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        rpr = etree.Element(f"{{{W}}}rPr")
        run.insert(0, rpr)
    pos = rpr.find("w:position", NS)
    if pos is None:
        pos = etree.SubElement(rpr, f"{{{W}}}position")
    pos.set(f"{{{W}}}val", str(-round(prof_pt * 2)))


def gerar(docx_in, docx_out, saidas, manter_ole=False):
    """saidas: {EQ-NNNN: {"emf": Path, "metricas": {...}}} só das equações prontas.
    manter_ole=True: o objeto MathType continua no .docx (editável com o MathType) e só a prévia
    vira o EMF do EqPress. Serve para passar o arquivo adiante, NÃO para o InDesign: lá o ID se
    perde e a prévia de objeto OLE entra 2,83× menor (teste F5, INDESIGN §9).
    Devolve {"trocadas": [...], "mantidas": [...]} (mantidas = OLE original, com erro no lote)."""
    trocadas, mantidas = [], []
    with zipfile.ZipFile(docx_in) as zi:
        nomes = zi.namelist()
        partes = sorted((n for n in nomes if PARTES.match(n)), key=lambda n: (not n.endswith("document.xml"), n))
        novos, removidos, n_eq = {}, set(), 0
        # ids de docPr: os menores livres (os do Word podem ser enormes; o campo é inteiro)
        usados = {int(x) for n in partes for x in
                  etree.fromstring(zi.read(n)).xpath("//wp:docPr/@id", namespaces={"wp": WP})}
        livres = (i for i in range(1, 1 << 31) if i not in usados)
        for parte in partes:
            raiz = etree.fromstring(zi.read(parte))
            caminho_rels = posixpath.join(posixpath.dirname(parte), "_rels", posixpath.basename(parte) + ".rels")
            rels = etree.fromstring(zi.read(caminho_rels)) if caminho_rels in nomes else etree.Element(f"{{{REL}}}Relationships")
            por_id = {r.get("Id"): r for r in rels}
            mudou = False
            for obj in list(raiz.iter(f"{{{W}}}object")):
                ole = obj.find("o:OLEObject", NS)
                if ole is None or ole.get("ProgID") != PROGID_EQUACAO:
                    continue  # mesma regra do extrator: não conta como equação
                n_eq += 1
                eq_id = f"EQ-{n_eq:04d}"
                s = saidas.get(eq_id)
                if not s:
                    mantidas.append(eq_id)
                    continue
                # relação nova para a imagem; as do OLE e da prévia saem
                rid = f"rIdEqPress{n_eq}"
                destino = f"media/eqpress_{n_eq:04d}.emf"
                _el(REL, "Relationship", rels, Id=rid, Type=TIPO_IMAGEM, Target=destino)
                novos[posixpath.normpath(posixpath.join(posixpath.dirname(parte), destino))] = s["emf"].read_bytes()
                img = obj.find("v:shape/v:imagedata", NS)
                m = s["metricas"]
                if manter_ole and img is not None:
                    r_previa = img.get(f"{{{R}}}id")
                    if r_previa in por_id:
                        removidos.add(posixpath.normpath(posixpath.join(posixpath.dirname(parte), por_id[r_previa].get("Target"))))
                        rels.remove(por_id.pop(r_previa))
                    img.set(f"{{{R}}}id", rid)
                    img.set(f"{{{NS['o']}}}title", eq_id)
                    shape = img.getparent()
                    shape.set("alt", eq_id)
                    shape.set("style", f"width:{m['largura_pt']:.2f}pt;height:{m['altura_pt']:.2f}pt")
                    obj.set(f"{{{W}}}dxaOrig", str(round(m["largura_pt"] * 20)))
                    obj.set(f"{{{W}}}dyaOrig", str(round(m["altura_pt"] * 20)))
                    _position(obj.getparent(), m["profundidade_pt"])
                    trocadas.append(eq_id)
                    mudou = True
                    continue
                for r in (ole.get(f"{{{R}}}id"), img.get(f"{{{R}}}id") if img is not None else None):
                    if r in por_id:
                        removidos.add(posixpath.normpath(posixpath.join(posixpath.dirname(parte), por_id[r].get("Target"))))
                        rels.remove(por_id.pop(r))
                run = obj.getparent()
                run.replace(obj, _desenho(eq_id, rid, next(livres), m["largura_pt"], m["altura_pt"]))
                _position(run, m["profundidade_pt"])
                trocadas.append(eq_id)
                mudou = True
            if mudou:
                novos[parte] = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)
                novos[caminho_rels] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
        # arquivos de OLE/prévia que nenhuma outra relação usa mais
        ainda_usados = set()
        for n in nomes:
            if n.endswith(".rels") and n not in novos:
                base = posixpath.dirname(posixpath.dirname(n))
                for r in etree.fromstring(zi.read(n)):
                    if r.get("TargetMode") != "External":
                        ainda_usados.add(posixpath.normpath(posixpath.join(base, r.get("Target"))))
        for n, dados in novos.items():
            if n.endswith(".rels"):
                base = posixpath.dirname(posixpath.dirname(n))
                for r in etree.fromstring(dados):
                    ainda_usados.add(posixpath.normpath(posixpath.join(base, r.get("Target"))))
        removidos -= ainda_usados
        ct = etree.fromstring(zi.read("[Content_Types].xml"))
        if not any(d.get("Extension", "").lower() == "emf" for d in ct.iter(f"{{{CT}}}Default")):
            _el(CT, "Default", ct, Extension="emf", ContentType="image/x-emf")
        for o in list(ct.iter(f"{{{CT}}}Override")):
            if o.get("PartName", "").lstrip("/") in removidos:
                ct.remove(o)
        novos["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(docx_out, "w", zipfile.ZIP_DEFLATED) as zo:
            for item in zi.infolist():
                if item.filename in removidos:
                    continue
                zo.writestr(item, novos.pop(item.filename, None) or zi.read(item))
            for n, dados in novos.items():  # imagens novas
                zo.writestr(n, dados)
    return {"trocadas": trocadas, "mantidas": mantidas}
