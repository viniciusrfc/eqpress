"""SPIKE S5/O0 (descartável): cobertura por chapa (CMYK + especiais) de EPS/PDF via gs tiffsep."""
import subprocess, sys, re, tempfile
from pathlib import Path
from PIL import Image

def chapas(arq, dpi=600):
    with tempfile.TemporaryDirectory() as d:
        base = Path(d) / 's.tif'
        a = ['gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=tiffsep', f'-r{dpi}', f'-sOutputFile={base}']
        if arq.suffix.lower() == '.eps': a.append('-dEPSCrop')
        subprocess.run(a + [str(arq)], check=True, capture_output=True)
        out = {}
        for t in sorted(Path(d).glob('s(*).tif')):
            nome = re.search(r'\((.*)\)', t.name).group(1)
            im = Image.open(t).convert('L')  # 255 = sem tinta
            h = im.histogram(); total = sum(h)
            tinta = sum(c * (255 - v) / 255 for v, c in enumerate(h)) / total * 100
            px = sum(h[:255]) / total * 100
            out[nome] = (round(tinta, 3), round(px, 3))
        return out

for f in sys.argv[1:]:
    r = chapas(Path(f))
    print(Path(f).name.ljust(26), '  '.join(f'{k}: {v[0]}%' for k, v in r.items() if v[1] > 0) or 'vazio')
