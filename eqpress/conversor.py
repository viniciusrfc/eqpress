"""F2 — árvore MTEF → LaTeX (canônico, ED-01) e MathML (derivado).

O LaTeX usa só o subconjunto que renderiza igual em LaTeX, MathJax 3 e KaTeX (ED-04, CA-17).
Nada é descartado em silêncio: o que não tem tradução exata vira aviso (CA-13).
"""
from dataclasses import dataclass, field

from lxml import etree

from . import mtef as M

# --- caracteres -------------------------------------------------------------------------------
GREGO = dict(zip(
    "αβγδεζηθικλμνξπρςστυφχψωϑϕϖϵΓΔΘΛΞΠΣΥΦΨΩ",
    r"\alpha \beta \gamma \delta \varepsilon \zeta \eta \theta \iota \kappa \lambda \mu \nu \xi \pi"
    r" \rho \varsigma \sigma \tau \upsilon \varphi \chi \psi \omega \vartheta \phi \varpi \epsilon"
    r" \Gamma \Delta \Theta \Lambda \Xi \Pi \Sigma \Upsilon \Phi \Psi \Omega".split(),
))
SIMBOLOS = {
    "−": "-", "+": "+", "=": "=", "<": "<", ">": ">", "(": "(", ")": ")", "[": "[", "]": "]",
    ",": ",", ".": ".", ";": ";", ":": ":", "!": "!", "?": "?", "/": "/", "|": "|", "'": "'",
    "*": "*", "-": r"\text{-}", "–": r"\text{–}", "—": r"\text{—}", "\xa0": "~",
    "{": r"\{", "}": r"\}", "%": r"\%", "$": r"\$", "#": r"\#", "&": r"\&", "_": r"\_",
    "⋅": r"\cdot", "·": r"\cdot", "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp",
    "→": r"\rightarrow", "←": r"\leftarrow", "↔": r"\leftrightarrow", "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow", "↑": r"\uparrow", "↓": r"\downarrow",
    "⇌": r"\rightleftharpoons", "⇄": r"\rightleftarrows", "↦": r"\mapsto",
    "≤": r"\le", "≥": r"\ge", "≠": r"\ne", "≈": r"\approx", "≡": r"\equiv", "≅": r"\cong",
    "∼": r"\sim", "∝": r"\propto", "≪": r"\ll", "≫": r"\gg", "≃": r"\simeq",
    "∞": r"\infty", "∴": r"\therefore", "∵": r"\because", "•": r"\bullet", "°": r"^{\circ}",
    "∈": r"\in", "∉": r"\notin", "⊂": r"\subset", "⊃": r"\supset", "⊆": r"\subseteq",
    "⊇": r"\supseteq", "∪": r"\cup", "∩": r"\cap", "∅": r"\varnothing", "∀": r"\forall",
    "∃": r"\exists", "¬": r"\neg", "∧": r"\wedge", "∨": r"\vee", "∂": r"\partial",
    "∇": r"\nabla", "′": r"'", "″": r"''", "∠": r"\angle", "⊥": r"\perp", "∥": r"\parallel",
    "…": r"\ldots", "⋯": r"\cdots", "ℝ": r"\mathbb{R}", "ℕ": r"\mathbb{N}", "ℤ": r"\mathbb{Z}",
    "ℚ": r"\mathbb{Q}", "ℂ": r"\mathbb{C}", "∑": r"\sum", "∏": r"\prod", "∫": r"\int",
    "√": r"\surd", "∘": r"\circ", "△": r"\triangle", "⟂": r"\perp", "ℓ": r"\ell",
}
# MTCode de uso privado com significado inferido do contexto (MTEF.md §6)
PUA = {0xEC07: "|", 0xEC08: "|"}
RELACOES = set("=<>≤≥≈≠≡≅∼∝≪≫≃→←↔⇒⇐⇔⇌⇄∈⊂⊃⊆⊇")
ESPACOS = {r"\,", r"\ ", "~", ""}
TEXTO_ESC = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "%": r"\%",
             "&": r"\&", "#": r"\#", "_": r"\_", "^": r"\^{}", "~": r"\~{}"}
CORES_BASE = {"black": (0, 0, 0), "red": (1000, 0, 0), "green": (0, 1000, 0), "blue": (0, 0, 1000),
              "cyan": (0, 1000, 1000), "magenta": (1000, 0, 1000), "yellow": (1000, 1000, 0),
              "orange": (1000, 500, 0), "purple": (750, 0, 250), "gray": (500, 500, 500)}

# --- templates (MTEF.md §5) -------------------------------------------------------------------
# cercas 0–8: (esquerda, direita) em \left/\right
CERCAS = {0: (r"\langle", r"\rangle"), 1: ("(", ")"), 2: (r"\{", r"\}"), 3: ("[", "]"),
          4: ("|", "|"), 5: (r"\|", r"\|"), 6: (r"\lfloor", r"\rfloor"), 7: (r"\lceil", r"\rceil"),
          8: ("[", "]")}
INTERVALO = ["(", ")", "[", "]"]  # tvINTV: 0 ( , 1 ) , 2 [ , 3 ]
OPERADORES = {"∑": r"\sum", "∏": r"\prod", "∐": r"\coprod", "⋃": r"\bigcup", "⋂": r"\bigcap",
              "∫": r"\int", "∬": r"\iint", "∭": r"\iiint", "∮": r"\oint", "⨁": r"\bigoplus",
              "⨂": r"\bigotimes", "⋁": r"\bigvee", "⋀": r"\bigwedge"}
OPERADOR_PADRAO = {15: "∫", 16: "∑", 17: "∏", 18: "∐", 19: "⋃", 20: "⋂", 21: "∫", 22: "∑"}
# embelezamentos 2–37 (DOC-PUBLICA:MTEF5, EMBELL): forma LaTeX e (tipo, caractere) MathML
EMBELEZ = {
    2: (r"\dot{%s}", "over", "˙"), 3: (r"\ddot{%s}", "over", "¨"),
    4: (r"\overset{...}{%s}", "over", "⃛"), 5: ("%s'", "sup", "′"), 6: ("%s''", "sup", "″"),
    7: (r"{}^{\backprime}%s", "pre", "‵"), 8: (r"\tilde{%s}", "over", "~"),
    9: (r"\hat{%s}", "over", "^"), 10: (r"\cancel{%s}", "enc", "updiagonalstrike"),
    11: (r"\overrightarrow{%s}", "over", "→"), 12: (r"\overleftarrow{%s}", "over", "←"),
    13: (r"\overleftrightarrow{%s}", "over", "↔"), 14: (r"\overset{\rightharpoonup}{%s}", "over", "⇀"),
    15: (r"\overset{\leftharpoonup}{%s}", "over", "↼"),
    16: (r"\cancel{%s}", "enc", "horizontalstrike"),  # barra no meio: aproximada (aviso)
    17: (r"\bar{%s}", "over", "¯"), 18: ("%s'''", "sup", "‴"),
    19: (r"\overset{\frown}{%s}", "over", "⌢"), 20: (r"\overset{\smile}{%s}", "over", "⌣"),
    21: (r"\xcancel{%s}", "enc", "updiagonalstrike downdiagonalstrike"),
    22: (r"\cancel{%s}", "enc", "updiagonalstrike"), 23: (r"\bcancel{%s}", "enc", "downdiagonalstrike"),
    24: (r"\overset{....}{%s}", "over", "⃜"), 25: (r"\underset{.}{%s}", "under", "."),
    26: (r"\underset{..}{%s}", "under", ".."), 27: (r"\underset{...}{%s}", "under", "..."),
    28: (r"\underset{....}{%s}", "under", "...."), 29: (r"\underline{%s}", "under", "_"),
    30: (r"\underset{\sim}{%s}", "under", "~"), 31: (r"\underset{\frown}{%s}", "under", "⌢"),
    32: (r"\underset{\smile}{%s}", "under", "⌣"), 33: (r"\underrightarrow{%s}", "under", "→"),
    34: (r"\underleftarrow{%s}", "under", "←"), 35: (r"\underleftrightarrow{%s}", "under", "↔"),
    36: (r"\underset{\rightharpoonup}{%s}", "under", "⇀"),
    37: (r"\underset{\leftharpoonup}{%s}", "under", "↼"),
}
APROXIMADOS = {16: "barra horizontal no meio do caractere aproximada por \\cancel"}


def _ch(c):
    return chr(c.cod) if c.cod is not None and not 0xE000 <= c.cod <= 0xF8FF else None


def _letra(c):
    ch = _ch(c)
    return ch is not None and ch.isalpha()


def _digito(c):
    return isinstance(c, M.Car) and c.tf == 8 and _ch(c) is not None and _ch(c).isdigit()


def _vazio(x):
    return x is None or (isinstance(x, M.Linha) and (x.nula or not x.itens))


def _juntar(toks):
    s = ""
    for t in toks:
        if s and t and s[-1].isalpha() and t[0].isalpha() and "\\" in s and s.rsplit("\\", 1)[-1].isalpha():
            s += " "
        s += t
    return s


def _slots(t):
    return ([f for f in t.filhos if not isinstance(f, M.Car)], [f for f in t.filhos if isinstance(f, M.Car)])


@dataclass
class Resultado:
    latex: str | None
    mathml: str | None
    avisos: list[str] = field(default_factory=list)
    erro: str | None = None  # preenchido = equação não suportada (relatório)


class Latex:
    def __init__(self, eq):
        self.eq, self.avisos = eq, []

    def aviso(self, msg):
        if msg not in self.avisos:
            self.avisos.append(msg)

    # --- estrutura ---
    def no(self, x):
        if x is None or isinstance(x, M.Linha):
            return "" if _vazio(x) else self.itens(x.itens)
        if isinstance(x, M.Pilha):
            return self.pilha(x)
        if isinstance(x, M.Matriz):
            return self.matriz(x)
        if isinstance(x, M.Tmpl):
            return self.tmpl(x)
        if isinstance(x, M.Car):
            return self.itens([x])
        raise M.NaoSuportada(f"objeto inesperado {type(x).__name__}")

    def itens(self, itens):
        out, i = [], 0
        while i < len(itens):
            x = itens[i]
            if isinstance(x, M.Tmpl) and x.sel in (27, 28, 29):
                s = self.scripts(x)
                if x.var & 1:  # tvSU_PRECEDES: pré-script, base vazia
                    out.append("{}" + s)
                else:
                    if not out or out[-1] in ESPACOS or out[-1].endswith(("\\,", "\\ ")):
                        out.append("{}")
                    out[-1] += s
                i += 1
            elif isinstance(x, M.Car):
                j = self.fim_corrida(itens, i)
                out.extend(self.corrida(itens, i, j, out))
                i = j
            else:
                out.append(self.no(x))
                i += 1
        return _juntar(out)

    def grupo(self, c):
        """Chave de agrupamento de caracteres consecutivos (mesma chave = mesmo comando)."""
        if c.emb or c.tf in (6, 8, 11, 22, 23, 24) or _ch(c) is None:
            return None
        if c.tf in (1, 12, 9, 10) or c.tf < 0:
            return ("texto", c.cor)
        if c.tf == 7:
            return ("vetor", c.cor)
        if c.tf == 2 and _letra(c):
            return ("funcao", c.cor)
        if c.tf == 3 and _letra(c):
            return ("variavel", c.cor)
        return None

    def fim_corrida(self, itens, i):
        g = self.grupo(itens[i])
        j = i + 1
        if g is None:
            return j
        while j < len(itens) and isinstance(itens[j], M.Car) and self.grupo(itens[j]) == g \
                and not (g[0] == "funcao" and itens[j].func):
            j += 1
        return j

    def corrida(self, itens, i, j, out):
        cs = itens[i:j]
        g = self.grupo(cs[0])
        texto = "".join(_ch(c) for c in cs) if g else None
        if g is None:
            c = cs[0]
            toks = [self.caractere(c, itens, i, out)]
        elif g[0] == "texto":
            for c in cs:
                if c.tf < 0:
                    self.aviso(f"fonte explícita ({self.nome_fonte(c.tf)}) tratada como texto")
            toks = []
            for k, parte in enumerate(texto.split(" ")):
                if k:
                    toks.append(r"\ ")
                if parte:
                    toks.append(r"\text{" + "".join(TEXTO_ESC.get(ch, ch) for ch in parte) + "}")
        elif g[0] == "vetor":
            toks = [r"\mathbf{" + "".join(TEXTO_ESC.get(ch, ch) for ch in texto) + "}"]
        elif g[0] == "funcao":
            vizinho = (i > 0 and isinstance(itens[i - 1], M.Car) and _letra(itens[i - 1])) or \
                      (j < len(itens) and isinstance(itens[j], M.Car) and _letra(itens[j]))
            if cs[0].func and len(cs) > 1 and not vizinho:
                toks = [r"\operatorname{" + texto + "}"]
            else:
                toks = [r"\mathrm{" + texto + "}"]
        else:  # variável
            # palavra com letra acentuada: KaTeX não aceita em modo matemático (ED-04)
            toks = [r"\text{" + texto + "}"] if not texto.isascii() else \
                [GREGO.get(ch, ch) for ch in texto]
        cor = self.cor(cs[0].cor)
        if cor:
            toks = [r"\textcolor{" + cor + "}{" + _juntar(toks) + "}"]
        return toks

    def caractere(self, c, itens, i, out):
        ch = _ch(c)
        if c.tf == 23:
            return ""
        if c.tf == 24:
            if c.cod != 0xEF02:
                self.aviso(f"espaço MTCode U+{c.cod:04X} sem largura conhecida: usado \\,")
            return r"\,"
        if c.cod is None:
            self.aviso("caractere sem MTCode")
            return r"\boxed{?}"
        if ch is None:
            if c.cod in PUA:
                ch = PUA[c.cod]
            else:  # R-MTEF-06
                self.aviso(f"MTCode U+{c.cod:04X} (uso privado) sem mapeamento")
                return r"\boxed{?}"
        if ch == "," and out and out[-1][-1:].isdigit() and i + 1 < len(itens) and _digito(itens[i + 1]):
            tok = "{,}"  # vírgula decimal
        elif ch in GREGO:
            tok = GREGO[ch]
        elif ch in SIMBOLOS:
            tok = SIMBOLOS[ch]
        elif ch.isascii() and ch.isalnum():
            tok = ch
        elif ch.isalpha():
            tok = r"\text{" + ch + "}"
        else:
            self.aviso(f"caractere {ch!r} (U+{c.cod:04X}) sem comando LaTeX: usado direto")
            tok = ch
        for e in c.emb:
            if e not in EMBELEZ:
                raise M.NaoSuportada(f"embelezamento {e} desconhecido")
            if e in APROXIMADOS:
                self.aviso(APROXIMADOS[e])
            tok = EMBELEZ[e][0] % ("{" + tok + "}" if e in (5, 6, 18) and len(tok) > 1 else tok)
        cor = self.cor(c.cor)
        return r"\textcolor{" + cor + "}{" + tok + "}" if cor else tok

    def nome_fonte(self, tf):
        try:
            return self.eq.fontes[self.eq.estilos_fonte[-tf - 1][0] - 1][1]
        except IndexError:
            return f"estilo {tf}"

    def cor(self, idx):
        """R-MTEF-04: preto/padrão → None; outra cor → nome-base mais próximo (destaque)."""
        if idx < 1 or idx > len(self.eq.cores):
            return None
        d = self.eq.cores[idx - 1]
        v = d["valores"]
        if d["modelo"] == "cmyk":
            v = [(1000 - min(1000, x + v[3])) for x in v[:3]]
        nome = min(CORES_BASE, key=lambda k: sum((a - b) ** 2 for a, b in zip(CORES_BASE[k], v)))
        if nome == "black":
            return None
        if CORES_BASE[nome] != tuple(v):
            self.aviso(f"cor {d['nome'] or v} aproximada por {nome}")
        return nome

    def scripts(self, t):
        ls, _ = _slots(t)
        sub, sup = (ls + [None, None])[:2]
        s = ""
        if not _vazio(sub):
            s += "_{" + self.no(sub) + "}"
        if not _vazio(sup):
            s += "^{" + self.no(sup) + "}"
        return s or "{}"

    def pilha(self, p):
        if p.halign == 4:  # alinhamento no relacional
            linhas = []
            for ln in p.linhas:
                its = [] if _vazio(ln) else ln.itens
                k = next((n for n, x in enumerate(its) if isinstance(x, M.Car) and x.tf in (6, 11)
                          and _ch(x) in RELACOES), None)
                linhas.append("&" + self.itens(its) if k is None else
                              self.itens(its[:k]) + "&" + self.itens(its[k:]))
            return r"\begin{aligned}" + r"\\".join(linhas) + r"\end{aligned}"
        col = {1: "l", 2: "c", 3: "r"}.get(p.halign, "r")
        # linhas de pilha em tamanho cheio, como no MTEF (células de array seriam estilo texto)
        linhas = [r"\displaystyle " + self.no(x) if not _vazio(x) else "" for x in p.linhas]
        return r"\begin{array}{" + col + "}" + r"\\".join(linhas) + r"\end{array}"

    def matriz(self, m):
        sep = {0: "", 1: "|", 2: ":", 3: ":"}
        lin = {0: "", 1: r"\hline ", 2: r"\hdashline ", 3: r"\hdashline "}
        if 3 in m.part_lin or 3 in m.part_col:
            self.aviso("linha pontilhada de matriz aproximada por tracejada")
        col = {1: "l", 2: "c", 3: "r"}.get(m.hjust, "c")
        spec = "".join(sep[m.part_col[k]] + (col if k < m.cols else "") for k in range(m.cols + 1))
        cel = [r"\displaystyle " + self.no(x) if not _vazio(x) else "" for x in m.celulas]
        if len(cel) != m.lins * m.cols:
            raise M.NaoSuportada(f"matriz {m.lins}x{m.cols} com {len(cel)} células")
        corpo = lin[m.part_lin[0]]
        for r in range(m.lins):
            corpo += "&".join(cel[r * m.cols:(r + 1) * m.cols])
            if r < m.lins - 1 or m.part_lin[r + 1]:
                corpo += r"\\" + lin[m.part_lin[r + 1]]
        return r"\begin{array}{" + spec + "}" + corpo + r"\end{array}"

    def tmpl(self, t):
        ls, cs = _slots(t)
        s = [self.no(x) for x in ls] + [""] * 4
        sel, var = t.sel, t.var
        if sel <= 9:
            if sel == 9:
                e, d = INTERVALO[var & 3], INTERVALO[(var >> 4) & 3]
            else:
                e, d = CERCAS[sel]
                e, d = (e if var & 1 else "."), (d if var & 2 else ".")
            if sel == 8:  # colchete branco ⟦ ⟧: sem delimitador portátil, dois colchetes
                return rf"\left{e}\!\left{e} {s[0]} \right{d}\!\right{d}"
            return rf"\left{e} {s[0]} \right{d}"
        if sel == 10:
            return rf"\sqrt[{s[1]}]{{{s[0]}}}" if var == 1 and s[1] else rf"\sqrt{{{s[0]}}}"
        if sel == 11:
            if var & 2:
                return "{" + s[0] + "}/{" + s[1] + "}"
            return (r"\tfrac" if var & 1 else r"\frac") + "{" + s[0] + "}{" + s[1] + "}"
        if sel in (12, 13):
            cmd = r"\underline" if sel == 12 else r"\overline"
            r = cmd + "{" + s[0] + "}"
            return cmd + "{" + r + "}" if var & 1 else r
        if sel == 14:
            return self.seta(t, ls, cs)
        if 15 <= sel <= 22:
            ch = _ch(cs[0]) if cs else None
            if ch not in OPERADORES:
                if ch is not None:
                    self.aviso(f"operador {ch!r} sem comando: usado \\mathop")
                    op = r"\mathop{" + ch + "}"
                else:
                    op = OPERADORES[OPERADOR_PADRAO[sel]]
            else:
                op = OPERADORES[ch]
            r = op + (r"\limits" if var & 0x40 else r"\nolimits")
            if s[2]:
                r += "_{" + s[2] + "}"
            if s[1]:
                r += "^{" + s[1] + "}"
            return r + " " + s[0] if s[0] else r
        if sel == 23:
            r = r"\mathop{" + s[0] + r"}\limits"
            return r + ("_{" + s[1] + "}" if s[1] else "") + ("^{" + s[2] + "}" if s[2] else "")
        if sel == 24:
            return (r"\overbrace{%s}^{%s}" if var & 1 else r"\underbrace{%s}_{%s}") % (s[0], s[1])
        if sel == 25:
            self.aviso("colchete horizontal aproximado por barra (sem \\underbracket portátil)")
            return (r"\overset{%s}{\overline{%s}}" if var & 1 else r"\underset{%s}{\underline{%s}}") % (s[1], s[0])
        if sel == 26:
            q = s[1] if var & 1 else ""
            return r"\left)\overset{" + q + r"}{\overline{" + s[0] + r"}}\right." if q else \
                r"\left)\overline{" + s[0] + r"}\right."
        if sel == 30:
            e = r"\left\langle " if var & 1 else r"\left. "
            d = r"\right\rangle" if var & 2 else r"\right."
            meio = r"\middle|" if var & 1 and var & 2 else ""
            if var & 1 and not var & 2:
                d = r"\right|"
            if var & 2 and not var & 1:
                e = r"\left|"
            return e + s[0] + meio + s[1] + d
        if sel == 31:
            seta = {1: "leftarrow", 2: "rightarrow", 3: "leftrightarrow"}.get(var & 3, "rightarrow")
            if var & 8:
                h = r"\leftharpoonup" if var & 1 and not var & 2 else r"\rightharpoonup"
                return (r"\underset{%s}{%s}" if var & 4 else r"\overset{%s}{%s}") % (h, s[0])
            return ("\\under" if var & 4 else "\\over") + seta + "{" + s[0] + "}"
        if sel == 32:
            return r"\widetilde{" + s[0] + "}"
        if sel == 33:
            return r"\widehat{" + s[0] + "}"
        if sel == 34:
            return r"\overset{\frown}{" + s[0] + "}"
        if sel == 35:
            return r"\overline{" + s[0] + r"\,|}"
        if sel == 36:
            if var & 1:
                self.aviso("risco horizontal aproximado por \\cancel (sem \\sout portátil)")
                return r"\cancel{" + s[0] + "}"
            cmd = {2: "cancel", 4: "bcancel", 6: "xcancel"}.get(var & 6, "cancel")
            return "\\" + cmd + "{" + s[0] + "}"
        if sel == 37:
            if var & 0x1E == 0x1E:
                return r"\boxed{" + s[0] + "}"
            r = s[0]
            if var & 8:
                r = r"\overline{" + r + "}"
            if var & 0x10:
                r = r"\underline{" + r + "}"
            if var & 6:
                r = (r"\left|" if var & 2 else r"\left.") + r + (r"\right|" if var & 4 else r"\right.")
            return r
        raise M.NaoSuportada(f"template seletor {sel}")  # R-MTEF-05

    def seta(self, t, ls, cs):
        """ArroBoxClass (seletor 14). Ordem dos rótulos: cima, baixo (MTEF.md §5, a confirmar D-09)."""
        var = t.var
        lab = [self.no(x) for x in ls]
        cima = lab[0] if var & 4 and lab else ""
        baixo = (lab[1] if len(lab) > 1 else lab[0] if not var & 4 and lab else "") if var & 8 else ""
        chars = [_ch(c) for c in cs]
        tipo = var & 3
        if tipo == 2:  # arpões
            dir_ = not chars or chars[0] in ("⇀", "⇁", "→")
            if not cima and not baixo:
                return r"\rightleftharpoons" if dir_ else r"\leftrightharpoons"
            cmd = r"\xrightleftharpoons" if dir_ else r"\xleftrightharpoons"
            return cmd + (f"[{baixo}]" if baixo else "") + "{" + cima + "}"
        if tipo == 1:  # seta dupla
            base = r"\rightleftarrows" if not chars or chars[0] == "→" else r"\leftrightarrows"
            if baixo:
                base = r"\underset{" + baixo + "}{" + base + "}"
            return r"\overset{" + cima + "}{" + base + "}" if cima else base
        cmd = {0x10: r"\xleftarrow", 0x20: r"\xrightarrow", 0x30: r"\xleftrightarrow"}.get(var & 0x30, r"\xrightarrow")
        return cmd + (f"[{baixo}]" if baixo else "") + "{" + cima + "}"


# --- MathML -----------------------------------------------------------------------------------
MML = "http://www.w3.org/1998/Math/MathML"


def E(tag, *filhos, texto=None, **at):
    el = etree.Element(tag, {k.replace("_", "-"): str(v) for k, v in at.items()})
    if texto is not None:
        el.text = texto
    for f in filhos:
        el.append(f)
    return el


class MathML:
    """Derivado da mesma árvore (ED-02). Cada token leva data-eqpress-typeface (MTEF.md §7)."""

    def __init__(self, eq):
        self.eq = eq

    def documento(self, raiz):
        m = E("math", self.no(raiz), xmlns=MML)
        return etree.tostring(m, encoding="unicode")

    def no(self, x):
        if x is None or isinstance(x, M.Linha):
            return E("mrow", *self.itens([] if _vazio(x) else x.itens))
        if isinstance(x, M.Pilha):
            return self.pilha(x)
        if isinstance(x, M.Matriz):
            return self.matriz(x)
        if isinstance(x, M.Tmpl):
            return self.tmpl(x)
        return E("mrow", *self.itens([x]))

    def itens(self, itens):
        out, pre, i = [], None, 0
        while i < len(itens):
            x = itens[i]
            if isinstance(x, M.Tmpl) and x.sel in (27, 28, 29):
                ls, _ = _slots(x)
                sub, sup = [None if _vazio(s) else self.no(s) for s in (ls + [None, None])[:2]]
                if x.var & 1:
                    pre = (sub, sup)
                else:
                    base = out.pop() if out else E("mrow")
                    out.append(self.script(base, sub, sup))
                i += 1
                continue
            if isinstance(x, M.Car):
                j = i + 1
                if _digito(x):  # número com separador decimal
                    while j < len(itens) and (_digito(itens[j]) or (
                            isinstance(itens[j], M.Car) and _ch(itens[j]) in (",", ".") and j + 1 < len(itens)
                            and _digito(itens[j + 1]))):
                        j += 1
                    el = E("mn", texto="".join(_ch(c) for c in itens[i:j]), data_eqpress_typeface=8)
                elif x.tf in (1, 12) or (x.tf == 2 and _letra(x)):
                    while j < len(itens) and isinstance(itens[j], M.Car) and itens[j].tf == x.tf \
                            and not itens[j].emb and (x.tf != 2 or _letra(itens[j])) and not itens[j].func:
                        j += 1
                    el = self.token(itens[i:j])
                else:
                    el = self.token([x])
                i = j
            else:
                el = self.no(x)
                i += 1
            if el is None:
                continue
            if pre:
                el = E("mmultiscripts", el, E("mprescripts"), pre[0] if pre[0] is not None else E("none"),
                       pre[1] if pre[1] is not None else E("none"))
                pre = None
            out.append(el)
        return out

    def script(self, base, sub, sup):
        if sub is not None and sup is not None:
            return E("msubsup", base, sub, sup)
        if sub is not None:
            return E("msub", base, sub)
        if sup is not None:
            return E("msup", base, sup)
        return base

    def token(self, cs):
        c = cs[0]
        tf = c.tf
        if tf == 23:
            return None
        if tf == 24:
            return E("mspace", width="0.1667em", data_eqpress_typeface=24)
        txt = "".join(_ch(k) or PUA.get(k.cod, "�") for k in cs)
        at = {"data_eqpress_typeface": tf}
        if tf in (1, 12, 9, 10) or tf < 0:
            el = E("mtext", texto=txt.replace(" ", "\xa0"), **at)
        elif tf == 2 and _letra(c):
            el = E("mi", texto=txt, mathvariant="normal", **at)
        elif tf == 7:
            el = E("mn" if txt.isdigit() else "mi", texto=txt, mathvariant="bold", **at)
        elif tf in (3, 4, 5) and txt.isalpha():
            el = E("mi", texto=txt, **({"mathvariant": "normal"} if tf == 5 else {}), **at)
        elif tf == 8 and txt.isdigit():
            el = E("mn", texto=txt, **at)
        elif tf == 22:
            el = E("mo", texto=txt, stretchy="true", **at)
        else:
            el = E("mo", texto=txt, **at)
        for e in c.emb:
            _, tipo, ch = EMBELEZ[e]
            if tipo == "over":
                el = E("mover", el, E("mo", texto=ch), accent="true")
            elif tipo == "under":
                el = E("munder", el, E("mo", texto=ch), accentunder="true")
            elif tipo == "sup":
                el = E("msup", el, E("mo", texto=ch))
            elif tipo == "pre":
                el = E("mmultiscripts", el, E("mprescripts"), E("none"), E("mo", texto=ch))
            else:
                el = E("menclose", el, notation=ch)
        return el

    def pilha(self, p):
        if p.halign == 4:
            linhas = []
            for ln in p.linhas:
                its = [] if _vazio(ln) else ln.itens
                k = next((n for n, x in enumerate(its) if isinstance(x, M.Car) and x.tf in (6, 11)
                          and _ch(x) in RELACOES), len(its))
                linhas.append(E("mtr", E("mtd", E("mrow", *self.itens(its[:k]))),
                                E("mtd", E("mrow", *self.itens(its[k:])))))
            return E("mtable", *linhas, columnalign="right left", columnspacing="0")
        al = {1: "left", 2: "center", 3: "right"}.get(p.halign, "right")
        return E("mtable", *[E("mtr", E("mtd", self.no(x))) for x in p.linhas], columnalign=al)

    def matriz(self, m):
        tipo = {0: "none", 1: "solid", 2: "dashed", 3: "dashed"}
        cel = [self.no(x) for x in m.celulas]
        lins = [E("mtr", *[E("mtd", c) for c in cel[r * m.cols:(r + 1) * m.cols]]) for r in range(m.lins)]
        at = {"columnalign": {1: "left", 2: "center", 3: "right"}.get(m.hjust, "center")}
        if any(m.part_lin[1:-1]):
            at["rowlines"] = " ".join(tipo[v] for v in m.part_lin[1:-1])
        if any(m.part_col[1:-1]):
            at["columnlines"] = " ".join(tipo[v] for v in m.part_col[1:-1])
        borda = [m.part_lin[0], m.part_lin[-1], m.part_col[0], m.part_col[-1]]
        tab = E("mtable", *lins, **at)
        if any(borda):
            lados = [n for n, v in zip(["top", "bottom", "left", "right"], borda) if v]
            tab = E("menclose", tab, notation=" ".join(lados))
        return tab

    def mo(self, ch, **at):
        return E("mo", texto=ch, **at)

    def tmpl(self, t):
        ls, cs = _slots(t)
        s = [self.no(x) for x in ls] + [E("mrow") for _ in range(4)]
        v = [_vazio(x) for x in ls] + [True] * 4
        sel, var = t.sel, t.var
        if sel <= 9:
            pares = {0: "⟨⟩", 1: "()", 2: "{}", 3: "[]", 4: "||", 5: "‖‖", 6: "⌊⌋", 7: "⌈⌉", 8: "⟦⟧"}
            if sel == 9:
                e, d = "()[]"[var & 3], "()[]"[(var >> 4) & 3]
            else:
                e, d = pares[sel]
                e, d = (e if var & 1 else ""), (d if var & 2 else "")
            filhos = [s[0]]
            if e:
                filhos.insert(0, self.mo(e, fence="true", stretchy="true"))
            if d:
                filhos.append(self.mo(d, fence="true", stretchy="true"))
            return E("mrow", *filhos)
        if sel == 10:
            return E("mroot", s[0], s[1]) if var == 1 and not v[1] else E("msqrt", s[0])
        if sel == 11:
            f = E("mfrac", s[0], s[1], **({"bevelled": "true"} if var & 2 else {}))
            return E("mstyle", f, displaystyle="false") if var & 1 else f
        if sel in (12, 13):
            r = s[0]
            for _ in range(2 if var & 1 else 1):
                r = (E("munder", r, self.mo("_", stretchy="true"), accentunder="true") if sel == 12
                     else E("mover", r, self.mo("‾", stretchy="true"), accent="true"))
            return r
        if sel == 14:
            seta = {0: "→", 1: "⇄", 2: "⇌"}[var & 3] if var & 3 else \
                {0x10: "←", 0x20: "→", 0x30: "↔"}.get(var & 0x30, "→")
            if (var & 3) and cs and _ch(cs[0]) in ("←", "↽"):
                seta = {1: "⇆", 2: "⇋"}[var & 3]
            cima = s[0] if var & 4 else None
            baixo = (s[1] if var & 4 else s[0]) if var & 8 else None
            op = self.mo(seta, stretchy="true")
            if cima is not None and baixo is not None:
                return E("munderover", op, baixo, cima)
            if cima is not None:
                return E("mover", op, cima)
            return E("munder", op, baixo) if baixo is not None else op
        if 15 <= sel <= 22:
            ch = _ch(cs[0]) if cs else OPERADOR_PADRAO[sel]
            op = self.mo(ch, largeop="true", movablelimits="false")
            tag = ("munderover", "munder", "mover") if var & 0x40 else ("msubsup", "msub", "msup")
            if not v[2] and not v[1]:
                op = E(tag[0], op, s[2], s[1])
            elif not v[2]:
                op = E(tag[1], op, s[2])
            elif not v[1]:
                op = E(tag[2], op, s[1])
            return E("mrow", op, s[0])
        if sel == 23:
            if not v[1] and not v[2]:
                return E("munderover", s[0], s[1], s[2])
            return E("munder", s[0], s[1]) if not v[1] else (E("mover", s[0], s[2]) if not v[2] else s[0])
        if sel in (24, 25):
            ch = ("⏞" if var & 1 else "⏟") if sel == 24 else ("⎴" if var & 1 else "⎵")
            if var & 1:
                return E("mover", E("mover", s[0], self.mo(ch, stretchy="true")), s[1])
            return E("munder", E("munder", s[0], self.mo(ch, stretchy="true")), s[1])
        if sel == 26:
            div = E("menclose", s[0], notation="longdiv")
            return E("mover", div, s[1]) if var & 1 else div
        if sel == 30:
            filhos = []
            if var & 1:
                filhos += [self.mo("⟨", fence="true"), s[0]]
            filhos.append(self.mo("|", fence="true"))
            if var & 2:
                filhos += [s[1], self.mo("⟩", fence="true")]
            return E("mrow", *filhos)
        if sel == 31:
            ch = {1: "←", 2: "→", 3: "↔"}.get(var & 3, "→")
            if var & 8:
                ch = "↼" if var & 1 and not var & 2 else "⇀"
            o = self.mo(ch, stretchy="true")
            return E("munder", s[0], o) if var & 4 else E("mover", s[0], o)
        if 32 <= sel <= 35:
            ch = {32: "~", 33: "^", 34: "⌢", 35: "‾"}[sel]
            r = E("mover", s[0], self.mo(ch, stretchy="true"), accent="true")
            return E("mrow", r, self.mo("|")) if sel == 35 else r
        if sel == 36:
            n = ["horizontalstrike"] if var & 1 else \
                [k for b, k in ((2, "updiagonalstrike"), (4, "downdiagonalstrike")) if var & b]
            return E("menclose", s[0], notation=" ".join(n) or "updiagonalstrike")
        if sel == 37:
            lados = [k for b, k in ((2, "left"), (4, "right"), (8, "top"), (0x10, "bottom")) if var & b]
            n = ("roundedbox" if var & 1 else "box") if len(lados) == 4 else " ".join(lados)
            return E("menclose", s[0], notation=n)
        raise M.NaoSuportada(f"template seletor {sel}")


def converter(mtef: bytes) -> Resultado:
    """MTEF → Resultado. Nunca levanta exceção: erro vai para Resultado.erro (CA-13)."""
    try:
        eq = M.ler(mtef)
        lx = Latex(eq)
        latex = lx.no(eq.raiz)
        mathml = MathML(eq).documento(eq.raiz)
        return Resultado(latex, mathml, lx.avisos)
    except M.NaoSuportada as e:
        return Resultado(None, None, [], str(e))
    except Exception as e:  # defeito do parser: também vai para o relatório, nunca some
        return Resultado(None, None, [], f"erro interno: {type(e).__name__}: {e}")
