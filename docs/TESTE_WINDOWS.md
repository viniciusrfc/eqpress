# Teste do EqPress no Windows — roteiro para o colaborador

Leva uns 40 minutos. Anote o que acontecer em cada passo (um print ajuda muito) e devolva os
arquivos da lista do fim.

## 1. Instalar
1. Baixe o `EqPress-Setup.exe` que receber e dê dois cliques.
2. Se o Windows mostrar "O Windows protegeu o computador", clique em **Mais informações** e depois
   em **Executar assim mesmo** (o instalador ainda não tem assinatura digital).
3. Siga o instalador até o fim. Não precisa de internet.

## 2. Diagnóstico
1. Abra o **EqPress** pelo menu Iniciar.
2. Em **Início**, clique em **Copiar diagnóstico**. Esperado: "Tudo certo". Cole o texto copiado
   num e-mail e mande junto com o resto (vale também se aparecer "Há um problema").

## 3. Preparar um Word
1. Em **Início › Preparar um Word**, escolha um `.docx` de um capítulo real com equações do MathType
   e o padrão do livro. Clique em **Preparar**.
2. Esperado: "N de N equações prontas". Clique em **Abrir conferência** e confira as equações.

## 4. InDesign
1. Na tela Início, clique em **Instalar scripts no InDesign**. Feche e abra o InDesign.
2. Num documento novo, **Arquivo › Inserir** o `…_EqPress.docx` (está na pasta `…_EqPress`).
3. **Janela › Utilitários › Scripts › Usuário › EqPress - Vincular e alinhar equações**, escolha a
   pasta `…_EqPress`. Esperado no resumo: maior desvio de baseline ≤ 0,1 pt e nenhuma equação sem PDF.
4. **Janela › Saída › Visualização de separações**: as equações devem aparecer só na chapa preta.
5. Clique numa equação e rode **EqPress - Editar equação selecionada**. Esperado: o EqPress abre
   nessa equação. Mude algo, **Ctrl+S**, volte ao InDesign e rode "Vincular e alinhar" de novo.

## 5. Padrões
1. Em **Padrões dos livros**, crie um padrão (ex.: Arial 10), salve, e use **Exportar…**.
2. Em **Início › Trocar o padrão de um livro**, troque o livro do passo 3 para esse padrão e rode
   "Vincular e alinhar" no InDesign.

## Devolver
- prints de cada passo com problema;
- o arquivo `vinculo_indesign.txt` (pasta `…_EqPress`);
- um PDF exportado do InDesign (PDF/X-1a) com as equações;
- o `.docx` do autor usado (se puder compartilhar).
