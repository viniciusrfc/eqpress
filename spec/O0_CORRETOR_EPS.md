# O0 — Corretor de EPS existentes (preto composto → 100 % K)

> **ESTACIONADO (2026-10-15)** a pedido do usuário: o foco é o editor e o pipeline principal.
> Os achados de cor deste documento continuam valendo para o renderizador (PRESET, CA-06).

Objetivo: corrigir os EPS de equação de livros já diagramados sem refazer a diagramação.
Fonte do objetivo: OBSERVACAO-USUARIO §3 O0. Protótipo: `spikes/o0_eps/corrigir_eps.py` (SPIKE:O0).

## 0. Fluxo real (OBSERVACAO-USUARIO, 2026-10-15)

> "Esses EPS todos foram extraídos do MathType. [...] ele está no Word, eu edito por lá e insiro no
> InDesign; ele só sai .eps quando eu preciso alterar alguma coisa nele, caso contrário ele fica
> como objeto incorporado ao arquivo ID."

Consequências:

- **O0-00 O alvo principal são os gráficos de equação INCORPORADOS no .indd**, que vieram do Word
  via Arquivo > Inserir. EPS em disco são minoria: só as equações que já foram editadas.
- O corretor precisa então de dois modos:
  1. **arquivo** (EPS em disco, §2): já prototipado;
  2. **documento** (script no InDesign): percorre os gráficos de equação incorporados,
     desincorpora cada um para uma pasta temporária, corrige, revincula ou reincorpora no mesmo
     quadro (sem mudar posição nem escala) e gera o relatório.
- ⏳ O modo documento depende de saber **em que formato a equação fica incorporada** (WMF? PICT?
  EPS? PDF?) e se o InDesign deixa desincorporá-la. Para isso, rodar a sonda num .indd real (D-14).
- Hipótese a confirmar (SPIKE:S5b + este fluxo): a prévia do Word é WMF, ou seja, RGB; o InDesign
  converte o preto RGB para CMYK pelo perfil do documento na exportação, e daí sai C73 M68 Y67 K89.
- Os EPS das amostras têm `%%Creator: Adobe Illustrator(R) 24.0` e procsets AGM no cabeçalho
  (fato do arquivo). Ou seja, alguma etapa do caminho "desincorporar → editar" passa pelo
  Illustrator ou grava nesse formato (D-12).

## 1. O que as amostras mostram

| Arquivo | Origem | Tintas (Ghostscript tiffsep) | Classificação |
|---|---|---|---|
| eq_composta.EPS | Illustrator 24, DOS EPS com prévia TIFF | C 5,7 · M 4,9 · Y 3,9 · K 6,1 % | equação, **preto composto** |
| eq_composta_pan.eps e 8 outros `eq*_pan.eps` | Illustrator 24 | só PANTONE 219 C | equação em tinta especial, ok |
| fig_a_pan / fig_b_pan | Illustrator 24 | Black + PANTONE 219 C | figura, ok |
| fig_c / fig_d | Illustrator 24 | CMYK; preto já é `0 0 0 1` | figura colorida, ok |

Fonte: AMOSTRA:*.eps, SPIKE:O0.

- A cor de preto composto de `eq_composta.EPS` é **um único** operador
  `.911711 .786862 .619532 .974487 cmyk` (operador `cmyk` do procset Adobe AGM) no corpo da página.
- No livro diagramado (AMOSTRA:"paginas_grafica.pdf"), as equações em preto dos
  enunciados saem com **C73 M68 Y67 K89** (297 % de tinta), por exemplo "√3 m" na questão 07 da
  p. 701. São valores diferentes dos do EPS acima, ou seja, a origem/conversão varia. **A regra
  não pode depender de um valor exato.**
- Todos os EPS das amostras têm cabeçalho e procsets do Illustrator 24, embora venham do fluxo
  MathType (ver §0). Dúvida D-12.

## 2. Requisitos

- **O0-01 Edição no lugar, mesmo comprimento.** Cada operador de cor trocado é substituído por
  `0 0 0 1` + espaços até o mesmo número de bytes. Resultado: cabeçalho DOS EPS (offsets da
  seção PostScript e da prévia), `%%BoundingBox`, `%%HiResBoundingBox` e o resto do arquivo ficam
  byte a byte iguais. Fonte: SPIKE:O0 (117 bytes alterados; caixa idêntica).
- **O0-02 Proibido reescrever via conversor** (Ghostscript pdfwrite/eps2write ou similar): no
  spike, isso mudou a HiResBoundingBox de 83,18×21,55 para 82,40×21,50 pt, o que desloca o gráfico
  no InDesign. Fonte: SPIKE:O0.
- **O0-03 Regra de "preto composto":** K ≥ `limiar` (padrão 0,90) **e** C, M ou Y > 0. Qualquer
  outra cor permanece intacta e entra no relatório como "cor mantida". Fonte: SPIKE:O0 (figuras MAT*
  com cores intencionais não foram alteradas).
- **O0-04 Metadados de chapas:** `%%DocumentProcessColors` vira `Black` (com padding) e os itens
  Cyan/Magenta/Yellow de `xmpTPg:PlateNames` são trocados por espaços (o XML continua válido).
- **O0-05 Formatos não reconhecidos** (sem operador `cmyk` do AGM: `setcmykcolor`, `setrgbcolor`,
  `k`, imagens raster etc.) → arquivo **não** é alterado e o relatório diz "não suportado".
  Novos dialetos só entram com amostra (D-12).
- **O0-06 Segurança:** original salvo como `<nome>.orig.eps` antes de gravar; o processamento é
  idempotente (rodar 2× não muda nada).
- **O0-07 Vínculos do InDesign:** mesmo caminho e nome → o InDesign marca como "modificado"; um
  "Atualizar vínculo" basta. O layout não muda por causa da O0-01.
- **O0-08 Relatório antes/depois** por arquivo: cobertura por chapa (Ghostscript `tiffsep`,
  incluindo tintas especiais), cores trocadas, caixa antes/depois (deve ser igual), status.
- **O0-09 Prévia TIFF** embutida não é regenerada (é só para a tela). Ela continua mostrando o
  preto antigo, o que é inofensivo para a impressão; regenerar fica opcional (D-13).
- **O0-10 Overprint:** não é aplicado no EPS (pendente). No InDesign, pode-se ligar
  "Sobreimprimir preto [Preto]" só para objetos nativos; para gráficos colocados, depende do arquivo.
  Ver D-13.

## 3. Critério de aceite

CA-15: para cada EPS de equação com preto composto, após a correção: chapas C = M = Y = 0
(tiffsep), BoundingBox e HiResBoundingBox idênticas, tamanho do arquivo idêntico, e o InDesign
atualiza o vínculo sem mover o quadro.
