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

    def _parse_amazon_price(self, raw_text: str) -> float:
        if not raw_text:
            return 0.0
        # Extraer patrón numérico monetario (ej. "COP 959,403.90", "$1.250.000", "$249.99")
        match = re.search(r'[\d.,]+', raw_text)
        if not match:
            return 0.0
        num_str = match.group(0).strip('.,')
        if not num_str:
            return 0.0
        # Si termina en .XX o ,XX (2 decimales) y tiene separadores previos
        if re.search(r'[.,]\d{2}$', num_str):
            integer_part = num_str[:-3]
            clean_int = re.sub(r'[^\d]', '', integer_part)
            return float(clean_int) if clean_int else 0.0
        # En cualquier otro caso (ej. entero con separadores de miles 1.250.000 o 959,403)
        clean_all = re.sub(r'[^\d]', '', num_str)
        return float(clean_all) if clean_all else 0.0

    def parse_items(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        seen_asins = set()

        # Selección jerárquica excluyente para no duplicar contenedor padre e hijo
        cards = soup.select('div.s-result-item[data-asin]:not([data-asin=""])')
        if not cards:
            cards = soup.select('div[data-cy="asin-faceout-container"]')

        for idx, card in enumerate(cards, 1):
            try:
                # 1. Extracción del Título
                title_elem = (
                    card.select_one('div[data-cy="title-recipe"] h2 span')
                    or card.select_one('h2 a span, h2 span, h2')
                )
                if not title_elem:
                    continue
                title = title_elem.get_text(separator=" ", strip=True)
                if not title:
                    continue

                # 2. Extracción de Enlace (URL canónica)
                link_elem = (
                    card.select_one('div[data-cy="title-recipe"] a.a-link-normal')
                    or card.select_one('h2 a.a-link-normal, a.a-link-normal.s-no-outline, a.a-link-normal')
                )
                url_path = link_elem.get('href', '') if link_elem else ""

                # 3. Extracción de ASIN en cascada (4 vectores: atributo directo, CSA padre, input oculto o URL /dp/)
                asin = (card.get("data-asin") or "").strip()

                if not asin:
                    csa_node = card if card.get("data-csa-c-item-id") else card.find_parent(attrs={"data-csa-c-item-id": True})
                    if csa_node:
                        raw_csa = csa_node.get("data-csa-c-item-id", "")
                        match = re.search(r'([A-Z0-9]{10})', raw_csa)
                        if match:
                            asin = match.group(1)

                if not asin:
                    input_asin = card.select_one('input[name*="asin"]')
                    if input_asin and input_asin.get('value'):
                        asin = input_asin['value'].strip()

                if not asin and url_path:
                    dp_match = re.search(r'/(?:dp|gp/product|offer-listing)/([A-Z0-9]{10})', url_path)
                    if dp_match:
                        asin = dp_match.group(1)

                item_id = f"AMZ-{asin}" if asin else f"AMZ-PLP-{idx:03d}"

                if asin and asin in seen_asins:
                    continue
                if asin:
                    seen_asins.add(asin)

                if url_path.startswith('/'):
                    url = f"https://www.amazon.com{url_path}"
                elif url_path.startswith('http'):
                    url = url_path
                else:
                    url = f"https://www.amazon.com/dp/{asin}" if asin else f"https://www.amazon.com/item_{idx}"

                # 4. Extracción de Precio Normalizado (Soporta Precio Principal, Atributo ATC y "Más opciones de compra")
                price_value = 0.0
                price_elem = (
                    card.select_one('div[data-cy="price-recipe"] span.a-price span.a-offscreen')
                    or card.select_one('.a-price .a-offscreen')
                )
                if price_elem:
                    price_value = self._parse_amazon_price(price_elem.get_text(strip=True))

                if price_value == 0.0:
                    atc_node = card.select_one('[data-csa-c-price-to-pay]')
                    if atc_node and atc_node.get('data-csa-c-price-to-pay'):
                        price_value = self._parse_amazon_price(atc_node.get('data-csa-c-price-to-pay', ''))

                if price_value == 0.0:
                    sec_elem = card.select_one('div[data-cy="secondary-offer-recipe"] span.a-color-base')
                    if sec_elem:
                        price_value = self._parse_amazon_price(sec_elem.get_text(strip=True))

                if price_value == 0.0:
                    whole_elem = card.select_one('.a-price-whole')
                    if whole_elem:
                        price_value = self._parse_amazon_price(whole_elem.get_text(strip=True))

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