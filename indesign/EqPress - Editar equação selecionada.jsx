// EqPress — Editar equação selecionada (INDESIGN §5, EDITOR ED-20).
// Selecione a equação (o quadro ou a imagem) e rode: o editor EqPress abre nela. Depois de salvar
// no editor, rode "EqPress - Vincular e alinhar equações" para atualizar o PDF e a baseline.
#target indesign

(function () {
    if (app.documents.length === 0 || app.selection.length !== 1) {
        alert("Selecione uma equação (clique nela) e rode de novo.");
        return;
    }
    var item = app.selection[0];
    // aceita o quadro, a imagem dentro dele ou o caractere-âncora no texto
    if (item.hasOwnProperty("allGraphics") && item.allGraphics.length) item = item.allGraphics[0];
    var link = null;
    try { link = item.itemLink; } catch (e) {}
    if (!link || !link.isValid) {
        alert("A seleção não é uma equação vinculada do EqPress.\n" +
              "Rode antes \"EqPress - Vincular e alinhar equações\".");
        return;
    }
    var pdf = File(link.filePath);
    var json = File(pdf.fsName.replace(/\.pdf$/i, ".json"));
    if (!/\.pdf$/i.test(pdf.name) || !json.exists) {
        alert("Esta imagem não é uma equação do EqPress (não achei " + json.fsName + ").");
        return;
    }
    var url = "eqpress://editar?arquivo=" + encodeURIComponent(json.fsName);
    if ($.os.indexOf("Windows") >= 0) {
        // Windows: o shell entrega o link ao EqPress (o esquema eqpress:// é registrado pelo app)
        app.doScript('CreateObject("WScript.Shell").Run "' + url + '"', ScriptLanguage.VISUAL_BASIC);
    } else {
        // Mac: "open location" dentro do InDesign é tratado pelo próprio InDesign (que ignora o
        // link); o comando open do macOS entrega o link ao EqPress
        app.doScript('do shell script "open " & quoted form of "' + url + '"', ScriptLanguage.APPLESCRIPT_LANGUAGE);
    }
})();
