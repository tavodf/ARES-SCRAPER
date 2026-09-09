import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from adapters.base_adapter import BaseAdapter

class MercadoLibreAdapter(BaseAdapter):
    """
    Adaptador especializado para la extracción de datos en MercadoLibre Colombia.
    Maneja paginación por offset (_Desde_X) y limpieza de URLs con fragmentos.
    """

    def build_pagination_url(self, base_url: str, page: int) -> str:
        # 1. Limpiar fragmentos (#D[...]) y parámetros de paginación previos si existen
        clean_url = base_url.split('#')[0]
        clean_url = re.sub(r'_Desde_\d+', '', clean_url)
        clean_url = clean_url.rstrip('/')

        if page <= 1:
            return clean_url
        
        # 2. Calcular el offset de MercadoLibre (Página 1 = 1, Página 2 = 51, Página 3 = 101, etc.)
        offset = ((page - 1) * 50) + 1
        return f"{clean_url}_Desde_{offset}"

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "es-CO,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.mercadolibre.com.co/"
        }

    def parse_items(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []

        # Selector robusto para tarjetas de resultados en MercadoLibre
        cards = soup.select('.ui-search-result, .poly-card')

        for idx, card in enumerate(cards, 1):
            try:
                # Extracción de Título
                title_elem = card.select_one('.ui-search-item__title, .poly-component__title')
                title = title_elem.get_text(strip=True) if title_elem else "Sin título"

                # Extracción de Enlace
                link_elem = card.select_one('a.ui-search-link, a.poly-component__title')
                url = link_elem.get('href', '') if link_elem else ""

                # Extracción y Normalización de Precio
                price_elem = card.select_one('.andes-money-amount__fraction, .poly-price__current .andes-money-amount__fraction')
                raw_price = price_elem.get_text(strip=True) if price_elem else "0"
                
                # Limpiar formato monetario (remover puntos o comas de miles)
                clean_price_str = re.sub(r'[^\d]', '', raw_price)
                price_value = float(clean_price_str) if clean_price_str else 0.0

                products.append({
                    "id": f"MELI-{idx:03d}",
                    "title": title,
                    "price": price_value,
                    "url": url,
                    "category": "mercadolibre_adapter",
                    "timestamp": "Extraído por Ares Scraper"
                })
            except Exception as e:
                # Tolerancia a fallos por tarjeta individual
                continue

        return products