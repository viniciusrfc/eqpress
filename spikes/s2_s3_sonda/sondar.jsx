// SPIKE S2/S3 (descartável) — sonda no InDesign, depois de Arquivo > Inserir dos .docx de teste.
// Uso: Janela > Utilitários > Scripts > clique duplo (copie para a pasta de scripts do usuário).
// Grava ~/Desktop/eqpress_sonda.tsv com, para cada gráfico: tipo, nome do link, status, rótulo,
// nome do quadro, texto alternativo e medidas de baseline.
#target indesign
(function () {
    var doc = app.activeDocument;
    var oldUnits = doc.viewPreferences.verticalMeasurementUnits;
    doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.POINTS;
    doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.POINTS;
    var out = ['n\ttipo\tformato\tincorporado\tlink_nome\tlink_status\tlink_caminho\tlabel_grafico\tlabel_quadro\tnome_quadro\talt_texto\tinline\tbaseline_y\tquadro_topo\tquadro_base\tdesce_abaixo_baseline_pt\tdesloc_baseline_char\tlargura_pt\taltura_pt'];
    var gs = doc.allGraphics;
    for (var i = 0; i < gs.length; i++) {
        var g = gs[i], f = g.parent, link = g.itemLink, row = [i + 1, g.constructor.name];
        var fmt = ''; try { fmt = g.imageTypeName; } catch (e) {}
        row.push(fmt, link ? String(link.status === LinkStatus.LINK_EMBEDDED) : '');
        row.push(link ? link.name : '', link ? String(link.status) : '', link ? link.filePath : '');
        row.push(g.label, f.label, f.name);
        var alt = '';
        try { alt = f.objectExportOptions.customAltText + ' | src=' + f.objectExportOptions.altTextSourceType; } catch (e) {}
        row.push(alt);
        var ch = f.parent, isInline = ch && ch.constructor.name === 'Character';
        row.push(isInline);
        var vb = f.visibleBounds; // [topo, esq, base, dir]
        if (isInline) {
            row.push(ch.baseline, vb[0], vb[2], (vb[2] - ch.baseline).toFixed(3), ch.baselineShift);
        } else {
            row.push('', vb[0], vb[2], '', '');
        }
        row.push((vb[3] - vb[1]).toFixed(3), (vb[2] - vb[0]).toFixed(3));
        out.push(row.join('\t'));
    }
    doc.viewPreferences.verticalMeasurementUnits = oldUnits;
    var file = new File(Folder.desktop + '/eqpress_sonda.tsv');
    file.encoding = 'UTF-8'; file.open('w'); file.write(out.join('\n')); file.close();
    alert('EqPress sonda: ' + gs.length + ' gráficos.\nResultado em ' + file.fsName);
})();
