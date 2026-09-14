import os
import time
import webview
from adapters.router import get_adapter
import scraper
import analyzer

class AresInteractiveAPI:
    def __init__(self):
        self.current_url = ""
        self.current_adapter = None
        self.raw_doms = []
        self.parsed_items = []
        self.start_time = 0

    def auditar_target(self, url: str):
        if not url or not url.startswith("http"):
            return {"status": "error", "message": "Protocolo inválido. Requiere http:// o https://"}

        self.current_url = url
        self.start_time = time.time()
        try:
            self.current_adapter = get_adapter(url)
            adapter_name = self.current_adapter.__class__.__name__

            dom_inicial = scraper.obtener_dom(url)
            if not dom_inicial:
                return {"status": "error", "message": "Sin respuesta del servidor objetivo."}

            items_muestra = self.current_adapter.parse_items(dom_inicial)
            total_muestra = len(items_muestra)

            if total_muestra == 0:
                return {"status": "error", "message": "Muestra inicial arrojó 0 productos. Ajustar selectores."}

            return {
                "status": "success",
                "adapter": adapter_name,
                "total_muestra": total_muestra
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ejecutar_barrido(self, pages: int):
        try:
            pages = int(pages) if int(pages) > 0 else 1
            self.raw_doms = scraper.extraer_multiples_paginas(self.current_url, pages)

            if not self.raw_doms:
                return {"status": "error", "message": "Falla de red en barrido masivo."}

            self.parsed_items = []
            for dom in self.raw_doms:
                items = self.current_adapter.parse_items(dom)
                self.parsed_items.extend(items)

            duracion = round(time.time() - self.start_time, 1)

            return {
                "status": "success",
                "total_extraido": len(self.parsed_items),
                "duracion": f"{duracion}s",
                "items": self.parsed_items
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def guardar_dataset(self, dataset_name: str):
        if not self.parsed_items:
            return {"status": "error", "message": "Sin registros en memoria."}

        try:
            nombre = dataset_name.strip() if dataset_name else "ares_dataset"
            ruta = analyzer.procesar_y_guardar_datos(self.parsed_items, nombre)

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
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 1;
            opacity: 0.65;
            pointer-events: none;
        }
        header {
            position: relative; z-index: 10;
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 24px;
            border-bottom: 1px solid #ff0000;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(6px);
        }
        .brand { display: flex; align-items: center; gap: 8px; font-weight: bold; }
        .brand-logo { border: 1px solid #ff0000; padding: 2px 6px; box-shadow: 0 0 8px #ff0000; color: #ff0000; }
        .brand-text { font-size: 11px; letter-spacing: 2px; color: #ff4444; }
        .nav-tabs { display: flex; gap: 10px; }
        .nav-btn {
            background: transparent; border: 1px solid #660000; color: #ff6666;
            padding: 5px 14px; font-size: 11px; cursor: pointer; font-family: monospace;
        }
        .nav-btn.active {
            background: #ff0000; color: #000; font-weight: bold; box-shadow: 0 0 10px #ff0000; border-color: #ff0000;
        }

        main {
            position: relative; z-index: 10;
            flex: 1; padding: 20px;
            display: flex; justify-content: center; align-items: center;
            overflow-y: auto;
        }

        /* CORE FRAME FLOTANTE CON 70% TRANSPARENCIA */
        .core-frame {
            width: 100%;
            max-width: 880px;
            background: rgba(4, 0, 0, 0.70);
            backdrop-filter: blur(4px);
            border: 2px solid #ff0000;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.35);
            padding: 18px 22px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .hud-title {
            text-align: center; font-size: 14px; letter-spacing: 3px; color: #ff0000; font-weight: bold;
        }
        .hud-sub {
            text-align: center; font-size: 9px; color: #882222; letter-spacing: 2px; margin-bottom: 4px;
        }

        .target-row { display: flex; gap: 10px; align-items: center; }
        .target-row label { font-size: 11px; color: #ff4444; white-space: nowrap; font-weight: bold; }
        .target-row input {
            flex: 1; background: rgba(0, 0, 0, 0.75); border: 1px solid #aa0000; color: #ff9999;
            padding: 8px 12px; font-family: monospace; font-size: 11px;
        }
        .target-row input:focus { outline: none; border-color: #ff0000; box-shadow: 0 0 10px #ff0000; }
        .btn-flow {
            background: #ff0000; color: #000; border: none; padding: 8px 18px;
            font-weight: bold; font-family: monospace; cursor: pointer; letter-spacing: 1px;
            box-shadow: 0 0 12px #ff0000;
        }

        .clean-check {
            font-size: 10px; color: #ff6666; display: flex; align-items: center; gap: 6px;
        }

        .console-card {
            background: rgba(2, 0, 0, 0.65);
            border: 1px solid #550000;
            display: flex; flex-direction: column; height: 180px;
            padding: 10px;
        }
        .console-header {
            display: flex; justify-content: space-between; font-size: 10px;
            color: #882222; border-bottom: 1px solid #330000; padding-bottom: 4px; margin-bottom: 6px;
        }
        .console-stream {
            flex: 1; overflow-y: auto; font-size: 11px; line-height: 1.4; color: #ff7777;
        }

        .cli-row { display: flex; gap: 8px; align-items: center; margin-top: 4px; }
        .cli-row span { font-size: 11px; color: #ff0000; font-weight: bold; }
        .cli-row input {
            flex: 1; background: rgba(0, 0, 0, 0.75); border: 1px solid #550000; color: #ff8888;
            padding: 6px 10px; font-family: monospace; font-size: 11px;
        }
        .chips-bar { display: flex; gap: 8px; font-size: 10px; margin-top: 4px; }
        .chip {
            background: rgba(20, 0, 0, 0.6); border: 1px solid #440000; color: #aa4444;
            padding: 3px 8px; cursor: pointer;
        }
        .chip:hover { border-color: #ff0000; color: #ff0000; }

        #viewDatos { display: none; width: 100%; max-width: 950px; height: 100%; flex-direction: column; }
        .table-wrap {
            flex: 1; background: rgba(5, 0, 0, 0.85); border: 1px solid #ff0000;
            overflow-y: auto; margin-top: 10px;
        }
        table { width: 100%; border-collapse: collapse; font-size: 11px; text-align: left; }
        th { background: #150000; color: #ff0000; padding: 8px; border-bottom: 1px solid #aa0000; position: sticky; top: 0; }
        td { padding: 6px 8px; border-bottom: 1px solid #220000; color: #ffcccc; }
        tr:hover td { background: rgba(255, 0, 0, 0.08); }
        .td-price { color: #00ff66; font-weight: bold; }

        footer {
            position: relative; z-index: 10;
            display: flex; justify-content: space-between; align-items: center;
            padding: 6px 24px; font-size: 10px; color: #661111;
            border-top: 1px solid #330000; background: rgba(0, 0, 0, 0.9);
        }

        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.88); z-index: 100;
            justify-content: center; align-items: center;
        }
        .modal-box {
            background: #080000; border: 2px solid #ff0000;
            box-shadow: 0 0 30px #ff0000; padding: 20px; width: 460px;
        }
        .modal-actions { display: flex; gap: 10px; margin-top: 14px; }
        .modal-actions button {
            flex: 1; padding: 8px; font-family: monospace; font-size: 11px; font-weight: bold; cursor: pointer;
        }
        .btn-yes { background: #ff0000; color: #000; border: none; }
        .btn-no { background: #220000; color: #ff5555; border: 1px solid #660000; }
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
                <div class="hud-sub">— EXTRACTOR & MINERÍA WEB EN TIEMPO REAL —</div>
            </div>

            <div class="target-row">
                <label>@ URL_OBJETIVO:</label>
                <input type="text" id="targetUrl" placeholder="https://www.amazon.com/s?k=... o https://www.temu.com/...">
                <button class="btn-flow" id="btnFlujo" onclick="iniciarReconocimiento()">[ ▶ INICIAR FLUJO ]</button>
            </div>

            <div class="clean-check">
                <input type="checkbox" id="cleanDataCheck" checked>
                <label for="cleanDataCheck">Limpiar datos automáticamente antes de cada scrap (evita contaminación)</label>
            </div>

            <div class="console-card">
                <div class="console-header">
                    <span>>_ CONSOLE_OUTPUT_STREAM | ARES-OS_DIAGNOSTICS</span>
                    <span style="cursor:pointer;" onclick="limpiarLogs()">[ LIMPIAR LOGS ]</span>
                </div>
                <div class="console-stream" id="logs">
                    [SYSTEM] Ares Grid OS v1.0 listo. Enlace de red en espera...<br>
                </div>
            </div>

            <div>
                <div class="cli-row">
                    <span>COMANDO ></span>
                    <input type="text" id="cliInput" placeholder="Escriba comando o use los accesos rápidos...">
                </div>
                <div class="chips-bar">
                    <span class="chip" onclick="ejecutarChip('ayuda')">ayuda</span>
                    <span class="chip" onclick="ejecutarChip('limpiardatos')">limpiar datos</span>
                    <span class="chip" onclick="limpiarLogs()">limpiar logs</span>
                    <span class="chip" onclick="mostrarTab('data')">datos</span>
                </div>
            </div>
        </div>

        <div id="viewDatos">
            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(10,0,0,0.85); padding:10px 16px; border:1px solid #ff0000;">
                <span style="font-size:12px; color:#ff0000; font-weight:bold;">[ MATRIZ DE REGISTROS EXTRAÍDOS ]</span>
                <button class="nav-btn" onclick="mostrarTab('console')">[ + VOLVER A CONSOLA ]</button>
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>PRODUCTO (TÍTULO)</th>
                            <th>PRECIO</th>
                            <th>ENLACE</th>
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
        <span>MODO: CONSOLA & DATOS</span>
        <span>REGISTROS: <span id="footCount">0</span></span>
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
        // MATRIX LIMPIO: NEGRO ABSOLUTO Y LETRAS NÍTIDAS
        const canvas = document.getElementById('matrixCanvas');
        const ctx = canvas.getContext('2d');
        function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
        resizeCanvas(); window.addEventListener('resize', resizeCanvas);

        const chars = "0123456789ABCDEFNOVUXARESØ1¥$";
        const fontDim = 13;
        const cols = Math.floor(window.innerWidth / fontDim);
        const drops = Array(cols).fill(1);

        function drawMatrix() {
            // Fondo negro puro con ligera persistencia
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

            document.getElementById('btnFlujo').innerText = "[ AUDITANDO... ]";
            log(`[SISTEMA] Handshake con el blanco: ${url}`, "#00ffff");

            const res = await window.pywebview.api.auditar_target(url);
            document.getElementById('btnFlujo').innerText = "[ ▶ INICIAR FLUJO ]";

            if(res.status === 'error') {
                playBeep(250, 0.25);
                log(`[ERROR] ${res.message}`, "#ff0000");
                return;
            }

            playBeep(1100, 0.1);
            log(`[ADAPTADOR ASIGNADO] ${res.adapter} | Muestra base: ${res.total_muestra} registros.`, "#00ff66");
            abrirCompuertaBarrido(res.adapter, res.total_muestra);
        }

        function abrirCompuertaBarrido(adapter, muestra) {
            document.getElementById('modalTitle').innerText = "[ COMPUERTA 1: AUTORIZAR BARRIDO ]";
            document.getElementById('modalBody').innerHTML = `
                Adaptador: <b>${adapter}</b><br>
                Muestra base confirmada: <b>${muestra}</b> registros.<br><br>
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
            cerrarModal();

            log(`[BARRIDO] Extracción sobre ${pages} página(s)...`, "#00ffff");
            const res = await window.pywebview.api.ejecutar_barrido(pages);

            if(res.status === 'error') {
                playBeep(250, 0.25);
                log(`[ERROR BARRIDO] ${res.message}`, "#ff0000");
                return;
            }

            document.getElementById('countData').innerText = res.total_extraido;
            document.getElementById('footCount').innerText = res.total_extraido;

            poblarTabla(res.items);

            playBeep(1200, 0.15);
            hablarVozRobotica(`Usuario, hemos encontrado ${res.total_extraido} registros en el sector.`);
            log(`[COMPLETADO] Flujo finalizado. ${res.total_extraido} registros en memoria.`, "#00ff66");

            abrirCompuertaDescarga(res.total_extraido);
        }

        function poblarTabla(items) {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = "";
            items.forEach(it => {
                const priceFormatted = `$${Number(it.price).toLocaleString()}`;
                tbody.innerHTML += `
                    <tr>
                        <td style="color:#ff5555;">${it.id}</td>
                        <td>${it.title.substring(0, 52)}...</td>
                        <td class="td-price">${priceFormatted}</td>
                        <td><a href="${it.url}" target="_blank" style="color:#00ffff; text-decoration:none;">[VER]</a></td>
                    </tr>
                `;
            });
        }

        function abrirCompuertaDescarga(total) {
            document.getElementById('modalTitle').innerText = "[ COMPUERTA 2: PERSISTENCIA ]";
            document.getElementById('modalBody').innerHTML = `
                Se recolectaron <b>${total}</b> registros en memoria.<br><br>
                ¿Desea normalizar y exportar este dataset al Data Lake?
            `;
            document.getElementById('modalInputs').innerHTML = `
                <div style="margin-bottom:10px;">
                    <label style="font-size:11px; color:#ff8888;">NOMBRE DEL ARCHIVO (.CSV):</label>
                    <input type="text" id="modalDatasetName" value="dataset_market" style="width:100%; background:#000; border:1px solid #aa0000; color:#fff; font-family:monospace; padding:6px;">
                </div>
            `;
            document.getElementById('modalActions').innerHTML = `
                <button class="btn-yes" onclick="confirmarGuardado()">[ PERSISTIR DATASET ]</button>
                <button class="btn-no" onclick="cerrarModal()">[ DESCARTAR ]</button>
            `;
            document.getElementById('modalControl').style.display = "flex";
        }

        async function confirmarGuardado() {
            playBeep(1000, 0.08);
            const name = document.getElementById('modalDatasetName').value;
            cerrarModal();

            log(`[DATALAKE] Guardando matriz de datos en disco...`, "#00ffff");
            const res = await window.pywebview.api.guardar_dataset(name);

            if(res.status === 'error') {
                playBeep(250, 0.25);
                log(`[ERROR GUARDADO] ${res.message}`, "#ff0000");
                return;
            }

            playBeep(1300, 0.18);
            log(`[ÉXITO FINAL] Archivo guardado en: ${res.ruta}`, "#00ff66");
        }

        function cerrarModal() {
            playBeep(400, 0.06);
            document.getElementById('modalControl').style.display = "none";
            log("[SISTEMA] Compuerta cerrada por el operador.", "#555555");
        }

        function ejecutarChip(cmd) {
            playBeep(750, 0.05);
            if(cmd === 'ayuda') {
                log("Comandos: 'ayuda', 'limpiar datos', 'limpiar logs', 'datos'.");
            } else if(cmd === 'limpiardatos') {
                document.getElementById('tableBody').innerHTML = '<tr><td colspan="4" style="text-align:center; color:#555; padding:20px;">TABLA VACÍA // SIN REGISTROS</td></tr>';
                document.getElementById('countData').innerText = "0";
                document.getElementById('footCount').innerText = "0";
                log("[SISTEMA] Buffer de datos purgado.", "#ffaa00");
            }
        }
    </script>
</body>
</html>"""

    webview.create_window(
        title="NOVUX // ARES GRID CYBER SCRAPER",
        html=html_content,
        js_api=api,
        width=960,
        height=680,
        background_color='#000000',
        resizable=True
    )
    webview.start()

if __name__ == "__main__":
    iniciar_interfaz()