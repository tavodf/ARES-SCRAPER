import os
import json
import socket
import ipaddress
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, 'index.html')

def is_safe_target_url(target_url: str) -> tuple[bool, str]:
    """
    Escudo Anti-SSRF NOVUX: Bloquea IPs privadas, localhost, link-local y metadata.
    """
    try:
        parsed = urlparse(target_url)
        if parsed.scheme not in ('http', 'https'):
            return False, "Esquema no permitido (solo http/https)."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Hostname no detectado."
            
        if hostname.lower() in ('localhost', '127.0.0.1', '::1', '169.254.169.254'):
            return False, "Acceso a localhost o metadata bloqueado por política de seguridad."
            
        # Resolver IP real y verificar que no sea privada
        ip_str = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip_str)
        
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
            return False, f"Destino en rango IP privado/restringido ({ip_str}) bloqueado."
            
        return True, "Destino seguro verificado."
    except Exception as e:
        return False, f"Fallo en validación de resolución de host: {e}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload')
        self.end_headers()
        try:
            with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.wfile.write(f"<h1>Error cargando ARES UI: {e}</h1>".encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
            target_url = payload.get('url', '')
            if target_url:
                safe, reason = is_safe_target_url(target_url)
                if not safe:
                    self.send_response(403)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "blocked",
                        "error": "SECURITY_POLICY_VIOLATION",
                        "detail": reason
                    }).encode('utf-8'))
                    return
        except Exception:
            pass

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.end_headers()
        self.wfile.write(b'{"status": "success", "mode": "cloud_simulation", "security_shield": "active"}')

app = handler
