# EqPress

Prepara equações do MathType para livros diagramados no Adobe InDesign, no Mac e no Windows.

> **Apoie o projeto:** o EqPress é gratuito. Se ele ajuda no seu trabalho, a chave Pix é
> `viniciusrfc@gmail.com`.

O EqPress lê um Word (`.docx`) com equações do MathType e refaz cada uma no padrão do livro: fonte,
corpo, cor e tinta. O resultado é um PDF vetorial por equação, em 100K ou tinta especial, com
sobreimpressão. No InDesign, um script troca as imagens pelos PDFs e alinha cada equação à linha de
base do texto. Depois, é possível editar uma equação ou trocar o padrão do livro inteiro sem inserir
o Word de novo.

> *English: EqPress restyles MathType equations from `.docx` files into print-ready vector PDFs and
> places them in Adobe InDesign, aligned to the baseline. macOS and Windows. The interface and docs
> are in Brazilian Portuguese. MIT licensed.*

**O EqPress é independente.** Não tem vínculo com a Wiris/Design Science (MathType), a Adobe ou a
Microsoft e não inclui código delas. O MathType não precisa estar instalado para rodar o EqPress.

## Requisitos

| | Mac | Windows |
|---|---|---|
| Sistema | macOS 15 ou mais novo | Windows 10 ou 11, 64 bits (testado no 11) |
| Processador | Apple Silicon (M1 ou mais novo). Intel não é compatível | x64 |

Você também vai precisar de:

- **Adobe InDesign**, para montar o livro. Testado nas versões 2024 e 2026 no Mac e no InDesign para
  Windows.
- **Word com equações do MathType**, em `.docx`. Equações nativas do Word e arquivos `.doc` não são
  processados.
- **A fonte do livro instalada** no computador.
- **No Mac, de preferência o Microsoft Word.** A fonte Symbol do Office é a mesma usada pelo MathType.
  Sem ela, o EqPress usa a Symbol do macOS, que desenha algumas setas de outro jeito.

Tudo o mais vem no instalador (Python, TeX, Ghostscript, Inkscape, STIX Two Math), e o EqPress
funciona sem internet.

## Instalação

Baixe a versão mais recente em **[Releases](https://github.com/viniciusrfc/eqpress/releases/latest)**.

Os instaladores ainda não têm assinatura digital, por isso o sistema mostra um aviso na primeira vez.
O código está aqui e os instaladores são gerados pelo GitHub Actions a partir dele.

### Mac

1. Baixe o `EqPress.dmg` e abra.
2. Arraste o **EqPress** para **Aplicativos**.
3. Abra o EqPress. O macOS vai avisar que não pode verificar o app. Feche o aviso, sem mover o app
   para o Lixo.
4. Vá em **Ajustes do Sistema › Privacidade e Segurança**, role até **Segurança** e clique em
   **Abrir Mesmo Assim**. Confirme com sua senha.

Se o macOS disser que o app está "danificado", rode no Terminal e abra de novo:

```sh
xattr -dr com.apple.quarantine /Applications/EqPress.app
```

### Windows

1. Baixe o `EqPress_<versão>_x64-setup.exe` e dê dois cliques.
2. Se aparecer "O Windows protegeu o computador", clique em **Mais informações** e em
   **Executar assim mesmo**.
3. Siga o instalador. Não precisa de senha de administrador. Se o WebView2 não estiver presente, o
   instalador o baixa, e aí sim precisa de internet.
4. Abra o **EqPress** pelo menu Iniciar.

### Depois de instalar, nos dois sistemas

1. Abra o InDesign uma vez e feche, se ele nunca foi aberto neste computador.
2. No EqPress, em **Início**, clique em **Instalar scripts no InDesign**.
3. Clique em **Copiar diagnóstico**. O esperado é "Tudo certo".
4. Feche o InDesign, se estiver aberto, e abra de novo. Os scripts aparecem em **Janela › Utilitários
   › Scripts › Usuário**.

## Como usar

### 1. Crie o padrão do livro

Na aba **Padrões dos livros**, clique em **Novo padrão** e defina nome, fonte, corpo, variáveis retas
ou em itálico, cor e tinta. Para tinta especial, use o nome idêntico ao do InDesign. A prova ao lado
mostra o resultado. Clique em **Salvar como versão nova**.

Use **Exportar…** e **Importar…** para passar padrões a outras pessoas da equipe.

### 2. Prepare o Word

Em **Início › Preparar um Word**, escolha o `.docx` e o padrão e clique em **Preparar**. Quando
terminar, clique em **Abrir conferência** e confira cada equação dentro da frase.

Ao lado do `.docx` aparece a pasta `<nome>_EqPress`:

| Arquivo | Para quê |
|---|---|
| `<nome>_EqPress.docx` | É este que entra no InDesign |
| `<nome>_EqPress_editavel.docx` | Aparência nova, com o MathType ainda editável |
| `equacoes/` | Um PDF e um JSON por equação (EPS e EMF, se ativados no padrão) |
| `conferir.html` | Página de conferência |
| `relatorio.json` | Resumo, com equações que deram erro |

Não renomeie nem mova o conteúdo da pasta, porque os vínculos do InDesign dependem dela. Uma equação
com erro mantém o original e aparece no relatório.

### 3. Monte no InDesign

1. **Arquivo › Inserir** e escolha `<nome>_EqPress.docx`, como você já faz com o Word.
2. No painel Scripts, rode **EqPress - Vincular e alinhar equações** e escolha a pasta `<nome>_EqPress`.
3. Leia o resumo. O esperado é desvio de linha de base de no máximo 0,1 pt e nenhuma equação sem PDF.
   O detalhe de cada equação fica em `vinculo_indesign.txt`.
4. Em **Janela › Saída › Visualização de separações**, confira a chapa das equações.

### 4. Ajuste depois de montar

**Editar uma equação:** selecione a equação no InDesign e rode **EqPress - Editar equação
selecionada**. O EqPress abre nela. Edite, salve com ⌘S ou Ctrl+S, volte ao InDesign e rode
**Vincular e alinhar** de novo. A versão anterior fica no histórico.

**Trocar o padrão do livro inteiro:** em **Início › Trocar o padrão de um livro já montado**, escolha
a pasta `_EqPress` e o padrão novo. Depois rode **Vincular e alinhar** no InDesign. Equações com
ajuste próprio continuam como estão.

**Correções de conteúdo** devem ser feitas pelo autor no MathType, no `_editavel.docx` ou no original.
O EqPress cuida das etapas de diagramação e não grava objetos MathType.

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| Aviso de fonte ou face ausente | Instale a fonte do livro, inclusive o itálico e o negrito se forem usados, e reabra o EqPress |
| "Não achei o InDesign" ao instalar scripts | Abra e feche o InDesign uma vez e tente de novo |
| Scripts não aparecem no painel | Feche e abra o InDesign. Depois de atualizar o EqPress, instale os scripts de novo |
| "Editar equação selecionada" não abre o EqPress | Abra o EqPress uma vez. No Mac, confirme que ele está em **Aplicativos** |
| Equação sem PDF no resumo do script | Confira se escolheu a pasta `_EqPress` certa e se ela não foi alterada |

Para pedir ajuda, abra uma [issue](https://github.com/viniciusrfc/eqpress/issues) e cole o texto de
**Copiar diagnóstico**. Não anexe material protegido por direitos autorais.

Os padrões ficam em `~/Library/Application Support/EqPress/Padrões` no Mac e em
`%APPDATA%\EqPress\Padrões` no Windows. Ao desinstalar, essas pastas não são apagadas.

## Limitações conhecidas

- Mac Intel e Linux não têm instalador.
- Só são processadas equações do MathType (objetos OLE) em `.docx`.
- A edição pelo InDesign e a troca de padrão ainda não foram conferidas por completo no Windows.
- Não há suplemento para o Word.

## Para quem desenvolve

O núcleo é em Python (`eqpress/`), o app em Tauri 2 + MathLive (`editor/`) e os scripts do InDesign
em ExtendScript (`indesign/`). As decisões técnicas estão em `spec/`.

**Núcleo.** Precisa de Python 3.12.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# macOS, além disso:
brew install ghostscript tectonic && brew install --cask inkscape
# Windows: Ghostscript e Inkscape (choco install ghostscript inkscape) e o tectonic no PATH

.venv/bin/python -m eqpress diagnostico --familia Arial --completo
.venv/bin/python -m pytest -q
.venv/bin/python -m eqpress testar arquivo.docx --familia Arial --corpo 10
```

Os testes que usam o corpus `samples/` são pulados sem ele, porque esse material é protegido e não é
versionado. Para os testes da parte web, rode `npm install` em `ferramentas/web`.

**App.** Precisa de Node 22 e Rust. O Tauri exige um núcleo em `editor/src-tauri/binaries/`. Em
desenvolvimento, use um atalho para o Python do repositório (exemplo para Mac Apple Silicon):

```sh
mkdir -p editor/src-tauri/binaries
printf '#!/bin/sh\nPYTHONPATH="%s" exec "%s/.venv/bin/python" -m eqpress "$@"\n' "$PWD" "$PWD" \
  > editor/src-tauri/binaries/eqpress-nucleo-aarch64-apple-darwin
chmod +x editor/src-tauri/binaries/eqpress-nucleo-aarch64-apple-darwin
cd editor && npm ci && npm run vendor && npx tauri dev
```

**Instaladores.** São gerados em `.github/workflows/` (`mac.yml` e `windows.yml`). Para lançar uma
versão, atualize `version` em `editor/src-tauri/tauri.conf.json`, `Cargo.toml` e `eqpress/__init__.py` e envie uma tag
`vX.Y.Z`. O CI publica o `.dmg` e o `.exe` no Release.

**Contribuições.** Issues e pull requests são bem-vindos.

Regra importante: o projeto é *clean room*. Não contribua com nada obtido por engenharia reversa do
MathType, nem com código, ícones, textos ou fontes proprietárias. A origem de cada informação está em
`spec/PROVENIENCIA.md`.

## Licença

Código sob a licença [MIT](LICENSE). Os instaladores incluem componentes de terceiros, entre eles
Ghostscript (AGPL-3.0) e Inkscape (GPL), sob as licenças deles. Veja
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
