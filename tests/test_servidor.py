import json
import subprocess
import sys
from pathlib import Path


def test_servidor_fala_utf8():
    """O app conversa em UTF-8; no Windows o pipe do Python é cp1252 (acentos quebravam o núcleo)."""
    cmd = "Ação→Á"
    r = subprocess.run([sys.executable, "-m", "eqpress", "servidor"], input=(json.dumps({"cmd": cmd}, ensure_ascii=False) + "\n").encode("utf-8"),
                       capture_output=True, cwd=Path(__file__).parent.parent, timeout=60)
    assert json.loads(r.stdout.decode("utf-8")) == {"erro": f"comando desconhecido: {cmd}"}
