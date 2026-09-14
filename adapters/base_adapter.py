from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAdapter(ABC):
    """
    Clase abstracta base para todos los adaptadores de marketplaces de Ares Scraper.
    Aplica el principio de inversión de dependencias y el patrón Adapter.
    """
    # Define si el marketplace requiere Selenium con evasión WAF o requests estático
    is_dynamic: bool = False

    @abstractmethod
    def build_pagination_url(self, base_url: str, page: int) -> str:
        """Construye la URL específica para la página solicitada según la lógica del marketplace."""
        pass

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Retorna los headers HTTP específicos requeridos para peticiones directas."""
        pass

    @abstractmethod
    def parse_items(self, html_content: str) -> List[Dict[str, Any]]:
        """Extrae y normaliza las tarjetas de productos del HTML crudo."""
        pass