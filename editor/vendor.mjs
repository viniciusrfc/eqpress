// Copia as bibliotecas da interface para ui/vendor (igual no macOS e no Windows: o `cp` do
// script antigo não existe no cmd do Windows e a montagem seguia sem elas → botões mortos).
import { cpSync, rmSync, existsSync } from "node:fs";

const N = "node_modules/";
const copias = {
  "mathlive/": ["mathlive/mathlive.min.mjs", "mathlive/mathlive-static.css", "mathlive/fonts", "mathlive/LICENSE.txt"],
  "lato/": ["@fontsource/lato/400.css", "@fontsource/lato/700.css", "@fontsource/lato/LICENSE", "@fontsource/lato/files"],
  "katex/": ["katex/dist/katex.min.js", "katex/LICENSE"],
  "mathjax/": ["mathjax/es5/tex-mml-chtml.js", "mathjax/LICENSE"],
  "mathjax/input/tex/": ["mathjax/es5/input/tex/extensions"],
};

rmSync("ui/vendor", { recursive: true, force: true });
for (const [destino, origens] of Object.entries(copias)) {
  for (const o of origens) {
    cpSync(N + o, `ui/vendor/${destino}${o.split("/").pop()}`, { recursive: true });
  }
}
for (const f of ["mathlive/mathlive.min.mjs", "katex/katex.min.js", "mathjax/tex-mml-chtml.js", "lato/400.css"]) {
  if (!existsSync(`ui/vendor/${f}`)) throw new Error(`faltou ui/vendor/${f}`);
}
console.log("ui/vendor pronto");
