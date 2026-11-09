# CHANGELOG

## 2026-11-09
- Abertura do código: licença MIT, `THIRD_PARTY_NOTICES.md`, licenças das ferramentas embutidas nos
  instaladores (`recursos/licencas`), README com instalação e uso no Mac e no Windows.
- Tag `v*` publica o `.dmg` e o `.exe` no Release do GitHub.
- Nomes de materiais reais trocados por nomes genéricos (`corpus_*`, `exemplo_*`); identificador do
  app agora é `io.github.viniciusrfc.eqpress`.

## 2026-10-19 — SESSÃO B
- Decisão de escopo: correções de conteúdo ficam com o professor no MathType; o EqPress é para as
  etapas do InDesign. Sem gravação de objeto MathType (MTEF) a partir do EqPress (INDESIGN §9).
- **Instalador do Mac** (`EqPress.dmg`, 164 MB, Apple Silicon, macOS 15+): app + núcleo empacotado
  + tectonic oficial + pacote TeX offline + Ghostscript compilado do código-fonte (só depende do
  macOS) + Inkscape enxuto (645 → 235 MB). Montado no CI (`.github/workflows/mac.yml`). Sem
  assinatura da Apple: o app tira a quarentena das ferramentas embutidas ao iniciar o núcleo.
  Conferido aqui: núcleo do .dmg com PATH mínimo → PDF/EPS/EMF, só 100K; app aberto → familias,
  padrões e prova pelo núcleo empacotado. Desenvolvimento: `binaries/eqpress-nucleo-aarch64-apple-darwin`
  local é um atalho para o `.venv` (fora do git).
- Windows, 1º teste no PC: a interface abria com todos os botões mortos. Causa: o `npm run vendor`
  usava `rm`/`cp`, que não existem no cmd do Windows; a montagem seguiu sem MathLive/KaTeX/MathJax
  e o `app.js` não carregava. Agora `editor/vendor.mjs` (Node, igual nos dois sistemas) confere os
  arquivos, e a etapa do CI para em qualquer erro de comando. Atalhos Salvar/Abrir aceitam Ctrl.
- Windows, 2º teste: botões respondiam mas nada processava (padrão "Salvando…" para sempre,
  Instalar scripts parado). Causa: o pipe do núcleo no Windows é cp1252 e o app fala UTF-8; respostas
  com acento ("Padrões", "equações.jsx") derrubavam o núcleo. `servidor` agora força UTF-8 (teste
  `test_servidor_fala_utf8`, roda no CI Windows) e a UI mostra falha do núcleo em vez de travar.
- Windows, 3º teste: padrão ainda "não salva". No CI Windows o núcleo empacotado faz a sequência da
  tela Padrões sem erro (prova 5 s, salvar 0,5 s; `tests/fluxo_app.py`). Para enxergar o PC do
  colaborador: versão 0.1.1 no diagnóstico + `registro.txt` (cada pedido, tempo e erro) dentro do
  "Copiar diagnóstico"; erro de programa na tela aparece na mensagem da tela aberta; provas uma por
  vez (antes enfileiravam e o Salvar esperava atrás de todas).
- **W5 aprovado** (0.1.1, PC do colaborador, Windows 11): padrão salvo, Preparar de um capítulo real
  (14 equações, 0 erros), InDesign Windows Inserir + Vincular e alinhar: 14/14 trocadas pelo
  PDF, desvio máximo de baseline 0,000 pt. Traço das equações idêntico ao render do Mac (mesmo
  padrão Calibri 10).

## 2026-10-17 — SESSÃO B
- **Instalador do Windows** (`EqPress-Setup.exe`, ~142 MB, NSIS, por usuário): app + núcleo
  empacotado (PyInstaller) + tectonic com pacote TeX offline + Ghostscript + Inkscape enxuto +
  STIX Two Math. Montado no GitHub Actions (`windows.yml`, job `instalador`); o núcleo empacotado
  passa no `diagnostico --completo` sem internet (PDF/EPS/EMF, separação ok). Roteiro de teste:
  `docs/TESTE_WINDOWS.md`. Falta: teste no PC do colaborador (W5).
- Windows (plano W0–W1): repositório no GitHub com testes num Windows a cada
  envio (`.github/workflows/windows.yml`); `eqpress/plataforma.py` (pastas, fontes, ferramentas,
  abrir/mostrar); UTF-8 explícito; STIX Two Math embutida (`recursos/fontes`, OFL); fontes no TeX
  por caminho relativo (`eqfontes/`, o "C:" quebrava o XeTeX); Symbol do Windows por número do glifo;
  `python -m eqpress diagnostico`.
- Interface do app em **Lato** (OFL, @fontsource/lato 5.3.0, embutida em `ui/vendor/lato`), 14 px,
  negrito 700, no lugar da Avenir Next.
- App com três telas: **Início** (Preparar um Word, Trocar o padrão de um livro, Editar uma
  equação), **Padrões dos livros** (lista, ficha com fonte/corpo/variáveis/símbolos/cor/tinta
  especial/sobreimpressão/EPS/EMF, prova ao vivo, salvar como versão nova, importar/exportar) e
  **Equação**. Biblioteca de padrões em ~/Library/Application Support/EqPress/Padrões
  (`eqpress/biblioteca.py`); schema ganhou `titulo`. Núcleo: `editor.atender`. Testes novos.

## 2026-10-16 — SESSÃO B
- Editor compacto: janela 900×580 (mín. 680×440), uma coluna (paletas, edição, prova numa faixa
  embaixo com tinta e medidas), "Fonte desta equação" como painel no topo, LaTeX pelo rodapé,
  nome do grupo da paleta no rodapé ao passar o mouse, Esc fecha os painéis.
- Setas e símbolos (⇒ → = + − · gregos) na **Symbol do Windows** (a do Office, igual ao MathType)
  em vez da Symbol do macOS, que desenhava as setas finas como a Arial. Codificação antiga mapeada
  pela tabela pública Adobe Symbol (PRESET P-08). Corrigido junto: família fixa alta, porque o
  `\mathrm` alocado sob demanda caía na mesma família.
- Trocar a fonte do livro inteiro sem reinserir o Word: `eqpress reestilizar pasta` e
  "Trocar fonte do livro.command" (refaz todas as equações no lugar a partir do LaTeX de cada uma,
  padrão anterior no histórico, versão +1). No InDesign: "Vincular e alinhar".
- Ajuste "Só nesta equação" no editor (fonte, corpo, itálico), gravado no JSON e mantido pelo reestilizar.
- Tela do editor redesenhada (frontend-design): a prova mostra a equação real com a linha de base
  em ciano de guia e a cota da profundidade; tinta do padrão; medidas; paletas em duas fileiras.
- Corrigido o editor não salvar (nem renderizar a prévia) quando aberto pelo InDesign/Finder: o app
  recebe PATH mínimo e não achava tectonic/gs/inkscape; o núcleo agora inclui as pastas do Homebrew
  e do TeX no PATH. Teste com ambiente mínimo.
- Corrigido "Editar equação selecionada" não abrir o editor: `open location` executado dentro do
  InDesign é tratado pelo InDesign (ignora o link); agora usa `do shell script "open …"`.
  Testado no InDesign 2024: o EqPress abre e carrega a equação.
- Editor conferido no navegador (mesma `ui/`): abrir, paleta, prévia real automática, salvar com
  histórico. Script do InDesign "EqPress - Editar equação selecionada" (abre o editor via
  `eqpress://`); EqPress.app em ~/Applications; testes `tests/test_editor.py`.
- REA (rea.tools, engenharia reversa) **não** será usado: viola a regra de clean room (PROVENIENCIA §3).
- F6 (início) editor EqPress.app (Tauri 2 + MathLive 0.105.3, `editor/`): paletas em duas fileiras,
  menus Estilo/Tamanho, LaTeX sincronizado, prévia real pelo núcleo (`python -m eqpress servidor`,
  `eqpress/editor.py`), salvar com conferência de separação e portabilidade, histórico e troca
  atômica do PDF; abre por `eqpress://editar?arquivo=…`. Compila; interface ainda não conferida
  visualmente. Falta: script "Editar equação selecionada" no InDesign, tela "Padrão do livro", testes.
- Word editável: além do `_EqPress.docx` (imagens, para o InDesign), sai `_EqPress_editavel.docx`
  com os objetos MathType intactos e a aparência nova (dois cliques abrem o MathType). Manter o
  MathType no arquivo do InDesign foi testado e descartado (ID perdido, tamanho 2,83× menor).
- Script do InDesign: resumo numa janela com rolagem (o alert não rolava), botão para abrir o
  relatório e uma linha por equação (página, ação, deslocamento, desvio); arquivo com quebras Unix.
- F5 script do InDesign "EqPress - Vincular e alinhar equações" (`indesign/`, instalado no painel
  Scripts do 2024 e 2026): troca cada imagem EQ-NNNN pelo PDF 100K e alinha a baseline medindo no
  próprio InDesign. Teste automático (`tests/indesign_teste.py`): 136 equações, desvio 0,0000 pt,
  equações só em K no PDF/X-1a exportado.
- Corrigido: equações "espremidas" no Word/InDesign. O Inkscape grava no cabeçalho do EMF um
  quadro ~2 pt mais alto que o desenho; Word e InDesign comprimiam a equação para ~82 % da altura.
  O EqPress agora regrava rclBounds/rclFrame com a caixa do PDF (teste novo).
- Padrão do livro simplificado (`eqpress/padrao.py`): o "Testar EqPress.command" pergunta fonte,
  corpo e itálico das variáveis (lembra a última escolha) e gera PDF/EMF/Word com eles. Grego e
  símbolos seguem na Symbol, o resto na STIX Two Math. CLI: `testar x.docx --familia Arial --corpo 10`.
- F4 .docx pronto (`eqpress/docx_saida.py`): cada equação vira EMF inline com o ID em
  `docPr/@descr` e `w:position` da profundidade (0,5 pt); OLE e prévias WMF removidos; equação com
  erro mantém o OLE original. `testar`/`estilizar` gravam `<nome>_EqPress.docx`; link na página.
- Teste simplificado: "Testar EqPress.command" (dois cliques → escolher .docx → abre
  `conferir.html` com cada equação nova dentro da frase do Word, alinhada pela baseline, e links
  PDF/EPS/EMF). CLI `python -m eqpress testar arquivo.docx`. EMF em uma só execução do Inkscape.
- F3 renderizador (`eqpress/renderizador.py`): LaTeX + preset → PDF em contorno na cor do preset
  (100 % K ou tinta especial), sobreimpressão, métricas de baseline; EPS e EMF opcionais.
  Corpus: 282 PDFs em ~14 s, CA-06/08 verdes. Lote e CLI: `python -m eqpress estilizar|renderizar`
  (`eqpress/lote.py`). Preset exemplo de resolução em PANTONE 219 C.
- F2: frações, linhas de pilha e células de matriz em tamanho cheio (`\displaystyle`), como no MTEF.
- spec: saídas PDF + EPS + EMF, suplemento do Word Mac (F6b), layout do editor (ED-18); PRESET §10.
- F2 parser MTEF (`eqpress/mtef.py`) e conversor árvore → LaTeX + MathML (`eqpress/conversor.py`):
  282/282 sem erro; LaTeX renderiza em KaTeX e MathJax 3 (`ferramentas/web/verificar.js`).
  Testes: exemplo byte a byte da doc pública, seletores 0–37, embelezamentos 2–37, erros (CA-13).
- Corrigido salto de registros FUTURE (`self.i += self.uint()` lia o cursor antes de avançar).
- spec/MTEF.md §8: decisões do F2.

## 2026-10-15 — SESSÃO B
- F1 extrator (`eqpress/extrator.py`, `python -m eqpress.extrator x.docx`): 282/282 equações do corpus
  com ID, parte, local, parágrafo, destacada, `w:position`, tamanhos, OLE, prévia e bytes MTEF;
  objetos com outro ProgID reportados. Testes em `tests/test_extrator.py`.
- spec/FORMATO_DOCX_OLE: corrigido offset do tamanho do MTEF (u32@8, não @6); style em `in`.

## 2026-10-15
- Fim da SESSÃO A: spec/PLANO.md (fases F1–F8, O1–O8, ambiente, pendências não bloqueantes) e SESSAO_B.md (prompt da nova sessão).
- S5 concluído: PDFs 100K colocados direto e exportados em PDF/X-1a saem só em K; overprint do PDF preservado; RGB vira preto composto; DeviceGray vira K (permitido, não padrão).
- Resultados S1–S4: EMF no .docx; ID em docPr/@descr; baselineShift exato pelo script; troca por PDF obrigatória; S4 não adotado. Achado: menos (−) do MathType vira □ no InDesign Mac.
- D-15: LaTeX canônico e portátil (MathJax/KaTeX), ED-04, CA-17. D-03: 8 % a validar visualmente.
- PRESET §2.1: três camadas de fonte (livro / Symbol / fonte matemática = STIX Two Math), MT Extra proibida.
- EDITOR §3.1: calibração do padrão do livro dentro do editor (resposta D-04); PRESET P-05.
- spec/EDITOR.md (editor de fórmulas: modos, fonte canônica, interface, integração, aceite).
- O0 estacionado; foco no editor e no pipeline principal.
- O0 reorientado: alvo principal = equações incorporadas no .indd (relato do usuário); sonda passa a
  registrar formato e status de incorporação.
- S5b: separação por chapa dos EPS e do PDF de gráfica. Preto composto medido (C73 M68 Y67 K89) nas
  equações de enunciado; resoluções em PANTONE 219 C estão limpas.
- O0: protótipo de correção no lugar (mesmo tamanho de arquivo, BoundingBox preservada) e
  spec/O0_CORRETOR_EPS.md.
- COMPORTAMENTO A.5: cor por contexto (enunciado × resolução); CA-15, CA-16.

## 2026-10-14 — SESSÃO A, início
- Inventário do corpus (S0) e parser MTEF de spike.
- Geradores de teste para S1–S5 e sonda .jsx para S2/S3.
- Primeira versão de todos os documentos de spec/.
