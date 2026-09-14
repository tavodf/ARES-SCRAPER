import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from adapters.base_adapter import BaseAdapter

class AmazonAdapter(BaseAdapter):
    is_dynamic = True
    """
    Adaptador especializado para la extracción de datos en Amazon.
    Calibrado para el layout de búsqueda moderno de Amazon (Loom / puis-card).
    """

    def build_pagination_url(self, base_url: str, page: int) -> str:
        clean_url = base_url.split('#')[0]
        clean_url = re.sub(r'&page=\d+', '', clean_url)
        clean_url = re.sub(r'\?page=\d+&?', '?', clean_url)
        clean_url = clean_url.rstrip('&?')

        if page <= 1:
            return clean_url
        
        separator = '&' if '?' in clean_url else '?'
        return f"{clean_url}{separator}page={page}"

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-US,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }

    def parse_items(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []

        # Vector Estructural: Contenedores principales de tarjetas según el DOM auditado
        cards = soup.select('div[data-cy="asin-faceout-container"], div.s-result-item[data-asin]:not([data-asin=""])')

        for idx, card in enumerate(cards, 1):
            try:
                # 1. Extracción del Título
                title_elem = card.select_one('div[data-cy="title-recipe"] h2 span') or card.select_one('h2 span, h2')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                if not title:
                    continue

                # 2. Extracción de ASIN como clave primaria (ID)
                asin = ""
                # Intentar leer desde el contenedor padre o ancestros
                parent_widget = card.find_parent(attrs={"data-csa-c-item-id": True})
                if parent_widget:
                    raw_csa = parent_widget.get("data-csa-c-item-id", "")
                    match = re.search(r'([A-Z0-9]{10})', raw_csa)
                    if match:
                        asin = match.group(1)

                # Respaldo de ASIN desde formulario de compra o input oculto
                if not asin:
                    input_asin = card.select_one('input[name*="asin"]')
                    if input_asin and input_asin.get('value'):
                        asin = input_asin['value'].strip()

                item_id = f"AMZ-{asin}" if asin else f"AMZ-PLP-{idx:03d}"

                # 3. Extracción de Enlace (URL canónica)
                link_elem = card.select_one('div[data-cy="title-recipe"] a.a-link-normal') or card.select_one('a.a-link-normal')
                url_path = link_elem.get('href', '') if link_elem else ""
                
                if url_path.startswith('/'):
                    url = f"https://www.amazon.com{url_path}"
                elif url_path.startswith('http'):
                    url = url_path
                else:
                    url = f"https://www.amazon.com/dp/{asin}" if asin else f"https://www.amazon.com/item_{idx}"

                # 4. Extracción de Precio Normalizado
                price_elem = card.select_one('div[data-cy="price-recipe"] span.a-price span.a-offscreen') or card.select_one('.a-price .a-offscreen')
                if price_elem:
                    raw_price = price_elem.get_text(strip=True)
                    # Aislar solo la parte entera para evitar conflictos de comas y decimales en COP
                    clean_str = re.sub(r'[^\d]', '', raw_price.split('.')[0])
                    price_value = float(clean_str) if clean_str else 0.0
                else:
                    price_value = 0.0

                # 5. Imagen de Portada
                img_elem = card.select_one('div[data-cy="image-container"] img.s-image') or card.select_one('img.s-image')
                image_url = img_elem.get('src', '') if img_elem else ""

                products.append({
                    "id": item_id,
                    "title": title,
                    "price": price_value,
                    "url": url,
                    "image_url": image_url,
                    "category": "amazon_adapter",
                    "timestamp": "Extraído por Ares Scraper"
                })
            except Exception:
                continue

        return products