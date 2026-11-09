# COMPORTAMENTO — casos entrada → saída

Duas partes: (A) o "padrão" atual, decodificado das amostras; (B) casos que o usuário vai
descrever (prints/PDFs). A parte B fica **em aberto** até o usuário enviar o material.

## A. Padrão atual observado nas amostras (EQN_PREFS)

Duas variantes no corpus; diferem só no tamanho "completo" (Fonte: SPIKE:S0, AMOSTRA:todas):

| Variante | Equações | Completo |
|---|---|---|
| P1 | 157 | 9 pt |
| P2 | 125 | 10 pt |

### A.1 Tamanhos (ordem da doc pública: completo, subscrito, sub-subscrito, símbolo, sub-símbolo, usuário 1, usuário 2, incremento)

| Item | Valor decodificado | Situação |
|---|---|---|
| Completo | 9 pt / 10 pt | ok |
| Subscrito | 7 pt | ok |
| Sub-subscrito | **8 %** | usuário (2026-10-15, D-03): "8 %, vamos testar". Validar na prova visual O5 contra a prévia WMF |
| Símbolo | **11 %** | ⚠ idem |
| Sub-símbolo | 9 pt | confirmar |
| Usuário 1 | 75 % | |
| Usuário 2 | 150 % | |
| Incremento | 1 pt | |

O decodificador foi conferido contra o exemplo da doc pública ("12 pt, 58 %, 42 %, 150 %…"), então
os valores acima são os que estão gravados. Ou o padrão do livro tem esses números mesmo, ou a
ordem dos tamanhos no MathType 7 difere da doc de 1999. A resposta do usuário (D-03) decide.

### A.2 Estilos (FONT_DEF: 1 Calibri, 2 Symbol, 3 Calibri Light, 4 MT Extra)

| Estilo | Fonte | Negrito | Itálico |
|---|---|---|---|
| Texto | Calibri | não | não |
| Função | Calibri | não | não |
| Variável | Calibri | não | **não** |
| Grego minúsculo | Symbol | não | não |
| Grego maiúsculo | Symbol | não | não |
| Símbolo | Symbol | não | não |
| Vetor/matriz | Calibri | **sim** | não |
| Número | Calibri | não | não |
| Usuário 1 | Calibri Light | não | não |
| Usuário 2 | Calibri Light | não | não |
| MT Extra | MT Extra | não | não |

Observação: variável **sem itálico** é escolha editorial do padrão atual (não é o padrão de fábrica).
O preset de migração (`exemplo_atual.json`) deve reproduzir isso, trocando Symbol/MT Extra por uma
fonte do livro com cobertura matemática (Dúvida D-04).

### A.3 Espaçamentos (iguais em P1 e P2)

| Parâmetro | Valor | Parâmetro | Valor |
|---|---|---|---|
| LINESPACE (linhas) | 150 % | FRACTGAP (fração inclinada) | 8 % |
| MATRIXROW | 150 % | FENCEOVER (delimitador) | 8 % |
| MATRIXCOL | 100 % | OPERSPACING | 100 % |
| SUPHEIGHT (sobrescrito) | 45 % | NONOPERSPACING | 100 % |
| SUBDEPTH (subscrito) | 25 % | CHARWIDTH | 0 % |
| SUBSUPGAP | 8 % | MINGAP | 8 % |
| LIMHEIGHT | 25 % | VRADGAP (radical vertical) | 17 % |
| LIMDEPTH | 100 % | HRADGAP (radical horizontal) | 8 % |
| LIMSPACE | 100 % | RADWIDTH | 100 % |
| FRACTHEIGHT (numerador) | 35 % | EMBELLGAP | 12,5 % |
| FRACTDEPTH (denominador) | 100 % | PRIMEHEIGHT | 45 % |
| FRACTOVER (sobra da barra) | 8 % | BOX_STROKE_THICK | 5 % |
| FRACTTHICK (barra) | 5 % | STRIKE_THRU_THICK | 5 % |
| FRACTTHICK2 (barra em fração pequena) | 2,5 % | MATRIX_PART_THICK | 5 % |
| RAD_THICK | 5 % | HORIZ_FENCE_GAP | 10 % |

Percentuais relativos ao tamanho completo, como na doc pública. Esses 30 valores entram 1:1 no
preset (PRESET.md §4); o renderizador converte para a métrica do motor tipográfico.

### A.4 Cor

127 equações declaram preto **RGB(0,0,0)**; 1 declara vermelho RGB. Hipótese a confirmar no S5: o
preto RGB na origem é a causa do preto composto que chega ao InDesign (Fonte: SPIKE:S0 +
OBSERVACAO-USUARIO §0 item 6).

### A.5 Cor por contexto (livro diagramado)

No PDF de gráfica de matemática (AMOSTRA:"paginas_grafica.pdf"), a cor da equação depende de **onde** ela está, não da categoria:

| Contexto | Cor esperada | Cor medida hoje |
|---|---|---|
| Enunciado | preto 100 % K | **C73 M68 Y67 K89** ✘ |
| Resolução / resposta | PANTONE 219 C (100 %) | PANTONE 219 C, sem outras tintas ✔ (EPS refeitos no Illustrator) |

Fonte: SPIKE:S5b. No .docx, o contexto já vem separado por arquivo
(`*_somente_questoes.docx` × `*_somente_resolucoes.docx`), então a solução é **um preset por
contexto**: `livroX_v1.json` (100 % K) e `livroX_resolucao_v1.json` com
`baseado_em: livroX_v1` e `cores.padrao` = tinta especial "PANTONE 219 C". Nenhum campo novo no
schema. Se o mesmo .docx misturar contextos, ver Dúvida D-11.

## B. Casos do usuário (a preencher)

Formato de cada caso:

```
### CASO-NN — <título>
Entrada: AMOSTRA:<arquivo>, equação EQ-NNNN (ou print)
Saída atual (MathType + padrão): <print/PDF>
Saída esperada do EqPress: <o que deve ser igual / o que deve mudar>
Tolerância: <ex.: largura ±2 %, baseline ±0,1 pt>
```

Casos mínimos pedidos ao usuário (Dúvida D-01): fração aninhada, raiz com índice, sistema com chave,
matriz 2×6 (existe no corpus), equação química com ⇌ e rótulos, chave horizontal com rótulo, valor
com unidade ("12 m/s"), equação de uma letra só (candidata ao O2), equação com destaque em cor.
