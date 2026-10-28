import requests
from typing import List, Optional
from adapters.router import get_adapter
from scraper_selenium import obtener_dom_dinamico, obtener_multiples_doms_dinamicos

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

def extraer_multiples_paginas(base_url: str, pages: int = 1, dom_inicial: Optional[str] = None) -> List[str]:
    """Recorre iterativamente las páginas delegando al motor correspondiente y reutilizando la Página 1 si ya fue auditada."""
    adapter = get_adapter(base_url)
    html_pages: List[str] = []

    print(f"\n[SISTEMA] Iniciando barrido masivo de {pages} página(s) con {adapter.__class__.__name__}...")

    start_page = 1
    if dom_inicial:
        print("[CACHE] Reutilizando DOM auditado de Página 1 desde memoria activa (0 pérdidas).")
        html_pages.append(dom_inicial)
        start_page = 2

    if start_page > pages:
        print(f"[ÉXITO] Barrido masivo finalizado. {len(html_pages)} HTML(s) cargados en memoria.")
        return html_pages

    remaining_urls = [adapter.build_pagination_url(base_url, page) for page in range(start_page, pages + 1)]

    if adapter.is_dynamic:
        nuevos_doms = obtener_multiples_doms_dinamicos(remaining_urls)
        html_pages.extend(nuevos_doms)
    else:
        headers = adapter.get_headers()
        for idx, target_url in enumerate(remaining_urls, start=start_page):
            print(f"[RED] Consultando Página {idx} de {pages} -> {target_url}")
            try:
                response = requests.get(target_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    html_pages.append(response.text)
                else:
                    print(f"[ALERTA] Página {idx} respondió con código HTTP {response.status_code}")
            except Exception as e:
                print(f"[ERROR DE RED] Fallo al extraer la página {idx}: {e}")

    print(f"[ÉXITO] Barrido masivo finalizado. {len(html_pages)} HTML(s) cargados en memoria.")
    return html_pages