import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from adapters.base_adapter import BaseAdapter

class AmazonAdapter(BaseAdapter):
    """
    Adaptador especializado para la extracción de datos en Amazon.
    Maneja paginación por parámetro &page=N y selectores de SSR estables.
    """

    def build_pagination_url(self, base_url: str, page: int) -> str:
        # 1. Limpiar fragmentos y parámetros de página previos si existen
        clean_url = base_url.split('#')[0]
        clean_url = re.sub(r'&page=\d+', '', clean_url)
        clean_url = re.sub(r'\?page=\d+&?', '?', clean_url)
        clean_url = clean_url.rstrip('&?')

        if page <= 1:
            return clean_url
        
        # 2. Agregar parámetro de paginación según la estructura de la URL base
        separator = '&' if '?' in clean_url else '?'
        return f"{clean_url}{separator}page={page}"

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "es-US,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

    def parse_items(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []

        # Selector robusto para tarjetas de resultados en Amazon (SSR)
        cards = soup.select('div.s-result-item[data-asin]:not([data-asin=""])')

        for idx, card in enumerate(cards, 1):
            try:
                # Extracción de Título
                title_elem = card.select_one('h2 a span, .a-text-normal')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                # Extracción de Enlace
                link_elem = card.select_one('h2 a.a-link-normal')
                url_path = link_elem.get('href', '') if link_elem else ""
                url = f"https://www.amazon.com{url_path}" if url_path.startswith('/') else url_path

                # Extracción y Normalización de Precio
                price_elem = card.select_one('.a-price .a-offscreen')
                if not price_elem:
                    continue
                raw_price = price_elem.get_text(strip=True)
                
                # Limpiar formato monetario (remover símbolos de moneda, comas de miles)
                clean_price_str = re.sub(r'[^\d.]', '', raw_price)
                price_value = float(clean_price_str) if clean_price_str else 0.0

                products.append({
                    "id": f"AMZ-{idx:03d}",
                    "title": title,
                    "price": price_value,
                    "url": url,
                    "category": "amazon_adapter",
                    "timestamp": "Extraído por Ares Scraper"
                })
            except Exception as e:
                # Tolerancia a fallos por tarjeta individual
                continue

        return products