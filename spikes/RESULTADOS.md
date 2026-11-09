# RESULTADOS DOS SPIKES

Status: ✅ concluído · 🟡 parte automática feita, aguardando teste do usuário · ⬜ não iniciado

Arquivos de teste: `spikes/out/testes/` (regerar com
`.venv/bin/python spikes/s1_s5_gerar/gerar.py`; requer `tectonic`, `gs`, `inkscape`).

---

## S0 — Inventário do corpus ✅

`spikes/s0_corpus/analisar_corpus.py samples/*.docx`

- 282 equações, 282 parseadas sem erro com um parser escrito a partir da doc pública do MTEF5.
- Todas: `Equation.DSMT4`, MTEF v5, MathType 7.4 Windows, app key `DSMT7`, prévia WMF, cabeçalho
  OLE de 28 bytes.
- Templates usados: FRACT 151, SUP 127, SUB 86, PAREN 69, ROOT 22, BAR 12, BRACK 10, BRACE 8
  (sistemas), SUBSUP 7, ARROW 4, HBRACE 3. Matrizes: 6 (2×6, 1×8, 2×8). Piles: 41.
- Sem nudges, embelezamentos ou registros futuros.
- O bit "inline" do MTEF não bate com a posição no Word (227/282 marcadas "display").
- Padrão atual decodificado do EQN_PREFS: ver spec/COMPORTAMENTO.md §A.

**Decisão:** o corpus atual cobre ~1/3 dos templates. A SESSÃO B precisa de equações sintéticas
para os outros (integrais, somatórios, limites, acentos, setas…), geradas **pelo usuário** no
MathType (Dúvida D-09), porque não podemos gerar MTEF "como o MathType gera" sem o MathType.

---

## Ambiente dos testes do usuário (2026-10-15)

InDesign 2024 (19.4, macOS), conforme o caminho dos vínculos na sonda e o Creator do PDF do S4.
Arquivo da sonda: `spikes/out/testes/eqpress_sonda.tsv` (9 gráficos: S2 + S3).

## S1 — Formato da imagem no .docx ✅ (decidido)

Gerados: `S1_emf.docx`, `S1_wmf.docx`, `S1_svg.docx` (SVG + PNG 96 dpi de reserva),
`S1_png1200.docx`, `S1_pdf.docx` (PDF direto no `a:blip`, experimental). Cada um com 3 equações
(fórmula de Bhaskara, ¾ inline, "v₀ = 12 m/s"). Texto em contorno em EMF/WMF/SVG.

Observado aqui (sem InDesign):
- EMF 13,7 KB, WMF 3,4 KB, SVG 12 KB para a mesma equação. WMF tem coordenadas inteiras de baixa
  resolução, esperado perder qualidade.

**Resultado do usuário:** todos abrem no Word; só o **WMF fica deformado**. Todos entram no
InDesign com boa resolução.

**Achado da sonda (decisivo):** o InDesign 2024 importa as imagens do .docx como gráfico **incorporado**
do tipo `WMF`, formato "Metarquivos avançados do Windows" (EMF), com nome de vínculo inventado
(`ImageNNN.EPS`, caminho falso dentro do app). É isso que vira ".eps" quando o usuário desincorpora.
Metarquivo do Windows é RGB, então o preto sai composto na exportação, seja qual for o formato
posto no .docx.

**Decisão:** `imagem_docx = emf`. Fica nítido no Word e entra no InDesign. A cor certa (100 % K) vem
**obrigatoriamente** da troca pelo PDF vinculado feita pelo script "Vincular equações". A imagem do
.docx é só um marcador de lugar com o tamanho certo. WMF descartado (deforma).

Roteiro original (para referência):
1. Abrir cada `S1_*.docx` no Word: abre? Mostra a equação? (anotar)
2. No InDesign: Arquivo > Inserir com as opções de hoje.
3. Para cada formato: a equação aparece? É vetor (ampliar 800 %)? Tamanho igual ao do Word?
   O painel Vínculos mostra o quê?
4. Exportar PDF de gráfica e conferir nitidez.

| Formato | Word abre | InDesign importa | Vetor | Tamanho ok | Observações |
|---|---|---|---|---|---|
| EMF | | | | | |
| WMF | | | | | |
| SVG (+PNG) | | | | | |
| PNG 1200 | | | | | |
| PDF | | | | | |

---

## S2 — Baseline ✅

`S2_baseline.docx`: a mesma fração ¾ com `w:position` 0, −1, −2, −3,5, −5 pt.
Profundidade real da fração (do TeX): 3,44 pt → o valor "certo" no Word seria −3,5 pt (arredondado
a 0,5 pt).

**Achado:** `w:position` só aceita meios-pontos → precisão de 0,5 pt no Word. O critério de
≤ 0,1 pt só é alcançável no InDesign, pelo script (spec/INDESIGN.md §4).

**Resultado (sonda):** o `w:position` chega como **deslocamento de linha de base** (`baselineShift`)
do caractere-âncora, mas truncado a pontos inteiros:

| w:position | esperado | baselineShift no InDesign |
|---|---|---|
| 0 | 0 | 0 |
| −1 pt | −1 | **0** |
| −2 pt | −2 | −2 |
| −3,5 pt | −3,5 | **−3** |
| −5 pt | −5 | −5 |

Tamanho do quadro = tamanho do `wp:extent` (diferença ≤ 0,04 pt). O fundo do quadro fica na
baseline deslocada.

**Decisão:** o `.docx` leva o `w:position` aproximado só para a aparência no Word; o script
"Vincular equações" **sobrescreve** o `baselineShift` com o valor exato do JSON (BL-02).

Roteiro original: Quero saber se o deslocamento chega como `baselineShift` (coluna
`desloc_baseline_char`) ou de outra forma.

---

## S3 — Identificador que sobrevive ✅

`S3_identificador.docx`: quatro equações, cada uma com o ID em **um só** canal:
EQ-0101 só no nome do arquivo (`word/media/EQ-0101.emf`), EQ-0102 só em `docPr/@name`,
EQ-0103 só em `docPr/@descr` (texto alternativo), EQ-0104 só em `docPr/@title`.

**Roteiro do usuário:** importar e rodar `sondar.jsx` (mesmo TSV do S2). A sonda lista nome do
link, rótulo, nome do quadro e texto alternativo.

| Canal | Sobrevive? | Onde aparece no InDesign |
|---|---|---|
| nome do arquivo | ✘ | o InDesign renomeia para `ImageNNN.EPS` |
| docPr/@name | ✘ | — |
| docPr/@descr | ✔ | texto alternativo do quadro: `objectExportOptions.customAltText` = "EQ-0103" |
| docPr/@title | ✘ | — |

**Decisão:** o ID vai em `docPr/@descr` (texto alternativo). O script lê
`frame.objectExportOptions.customAltText`.

---

## S4 — Preservar o OLE e trocar só a prévia 🟡 (viável, não adotado)

`S4_ole_previa_trocada.docx`: cópia de `corpus_mt_questoes.docx` em que **apenas** a
prévia da 1ª equação (`word/media/image2.wmf`) foi trocada pelo WMF do EqPress (Bhaskara); o
`oleObject` continua o original.

**Resultado (PDF do usuário, InDesign 19.4 Mac):** a prévia trocada aparece no lugar da 1ª equação,
mas (a) o WMF gerado pelo Inkscape sai com traço grosso e deformado (mesmo defeito do S1) e (b) é
esticado para a caixa original do objeto. Com EMF e caixa ajustada funcionaria, mas não resolve a
cor (continua metarquivo RGB). **Não adotado**; manter o OLE só importaria para reabrir no MathType,
o que o projeto quer eliminar.

**Achado colateral:** no mesmo PDF, as equações **originais** do MathType (não tocadas) mostram o
sinal de menos como **□** (glifo ausente), por ex. alternativas A e D ("□3/4", "□4/3"). A prévia WMF
do MathType chama fontes (Symbol/MT Extra) que o InDesign Mac não resolve igual ao Windows. É mais
um defeito do fluxo atual no Mac que o EqPress elimina (texto em contorno no PDF).

Roteiro original:
1. Abrir no Word **sem** clicar na equação: aparece a Bhaskara (nova) ou a original?
2. Salvar no Word, fechar, reabrir: a prévia nova se manteve?
3. Importar no InDesign: o que entra?
4. (Se tiver MathType por perto) clicar duas vezes: o MathType abre a equação original — esperado.

---

## S5 — Cor na separação ✅

PDFs gerados (`spikes/out/testes/S5_*.pdf`), mesma equação, cores reescritas no conteúdo:

| Arquivo | Operadores de cor | inkcov C/M/Y/K (%) |
|---|---|---|
| S5_EQ-0001_k100.pdf | só `0 0 0 1 k/K` | 0 / 0 / 0 / 0,121 |
| S5_EQ-0001_k100_op.pdf | `0 0 0 1 k/K` + ExtGState OP/op/OPM 1 | 0 / 0 / 0 / 0,121 |
| S5_EQ-0001_gray.pdf | só `0 g/G` | 0 / 0 / 0 / 0,121 |
| S5_EQ-0001_rgb.pdf | só `0 0 0 rg/RG` | 0,121 / 0,121 / 0,121 / 0,121 |

**Achados:**
1. Pedir `\color[cmyk]{0,0,0,1}` no LaTeX **não basta**: o driver (xdvipdfmx) intercala `0 g`/`0 G`
   (DeviceGray) por conta própria. O renderizador precisa normalizar ou validar os operadores
   depois de gerar. ✔ confirma a regra "não confiar no black padrão".
2. O `inkcov` do Ghostscript mostra DeviceGray como só K, então ele não distingue Gray de CMYK. A
   QA precisa de duas checagens: inkcov **e** varredura de operadores/espaços de cor (CA-06).
3. RGB (0,0,0) vira C=M=Y=K → preto composto, como o problema relatado.
4. O PDF "Resolução" das amostras é RGB (PDF digital) e não serve para separação. ~~Não há EPS~~ →
   o usuário forneceu EPS e um PDF de gráfica em 2026-10-15 (abaixo).

### S5 no InDesign — PDFs colocados direto (2026-10-15) ✅

O usuário colocou os 4 PDFs (Arquivo > Colocar) numa página e exportou
`spikes/out/testes/teste100k.pdf` (InDesign 19.4 Mac, PDF/X-1a:2001, intenção de saída
"Japan Web Coated (Ad)"). As 4 equações ficam empilhadas; cada uma foi identificada pelo operador
que sobrou no conteúdo exportado:

| Posição | Origem (identificada por) | Operadores no PDF exportado | Chapas (gs tiffsep) | Sobreimpressão |
|---|---|---|---|---|
| 1ª (topo) | rgb (preto composto) | `0.839 0.83 0.729 0.797 k/K` | C, M, Y **e** K | não |
| 2ª | k100 | `0 0 0 1 k/K` | só K | não (GS0 OP false) |
| 3ª | k100_op | `0 0 0 1 k/K` + GS1 `/OP true /op true /OPM 1` | só K | **sim, preservada** |
| 4ª | gray | `/DeviceN [/Black]` 1 | só K | não |

Página inteira, inkcov: C 0,0005 / M 0,0005 / Y 0,0005 / K 0,002; a tinta C/M/Y aparece só na faixa
da 1ª equação (bbox idêntica nas três chapas).

**Decisões:**
1. ✔ PDF em `0 0 0 1 k/K` atravessa o InDesign e a exportação X-1a **só em K**: confirma o caminho
   do EqPress (INDESIGN VIN-00).
2. ✔ O ExtGState de sobreimpressão do PDF da equação é **preservado** na exportação → manter
   `cores.sobreimpressao = true` como padrão (PRESET §5).
3. DeviceGray vira tinta Black (só K) no InDesign, mas sem ganho sobre CMYK e dependente das
   configurações de conversão de cor. O modelo `cinza` continua no schema, **não é padrão**, e a QA
   (CA-06) segue exigindo `0 0 0 1 k/K` com preset 100 % K.
4. RGB vira preto composto (C84 M83 Y73 K80 com esse perfil), o mesmo defeito do fluxo atual →
   RGB continua fora do schema e é erro na QA.

Pendente (não bloqueia): conferir se o Preflight acusa a 1ª equação (perfil `.idpp`, INDESIGN §8).

### S5b — EPS atuais e PDF de gráfica (amostras de 2026-10-15) ✅

Ferramenta: `spikes/s5_eps/separar.py` (Ghostscript `tiffsep`, cobertura por chapa, incluindo
tintas especiais).

- `eq_composta.EPS` (equação, Illustrator 24): **preto composto** C 5,7 / M 4,9 / Y 3,9 / K 6,1 %
  de cobertura; cor única `.911711 .786862 .619532 .974487 cmyk`.
- `eq*_pan.eps` (9 equações): **só PANTONE 219 C**, nenhuma outra chapa.
- `MAT*` (figuras): CMYK intencional; o preto já é `0 0 0 1`.
- PDF "paginas_grafica.pdf" (InDesign 15.1 Windows, 14 p., sem PDF/X): separado página
  a página e restrito à TrimBox:
  - Equações de **resolução** (caixas "Resolução", respostas inline): só PANTONE 219 C; em 0 pixels
    a Pantone se sobrepõe a C, M, Y ou K. ✔
  - Equações de **enunciado** em preto (ex.: "√3 m", "√3 = 1,73", "10√2", "600√2" na p. 701):
    **C73 M68 Y67 K89**, preto composto de 297 % de tinta. ✘ É exatamente o problema relatado,
    agora medido.
  - Texto vivo do InDesign: 100 % K.
- Conclusão: o defeito está nas equações em preto; a solução atual para as coloridas (EPS refeito
  em Pantone no Illustrator) funciona, mas é manual.

---

## O0 — Corretor de EPS ✅ (protótipo)

`spikes/o0_eps/corrigir_eps.py entrada.eps saida.eps`:
- `eq_composta.EPS` → só chapa Black (K 6,25 %); BoundingBox e HiResBoundingBox **idênticas**;
  mesmo tamanho de arquivo; 117 bytes alterados.
- Os 13 outros EPS: 0 alterações (corretamente).
- Tentativa via Ghostscript (EPS→PDF→EPS): cores ok, mas a HiResBoundingBox mudou → descartada.
- Spec: `spec/O0_CORRETOR_EPS.md`. **Falta:** você testar o EPS corrigido no InDesign
  (`spikes/out/o0/eq_composta_100K.eps`): colocar, conferir na Visualização de Separações e exportar o
  PDF de gráfica.

**Usuário (2026-10-15):** "continua o problema preto 4 cores". Isso vale para o caminho
Word → InDesign (metarquivo RGB, ver S1). **Ainda falta** o teste dos 4 PDFs do EqPress colocados
diretamente (Arquivo > Colocar), que é o caminho que o produto usa.

**Roteiro do usuário:** colocar os 4 PDFs num documento InDesign, exportar com o preset de PDF da
gráfica, abrir a Visualização de Separações (InDesign) e a Visualização de saída (Acrobat):

| Variante | Só K na separação? | Overprint visível? | Observações |
|---|---|---|---|
| k100 | | | |
| k100_op | | | |
| gray | | | |
| rgb | | | |

---

## S6 — Ordem de sub-objetos de ARROW e PUA do MTCode ⬜

Depende de equações sintéticas do usuário (D-09).
