// EqPress — Vincular e alinhar equações (InDesign 2024+, ExtendScript).
// Para cada imagem cujo texto alternativo é EQ-NNNN (vinda do _EqPress.docx):
//   1. troca a imagem pelo PDF equacoes/NNNN.pdf (cor 100K / tinta do padrão) — INDESIGN VIN-00/01
//   2. tamanho 100 %, quadro justo ao PDF, estilo de objeto "Equação" — VIN-02/03
//   3. baseline: fundo do quadro − baseline da linha = profundidade_pt do NNNN.json, medido e
//      corrigido no próprio InDesign até < 0,01 pt — BL-02 (aceite CA-04: ≤ 0,1 pt)
// Rodar de novo = "Atualizar todas": atualiza PDFs alterados e realinha (INDESIGN §6).
#target indesign

(function () {
    if (app.documents.length === 0) {
        alert("Abra o documento do InDesign antes de rodar o EqPress.");
        return;
    }
    var doc = app.activeDocument;
    var pasta = escolherPasta(doc);
    if (!pasta) return;

    var vp = doc.viewPreferences;
    var unidades = [vp.horizontalMeasurementUnits, vp.verticalMeasurementUnits];
    var corte = app.pdfPlacePreferences.pdfCrop;
    var fundo = app.pdfPlacePreferences.transparentBackground;
    var res = { vinculadas: 0, atualizadas: 0, sozinhas: 0, detalhes: [], faltando: [], erros: [], duplicadas: [], desvioMax: 0, piores: [] };
    try {
        vp.horizontalMeasurementUnits = MeasurementUnits.POINTS;
        vp.verticalMeasurementUnits = MeasurementUnits.POINTS;
        app.pdfPlacePreferences.pdfCrop = PDFCrop.CROP_MEDIA;
        app.pdfPlacePreferences.transparentBackground = true;
        app.doScript(function () { processar(doc, pasta, res); }, ScriptLanguage.JAVASCRIPT,
                     undefined, UndoModes.ENTIRE_SCRIPT, "EqPress: vincular e alinhar equações");
    } finally {
        vp.horizontalMeasurementUnits = unidades[0];
        vp.verticalMeasurementUnits = unidades[1];
        app.pdfPlacePreferences.pdfCrop = corte;
        app.pdfPlacePreferences.transparentBackground = fundo;
    }
    relatorio(pasta, res);
})();

function escolherPasta(doc) {
    if ($.global.EQPRESS_TESTE) return Folder($.global.EQPRESS_TESTE.pasta);  // teste automático, sem janelas
    var salva = doc.extractLabel("eqpress_pasta");
    if (salva && Folder(salva).exists &&
        confirm("Usar as equações de:\n" + Folder(salva).fsName + " ?\n\n(Não = escolher outra pasta)")) {
        return Folder(salva);
    }
    var f = Folder.selectDialog("Escolha a pasta _EqPress (ou a pasta equacoes dentro dela)");
    if (!f) return null;
    if (Folder(f + "/equacoes").exists) f = Folder(f + "/equacoes");
    doc.insertLabel("eqpress_pasta", f.fullName);
    return f;
}

function lerNumero(texto, chave) {
    var m = texto.match(new RegExp('"' + chave + '"\\s*:\\s*(-?[0-9.]+)'));
    return m ? parseFloat(m[1]) : null;
}

function lerMetricas(arquivo) {
    arquivo.encoding = "UTF-8";
    arquivo.open("r");
    var s = arquivo.read();
    arquivo.close();
    return { largura: lerNumero(s, "largura_pt"), altura: lerNumero(s, "altura_pt"),
             prof: lerNumero(s, "profundidade_pt") };
}

function estiloEquacao(doc) {
    var st = doc.objectStyles.itemByName("Equação");
    if (st.isValid) return st;
    st = doc.objectStyles.add({ name: "Equação" });
    try {
        st.fillColor = doc.swatches.itemByName("None");
        st.strokeColor = doc.swatches.itemByName("None");
        st.strokeWeight = 0;
        st.textWrapPreferences.textWrapMode = TextWrapModes.NONE;
    } catch (e) {}
    return st;
}

function idDoQuadro(fr) {
    try {
        var t = fr.objectExportOptions.customAltText;
        return /^EQ-\d{4}$/.test(t) ? t : null;
    } catch (e) {
        return null;
    }
}

// baseline da linha medida num caractere de texto comum (sem deslocamento): o "baseline" da linha
// segue o primeiro caractere, e quando ele é a própria equação a medida andaria junto com ela.
// null = a linha não tem texto (equação sozinha)
function baselineDaLinha(ch) {
    var cs = ch.lines[0].characters;
    for (var i = 0; i < cs.length; i++) {
        var c = cs[i];
        var t = String(c.contents);
        if (t.length === 1 && !/[\s\uFFFC\u0003\u000D\u2029]/.test(t) && c.baselineShift === 0) return c.baseline;
    }
    return null;
}

// devolve o desvio final (pt), ou null quando a equação está sozinha na linha
function alinhar(fr, prof) {
    var ch = fr.parent;  // caractere-âncora do gráfico na linha
    var ao = fr.anchoredObjectSettings;
    ao.anchoredPosition = AnchorPosition.INLINE_POSITION;
    ao.anchorYoffset = 0;
    ch.baselineShift = 0;
    var base = baselineDaLinha(ch);
    if (base === null) {
        // o deslocamento moveria a linha inteira junto; com 0 o fundo apoia na baseline e a
        // entrelinha automática abre espaço para a equação (nada invade a linha de baixo)
        return null;
    }
    ch.baselineShift = -prof;
    var d = 0;
    for (var k = 0; k < 4; k++) {  // o InDesign arredonda internamente; mede e corrige
        base = baselineDaLinha(ch);
        d = (fr.geometricBounds[2] - base) - prof;
        if (Math.abs(d) < 0.01) break;
        ch.baselineShift = ch.baselineShift + d;
    }
    return (fr.geometricBounds[2] - baselineDaLinha(ch)) - prof;
}

function processar(doc, pasta, res) {
    var estilo = estiloEquacao(doc);
    var vistos = {};
    var graficos = doc.allGraphics;
    for (var i = 0; i < graficos.length; i++) {
        var g = graficos[i];
        var fr = g.parent;
        var id = idDoQuadro(fr);
        if (!id) continue;
        if (vistos[id]) res.duplicadas.push(id);
        vistos[id] = true;
        var n = id.substr(3);
        var pdf = File(pasta + "/" + n + ".pdf");
        var json = File(pasta + "/" + n + ".json");
        if (!pdf.exists || !json.exists) {
            res.faltando.push(id);
            continue;
        }
        try {
            var m = lerMetricas(json);
            var link = g.itemLink;
            var acao;
            if (link && link.isValid && File(link.filePath).fsName == pdf.fsName) {
                acao = link.status != LinkStatus.NORMAL ? "PDF atualizado" : "já vinculada, conferida";
                if (link.status != LinkStatus.NORMAL) link.update();
                res.atualizadas++;
            } else {
                fr.place(pdf);
                acao = "imagem do Word trocada pelo PDF";
                res.vinculadas++;
            }
            fr.applyObjectStyle(estilo, false, false);
            g = fr.graphics[0];
            g.absoluteHorizontalScale = 100;
            g.absoluteVerticalScale = 100;
            fr.fit(FitOptions.FRAME_TO_CONTENT);
            fr.objectExportOptions.altTextSourceType = SourceType.SOURCE_CUSTOM;
            fr.objectExportOptions.customAltText = id;  // o place pode limpar o texto alternativo
            var b = fr.geometricBounds;
            if (Math.abs((b[3] - b[1]) - m.largura) > 0.05 || Math.abs((b[2] - b[0]) - m.altura) > 0.05) {
                res.erros.push(id + ": quadro " + (b[3] - b[1]).toFixed(2) + "×" + (b[2] - b[0]).toFixed(2) +
                               " pt ≠ PDF " + m.largura + "×" + m.altura + " pt");
            }
            var desvio = alinhar(fr, m.prof);
            var pagina = "";
            try { pagina = "p. " + fr.parent.parentTextFrames[0].parentPage.name + " · "; } catch (e) {}
            res.detalhes.push(id + " — " + pagina + acao + " · " + (desvio === null
                ? "sozinha na linha (sem deslocamento)"
                : "deslocamento " + fr.parent.baselineShift.toFixed(2) + " pt, desvio " + Math.abs(desvio).toFixed(3) + " pt"));
            if (desvio === null) {
                res.sozinhas++;
                continue;
            }
            desvio = Math.abs(desvio);
            if (desvio > res.desvioMax) res.desvioMax = desvio;
            if (desvio > 0.1) res.piores.push(id + " (" + desvio.toFixed(3) + " pt)");
        } catch (e) {
            res.erros.push(id + ": " + e.message);
        }
    }
}

function relatorio(pasta, res) {
    var total = res.vinculadas + res.atualizadas;
    var linhas = [
        "EqPress — vincular e alinhar equações",
        "Pasta: " + pasta.fsName,
        "",
        "Equações prontas: " + total + " (" + res.vinculadas + " trocadas pelo PDF, " +
            res.atualizadas + " já vinculadas e conferidas)",
        "Maior desvio de baseline no meio do texto: " + res.desvioMax.toFixed(3) + " pt (limite 0,1 pt)",
        "Sozinhas na linha (apoiadas na própria baseline): " + res.sozinhas
    ];
    if (res.piores.length) linhas.push("Acima do limite: " + res.piores.join(", "));
    if (res.faltando.length) linhas.push("Sem PDF na pasta: " + res.faltando.join(", "));
    if (res.duplicadas.length) linhas.push("ID repetido no documento: " + res.duplicadas.join(", "));
    if (res.erros.length) linhas.push("Erros:\n  " + res.erros.join("\n  "));
    if (total === 0 && !res.faltando.length) {
        linhas.push("", "Nenhuma imagem com texto alternativo EQ-NNNN foi encontrada.",
                    "O texto foi inserido a partir do arquivo _EqPress.docx?");
    }
    linhas.push("", "Por equação:");
    linhas = linhas.concat(res.detalhes);
    var texto = linhas.join("\n");
    var log = File(pasta.parent + "/vinculo_indesign.txt");
    log.encoding = "UTF-8";
    log.lineFeed = "Unix";  // no Mac o padrão é "\r" e o arquivo abriria numa linha só
    log.open("w");
    log.write(texto);
    log.close();
    if ($.global.EQPRESS_TESTE) $.global.EQPRESS_TESTE.resultado = res;
    else mostrar(texto, log);
}

// janela com texto rolável (o alert do InDesign não rola quando o resumo é longo)
function mostrar(texto, log) {
    var w = new Window("dialog", "EqPress — resumo");
    w.alignChildren = "fill";
    var campo = w.add("edittext", undefined, texto, { multiline: true, scrolling: true, readonly: true });
    campo.preferredSize = [640, 420];
    var botoes = w.add("group");
    botoes.alignment = "right";
    var abrir = botoes.add("button", undefined, "Abrir arquivo do relatório");
    botoes.add("button", undefined, "OK", { name: "ok" });
    abrir.onClick = function () { log.execute(); };
    w.show();
}
