from urllib.parse import urlparse
from adapters.base_adapter import BaseAdapter
from adapters.meli_adapter import MercadoLibreAdapter
from adapters.amazon_adapter import AmazonAdapter
from adapters.temu_adapter import TemuAdapter

def get_adapter(url: str) -> BaseAdapter:
    """Analiza la URL objetivo y retorna el adaptador especializado."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    # Ecosistema MercadoLibre: clasificados, vehículos, inmuebles y retail regional
    meli_domains = ["mercadolibre", "mercadolivre", "tucarro", "tuinmueble", "tumoto"]
    if any(m in domain for m in meli_domains):
        return MercadoLibreAdapter()
    elif "amazon" in domain:
        return AmazonAdapter()
    elif "temu" in domain:
        return TemuAdapter()
    else:
        return AmazonAdapter()