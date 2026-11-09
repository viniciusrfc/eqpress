"""Os pedidos que a tela Padrões faz, na ordem, contra o núcleo (empacotado ou não), como o app:
uma linha JSON UTF-8 por pedido. Uso no CI: python tests/fluxo_app.py dist/eqpress-nucleo.exe
"""
import json
import subprocess
import sys
import time

cmd = [sys.argv[1], "servidor"] if len(sys.argv) > 1 else [sys.executable, "-m", "eqpress", "servidor"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def pedir(q):
    t = time.time()
    p.stdin.write((json.dumps(q, ensure_ascii=False) + "\n").encode("utf-8"))
    p.stdin.flush()
    r = json.loads(p.stdout.readline().decode("utf-8"))
    curto = {k: (v[:60] + "…" if isinstance(v, str) and len(v) > 60 else v) for k, v in r.items() if k != "padroes"}
    print(f"{q['cmd']}: {time.time() - t:.1f}s {curto}", flush=True)
    assert "erro" not in r, r["erro"]
    return r


lista = pedir({"cmd": "padroes"})["padroes"]
base = lista[0]
campos = {**base, "nome": "Teste CI – Arial 10", "familia": "Arial", "corpo": 10}
pedir({"cmd": "padrao_prova", "campos": campos, "base": base["arquivo"]})
v = pedir({"cmd": "padrao_salvar", "campos": campos, "base": base["arquivo"]})
assert any(x["arquivo"] == v["arquivo"] for x in pedir({"cmd": "padroes"})["padroes"])
print("fluxo ok")
