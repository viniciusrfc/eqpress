"""CLI: python -m eqpress estilizar|renderizar (PLANO §2)."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .lote import estilizar, renderizar_json


def main():
    ap = argparse.ArgumentParser(prog="eqpress")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("estilizar", help=".docx → equacoes/NNNN.pdf + .json + relatorio.json")
    a.add_argument("docx")
    a.add_argument("--preset", required=True)
    a.add_argument("--saida", required=True)
    b = sub.add_parser("renderizar", help="re-renderiza NNNN.json (editor)")
    b.add_argument("json")
    b.add_argument("--preset", required=True)
    c = sub.add_parser("testar", help="estiliza o .docx ao lado dele e abre a página de conferência")
    c.add_argument("docx")
    c.add_argument("--preset", help="arquivo de padrão (.json); sem ele, usa --familia/--corpo ou pergunta")
    c.add_argument("--familia", help="fonte das equações, ex.: Arial")
    c.add_argument("--corpo", type=float, default=10, help="corpo em pt (padrão 10)")
    c.add_argument("--italico", action="store_true", help="variáveis em itálico")
    c.add_argument("--perguntar", action="store_true", help="pergunta fonte/corpo/itálico em janelas do macOS")
    sub.add_parser("servidor", help="processo do editor (uma linha JSON por pedido)")
    g = sub.add_parser("diagnostico", help="ferramentas, fontes e render de teste deste computador")
    g.add_argument("--familia", default="Calibri")
    g.add_argument("--completo", action="store_true", help="também gera PDF, EPS e EMF e confere a cor")
    d = sub.add_parser("reestilizar", help="troca a fonte/corpo de todas as equações de uma pasta _EqPress")
    d.add_argument("pasta")
    d.add_argument("--preset", help="padrão novo (.json)")
    d.add_argument("--familia")
    d.add_argument("--corpo", type=float)
    d.add_argument("--italico", choices=["sim", "nao"])
    d.add_argument("--perguntar", action="store_true", help="pergunta fonte/corpo/itálico em janelas do macOS")
    args = ap.parse_args()
    if args.cmd == "reestilizar":
        from . import padrao
        from .lote import reestilizar
        pasta = Path(args.pasta)
        if pasta.name == "equacoes":
            pasta = pasta.parent
        preset = args.preset
        if not preset:
            if args.perguntar:
                escolha = padrao.perguntar()
                if escolha is None:
                    return 0
                familia, corpo, italico = escolha
            else:
                familia, corpo = args.familia, args.corpo
                italico = None if args.italico is None else args.italico == "sim"
            atual = json.loads((pasta / "padrao.json").read_text(encoding="utf-8"))
            novo = padrao.aplicar(atual, familia, corpo, italico)
            novo["versao"] = atual.get("versao", 1) + 1  # O3: versão nova, a anterior vai ao histórico
            preset = pasta / "padrao_novo.json"
            preset.write_text(json.dumps(novo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"Refazendo as equações de {pasta.name}…")
        rel = reestilizar(pasta, preset)
        if Path(preset).name == "padrao_novo.json":
            Path(preset).unlink()
        msg = f"{rel['refeitas']} de {rel['equacoes']} equações refeitas com o padrão {rel['preset']}."
        if rel["ajustes_individuais"]:
            msg += f" {rel['ajustes_individuais']} com ajuste próprio (mantido)."
        if rel["com_erro"]:
            msg += f" Com erro (PDF anterior mantido): {', '.join(e['id'] for e in rel['com_erro'])}."
        msg += " No InDesign, rode \"EqPress - Vincular e alinhar equações\"."
        print(msg)
        if args.perguntar:
            subprocess.run(["osascript", "-e", f'display dialog {json.dumps(msg)} with title "EqPress" buttons {{"OK"}}'])
        return 0 if not rel["com_erro"] else 1
    if args.cmd == "diagnostico":
        from .diagnostico import completo, diagnostico
        d = diagnostico(args.familia)
        ok = d["render"].get("ok") and (not args.completo or completo(args.familia, d))
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0 if ok else 1
    if args.cmd == "servidor":
        from .editor import servidor
        servidor()
        return 0
    if args.cmd == "testar":
        from .prova import gerar
        docx = Path(args.docx)
        pasta = docx.with_name(docx.stem + "_EqPress")
        preset = args.preset
        if not preset:
            from . import padrao
            escolha = padrao.perguntar() if args.perguntar else (args.familia, args.corpo, args.italico)
            if escolha is None:
                return 0  # cancelado
            familia, corpo, italico = escolha
            pasta.mkdir(parents=True, exist_ok=True)
            preset = pasta / "padrao.json"
            preset.write_text(json.dumps(padrao.criar(familia or "Calibri", corpo, italico),
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"Padrão: {familia or 'Calibri'} {corpo:g} pt, variáveis {'em itálico' if italico else 'retas'}")
        print(f"Processando {docx.name}…")
        rel = estilizar(docx, preset, pasta)
        pagina = gerar(docx, pasta, rel)
        print(f"{rel['pdfs']} de {rel['equacoes']} equações prontas em {pasta}")
        print(f"Word para o InDesign: {pasta / rel['docx_saida']}")
        print(f"Word editável (MathType): {pasta / rel['docx_editavel']}")
        if not os.environ.get("EQPRESS_SEM_ABRIR"):
            from .plataforma import abrir
            abrir(pagina)
        return 0
    if args.cmd == "estilizar":
        rel = estilizar(args.docx, args.preset, args.saida)
        print(json.dumps({k: rel[k] for k in ("equacoes", "pdfs", "status")}, ensure_ascii=False))
        return 0 if rel["status"] == "ok" else 1
    s = renderizar_json(args.json, args.preset)
    print(json.dumps({**s.metricas(), "erro": s.erro}, ensure_ascii=False))
    return 0 if s.erro is None else 1


if __name__ == "__main__":
    sys.exit(main())
