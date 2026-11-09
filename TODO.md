# TODO

## SESSÃO A
- [x] S0 inventário do corpus (282 equações, 100 % parseadas)
- [x] Gerar arquivos de teste S1–S5
- [x] spec/: FORMATO_DOCX_OLE, MTEF, COMPORTAMENTO (parte A), PRESET_SCHEMA + PRESET, INDESIGN, CRITERIOS_ACEITE, PROVENIENCIA
- [x] S1, S2, S3, S4 concluídos (InDesign 19.4 Mac)
- [x] S5: PDFs colocados direto no InDesign → 100K sai só em K, sobreimpressão preservada
- [ ] Usuário: responder dúvidas D-01…D-10
- [ ] COMPORTAMENTO parte B (casos do usuário)
- [ ] S6 com equações sintéticas do usuário
- [ ] Fechar decisões ⏳ em INDESIGN.md e PRESET (imagem_docx, canal do ID)
- [x] spec/EDITOR.md
- [x] D-15 respondida: fonte canônica LaTeX, portátil para web (ED-04, CA-17)
- [x] D-03 respondida: manter 8 % e testar na prova visual
- [x] D-04 respondida: fonte/corpo por livro, calibrados no editor (EDITOR §3.1)
- [ ] Perfil de Preflight .idpp → movido para F5 (spec/PLANO.md)
- [x] S5b: análise dos EPS e do PDF de gráfica
- [x] O0: protótipo do corretor de EPS no lugar
- [ ] Usuário: testar eq_composta_100K.eps no InDesign
- [ ] Usuário: rodar sondar.jsx numa CÓPIA de um .indd real (formato das equações incorporadas, D-14)
- [ ] ~~O0 modo documento~~ ESTACIONADO a pedido do usuário (foco no editor/pipeline principal)

- [x] spec/PLANO.md + SESSAO_B.md (handoff)

## SESSÃO B (nova sessão, ver SESSAO_B.md)
- [x] F1 extrator (282/282, testes verdes)
- [x] F2 parser MTEF → LaTeX + MathML (282/282, KaTeX + MathJax)
- [x] F3 renderizador (282 PDFs, 100K/especial, EPS/EMF, métricas)
- [ ] Usuário: PDF/X (perfil ICC) e D-03 (sub_subscrito 8 %)
- [x] F4 gerador do .docx pronto (282 trocadas, testes verdes)
- [ ] Usuário: abrir um `_EqPress.docx` no Word e importar no InDesign (Arquivo > Inserir)
- [x] F5 script InDesign: vincular PDF 100K + baseline (teste automático 2024/2026)
- [ ] Usuário: rodar o script no documento real
- [ ] Perfil de Preflight .idpp (INDESIGN §8)
- [x] F6a editor EqPress.app: paletas, estilo/tamanho, LaTeX, prévia real, salvar + histórico; abrir pelo InDesign
- [ ] Usuário: testar "Editar equação selecionada" → editor → salvar → "Vincular e alinhar"
- [ ] F6b tela "Padrão do livro", equação nova, prévia < 1 s (motor TeX sempre aberto)
- [x] FW W0–W4: Windows (CI, núcleo portátil, Symbol por glifo, núcleo empacotado, instalador)
- [x] FW W5: teste no PC do colaborador (0.1.1): Preparar, Vincular e alinhar 14/14, desvio 0,000 pt
- [ ] FW: conferir no Windows "Editar equação selecionada" (InDesign → app → salvar → Vincular) e Trocar padrão
- [ ] F6c suplemento Word Mac; F7, F8 conforme spec/PLANO.md
