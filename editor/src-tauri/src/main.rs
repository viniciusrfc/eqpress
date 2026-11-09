// EqPress — app do editor (EDITOR §4). A interface (ui/) conversa com o núcleo em Python
// (`python -m eqpress servidor`, mesmo motor do lote: ED-21) por uma linha JSON por pedido.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;

use serde_json::Value;
use tauri::{Emitter, Manager};
use tauri_plugin_deep_link::DeepLinkExt;
use tauri_plugin_dialog::DialogExt;

// raiz do repositório: só para desenvolvimento, quando o núcleo empacotado não está ao lado do app
const RAIZ: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");

struct Nucleo {
    _processo: Child,
    entrada: ChildStdin,
    saida: BufReader<ChildStdout>,
}

#[derive(Default)]
struct Estado {
    nucleo: Mutex<Option<Nucleo>>,
    pendente: Mutex<Option<String>>, // arquivo pedido antes de a janela estar pronta
}

/// Núcleo empacotado (eqpress-nucleo, ao lado do executável do app) com as ferramentas que vêm
/// no instalador; sem ele (desenvolvimento), o Python do repositório.
fn iniciar(app: &tauri::AppHandle) -> Result<Nucleo, String> {
    let nome = if cfg!(windows) { "eqpress-nucleo.exe" } else { "eqpress-nucleo" };
    let empacotado = std::env::current_exe().ok().and_then(|e| e.parent().map(|d| d.join(nome)));
    let mut c = match empacotado.filter(|p| p.exists()) {
        Some(p) => {
            // Mac: o .dmg baixado marca tudo com quarentena; o app já foi aprovado ao abrir, mas o
            // TeX, o Ghostscript e o Inkscape que vêm dentro dele seriam barrados um a um
            #[cfg(target_os = "macos")]
            if let Some(pacote) = p.ancestors().nth(3).filter(|d| d.extension().is_some_and(|e| e == "app")) {
                let _ = Command::new("/usr/bin/xattr").args(["-dr", "com.apple.quarantine"]).arg(pacote).status();
            }
            let mut c = Command::new(p);
            c.arg("servidor");
            if let Ok(rec) = app.path().resource_dir() {
                let ferramentas = rec.join("ferramentas");
                if ferramentas.is_dir() {
                    c.env("EQPRESS_FERRAMENTAS", ferramentas);
                }
            }
            c
        }
        None => {
            let py = if cfg!(windows) { format!("{RAIZ}/.venv/Scripts/python.exe") } else { format!("{RAIZ}/.venv/bin/python") };
            let mut c = Command::new(py);
            c.args(["-m", "eqpress", "servidor"]).current_dir(RAIZ);
            c
        }
    };
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        c.creation_flags(0x0800_0000); // CREATE_NO_WINDOW: sem janela de console
    }
    let mut p = c
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| format!("não consegui iniciar o núcleo do EqPress: {e}"))?;
    let entrada = p.stdin.take().ok_or("sem entrada do núcleo")?;
    let saida = BufReader::new(p.stdout.take().ok_or("sem saída do núcleo")?);
    Ok(Nucleo { _processo: p, entrada, saida })
}

#[tauri::command]
async fn pedido(app: tauri::AppHandle, q: Value, estado: tauri::State<'_, Estado>) -> Result<Value, String> {
    let mut g = estado.nucleo.lock().map_err(|e| e.to_string())?;
    if g.is_none() {
        *g = Some(iniciar(&app)?);
    }
    let n = g.as_mut().unwrap();
    let mut linha = String::new();
    let ok = writeln!(n.entrada, "{q}").and_then(|_| n.entrada.flush()).is_ok()
        && n.saida.read_line(&mut linha).map(|b| b > 0).unwrap_or(false);
    if !ok {
        *g = None; // o próximo pedido reinicia o núcleo
        return Err("o núcleo do EqPress parou; tente de novo".into());
    }
    serde_json::from_str(&linha).map_err(|e| format!("resposta inválida do núcleo: {e}"))
}

/// Diálogos do sistema: "equacao" (NNNN.json), "docx", "pasta" (_EqPress), "padrao" (importar),
/// "salvar_padrao" (exportar, com `sugestao` de nome).
#[tauri::command]
async fn escolher(app: tauri::AppHandle, tipo: String, sugestao: Option<String>) -> Option<String> {
    let d = app.dialog().file();
    let r = match tipo.as_str() {
        "equacao" => d.set_title("Abrir equação do EqPress").add_filter("Equação EqPress", &["json"]).blocking_pick_file(),
        "docx" => d.set_title("Escolha o Word com as equações do MathType").add_filter("Word", &["docx"]).blocking_pick_file(),
        "pasta" => d.set_title("Escolha a pasta _EqPress do livro").blocking_pick_folder(),
        "padrao" => d.set_title("Importar padrão").add_filter("Padrão EqPress", &["json"]).blocking_pick_file(),
        "salvar_padrao" => d
            .set_title("Exportar padrão")
            .set_file_name(sugestao.unwrap_or_else(|| "padrao.json".into()))
            .add_filter("Padrão EqPress", &["json"])
            .blocking_save_file(),
        _ => None,
    };
    r.map(|f| f.to_string())
}

#[tauri::command]
fn pendente(estado: tauri::State<'_, Estado>) -> Option<String> {
    estado.pendente.lock().ok()?.take()
}

/// eqpress://editar?arquivo=/…/equacoes/0042.json → caminho do JSON (ED-20)
fn arquivo_do_link(link: &url::Url) -> Option<String> {
    link.query_pairs().find(|(k, _)| k == "arquivo").map(|(_, v)| v.into_owned())
}

fn main() {
    tauri::Builder::default()
        // Windows/Linux: o link eqpress:// abre outro processo; este plugin o entrega à janela aberta
        // (precisa ser o primeiro plugin; com a feature deep-link ele dispara o on_open_url)
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.set_focus();
            }
        }))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_deep_link::init())
        .manage(Estado::default())
        .setup(|app| {
            #[cfg(any(windows, target_os = "linux"))]
            app.deep_link().register_all()?; // registra eqpress:// para este usuário
            let h = app.handle().clone();
            if let Some(links) = app.deep_link().get_current()? {
                if let Some(c) = links.iter().find_map(arquivo_do_link) {
                    *app.state::<Estado>().pendente.lock().unwrap() = Some(c);
                }
            }
            app.deep_link().on_open_url(move |ev| {
                for c in ev.urls().iter().filter_map(arquivo_do_link) {
                    *h.state::<Estado>().pendente.lock().unwrap() = Some(c.clone());
                    let _ = h.emit("abrir", c);
                    if let Some(w) = h.get_webview_window("main") {
                        let _ = w.set_focus();
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![pedido, escolher, pendente])
        .run(tauri::generate_context!())
        .expect("erro ao iniciar o EqPress");
}
