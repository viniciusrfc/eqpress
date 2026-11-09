"""SPIKE O0 (descartável): preto composto → 100 % K editando o EPS no lugar.

Substituições do MESMO comprimento (padding com espaços), então o cabeçalho DOS EPS (offsets da
seção PostScript e da prévia TIFF), a BoundingBox e todo o resto ficam byte a byte iguais.
Fonte: AMOSTRA:eq_composta.EPS (Illustrator 24, operador AGM `cmyk`).
Uso: corrigir_eps.py entrada.eps saida.eps [limiar_K=0.9]
"""
import re, struct, sys
from pathlib import Path

COR = re.compile(rb'(?m)^(\s*)(\.?\d*\.?\d+) (\.?\d*\.?\d+) (\.?\d*\.?\d+) (\.?\d*\.?\d+)( cmyk)')


def mesmo_tamanho(velho: bytes, novo: bytes) -> bytes:
    assert len(novo) <= len(velho), (velho, novo)
    return novo + b' ' * (len(velho) - len(novo))


def corrigir(dados: bytes, limiar=0.9):
    trocas = []

    def troca(m):
        c, mg, y, k = (float(x) for x in m.groups()[1:5])
        if k >= limiar and (c or mg or y):  # ponytail: "preto" = K ≥ limiar; cores reais de destaque passam intactas
            trocas.append((c, mg, y, k))
            corpo = m.group(0)[len(m.group(1)):-len(m.group(6))]
            return m.group(1) + mesmo_tamanho(corpo, b'0 0 0 1') + m.group(6)
        return m.group(0)

    dados = COR.sub(troca, dados)
    if trocas:  # metadados de chapas: só Black
        dados = re.sub(rb'%%DocumentProcessColors:[^\r\n]*',
                       lambda m: mesmo_tamanho(m.group(0), b'%%DocumentProcessColors:  Black'), dados)
        for t in (b'Cyan', b'Magenta', b'Yellow'):
            dados = dados.replace(b'<rdf:li>' + t + b'</rdf:li>', b' ' * len(b'<rdf:li>' + t + b'</rdf:li>'))
    return dados, trocas


if __name__ == '__main__':
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    lim = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9
    velho = src.read_bytes()
    novo, trocas = corrigir(velho, lim)
    assert len(novo) == len(velho)
    if velho[:4] == b'\xc5\xd0\xd3\xc6':  # DOS EPS: offsets intactos
        assert novo[:30] == velho[:30]
    dst.write_bytes(novo)
    print(f'{src.name}: {len(trocas)} cor(es) trocada(s) → 0 0 0 1', sorted(set(trocas)))
