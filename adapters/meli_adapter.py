import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from adapters.base_adapter import BaseAdapter

class MercadoLibreAdapter(BaseAdapter):
    is_dynamic = True
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
        seen_keys = set()

        # Selección jerárquica excluyente para evitar multiplicar 5x el mismo producto por nodos hijos anidados
        cards = soup.select('li.ui-search-layout__item')
        if not cards:
            cards = soup.select('div.ui-search-result, li.results-item, div.ui-result-row')
        if not cards:
            cards = soup.select('div.poly-card, div.andes-card')
        if not cards:
            cards = soup.select('div[class*="showroom"], div[class*="brand-wrapper"]')

        for idx, card in enumerate(cards, 1):
            try:
                # 1. Título principal
                title_elem = card.select_one(
                    '.poly-component__title, .ui-search-item__title, h2 a, h2, a.ui-search-link, div[class*="title"]'
                )
                title = (title_elem.get('title') or title_elem.get_text(strip=True)) if title_elem else "Sin título"

                # Enriquecer con atributos de clasificados/vehículos (Año | Kilometraje | Ubicación) si existen
                attrs_elems = card.select('.poly-attributes_list__item, .ui-search-card-attributes__attribute')
                if attrs_elems:
                    attrs_text = " | ".join(a.get_text(strip=True) for a in attrs_elems if a.get_text(strip=True))
                    if attrs_text and attrs_text not in title:
                        title = f"{title} ({attrs_text})"

                # 2. Enlace y Clave Primaria Real (MCO-XXXX)
                link_elem = card.select_one('a.poly-component__title, a.ui-search-link, h2 a, a[href]')
                raw_url = link_elem.get('href', '') if link_elem else ""
                clean_url = raw_url.split('#')[0].strip() if raw_url else ""

                mco_match = re.search(r'(MCO-?\d+)', clean_url or raw_url, re.IGNORECASE)
                if mco_match:
                    clean_mco = mco_match.group(1).upper().replace('-', '')
                    item_id = f"MELI-{clean_mco}"
                else:
                    item_id = f"MELI-PLP-{idx:03d}"

                # 3. Precio (aislando el contenedor principal de precio actual, ignorando cuotas o precios tachados)
                price_elem = (
                    card.select_one('.poly-price__current .andes-money-amount__fraction')
                    or card.select_one('.ui-search-price__second-line .andes-money-amount__fraction')
                    or card.select_one('.andes-money-amount__fraction, .price-tag-fraction, span[class*="fraction"]')
                )
                raw_price = price_elem.get_text(strip=True) if price_elem else "0"
                clean_price_str = re.sub(r'[^\d]', '', raw_price)
                price_value = float(clean_price_str) if clean_price_str else 0.0

                # 4. Imagen (soportando lazy-loading data-src)
                img_elem = card.select_one('.poly-card__portada img, .ui-search-result-image__element, img')
                image_url = (img_elem.get('data-src') or img_elem.get('src', '')) if img_elem else ""
                if image_url.startswith('data:image') and img_elem and img_elem.get('data-src'):
                    image_url = img_elem.get('data-src', '')

                # Filtrado de seguridad
                if title == "Sin título" or price_value == 0.0:
                    continue

                # Clave de unicidad por tarjeta real
                dedup_key = clean_url if clean_url else f"{item_id}|{title}|{price_value}"
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                products.append({
                    "id": item_id,
                    "title": title,
                    "price": price_value,
                    "url": clean_url or raw_url or f"https://listado.mercadolibre.com.co/{item_id}",
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
            title_elem = soup.select_one('h1.ui-pdp-title')
            title = title_elem.get_text(strip=True) if title_elem else "Producto Individual Sin Título"

            price_elem = (
                soup.select_one('.ui-pdp-price__second-line .andes-money-amount__fraction')
                or soup.select_one('.andes-money-amount__fraction')
            )
            raw_price = price_elem.get_text(strip=True) if price_elem else "0"
            clean_price_str = re.sub(r'[^\d]', '', raw_price)
            price_value = float(clean_price_str) if clean_price_str else 0.0

            img_elem = soup.select_one('.ui-pdp-gallery__figure img, img.ui-pdp-image')
            image_url = (img_elem.get('data-zoom') or img_elem.get('src', '')) if img_elem else ""

            canonical_elem = soup.select_one('link[rel="canonical"]')
            pdp_url = canonical_elem.get('href', 'Ficha Individual PDP') if canonical_elem else "Ficha Individual PDP"

            return [{
                "id": "MELI-PDP-001",
                "title": title,
                "price": price_value,
                "url": pdp_url,
                "image_url": image_url,
                "category": "mercadolibre_pdp",
                "timestamp": "Extraído por Ares Scraper"
            }]
        except Exception as e:
            print(f"[ALERTA] Error al parsear PDP individual: {e}")
            return []