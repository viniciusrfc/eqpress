"""Tudo o que muda entre macOS e Windows mora aqui (plano Windows, W1): pastas de dados e cache,
pastas de fontes, onde achar as ferramentas e como abrir/mostrar arquivos.

O app instalado passa EQPRESS_FERRAMENTAS (pasta com tectonic, Ghostscript, Inkscape) e o
PyInstaller expõe os recursos empacotados em sys._MEIPASS; em desenvolvimento vale o repositório.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

WINDOWS = sys.platform == "win32"
RAIZ = Path(__file__).resolve().parent.parent
# recursos empacotados (spec/PRESET_SCHEMA.json, spec/exemplos, recursos/fontes, indesign/*.jsx)
RECURSOS = Path(getattr(sys, "_MEIPASS", RAIZ))

if WINDOWS:
    DADOS = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "EqPress"
    CACHE = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "EqPress"
    _windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    PASTAS_FONTES = [_windir / "Fonts",
                     Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"]
else:
    DADOS = Path.home() / "Library/Application Support/EqPress"
    CACHE = Path.home() / "Library/Caches/EqPress"
    PASTAS_FONTES = [Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
                     Path("/Library/Fonts"), Path.home() / "Library/Fonts",
                     *sorted(Path("/Applications").glob("Microsoft *.app/Contents/Resources/DFonts"))]
# fontes que o EqPress leva junto (STIX Two Math: o Windows não tem; OFL)
PASTAS_FONTES.append(RECURSOS / "recursos/fontes")

# nome do executável de cada ferramenta
_NOMES = {"gs": ["gswin64c", "gswin32c", "gs"] if WINDOWS else ["gs"],
          "tectonic": ["tectonic"], "inkscape": ["inkscape"]}
# onde procurar além do PATH (app aberto pelo Finder/InDesign recebe PATH mínimo no Mac)
_PASTAS_EXTRAS = [] if WINDOWS else ["/opt/homebrew/bin", "/usr/local/bin", "/Library/TeX/texbin",
                                     "/Applications/Inkscape.app/Contents/MacOS"]


def ferramenta(nome):
    """Caminho do executável (1º o que veio no instalador, depois o sistema) ou None."""
    pastas = []
    embutidas = os.environ.get("EQPRESS_FERRAMENTAS")
    if embutidas:
        base = Path(embutidas)
        # cada ferramenta pode vir na raiz ou numa subpasta (bin/ do Ghostscript, Inkscape/bin…,
        # no Mac Inkscape.app/Contents/MacOS)
        pastas += [str(p) for p in [base, *base.glob("*"), *base.glob("*/bin"), *base.glob("*.app/Contents/MacOS")]
                   if p.is_dir()]
    caminho = os.pathsep.join(pastas + [os.environ.get("PATH", "")] + _PASTAS_EXTRAS)
    for n in _NOMES[nome]:
        achado = shutil.which(n, path=caminho)
        if achado:
            return achado
    return None


def abrir(caminho):
    """Abre o arquivo no programa padrão do sistema."""
    if WINDOWS:
        os.startfile(str(caminho))  # noqa: S606
    else:
        subprocess.run(["open", str(caminho)])


def mostrar(caminho):
    """Mostra o arquivo selecionado no Finder/Explorer."""
    if WINDOWS:
        subprocess.run(["explorer", f"/select,{Path(caminho)}"])
    else:
        subprocess.run(["open", "-R", str(caminho)])


def pastas_scripts_indesign():
    """Pastas 'Scripts Panel' de usuário de cada versão do InDesign instalada."""
    if WINDOWS:
        base = Path(os.environ.get("APPDATA", "")) / "Adobe/InDesign"
    else:
        base = Path.home() / "Library/Preferences/Adobe InDesign"
    return sorted(base.glob("Version */*/Scripts/Scripts Panel"))


# Windows: programas chamados pelo núcleo sem abrir janela de console
SEM_JANELA = {"creationflags": 0x08000000} if WINDOWS else {}


def ambiente_tectonic():
    """(variáveis, argumentos) extras para o tectonic. No app instalado, o pacote de arquivos do
    TeX vem pronto em <ferramentas>/tectonic-cache: é copiado uma vez para o cache do usuário
    (o TeX grava formatos ali) e o tectonic roda sem internet (--only-cached)."""
    embutidas = os.environ.get("EQPRESS_FERRAMENTAS")
    semente = Path(embutidas) / "tectonic-cache" if embutidas else None
    # só com o pacote completo (VERSAO é gravado no fim da montagem); enquanto é montado, o
    # tectonic baixa normalmente para o TECTONIC_CACHE_DIR indicado
    if not semente or not (semente / "VERSAO").exists():
        return {}, []
    cache = CACHE / "tectonic"
    marca_nova = (semente / "VERSAO").read_text(encoding="utf-8") if (semente / "VERSAO").exists() else ""
    marca = cache / "VERSAO"
    if not marca.exists() or marca.read_text(encoding="utf-8") != marca_nova:
        shutil.copytree(semente, cache, dirs_exist_ok=True)
    return {"TECTONIC_CACHE_DIR": str(cache)}, ["--only-cached"]
