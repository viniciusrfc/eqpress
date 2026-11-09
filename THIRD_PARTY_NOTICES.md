# Componentes de terceiros

O código deste repositório está sob a licença MIT (`LICENSE`). Os instaladores do EqPress também
trazem os programas e bibliotecas abaixo, cada um sob a sua própria licença. A licença MIT do
EqPress **não** se aplica a eles.

As versões exatas de cada instalador ficam em `ferramentas/licencas/VERSOES.txt`, dentro do app.

## Programas separados

O EqPress chama estes programas pela linha de comando.

| Programa | Licença | Código-fonte |
|---|---|---|
| [Ghostscript](https://ghostscript.com) | AGPL-3.0 | <https://github.com/ArtifexSoftware/ghostpdl-downloads/releases> |
| [Inkscape](https://inkscape.org) | GPL-2.0 ou posterior | <https://gitlab.com/inkscape/inkscape> e <https://inkscape.org/release/> |
| [Tectonic](https://tectonic-typesetting.github.io) | MIT | <https://github.com/tectonic-typesetting/tectonic> |
| Pacotes TeX usados pelo Tectonic | LPPL e outras licenças livres | <https://github.com/tectonic-typesetting/tectonic-texlive-bundles> |

Ghostscript e Inkscape não têm alterações no código. No Mac, o Ghostscript é compilado do código-fonte
original. No Windows, vem do pacote oficial. O Inkscape é distribuído em cópia reduzida: foram
retirados traduções, tutoriais, exemplos, extensões, temas, modelos, documentação e o Python
embutido. Os comandos exatos estão em `.github/workflows/`.

Os textos completos da AGPL e da GPL estão em `recursos/licencas/`, no repositório, e em
`ferramentas/licencas/`, no app instalado.

Quem redistribuir os instaladores precisa cumprir os termos da AGPL e da GPL para esses dois
programas, inclusive quanto ao acesso ao código-fonte correspondente.

## Bibliotecas e fontes

| Componente | Licença |
|---|---|
| Tauri e plugins | MIT ou Apache-2.0 |
| MathLive, KaTeX | MIT |
| MathJax | Apache-2.0 |
| Python | PSF-2.0 |
| PyInstaller (carregador do núcleo) | GPL-2.0 com exceção para distribuição |
| lxml, olefile | BSD |
| fontTools, jsonschema | MIT |
| Pillow | MIT-CMU (HPND) |
| pikepdf | MPL-2.0 |
| qpdf (dentro do pikepdf) | Apache-2.0 |
| STIX Two Math | SIL OFL 1.1 (`recursos/fontes/STIX-OFL.txt`) |
| Lato | SIL OFL 1.1 |

No Windows, o instalador pode acionar o instalador do Microsoft Edge WebView2 Runtime, sob os termos
da Microsoft.

## Marcas e fontes do sistema

MathType, InDesign, Word, Windows e macOS são marcas de seus respectivos donos. O EqPress é
independente e não tem vínculo com essas empresas.

Calibri, Arial, Symbol e outras fontes comerciais **não** vão no instalador. O EqPress usa as fontes
já instaladas no computador de quem o executa.
