# PLANO — fases da SESSÃO B

Fonte: OBSERVACAO-USUARIO (briefing §3, §7, §9), com os ajustes decididos na SESSÃO A.
Cada fase só termina com **testes automatizados verdes** sobre o corpus de `/samples`.

## 1. Fases

| Fase | Entrega | Spec | Pronto quando |
|---|---|---|---|
| F1 | Extrator: lista as equações do .docx (id, posição, inline/display, bytes OLE) | FORMATO_DOCX_OLE | 282/282 equações do corpus listadas; nº de `w:object` = nº de linhas |
| F2 | Parser MTEF → árvore → **LaTeX** (canônico) + MathML (derivado); relatório de não suportadas, nunca falha em silêncio | MTEF, COMPORTAMENTO, EDITOR §2 e §5 | 282/282 sem erro; LaTeX renderiza em MathJax 3 e KaTeX (CA-17) |
| F3 | Renderizador: LaTeX + preset → PDF (100 % K, contorno) + EPS/EMF opcionais + JSON de métricas | PRESET, PRESET_SCHEMA, COMPORTAMENTO §A | CA-06 (separação) e métricas de baseline em todo o corpus |
| F4 | Gerador do .docx pronto: imagem EMF inline, ID em `docPr/@descr`, `w:position` | FORMATO_DOCX_OLE, INDESIGN §3–4 | abre no Word; contagem entrada = saída = /equacoes |
| F5 | Scripts UXP: "Vincular equações", "Editar equação selecionada", "Atualizar todas" + perfil Preflight `.idpp` | INDESIGN | baseline ≤ 0,1 pt (CA de baseline); nenhuma imagem do Word restante |
| F6 | Editor macOS (Tauri + MathLive), incluindo a tela "Padrão do livro" | EDITOR | CA-E1..E4 |
| F6b | Suplemento do Word para Mac (inserir/editar/converter) | EDITOR §4.1 | ED-40/41 no Word Mac do usuário |
| FW | Windows (colaboradores): instalador único, mesmo app e scripts | plano em `~/.claude/plans/…`; INDESIGN §9 | CA-11W; roteiro `docs/TESTE_WINDOWS.md` no PC do colaborador |
| F7 | Re-estilização em lote | INDESIGN §6 | trocar preset + "Atualizar todas" atualiza o livro |
| F8+ | Otimizações O1–O8 (abaixo), nesta ordem | — | cada uma com seu teste |

Ajuste em relação ao briefing: F2 gera LaTeX como fonte canônica e MathML derivado (D-15, EDITOR ED-01).

## 2. CLI final

`eqpress estilizar|vincular|reestilizar|relatorio|depara <arquivo|pasta> --preset x.json`
(+ `eqpress renderizar NNNN.json`, usado pelo editor, EDITOR ED-21).

## 3. Otimizações (fases opcionais, em ordem de valor)

- **O0** Corretor de EPS existentes — **ESTACIONADO** a pedido do usuário (ver O0_CORRETOR_EPS.md).
- **O1** Preset a partir do InDesign: lê estilos do .indd/modelo e gera o preset (INDESIGN §7).
- **O2** Equações simples viram texto vivo com estilo de caractere; regras no preset (PRESET §7).
- **O3** Biblioteca de presets por coleção, versionada (`livroX_v2.json`, PRESET §8).
- **O4** Relatório de QA por documento: total, não suportadas, convertidas em texto, duplicadas
  (render único por hash), vazias, fontes ausentes.
- **O5** Prova visual: HTML lado a lado (prévia original do Word × render novo).
- **O6** Depara: .docx do autor × livro final (contagem e MathML de cada equação).
- **O7** Lote: pasta de capítulos com o mesmo preset.
- **O8** Volta para o autor: .docx com equações nativas do Word (OMML).

## 4. Ambiente disponível no Mac (SESSÃO A)

- Python 3.12; Ghostscript; Inkscape; **tectonic** (motor XeTeX). **Não há LuaLaTeX instalado.**
  O briefing propõe LuaLaTeX; tectonic já mostrou funcionar com fontes OpenType (SPIKE S1–S5).
  A escolha do motor é da SESSÃO B; qualquer motor precisa passar pela normalização de cor (RESULTADOS S5 achado 1).
- InDesign 2024 (19.4) e 2026; Word; Acrobat DC.
- Fontes: STIX Two Math e Symbol do sistema; MT Extra instalada mas **proibida** (PRESET P-07).

## 5. Pendências que não bloqueiam o início

- D-09: equações sintéticas com templates ausentes do corpus (seta com rótulo, chave horizontal,
  ∑/∫ com limites) → afeta só a cobertura de F2 para templates raros; até lá, testar pela doc pública.
- D-01: casos com print do resultado esperado (COMPORTAMENTO parte B) → afeta a calibração fina de F3.
- D-07, D-08, D-11: ver PROVENIENCIA/CRITERIOS; perguntar ao usuário quando a fase chegar.
