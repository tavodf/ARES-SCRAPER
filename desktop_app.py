import os
import webview
from bs4 import BeautifulSoup
import scraper
import analyzer
from adapters.router import get_adapter

class NativeBridge:
    """
    Puente de comunicación nativa entre el frontend (React/TS) 
    y el backend modular de Python a través de pywebview.
    """

    def inspect_target(self, url: str) -> dict:
        """
        Fase 1: Reconocimiento previo y huella DOM sin barrido masivo. 
        Devuelve el título, estado y adaptador asignado.
        """
        print(f"\n[ESCRITORIO] Inspeccionando objetivo preliminar: {url}")
        try:
            dom = scraper.obtener_dom(url)
            if not dom:
                return {"status": "error", "message": "No se obtuvo respuesta del servidor objetivo."}

            soup = BeautifulSoup(dom, 'html.parser')
            titulo = soup.title.string.strip() if soup.title else "Sin título detectado"
            
            # Identificar el adaptador correspondiente para reportar la estrategia
            adapter = get_adapter(url)
            estrategia = adapter.__class__.__name__

            print(f"[RECONOCIMIENTO] Título detectado: {titulo}")
            print(f"[RECONOCIMIENTO] Adaptador Activo: {estrategia}")
            
            return {
                "status": "success",
                "title": titulo,
                "strategy": estrategia,
                "url": url
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run_scraping(self, url: str, pages: int = 1, dataset_name: str = "market_dataset") -> dict:
        """
        Fase 2: Ejecución masiva parametrizada por el operador utilizando 
        el enrutador de adaptadores y el pipeline de Pandas.
        """
        try:
            pages = int(pages)
        except (ValueError, TypeError):
            pages = 1

        if not dataset_name or not str(dataset_name).strip():
            dataset_name = "market_dataset"

        print(f"\n[ESCRITORIO] Iniciando barrido nativo para: {url}")
        print(f"[ESCRITORIO] Configuración: {pages} página(s) | Salida: {dataset_name}.csv")

        try:
            # 1. Extracción de HTMLs mediante el scraper de red y adaptadores
            doms = scraper.extraer_multiples_paginas(url, pages)
            if not doms:
                return {"status": "error", "message": "No se recolectaron datos en el barrido."}

            adapter = get_adapter(url)
            todos_los_productos = []
            estrategia_final = adapter.__class__.__name__

            # 2. Parseo estructurado por cada DOM recolectado
            for dom in doms:
                prods = adapter.parse_items(dom)
                todos_los_productos.extend(prods)

            if not todos_los_productos:
                return {"status": "error", "message": "La lista de productos quedó vacía tras el parseo."}

            # 3. Persistencia de datos mediante Pandas en el Data Lake
            ruta_archivo = analyzer.procesar_y_guardar_datos(todos_los_productos, dataset_name)

            # 4. Formatear items para el consumo del frontend
            items_formateados = []
            for i, prod in enumerate(todos_los_productos, 1):
                items_formateados.append({
                    "id": prod.get("id", f"NVX-{i:03d}"),
                    "title": prod.get("title", "Sin título"),
                    "price": str(prod.get("price", "0.0")),
                    "url": prod.get("url", url),
                    "category": estrategia_final,
                    "timestamp": "Extraído por Ares Scraper"
                })

            return {
                "status": "success",
                "total": len(items_formateados),
                "ruta_archivo": ruta_archivo,
                "items": items_formateados
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    print("[SISTEMA] Aislando variables. Iniciando puente nativo de ARES SCRAPER...")
    
    # 1. Resolución de la ruta absoluta del index.html compilado del frontend
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_INDEX = os.path.join(BASE_DIR, "frontend", "dist", "index.html")

    # 2. Validación de existencia del bundle antes de invocar WebView
    if not os.path.exists(FRONTEND_INDEX):
        print(f"\n[ERROR CRÍTICO] No se encuentra la interfaz compilada en: {FRONTEND_INDEX}")
        print("[ACCIÓN REQUERIDA] Ejecuta 'npm run build' dentro del directorio frontend.")
    else:
        api = NativeBridge()
        
        # 3. Creación de la ventana nativa de cabina con PyWebView
        window = webview.create_window(
            title='ARES SCRAPER // MARKET PRICING ENGINE',
            url=FRONTEND_INDEX,
            js_api=api,
            width=1280,
            height=800,
            background_color='#030000',
            min_size=(900, 600)
        )
        webview.start(debug=True)