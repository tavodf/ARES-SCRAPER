import os
from http.server import BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, 'index.html')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        try:
            with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.wfile.write(f"<h1>Error cargando ARES UI: {e}</h1>".encode('utf-8'))

    def do_POST(self):
        # Responder OK a cualquier invocación API en demo cloud
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "success", "mode": "cloud_simulation"}')

app = handler
