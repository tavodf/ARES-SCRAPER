import sys
import time
from bs4 import BeautifulSoup
from adapters.router import get_adapter
import scraper
import analyzer

def print_header():
    print("\n" + "="*115)
    print("   [ ARES SCRAPER ] - MOTOR DE BARRIDO Y PRICING INDUSTRIAL (DATA LAKE ENGINE)")
    print("="*115)

def auditar_y_previsualizar(url):
    """
    Realiza el reconocimiento inicial, extrae la primera página de muestra,
    ejecuta el parseo y despliega la matriz tabular de previsualización.
    """
    adapter = get_adapter(url)
    headers = adapter.get_headers()
    
    print(f"\n[SISTEMA] Adaptador asignado: {adapter.__class__.__name__}")
    print(f"[SISTEMA] Conectando y extrayendo muestra inicial (Página 1)...")
    
    try:
        # Extraer primer DOM para previsualización inmediata
        dom_inicial = scraper.obtener_dom(url)
        if not dom_inicial:
            print("[ERROR] No se pudo obtener respuesta del servidor objetivo.")
            return None, 0

        soup = BeautifulSoup(dom_inicial, 'html.parser')
        titulo_sitio = soup.title.string.strip() if soup.title else 'No detectado'
        print(f"[ÉXITO] Conexión establecida. Título del Sitio: {titulo_sitio}")

        # Parsear ítems de la muestra inicial
        productos_muestra = adapter.parse_items(dom_inicial)
        
        if productos_muestra:
            # Mostrar tabla tabular previa usando el analizador
            analyzer.mostrar_tabla_preview(productos_muestra)
        else:
            print("[ALERTA] La muestra inicial no arrojó productos con los selectores actuales.")

        return adapter, len(productos_muestra)

    except Exception as e:
        print(f"\n[ERROR CRÍTICO] Fallo durante la auditoría y previsualización: {e}")
        return None, 0

def calcular_tiempo_estimado(paginas: int, delay: float = 1.5) -> str:
    total_segundos = paginas * delay
    return f"{total_segundos:.1f} segundos aprox."

def motor_interactivo():
    print_header()
    
    while True:
        target = input("\n[INPUT] Ingrese la URL objetivo (o escriba 'salir' para abortar): ").strip()
        
        if target.lower() == 'salir':
            print("[SISTEMA] Secuencia de apagado iniciada. Entorno cerrado.")
            sys.exit()
            
        if not target.startswith("http"):
            print("[ALERTA] Protocolo faltante. La URL debe incluir 'http://' o 'https://'.")
            continue
            
        # 1. Auditoría y Previsualización Tabular Inicial (Página 1)
        adapter, total_muestra = auditar_y_previsualizar(target)
        if not adapter or total_muestra == 0:
            print("[SISTEMA] Reiniciando ciclo de entrada...")
            continue
            
        opcion = input("\n[INPUT] ¿Desea proceder con el barrido masivo basado en esta estructura? (S/N): ").upper()
        if opcion != 'S':
            print("[SISTEMA] Operación omitida por el operador. Reiniciando ciclo...")
            continue
            
        # 2. Configuración de Paginación Masiva
        try:
            paginas_input = input("[INPUT] Ingrese el número total de páginas a escanear (Ej. 3): ").strip()
            max_paginas = int(paginas_input) if paginas_input else 1
        except ValueError:
            max_paginas = 1
            print("[ALERTA] Valor inválido. Se configurará por defecto a 1 sola página.")

        # 3. Cálculo matemático del tiempo estimado
        tiempo_estimado = calcular_tiempo_estimado(max_paginas, delay=1.5)
        print(f"\n[ESTIMACIÓN] Tiempo aproximado de barrido para {max_paginas} página(s): {tiempo_estimado}")
        
        confirmar = input("[INPUT] ¿Desea ejecutar la extracción masiva? (S/N): ").upper()
        
        if confirmar == 'S':
            # 4. Ingesta masiva mediante scraper.py
            lista_doms = scraper.extraer_multiples_paginas(target, max_paginas)
            
            if not lista_doms:
                print("[ALERTA] No se recolectaron datos en el barrido masivo. Reiniciando ciclo...")
                continue
                
            # 5. Parsing iterativo sobre todos los DOMs recolectados
            todos_los_productos = []
            for idx, dom in enumerate(lista_doms, 1):
                print(f"[PARSER] Procesando datos de la página {idx} con {adapter.__class__.__name__}...")
                productos_pagina = adapter.parse_items(dom)
                todos_los_productos.extend(productos_pagina)
                
            print(f"\n[ÉXITO] Extracción masiva completada. Total unificado acumulado: {len(todos_los_productos)} registros.")
            
            if not todos_los_productos:
                print("[ALERTA] La lista final de productos quedó vacía.")
                continue

            # 6. Protocolo de nombramiento y persistencia en Data Lake
            nombre_usuario = input("[INPUT] Ingrese un identificador base para guardar el Dataset en CSV (o 'cancelar'): ").strip()
            
            if nombre_usuario.lower() == 'cancelar' or not nombre_usuario:
                print("[SISTEMA] Operación de guardado abortada. Datos descartados de forma segura.")
                continue
                
            # 7. Exportación persistente mediante Analyzer
            ruta_archivo = analyzer.procesar_y_guardar_datos(todos_los_productos, nombre_usuario)
            
            if ruta_archivo:
                print(f"\n[SISTEMA] Ciclo de pricing finalizado con éxito. Matriz exportada en: {ruta_archivo}")
        else:
            print("[SISTEMA] Operación cancelada por el operador. Reiniciando ciclo...")

if __name__ == "__main__":
    motor_interactivo()