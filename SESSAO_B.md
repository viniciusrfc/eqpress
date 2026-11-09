# Como iniciar a SESSÃO B

Abra uma **sessão nova** do Claude Code nesta pasta (`/clear` ou um terminal novo) e cole o texto abaixo.

---

Você vai implementar o EqPress (SESSÃO B — implementação, clean room). Responda em português do Brasil.

Regras de clean room (obrigatórias):
- Leia SOMENTE `/spec`, `/spikes/RESULTADOS.md` e `/samples`. Não abra o restante de `/spikes`
  (código de protótipo), nem o histórico da SESSÃO A.
- PROIBIDO: decompilar, desmontar, depurar ou inspecionar binários do MathType; copiar código, ícones,
  textos de interface ou fontes proprietárias (MT Extra, Euclid etc.); usar código vazado.
- PERMITIDO: documentação pública do MTEF; estrutura OOXML/OLE dos .docx em /samples; comportamento
  descrito pelo usuário; bibliotecas open source MIT/Apache/BSD/LPPL/OFL.
- Se algo só puder ser obtido violando estas regras, PARE e pergunte.

Comece por `spec/PROVENIENCIA.md` e `spec/PLANO.md`. Siga as fases F1 → F8 do PLANO; cada fase só
termina com testes automatizados verdes sobre o corpus de `/samples`. Código de produção fora de
`/spikes`. TODO list, commits pequenos, CHANGELOG. Em caso de ambiguidade, pergunte antes de supor.

Primeira tarefa: F1 (extrator).
