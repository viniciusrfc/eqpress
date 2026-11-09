# EDITOR — editor de fórmulas EqPress (macOS)

O editor é o que substitui o MathType no dia a dia: abrir uma equação, editar visualmente, salvar,
e o InDesign atualizar o vínculo. Fonte: OBSERVACAO-USUARIO §0 itens 5, §2 itens 5–6, §5, §7 F6.

## 1. Papéis do editor

| Modo | Como abre | Resultado ao salvar |
|---|---|---|
| Editar equação vinculada | "Editar equação selecionada" no InDesign → `eqpress://editar?arquivo=/…/equacoes/0042.json` | regrava `0042.json` e re-renderiza `0042.pdf` **no mesmo caminho** |
| Editar equação do lote antes do InDesign | abrir `0042.json` pelo app ou pelo relatório O4/O5 | idem; o .docx é regerado com `eqpress estilizar` |
| Nova equação | ⌘N no app | grava `NNNN.json/.pdf` na pasta escolhida; o usuário coloca no InDesign |

Fonte: OBSERVACAO-USUARIO §2 itens 5–6; INDESIGN.md §5.

## 2. Formato-fonte da equação (`NNNN.json`)

```json
{
  "id": "EQ-0042",
  "fonte": { "latex": "x=\\frac{-b\\pm\\sqrt{b^{2}-4ac}}{2a}", "mathml": "<math>…</math>" },
  "categorias": [ { "faixa": [0, 1], "categoria": "variavel" } ],
  "origem": { "docx": "autor.docx", "ole": "embeddings/oleObject12.bin", "mtef_sha1": "…" },
  "preset": "livroX_v2", "preset_sha1": "…",
  "metricas": { "largura_pt": 89.9, "altura_pt": 21.3, "profundidade_pt": 9.6 },
  "contexto": "enunciado"
}
```

- **ED-01 Fonte canônica = LaTeX** (subconjunto definido em §5); o MathML é **derivado** e
  gravado junto (para O6 depara, O8 OMML e comparação). Motivo: o editor visual (MathLive) e o
  renderizador (LuaLaTeX) trabalham em LaTeX; manter MathML como canônico obrigaria a converter
  MathML↔LaTeX a cada edição, com perda. Fonte: OBSERVACAO-USUARIO §5 (MathLive + LuaLaTeX).
  ✔ Confirmado pelo usuário em 2026-10-15 (D-15): "pode guardar em LaTeX para utilizarmos online".
- **ED-04 Reuso online:** o subconjunto LaTeX (§5) precisa renderizar também em MathJax 3 e KaTeX
  sem alteração, para as mesmas equações irem para a web. Comandos fora disso (ex.: macros só de
  LuaLaTeX) são proibidos no arquivo-fonte; ajustes tipográficos ficam no preset, não no LaTeX.
  Teste: o lote do corpus renderiza sem erro no MathJax e no KaTeX. Fonte: OBSERVACAO-USUARIO 2026-10-15.
- **ED-02** A importação do .docx gera LaTeX a partir do MTEF (MTEF → árvore → LaTeX e MathML), não
  MathML → LaTeX.
- **ED-03** O estilo MathType por caractere (typeface: variável, função, texto…) é preservado como
  comandos do subconjunto (`\mathrm`, `\mathit`, `\text`, `\operatorname`) ou pela lista
  `categorias`; o preset decide a aparência final (PRESET.md §2).

## 3. Interface

- **ED-10** Área de edição visual (MathLive): digitação direta, atalhos e paleta de templates.
  Paleta mínima = templates do corpus (fração, raiz, sobrescrito/subscrito, parênteses/colchetes/
  chave/barras, sistema com chave à esquerda, matriz, seta com rótulo (química), chave horizontal
  com rótulo) + todos os seletores 0–37 do MTEF (MTEF.md §5).
- **ED-11** Prévia ao lado com o **render real** (o PDF que vai para o InDesign, com o preset), não
  a renderização do MathLive. Atualiza ao parar de digitar (≤ 1 s para uma equação típica; ver D-08).
- **ED-12** Campo de LaTeX editável (modo avançado), sincronizado com a área visual.
- **ED-13** Seletor de categoria para a seleção (texto, função, variável… = os estilos do preset),
  equivalente ao menu Estilo do MathType, mas com nomes próprios. Fonte: OBSERVACAO-USUARIO §4.
- **ED-14** Indicador de cor/tinta do preset (ex.: "Preto 100K", "PANTONE 219 C") e alerta se a
  equação tem cor fora do preset.
- **ED-15** Salvar = ⌘S; ao salvar, o editor roda a verificação de separação (CA-06) e mostra
  ok/erro antes de gravar o PDF.
- **ED-16** Desfazer/refazer ilimitado na sessão; ao gravar, guarda a versão anterior do JSON e do
  PDF em `equacoes/.historico/` (para desfazer uma edição já atualizada no InDesign).
- **ED-17** Interface em português do Brasil. Nenhum texto, ícone ou nome de comando copiado do
  MathType (regra de clean room, OBSERVACAO-USUARIO §1).

- **ED-18** Organização da tela no estilo do editor que a equipe já usa: barra de paletas de
  templates no alto (frações e raízes, scripts, cercas, operadores grandes, setas, símbolos, grego,
  matrizes), área de edição grande, menus Estilo e Tamanho, atalhos de teclado usuais de editor de
  equações. Ícones, rótulos e nomes de menu **próprios**, em português (ED-17). Fonte:
  OBSERVACAO-USUARIO 2026-10-16 ("interface igual MathType" → aceito "layout parecido").
- **ED-19** Copiar a equação: área de transferência com PDF + EMF (colar no Word/InDesign) e LaTeX
  em texto.

## 3.1 Calibrar o padrão do livro (editor de presets)

Fonte: OBSERVACAO-USUARIO 2026-10-15: "as fontes podem variar, tem livro que é Calibri 10, tem livro
que é Calibri 9 ou outra fonte, isso eu calibro no editor de fórmula".

- **ED-30** Tela "Padrão do livro" dentro do editor, que cria e edita presets (PRESET_SCHEMA.json),
  sem editar JSON à mão. Seções: Estilos (as 9 categorias: família instalada no Mac, negrito,
  itálico, cor), Tamanhos (completo em pt; demais em pt ou %), Espaçamentos (os 30 parâmetros),
  Cor/tinta, Saída.
- **ED-31** Prévia ao vivo enquanto calibra: um conjunto fixo de equações de prova (as dos casos de
  COMPORTAMENTO B + as do corpus) renderizado com o preset em edição, ao lado de uma linha de texto
  na fonte e corpo do livro, para conferir o alinhamento visual com o texto corrido.
- **ED-32** Lista de fontes = as instaladas no macOS. Fontes do MathType (MT Extra, Euclid…)
  aparecem bloqueadas (P-02).
- **ED-33** Glifos ausentes: se a família escolhida não tem um caractere usado (ex.: Calibri não tem
  ⇌, ∑ grande, delimitadores extensíveis), a prévia marca o caractere e indica que ele vem da
  `fonte_matematica`. O usuário escolhe a `fonte_matematica` na mesma tela.
- **ED-34** Salvar o padrão grava uma **nova versão** (`livroX_v3.json`, O3), nunca sobrescreve uma
  versão já usada num lote. Opção "Aplicar ao livro" = `reestilizar` (INDESIGN.md §6).
- **ED-35** Ponto de partida: "Novo a partir de .docx" (lê o EQN_PREFS das equações do autor,
  PRESET.md §9) ou "Novo a partir de outro padrão" (`baseado_em`). Calibri 9 e Calibri 10 = dois
  presets, o segundo baseado no primeiro, mudando só `tamanhos.completo`.

## 4. Integração

- **ED-20** O app registra o esquema de URL `eqpress://` (abrir/editar) no macOS.
- **ED-21** Salvar re-renderiza pelo mesmo núcleo da CLI (`eqpress renderizar NNNN.json`), para que
  editor e lote produzam o mesmo PDF byte a byte (P-01).
- **ED-22** Se o PDF estiver aberto/bloqueado, o editor grava em arquivo temporário e troca
  atomicamente (o InDesign só vê o arquivo completo).
- **ED-23** O editor nunca altera o preset; trocar o estilo do livro inteiro é `reestilizar`
  (INDESIGN.md §6).

## 4.1 Suplemento do Word para Mac

Fonte: OBSERVACAO-USUARIO 2026-10-16 ("suporte para Word": gerar o .docx pronto **e** editar
dentro do Word Mac).

- **ED-40** Suplemento Office (Office.js, roda no Word para Mac): "Inserir equação" e "Editar
  equação selecionada" abrem o editor EqPress (`eqpress://`) e, ao salvar, inserem/trocam no
  documento uma imagem inline (EMF ou PNG, conforme o que o Office.js aceitar no Mac) com o LaTeX e
  o ID no texto alternativo, para reabrir a edição depois.
- **ED-41** "Converter equações do documento": roda o pipeline F1–F4 no documento aberto.
- ⏳ A confirmar num spike: quais formatos de imagem o Office.js insere no Word Mac e se o texto
  alternativo sobrevive a salvar/reabrir.

## 5. Subconjunto LaTeX suportado

O que o editor grava e o renderizador aceita (o resto é recusado com mensagem clara):
`\frac \dfrac \tfrac \sqrt[n]{} ^ _ \left \right \middle \begin{cases} \begin{matrix}/pmatrix/
bmatrix/vmatrix/array \overbrace \underbrace \overline \underline \vec \hat \tilde \dot \ddot
\overset \underset \xrightarrow[]{} \xleftrightharpoons \sum \prod \int \iint \iiint \oint \lim
\text \mathrm \mathit \mathbf \operatorname`, letras gregas, operadores e setas Unicode.
Cobertura exigida: tudo o que o conversor MTEF→LaTeX produz para os seletores 0–37 (MTEF.md §5).

## 6. Tecnologia (proposta do briefing, a confirmar na SESSÃO B)

| Parte | Escolha | Licença |
|---|---|---|
| App | Tauri 2 (Rust + WebView do macOS), Apple Silicon nativo | MIT/Apache-2.0 |
| Edição visual | MathLive | MIT |
| Render | núcleo Python + LuaLaTeX (TeX Live / MacTeX) | LPPL/GPL (ferramenta externa, não linkada) |
| Fontes matemáticas | as do preset (OFL quando fornecidas pelo EqPress) | OFL |

## 7. Critérios de aceite do editor

- CA-E1: abrir pelo InDesign → editar → ⌘S → "Atualizar vínculo" mostra a mudança (= CA-10).
- CA-E2: abrir e salvar sem mudanças não altera o PDF (mesmo hash).
- CA-E3: as 282 equações do corpus abrem no editor e salvam sem alteração visual (prova lado a lado
  O5 sem diferenças).
- CA-E4: prévia atualizada em ≤ 1 s para equação típica (meta, ver D-08).
