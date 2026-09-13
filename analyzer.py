import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

def mostrar_tabla_preview(productos: List[Dict[str, Any]]):
    """
    Imprime en consola una tabla estructurada limitada a los primeros 5 registros
    para evitar saturación visual en la terminal.
    """
    if not productos:
        print("[ALERTA] No hay registros para mostrar en la tabla.")
        return

    # Limitar la muestra visual a máximo 5 elementos
    muestra = productos[:5]

    print("\n" + "="*115)
    print(f" [MATRIZ DE PREVISUALIZACIÓN - TOP 5] - Total de objetos en esta página: {len(productos)}")
    print("="*115)
    print(f"{'ID':<10} | {'PRECIO':<10} | {'TÍTULO (NOMBRE)':<45} | {'IMAGEN URL'}")
    print("-" * 115)

    for p in muestra:
        titulo_cortado = (p.get('title')[:42] + '...') if len(p.get('title', '')) > 42 else p.get('title', '')
        precio_str = f"${p.get('price', 0):,.2f}"
        print(f"{p.get('id'):<10} | {precio_str:<10} | {titulo_cortado:<45} | {p.get('image_url')}")
    
    print("="*115)
    if len(productos) > 5:
        print(f"   [INFO] Mostrando 5 de {len(productos)} registros detectados en la muestra inicial.")
    print("="*115)

def procesar_y_guardar_datos(productos: List[Dict[str, Any]], dataset_name: str = "market_dataset") -> str:
    """
    Recibe la lista de productos crudos, los consolida mediante Pandas,
    aplica normalización y los persiste en formato CSV dentro del Data Lake procesado.
    """
    if not productos:
        print("[ALERTA] La lista de productos está vacía. No hay datos para procesar.")
        return ""

    # 1. Crear DataFrame a partir de los datos recolectados
    df = pd.DataFrame(productos)

    # 2. Limpieza y normalización de columnas
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)

    if 'timestamp' in df.columns:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df['timestamp'] = current_time

    # --- INICIO DE BLOQUE DE LIMPIEZA ESTRUCTURAL ---
    total_raw = len(df)
    
    # Reasignar Clave Primaria: Deduplicar estrictamente por URL única
    if 'url' in df.columns:
        df = df.drop_duplicates(subset=['url'], keep='first')
    else:
        # Fallback de seguridad si el adaptador no mapeó URLs
        df = df.drop_duplicates(subset=['title'], keep='first') 
        
    # Emitir telemetría de purga en consola
    ruido_eliminado = total_raw - len(df)
    if ruido_eliminado > 0:
        print(f"[TELEMETRÍA] Sensor de Data Lake: {ruido_eliminado} nodos clonados (anuncios patrocinados) purgados.")
    # --- FIN DE BLOQUE DE LIMPIEZA ESTRUCTURAL ---

    # 3. Definir la ruta de persistencia en el Data Lake
    output_dir = os.path.join("data_lake", "02_processed")
    os.makedirs(output_dir, exist_ok=True)

    # Sanitizar el nombre del archivo
    safe_name = "".join(c for c in dataset_name if c.isalnum() or c in ('_', '-')).rstrip()
    if not safe_name:
        safe_name = "market_dataset"

    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ruta_archivo = os.path.join(output_dir, filename)

    # 4. Guardar archivo CSV con codificación UTF-8
    df.to_csv(ruta_archivo, index=False, encoding='utf-8-sig')
    print(f"[ÉXITO] Dataset persistido correctamente en: {ruta_archivo} ({len(df)} registros)")

    return ruta_archivo