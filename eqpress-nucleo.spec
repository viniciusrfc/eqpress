# PyInstaller: núcleo do EqPress num executável único (plano Windows, W2).
#   pyinstaller eqpress-nucleo.spec   →   dist/eqpress-nucleo(.exe)
# Os dados vão em sys._MEIPASS (plataforma.RECURSOS): schema e padrões de exemplo, STIX Two Math,
# scripts do InDesign.
from pathlib import Path

dados = [("spec/PRESET_SCHEMA.json", "spec"), ("recursos/fontes", "recursos/fontes"), ("indesign", "indesign")]
dados += [(str(p), "spec/exemplos") for p in Path("spec/exemplos").glob("*.json")]

a = Analysis(["nucleo.py"], datas=dados, hiddenimports=["eqpress.diagnostico", "eqpress.editor", "eqpress.biblioteca"])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name="eqpress-nucleo", console=True, upx=False)
