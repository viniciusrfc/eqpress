# MTEF — resumo para implementação (MTEF v5)

**Fonte principal:** DOC-PUBLICA:MTEF5 ("MathType MTEF v.5", Design Science, 1999), cópia pública em
<https://rtf2latex2e.sourceforge.net/MTEF5.html>. A versão atual em docs.wiris.com passou a exigir
login (verificado em 2026-10-14) e **não foi usada**. A cobertura no corpus vem do SPIKE:S0.

O parser deve ser escrito a partir deste documento e da spec pública, **sem** consultar código de
terceiros que implemente MTEF (decisão conservadora de clean room; ver Dúvidas).

## 1. Cabeçalho (após os 28 bytes OLE)

| Bytes | Campo | Corpus |
|---|---|---|
| 1 | versão MTEF | 5 (282/282) |
| 1 | plataforma (0 Mac, 1 Windows) | 1 |
| 1 | produto (0 MathType, 1 Equation Editor) | 0 |
| 1 | versão do produto | 7 |
| 1 | subversão | 4 |
| cstr | app key | `DSMT7` |
| 1 | opções da equação (bit 0 = inline) | ⚠ não confiável, ver FORMATO_DOCX_OLE R-DOCX-04 |

- **R-MTEF-01** Aceitar versão 5. Versões ≠ 5 → equação "não suportada" no relatório (nunca falha
  silenciosa). Fonte: DOC-PUBLICA:MTEF5, SPIKE:S0.

## 2. Codificação de valores

- Registro = byte de tipo + byte de opções (exceto END, que não tem opções; RULER também não tem).
- Inteiro sem sinal: 1 byte se < 255; senão `0xFF` + u16 LE.
- Inteiro com sinal (ex.: typeface): `v+128` em 1 byte; senão `0xFF` + u16 LE de `v+32768`.
- Unidades de dimensão: 1/32 pt.
- Nudge (opção `0x08`): 2 bytes (dx+128, dy+128), ou `128,128` seguidos de dx,dy em s16. Nenhum
  nudge no corpus, mas o parser precisa suportar (e o renderizador aplica o deslocamento).
- Arrays de dimensão (EQN_PREFS): 1 byte de contagem + "nibble stream": nibble de unidade
  (0 in, 1 cm, 2 pt, 3 pc, 4 %), dígitos (0–9, A = ".", B = "−") e F = fim; padding com 0.
- Leitores de arrays: guiar pela contagem; a mais → pular; a menos → padrão.

Fonte: DOC-PUBLICA:MTEF5.

## 3. Registros

| Tipo | Nome | Uso no corpus (SPIKE:S0) | Observação |
|---|---|---|---|
| 0 | END | — | fecha lista |
| 1 | LINE | 1 347 | opção 0x01 = linha nula (sem lista, sem END); 0x04 = espaçamento; 0x02 = RULER |
| 2 | CHAR | 4 592 | typeface + MTCode (u16) + [pos. 8 bits 0x04 / 16 bits 0x10]; 0x20 = sem MTCode; 0x01 = embelezamentos; 0x02 = início de função |
| 3 | TMPL | 499 | seletor, variação (1–2 bytes: se bit 0x80, `(b1&0x7F)|(b2<<8)`), opções do template, sub-objetos |
| 4 | PILE | 41 | halign, valign, [RULER], linhas |
| 5 | MATRIX | 6 | valign, h_just, v_just, linhas, colunas, partições (2 bits cada, (n+1) valores, arredondado a bytes), células em ordem linha a linha |
| 6 | EMBELL | 0 | tipos 2–37 (pontos, linhas, setas, til, chapéu…) |
| 7 | RULER | 0 | n paradas: tipo (0 esq,1 centro,2 dir,3 igual,4 decimal) + offset u16 |
| 8 | FONT_STYLE_DEF | 1 | índice FONT_DEF + estilo (bit0 negrito, bit1 itálico) |
| 9 | SIZE | 0 | lsize/dsize; 101 = tamanho explícito; 100 = delta grande |
| 10–14 | FULL/SUB/SUB2/SYM/SUBSYM | 748 | tamanho lógico corrente |
| 15 | COLOR | 246 | índice COLOR_DEF (⚠ índice 0 aparece 68×: tratar como "cor padrão") |
| 16 | COLOR_DEF | 128 | RGB ou CMYK (opção 0x01), spot (0x02), nome (0x04); valores u16 0–1000 |
| 17 | FONT_DEF | 1 129 | índice ENCODING_DEF + nome |
| 18 | EQN_PREFS | 282 | tamanhos, espaçamentos, estilos (= o "padrão" atual, ver COMPORTAMENTO.md) |
| 19 | ENCODING_DEF | 282 | nome; índices 1–4 predefinidos (MTCode, Unknown, Symbol, MTExtra) |
| ≥100 | FUTURE | 0 | seguido de uint de tamanho → pular |

- **R-MTEF-02** Tipos 20–99 desconhecidos → equação não suportada + byte offset no relatório.
  Fonte: DOC-PUBLICA:MTEF5.
- **R-MTEF-03** Definições são indexadas a partir de 1 na ordem do stream (ENCODING_DEF a partir de 5).
- **R-MTEF-04** Cor da equação de origem: o corpus traz `COLOR_DEF RGB(0,0,0)` em 127 equações e
  `RGB(1000,0,0) "Red"` em 1. O preset decide a cor de saída; a cor de origem só serve para
  **preservar destaques intencionais** (não-preto → categoria de cor "destaque" do preset).
  Fonte: SPIKE:S0, OBSERVACAO-USUARIO §2.1.

## 4. Typefaces (estilos)

Valor positivo = estilo; negativo = fonte explícita (FONT_STYLE_DEF −n).

| Valor | Estilo | Categoria do preset | Corpus |
|---|---|---|---|
| 1 | fnTEXT | texto | 257 |
| 2 | fnFUNCTION | funcao | 351 |
| 3 | fnVARIABLE | variavel | 1 089 |
| 4 | fnLCGREEK | grego_min | 16 |
| 5 | fnUCGREEK | grego_mai | 18 |
| 6 | fnSYMBOL | simbolo | 983 |
| 7 | fnVECTOR | vetor_matriz | 4 |
| 8 | fnNUMBER | numero | 1 534 |
| 9/10 | fnUSER1/2 | extra | 0 |
| 11 | fnMTEXTRA | simbolo (mapeado p/ Unicode) | 10 |
| 12 | fnTEXT_FE | texto | 0 |
| 22 | fnEXPAND | delimitador extensível | 201 |
| 23 | fnMARKER | ignorar (marcador) | 0 |
| 24 | fnSPACE | espaço | 128 |
| −1 | fonte explícita | texto, com aviso | 1 |

## 5. Templates (TMPL)

Ordem dos sub-objetos por classe (DOC-PUBLICA:MTEF5 "Template subobject order"):

| Classe | Ordem |
|---|---|
| ParBoxClass | conteúdo, delimitador esq. (opcional), delimitador dir. (opcional) |
| RootBoxClass | radicando, índice |
| FracBoxClass | numerador, denominador |
| ScrBoxClass | subscrito, sobrescrito (ambos presentes; ausente = LINE nula) |
| BigOpBoxClass | principal, superior, inferior, caractere do operador |
| LimBoxClass | principal, inferior, superior |
| HFenceBoxClass | principal, rótulo, caractere da chave |
| ArroBoxClass | rótulo de cima, rótulo de baixo, (seta) — ver nota |
| LDivBoxClass | dividendo, quociente |
| DiracBoxClass | esquerda, direita, ⟨ (opc.), \|, ⟩ (opc.) |
| SlashBoxClass | numerador, denominador |

Nota ArroBoxClass: a doc pública lista "main slot / arrow character"; a variação define slots de
cima/baixo (tvAR_TOP 0x04, tvAR_BOTTOM 0x08). Confirmar a ordem exata com uma equação de teste
(SPIKE:S6, pendente) — as 4 setas do corpus são de química (⇌ com rótulo).

Seletor → MathML (proposta) e cobertura:

| Sel | Nome | Corpus | MathML |
|---|---|---|---|
| 0–8 | ANGLE PAREN BRACE BRACK BAR DBAR FLOOR CEILING OBRACK | PAREN 69, BAR 12, BRACK 10, BRACE 8 (só esq. = sistema) | `<mrow><mo fence stretchy>…</mo>…</mrow>` |
| 9 | INTERVAL | 0 | idem, delimitadores pela variação |
| 10 | ROOT (0 quadrada, 1 n-ésima) | 22 | `msqrt` / `mroot` |
| 11 | FRACT (0x01 pequena, 0x02 barra /, 0x04 base) | 151 | `mfrac` (bevelled se 0x02) |
| 12/13 | UBAR/OBAR (0x01 dupla) | 0 | `munder`/`mover` + `‾` |
| 14 | ARROW | 4 (var 0x0d, 0x0e) | `munderover` com `mo` esticável |
| 15 | INTEG | 0 | `msubsup`/`munderover` + `∫∬∭∮` |
| 16–22 | SUM PROD COPROD UNION INTER INTOP SUMOP | 0 | `munderover` (0x40) ou `msubsup` |
| 23 | LIM | 0 | `munder`/`munderover` |
| 24/25 | HBRACE/HBRACK (0x01 em cima) | 3 | `munder`/`mover` + `⏟`/`⏞` |
| 26 | LDIV | 0 | `mlongdiv` (MathML 3) ou fallback |
| 27/28/29 | SUB SUP SUBSUP (0x01 pré-script) | 86/127/7 | `msub`/`msup`/`msubsup`/`mmultiscripts` |
| 30 | DIRAC | 0 | `mrow` ⟨ \| ⟩ |
| 31 | VEC | 0 | `mover` + `→` |
| 32–35 | TILDE HAT ARC JSTATUS | 0 | `mover` + acento |
| 36 | STRIKE | 0 | `menclose` |
| 37 | BOX | 0 | `menclose` |

- **R-MTEF-05** Todos os seletores 0–37 devem ser suportados (não só os do corpus), cada um com
  teste. Seletor > 37 → não suportada + relatório. Fonte: DOC-PUBLICA:MTEF5, OBSERVACAO-USUARIO §7 F2.

## 6. Caracteres

- MTCode = superconjunto de Unicode. Fora da faixa de uso privado (PUA, U+E000–U+F8FF), o MTCode é
  usado como Unicode diretamente. Fonte: DOC-PUBLICA:MTEF5.
- Corpus: 110 códigos distintos. Códigos de uso privado encontrados (SPIKE:S0):

| MTCode | Typeface | Ocorr. | Contexto observado | Mapeamento proposto | Fonte |
|---|---|---|---|---|---|
| U+EF02 | fnSPACE | 128 | entre tokens | espaço fino (`mspace`) — **largura a confirmar** | AMOSTRA (inferência) |
| U+EC07 / U+EC08 | fnEXPAND | 12/12 | delimitadores esq./dir. do template BAR | `|` esticável | AMOSTRA (inferência pelo template) |

  A tabela pública "MTCode Encoding Tables" não está mais acessível sem login. **R-MTEF-06**:
  todo MTCode em PUA sem mapeamento conhecido → glifo de substituição visível + aviso no relatório.
- **R-MTEF-07** Nunca usar MT Extra, Symbol (para glifos) ou outra fonte do MathType na saída; os
  caracteres são renderizados nas fontes do preset. Fonte: OBSERVACAO-USUARIO §1, §4.

## 7. Mapeamento MTEF → MathML (regras gerais)

- LINE → `<mrow>`; PILE → `<mtable>` de 1 coluna com `columnalign` pelo halign (4 = alinhar no
  relacional → `mtable` com `maligngroup`/2 colunas); MATRIX → `<mtable>` com
  `rowlines`/`columnlines` a partir das partições.
- CHAR: typeface 3/4/5 → `<mi>`; 8 → `<mn>`; 6/11 e operadores → `<mo>`; 1 → `<mtext>`;
  2 com início de função (0x02) → `<mi mathvariant="normal">` agrupando até o fim da sequência de
  função; 22 → `<mo stretchy="true">`; 24 → `<mspace>`.
- O MathML gerado leva `data-eqpress-typeface="N"` (ou atributo de classe) em cada token para o
  renderizador aplicar a categoria do preset, já que MathML puro não carrega "estilo MathType".
- Tamanho lógico (FULL/SUB/SUB2/SYM/SUBSYM) é registrado por token; o renderizador aplica os
  tamanhos do preset. SUB/SUB2 implícitos em scripts seguem o preset, não o arquivo.
- Embelezamentos → `mover`/`munder` com o caractere de acento correspondente.

O MathML é o formato-fonte persistido (`/equacoes/0042.json`); a conversão para LaTeX
(renderizador) parte dele.

## 8. Decisões da SESSÃO B (F2, 2026-10-16)

Fonte: AMOSTRA:todas (inventário do conversor) + DOC-PUBLICA:MTEF5 + teste de portabilidade em
KaTeX 0.16.11 e MathJax 3.2.2 (`ferramentas/web/verificar.js`).

- §7 está superado por ED-01/ED-02: LaTeX e MathML saem **ambos da árvore**; LaTeX é o canônico.
- Registros sem byte de opções (conforme o exemplo da doc pública): FONT_DEF, ENCODING_DEF,
  FONT_STYLE_DEF, SIZE, FULL…SUBSYM, COLOR. Com opções: LINE, CHAR, TMPL, PILE, MATRIX, EMBELL,
  COLOR_DEF, EQN_PREFS. Assim as 282 equações são lidas até o último byte.
- O slot principal de uma cerca pode ser um PILE direto (chave de sistema, 8 casos), não só LINE.
- As 4 setas do corpus têm rótulos **vazios** (⇌/⇄ simples); a ordem cima/baixo continua a confirmar (D-09).
- Mapeamento por estilo: variável → letra; número → dígito; função → `\mathrm{}` (`\operatorname{}`
  só com FUNC_START e sem letra colada); texto e fonte explícita → `\text{}` (espaço = `\ `);
  vetor → `\mathbf{}`; fnSPACE U+EF02 → `\,`; vírgula entre dígitos → `{,}`.
- Palavra com letra acentuada em estilo variável → `\text{}` (KaTeX recusa em modo matemático).
- Sem equivalente portável (aviso no relatório): `\overbracket`/`\underbracket` (seletor 25),
  `\sout` (seletor 36 horizontal, embelezamento 16), `\dddot`/`\ddddot` (embelez. 4 e 24 viram
  `\overset{...}{}`), `\overrightharpoon` (vira `\overset{\rightharpoonup}{}`).
- Cor ≠ preto → `\textcolor{<nome-base>}{}`; nenhuma equação do corpus usa cor (o "Red" é só definido).
- O LaTeX deve ser renderizado em **modo display** (como o MathType desenha frações em linha);
  o F3 aplica isso, e o uso web também deve usar display.
