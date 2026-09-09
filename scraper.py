import requests
from typing import List, Optional
from adapters.router import get_adapter

def obtener_dom(url: str) -> Optional[str]:
    """Realiza una petición HTTP simple para la inspección preliminar de un target."""
    adapter = get_adapter(url)
    headers = adapter.get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
        print(f"[ALERTA] Código de estado HTTP no exitoso: {response.status_code}")
        return None
    except Exception as e:
        print(f"[ERROR DE RED] Excepción al consultar {url}: {e}")
        return None

def extraer_multiples_paginas(base_url: str, pages: int = 1) -> List[str]:
    """
    Recorre iterativamente las páginas solicitadas utilizando la lógica 
    de paginación específica del adaptador correspondiente.
    """
    adapter = get_adapter(base_url)
    headers = adapter.get_headers()
    html_pages = []

    print(f"\n[SISTEMA] Iniciando barrido masivo de {pages} página(s) con {adapter.__class__.__name__}...")

    for page in range(1, pages + 1):
        target_url = adapter.build_pagination_url(base_url, page)
        print(f"[RED] Consultando Página {page} de {pages} -> {target_url}")

        try:
            response = requests.get(target_url, headers=headers, timeout=15)
            if response.status_code == 200:
                html_pages.append(response.text)
            else:
                print(f"[ALERTA] Página {page} respondió con código HTTP {response.status_code}")
        except Exception as e:
            print(f"[ERROR DE RED] Fallo al extraer la página {page}: {e}")

    print(f"[ÉXITO] Barrido masivo finalizado. {len(html_pages)} HTML(s) cargados en memoria.")
    return html_pages