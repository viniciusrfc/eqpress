// Teste automático do "Vincular e alinhar" (chamado por tests/indesign_teste.py, não é para o usuário).
// Entrada: $.global.EQPRESS_TESTE = {docx, pasta, script, saida_pdf, saida_json}
#target indesign
(function () {
    var T = $.global.EQPRESS_TESTE;
    app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
    var doc = app.documents.add();
    try {
        doc.documentPreferences.facingPages = false;
        doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.POINTS;
        doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.POINTS;
        var pg = doc.pages[0];
        var b = pg.bounds, m = pg.marginPreferences;
        var caixa = [b[0] + m.top, b[1] + m.left, b[2] - m.bottom, b[3] - m.right];
        var tf = pg.textFrames.add({ geometricBounds: caixa });
        tf.place(File(T.docx));
        var n = 0;
        while (tf.overflows && n++ < 200) {  // flui o texto por páginas novas
            var nova = doc.pages.add();
            var t2 = nova.textFrames.add({ geometricBounds: caixa });
            tf.nextTextFrame = t2;
            tf = t2;
        }
        var antes = doc.allGraphics.length;
        $.evalFile(File(T.script));
        // medição independente do script: fundo do quadro − baseline da linha vs. profundidade do JSON
        var medidas = [], tipos = {};
        var gs = doc.allGraphics;
        for (var i = 0; i < gs.length; i++) {
            var fr = gs[i].parent, id = "";
            try { id = fr.objectExportOptions.customAltText; } catch (e) {}
            var tipo = gs[i].constructor.name;
            tipos[tipo] = (tipos[tipo] || 0) + 1;
            if (!/^EQ-\d{4}$/.test(id)) continue;
            var f = File(T.pasta + "/" + id.substr(3) + ".json");
            f.encoding = "UTF-8"; f.open("r"); var s = f.read(); f.close();
            var prof = parseFloat(s.match(/"profundidade_pt"\s*:\s*(-?[0-9.]+)/)[1]);
            var gb = fr.geometricBounds;
            var base = null, cs = fr.parent.lines[0].characters;  // baseline num caractere de texto comum
            for (var c = 0; c < cs.length && base === null; c++) {
                var t = String(cs[c].contents);
                if (t.length === 1 && !/[\s\uFFFC\u0003\u000D\u2029]/.test(t) && cs[c].baselineShift === 0) base = cs[c].baseline;
            }
            var linha = String(fr.parent.lines[0].contents).replace(/[\s\uFFFC\u0003\u000D\u2029]/g, "");
            var ln = fr.parent.lines[0];
            var info = '"shift":' + fr.parent.baselineShift.toFixed(3) + ',"primeira_do_quadro":' +
                       (ln.index === ln.parentTextFrames[0].lines[0].index) + ',"linha":' +
                       '"' + String(ln.contents).replace(/[^A-Za-z0-9 ,.:=+-]/g, "#").substr(0, 60) + '",';
            medidas.push('{' + info + '"id":"' + id + '","sozinha":' + (base === null) + ',"tipo":"' + tipo + '","desvio":' +
                         (base === null ? 0 : (gb[2] - base) - prof).toFixed(4) +
                         ',"largura":' + (gb[3] - gb[1]).toFixed(3) + ',"altura":' + (gb[2] - gb[0]).toFixed(3) + "}");
        }
        // para conferir as chapas só das equações, as fotos do documento saem antes de exportar
        var todos = doc.allGraphics;
        for (var j = todos.length - 1; j >= 0; j--) {
            var alt = "";
            try { alt = todos[j].parent.objectExportOptions.customAltText; } catch (e) {}
            if (!/^EQ-\d{4}$/.test(alt)) todos[j].parent.remove();
        }
        var preset = app.pdfExportPresets.itemByName("[PDF/X-1a:2001]");
        doc.exportFile(ExportFormat.PDF_TYPE, File(T.saida_pdf), false, preset.isValid ? preset : undefined);
        var tiposTxt = [];
        for (var k in tipos) tiposTxt.push('"' + k + '":' + tipos[k]);
        var r = T.resultado || {};
        var out = File(T.saida_json);
        out.encoding = "UTF-8"; out.open("w");
        out.write('{"graficos_antes":' + antes + ',"tipos":{' + tiposTxt.join(",") + '},"vinculadas":' +
                  (r.vinculadas || 0) + ',"atualizadas":' + (r.atualizadas || 0) + ',"erros":' +
                  (r.erros ? r.erros.length : -1) + ',"faltando":' + (r.faltando ? r.faltando.length : -1) +
                  ',"medidas":[' + medidas.join(",") + "]}");
        out.close();
    } finally {
        doc.close(SaveOptions.NO);
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.INTERACT_WITH_ALL;
    }
})();
