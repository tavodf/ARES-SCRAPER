import os
import sys
import time
import ctypes
import threading

def _asegurar_escritorio_interactivo():
    """
    Si el proceso fue lanzado desde un entorno sandboxed (ej. exebox-*),
    redirige la ejecución al escritorio interactivo principal (WinSta0\\Default)
    para que la ventana gráfica sea visible en la pantalla del usuario.
    """
    if os.name != "nt" or os.environ.get("ARES_DEFAULT_DESKTOP") == "1":
        return
    try:
        u32 = ctypes.windll.user32
        k32 = ctypes.windll.kernel32
        hdesk = u32.GetThreadDesktop(k32.GetCurrentThreadId())
        buf = ctypes.create_unicode_buffer(256)
        u32.GetUserObjectInformationW(hdesk, 2, buf, 512, None)
        if buf.value and buf.value.lower() != "default":
            from ctypes import wintypes
            class STARTUPINFOW(ctypes.Structure):
                _fields_ = [
                    ('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR),
                    ('lpDesktop', wintypes.LPWSTR), ('lpTitle', wintypes.LPWSTR),
                    ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
                    ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD),
                    ('dwXCountChars', wintypes.DWORD), ('dwYCountChars', wintypes.DWORD),
                    ('dwFillAttribute', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                    ('wShowWindow', wintypes.WORD), ('cbReserved2', wintypes.WORD),
                    ('lpReserved2', ctypes.POINTER(wintypes.BYTE)),
                    ('hStdInput', wintypes.HANDLE), ('hStdOutput', wintypes.HANDLE),
                    ('hStdError', wintypes.HANDLE)
                ]
            class PROCESS_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                    ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)
                ]
            os.environ["ARES_DEFAULT_DESKTOP"] = "1"
            si = STARTUPINFOW()
            si.cb = ctypes.sizeof(si)
            si.lpDesktop = "WinSta0\\Default"
            si.dwFlags = 1
            si.wShowWindow = 1
            pi = PROCESS_INFORMATION()
            cmd_str = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
            cmd_buf = ctypes.create_unicode_buffer(cmd_str)
            ok = k32.CreateProcessW(
                None, cmd_buf, None, None, False, 0, None, os.getcwd(), ctypes.byref(si), ctypes.byref(pi)
            )
            if ok:
                k32.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)
                sys.exit(0)
    except Exception:
        pass

_asegurar_escritorio_interactivo()

import webview
from adapters.router import get_adapter

_scraper_mod = None
_analyzer_mod = None
_log_buffer = []

class _ConsoleTeeStream:
    """Captura todos los prints y errores de Python en tiempo real para enviarlos a la consola de la GUI."""
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, text):
        if self.original_stream:
            try:
                self.original_stream.write(text)
            except Exception:
                pass
        if text and text.strip():
            for line in text.splitlines():
                clean_line = line.strip()
                if clean_line:
                    _log_buffer.append(clean_line)

    def flush(self):
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass

sys.stdout = _ConsoleTeeStream(sys.__stdout__)
sys.stderr = _ConsoleTeeStream(sys.__stderr__)

def _cargar_modulos_pesados():
    global _scraper_mod, _analyzer_mod
    if _scraper_mod is None:
        import scraper as s
        _scraper_mod = s
    if _analyzer_mod is None:
        import analyzer as a
        _analyzer_mod = a
    return _scraper_mod, _analyzer_mod

class AresInteractiveAPI:
    def __init__(self):
        self.current_url = ""
        self.current_adapter = None
        self.dom_inicial = None
        self.raw_doms = []
        self.parsed_items = []
        self.start_time = 0

    def obtener_logs_pendientes(self):
        global _log_buffer
        if not _log_buffer:
            return []
        lote = list(_log_buffer)
        _log_buffer.clear()
        return lote

    def limpiar_memoria(self):
        self.raw_doms = []
        self.parsed_items = []
        self.dom_inicial = None
        return {"status": "success"}

    def auditar_target(self, url: str, clean_before: bool = True):
        if not url or not url.startswith("http"):
            return {"status": "error", "message": "Protocolo inválido. Requiere http:// o https://"}

        if clean_before:
            self.parsed_items = []
            self.raw_doms = []

        self.current_url = url
        self.start_time = time.time()
        try:
            scraper, analyzer = _cargar_modulos_pesados()
            import scraper_selenium
            self.current_adapter = get_adapter(url)
            adapter_name = self.current_adapter.__class__.__name__

            self.dom_inicial = scraper.obtener_dom(url)
            if not self.dom_inicial:
                detalle_err = getattr(scraper_selenium, "ULTIMO_ERROR_STEALTH", "")
                msg = f"Sin respuesta del servidor objetivo. {detalle_err}".strip()
                return {"status": "error", "message": msg}

            items_crudos = self.current_adapter.parse_items(self.dom_inicial)
            items_muestra, ruido_muestra = analyzer.depurar_y_normalizar_memoria(items_crudos)
            total_muestra = len(items_muestra)

            if total_muestra == 0:
                return {"status": "error", "message": "Muestra inicial arrojó 0 productos. Verifique si hay Captcha o ajuste selectores."}

            return {
                "status": "success",
                "adapter": adapter_name,
                "total_muestra": total_muestra,
                "ruido_muestra": ruido_muestra
            }
        except Exception as e:
            return {"status": "error", "message": f"{type(e).__name__}: {e}"}

    def ejecutar_barrido(self, pages: int, clean_before: bool = True):
        try:
            scraper, analyzer = _cargar_modulos_pesados()
            import scraper_selenium
            pages = int(pages) if int(pages) > 0 else 1
            self.raw_doms = scraper.extraer_multiples_paginas(
                self.current_url, pages, dom_inicial=self.dom_inicial
            )

            if not self.raw_doms:
                detalle_err = getattr(scraper_selenium, "ULTIMO_ERROR_STEALTH", "")
                return {"status": "error", "message": f"Falla de red en barrido masivo. {detalle_err}".strip()}

            nuevos_items = []
            for dom in self.raw_doms:
                items = self.current_adapter.parse_items(dom)
                nuevos_items.extend(items)

            if clean_before:
                lote_combinado = nuevos_items
            else:
                lote_combinado = self.parsed_items + nuevos_items

            # Depuración y normalización inmediata en memoria para sincronizar 1:1 Pantalla y Descarga
            self.parsed_items, ruido_purgado = analyzer.depurar_y_normalizar_memoria(lote_combinado)

            duracion = round(time.time() - self.start_time, 1)

            precios_validos = [float(it.get("price", 0)) for it in self.parsed_items if float(it.get("price", 0)) > 0]
            precio_promedio = round(sum(precios_validos) / len(precios_validos), 0) if precios_validos else 0.0
            precio_min = round(min(precios_validos), 0) if precios_validos else 0.0
            precio_max = round(max(precios_validos), 0) if precios_validos else 0.0

            return {
                "status": "success",
                "total_extraido": len(self.parsed_items),
                "ruido_purgado": ruido_purgado,
                "precio_promedio": precio_promedio,
                "precio_min": precio_min,
                "precio_max": precio_max,
                "duracion": f"{duracion}s",
                "items": self.parsed_items
            }
        except Exception as e:
            return {"status": "error", "message": f"{type(e).__name__}: {e}"}

    def guardar_dataset(self, dataset_name: str):
        if not self.parsed_items:
            return {"status": "error", "message": "Sin registros en memoria."}

        try:
            _, analyzer = _cargar_modulos_pesados()
            nombre = dataset_name.strip() if dataset_name else "ares_dataset"
            ruta = analyzer.procesar_y_guardar_datos(self.parsed_items, nombre)

            return {
                "status": "success",
                "total_guardado": len(self.parsed_items),
                "ruta": ruta
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def exportar_json(self, dataset_name: str = "ares_dataset"):
        if not self.parsed_items:
            return {"status": "error", "message": "Sin registros en memoria para exportar a JSON."}
        try:
            _, analyzer = _cargar_modulos_pesados()
            nombre = dataset_name.strip() if dataset_name else "ares_dataset"
            ruta = analyzer.exportar_json_datos(self.parsed_items, nombre)
            return {
                "status": "success",
                "total_guardado": len(self.parsed_items),
                "ruta": ruta
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


def iniciar_interfaz():
    api = AresInteractiveAPI()

    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>NOVUX CYBER SCRAPER // ARES GRID</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #000000;
            color: #ff3333;
            font-family: 'Consolas', monospace;
            overflow: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        #matrixCanvas {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: 1;
            opacity: 0.65;
            pointer-events: none;
        }
        header {
            position: relative; z-index: 10;
            display: flex; justify-content: space-between; align-items: center;
            padding: clamp(8px, 1.2vh, 14px) clamp(14px, 2.5vw, 32px);
            border-bottom: 1px solid #ff0000;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(6px);
            flex-wrap: wrap;
            gap: 8px;
        }
        .brand { display: flex; align-items: center; gap: 8px; font-weight: bold; }
        .brand-logo { border: 1px solid #ff0000; padding: 2px 6px; box-shadow: 0 0 8px #ff0000; color: #ff0000; }
        .brand-text { font-size: clamp(10px, 1vw, 13px); letter-spacing: 2px; color: #ff4444; }
        .nav-tabs { display: flex; gap: 10px; }
        .nav-btn {
            background: transparent; border: 1px solid #660000; color: #ff6666;
            padding: 5px 14px; font-size: clamp(10px, 0.95vw, 12px); cursor: pointer; font-family: monospace;
        }
        .nav-btn:hover { border-color: #ff0000; color: #ffaaaa; }
        .nav-btn.active {
            background: #ff0000; color: #000; font-weight: bold; box-shadow: 0 0 10px #ff0000; border-color: #ff0000;
        }

        main {
            position: relative; z-index: 10;
            flex: 1; padding: clamp(10px, 2vh, 24px) clamp(12px, 3vw, 36px);
            display: flex; justify-content: center; align-items: center;
            overflow-y: auto;
            width: 100%;
        }

        /* CORE FRAME FLOTANTE RESPONSIVE CON 70% TRANSPARENCIA */
        .core-frame {
            width: clamp(320px, 86vw, 1220px);
            max-height: calc(100vh - 92px);
            background: rgba(4, 0, 0, 0.70);
            backdrop-filter: blur(4px);
            border: 2px solid #ff0000;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.35);
            padding: clamp(12px, 2vh, 22px) clamp(14px, 2.2vw, 28px);
            display: flex;
            flex-direction: column;
            gap: clamp(8px, 1.3vh, 14px);
            overflow-y: auto;
        }

        .hud-title {
            text-align: center; font-size: clamp(13px, 1.3vw, 18px); letter-spacing: 3px; color: #ff0000; font-weight: bold;
        }
        .hud-sub {
            text-align: center; font-size: clamp(8px, 0.8vw, 11px); color: #882222; letter-spacing: 2px; margin-bottom: 2px;
        }

        .target-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .target-row label { font-size: clamp(10px, 0.95vw, 12px); color: #ff4444; white-space: nowrap; font-weight: bold; }
        .target-row input {
            flex: 1; min-width: 200px; background: rgba(0, 0, 0, 0.75); border: 1px solid #aa0000; color: #ff9999;
            padding: 8px 12px; font-family: monospace; font-size: clamp(10px, 0.95vw, 12px);
        }
        .target-row input:focus { outline: none; border-color: #ff0000; box-shadow: 0 0 10px #ff0000; }
        .btn-flow {
            background: #ff0000; color: #000; border: none; padding: 8px 18px;
            font-weight: bold; font-family: monospace; cursor: pointer; letter-spacing: 1px;
            box-shadow: 0 0 12px #ff0000; white-space: nowrap; font-size: clamp(10px, 0.95vw, 12px);
        }

        .clean-check {
            font-size: clamp(9px, 0.85vw, 11px); color: #ff6666;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;
        }
        .clean-check-left { display: flex; align-items: center; gap: 6px; }

        /* PANEL KPI TÁCTICO RESPONSIVE */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }
        .kpi-card {
            background: rgba(12, 0, 0, 0.75);
            border: 1px solid #550000;
            padding: clamp(5px, 0.9vh, 10px) 8px;
            text-align: center;
        }
        .kpi-title { font-size: clamp(7.5px, 0.7vw, 9.5px); color: #993333; letter-spacing: 1px; margin-bottom: 2px; }
        .kpi-val { font-size: clamp(11px, 1.1vw, 15px); font-weight: bold; color: #00ff66; }

        .console-card {
            background: rgba(2, 0, 0, 0.65);
            border: 1px solid #550000;
            display: flex; flex-direction: column;
            flex: 1;
            min-height: 135px;
            height: clamp(150px, 30vh, 420px);
            padding: 10px;
        }
        .console-header {
            display: flex; justify-content: space-between; align-items: center; font-size: clamp(9px, 0.85vw, 11px);
            color: #882222; border-bottom: 1px solid #330000; padding-bottom: 4px; margin-bottom: 6px;
            flex-wrap: wrap; gap: 6px;
        }
        .console-actions {
            display: flex; gap: 10px; align-items: center;
        }
        .console-action-btn {
            cursor: pointer; color: #ff6666; padding: 2px 8px; border: 1px solid #550000; background: rgba(30, 0, 0, 0.6);
        }
        .console-action-btn:hover {
            border-color: #ff0000; color: #00ff66;
        }
        .console-stream {
            flex: 1; overflow-y: auto; font-size: clamp(10.5px, 0.95vw, 12.5px); line-height: 1.45; color: #ff7777;
            user-select: text !important; -webkit-user-select: text !important;
            cursor: text; outline: none; padding: 2px 4px;
            white-space: pre-wrap; word-break: break-word;
        }
        .console-stream:focus {
            border-left: 2px solid #ff0000;
            background: rgba(15, 0, 0, 0.45);
        }

        .cli-row { display: flex; gap: 8px; align-items: center; margin-top: 2px; flex-wrap: wrap; }
        .cli-row span { font-size: clamp(10px, 0.95vw, 12px); color: #ff0000; font-weight: bold; }
        .cli-row input {
            flex: 1; min-width: 180px; background: rgba(0, 0, 0, 0.75); border: 1px solid #550000; color: #ff8888;
            padding: 6px 10px; font-family: monospace; font-size: clamp(10px, 0.95vw, 12px);
        }
        .cli-row input:focus { outline: none; border-color: #ff0000; }
        .btn-cli {
            background: #220000; border: 1px solid #880000; color: #ff6666;
            padding: 5px 12px; font-family: monospace; font-size: clamp(9.5px, 0.85vw, 11px); cursor: pointer;
        }
        .btn-cli:hover { background: #ff0000; color: #000; font-weight: bold; }
        .chips-bar { display: flex; flex-wrap: wrap; gap: 6px; font-size: clamp(9.5px, 0.85vw, 11px); margin-top: 5px; }
        .chip {
            background: rgba(20, 0, 0, 0.6); border: 1px solid #440000; color: #aa4444;
            padding: 3px 8px; cursor: pointer;
        }
        .chip:hover { border-color: #ff0000; color: #ff0000; }

        /* VISTA DE DATOS E INTELIGENCIA COMERCIAL RESPONSIVE */
        #viewDatos {
            display: none;
            width: clamp(320px, 92vw, 1440px);
            height: calc(100vh - 96px);
            flex-direction: column;
        }
        .data-toolbar {
            display: flex; justify-content: space-between; align-items: center; gap: 10px;
            background: rgba(10, 0, 0, 0.88); padding: 10px 14px; border: 1px solid #ff0000;
            flex-wrap: wrap;
        }
        .filter-controls { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
        .search-input {
            background: #050000; border: 1px solid #880000; color: #ffcccc;
            padding: 5px 10px; font-family: monospace; font-size: 11px; width: clamp(150px, 18vw, 260px);
        }
        .search-input:focus { outline: none; border-color: #ff0000; }
        .table-wrap {
            flex: 1; background: rgba(5, 0, 0, 0.85); border: 1px solid #ff0000;
            overflow-y: auto; margin-top: 8px;
        }
        table { width: 100%; border-collapse: collapse; font-size: clamp(10.5px, 0.9vw, 12.5px); text-align: left; }
        th { background: #150000; color: #ff0000; padding: 8px; border-bottom: 1px solid #aa0000; position: sticky; top: 0; }
        td { padding: 6px 8px; border-bottom: 1px solid #220000; color: #ffcccc; }
        tr:hover td { background: rgba(255, 0, 0, 0.08); }
        .td-price { color: #00ff66; font-weight: bold; }

        footer {
            position: relative; z-index: 10;
            display: flex; justify-content: space-between; align-items: center;
            padding: 6px clamp(14px, 2.5vw, 32px); font-size: clamp(9px, 0.8vw, 11px); color: #661111;
            border-top: 1px solid #330000; background: rgba(0, 0, 0, 0.9);
            flex-wrap: wrap; gap: 6px;
        }

        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.88); z-index: 100;
            justify-content: center; align-items: center; padding: 16px;
        }
        .modal-box {
            background: #080000; border: 2px solid #ff0000;
            box-shadow: 0 0 30px #ff0000; padding: 20px; width: min(92vw, 480px);
        }
        .modal-actions { display: flex; gap: 10px; margin-top: 14px; }
        .modal-actions button {
            flex: 1; padding: 8px; font-family: monospace; font-size: 11px; font-weight: bold; cursor: pointer;
        }
        .btn-yes { background: #ff0000; color: #000; border: none; }
        .btn-no { background: #220000; color: #ff5555; border: 1px solid #660000; }

        @media (max-width: 760px) {
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
            .btn-flow { width: 100%; }
            .core-frame { width: 96vw; }
            #viewDatos { width: 96vw; }
        }
    </style>
</head>
<body>
    <canvas id="matrixCanvas"></canvas>

    <header>
        <div class="brand">
            <span class="brand-logo">[N]</span>
            <span class="brand-text">NOVUX // ARES GRID</span>
        </div>
        <div class="nav-tabs">
            <button class="nav-btn active" id="tabConsole" onclick="mostrarTab('console')">[ >_ CONSOLA ]</button>
            <button class="nav-btn" id="tabData" onclick="mostrarTab('data')">[ ☷ DATOS (<span id="countData">0</span>) ]</button>
        </div>
    </header>

    <main>
        <div class="core-frame" id="viewConsole">
            <div>
                <div class="hud-title">[ NOVUX DATA FACTORY ] // ARES GRID</div>
                <div class="hud-sub">— EXTRACTOR &amp; MINERÍA WEB EN TIEMPO REAL —</div>
            </div>

            <div class="target-row">
                <label>@ URL_OBJETIVO:</label>
                <input type="text" id="targetUrl" placeholder="https://listado.mercadolibre.com.co/... | https://www.amazon.com/s?k=... | https://www.temu.com/...">
                <button class="btn-flow" id="btnFlujo" onclick="iniciarReconocimiento()">[ ▶ INICIAR FLUJO ]</button>
            </div>

            <div class="clean-check">
                <div class="clean-check-left">
                    <input type="checkbox" id="cleanDataCheck" checked>
                    <label for="cleanDataCheck">Limpiar datos automáticamente antes de cada scrap (desmarcar para acumular multi-tienda)</label>
                </div>
                <span style="color:#00ff66; font-size:9px;">[✓] SESIÓN STEALTH PERSISTENTE ACTIVA</span>
            </div>

            <!-- TARJETAS KPI TÁCTICAS -->
            <div class="kpi-row" id="kpiPanel">
                <div class="kpi-card">
                    <div class="kpi-title">REGISTROS ÚNICOS</div>
                    <div class="kpi-val" id="kpiTotal">0 ITEMS</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">CLONES PURGADOS</div>
                    <div class="kpi-val" id="kpiPurged" style="color:#ffaa00;">0 NODOS</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">PRECIO PROMEDIO</div>
                    <div class="kpi-val" id="kpiAvg">$0</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">TIEMPO EJECUCIÓN</div>
                    <div class="kpi-val" id="kpiTime" style="color:#00ffff;">0.0s</div>
                </div>
            </div>

            <div class="console-card">
                <div class="console-header">
                    <span>>_ CONSOLE_OUTPUT_STREAM | ARES-OS_DIAGNOSTICS (INTERACTIVA: SELECCIONE, COPIE O ESCRIBA)</span>
                    <div class="console-actions">
                        <span class="console-action-btn" onclick="copiarLogs()">[ 📋 COPIAR LOGS ]</span>
                        <span class="console-action-btn" onclick="limpiarLogs()">[ LIMPIAR LOGS ]</span>
                    </div>
                </div>
                <div class="console-stream" id="logs" contenteditable="true" spellcheck="false">[SYSTEM] Ares Grid OS v1.1 listo. Consola interactiva habilitada (puede seleccionar, copiar o escribir notas/errores aquí).<br></div>
            </div>

            <div>
                <div class="cli-row">
                    <span>COMANDO ></span>
                    <input type="text" id="cliInput" placeholder="Escriba comando (ayuda, datos, ordenar asc, export json) y presione Enter..." onkeydown="if(event.key==='Enter') procesarComandoCLI()">
                    <button class="btn-cli" onclick="procesarComandoCLI()">[ EJECUTAR ]</button>
                </div>
                <div class="chips-bar">
                    <span class="chip" onclick="ejecutarChip('ayuda')">ayuda</span>
                    <span class="chip" onclick="ejecutarChip('limpiardatos')">limpiar datos</span>
                    <span class="chip" onclick="copiarLogs()">copiar logs</span>
                    <span class="chip" onclick="limpiarLogs()">limpiar logs</span>
                    <span class="chip" onclick="mostrarTab('data')">datos</span>
                    <span class="chip" onclick="ejecutarChip('ordenar_asc')">precio ▲</span>
                    <span class="chip" onclick="ejecutarChip('ordenar_desc')">precio ▼</span>
                    <span class="chip" onclick="ejecutarChip('export_json')">export json</span>
                </div>
            </div>
        </div>

        <div id="viewDatos">
            <div class="data-toolbar">
                <div>
                    <span style="font-size:12px; color:#ff0000; font-weight:bold;">[ MATRIZ DE REGISTROS EXTRAÍDOS ]</span>
                    <div style="font-size:9px; color:#00ff66; margin-top:2px;" id="statsBar">
                        MÍN: $0 | PROM: $0 | MÁX: $0
                    </div>
                </div>
                <div class="filter-controls">
                    <input type="text" class="search-input" id="searchTableInput" placeholder="Filtrar por nombre o ID..." oninput="filtrarYRenderizarTabla()">
                    <button class="nav-btn" id="btnSortAsc" onclick="ordenarTabla('asc')">[ ▲ PRECIO MENOR ]</button>
                    <button class="nav-btn" id="btnSortDesc" onclick="ordenarTabla('desc')">[ ▼ PRECIO MAYOR ]</button>
                    <button class="nav-btn" onclick="abrirCompuertaDescarga(currentItems.length)">[ 💾 EXPORTAR CSV ]</button>
                    <button class="nav-btn" onclick=" mostrarTab('console')">[ + CONSOLA ]</button>
                </div>
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th style="width:135px;">ID</th>
                            <th>PRODUCTO (TÍTULO &amp; ESPECIFICACIONES)</th>
                            <th style="width:130px;">PRECIO</th>
                            <th style="width:80px;">ENLACE</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <tr><td colspan="4" style="text-align:center; color:#555; padding:20px;">TABLA VACÍA // SIN REGISTROS</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <footer>
        <span>[ NOVUX TECHNOLOGIES ] © 2026 // ARES GRID</span>
        <span id="footStatus">ESTADO: IDLE // WIP=1</span>
        <span>REGISTROS ÚNICOS: <span id="footCount">0</span></span>
    </footer>

    <div class="modal-overlay" id="modalControl">
        <div class="modal-box">
            <div style="font-size:13px; color:#ff0000; font-weight:bold; margin-bottom:10px;" id="modalTitle">[ COMPUERTA 1 ]</div>
            <div style="font-size:11px; color:#ffcccc; margin-bottom:12px; line-height:1.4;" id="modalBody"></div>
            <div id="modalInputs"></div>
            <div class="modal-actions" id="modalActions"></div>
        </div>
    </div>

    <script>
        let currentItems = [];
        let currentSortOrder = null;

        // MATRIX RESPONSIVE: SE ADAPTA AL 100% DE CUALQUIER RESOLUCIÓN O PANTALLA MAXIMIZADA
        const canvas = document.getElementById('matrixCanvas');
        const ctx = canvas.getContext('2d');
        const chars = "0123456789ABCDEFNOVUXARESØ1¥$";
        const fontDim = 13;
        let drops = [];

        function resizeCanvas() {
            const w = document.documentElement.clientWidth || window.innerWidth;
            const h = document.documentElement.clientHeight || window.innerHeight;
            canvas.width = w;
            canvas.height = h;
            const newCols = Math.ceil(w / fontDim) + 2;
            if (newCols > drops.length) {
                for (let i = drops.length; i < newCols; i++) {
                    drops.push(Math.floor(Math.random() * Math.max(10, Math.floor(h / fontDim))));
                }
            } else if (newCols < drops.length) {
                drops.length = newCols;
            }
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        function drawMatrix() {
            const currentW = document.documentElement.clientWidth || window.innerWidth;
            const currentH = document.documentElement.clientHeight || window.innerHeight;
            if (canvas.width !== currentW || canvas.height !== currentH) {
                resizeCanvas();
            }

            ctx.fillStyle = "rgba(0, 0, 0, 0.12)";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.font = `bold ${fontDim}px monospace`;
            for(let i = 0; i < drops.length; i++) {
                const txt = chars.charAt(Math.floor(Math.random() * chars.length));
                const x = i * fontDim;
                const y = drops[i] * fontDim;

                const rand = Math.random();
                if (rand > 0.96) {
                    ctx.fillStyle = "#ffffff"; // Blanco brillante
                } else if (rand > 0.88) {
                    ctx.fillStyle = "#ffd700"; // Dorado neón
                } else {
                    ctx.fillStyle = "#ff1a1a"; // Rojo cibernético
                }

                ctx.fillText(txt, x, y);

                if(y > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
        }
        setInterval(drawMatrix, 40);

        function playBeep(freq=650, duration=0.08) {
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + duration);
            } catch(e) {}
        }

        function hablarVozRobotica(mensaje) {
            if ('speechSynthesis' in window) {
                const utter = new SpeechSynthesisUtterance(mensaje);
                utter.rate = 0.92;
                utter.pitch = 0.75;
                utter.lang = 'es-ES';
                window.speechSynthesis.speak(utter);
            }
        }

        function getTS() {
            const d = new Date();
            return `[${d.toTimeString().split(' ')[0]}]`;
        }
        function log(msg, color="#ff7777") {
            const box = document.getElementById('logs');
            box.innerHTML += `<span style="color:${color}">${getTS()} ${msg}</span><br>`;
            box.scrollTop = box.scrollHeight;
        }
        function limpiarLogs() { playBeep(450, 0.05); document.getElementById('logs').innerHTML = ""; }

        async function copiarLogs() {
            playBeep(880, 0.06);
            const box = document.getElementById('logs');
            const selection = window.getSelection().toString();
            const textToCopy = selection ? selection : box.innerText;
            try {
                await navigator.clipboard.writeText(textToCopy);
                log("[PORTAPAPELES] Contenido de la consola copiado con éxito.", "#00ff66");
            } catch (e) {
                const temp = document.createElement("textarea");
                temp.value = textToCopy;
                document.body.appendChild(temp);
                temp.select();
                document.execCommand("copy");
                document.body.removeChild(temp);
                log("[PORTAPAPELES] Contenido de la consola copiado con éxito.", "#00ff66");
            }
        }

        async function sincronizarLogsBackend() {
            try {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.obtener_logs_pendientes) {
                    const lineas = await window.pywebview.api.obtener_logs_pendientes();
                    if (lineas && lineas.length > 0) {
                        lineas.forEach(l => {
                            let c = "#ff9999";
                            if (l.includes("[ERROR") || l.includes("[ALERTA")) c = "#ff2222";
                            else if (l.includes("[ÉXITO]") || l.includes("Sesión activa")) c = "#00ff66";
                            else if (l.includes("[STEALTH]") || l.includes("[RED]") || l.includes("[CACHE]")) c = "#00ffff";
                            else if (l.includes("[TELEMETRÍA]")) c = "#ffaa00";
                            log(l, c);
                        });
                    }
                }
            } catch(e) {}
        }
        setInterval(sincronizarLogsBackend, 600);

        function mostrarTab(tab) {
            playBeep(800, 0.05);
            if(tab === 'console') {
                document.getElementById('viewConsole').style.display = 'flex';
                document.getElementById('viewDatos').style.display = 'none';
                document.getElementById('tabConsole').classList.add('active');
                document.getElementById('tabData').classList.remove('active');
            } else {
                document.getElementById('viewConsole').style.display = 'none';
                document.getElementById('viewDatos').style.display = 'flex';
                document.getElementById('tabConsole').classList.remove('active');
                document.getElementById('tabData').classList.add('active');
            }
        }

        async function iniciarReconocimiento() {
            playBeep(900, 0.08);
            const url = document.getElementById('targetUrl').value.trim();
            if(!url) { log("[ALERTA] Ingrese una URL válida.", "#ff3333"); return; }

            const cleanBefore = document.getElementById('cleanDataCheck').checked;
            if (cleanBefore) {
                currentItems = [];
                currentSortOrder = null;
                document.getElementById('tableBody').innerHTML = '<tr><td colspan="4" style="text-align:center; color:#555; padding:20px;">TABLA VACÍA // SIN REGISTROS</td></tr>';
                document.getElementById('countData').innerText = "0";
                document.getElementById('footCount').innerText = "0";
                log("[SANITIZACIÓN] Buffer previo limpiado automáticamente.", "#ffaa00");
            } else {
                log(`[MODO ACUMULACIÓN] Conservando ${currentItems.length} registros previos en memoria.`, "#ffaa00");
            }

            document.getElementById('btnFlujo').innerText = "[ AUDITANDO... ]";
            document.getElementById('footStatus').innerText = "ESTADO: AUDITANDO TARGET...";
            log(`[SISTEMA] Handshake con el blanco: ${url}`, "#00ffff");

            const res = await window.pywebview.api.auditar_target(url, cleanBefore);
            await sincronizarLogsBackend();
            document.getElementById('btnFlujo').innerText = "[ ▶ INICIAR FLUJO ]";

            if(res.status === 'error') {
                playBeep(250, 0.25);
                document.getElementById('footStatus').innerText = "ESTADO: ERROR EN AUDITORÍA";
                log(`[ERROR] ${res.message}`, "#ff0000");
                return;
            }

            playBeep(1100, 0.1);
            document.getElementById('footStatus').innerText = "ESTADO: EN ESPERA COMPUERTA 1";
            log(`[ADAPTADOR ASIGNADO] ${res.adapter} | Muestra única Página 1: ${res.total_muestra} registros (${res.ruido_muestra} clones filtrados).`, "#00ff66");
            abrirCompuertaBarrido(res.adapter, res.total_muestra);
        }

        function abrirCompuertaBarrido(adapter, muestra) {
            document.getElementById('modalTitle').innerText = "[ COMPUERTA 1: AUTORIZAR BARRIDO ]";
            document.getElementById('modalBody').innerHTML = `
                Adaptador: <b style="color:#00ff66;">${adapter}</b><br>
                Muestra única verificada (Página 1): <b style="color:#00ffff;">${muestra}</b> productos reales.<br>
                <i>(Página 1 ya en caché de memoria; si elige 1 página la extracción será instantánea).</i><br><br>
                ¿Autoriza proceder con el barrido masivo?
            `;
            document.getElementById('modalInputs').innerHTML = `
                <div style="margin-bottom:10px;">
                    <label style="font-size:11px; color:#ff8888;">PÁGINAS A ESCANEAR:</label>
                    <input type="text" id="modalPages" value="1" style="width:70px; text-align:center; background:#000; border:1px solid #aa0000; color:#fff; font-family:monospace; padding:4px;">
                </div>
            `;
            document.getElementById('modalActions').innerHTML = `
                <button class="btn-yes" onclick="confirmarBarrido()">[ CONFIRMAR BARRIDO ]</button>
                <button class="btn-no" onclick="cerrarModal()">[ ABORTAR ]</button>
            `;
            document.getElementById('modalControl').style.display = "flex";
        }

        async function confirmarBarrido() {
            playBeep(950, 0.08);
            const pages = document.getElementById('modalPages').value;
            const cleanBefore = document.getElementById('cleanDataCheck').checked;
            cerrarModal();

            document.getElementById('footStatus').innerText = `ESTADO: BARRIENDO ${pages} PÁGINA(S)...`;
            log(`[BARRIDO] Extracción sobre ${pages} página(s)...`, "#00ffff");
            const res = await window.pywebview.api.ejecutar_barrido(pages, cleanBefore);

            if(res.status === 'error') {
                playBeep(250, 0.25);
                document.getElementById('footStatus').innerText = "ESTADO: FALLO DE RED";
                log(`[ERROR BARRIDO] ${res.message}`, "#ff0000");
                return;
            }

            currentItems = res.items || [];

            // Actualizar KPIs y Contadores (100% sincronizados con el CSV final)
            document.getElementById('countData').innerText = res.total_extraido;
            document.getElementById('footCount').innerText = res.total_extraido;
            document.getElementById('kpiTotal').innerText = `${res.total_extraido} ITEMS`;
            document.getElementById('kpiPurged').innerText = `${res.ruido_purgado} NODOS`;
            document.getElementById('kpiAvg').innerText = `$${Number(res.precio_promedio).toLocaleString()}`;
            document.getElementById('kpiTime').innerText = res.duracion;
            document.getElementById('footStatus').innerText = "ESTADO: MATRIZ CONSOLIDADA";

            document.getElementById('statsBar').innerText =
                `MÍN: $${Number(res.precio_min).toLocaleString()} | PROM: $${Number(res.precio_promedio).toLocaleString()} | MÁX: $${Number(res.precio_max).toLocaleString()}`;

            filtrarYRenderizarTabla();

            playBeep(1200, 0.15);
            hablarVozRobotica(`Usuario, hemos encontrado ${res.total_extraido} registros únicos en el sector.`);
            if (res.ruido_purgado > 0) {
                log(`[TELEMETRÍA DATA LAKE] ${res.ruido_purgado} nodos clonados/patrocinados fueron purgados.`, "#ffaa00");
            }
            log(`[COMPLETADO] Flujo finalizado en ${res.duracion}. ${res.total_extraido} registros únicos listos para descarga.`, "#00ff66");

            abrirCompuertaDescarga(res.total_extraido, res.ruido_purgado);
        }

        function ordenarTabla(order) {
            playBeep(850, 0.05);
            currentSortOrder = order;
            document.getElementById('btnSortAsc').classList.toggle('active', order === 'asc');
            document.getElementById('btnSortDesc').classList.toggle('active', order === 'desc');
            filtrarYRenderizarTabla();
            log(`[MATRIZ] Registros ordenados por precio (${order === 'asc' ? 'Menor a Mayor' : 'Mayor a Menor'}).`, "#00ffff");
        }

        function filtrarYRenderizarTabla() {
            const query = (document.getElementById('searchTableInput').value || "").toLowerCase().trim();
            let list = [...currentItems];

            if (query) {
                list = list.filter(it =>
                    String(it.title || "").toLowerCase().includes(query) ||
                    String(it.id || "").toLowerCase().includes(query)
                );
            }

            if (currentSortOrder === 'asc') {
                list.sort((a, b) => Number(a.price || 0) - Number(b.price || 0));
            } else if (currentSortOrder === 'desc') {
                list.sort((a, b) => Number(b.price || 0) - Number(a.price || 0));
            }

            poblarTabla(list);
        }

        function poblarTabla(items) {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = "";
            if (!items || items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#555; padding:20px;">SIN COINCIDENCIAS // TABLA VACÍA</td></tr>';
                return;
            }
            items.forEach(it => {
                const priceFormatted = `$${Number(it.price).toLocaleString()}`;
                const titleText = String(it.title || "");
                const titleDisplay = titleText.length > 68 ? titleText.substring(0, 68) + "..." : titleText;
                tbody.innerHTML += `
                    <tr>
                        <td style="color:#ff5555; font-weight:bold;">${it.id}</td>
                        <td title="${titleText.replace(/"/g, '&quot;')}">${titleDisplay}</td>
                        <td class="td-price">${priceFormatted}</td>
                        <td><a href="${it.url}" target="_blank" style="color:#00ffff; text-decoration:none; font-weight:bold;">[VER]</a></td>
                    </tr>
                `;
            });
        }

        function abrirCompuertaDescarga(total, purgados = 0) {
            if (!total || total === 0) {
                log("[ALERTA] No hay registros en memoria para exportar.", "#ff3333");
                return;
            }
            document.getElementById('modalTitle').innerText = "[ COMPUERTA 2: PERSISTENCIA DATA LAKE ]";
            document.getElementById('modalBody').innerHTML = `
                Registros únicos verificados a descargar: <b style="color:#00ff66;">${total}</b> productos (100% íntegros).<br>
                Ruido publicitario / duplicados eliminados: <b style="color:#ffaa00;">${purgados}</b>.<br><br>
                ¿Desea exportar este dataset al Data Lake (.CSV compatible con Excel)?
            `;
            document.getElementById('modalInputs').innerHTML = `
                <div style="margin-bottom:10px;">
                    <label style="font-size:11px; color:#ff8888;">NOMBRE DEL ARCHIVO (.CSV):</label>
                    <input type="text" id="modalDatasetName" value="dataset_market" style="width:100%; background:#000; border:1px solid #aa0000; color:#fff; font-family:monospace; padding:6px;">
                </div>
            `;
            document.getElementById('modalActions').innerHTML = `
                <button class="btn-yes" onclick="confirmarGuardado()">[ PERSISTIR DATASET (.CSV) ]</button>
                <button class="btn-no" onclick="cerrarModal()">[ POSPONER ]</button>
            `;
            document.getElementById('modalControl').style.display = "flex";
        }

        async function confirmarGuardado() {
            playBeep(1000, 0.08);
            const name = document.getElementById('modalDatasetName').value;
            cerrarModal();

            log(`[DATALAKE] Guardando matriz de ${currentItems.length} registros únicos en disco...`, "#00ffff");
            const res = await window.pywebview.api.guardar_dataset(name);

            if(res.status === 'error') {
                playBeep(250, 0.25);
                log(`[ERROR GUARDADO] ${res.message}`, "#ff0000");
                return;
            }

            playBeep(1300, 0.18);
            log(`[ÉXITO FINAL] ${res.total_guardado} registros guardados sin pérdidas en: ${res.ruta}`, "#00ff66");
        }

        function cerrarModal() {
            playBeep(400, 0.06);
            document.getElementById('modalControl').style.display = "none";
            log("[SISTEMA] Compuerta cerrada por el operador.", "#555555");
        }

        async function procesarComandoCLI() {
            const input = document.getElementById('cliInput');
            const rawCmd = input.value.trim();
            if (!rawCmd) return;
            input.value = "";
            log(`ARES_GRID > ${rawCmd}`, "#ffffff");

            const lower = rawCmd.toLowerCase();
            if (rawCmd.startsWith("http://") || rawCmd.startsWith("https://")) {
                document.getElementById('targetUrl').value = rawCmd;
                await iniciarReconocimiento();
            } else if (lower === "ayuda" || lower === "help") {
                ejecutarChip('ayuda');
            } else if (lower === "limpiar datos" || lower === "limpiardatos" || lower === "clear data") {
                ejecutarChip('limpiardatos');
            } else if (lower === "limpiar logs" || lower === "clear") {
                limpiarLogs();
            } else if (lower === "datos" || lower === "data") {
                mostrarTab('data');
            } else if (lower === "consola" || lower === "console") {
                mostrarTab('console');
            } else if (lower === "ordenar asc" || lower === "precio asc") {
                mostrarTab('data');
                ordenarTabla('asc');
            } else if (lower === "ordenar desc" || lower === "precio desc") {
                mostrarTab('data');
                ordenarTabla('desc');
            } else if (lower.startsWith("export json") || lower === "json") {
                ejecutarChip('export_json');
            } else if (lower.startsWith("export csv") || lower === "csv") {
                abrirCompuertaDescarga(currentItems.length, 0);
            } else {
                log(`[CLI] Comando no reconocido: '${rawCmd}'. Escriba 'ayuda' para ver opciones.`, "#ff5555");
            }
        }

        async function ejecutarChip(cmd) {
            playBeep(750, 0.05);
            if(cmd === 'ayuda') {
                log("Directivas disponibles: 'ayuda', 'limpiar datos', 'limpiar logs', 'datos', 'ordenar asc', 'ordenar desc', 'export json', o pegue una URL http(s)://.", "#00ffff");
            } else if(cmd === 'limpiardatos') {
                await window.pywebview.api.limpiar_memoria();
                currentItems = [];
                currentSortOrder = null;
                document.getElementById('tableBody').innerHTML = '<tr><td colspan="4" style="text-align:center; color:#555; padding:20px;">TABLA VACÍA // SIN REGISTROS</td></tr>';
                document.getElementById('countData').innerText = "0";
                document.getElementById('footCount').innerText = "0";
                document.getElementById('kpiTotal').innerText = "0 ITEMS";
                document.getElementById('kpiPurged').innerText = "0 NODOS";
                document.getElementById('kpiAvg').innerText = "$0";
                document.getElementById('kpiTime').innerText = "0.0s";
                log("[SISTEMA] Buffer de datos en memoria y tabla purgados al 100%.", "#ffaa00");
            } else if(cmd === 'ordenar_asc') {
                mostrarTab('data');
                ordenarTabla('asc');
            } else if(cmd === 'ordenar_desc') {
                mostrarTab('data');
                ordenarTabla('desc');
            } else if(cmd === 'export_json') {
                if (currentItems.length === 0) {
                    log("[ALERTA] No hay registros en memoria para exportar a JSON.", "#ff3333");
                    return;
                }
                const res = await window.pywebview.api.exportar_json("ares_dataset");
                if (res.status === 'success') {
                    playBeep(1300, 0.15);
                    log(`[JSON EXPORT] ${res.total_guardado} registros exportados en: ${res.ruta}`, "#00ff66");
                } else {
                    log(`[ERROR JSON] ${res.message}`, "#ff0000");
                }
            }
        }
    </script>
</body>
</html>"""

    window = webview.create_window(
        title="NOVUX // ARES GRID CYBER SCRAPER",
        html=html_content,
        js_api=api,
        width=980,
        height=700,
        background_color='#000000',
        resizable=True,
        on_top=True
    )

    def _activar_ventana_frente(win):
        try:
            time.sleep(1.5)
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "NOVUX // ARES GRID CYBER SCRAPER")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            win.on_top = False
        except Exception:
            pass

    webview.start(_activar_ventana_frente, window)

if __name__ == "__main__":
    iniciar_interfaz()