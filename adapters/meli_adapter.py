import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from adapters.base_adapter import BaseAdapter

class MercadoLibreAdapter(BaseAdapter):
    """
    Adaptador maestro para MercadoLibre Colombia.
    Detecta automáticamente la tipología de la URL:
      - PLP (Páginas de Listado / Búsqueda / Clasificados)
      - PDP (Páginas de Detalle de Producto Individual)
    """

    def build_pagination_url(self, base_url: str, page: int) -> str:
        # Si es una página de detalle individual (PDP), no aplica paginación
        if '/p/' in base_url or '/articulo/' in base_url:
            return base_url

        clean_url = base_url.split('#')[0]
        clean_url = re.sub(r'_Desde_\d+', '', clean_url)
        clean_url = clean_url.rstrip('/')

        if page <= 1:
            return clean_url
        
        offset = ((page - 1) * 50) + 1
        return f"{clean_url}_Desde_{offset}"

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Referer": "https://www.mercadolibre.com.co/",
            "Upgrade-Insecure-Requests": "1"
        }

    def parse_items(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Enruta el HTML hacia el parser correcto dependiendo de si es un Listado o un Producto Único.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Detectar si estamos en una Ficha de Detalle de Producto (PDP) de forma limpia
        pdp_container = soup.select_one('.ui-pdp-container, h1.ui-pdp-title')
        if pdp_container:
            return self._parse_pdp(soup)
        
        # Por defecto, procesar como Página de Listado / Búsqueda (PLP)
        return self._parse_plp(soup)

    def _parse_plp(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parser avanzado para Páginas de Listado, Búsqueda y Clasificados (Vehículos/Retail/Showrooms)."""
        products = []
        
        # Selectores ampliados: incluye contenedores estándar, grillas poly y clasificados/showroom
        cards = soup.select(
            'li.ui-search-layout__item, '
            'div.poly-card, '
            'div.ui-search-result, '
            'div.andes-card, '
            'div.ui-result-row, '
            'li.results-item, '
            'div[class*="showroom"], '
            'div[class*="brand-wrapper"], '
            'div[class*="poly-component"]'
        )

        for idx, card in enumerate(cards, 1):
            try:
                # Título
                title_elem = card.select_one('.ui-search-item__title, .poly-component__title, h2, a.ui-search-link, div[class*="title"]')
                title = title_elem.get('title') or title_elem.get_text(strip=True) if title_elem else "Sin título"

                # Enlace
                link_elem = card.select_one('a.ui-search-link, a.poly-component__title, a')
                url = link_elem.get('href', '') if link_elem else ""

                # Precio
                price_elem = card.select_one('.andes-money-amount__fraction, .poly-price__current .andes-money-amount__fraction, .price-tag-fraction, span[class*="fraction"]')
                raw_price = price_elem.get_text(strip=True) if price_elem else "0"
                
                clean_price_str = re.sub(r'[^\d]', '', raw_price)
                price_value = float(clean_price_str) if clean_price_str else 0.0

                # Imagen
                img_elem = card.select_one('.ui-search-result-image__element, .poly-card__portada img, img')
                image_url = img_elem.get('src') or img_elem.get('data-src', '') if img_elem else ""

                # Filtrado de seguridad
                if title == "Sin título" or price_value == 0.0:
                    continue

                products.append({
                    "id": f"MELI-PLP-{idx:03d}",
                    "title": title,
                    "price": price_value,
                    "url": url,
                    "image_url": image_url,
                    "category": "mercadolibre_plp",
                    "timestamp": "Extraído por Ares Scraper"
                })
            except Exception:
                continue

        return products

    def _parse_pdp(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parser especializado para Fichas Individuales de Producto (PDP)."""
        try:
            # Título principal del producto
            title_elem = soup.select_one('h1.ui-pdp-title')
            title = title_elem.get_text(strip=True) if title_elem else "Producto Individual Sin Título"

            # Precio principal (fracción)
            price_elem = soup.select_one('.andes-money-amount__fraction')
            raw_price = price_elem.get_text(strip=True) if price_elem else "0"
            clean_price_str = re.sub(r'[^\d]', '', raw_price)
            price_value = float(clean_price_str) if clean_price_str else 0.0

            # Imagen principal de la galería
            img_elem = soup.select_one('.ui-pdp-gallery__figure img, img.ui-pdp-image')
            image_url = img_elem.get('src') or img_elem.get('data-zoom', '') if img_elem else ""

            # URL de referencia (en PDP devolvemos la misma o vacía, pero estructurada)
            return [{
                "id": "MELI-PDP-001",
                "title": title,
                "price": price_value,
                "url": "Ficha Individual PDP",
                "image_url": image_url,
                "category": "mercadolibre_pdp",
                "timestamp": "Extraído por Ares Scraper"
            }]
        except Exception as e:
            print(f"[ALERTA] Error al parsear PDP individual: {e}")
            return []