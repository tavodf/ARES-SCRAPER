import os
import re

source_path = os.path.join(os.path.dirname(__file__), 'desktop_app.py')
dest_html_path = os.path.join(os.path.dirname(__file__), 'index.html')
dest_vercel_path = os.path.join(os.path.dirname(__file__), 'vercel.json')

with open(source_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Extraer HTML puro entre html_content = """ y """
start_token = 'html_content = """'
end_token = '"""\n\n    window = webview.create_window'

s_idx = code.find(start_token)
if s_idx == -1:
    raise ValueError("start_token no encontrado")
s_idx += len(start_token)

e_idx = code.find(end_token, s_idx)
if e_idx == -1:
    # Buscar alternativa
    end_token = '</html>"""'
    e_idx = code.find(end_token, s_idx) + len('</html>')

raw_html = code[s_idx:e_idx].strip()
if raw_html.startswith('"""'):
    raw_html = raw_html[3:].strip()
if raw_html.endswith('"""'):
    raw_html = raw_html[:-3].strip()

# Enriquecer index.html con:
# 1) Puente Universal Inteligente: Si no hay servidor local, corre el motor de simulación interactiva
# 2) Descarga directa de CSV/JSON en el navegador (Blob)
# 3) Lead Lock Anti-Theft de 45 segundos con modal de alta conversión a WhatsApp de Gustavo De La Rosa

universal_engine_script = """
    <script>
        // ====================================================================
        // NOVUX ARES // MOTOR UNIVERSAL HYBRID (LOCAL PYTHON + CLOUD CLIENT)
        // ====================================================================
        const WHATSAPP_PHONE = '573196300410';
        const WHATSAPP_MSG = encodeURIComponent('Hola Gustavo, probé la demo interactiva de NOVUX ARES Cyber Scraper en novuxops.com y me interesa implementar este motor de extracción masiva en los servidores de mi empresa.');

        // Dataset táctico para demostración en vivo (E-commerce Benchmark)
        const MOCK_DATASET = [
            { id: "MCO-94812", title: "Café Especial Molido Juan Valdez Volcán 500g", price: 32000, url: "https://tienda.juanvaldez.com/cafe-volcan-500g" },
            { id: "MCO-83921", title: "Café Gourmet Tostado Sello Rojo 250g", price: 21000, url: "https://articulo.mercadolibre.com.co/MCO-83921" },
            { id: "MCO-74812", title: "Café Águila Roja Suave Molido 500g", price: 18500, url: "https://www.exito.com/cafe-molido-aguila-roja" },
            { id: "MCO-63219", title: "Café Colcafé Clásico Frasco Instantáneo 170g", price: 16200, url: "https://www.alkosto.com/cafe-colcafe-170g" },
            { id: "MCO-51902", title: "Café Matiz Ámbar Molido Premium 340g", price: 28900, url: "https://tienda.matiz.com/cafe-ambar" },
            { id: "MCO-40918", title: "Café Quindío Origen Especial Caturra 500g", price: 36500, url: "https://cafequindio.com/origen-especial" },
            { id: "MCO-33821", title: "Monitor Gamer ASUS TUF Gaming 27 Pulgadas IPS 165Hz", price: 1250000, url: "https://articulo.mercadolibre.com.co/MCO-33821" },
            { id: "MCO-22910", title: "Portátil Lenovo ThinkPad E14 Intel Core i7 16GB RAM 512GB SSD", price: 3850000, url: "https://www.lenovo.com/co/thinkpad-e14" },
            { id: "MCO-11827", title: "Teclado Mecánico RGB Redragon Kumara Switch Blue", price: 189000, url: "https://www.alkosto.com/teclado-redragon" },
            { id: "MCO-99214", title: "Mouse Inalámbrico Logitech MX Master 3S Ergonómico", price: 420000, url: "https://www.logitech.com/mx-master-3s" },
            { id: "MCO-88123", title: "Apple iPhone 15 Pro Max 256GB Titanio Natural", price: 5490000, url: "https://www.apple.com/co/iphone-15-pro" },
            { id: "MCO-77291", title: "Samsung Galaxy S24 Ultra 512GB Gris Titanio con Galaxy AI", price: 5290000, url: "https://www.samsung.com/co/galaxy-s24" }
        ];

        // Anti-Theft / Lead Lock Timer (45 Segundos)
        let aresTimeLeft = 45;
        let aresLocked = false;

        setInterval(() => {
            if (aresLocked) return;
            aresTimeLeft--;
            const timerEl = document.getElementById('aresTimerBadge');
            if (timerEl) {
                const s = aresTimeLeft < 10 ? `0${aresTimeLeft}` : aresTimeLeft;
                timerEl.innerText = `PRUEBA TÁCTICA: 00:${s}s`;
            }
            if (aresTimeLeft <= 0) {
                aresLocked = true;
                mostrarLeadLock();
            }
        }, 1000);

        function mostrarLeadLock() {
            playBeep(300, 0.3);
            const modal = document.getElementById('modalLeadLock');
            if (modal) modal.style.display = 'flex';
        }

        function reiniciarPrueba() {
            aresTimeLeft = 45;
            aresLocked = false;
            const modal = document.getElementById('modalLeadLock');
            if (modal) modal.style.display = 'none';
            log("[SEGURIDAD] Prueba reiniciada por 45 segundos adicionales.", "#00ff66");
        }

        function descargarArchivoCliente(contenido, nombreArchivo, mimeType) {
            const blob = new Blob([contenido], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = nombreArchivo;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        const aresApi = (window.pywebview && window.pywebview.api) ? window.pywebview.api : {
            obtener_logs_pendientes: async () => {
                try {
                    const r = await fetch('/api/logs');
                    if (r.ok) return await r.json();
                } catch(e) {}
                return [];
            },
            limpiar_memoria: async () => {
                try {
                    const r = await fetch('/api/limpiar', { method: 'POST' });
                    if (r.ok) return await r.json();
                } catch(e) {}
                return { status: 'success' };
            },
            auditar_target: async (url, cleanBefore) => {
                try {
                    const r = await fetch('/api/auditar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, clean_before: cleanBefore })
                    });
                    if (r.ok) return await r.json();
                } catch(e) {}

                // Fallback de demostración reactiva en la nube (Vercel)
                await new Promise(r => setTimeout(r, 600));
                let domain = "target_general";
                try { domain = new URL(url).hostname; } catch(_) {}
                return {
                    status: 'success',
                    adapter: `StealthAdapter [${domain}]`,
                    total_muestra: MOCK_DATASET.length,
                    ruido_muestra: 14
                };
            },
            ejecutar_barrido: async (pages, cleanBefore) => {
                try {
                    const r = await fetch('/api/barrido', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ pages, clean_before: cleanBefore })
                    });
                    if (r.ok) return await r.json();
                } catch(e) {}

                // Fallback interactivo en Vercel
                await new Promise(r => setTimeout(r, 800));
                const items = [...MOCK_DATASET];
                const precios = items.map(i => i.price);
                const avg = Math.round(precios.reduce((a, b) => a + b, 0) / precios.length);
                const min = Math.min(...precios);
                const max = Math.max(...precios);

                return {
                    status: 'success',
                    total_extraido: items.length,
                    ruido_purgado: 14,
                    precio_promedio: avg,
                    precio_min: min,
                    precio_max: max,
                    duracion: "1.4s",
                    items: items
                };
            },
            guardar_dataset: async (name) => {
                try {
                    const r = await fetch('/api/guardar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ dataset_name: name })
                    });
                    if (r.ok) return await r.json();
                } catch(e) {}

                // Exportación nativa CSV directa en el navegador
                let csv = "ID,TITULO,PRECIO,URL\\n";
                currentItems.forEach(it => {
                    csv += `"${it.id}","${String(it.title).replace(/"/g, '""')}",${it.price},"${it.url}"\\n`;
                });
                descargarArchivoCliente(csv, `${name || 'ares_dataset'}.csv`, 'text/csv;charset=utf-8;');
                return { status: 'success', total_guardado: currentItems.length, ruta: `Descargas / ${name || 'ares_dataset'}.csv` };
            },
            exportar_json: async (name) => {
                try {
                    const r = await fetch('/api/export_json', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ dataset_name: name })
                    });
                    if (r.ok) return await r.json();
                } catch(e) {}

                // Exportación nativa JSON en el navegador
                const jsonStr = JSON.stringify(currentItems, null, 2);
                descargarArchivoCliente(jsonStr, `${name || 'ares_dataset'}.json`, 'application/json');
                return { status: 'success', total_guardado: currentItems.length, ruta: `Descargas / ${name || 'ares_dataset'}.json` };
            }
        };
    </script>
"""

# Modal Lead Lock HTML
lead_lock_modal_html = """
    <!-- HUD PERMANENTE TEMPORAL DE PRUEBA CORPORATIVA -->
    <div id="aresTimerBadge" style="position: fixed; top: 12px; right: 20px; z-index: 50; background: rgba(10, 0, 0, 0.85); border: 1px solid #ffaa00; color: #ffcc00; font-family: 'Consolas', monospace; font-size: 11px; padding: 4px 12px; border-radius: 20px; box-shadow: 0 0 15px rgba(255, 170, 0, 0.4); display: flex; align-items: center; gap: 6px;">
        PRUEBA TÁCTICA: 00:45s
    </div>

    <!-- MODAL TAKEOVER ANTI-THEFT // LEAD LOCK (45 SEGUNDOS) -->
    <div id="modalLeadLock" style="display: none; position: fixed; inset: 0; z-index: 200; background: rgba(0, 0, 0, 0.94); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); justify-content: center; align-items: center; padding: 16px;">
        <div style="background: #080000; border: 2px solid #ff0000; box-shadow: 0 0 60px rgba(255, 0, 0, 0.5); padding: clamp(20px, 4vh, 36px); width: min(94vw, 560px); text-align: center; font-family: 'Consolas', monospace; color: #fff;">
            <div style="font-size: 40px; margin-bottom: 12px;">🛡️</div>
            <div style="font-size: 11px; letter-spacing: 3px; color: #ff5555; text-transform: uppercase; margin-bottom: 8px;">
                [ DEMOSTRACIÓN TÁCTICA FINALIZADA (45s) ]
            </div>
            <h2 style="font-size: clamp(16px, 1.8vw, 22px); color: #fff; margin-bottom: 12px; font-weight: bold; letter-spacing: 1px;">
                ¿Necesitas extraer datos a escala industrial sin bloqueos WAF?
            </h2>
            <p style="font-size: 12px; color: #cccccc; line-height: 1.6; margin-bottom: 24px;">
                Has probado la muestra operativa de <b>NOVUX ARES GRID</b>. Para proteger nuestros algoritmos propietarios de bypass Layer 7 y desplegar este motor con red de proxies rotativos ilimitados en tu propia infraestructura:
            </p>
            <div style="display: flex; flex-direction: column; gap: 12px;">
                <a href="https://wa.me/573196300410?text=Hola%20Gustavo%2C%20vi%20la%20demostraci%C3%B3n%20de%20ARES%20GRID%20Cyber%20Scraper%20en%20novuxops.com%20y%20me%20interesa%20implementar%20el%20extractor%20masivo%20en%20mi%20empresa." target="_blank" rel="noopener noreferrer" style="background: linear-gradient(135deg, #10b981, #059669); color: #fff; text-decoration: none; padding: 12px 18px; font-weight: bold; font-size: 13px; border-radius: 4px; box-shadow: 0 0 25px rgba(16, 185, 129, 0.5); display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer;">
                    <span>📲 Contactar a Gustavo De La Rosa (WhatsApp)</span>
                </a>
                <div style="display: flex; gap: 10px;">
                    <a href="https://www.novuxops.com" target="_blank" rel="noopener noreferrer" style="flex: 1; background: #121216; border: 1px solid #444; color: #ffcc00; text-decoration: none; padding: 10px; font-size: 11px; display: flex; align-items: center; justify-content: center; gap: 6px;">
                        <span>🌐 novuxops.com</span>
                    </a>
                    <button onclick="reiniciarPrueba()" style="flex: 1; background: #220000; border: 1px solid #aa0000; color: #ff8888; padding: 10px; font-size: 11px; cursor: pointer; font-family: monospace;">
                        <span>🔄 Probar 45s Más</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
"""

# Inyectar el script bridge y el modal en raw_html
html_final = raw_html
# Reemplazar window.pywebview.api por aresApi
html_final = html_final.replace('window.pywebview.api', 'aresApi')

# Inyectar bridge antes del script principal
html_final = html_final.replace('<script>', universal_engine_script + '\n    <script>', 1)

# Inyectar modal antes del cierre del body
html_final = html_final.replace('</body>', lead_lock_modal_html + '\n</body>')

with open(dest_html_path, 'w', encoding='utf-8') as f:
    f.write(html_final)

# Crear vercel.json en ARES SCRAPER
vercel_config = """{
  "cleanUrls": true,
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
"""

with open(dest_vercel_path, 'w', encoding='utf-8') as f:
    f.write(vercel_config)

print("ARES index.html y vercel.json generados con éxito!")
