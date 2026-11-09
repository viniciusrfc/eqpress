# PRESET — o "padrão" do EqPress

Schema formal: `PRESET_SCHEMA.json` (JSON Schema 2020-12). Exemplo que reproduz o padrão atual das
amostras: `exemplos/exemplo_atual_v1.json`.

## 1. Princípios

- **P-01** O preset é o único lugar onde mora a aparência. Mesma fonte (MathML) + mesmo preset →
  mesmo PDF, byte a byte, exceto metadados de data (para o cache por hash do O4).
  Fonte: OBSERVACAO-USUARIO §2 item 6, §3 O4.
- **P-02** Fontes = as do livro, instaladas no Mac. O EqPress recusa (erro, não aviso) qualquer
  família cujo nome contenha "MT Extra", "Euclid" ou outra fonte distribuída com o MathType.
  Fonte: OBSERVACAO-USUARIO §1, §4.
- **P-03** Fonte ausente no Mac → o lote falha antes de renderizar e lista as fontes faltantes
  (entra no relatório O4).

- **P-05** Fonte e corpo variam por livro (ex.: Calibri 10, Calibri 9 ou outra família); não existe
  um padrão global. Cada livro/coleção tem seu preset, calibrado no editor (EDITOR.md §3.1).
  Fonte: OBSERVACAO-USUARIO 2026-10-15.

## 2. Categorias (estilos)

9 categorias, ligadas 1:1 aos typefaces do MTEF (MTEF.md §4): `texto`, `funcao`, `variavel`,
`grego_min`, `grego_mai`, `simbolo`, `vetor_matriz`, `numero`, `extra`. Cada uma tem `familia`,
`peso` (normal/negrito), `italico` e, opcionalmente, `cor`.

Glifos que a família da categoria não tem (ex.: ∑, ⇌, delimitadores grandes) vêm de
`fonte_matematica` — uma fonte OpenType com tabela MATH (ex.: STIX Two Math, Latin Modern Math,
Libertinus Math, todas OFL). Fonte: OBSERVACAO-USUARIO §4, §5 (unicode-math).

### 2.1 As três camadas de fonte (equivalência com o MathType)

O MathType usa uma fonte padrão para o texto e recorre a **Symbol** e **MT Extra** para cobrir os
caracteres matemáticos (OBSERVACAO-USUARIO 2026-10-15; confirmado nas amostras: FONT_DEF Calibri,
Calibri Light, Symbol e MT Extra em 282/282 equações, COMPORTAMENTO §A.2). O EqPress reproduz a
mesma lógica em três camadas:

| Camada | No MathType (amostras) | No EqPress | Regra |
|---|---|---|---|
| 1. Fonte do livro | Calibri / Calibri Light | `categorias.*.familia` (texto, função, variável, número, vetor, extra) | escolhida por livro (P-05) |
| 2. Gregos e símbolos | Symbol | `categorias.grego_min/grego_mai/simbolo.familia` | pode ser **Symbol** (fonte do sistema macOS, `/System/Library/Fonts/Symbol.ttf`, não é do MathType), a fonte do livro ou outra |
| 3. Matemática "extra" (delimitadores que crescem, setas de química, ∑ ∫ grandes, espaços) | MT Extra | `fonte_matematica` | fonte OpenType MATH; **padrão: STIX Two Math**, que já vem no macOS (`/System/Library/Fonts/Supplemental/STIXTwoMath.otf`, licença OFL) |

- **P-06 Ordem de busca do glifo:** família da categoria → `fonte_matematica`. Se nenhuma tiver o
  glifo, é erro no relatório (nunca um quadrado vazio em silêncio).
- **P-07 MT Extra é proibida** como `familia` ou `fonte_matematica`, mesmo instalada no Mac (este
  Mac tem `mtextra_01.ttf`, `mtextra_02.ttf` e "Mt Extra Tiger" em ~/Library/Fonts): é fonte
  distribuída com o MathType (OBSERVACAO-USUARIO §1). Os caracteres que hoje saem da MT Extra
  (ex.: U+EC07/EC08, U+EF02, MTEF.md §6) são mapeados para Unicode e desenhados pela
  `fonte_matematica`.
- **P-08** Symbol tem codificação antiga (não Unicode). Se for escolhida, o renderizador mapeia
  Unicode → posição Symbol, e caracteres fora dela caem na `fonte_matematica` (P-06).
  **Implementado (2026-10-16):** a família "Symbol" usa a **Symbol do Windows** que vem com o
  Office (a mesma do MathType), por escolha do usuário ("as setas têm que vir de uma fonte de
  símbolo"; a Symbol do macOS desenha ⇒ → fino como a Arial). Tabela pública Adobe Symbol
  Encoding → U+F000+código; só vale a cópia com essas posições numa tabela Unicode (a do Office);
  sem Office, cai na Symbol do macOS. A ⇌ (que no MathType vinha da MT Extra) fica na STIX Two Math.
  **Windows (2026-10-17):** `C:\Windows\Fonts\symbol.ttf` só tem as tabelas 1,0 e 3,0, que o XeTeX
  não usa. O renderizador pede cada desenho pelo **número do glifo** (`\XeTeXglyph`) lido da tabela
  3,0, em caixas com a classe matemática certa e nos três tamanhos; comandos (`\Rightarrow`,
  `\alpha`…) e os caracteres literais até 255 (`+ = < > -`) apontam para essas caixas. A fonte não é
  modificada. Confirmado no Windows Server 2025 (GitHub Actions).

## 3. Tamanhos

`completo` em pt; os demais em pt ou % do completo: `subscrito`, `sub_subscrito`, `simbolo`
(operadores grandes), `sub_simbolo`. Fonte: DOC-PUBLICA:MTEF5 (typesizes), OBSERVACAO-USUARIO §4.

## 4. Espaçamentos

Os 30 parâmetros de espaçamento do MTEF (`linespace` … `horiz_fence_gap`), mesmos nomes da doc
pública, sem o prefixo `parm`. Ver valores atuais em COMPORTAMENTO.md §A.3.

Responsabilidade do renderizador (SESSÃO B): converter cada parâmetro para o motor tipográfico.
Parâmetros sem equivalente direto devem ser **listados** no relatório como "aproximados", nunca
ignorados em silêncio.

## 5. Cor

- Modelos aceitos: `cmyk` (0–100 por canal), `especial` (tinta nomeada + alternativa CMYK, para
  livros a 2 cores) e `cinza` (SPIKE:S5: sai só em K no InDesign, mas não é padrão; prefira `cmyk` 0/0/0/100). RGB **não existe** no schema, de propósito.
  Fonte: OBSERVACAO-USUARIO §2.1.
- `cores.padrao` vale para todas as categorias; `categorias.X.cor` sobrescreve.
- `cores.destaque`: cor usada quando a equação de origem tem cor não-preta.
- `sobreimpressao` (padrão `true`): o PDF da equação recebe ExtGState `/OP true /op true /OPM 1`
  aplicado a todo o conteúdo. Fonte: OBSERVACAO-USUARIO §2.1; SPIKE:S5 (variante `_op`: a sobreimpressão é preservada na exportação PDF/X-1a do InDesign).
- **P-04** O nome da tinta especial precisa ser **idêntico** ao do amostra de cor no InDesign;
  senão o InDesign cria uma segunda tinta. O script de vinculação compara e avisa.

## 6. Saída

- `formato`: `pdfx4` (padrão), `pdfx1a` ou `pdf` simples. É o arquivo vinculado no InDesign.
- `extras`: lista de saídas adicionais, gravadas ao lado do PDF com o mesmo nome:
  `eps` (gerado a partir do PDF, mesma cor/tinta e sobreimpressão, conferido por CA-06) e
  `emf` (para Word). Fonte: OBSERVACAO-USUARIO 2026-10-16 ("saídas em EPS, WMF"; escolhido
  "PDF + EPS + EMF" porque o WMF deforma, SPIKE:S1). Substitui o "nunca EPS" do briefing §2.1.
- `texto`: `contorno` (padrão: elimina dependência de fonte na gráfica e no Word) ou
  `fontes_embutidas` (subconjunto).
- `imagem_docx`: formato da imagem dentro do .docx. Padrão **`emf`** (SPIKE:S1: nítido no Word e no
  InDesign; WMF deforma). É só marcador de lugar; a cor final vem do PDF vinculado (INDESIGN VIN-00).

## 7. Texto vivo (O2)

`texto_vivo.regras`:

| Regra | Converte quando |
|---|---|
| `um_simbolo` | a equação é um único CHAR (ex.: *x*) |
| `numero` | só dígitos, vírgula/ponto e sinal |
| `numero_com_unidade` | número + espaço + texto (ex.: 3 cm, 12 m/s sem fração) |
| `variavel_igual_numero` | variável, `=`, número (ex.: x = 2) |
| `sem_templates` | qualquer sequência linear sem TMPL/PILE/MATRIX |

`texto_vivo.nunca` vence as regras. Cada conversão entra no relatório com o texto gerado e o
estilo de caractere aplicado. O texto vivo usa estilos de caractere **do InDesign**
(`estilo_caractere`/`estilos_por_categoria`), para que mudar o estilo no InDesign mude todas.

## 8. Versionamento (O3)

Arquivo `<nome>_v<versao>.json`; nunca se edita uma versão publicada, cria-se outra.
`baseado_em` permite herança de um nível (campos ausentes vêm do preset base). O JSON de cada
equação grava `preset: "<nome>_v<versao>"` e o hash do preset efetivo.

## 9. Preset a partir do MathType e do InDesign

- **De uma amostra .docx**: `eqpress preset --de-docx autor.docx` gera o preset a partir do
  EQN_PREFS (como em COMPORTAMENTO.md §A), trocando fontes MathType por `A DEFINIR`.
  Fonte: SPIKE:S0.
- **Do InDesign (O1)**: ver INDESIGN.md §7.

## 10. Decisões da SESSÃO B (F3, 2026-10-16)

Fonte: testes do F3 (tectonic 0.17 / XeTeX + unicode-math, Ghostscript 10.08, Inkscape 1.4) sobre AMOSTRA:todas.

- Motor: **tectonic (XeTeX)** — LuaLaTeX não está instalado (PLANO §4). Uma compilação por lote,
  uma página por equação; o PDF individual (editor) sai idêntico ao do lote, byte a byte (P-01).
- **Frações em tamanho cheio:** `\frac` é desenhado com numerador/denominador em estilo display
  (FracBox do MTEF); linhas de pilha e células de matriz levam `\displaystyle` no LaTeX canônico.
  Sem isso, expoentes dentro de frações caíam no sub_subscrito (0,8 pt, D-03) e sumiam.
- Fontes por categoria: letras, números e grego por **alfabeto inteiro** (o unicode-math não
  aceita faixa por código para alfanuméricos); se a família não cobre o alfabeto, ele fica na
  fonte_matematica (aviso). Símbolos e pontuação: faixa por código, só os que a família tem (P-06).
- **Delimitadores** ( ) [ ] { } | vêm sempre da fonte_matematica: com a fonte do livro,
  `\left(`/`\right)` não crescem. Parêntese digitado sai, portanto, da STIX Two Math (aproximado).
- Pastas de fontes: sistema → usuário → apps do Office; o sistema vence (a `symbol.ttf` do Office
  tem codificação antiga; a Symbol do macOS é Unicode, P-08 não é necessário).
- Espaçamentos traduzidos: linespace (`\arraystretch`, `\jot`, `\extrarowheight`), matrixcol
  (`\arraycolsep`), fractthick/fractthick2, operspacing/nonoperspacing (mu). Os outros 24 são
  listados como aproximados no relatório (§4).
- Cor: o PDF do TeX passa pelo Ghostscript (texto em contorno) e todo operador de cor é reescrito
  para a cor do preset (preto → `padrao`, outra → `destaque`); sobreimpressão via ExtGState; caixa
  = caixa do TeX ∪ tinta. Verificação: varredura de operadores + inkcov + tiffsep (CA-06/16).
- EPS: Ghostscript eps2write a partir do PDF final; Bounding/HiResBoundingBox reescritas para a
  caixa do PDF (mesma baseline); sem data. Tinta especial e `setoverprint` preservados (tiffsep).
- EMF: Inkscape a partir do PDF final (texto já em contorno).
- ⏳ `saida.formato` pdfx4/pdfx1a: ainda gera PDF simples, com aviso no relatório (falta decidir o
  perfil ICC da intenção de saída). O S5 mostrou que PDF simples colocado no InDesign já sai só em K.
- ⏳ `cores` por categoria (`categorias.*.cor`): recusado com erro até ser implementado.
