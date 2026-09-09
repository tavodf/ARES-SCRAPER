from urllib.parse import urlparse
from adapters.base_adapter import BaseAdapter
from adapters.meli_adapter import MercadoLibreAdapter
from adapters.amazon_adapter import AmazonAdapter

def get_adapter(url: str) -> BaseAdapter:
    """
    Analiza la URL objetivo y retorna el adaptador especializado correspondiente.
    Si el dominio no está registrado explícitamente, retorna el adaptador de Amazon por defecto o una base genérica.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    if "mercadolibre" in domain or "mercadolivre" in domain:
        return MercadoLibreAdapter()
    elif "amazon" in domain:
        return AmazonAdapter()
    else:
        # Fallback predeterminado a Amazon o adaptador genérico
        return AmazonAdapter()
    