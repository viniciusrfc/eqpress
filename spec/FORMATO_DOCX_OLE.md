# FORMATO_DOCX_OLE — equações MathType dentro do .docx

Escopo: o que existe no .docx e onde fica. Tudo aqui foi observado **somente** nos 4 arquivos de
`/samples` (inventário reproduzível com `spikes/s0_corpus/analisar_corpus.py`), salvo onde a fonte
indicar DOC-PUBLICA.

## 1. Corpus analisado

| Arquivo | Equações | Prévia | Em tabela | Sozinhas no parágrafo |
|---|---|---|---|---|
| corpus_cn_questoes.docx | 45 | WMF | 0 | 7 |
| corpus_cn_resolucoes.docx | 56 | WMF | 0 | 35 |
| corpus_mt_questoes.docx | 80 | WMF | 0 | 12 |
| corpus_mt_resolucoes.docx | 101 | WMF | 0 | 48 |
| **Total** | **282** | | | |

Fonte: SPIKE:S0, AMOSTRA:todas.

## 2. Partes do pacote envolvidas

| Parte | Papel |
|---|---|
| `word/document.xml` | um `<w:object>` por equação, dentro de um `<w:r>` |
| `word/_rels/document.xml.rels` | liga o `r:id` do OLE a `embeddings/oleObjectN.bin` e o da prévia a `media/imageN.wmf` |
| `word/embeddings/oleObjectN.bin` | arquivo composto OLE (CFB) com o MTEF |
| `word/media/imageN.wmf` | prévia que o Word mostra (e que o InDesign importa hoje) |

As demais imagens `.png` em `word/media` são figuras do livro, não equações. Fonte: AMOSTRA:todas.

## 3. Marcação no document.xml

```xml
<w:r>
  <w:rPr><w:position w:val="-8"/></w:rPr>        <!-- opcional: deslocamento vertical -->
  <w:object w:dxaOrig="1560" w:dyaOrig="1020" w14:anchorId="5E8BEA5A">
    <v:shapetype id="_x0000_t75" .../>              <!-- só na 1ª ocorrência -->
    <v:shape id="_x0000_i1232" type="#_x0000_t75" style="width:78pt;height:51pt" o:ole="">
      <v:imagedata r:id="rId8" o:title=""/>         <!-- prévia (media/*.wmf) -->
    </v:shape>
    <o:OLEObject Type="Embed" ProgID="Equation.DSMT4" ShapeID="_x0000_i1232"
                 DrawAspect="Content" ObjectID="_1850495961" r:id="rId9"/>  <!-- embeddings/*.bin -->
  </w:object>
</w:r>
```

Regras observadas:

- **R-DOCX-01** O seletor de equação é `w:object/o:OLEObject[@ProgID="Equation.DSMT4"]`. As 282
  equações usam esse ProgID; nenhum outro ProgID aparece. O extrator deve listar (e reportar)
  qualquer `w:object` com outro ProgID, sem descartá-lo em silêncio. Fonte: AMOSTRA:todas.
- **R-DOCX-02** Tamanho exibido: `v:shape/@style` (`width`/`height` em pt). Tamanho original:
  `w:dxaOrig`/`w:dyaOrig` em twips (1/20 pt). Exemplo: 1560×1020 twips = 78×51 pt, igual ao style.
  O style pode vir em `pt` ou `in` (MT_resolucoes) e diferir do original em até 0,3 pt.
  Fonte: AMOSTRA:corpus_mt_resolucoes.docx.
- **R-DOCX-03** Deslocamento vertical: `w:rPr/w:position/@w:val` no run da equação, em
  **meios-pontos** (inteiro; `-8` = rebaixado 4 pt). As 282 equações têm valor negativo; na amostra
  vão de −4 (−2 pt) a −180 (−90 pt). Fonte: AMOSTRA:todas; unidade: DOC-PUBLICA:ECMA-376
  (`ST_SignedHpsMeasure`).
  ⚠ **Consequência:** a granularidade do Word é 0,5 pt, e o critério de aceite pede ≤ 0,1 pt. A
  baseline fina **não pode** depender só do `.docx`; o script do InDesign corrige com base no JSON de
  métricas (ver INDESIGN.md §4).
- **R-DOCX-04** Equação "destacada" × "inline": nas amostras, todas estão inline num run. Uma
  equação "destacada" é apenas um parágrafo cujo único conteúdo é a equação (102 de 282). O
  alinhamento do parágrafo varia (`w:jc` ausente ou `both`). **O bit "inline" do cabeçalho MTEF NÃO
  corresponde à posição no Word** (227 de 282 têm o bit de "display", inclusive equações no meio da
  frase), então o extrator classifica pela estrutura do parágrafo, não pelo bit. Fonte: SPIKE:S0.
- **R-DOCX-05** Nenhuma equação aparece em tabela, nota de rodapé ou caixa de texto nas amostras,
  mas o extrator deve percorrer também `footnotes.xml`, `endnotes.xml`, cabeçalhos/rodapés e
  `w:txbxContent`, e reportar o local. Fonte: AMOSTRA:MT_* (contêm footnotes.xml/endnotes.xml).
- **R-DOCX-06** Ordem estável: a ordem de documento dos `w:object` é a base do identificador
  `EQ-NNNN`. A numeração de `oleObjectN.bin` coincide com essa ordem nas amostras, mas **não** deve
  ser usada como identificador (o Word renumera ao salvar). Fonte: AMOSTRA:todas.

## 4. O objeto OLE (`oleObjectN.bin`)

Arquivo composto (CFB) com 4 streams, iguais nos 282 objetos:

| Stream | Tamanho | Conteúdo |
|---|---|---|
| `\x01CompObj` | 105 B | tipo do objeto; contém a string "MathType 7.0 Equation" |
| `\x01Ole` | 20 B | cabeçalho OLE padrão |
| `\x03ObjInfo` | 6 B | flags OLE |
| `Equation Native` | variável | **cabeçalho de 28 bytes + MTEF** |

Cabeçalho de `Equation Native`, conforme os bytes observados (ex.: oleObject1, 380 B):

| Offset | Bytes | Valor observado | Interpretação |
|---|---|---|---|
| 0 | u16 LE | `0x001C` (28) | tamanho do cabeçalho |
| 2 | u32 LE | `0x00020000` | versão do cabeçalho |
| 6 | u16 LE | `0xC301` | formato (constante nas 282) |
| 8 | u32 LE | ex.: `0x03C1` (961) | tamanho do MTEF (= 989 − 28 ✔, CN_resolucoes EQ-0001) |
| 12 | 16 B | variável | reservado; o leitor deve ignorar |

Correção SESSÃO B (2026-10-15): a tabela anterior punha o tamanho em u32@6, o que não fecha em
nenhuma das 282 equações; com u32@8 fecha em todas. Fonte: AMOSTRA:todas (bytes).

- **R-OLE-01** O leitor pula `hdr_len` bytes (lidos do offset 0, não fixos em 28) e valida que
  `u32@8 == len(stream) − hdr_len`. Divergência = aviso no relatório. Fonte: AMOSTRA:todas.
- **R-OLE-02** O MTEF de todas as amostras tem cabeçalho `v5 / Windows / MathType / 7.4`, app key
  `DSMT7`. Fonte: AMOSTRA:todas. Ver MTEF.md.

## 5. Prévia WMF

- **R-PREV-01** Toda equação tem prévia WMF em `word/media`. É o que o InDesign importa hoje via
  Arquivo > Inserir (OBSERVACAO-USUARIO §0). A prévia serve como **referência visual** para a prova
  lado a lado (O5): converter WMF→PNG com ferramenta open source (Inkscape/libwmf).
- **R-PREV-02** O EqPress nunca reaproveita a prévia como saída final (fontes MathType embutidas no
  desenho, cor RGB). Fonte: OBSERVACAO-USUARIO §0 item 6.

## 6. Pendências de amostra

- Nenhuma amostra tem equações em tabela, nota, caixa de texto, `Equation.3` (Equation Editor
  antigo) ou `Equation.DSMT6`. Se existirem nos livros reais, preciso de uma amostra.
- Não há EPS de equação em `/samples` (necessário para a análise de cor do S5 e para o O0).
