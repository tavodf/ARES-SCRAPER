import os
import sys

source_path = os.path.join(os.path.dirname(__file__), 'desktop_app.py')
dest_path = os.path.join(os.path.dirname(__file__), 'web_server.py')

with open(source_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extraer HTML puro (desde línea 247 hasta 1030)
html_lines = lines[247:1031]
html_raw = ''.join(html_lines)

# Limpiar encabezado y pie de string
first_line_prefix = 'html_content = """'
if html_raw.startswith(first_line_prefix):
    html_raw = html_raw[len(first_line_prefix):]
if html_raw.endswith('"""\n') or html_raw.endswith('"""'):
    html_raw = html_raw[:-3].rstrip()

api_bridge = """
    <script>
        // Puente API Universal: HTTP REST para navegador local (localhost:5000) o pywebview nativo
        const aresApi = (window.pywebview && window.pywebview.api) ? window.pywebview.api : {
            obtener_logs_pendientes: async () => {
                try {
                    const r = await fetch('/api/logs');
                    return await r.json();
                } catch(e) { return []; }
            },
            limpiar_memoria: async () => {
                const r = await fetch('/api/limpiar', { method: 'POST' });
                return await r.json();
            },
            auditar_target: async (url, cleanBefore) => {
                const r = await fetch('/api/auditar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, clean_before: cleanBefore })
                });
                return await r.json();
            },
            ejecutar_barrido: async (pages, cleanBefore) => {
                const r = await fetch('/api/barrido', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pages: pages, clean_before: cleanBefore })
                });
                return await r.json();
            },
            guardar_dataset: async (name) => {
                const r = await fetch('/api/guardar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dataset_name: name })
                });
                return await r.json();
            },
            exportar_json: async (name) => {
                const r = await fetch('/api/export_json', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dataset_name: name })
                });
                return await r.json();
            }
        };
    </script>
"""

# Inyectar puente
html_patched = html_raw.replace('<script>', api_bridge + '\n    <script>', 1)
html_patched = html_patched.replace('window.pywebview.api', 'aresApi')

# Guardar index.html para servicio estático
html_file_path = os.path.join(os.path.dirname(__file__), 'index.html')
with open(html_file_path, 'w', encoding='utf-8') as f:
    f.write(html_patched)

server_code = f'''# ============================================================================
# NOVUX ARES GRID // SERVIDOR WEB LOCAL (PORT 5000)
# Estándar: NVX-ENG-CORE | novuxops.com
# ============================================================================
import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ['ARES_DEFAULT_DESKTOP'] = '1'

from bottle import Bottle, request, response, run
from desktop_app import AresInteractiveAPI

app = Bottle()
api_instance = AresInteractiveAPI()

HTML_PATH = os.path.join(BASE_DIR, 'index.html')

@app.route('/')
def index():
    response.content_type = 'text/html; charset=utf-8'
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/logs', method=['GET'])
def get_logs():
    response.content_type = 'application/json'
    return json.dumps(api_instance.obtener_logs_pendientes())

@app.route('/api/limpiar', method=['POST'])
def limpiar():
    response.content_type = 'application/json'
    return json.dumps(api_instance.limpiar_memoria())

@app.route('/api/auditar', method=['POST'])
def auditar():
    data = request.json or {{}}
    url = data.get('url', '')
    clean_before = data.get('clean_before', True)
    res = api_instance.auditar_target(url, clean_before)
    response.content_type = 'application/json'
    return json.dumps(res)

@app.route('/api/barrido', method=['POST'])
def barrido():
    data = request.json or {{}}
    pages = data.get('pages', 1)
    clean_before = data.get('clean_before', True)
    res = api_instance.ejecutar_barrido(pages, clean_before)
    response.content_type = 'application/json'
    return json.dumps(res)

@app.route('/api/guardar', method=['POST'])
def guardar():
    data = request.json or {{}}
    name = data.get('dataset_name', 'ares_dataset')
    res = api_instance.guardar_dataset(name)
    response.content_type = 'application/json'
    return json.dumps(res)

@app.route('/api/export_json', method=['POST'])
def export_json():
    data = request.json or {{}}
    name = data.get('dataset_name', 'ares_dataset')
    res = api_instance.exportar_json(name)
    response.content_type = 'application/json'
    return json.dumps(res)

if __name__ == '__main__':
    print('===============================================================================')
    print('  [ARES GRID] Servidor Web Activo en http://localhost:5000')
    print('===============================================================================')
    run(app, host='127.0.0.1', port=5000, quiet=True)
'''

with open(dest_path, 'w', encoding='utf-8') as f:
    f.write(server_code)

print("web_server.py y index.html generados exitosamente.")
