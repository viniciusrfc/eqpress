# CRITÉRIOS DE ACEITE

Fonte de todos os critérios: OBSERVACAO-USUARIO §8, com o método de verificação definido aqui.
"Auto" = teste automatizado na SESSÃO B; "Manual" = conferência do usuário com roteiro.

| ID | Critério | Medida / limite | Como verificar | Tipo |
|---|---|---|---|---|
| CA-01 | Sem perda | nº de `w:object` de equação na entrada = nº de imagens de equação no .docx de saída = nº de PDFs em /equacoes (+ convertidas em texto vivo, listadas). Divergência ≠ 0 → listada no relatório e lote marcado "com divergências" | contagem no relatório; teste com os 4 .docx de /samples (282 eqs) e um sintético de 300+ | Auto |
| CA-02 | Cobertura do parser | 282/282 equações do corpus convertidas; seletores 0–37 cada um com teste; não suportadas = 0 no corpus | `pytest` | Auto |
| CA-03 | Importação igual a hoje | Arquivo > Inserir do .docx de saída, sem opções diferentes das atuais; único passo extra = rodar "Vincular equações" | roteiro manual com 1 capítulo | Manual |
| CA-04 | Baseline | \|(fundo do quadro − baseline) − profundidade_pt\| ≤ 0,1 pt em 100 % das equações inline | script de sonda (coluna `desce_abaixo_baseline_pt`) comparado ao JSON | Auto (no InDesign) |
| CA-05 | Vetor | PDF de equação sem imagem raster (0 XObjects /Image) e, no PDF final de gráfica, equações como vetor | inspeção do PDF (auto) + ampliação 800 % no Acrobat (manual) | Auto + Manual |
| CA-06 | Separações 100 % K | Com preset 100 % K: cobertura C = M = Y = 0 em 100 % das equações **e** nenhum operador de cor fora de `0 0 0 1 k/K` (ou da tinta especial do preset) no conteúdo do PDF | Ghostscript `inkcov` **+** varredura de operadores (o `inkcov` sozinho não distingue DeviceGray de K — SPIKE:S5) | Auto |
| CA-07 | Separações no PDF de gráfica | Visualização de separações do Acrobat: chapas C/M/Y vazias nas áreas de equação | roteiro manual | Manual |
| CA-08 | Overprint | Com `sobreimpressao: true`, ExtGState com OP/op = true e OPM = 1 aplicado ao conteúdo; Acrobat > Visualização de saída mostra overprint | auto (pikepdf) + manual | Auto + Manual |
| CA-09 | Re-estilização | Trocar preset + `reestilizar` + "Atualizar todas": zero quadros movidos/escalados manualmente; vínculos 100 % atualizados; baselines dentro de CA-04 | contagem de vínculos "OK" após atualização | Manual com script |
| CA-10 | Edição | Editar equação → salvar → "Atualizar vínculo" reflete a mudança, baseline dentro de CA-04 | roteiro manual | Manual |
| CA-11W | Windows | Instala e roda no Windows 10/11 x64 sem MathType e **sem internet** depois de instalado; Word, InDesign Windows (Vincular/Editar), editor e padrões | CI (`windows.yml`: testes + `diagnostico --completo` do núcleo empacotado, offline) + roteiro `docs/TESTE_WINDOWS.md` no PC do colaborador | Auto + Manual |
| CA-11 | Plataforma | Roda em macOS Apple Silicon sem Windows, Rosetta ou MathType instalados | CI/execução numa máquina limpa | Manual |
| CA-12 | Clean room | Nenhum arquivo de produção referencia fontes do MathType; PROVENIENCIA.md cobre 100 % dos requisitos | lint de fontes + revisão | Auto + revisão |
| CA-13 | Relatório | Toda equação não suportada, convertida em texto, duplicada, vazia ou com fonte ausente aparece no relatório (nunca falha silenciosa) | testes com casos sintéticos de cada tipo | Auto |
| CA-15 | O0: EPS corrigido | chapas C = M = Y = 0; BoundingBox, HiResBoundingBox e tamanho do arquivo idênticos; vínculo atualiza sem mover o quadro | `separar.py` + comparação de bytes; roteiro manual no InDesign | Auto + Manual |
| CA-16 | Cor por contexto | com o preset de resolução, 100 % das equações só na tinta especial definida, sem sobreposição com C/M/Y/K | tiffsep por equação | Auto |
| CA-17 | LaTeX portátil | 100 % das equações do corpus: fonte LaTeX renderiza sem erro em LuaLaTeX, MathJax 3 e KaTeX | teste automatizado nos 3 motores | Auto |
| CA-14 | Desempenho | ⏳ a definir pelo usuário (Dúvida D-08); proposta: 300 equações em ≤ 2 min num Mac M-series | cronômetro no lote de 282 | Auto |
