# PROVENIÊNCIA

Registro de **todas** as fontes de informação usadas na SESSÃO A. A SESSÃO B só pode usar o que
estiver aqui (via /spec), /spikes/RESULTADOS.md e /samples.

## 1. Fontes

| ID | Tipo | Descrição | Acesso | Usada em |
|---|---|---|---|---|
| DOC-PUBLICA:MTEF5 | Doc pública | "MathType MTEF v.5", Design Science, 09/08/1999 — cópia pública em https://rtf2latex2e.sourceforge.net/MTEF5.html | 2026-10-14 | MTEF.md, COMPORTAMENTO.md §A |
| DOC-PUBLICA:ECMA-376 | Norma pública | Office Open XML (unidade de `w:position`, `wp:inline`, `docPr`, extensão `svgBlip`) | conhecimento da norma | FORMATO_DOCX_OLE.md R-DOCX-03, gerador S1 |
| DOC-PUBLICA:PDF | Norma pública | ISO 32000 (operadores de cor `k/K/g/G/rg/RG`, ExtGState OP/op/OPM) | conhecimento da norma | PRESET.md §5, CA-06/08 |
| AMOSTRA:corpus_cn_questoes.docx | Amostra | 45 equações | /samples | FORMATO_DOCX_OLE, MTEF, COMPORTAMENTO |
| AMOSTRA:corpus_cn_resolucoes.docx | Amostra | 56 equações | /samples | idem |
| AMOSTRA:corpus_mt_questoes.docx | Amostra | 80 equações | /samples | idem + S4 |
| AMOSTRA:corpus_mt_resolucoes.docx | Amostra | 101 equações | /samples | idem |
| AMOSTRA:montagem_diagramada.pdf | Amostra | PDF diagramado, InDesign 19.4 Windows | /samples | INDESIGN.md (metadados) |
| AMOSTRA:resolucao_diagramada.pdf | Amostra | PDF diagramado (RGB, digital) | /samples | INDESIGN.md, RESULTADOS S5 |
| AMOSTRA:eq_composta.EPS e eq*_pan.eps (10 eqs.) | Amostra | EPS de equação salvos pelo Illustrator 24 | /samples, 2026-10-15 | O0_CORRETOR_EPS, RESULTADOS S5b |
| AMOSTRA:fig*.eps | Amostra | figuras (gráficos) em EPS | /samples, 2026-10-15 | O0_CORRETOR_EPS (casos que não devem mudar) |
| AMOSTRA:eq_pdfx_pan.pdf | Amostra | equação em PDF/X-1a, Illustrator 24 | /samples, 2026-10-15 | RESULTADOS S5b |
| AMOSTRA:paginas_grafica.pdf | Amostra | PDF de gráfica, 14 p., InDesign 15.1 Win | /samples, 2026-10-15 | COMPORTAMENTO A.5, RESULTADOS S5b |
| SPIKE:S5b, SPIKE:O0 | Spikes | `spikes/s5_eps/separar.py`, `spikes/o0_eps/corrigir_eps.py` | repo | O0_CORRETOR_EPS, COMPORTAMENTO |
| OBSERVACAO-USUARIO | Briefing | Briefing do projeto EqPress (§0–§9), 2026-10-14 | conversa | todos |
| OBSERVACAO-USUARIO 2026-10-16 | Conversa (SESSÃO B) | Saídas PDF + EPS + EMF; Word = .docx pronto + suplemento no Word Mac; interface com layout parecido, nomes próprios | conversa | PRESET §6, EDITOR ED-18/19, §4.1, PLANO F6b |
| SPIKE:S0 | Spike | Inventário do corpus (`spikes/s0_corpus/analisar_corpus.py`) | repo | todos os docs |
| SPIKE:S1…S5 | Spikes | `spikes/s1_s5_gerar/`, `spikes/s2_s3_sonda/` | repo | INDESIGN, PRESET, CRITERIOS |

## 1.1 Ferramentas e fontes embutidas nos instaladores (SESSÃO B, 2026-10-17)

| Item | Licença | Observação |
|---|---|---|
| tectonic 0.17 + pacote TeX (cache) | MIT; pacotes TeX com licenças livres (LPPL etc.) | executável separado |
| Ghostscript 10.08 | **AGPL-3.0** | executável separado; os instaladores o distribuem sob a AGPL-3.0 (`THIRD_PARTY_NOTICES.md`). Quem não puder cumprir a AGPL precisa da licença comercial da Artifex ou trocar a ferramenta |
| Inkscape 1.4 | GPL-2.0+ | executável separado (PDF → EMF) |
| STIX Two Math 2.13 | OFL-1.1 | `recursos/fontes`, com `STIX-OFL.txt` |
| Lato | OFL-1.1 | interface do app |
| MathLive, KaTeX | MIT | interface do app |
| MathJax 3.2.2 | Apache-2.0 | conferência do LaTeX no app |
| Python + bibliotecas (lxml, pikepdf, fontTools, olefile, jsonschema, Pillow) | BSD/MIT/MPL/Apache | empacotadas no `eqpress-nucleo.exe` (PyInstaller, GPL com exceção de distribuição) |

Fontes do Office/Windows (Calibri, Arial, Symbol) **não** vão no instalador: o EqPress usa as do PC.
A Symbol do Windows é lida pelo número do glifo, sem modificar o arquivo (PRESET P-08).

## 2. Fontes consultadas e **não** usadas

| Fonte | Motivo |
|---|---|
| docs.wiris.com (MTEF v5 atual, "How MTEF is stored", MTCode tables) | Exige login desde ≥ 2026; não acessado. Termos de uso desconhecidos. |
| Comentário do mantenedor do rtf2latex2e ("a doc mais recente tem licença incompatível com GPL") | Apenas registrado; o texto usado é a versão pública de 1999. |
| Implementações open source de leitores MTEF (LibreOffice, rtf2latex2e, mathtype-to-mathml etc.) | **Não consultadas** por decisão conservadora; ver Dúvida D-02. |

## 3. Nada disso foi usado (declaração)

Nenhum binário, instalador, plugin, fonte ou texto de interface do MathType foi aberto,
inspecionado ou copiado. Os únicos bytes de origem MathType analisados são os que **estão dentro dos
.docx fornecidos pelo usuário** (streams OLE e prévias WMF), conforme permitido em §1(b).

## 4. Requisitos × fonte

Cada requisito nos documentos de /spec traz a fonte na própria linha ou seção (prefixos R-DOCX,
R-OLE, R-PREV, R-MTEF, P-, ID-, VIN-, BL-, RE-, CA-). Requisito sem fonte = defeito da spec.

- `PLANO.md`: fases e otimizações transcritas do briefing (OBSERVACAO-USUARIO §3, §7, §9), com o ajuste de D-15 (LaTeX canônico).
