from bs4 import BeautifulSoup
from typing import List, Dict, Any
from adapters.base_adapter import BaseAdapter
import re

class TemuAdapter(BaseAdapter):
    is_dynamic = True
    
    """Adaptador de extracción para el DOM de Temu."""
    
    def get_headers(self) -> Dict[str, str]:
        # Temu requiere Headers robustos incluso si usamos Selenium como respaldo
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
    def build_pagination_url(self, base_url: str, page: int) -> str:
        # PENDIENTE: Ajustar el parámetro exacto de paginación de Temu
        if page == 1:
            return base_url
        if "?" in base_url:
            return f"{base_url}&page={page}"
        return f"{base_url}?page={page}"
        
    def parse_items(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        seen_ids = set()
        
        # Vector Estructural 1: Filtramos estrictamente por el anclaje de datos del contenedor
        cards = soup.select('div[data-tooltip^="goodContainer-"]')
        
        for idx, card in enumerate(cards, 1):
            try:
                # 1. Extracción de Título y Limpieza de Ruido
                title_elem = card.select_one('h2')
                if not title_elem:
                    continue
                raw_title = title_elem.get_text(separator=" ", strip=True)
                title = raw_title.replace("Abrir en una nueva pestaña.", "").strip()

                # 2. Generación de Clave Primaria (ID)
                raw_tooltip = card.get('data-tooltip', '')
                goods_id = raw_tooltip.replace('goodContainer-', '').strip() if raw_tooltip else f"PLP-{idx:03d}"
                item_id = f"TEMU-{goods_id}"

                if item_id in seen_ids:
                    continue

                # 3. Extracción de Enlace de Red (con respaldo canónico por goods_id para evitar URLs vacías)
                link_elem = card.select_one('a[href]')
                url = link_elem.get('href', '').strip() if link_elem else ''
                if url.startswith('/'):
                    url = f"https://www.temu.com{url}"
                elif not url:
                    url = f"https://www.temu.com/goods.html?goods_id={goods_id}"

                # 4. Extracción de Precio (Vector Estructural data-type)
                price_container = card.select_one('div[data-type="price"]')
                if price_container:
                    first_span = price_container.find('span')
                    raw_price = first_span.get_text(strip=True) if first_span else "0"
                else:
                    raw_price = "0"
                    
                clean_price_str = re.sub(r'[^\d]', '', raw_price)
                price_value = float(clean_price_str) if clean_price_str else 0.0

                # 5. Extracción de Imagen de Alta Resolución
                img_elem = card.select_one('img[data-js-main-img="true"]') or card.select_one('img')
                image_url = img_elem.get('src') if img_elem else ''

                # Filtro de Seguridad Final
                if not title or price_value == 0.0:
                    continue

                seen_ids.add(item_id)
                products.append({
                    "id": item_id,
                    "title": title,
                    "price": price_value,
                    "url": url,
                    "image_url": image_url,
                    "category": "temu_search",
                    "timestamp": "Extraído por Ares Scraper"
                })

            except Exception:
                continue
                
        return products