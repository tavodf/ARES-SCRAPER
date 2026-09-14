import requests
from typing import List, Optional
from adapters.router import get_adapter
from scraper_selenium import obtener_dom_dinamico

def obtener_dom(url: str) -> Optional[str]:
    """Realiza una petición preliminar respetando la naturaleza dinámica o estática del adaptador."""
    adapter = get_adapter(url)
    
    if adapter.is_dynamic:
        print(f"[SISTEMA] Compuerta activa: Desplegando motor dinámico ({adapter.__class__.__name__})...")
        return obtener_dom_dinamico(url)
        
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
    """Recorre iterativamente las páginas delegando al motor correspondiente."""
    adapter = get_adapter(base_url)
    html_pages = []

    print(f"\n[SISTEMA] Iniciando barrido masivo de {pages} página(s) con {adapter.__class__.__name__}...")

    for page in range(1, pages + 1):
        target_url = adapter.build_pagination_url(base_url, page)
        print(f"[RED] Consultando Página {page} de {pages} -> {target_url}")

        if adapter.is_dynamic:
            dom = obtener_dom_dinamico(target_url)
            if dom:
                html_pages.append(dom)
            else:
                print(f"[ALERTA] Falla en extracción dinámica para la página {page}")
        else:
            headers = adapter.get_headers()
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