# ============================================================================
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
    data = request.json or {}
    url = data.get('url', '')
    clean_before = data.get('clean_before', True)
    res = api_instance.auditar_target(url, clean_before)
    response.content_type = 'application/json'
    return json.dumps(res)

@app.route('/api/barrido', method=['POST'])
def barrido():
    data = request.json or {}
    pages = data.get('pages', 1)
    clean_before = data.get('clean_before', True)
    res = api_instance.ejecutar_barrido(pages, clean_before)
    response.content_type = 'application/json'
    return json.dumps(res)

@app.route('/api/guardar', method=['POST'])
def guardar():
    data = request.json or {}
    name = data.get('dataset_name', 'ares_dataset')
    res = api_instance.guardar_dataset(name)
    response.content_type = 'application/json'
    return json.dumps(res)

@app.route('/api/export_json', method=['POST'])
def export_json():
    data = request.json or {}
    name = data.get('dataset_name', 'ares_dataset')
    res = api_instance.exportar_json(name)
    response.content_type = 'application/json'
    return json.dumps(res)

if __name__ == '__main__':
    print('===============================================================================')
    print('  [ARES GRID] Servidor Web Activo en http://localhost:5000')
    print('===============================================================================')
    run(app, host='127.0.0.1', port=5000, quiet=True)
