"""SPIKE S0 (descartável) — inventário do corpus /samples.

Fontes: MTEF v5 pública (DOC-PUBLICA) + estrutura observada nas amostras (AMOSTRA).
Não é código de produção. Saída: JSON com estatísticas + lista de não-parseadas.
Uso: .venv/bin/python spikes/s0_corpus/analisar_corpus.py samples/*.docx > spikes/out/corpus.json
"""
import io, json, re, struct, sys, zipfile
from collections import Counter
import olefile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'v': 'urn:schemas-microsoft-com:vml', 'o': 'urn:schemas-microsoft-com:office:office',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
TMPL = {0: 'ANGLE', 1: 'PAREN', 2: 'BRACE', 3: 'BRACK', 4: 'BAR', 5: 'DBAR', 6: 'FLOOR', 7: 'CEILING', 8: 'OBRACK',
        9: 'INTERVAL', 10: 'ROOT', 11: 'FRACT', 12: 'UBAR', 13: 'OBAR', 14: 'ARROW', 15: 'INTEG', 16: 'SUM', 17: 'PROD',
        18: 'COPROD', 19: 'UNION', 20: 'INTER', 21: 'INTOP', 22: 'SUMOP', 23: 'LIM', 24: 'HBRACE', 25: 'HBRACK',
        26: 'LDIV', 27: 'SUB', 28: 'SUP', 29: 'SUBSUP', 30: 'DIRAC', 31: 'VEC', 32: 'TILDE', 33: 'HAT', 34: 'ARC',
        35: 'JSTATUS', 36: 'STRIKE', 37: 'BOX'}


class P:
    def __init__(s, b, st):
        s.b, s.i, s.st = b, 0, st

    def u8(s):
        v = s.b[s.i]; s.i += 1; return v

    def u16(s):
        v = struct.unpack_from('<H', s.b, s.i)[0]; s.i += 2; return v

    def uint(s):
        v = s.u8(); return s.u16() if v == 255 else v

    def cstr(s):
        j = s.b.index(0, s.i); v = s.b[s.i:j].decode('latin1'); s.i = j + 1; return v

    def nudge(s, opt):
        if opt & 8:
            dx, dy = s.u8(), s.u8()
            if dx == 128 and dy == 128: s.u16(); s.u16()
            s.st['nudge'] += 1

    def dims(s):
        n = s.u8(); out, cur, unit = [], '', None
        nib = []
        while len(out) < n:
            byte = s.u8(); nib += [byte >> 4, byte & 15]
            while nib and len(out) < n:
                x = nib.pop(0)
                if unit is None: unit = x
                elif x == 15: out.append(cur + ['in', 'cm', 'pt', 'pc', '%'][unit]); cur, unit = '', None
                else: cur += '0123456789.-'[x] if x < 12 else '?'
        return out

    def records(s, depth=0):
        """Lê registros até END; devolve contagem de objetos."""
        while s.i < len(s.b):
            t = s.u8()
            if t == 0: return
            s.rec(t, depth)

    def rec(s, t, depth):
        st = s.st; st['rec'][t] += 1
        if t == 1:  # LINE
            o = s.u8(); s.nudge(o)
            if o & 4: s.u16()
            if o & 2: s.rec(s.u8(), depth)
            if not o & 1: s.records(depth + 1)
        elif t == 2:  # CHAR
            o = s.u8(); s.nudge(o)
            tf = s.u8()
            tf = tf - 128 if tf != 255 else s.u16() - 32768
            mt = None
            if not o & 0x20: mt = s.u16()
            if o & 0x04: s.u8()
            if o & 0x10: s.u16()
            st['typeface'][tf] += 1
            if mt is not None: st['mtcode'][f'U+{mt:04X} {chr(mt) if mt < 0xE000 else "PUA"}'] += 1
            if o & 2: st['func_start'] += 1
            if o & 1: s.records(depth + 1)
        elif t == 3:  # TMPL
            o = s.u8(); s.nudge(o)
            sel = s.u8(); v = s.u8()
            if v & 0x80: v = (v & 0x7F) | (s.u8() << 8)
            s.u8()
            st['tmpl'][f'{sel}:{TMPL.get(sel, "?")} var=0x{v:04x}'] += 1
            s.records(depth + 1)
        elif t == 4:  # PILE
            o = s.u8(); s.nudge(o); h, va = s.u8(), s.u8()
            st['pile'][f'h{h} v{va}'] += 1
            if o & 2: s.rec(s.u8(), depth)
            s.records(depth + 1)
        elif t == 5:  # MATRIX
            o = s.u8(); s.nudge(o); va, hj, vj, r, c = (s.u8() for _ in range(5))
            s.i += ((r + 1) * 2 + 7) // 8 + ((c + 1) * 2 + 7) // 8
            st['matrix'][f'{r}x{c} h{hj}'] += 1
            s.records(depth + 1)
        elif t == 6:  # EMBELL
            o = s.u8(); s.nudge(o); st['embell'][s.u8()] += 1
        elif t == 7:  # RULER
            for _ in range(s.u8()): s.u8(); s.u16()
        elif t == 8: s.uint(); s.u8()
        elif t == 9:
            a = s.u8()
            if a == 101: st['size'][f'explicit {s.u16() / 32:.2f}pt'] += 1
            elif a == 100: s.u8(); s.u16()
            else: st['size'][f'l{a} d{s.u8() - 128}'] += 1
        elif 10 <= t <= 14: pass
        elif t == 15: st['color_use'][s.uint()] += 1
        elif t == 16:
            o = s.u8(); vals = [s.u16() for _ in range(4 if o & 1 else 3)]
            name = s.cstr() if o & 4 else ''
            st['color_def'][f'{"CMYK" if o & 1 else "RGB"}{vals}{" spot" if o & 2 else ""} {name}'] += 1
        elif t == 17: s.uint(); st['font'][s.cstr()] += 1
        elif t == 18:
            s.u8(); sizes = s.dims(); spaces = s.dims()
            styles = []
            for _ in range(s.u8()):
                fd = s.uint(); styles.append((fd, s.u8() if fd else None))
            st['prefs'][json.dumps({'sizes': sizes, 'spaces': spaces, 'styles': styles})] += 1
        elif t == 19: st['encoding'][s.cstr()] += 1
        elif t >= 100: s.i += s.uint(); st['future'][t] += 1
        else: raise ValueError(f'registro desconhecido {t} @ {s.i - 1}')


def mtef_de_ole(blob):
    ole = olefile.OleFileIO(io.BytesIO(blob))
    d = ole.openstream('Equation Native').read()
    hlen = struct.unpack_from('<H', d)[0]  # observado: 28
    return hlen, d[hlen:]


def analisar(path, st):
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    rels = {r.get('Id'): r.get('Target') for r in etree.fromstring(z.read('word/_rels/document.xml.rels'))}
    eqs = []
    for k, obj in enumerate(doc.iter(f'{{{W}}}object'), 1):
        ole = obj.find('o:OLEObject', NS); shape = obj.find('v:shape', NS); img = shape.find('v:imagedata', NS)
        run = obj.getparent(); para = run.getparent()
        while para.tag != f'{{{W}}}p': para = para.getparent()
        pos = run.find('w:rPr/w:position', NS)
        txt = ''.join(t.text or '' for t in para.iter(f'{{{W}}}t')).strip()
        e = {'n': k, 'progid': ole.get('ProgID'), 'ole': rels[ole.get(f'{{{NS["r"]}}}id')],
             'preview': rels[img.get(f'{{{NS["r"]}}}id')], 'style': shape.get('style'),
             'w_position_halfpt': int(pos.get(f'{{{W}}}val')) if pos is not None else None,
             'sozinha_no_paragrafo': not txt and len(para.findall('.//w:object', NS)) == 1,
             'in_table': any(a.tag == f'{{{W}}}tc' for a in para.iterancestors())}
        st['progid'][e['progid']] += 1
        st['preview_ext'][e['preview'].rsplit('.', 1)[1]] += 1
        try:
            hlen, m = mtef_de_ole(z.read('word/' + e['ole']))
            st['ole_hdr_len'][hlen] += 1
            st['mtef_hdr'][f'v{m[0]} plat{m[1]} prod{m[2]} {m[3]}.{m[4]}'] += 1
            p = P(m, st); p.i = 5; st['appkey'][p.cstr()] += 1
            e['inline_flag'] = bool(p.u8() & 1)
            p.records()
            e['ok'] = True
        except Exception as ex:
            e['ok'] = False; e['erro'] = repr(ex); st['erros'].append((path, k, repr(ex)))
        eqs.append(e)
    return eqs


if __name__ == '__main__':
    keys = ['rec', 'typeface', 'mtcode', 'tmpl', 'pile', 'matrix', 'embell', 'size', 'color_use', 'color_def', 'font',
            'prefs', 'encoding', 'future', 'progid', 'preview_ext', 'ole_hdr_len', 'mtef_hdr', 'appkey']
    st = {k: Counter() for k in keys}; st.update(nudge=0, func_start=0, erros=[])
    por_doc = {}
    for f in sys.argv[1:]:
        eqs = analisar(f, st)
        por_doc[f] = {'total': len(eqs), 'ok': sum(e['ok'] for e in eqs),
                      'display_flag': sum(not e.get('inline_flag', True) for e in eqs),
                      'sozinha_no_paragrafo': sum(e['sozinha_no_paragrafo'] for e in eqs),
                      'em_tabela': sum(e['in_table'] for e in eqs),
                      'w_position': Counter(str(e['w_position_halfpt']) for e in eqs),
                      'amostra': eqs[:3]}
    out = {k: (dict(v.most_common()) if isinstance(v, Counter) else v) for k, v in st.items()}
    out['por_doc'] = por_doc
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1, default=str)
