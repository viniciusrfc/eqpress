"""SPIKES S1–S5 (descartável) — gera os arquivos de teste para o usuário importar no InDesign.

Pipeline de protótipo: LaTeX (tectonic/XeTeX) → PDF → cores normalizadas (pikepdf)
→ EMF/WMF/SVG (Inkscape) e PNG (Ghostscript) → .docx de teste montados à mão (OOXML).
Uso: .venv/bin/python spikes/s1_s5_gerar/gerar.py   (saída em spikes/out/testes/)
"""
import json, re, shutil, subprocess, zipfile
from pathlib import Path
import pikepdf

OUT = Path(__file__).resolve().parents[1] / 'out' / 'testes'
REND = OUT / 'render'
EQS = {  # id -> LaTeX (equações representativas do corpus: fração, raiz, sobrescrito, frações em linha)
    'EQ-0001': r'x=\dfrac{-b\pm\sqrt{b^{2}-4ac}}{2a}',
    'EQ-0002': r'\tfrac{3}{4}',
    'EQ-0003': r'v_{0}=12\ \mathrm{m/s}',
}
TEX = r'''\documentclass[border=0pt]{standalone}
\usepackage{xcolor}\usepackage{unicode-math}
\newsavebox\eq
\begin{document}\sbox\eq{\color[cmyk]{0,0,0,1}$%s$}%%
\typeout{EQMET \the\wd\eq\space\the\ht\eq\space\the\dp\eq}\usebox\eq\end{document}'''

COR = {  # variante S5 -> operadores de preenchimento/traço
    'k100': ('0 0 0 1 k', '0 0 0 1 K'),
    'gray': ('0 g', '0 G'),
    'rgb': ('0 0 0 rg', '0 0 0 RG'),
}
COLOR_OPS = {'g', 'G', 'rg', 'RG', 'k', 'K', 'cs', 'CS', 'sc', 'SC', 'scn', 'SCN'}


def sh(*a):
    subprocess.run(a, check=True, capture_output=True)


def normalizar_cor(src, dst, cor, overprint):
    """Troca TODO operador de cor por um único modelo; opcionalmente liga overprint via ExtGState."""
    fill, stroke = COR[cor]
    pdf = pikepdf.open(src)
    pg = pdf.pages[0]
    novo = []
    if overprint:
        if '/ExtGState' not in pg.Resources: pg.Resources.ExtGState = pikepdf.Dictionary()
        pg.Resources.ExtGState['/GSop'] = pikepdf.Dictionary(Type=pikepdf.Name.ExtGState, OP=True, op=True, OPM=1)
        novo.append(([pikepdf.Name('/GSop')], pikepdf.Operator('gs')))
    for operands, op in pikepdf.parse_content_stream(pg):
        if str(op) in COLOR_OPS:
            continue
        novo.append((operands, op))
    # cor única definida no início e reafirmada após cada 'Q' (restore volta ao estado salvo, que já tem a cor)
    head = pikepdf.parse_content_stream(pikepdf.Stream(pdf, f'{fill} {stroke}'.encode()))
    pg.Contents = pdf.make_stream(pikepdf.unparse_content_stream(list(head) + novo))
    pdf.save(dst)


def render():
    REND.mkdir(parents=True, exist_ok=True)
    met = {}
    for eid, tex in EQS.items():
        base = REND / eid
        base.with_suffix('.tex').write_text(TEX % tex)
        sh('tectonic', '-X', 'compile', '--keep-logs', '--outdir', str(REND), str(base.with_suffix('.tex')))
        w, h, dp = (float(x[:-2]) * 72 / 72.27 for x in re.search(r'EQMET (\S+) (\S+) (\S+)', base.with_suffix('.log').read_text()).groups())
        raw = base.with_suffix('.pdf')
        for cor in COR:
            for op in (False, True):
                if cor != 'k100' and op: continue
                normalizar_cor(raw, REND / f'{eid}_{cor}{"_op" if op else ""}.pdf', cor, op)
        k = REND / f'{eid}_k100.pdf'
        # contorno das fontes (necessário para EMF/WMF/SVG não dependerem de fonte instalada)
        sh('gs', '-q', '-o', str(REND / f'{eid}_k100_outl.pdf'), '-sDEVICE=pdfwrite', '-dNoOutputFonts',
           '-sColorConversionStrategy=LeaveColorUnchanged', str(k))
        o = REND / f'{eid}_k100_outl.pdf'
        for ext in ('emf', 'wmf', 'svg'):
            sh('inkscape', str(o), f'--export-filename={REND / f"{eid}.{ext}"}')
        sh('gs', '-q', '-o', str(REND / f'{eid}.png'), '-sDEVICE=pngalpha', '-r1200', str(k))
        sh('gs', '-q', '-o', str(REND / f'{eid}_96.png'), '-sDEVICE=pngalpha', '-r96', str(k))
        with pikepdf.open(k) as pk:
            box = [float(x) for x in pk.pages[0].MediaBox]
        # pt PostScript; profundidade = quanto a imagem desce abaixo da baseline
        met[eid] = {'w_pt': box[2] - box[0], 'h_pt': box[3] - box[1], 'tex_wd': w, 'tex_ht': h, 'tex_dp': dp}
    return met


# ---------- OOXML mínimo ----------
NSDECL = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
          'xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"')
CT = {'emf': 'image/x-emf', 'wmf': 'image/x-wmf', 'png': 'image/png', 'svg': 'image/svg+xml', 'pdf': 'application/pdf'}
EMU = 12700  # por pt


class Docx:
    def __init__(self):
        self.body, self.media, self.rels, self.n = [], {}, [], 0

    def rel(self, path, nome, tipo='image'):
        self.n += 1
        rid = f'rId{self.n + 10}'
        self.media[f'word/media/{nome}'] = Path(path).read_bytes()
        self.rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                         f'relationships/{tipo}" Target="media/{nome}"/>')
        return rid

    def p(self, *runs):
        self.body.append('<w:p>' + ''.join(runs) + '</w:p>')

    @staticmethod
    def t(txt):
        return f'<w:r><w:t xml:space="preserve">{txt}</w:t></w:r>'

    def img(self, path, nome, w, h, eid, pos_halfpt=0, onde_id=('name', 'descr', 'title'), svg=None):
        rid = self.rel(path, nome)
        ext = ''
        if svg:
            sid = self.rel(svg, nome.rsplit('.', 1)[0] + '.svg')
            ext = ('<a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}"><asvg:svgBlip '
                   'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="%s"/></a:ext></a:extLst>' % sid)
        attrs = ' '.join(f'{k}="{eid if k != "name" else eid}"' for k in onde_id)
        if 'name' not in onde_id: attrs = f'name="Imagem {self.n}" ' + attrs
        cx, cy = round(w * EMU), round(h * EMU)
        pos = f'<w:position w:val="{pos_halfpt}"/>' if pos_halfpt else ''
        return (f'<w:r><w:rPr>{pos}</w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
                f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{self.n}" {attrs}/>'
                f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
                f'<pic:nvPicPr><pic:cNvPr id="{self.n}" name="{eid}"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}">{ext}</a:blip><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
                f'</wp:inline></w:drawing></w:r>')

    def save(self, path, extra_parts=None, extra_rels=()):
        doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NSDECL}><w:body>'
               + ''.join(self.body) + '<w:sectPr/></w:body></w:document>')
        types = ''.join(f'<Default Extension="{e}" ContentType="{c}"/>' for e, c in CT.items())
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml',
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                       '<Default Extension="xml" ContentType="application/xml"/>'
                       '<Default Extension="bin" ContentType="application/vnd.openxmlformats-officedocument.oleObject"/>'
                       + types +
                       '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                       '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
            z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            z.writestr('word/styles.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                       '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr></w:rPrDefault>'
                       '<w:pPrDefault><w:pPr><w:spacing w:after="240" w:line="360" w:lineRule="exact"/></w:pPr></w:pPrDefault></w:docDefaults></w:styles>')
            z.writestr('word/document.xml', doc)
            z.writestr('word/_rels/document.xml.rels',
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       + ''.join(self.rels) + ''.join(extra_rels) + '</Relationships>')
            for k, v in {**self.media, **(extra_parts or {})}.items():
                z.writestr(k, v)


def montar(met):
    e = 'EQ-0001'; m = met[e]; R = REND
    # S1 — um .docx por formato (se um formato quebrar o arquivo no Word, não derruba os outros)
    formatos = {'emf': (R / f'{e}.emf', None), 'wmf': (R / f'{e}.wmf', None),
                'svg': (R / f'{e}_96.png', R / f'{e}.svg'), 'png1200': (R / f'{e}.png', None),
                'pdf': (R / f'{e}_k100_op.pdf', None)}
    for fmt, (src, svg) in formatos.items():
        d = Docx()
        d.p(d.t(f'S1 — formato {fmt.upper()}. Texto antes '), d.img(src, f'{e}.{src.suffix[1:]}', m['w_pt'], m['h_pt'], e, svg=svg),
            d.t(' texto depois, na mesma linha.'))
        for e2 in ('EQ-0002', 'EQ-0003'):
            s2 = R / f'{e2}.{src.suffix[1:]}' if fmt in ('emf', 'wmf') else (R / f'{e2}_96.png' if fmt == 'svg' else
                 R / f'{e2}.png' if fmt == 'png1200' else R / f'{e2}_k100_op.pdf')
            d.p(d.t(f'Inline {e2}: valor '), d.img(s2, f'{e2}.{s2.suffix[1:]}', met[e2]['w_pt'], met[e2]['h_pt'], e2,
                                                   svg=(R / f'{e2}.svg' if fmt == 'svg' else None)), d.t(' fim.'))
        d.save(OUT / f'S1_{fmt}.docx')
    # S2 — baseline: mesma equação com w:position = 0, -2, -4, -7, -10 meios-pontos (granularidade do Word = 0,5 pt)
    d = Docx()
    for hp in (0, -2, -4, -7, -10):
        d.p(d.t(f'S2 position={hp / 2:+.1f} pt: Hx '), d.img(R / 'EQ-0002.emf', f'EQ-0002_p{abs(hp)}.emf', met['EQ-0002']['w_pt'],
                                                        met['EQ-0002']['h_pt'], f'EQ-S2-{abs(hp)}', pos_halfpt=hp), d.t(' xH'))
    d.save(OUT / 'S2_baseline.docx')
    # S3 — onde o ID sobrevive: nome do arquivo, docPr name, descr (alt text), title — cada um isolado
    d = Docx()
    casos = [('arquivo', 'EQ-0101.emf', ()), ('name', 'image1.emf', ('name',)), ('descr', 'image2.emf', ('descr',)),
             ('title', 'image3.emf', ('title',))]
    for caso, nome, onde in casos:
        eid = {'arquivo': 'EQ-0101', 'name': 'EQ-0102', 'descr': 'EQ-0103', 'title': 'EQ-0104'}[caso]
        x = d.img(R / 'EQ-0003.emf', nome, met['EQ-0003']['w_pt'], met['EQ-0003']['h_pt'], eid, onde_id=onde or ('descr',))
        if caso == 'arquivo': x = re.sub(r'descr="EQ-0101"', 'descr=""', x)
        d.p(d.t(f'S3 id via {caso} ({eid}): '), x, d.t(' fim.'))
    d.save(OUT / 'S3_identificador.docx')
    # S5 — mesma equação em 4 variantes de cor, como PDF solto (para Colocar no InDesign)
    for f in R.glob('EQ-0001_*.pdf'):
        if 'outl' not in f.name: shutil.copy(f, OUT / f'S5_{f.name}')


def s4(met):
    """S4 — mantém o OLE original da amostra e troca só a prévia WMF pelo render novo."""
    src = next(Path(__file__).resolve().parents[2].glob('samples/corpus_mt_questoes.docx'))
    dst = OUT / 'S4_ole_previa_trocada.docx'
    zin = zipfile.ZipFile(src)
    doc = zin.read('word/document.xml').decode('utf8')
    rels = zin.read('word/_rels/document.xml.rels').decode('utf8')
    # 1ª equação: descobre a prévia e substitui o arquivo pelo WMF novo, mantendo o nome
    rid = re.search(r'<w:object\b.*?<v:imagedata r:id="(rId\d+)"', doc, re.S).group(1)
    alvo = 'word/' + re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="{rid}"', rels).group(1)
    novo = (REND / 'EQ-0001.wmf').read_bytes()
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        for it in zin.infolist():
            z.writestr(it, novo if it.filename == alvo else zin.read(it))
    return alvo


def verificar():
    """Separações via Ghostscript inkcov em cada PDF de teste (mesma checagem que o produto fará)."""
    res = {}
    for f in sorted(OUT.glob('S5_*.pdf')):
        out = subprocess.run(['gs', '-q', '-o', '-', '-sDEVICE=inkcov', str(f)], capture_output=True, text=True).stdout.split()
        res[f.name] = dict(zip('CMYK', map(float, out[:4])))
    return res


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    met = render()
    montar(met)
    alvo = s4(met)
    rel = {'metricas': met, 'S4_previa_trocada': alvo, 'inkcov': verificar()}
    (OUT / 'relatorio_spike.json').write_text(json.dumps(rel, indent=1, ensure_ascii=False))
    print(json.dumps(rel, indent=1, ensure_ascii=False))
