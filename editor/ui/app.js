// EqPress — editor de fórmulas (EDITOR §1–§5). Interface própria (ED-17): nomes, ícones e textos
// do EqPress; os botões das paletas são desenhados pelo MathLive a partir do próprio LaTeX.
import { MathfieldElement, convertLatexToMarkup } from "./vendor/mathlive/mathlive.min.mjs";

MathfieldElement.fontsDirectory = "./vendor/mathlive/fonts";
MathfieldElement.soundsDirectory = null;

const tauri = window.__TAURI__;
const $ = (id) => document.getElementById(id);
const campo = $("campo");
const latexTxt = $("latex");
const estado = { json: null, preset: null, original: null, alterado: false, pedido: 0, ajustes: {} };

// --- paletas (ED-10/ED-18): fileira 1 = símbolos, fileira 2 = modelos -------------------------
// #0 = seleção atual, #? = lacuna a preencher
const P = (nome, icone, itens) => ({ nome, icone, itens });
const PALETAS = [
  P("Relações", "\\le", ["\\le", "\\ge", "\\ne", "\\approx", "\\equiv", "\\sim", "\\cong", "\\propto", "\\ll", "\\gg", "<", ">"]),
  P("Espaços", "a\\,b", ["\\,", "\\:", "\\;", "\\quad", "\\qquad", "\\!"]),
  P("Acentos", "\\hat{a}", ["\\dot{#0}", "\\ddot{#0}", "\\hat{#0}", "\\bar{#0}", "\\vec{#0}", "\\tilde{#0}", "#0'", "#0''"]),
  P("Operações", "\\pm", ["\\pm", "\\mp", "\\times", "\\div", "\\cdot", "\\circ", "\\ast"]),
  P("Setas", "\\rightarrow", ["\\rightarrow", "\\leftarrow", "\\leftrightarrow", "\\Rightarrow", "\\Leftarrow",
    "\\Leftrightarrow", "\\uparrow", "\\downarrow", "\\rightleftharpoons", "\\rightleftarrows", "\\mapsto"]),
  P("Lógica", "\\therefore", ["\\therefore", "\\because", "\\forall", "\\exists", "\\neg", "\\wedge", "\\vee"]),
  P("Conjuntos", "\\in", ["\\in", "\\notin", "\\subset", "\\supset", "\\subseteq", "\\supseteq", "\\cup", "\\cap",
    "\\varnothing", "\\mathbb{N}", "\\mathbb{Z}", "\\mathbb{Q}", "\\mathbb{R}", "\\mathbb{C}"]),
  P("Diversos", "\\infty", ["\\infty", "\\partial", "\\nabla", "^{\\circ}", "\\prime", "\\ldots", "\\cdots", "\\angle",
    "\\perp", "\\parallel", "\\ell", "\\%"]),
  P("Grego", "\\alpha", ["\\alpha", "\\beta", "\\gamma", "\\delta", "\\varepsilon", "\\zeta", "\\eta", "\\theta",
    "\\iota", "\\kappa", "\\lambda", "\\mu", "\\nu", "\\xi", "\\pi", "\\rho", "\\sigma", "\\tau", "\\upsilon",
    "\\varphi", "\\chi", "\\psi", "\\omega"]),
  P("Grego maiúsculo", "\\Omega", ["\\Gamma", "\\Delta", "\\Theta", "\\Lambda", "\\Xi", "\\Pi", "\\Sigma",
    "\\Upsilon", "\\Phi", "\\Psi", "\\Omega"]),
  P("Texto e funções", "\\text{ab}", ["\\text{#0}", "\\mathrm{#0}", "\\operatorname{sen}#?", "\\cos #?",
    "\\operatorname{tg}#?", "\\log_{#?}#?", "\\ln #?", "\\lim_{#?}#?"]),

  P("Cercas", "\\left(\\square\\right)", ["\\left(#0\\right)", "\\left[#0\\right]", "\\left\\{#0\\right\\}",
    "\\left|#0\\right|", "\\left\\|#0\\right\\|", "\\left\\langle #0\\right\\rangle", "\\left\\lfloor #0\\right\\rfloor",
    "\\left\\lceil #0\\right\\rceil", "\\left\\{#0\\right.", "\\left.#0\\right\\}", "\\left[#0\\right)", "\\left(#0\\right]"]),
  P("Frações e raízes", "\\frac{\\square}{\\square}", ["\\frac{#0}{#?}", "\\tfrac{#0}{#?}", "{#0}/{#?}",
    "\\sqrt{#0}", "\\sqrt[#?]{#0}"]),
  P("Índices", "\\square^{\\square}", ["#0^{#?}", "#0_{#?}", "#0_{#?}^{#?}", "{}_{#?}^{#?}#0",
    "\\overset{#?}{#0}", "\\underset{#?}{#0}"]),
  P("Somatórios", "\\sum", ["\\sum #?", "\\sum_{#?}#?", "\\sum_{#?}^{#?}#?", "\\prod_{#?}^{#?}#?",
    "\\coprod_{#?}^{#?}#?", "\\bigcup_{#?}^{#?}#?", "\\bigcap_{#?}^{#?}#?"]),
  P("Integrais", "\\int", ["\\int #?", "\\int_{#?}^{#?}#?", "\\iint #?", "\\iiint #?", "\\oint #?", "\\oint_{#?}#?"]),
  P("Barras e setas sobre", "\\overline{\\square}", ["\\overline{#0}", "\\underline{#0}", "\\overrightarrow{#0}",
    "\\overleftarrow{#0}", "\\overleftrightarrow{#0}", "\\widehat{#0}", "\\widetilde{#0}"]),
  P("Setas com rótulo", "\\xrightarrow{\\square}", ["\\xrightarrow{#?}", "\\xleftarrow{#?}", "\\xrightarrow[#?]{#?}",
    "\\xrightleftharpoons{#?}", "\\xrightleftharpoons[#?]{#?}", "\\xleftrightarrow{#?}"]),
  P("Matrizes", "\\begin{pmatrix}\\square&\\square\\\\\\square&\\square\\end{pmatrix}", [
    "\\begin{pmatrix}#?&#?\\\\#?&#?\\end{pmatrix}", "\\begin{bmatrix}#?&#?\\\\#?&#?\\end{bmatrix}",
    "\\begin{vmatrix}#?&#?\\\\#?&#?\\end{vmatrix}", "\\begin{pmatrix}#?&#?&#?\\\\#?&#?&#?\\\\#?&#?&#?\\end{pmatrix}",
    "\\begin{cases}#?\\\\#?\\end{cases}", "\\begin{aligned}#?&=#?\\\\#?&=#?\\end{aligned}"]),
  P("Chaves", "\\underbrace{\\square}_{\\square}", ["\\underbrace{#0}_{#?}", "\\overbrace{#0}^{#?}"]),
  P("Caixas e riscos", "\\boxed{\\square}", ["\\boxed{#0}", "\\cancel{#0}", "\\bcancel{#0}", "\\xcancel{#0}"]),
  P("Química", "\\rightleftharpoons", ["\\rightleftharpoons", "\\xrightarrow{#?}", "\\xrightleftharpoons[#?]{#?}",
    "{}^{#?}_{#?}\\text{#0}", "\\text{#0}_{#?}", "\\text{#0}^{#?}"]),
];

// rodapé: mostra o nome do grupo da paleta sob o mouse e volta à mensagem anterior
let mensagem = null;
function dica(texto) {
  const e = document.getElementById("estado");
  if (texto) {
    if (mensagem === null) mensagem = [e.textContent, e.className];
    e.textContent = texto;
    e.className = "";
  } else if (mensagem) {
    [e.textContent, e.className] = mensagem;
    mensagem = null;
  }
}

const icone = (lx) => convertLatexToMarkup(lx.replace(/#0|#\?/g, "\\square"));
const grade = $("grade");
let aberto = null;

function fecharGrade() {
  grade.hidden = true;
  if (aberto) aberto.classList.remove("aberto");
  aberto = null;
}

for (const p of PALETAS) {
  const b = document.createElement("button");
  b.className = "grupo";
  b.title = p.nome;
  b.addEventListener("mouseenter", () => dica(p.nome));
  b.addEventListener("mouseleave", () => dica(null));
  b.innerHTML = icone(p.icone);
  b.addEventListener("click", (ev) => {
    ev.stopPropagation();
    if (aberto === b) return fecharGrade();
    fecharGrade();
    aberto = b;
    b.classList.add("aberto");
    grade.innerHTML = `<div class="titulo">${p.nome}</div>`;
    for (const it of p.itens) {
      const x = document.createElement("button");
      x.title = it;
      x.innerHTML = icone(it);
      x.addEventListener("click", () => {
        campo.executeCommand(["insert", it, { selectionMode: "placeholder", format: "latex" }]);
        campo.focus();
        fecharGrade();
      });
      grade.appendChild(x);
    }
    const r = b.getBoundingClientRect();
    grade.style.left = Math.min(r.left, window.innerWidth - 300) + "px";
    grade.style.top = r.bottom + 4 + "px";
    grade.hidden = false;
  });
  $("paletas").appendChild(b);
}
document.addEventListener("click", (ev) => { if (!grade.contains(ev.target)) fecharGrade(); });

// --- menus Estilo e Tamanho (ED-13): envolvem a seleção ----------------------------------------
for (const id of ["estilo", "tamanho"]) {
  $(id).addEventListener("change", (ev) => {
    const modelo = ev.target.value;
    if (modelo) campo.executeCommand(["insert", modelo, { selectionMode: "item", format: "latex" }]);
    ev.target.value = "";
    campo.focus();
  });
}

// --- LaTeX ⇄ área visual (ED-12) ----------------------------------------------------------------
campo.addEventListener("input", () => {
  latexTxt.value = campo.getValue("latex-without-placeholders");
  marcarAlterado();
});
latexTxt.addEventListener("input", () => {
  campo.setValue(latexTxt.value, { silenceNotifications: true });
  marcarAlterado();
});

// --- conversa com o núcleo do EqPress (Rust → python -m eqpress servidor) ----------------------
async function pedido(q) {
  if (!tauri) throw new Error("abra pelo app EqPress");
  // falha do núcleo vira {erro} (os chamadores já mostram r.erro); antes a tela ficava em "Salvando…"
  try {
    return await tauri.core.invoke("pedido", { q });
  } catch (e) {
    erroGeral(String(e));
    return { erro: String(e) };
  }
}

// erro de programa na tela aparece no rodapé (o colaborador manda o print) em vez de travar calado
function erroGeral(texto) {
  mostrarEstado(texto, "erro");
  // o rodapé só aparece na tela Equação: repete nas mensagens da tela aberta
  for (const el of document.querySelectorAll(".vista:not([hidden]) .resultado")) {
    el.textContent = texto;
    el.className = "resultado erro";
  }
}
window.addEventListener("error", (ev) => erroGeral(`Erro na tela: ${ev.message}`));
window.addEventListener("unhandledrejection", (ev) => erroGeral(`Erro na tela: ${ev.reason}`));

function mostrarEstado(texto, tipo = "") {
  $("estado").textContent = texto;
  $("estado").className = tipo;
}

function marcarSalvo(sim) {
  $("salvar").classList.toggle("pendente", !sim);
  document.title = (sim ? "" : "• ") + document.title.replace(/^• /, "");
}

const pt = (v) => v.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + " pt";

// --- prova: render real com o padrão do livro (ED-11), ao parar de digitar --------------------
// no máximo uma prova no núcleo por vez: o que mudar enquanto ela roda vira uma só prova depois.
// Sem isto (Windows, 1ª prova lenta) as provas enfileiravam e o Salvar esperava atrás de todas.
function umaPorVez(fn) {
  let rodando = false, denovo = false;
  return async function vez() {
    if (rodando) { denovo = true; return; }
    rodando = true;
    try { await fn(); } finally { rodando = false; }
    if (denovo) { denovo = false; vez(); }
  };
}

let espera = null;
function agendarPrevia() {
  clearTimeout(espera);
  espera = setTimeout(atualizarPreviaUma, 500);
}

function desenharProva(r) {
  const folha = $("folha");
  const m = r.metricas;
  // a imagem tem a altura da caixa da equação; a linha de base fica a "profundidade" do fundo
  const base = (1 - m.profundidade_pt / m.altura_pt) * 100;
  // escala da tela (px por pt): até 2,6; menor se a equação não couber na faixa
  const escala = Math.min(2.6, 94 / m.altura_pt, (folha.clientWidth - 90) / m.largura_pt);
  folha.className = "folha";
  folha.innerHTML = `
    <div class="eq">
      <img src="${r.png}" alt="Prova da equação" style="width:${(m.largura_pt * escala).toFixed(1)}px;height:${(m.altura_pt * escala).toFixed(1)}px">
      <div class="base" style="top:${base}%"><span>linha de base</span></div>
      ${m.profundidade_pt > 0.05 ? `<div class="cota" style="top:${base}%;bottom:0"><span>${pt(m.profundidade_pt)}</span></div>` : ""}
    </div>`;
  $("m-largura").textContent = pt(m.largura_pt);
  $("m-altura").textContent = pt(m.altura_pt);
  $("m-desce").textContent = pt(m.profundidade_pt);
  $("medidas").hidden = false;
}

const atualizarPreviaUma = umaPorVez(() => atualizarPrevia());
async function atualizarPrevia() {
  if (!estado.preset) return;
  const n = ++estado.pedido;
  $("folha").classList.add("atualizando");
  mostrarEstado("Atualizando a prova…");
  const r = await pedido({ cmd: "previa", latex: latexTxt.value, preset: estado.preset, ajustes: estado.ajustes });
  if (n !== estado.pedido) return;  // chegou outra edição depois desta
  if (r.erro) {
    const folha = $("folha");
    folha.className = "folha erro";
    folha.innerHTML = `<p>${r.erro.replace(/[<&]/g, (c) => ({ "<": "&lt;", "&": "&amp;" })[c])}</p>`;
    $("medidas").hidden = true;
    mostrarEstado("A equação não pode ser desenhada assim. Veja a mensagem na prova.", "erro");
    return;
  }
  desenharProva(r);
  mostrarEstado(estado.alterado ? "Alterações ainda não salvas" : "Prova atualizada");
}

// --- só nesta equação: fonte, corpo, itálico ----------------------------------------------------
function lerAjustes() {
  const a = {};
  const f = $("aj-familia").value.trim();
  const c = parseFloat($("aj-corpo").value);
  const i = $("aj-italico").value;
  if (f) a.familia = f;
  if (c) a.corpo = c;
  if (i) a.italico = i === "sim";
  return a;
}

function mostrarAjustes(a) {
  $("aj-familia").value = a.familia || "";
  $("aj-corpo").value = a.corpo || "";
  $("aj-italico").value = a.italico === undefined ? "" : (a.italico ? "sim" : "nao");
  const ativo = Object.keys(a).length > 0;
  $("aj-limpar").disabled = !ativo;
  $("ajuste").classList.toggle("ativo", ativo);
  $("aj-botao").classList.toggle("ativo", ativo);
  const l = estado.livro;
  if (l) {
    $("nota-padrao").textContent = ativo
      ? "Esta equação não segue o padrão do livro."
      : `Sem ajuste, vale o padrão do livro: ${l.familia}, ${l.corpo.toLocaleString("pt-BR")} pt, variáveis ${l.italico ? "em itálico" : "retas"}.`;
    $("aj-familia").placeholder = l.familia;
    $("aj-corpo").placeholder = l.corpo.toLocaleString("pt-BR");
  }
}

function mudouAjuste() {
  estado.ajustes = lerAjustes();
  mostrarAjustes(estado.ajustes);
  marcarAlterado();
}
for (const id of ["aj-familia", "aj-corpo", "aj-italico"]) $(id).addEventListener("change", mudouAjuste);
$("aj-limpar").addEventListener("click", () => {
  estado.ajustes = {};
  mostrarAjustes({});
  marcarAlterado();
});

async function carregarFamilias() {
  const r = await pedido({ cmd: "familias" });
  if (r.familias) $("familias").innerHTML = r.familias.map((f) => `<option value="${f.replace(/"/g, "&quot;")}">`).join("");
}

// --- abrir e salvar -------------------------------------------------------------------------------
async function abrir(caminho) {
  const r = await pedido({ cmd: "abrir", json: caminho });
  if (r.erro) return mostrarEstado(r.erro, "erro");
  Object.assign(estado, { json: caminho, preset: r.preset, original: r.latex, alterado: false,
                          ajustes: r.ajustes || {}, livro: r.padrao_livro });
  campo.setValue(r.latex, { silenceNotifications: true });
  latexTxt.value = r.latex;  // o LaTeX canônico fica intacto até haver edição (CA-E2)
  $("eq-id").textContent = r.id;
  // "pasta do livro › 0042": o caminho inteiro fica na dica
  const partes = caminho.split("/");
  $("arquivo").textContent = `${partes.at(-3) || ""} › ${partes.at(-1).replace(/\.json$/, "")}`;
  $("arquivo").title = caminho;
  $("tinta").textContent = r.cor || "";
  mostrarAjustes(estado.ajustes);
  document.title = `${r.id} — EqPress`;
  $("aba-equacao").disabled = false;
  $("aba-equacao").textContent = `Equação ${r.id}`;
  mostrarVista("equacao");
  marcarSalvo(true);
  campo.focus();
  atualizarPreviaUma();
}

function marcarAlterado() {
  estado.alterado = true;
  marcarSalvo(false);
  agendarPrevia();
}

// ED-04: o LaTeX salvo abre no KaTeX e no MathJax; o MathML derivado vem do MathJax
async function conferirPortavel(latex) {
  try {
    window.katex.renderToString(latex, { displayMode: true, throwOnError: true,
      strict: (codigo, msg) => { throw new Error(msg); } });
  } catch (e) {
    return { erro: `o LaTeX não abre no KaTeX: ${e.message}` };
  }
  try {
    await window.MathJax.startup.promise;
    const mml = await window.MathJax.tex2mmlPromise(latex, { display: true });
    if (mml.includes("<merror")) return { erro: "o LaTeX não abre no MathJax" };
    return { mathml: mml };
  } catch (e) {
    return { erro: `o LaTeX não abre no MathJax: ${e.message || e}` };
  }
}

async function salvar() {
  if (!estado.json) return mostrarEstado("Abra uma equação antes de salvar.", "erro");
  const conf = await conferirPortavel(latexTxt.value);
  if (conf.erro) return mostrarEstado(`Não foi salvo: ${conf.erro}`, "erro");
  mostrarEstado("Salvando e conferindo as chapas…");
  const r = await pedido({ cmd: "salvar", json: estado.json, latex: latexTxt.value, ajustes: estado.ajustes,
                           mathml: conf.mathml });
  if (r.erro) return mostrarEstado(`Não foi salvo: ${r.erro}`, "erro");
  estado.alterado = false;
  estado.original = latexTxt.value;
  marcarSalvo(true);
  mostrarEstado(r.sem_mudancas ? "Nada mudou. O PDF continua o mesmo." :
    "Salvo. No InDesign, rode “Vincular e alinhar equações” para atualizar.", "ok");
}

function painelAjuste(abrir) {
  const pn = $("ajuste");
  pn.hidden = !abrir;
  $("aj-botao").setAttribute("aria-expanded", String(abrir));
  if (abrir) {
    const r = $("aj-botao").getBoundingClientRect();
    pn.style.top = r.bottom + 6 + "px";
    pn.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 310)) + "px";
    $("aj-familia").focus();
  }
}
$("aj-botao").addEventListener("click", (ev) => {
  ev.stopPropagation();
  painelAjuste($("ajuste").hidden);
});
document.addEventListener("click", (ev) => {
  if (!$("ajuste").hidden && !$("ajuste").contains(ev.target)) painelAjuste(false);
});
$("latex-botao").addEventListener("click", () => {
  const abrir = $("latex-painel").hidden;
  $("latex-painel").hidden = !abrir;
  $("latex-botao").setAttribute("aria-expanded", String(abrir));
  if (abrir) latexTxt.focus();
});
document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") { fecharGrade(); painelAjuste(false); }
});

$("salvar").addEventListener("click", salvar);
$("abrir").addEventListener("click", async () => {
  const c = await tauri.core.invoke("escolher", { tipo: "equacao" });
  if (c) abrir(c);
});
document.addEventListener("keydown", (ev) => {
  if ((ev.metaKey || ev.ctrlKey) && ev.key === "s") { ev.preventDefault(); salvar(); }
  if ((ev.metaKey || ev.ctrlKey) && ev.key === "o") { ev.preventDefault(); $("abrir").click(); }
});

// aberto pelo InDesign (eqpress://editar?arquivo=…) ou pelo Finder
if (tauri) {
  tauri.event.listen("abrir", (ev) => abrir(ev.payload));
  tauri.core.invoke("pendente").then((c) => { if (c) abrir(c); });
  carregarFamilias();
  carregarPadroes();
}

// === navegação: Início, Padrões dos livros, Equação ==========================================
function mostrarVista(nome) {
  for (const v of ["inicio", "padroes", "equacao"]) $(`vista-${v}`).hidden = v !== nome;
  for (const a of document.querySelectorAll(".aba")) {
    if (a.dataset.vista === nome) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
  fecharGrade();
  painelAjuste(false);
}
for (const a of document.querySelectorAll(".aba")) a.addEventListener("click", () => mostrarVista(a.dataset.vista));
$("eq-abrir").addEventListener("click", () => $("abrir").click());
$("diag").addEventListener("click", async () => {
  resultado("eq-resultado", "Testando ferramentas, fontes e um render completo…");
  const r = await pedido({ cmd: "diagnostico" });
  const texto = JSON.stringify(r, null, 1);
  try { await navigator.clipboard.writeText(texto); } catch (e) { /* sem área de transferência: mostra */ }
  resultado("eq-resultado", r.tudo_ok
    ? "Tudo certo. O diagnóstico foi copiado; cole num e-mail se alguém pedir."
    : "Há um problema. O diagnóstico foi copiado: cole e envie para quem cuida do EqPress.", r.tudo_ok ? "ok" : "erro");
});
$("eq-scripts").addEventListener("click", async () => {
  const r = await pedido({ cmd: "instalar_scripts" });
  if (r.erro) return resultado("eq-resultado", r.erro, "erro");
  resultado("eq-resultado", `Scripts instalados no InDesign (${r.versoes.join(", ")}). Feche e abra o InDesign; eles aparecem em Janela › Utilitários › Scripts › Usuário.`, "ok");
});

function resultado(id, texto, tipo = "") {
  $(id).textContent = texto;
  $(id).className = "resultado " + tipo;
}

// === padrões: lista compartilhada pelas telas ================================================
let padroes = [];
let atual = null;  // padrão aberto na ficha (arquivo) ou null = novo

const resumoPadrao = (p) => p.erro ? p.erro :
  `${p.familia} ${Number(p.corpo).toLocaleString("pt-BR")} pt · ${p.cor === "especial" ? p.tinta : "Preto 100K"} · versão ${p.versao}`;

async function carregarPadroes(selecionar) {
  const r = await pedido({ cmd: "padroes" });
  padroes = (r.padroes || []).filter((p) => !p.erro).concat((r.padroes || []).filter((p) => p.erro));
  for (const sel of document.querySelectorAll(".lista-padroes")) {
    const antes = sel.value;
    sel.innerHTML = padroes.filter((p) => !p.erro)
      .map((p) => `<option value="${p.arquivo}">${p.nome} (versão ${p.versao})</option>`).join("");
    if (antes) sel.value = antes;
  }
  const ul = $("pd-lista");
  ul.innerHTML = "";
  for (const p of padroes) {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.innerHTML = `<span class="nome-pd"></span><span class="${p.erro ? "erro-pd" : "resumo-pd"}"></span>`;
    b.firstChild.textContent = p.nome;
    b.lastChild.textContent = resumoPadrao(p);
    b.disabled = !!p.erro;
    b.addEventListener("click", () => abrirPadrao(p));
    li.appendChild(b);
    ul.appendChild(li);
  }
  const alvo = padroes.find((p) => p.arquivo === selecionar) || (atual && padroes.find((p) => p.arquivo === atual.arquivo)) || padroes[0];
  if (alvo && !alvo.erro) abrirPadrao(alvo);
  atualizarBotoes();
}

// === Início › Preparar um Word ================================================================
let docxEscolhido = null;
let preparado = null;
function atualizarBotoes() {
  $("pr-ir").disabled = !docxEscolhido || !$("pr-padrao").value;
  $("tr-ir").disabled = !pastaEscolhida || !$("tr-padrao").value;
}
$("pr-escolher").addEventListener("click", async () => {
  const c = await tauri.core.invoke("escolher", { tipo: "docx" });
  if (!c) return;
  docxEscolhido = c;
  $("pr-docx").textContent = c.split("/").pop();
  $("pr-docx").title = c;
  $("pr-depois").hidden = true;
  resultado("pr-resultado", "");
  atualizarBotoes();
});
$("pr-ir").addEventListener("click", async () => {
  $("pr-ir").disabled = true;
  $("pr-depois").hidden = true;
  resultado("pr-resultado", "Preparando… um capítulo leva de 15 segundos a 1 minuto.");
  const r = await pedido({ cmd: "preparar", docx: docxEscolhido, padrao: $("pr-padrao").value });
  atualizarBotoes();
  if (r.erro) return resultado("pr-resultado", `Não foi preparado: ${r.erro}`, "erro");
  preparado = r;
  const problemas = r.com_erro.length;
  resultado("pr-resultado", problemas
    ? `${r.pdfs} de ${r.equacoes} equações prontas; ${problemas} com problema (veja a conferência).`
    : `${r.pdfs} de ${r.equacoes} equações prontas.`, problemas ? "erro" : "ok");
  $("pr-depois").hidden = false;
});
$("pr-conferir").addEventListener("click", () => preparado && pedido({ cmd: "mostrar", caminho: preparado.conferir }));
$("pr-finder").addEventListener("click", () => preparado && pedido({ cmd: "mostrar", caminho: preparado.word, finder: true }));

// === Início › Trocar o padrão de um livro =====================================================
let pastaEscolhida = null;
$("tr-escolher").addEventListener("click", async () => {
  const c = await tauri.core.invoke("escolher", { tipo: "pasta" });
  if (!c) return;
  pastaEscolhida = c;
  $("tr-pasta").textContent = c.split("/").filter(Boolean).pop();
  $("tr-pasta").title = c;
  resultado("tr-resultado", "");
  atualizarBotoes();
});
for (const id of ["pr-padrao", "tr-padrao"]) $(id).addEventListener("change", atualizarBotoes);
$("tr-ir").addEventListener("click", async () => {
  $("tr-ir").disabled = true;
  resultado("tr-resultado", "Refazendo as equações…");
  const r = await pedido({ cmd: "trocar", pasta: pastaEscolhida, padrao: $("tr-padrao").value });
  atualizarBotoes();
  if (r.erro) return resultado("tr-resultado", r.erro, "erro");
  let msg = `${r.refeitas} de ${r.equacoes} equações refeitas. No InDesign, rode “Vincular e alinhar equações”.`;
  if (r.com_erro.length) msg += ` Com problema (ficou o PDF anterior): ${r.com_erro.map((e) => e.id).join(", ")}.`;
  resultado("tr-resultado", msg, r.com_erro.length ? "erro" : "ok");
});

// === Padrões dos livros: ficha com prova ao vivo ==============================================
function preencherFicha(c) {
  $("pd-nome").value = c.nome || "";
  $("pd-familia").value = c.familia || "Calibri";
  $("pd-corpo").value = c.corpo || 10;
  $("pd-italico").value = c.italico ? "sim" : "nao";
  $("pd-simbolos").value = c.simbolos || "Symbol";
  document.querySelector(`input[name="pd-cor"][value="${c.cor || "preto"}"]`).checked = true;
  $("pd-tinta").value = c.tinta || "";
  const alt = c.alternativa || [0, 100, 0, 0];
  ["pd-c", "pd-m", "pd-y", "pd-k"].forEach((id, k) => { $(id).value = alt[k]; });
  $("pd-sobre").checked = c.sobreimpressao !== false;
  $("pd-eps").checked = (c.extras || []).includes("eps");
  $("pd-emf").checked = (c.extras || []).includes("emf");
  $("pd-especial").hidden = (c.cor || "preto") !== "especial";
}

function lerFicha() {
  return {
    nome: $("pd-nome").value, familia: $("pd-familia").value.trim(), corpo: parseFloat($("pd-corpo").value) || 10,
    italico: $("pd-italico").value === "sim", simbolos: $("pd-simbolos").value.trim() || "Symbol",
    cor: document.querySelector('input[name="pd-cor"]:checked').value, tinta: $("pd-tinta").value,
    alternativa: ["pd-c", "pd-m", "pd-y", "pd-k"].map((id) => parseFloat($(id).value) || 0),
    sobreimpressao: $("pd-sobre").checked,
    extras: [$("pd-eps").checked && "eps", $("pd-emf").checked && "emf"].filter(Boolean),
  };
}

function abrirPadrao(p) {
  atual = p;
  for (const b of document.querySelectorAll("#pd-lista button")) {
    b.setAttribute("aria-current", String(b.firstChild.textContent === p.nome && b.lastChild.textContent === resumoPadrao(p)));
  }
  preencherFicha(p);
  $("pd-exportar").disabled = false;
  resultado("pd-resultado", "");
  provaPadraoUma();
}

$("pd-novo").addEventListener("click", () => {
  atual = null;
  for (const b of document.querySelectorAll("#pd-lista button")) b.setAttribute("aria-current", "false");
  preencherFicha({ nome: "", familia: "Calibri", corpo: 10, simbolos: "Symbol", cor: "preto", extras: [] });
  $("pd-exportar").disabled = true;
  resultado("pd-resultado", "Padrão novo: dê um nome e ajuste a fonte e a cor.");
  $("pd-nome").focus();
  provaPadraoUma();
});

let esperaPadrao = null;
$("pd-ficha").addEventListener("input", () => {
  $("pd-especial").hidden = document.querySelector('input[name="pd-cor"]:checked').value !== "especial";
  clearTimeout(esperaPadrao);
  esperaPadrao = setTimeout(provaPadraoUma, 600);
});

let pedidoPadrao = 0;
const provaPadraoUma = umaPorVez(() => provaPadrao());
async function provaPadrao() {
  const n = ++pedidoPadrao;
  const folha = $("pd-prova");
  folha.classList.add("atualizando");
  const r = await pedido({ cmd: "padrao_prova", campos: lerFicha(), base: atual && atual.arquivo });
  if (n !== pedidoPadrao) return;
  folha.classList.remove("atualizando");
  if (r.erro) {
    folha.className = "folha amostra erro";
    folha.innerHTML = `<p></p>`;
    folha.firstChild.textContent = r.erro;
    return;
  }
  folha.className = "folha amostra";
  const m = r.metricas;
  const escala = Math.min(2.4, 96 / m.altura_pt, (folha.clientWidth - 40) / m.largura_pt);
  folha.innerHTML = `<div class="eq"><img src="${r.png}" alt="Prova do padrão" style="width:${(m.largura_pt * escala).toFixed(1)}px;height:${(m.altura_pt * escala).toFixed(1)}px"></div>`;
}

$("pd-ficha").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  resultado("pd-resultado", "Salvando…");
  const r = await pedido({ cmd: "padrao_salvar", campos: lerFicha(), base: atual && atual.arquivo });
  if (r.erro) return resultado("pd-resultado", r.erro, "erro");
  atual = r;
  await carregarPadroes(r.arquivo);
  resultado("pd-resultado", `Salvo como versão ${r.versao}. As versões anteriores continuam na lista.`, "ok");
});

$("pd-importar").addEventListener("click", async () => {
  const c = await tauri.core.invoke("escolher", { tipo: "padrao" });
  if (!c) return;
  const r = await pedido({ cmd: "padrao_importar", origem: c });
  if (r.erro) return resultado("pd-resultado", r.erro, "erro");
  await carregarPadroes(r.arquivo);
  resultado("pd-resultado", `Importado: ${r.nome}.`, "ok");
});

$("pd-exportar").addEventListener("click", async () => {
  if (!atual) return;
  const nome = atual.arquivo.split("/").pop();
  const destino = await tauri.core.invoke("escolher", { tipo: "salvar_padrao", sugestao: nome });
  if (!destino) return;
  const r = await pedido({ cmd: "padrao_exportar", arquivo: atual.arquivo, destino });
  resultado("pd-resultado", r.erro || `Exportado. Envie o arquivo ${nome} ao colaborador; ele usa “Importar…”.`, r.erro ? "erro" : "ok");
});
