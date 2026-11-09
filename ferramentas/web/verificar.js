// CA-17 / ED-04: lê um array JSON de LaTeX no stdin e devolve, para cada um,
// {katex, mathjax, mathml}: katex/mathjax = null se renderizou, ou a mensagem de erro;
// mathml = MathML do MathJax (usado pelo editor para o MathML derivado, EDITOR ED-01).
// KaTeX: modo display, throwOnError; avisos de "strict" também contam como erro.
// MathJax 3: todos os pacotes que o autoload da web carregaria, sem noerrors/noundefined.
const katex = require('katex');
const { mathjax } = require('mathjax-full/js/mathjax.js');
const { TeX } = require('mathjax-full/js/input/tex.js');
const { AllPackages } = require('mathjax-full/js/input/tex/AllPackages.js');
const { liteAdaptor } = require('mathjax-full/js/adaptors/liteAdaptor.js');
const { RegisterHTMLHandler } = require('mathjax-full/js/handlers/html.js');
const { STATE } = require('mathjax-full/js/core/MathItem.js');
const { SerializedMmlVisitor } = require('mathjax-full/js/core/MmlTree/SerializedMmlVisitor.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({
  packages: AllPackages.filter((p) => !['noerrors', 'noundefined', 'bussproofs'].includes(p)),
  formatError: (_jax, err) => { throw err; },
});
const doc = mathjax.document('', { InputJax: tex });
const mml = new SerializedMmlVisitor();

function viaKatex(s) {
  try {
    katex.renderToString(s, {
      displayMode: true,
      throwOnError: true,
      strict: (code, msg) => { throw new Error(`strict ${code}: ${msg}`); },
    });
    return null;
  } catch (e) { return String(e.message || e); }
}

function viaMathjax(s) {
  try {
    const xml = mml.visitTree(doc.convert(s, { display: true, end: STATE.CONVERT }));
    return xml.includes('<merror') ? [xml, null] : [null, xml];
  } catch (e) { return [String(e.message || e), null]; }
}

let entrada = '';
process.stdin.on('data', (d) => { entrada += d; });
process.stdin.on('end', () => {
  const res = JSON.parse(entrada).map((s) => {
    const [mathjax, mathml] = viaMathjax(s);
    return { katex: viaKatex(s), mathjax, mathml };
  });
  process.stdout.write(JSON.stringify(res));
});
