# INDESIGN — importação, vinculação, baseline, edição, re-estilização

Ambiente informado: InDesign 2024 e 2026 instalados no Mac do usuário (observado em /Applications;
**versão de trabalho a confirmar**, Dúvida D-05). Os PDFs de referência foram gerados por
InDesign 19.4 (2024) **Windows** (metadados de AMOSTRA:montagem_diagramada.pdf e resolucao_diagramada.pdf), então o fluxo
pode envolver as duas plataformas (Dúvida D-06).

Itens marcados ⏳ dependem do resultado dos spikes S1–S5 (spikes/RESULTADOS.md).

## 1. Fluxo

```
livro_pronto.docx ──Arquivo > Inserir──► texto + imagens inline (como hoje)
                                         │
              script "Vincular equações" ┘
                 ├─ acha cada imagem de equação pelo ID (⏳ S3)
                 ├─ troca a imagem incorporada por vínculo a /equacoes/NNNN.pdf
                 ├─ aplica estilo de objeto "Equação"
                 └─ ajusta a baseline pelo JSON de métricas (§4)
```

## 2. Componentes

| Script | Função | Tecnologia |
|---|---|---|
| Vincular equações | §3 | UXP (InDesign ≥ 18.5); `.jsx` de reserva |
| Editar equação selecionada | §5 | UXP → abre o editor EqPress |
| Atualizar todas | §6 | UXP: atualiza vínculos + reaplica baseline |
| Sonda (spike) | mede S2/S3 | `spikes/s2_s3_sonda/sondar.jsx` |

UXP é o padrão (OBSERVACAO-USUARIO §2 item 4). O `.jsx` existe porque o S3 pode mostrar que alguma
propriedade só é acessível via ExtendScript.

## 3. Vincular equações

- **ID-01** Identificador `EQ-NNNN` (4 dígitos, ordem de documento, ver FORMATO_DOCX_OLE R-DOCX-06)
  gravado em `wp:docPr/@descr` (texto alternativo). É o único canal que sobrevive ao Arquivo > Inserir;
  o script lê em `frame.objectExportOptions.customAltText`. Fonte: SPIKE:S3 (InDesign 19.4 Mac).
- **ID-02** Se nenhum canal sobreviver, usa-se o fluxo alternativo (marcador `⟦EQ:0042⟧` no texto e
  inserção de PDF ancorado). Fonte: OBSERVACAO-USUARIO §2 "Fluxo alternativo".
- **VIN-00** O que chega do Word: gráfico incorporado do tipo WMF/EMF ("Metarquivos avançados do
  Windows"), nome `ImageNNN.EPS`, cor RGB. **A troca pelo PDF é obrigatória** para a cor 100 % K
  (SPIKE:S1, S5b). Equação não trocada = erro no relatório.
- **VIN-01** Troca: `graphic.place(File(pdf))` no mesmo quadro (ou `link.relink` se o S1 mostrar que
  a imagem chega como vínculo). O quadro mantém posição, tamanho segue o PDF (sem escala: 100 %).
- **VIN-02** Página do PDF importado: recorte "Caixa delimitadora (apenas camadas visíveis)" ou
  `MediaBox` == caixa da equação (o renderizador gera página justa). ⏳ confirmar no S1.
- **VIN-03** Aplica o estilo de objeto "Equação" (criado se não existir: sem contorno, sem
  preenchimento, ajuste de quadro ao conteúdo, sem enquadramento de texto).
- **VIN-04** Relatório no fim: vinculadas, não encontradas (ID no JSON mas não no documento),
  órfãs (imagem com ID sem PDF), duplicadas.

## 4. Baseline

- **BL-01** O `.docx` leva `w:position` arredondado a 0,5 pt (limite do formato, FORMATO_DOCX_OLE
  R-DOCX-03), que basta para a revisão visual no Word.
- **BL-02** No InDesign, o script calcula o deslocamento exato a partir do JSON da equação
  (`profundidade_pt` = quanto a caixa desce abaixo da baseline) e aplica **deslocamento de linha de
  base** (`baselineShift`) no caractere-âncora do gráfico inline, com precisão de 0,001 pt.
  Alvo: `fundo_do_quadro − baseline == profundidade_pt` (± 0,1 pt). A sonda mede exatamente essa
  diferença (coluna `desce_abaixo_baseline_pt`).
- **BL-03** O `w:position` chega como `baselineShift` do caractere-âncora, truncado a pontos inteiros
  (−1 pt → 0; −3,5 → −3). O script **sobrescreve** esse valor pelo exato. Fonte: SPIKE:S2.

## 5. Editar equação selecionada

1. Usuário seleciona o quadro da equação → script lê o caminho do vínculo
   (`/equacoes/0042.pdf`) e o JSON irmão (`0042.json`).
2. Abre o editor EqPress (app Tauri) via URL `eqpress://editar?arquivo=<json>`.
3. Editor salva o MathML no JSON, re-renderiza o PDF **no mesmo caminho** com o preset gravado
   no JSON.
4. InDesign marca o vínculo como modificado; "Atualizar vínculo" (ou "Atualizar todas", §6)
   recarrega o PDF e reaplica a baseline com as métricas novas.

## 6. Re-estilizar o livro diagramado

- `eqpress reestilizar /equacoes --preset livroX_v2.json` re-renderiza todos os PDFs no lugar.
- "Atualizar todas" (UXP): para cada vínculo de `/equacoes`, `link.update()` + baseline nova.
- **RE-01** Os vínculos e os quadros não mudam; mas se a largura da equação mudar, o texto reflui
  naturalmente. "Sem mexer no layout" = sem ação manual; reflow de texto é esperado
  (Dúvida D-07).

## 7. Preset a partir do InDesign (O1)

Script lê do documento/modelo: estilos de parágrafo e caractere escolhidos pelo usuário (fonte,
corpo, entrelinha, cor) e gera `<livro>_v1.json` preenchendo `categorias.*.familia`,
`tamanhos.completo` e `cores` a partir dos amostras de cor do documento. Espaçamentos vêm do preset
base (`baseado_em`).

## 8. Preflight

Entregar perfil `EqPress-Equacoes.idpp` com:

- Cor > Espaços de cor e modos não permitidos: RGB, LAB.
- Cor > Chapas de ciano, magenta ou amarelo não permitidas.
- Imagens e objetos > Vínculos ausentes ou modificados.

⏳ Validar no S5 se o preflight acusa um PDF de equação RGB colocado (o perfil é por documento; o
critério "mais de uma tinta em gráfico de equação" pode precisar de checagem complementar no script
"Vincular equações", que restringe a análise aos quadros com estilo "Equação").

## 9. Decisões da SESSÃO B (F5, 2026-10-16)

Fonte: teste automático no InDesign 2024 (19.4) e 2026 deste Mac (`tests/indesign_teste.py`).

- Script único **`indesign/EqPress - Vincular e alinhar equações.jsx`** (ExtendScript, roda no
  painel Scripts do 2024 e do 2026 sem instalar plugin): troca + estilo + baseline; rodar de novo
  = "Atualizar todas". UXP fica para quando o editor (F6) precisar abrir pelo InDesign.
- Pasta das equações: escolhida uma vez e guardada no documento (`insertLabel`); um desfazer
  (⌘Z) desfaz o script inteiro.
- **Medida da baseline:** `Line.baseline` segue o primeiro caractere da linha (se for a própria
  equação, a medida anda junto com o deslocamento). A baseline é medida num caractere de texto
  comum, sem deslocamento, da mesma linha; o script mede e corrige até < 0,01 pt.
- **Equação sozinha na linha** (sem texto para alinhar): deslocamento 0 — o fundo apoia na
  baseline e a entrelinha automática abre espaço (deslocar moveria a linha inteira).
- Resultado (corpus MT questões + CN resoluções, Arial 10): 136/136 trocadas pelo PDF;
  89 no meio do texto com desvio máximo 0,0000 pt; 47 sozinhas na linha; exportação PDF/X-1a
  com equações só em `0 0 0 1 k/K` e sobreimpressão preservada (OP/op/OPM 1).
- **Windows (2026-10-17):** os dois scripts valem no InDesign para Windows. "Editar equação
  selecionada" entrega o link `eqpress://` pelo `WScript.Shell` (VBScript); o app registra o
  esquema e mantém uma instância só. O botão "Instalar scripts no InDesign" (Início) copia os
  scripts para `%APPDATA%\Adobe\InDesign\Version *\*\Scripts\Scripts Panel`. A ser confirmado no
  PC do colaborador: importação do EMF do `.docx` e o ID em `docPr/@descr` no InDesign Windows.
- **Word editável (pedido do usuário, 2026-10-16: "se eu passar esse documento pra frente as
  fórmulas não ficam editáveis").** Teste no InDesign 2024 com o objeto MathType mantido e só a
  prévia trocada: o ID se perde (nem `v:shape/@alt` nem `v:imagedata/@o:title` chegam ao texto
  alternativo; marcadores do Word chegam renomeados, `.1268`…) e a prévia de objeto OLE entra
  2,83× menor (o InDesign lê o quadro do EMF em mm como pt). Decisão: **dois arquivos** —
  `_EqPress.docx` (imagens + ID, para o InDesign) e `_EqPress_editavel.docx` (MathType intacto,
  prévia nova; para passar adiante e, se editado no MathType, voltar ao EqPress).
- **Escopo (usuário, 2026-10-19):** a revisão com o professor é toda no Word com MathType (ele
  escreve e corrige lá; o EqPress só prepara de novo o que ele devolver). O EqPress é para as
  etapas que vão para o InDesign. **Não** gravar MTEF/objeto MathType a partir de equações
  editadas no EqPress; o editor próprio serve a ajustes de diagramação.
