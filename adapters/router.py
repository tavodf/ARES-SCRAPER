from urllib.parse import urlparse
from adapters.base_adapter import BaseAdapter
from adapters.meli_adapter import MercadoLibreAdapter
from adapters.amazon_adapter import AmazonAdapter
from adapters.temu_adapter import TemuAdapter

def get_adapter(url: str) -> BaseAdapter:
    """Analiza la URL objetivo y retorna el adaptador especializado."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    if "mercadolibre" in domain or "mercadolivre" in domain:
        return MercadoLibreAdapter()
    elif "amazon" in domain:
        return AmazonAdapter()
    elif "temu" in domain:
        return TemuAdapter()
    else:
        return AmazonAdapter()