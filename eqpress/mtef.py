"""F2 — parser MTEF v5 → árvore.

Fonte: DOC-PUBLICA:MTEF5 (spec/MTEF.md). Nenhum código de terceiros consultado.
"""
from dataclasses import dataclass, field

END, LINE, CHAR, TMPL, PILE, MATRIX, EMBELL, RULER = range(8)
FONT_STYLE_DEF, SIZE, FULL, SUB, SUB2, SYM, SUBSYM = range(8, 15)
COLOR, COLOR_DEF, FONT_DEF, EQN_PREFS, ENCODING_DEF = range(15, 20)
OPT_NUDGE = 0x08


class NaoSuportada(Exception):
    """Equação que o parser não sabe ler (R-MTEF-01/02/05); vai para o relatório."""


@dataclass
class Car:
    tf: int  # typeface (MTEF.md §4)
    cod: int | None  # MTCode
    emb: list[int] = field(default_factory=list)  # tipos de EMBELL
    func: bool = False  # mtefOPT_CHAR_FUNC_START
    tam: int = 0  # typesize lógico corrente (0 = completo)
    cor: int = 0  # índice COLOR_DEF corrente (0 = padrão)
    nudge: tuple | None = None


@dataclass
class Linha:
    itens: list = field(default_factory=list)
    nula: bool = False


@dataclass
class Tmpl:
    sel: int
    var: int
    opc: int
    filhos: list = field(default_factory=list)  # Linha/Car/… na ordem da classe (MTEF.md §5)
    nudge: tuple | None = None


@dataclass
class Pilha:
    halign: int
    valign: int
    linhas: list = field(default_factory=list)


@dataclass
class Matriz:
    valign: int
    hjust: int
    vjust: int
    lins: int
    cols: int
    part_lin: list  # 0 nenhuma, 1 sólida, 2 tracejada, 3 pontilhada (lins+1 valores)
    part_col: list
    celulas: list = field(default_factory=list)


@dataclass
class Equacao:
    versao: tuple  # (mtef, plataforma, produto, versão, subversão)
    app_key: str
    inline: bool  # ⚠ não confiável (R-DOCX-04)
    raiz: object  # Linha ou Pilha
    fontes: list = field(default_factory=list)  # FONT_DEF: (índice encoding, nome)
    cores: list = field(default_factory=list)  # COLOR_DEF: dict
    prefs: dict | None = None  # EQN_PREFS decodificado
    estilos_fonte: list = field(default_factory=list)  # FONT_STYLE_DEF: (índice FONT_DEF, estilo)


class Leitor:
    def __init__(self, dados):
        self.d, self.i = dados, 0
        self.tam, self.cor = 0, 0
        self.fontes, self.cores, self.estilos_fonte, self.prefs = [], [], [], None

    # --- valores primitivos (MTEF.md §2) ---
    def byte(self):
        if self.i >= len(self.d):
            raise NaoSuportada(f"fim inesperado do MTEF no byte {self.i}")
        b = self.d[self.i]
        self.i += 1
        return b

    def u16(self):
        return self.byte() | (self.byte() << 8)

    def s16(self):
        v = self.u16()
        return v - 0x10000 if v & 0x8000 else v

    def uint(self):
        b = self.byte()
        return self.u16() if b == 255 else b

    def sint(self):
        b = self.byte()
        return self.u16() - 32768 if b == 255 else b - 128

    def cstr(self):
        fim = self.d.index(0, self.i)
        s = self.d[self.i:fim].decode("latin-1")
        self.i = fim + 1
        return s

    def nudge(self, opc):
        if not opc & OPT_NUDGE:
            return None
        dx, dy = self.byte() - 128, self.byte() - 128
        if dx == 0 and dy == 0:  # 128,128 → seguem dx, dy em 16 bits
            dx, dy = self.s16(), self.s16()
        return (dx, dy)

    def dimensoes(self):
        """Array de dimensões (EQN_PREFS): lista de (unidade, texto)."""
        n = self.byte()
        nibbles = []

        def nib():
            if not nibbles:
                b = self.byte()
                nibbles.extend([b >> 4, b & 0xF])
            return nibbles.pop(0)

        unidades = ["in", "cm", "pt", "pc", "%"]
        res = []
        for _ in range(n):
            u = nib()
            s = ""
            while (c := nib()) != 0xF:
                s += "0123456789.-"[c] if c <= 0xB else "?"
            res.append((unidades[u] if u < 5 else str(u), s))
        return res  # nibble de padding descartado com a lista

    def regua(self):
        if self.byte() != RULER:
            raise NaoSuportada(f"RULER esperado no byte {self.i - 1}")
        return [(self.byte(), self.u16()) for _ in range(self.byte())]

    # --- registros ---
    def lista(self):
        """Lê objetos até END. Registros de estado/definição atualizam o leitor."""
        itens = []
        while True:
            ini = self.i
            t = self.byte()
            if t == END:
                return itens
            obj = self.registro(t, ini)
            if obj is not None:
                itens.append(obj)

    def registro(self, t, ini):
        if t == LINE:
            opc = self.byte()
            self.nudge(opc)
            if opc & 0x04:
                self.u16()  # espaçamento de linha
            if opc & 0x02:
                self.regua()
            if opc & 0x01:
                return Linha(nula=True)
            return Linha(self.lista())
        if t == CHAR:
            opc = self.byte()
            nd = self.nudge(opc)
            tf = self.sint()
            cod = None if opc & 0x20 else self.u16()
            if opc & 0x04:
                self.byte()
            if opc & 0x10:
                self.u16()
            emb = [e for e in self.lista()] if opc & 0x01 else []
            return Car(tf, cod, emb, bool(opc & 0x02), self.tam, self.cor, nd)
        if t == TMPL:
            opc = self.byte()
            nd = self.nudge(opc)
            sel = self.byte()
            var = self.byte()
            if var & 0x80:
                var = (var & 0x7F) | (self.byte() << 8)
            topc = self.byte()
            tam0 = self.tam
            filhos = self.lista()
            self.tam = tam0
            return Tmpl(sel, var, topc, filhos, nd)
        if t == PILE:
            opc = self.byte()
            self.nudge(opc)
            ha, va = self.byte(), self.byte()
            if opc & 0x02:
                self.regua()
            return Pilha(ha, va, self.lista())
        if t == MATRIX:
            opc = self.byte()
            self.nudge(opc)
            va, hj, vj, lins, cols = (self.byte() for _ in range(5))
            pl = self.particoes(lins + 1)
            pc = self.particoes(cols + 1)
            return Matriz(va, hj, vj, lins, cols, pl, pc, self.lista())
        if t == EMBELL:
            opc = self.byte()
            self.nudge(opc)
            return self.byte()
        if t == RULER:
            self.i -= 1
            self.regua()
            return None
        if t == FONT_STYLE_DEF:
            self.estilos_fonte.append((self.uint(), self.byte()))
            return None
        if t == SIZE:
            ls = self.byte()
            if ls == 101:
                self.s16()
                self.tam = -1  # tamanho explícito
            elif ls == 100:
                self.tam = self.byte()
                self.s16()
            else:
                self.tam = ls
                self.byte()
            return None
        if FULL <= t <= SUBSYM:
            self.tam = t - FULL
            return None
        if t == COLOR:
            self.cor = self.uint()
            return None
        if t == COLOR_DEF:
            opc = self.byte()
            vals = [self.u16() for _ in range(4 if opc & 0x01 else 3)]
            nome = self.cstr() if opc & 0x04 else None
            self.cores.append({"modelo": "cmyk" if opc & 1 else "rgb", "spot": bool(opc & 2),
                               "valores": vals, "nome": nome})
            return None
        if t == FONT_DEF:
            self.fontes.append((self.uint(), self.cstr()))
            return None
        if t == EQN_PREFS:
            self.byte()
            tamanhos, espacos = self.dimensoes(), self.dimensoes()
            estilos = []
            for _ in range(self.byte()):
                f = self.uint()
                estilos.append((f, self.byte()) if f else None)
            self.prefs = {"tamanhos": tamanhos, "espacos": espacos, "estilos": estilos}
            return None
        if t == ENCODING_DEF:
            self.cstr()
            return None
        if t >= 100:
            n = self.uint()  # não usar `self.i += self.uint()`: lê self.i antes de avançar
            self.i += n
            return None
        raise NaoSuportada(f"registro desconhecido {t} no byte {ini}")  # R-MTEF-02

    def particoes(self, n):
        bs = [self.byte() for _ in range((2 * n + 7) // 8)]
        return [(bs[k // 4] >> (2 * (k % 4))) & 3 for k in range(n)]


def ler(mtef: bytes) -> Equacao:
    r = Leitor(mtef)
    versao = tuple(r.byte() for _ in range(5))
    if versao[0] != 5:
        raise NaoSuportada(f"MTEF versão {versao[0]} (só v5)")  # R-MTEF-01
    app = r.cstr()
    inline = bool(r.byte() & 1)
    itens = r.lista()
    raizes = [x for x in itens if isinstance(x, (Linha, Pilha))]
    if len(raizes) != 1 or len(itens) != 1:
        raise NaoSuportada(f"esperada 1 LINE/PILE na raiz, achei {len(itens)} objetos")
    if r.i != len(mtef):
        # bytes após o END final: tolerado (preenchimento), mas não deve haver registro
        if any(mtef[r.i:]):
            raise NaoSuportada(f"{len(mtef) - r.i} bytes após o END final")
    return Equacao(versao, app, inline, raizes[0], r.fontes, r.cores, r.prefs, r.estilos_fonte)
