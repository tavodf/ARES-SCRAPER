import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple

def mostrar_tabla_preview(productos: List[Dict[str, Any]]):
    """
    Imprime en consola una tabla estructurada limitada a los primeros 5 registros
    para evitar saturación visual en la terminal.
    """
    if not productos:
        print("[ALERTA] No hay registros para mostrar en la tabla.")
        return

    muestra = productos[:5]

    print("\n" + "="*115)
    print(f" [MATRIZ DE PREVISUALIZACIÓN - TOP 5] - Total de objetos en esta página: {len(productos)}")
    print("="*115)
    print(f"{'ID':<14} | {'PRECIO':<12} | {'TÍTULO (NOMBRE)':<45} | {'IMAGEN URL'}")
    print("-" * 115)

    for p in muestra:
        titulo_cortado = (p.get('title')[:42] + '...') if len(p.get('title', '')) > 42 else p.get('title', '')
        precio_str = f"${p.get('price', 0):,.2f}"
        print(f"{str(p.get('id', '')):<14} | {precio_str:<12} | {titulo_cortado:<45} | {p.get('image_url')}")
    
    print("="*115)
    if len(productos) > 5:
        print(f"   [INFO] Mostrando 5 de {len(productos)} registros detectados en la muestra inicial.")
    print("="*115)


def depurar_y_normalizar_memoria(productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Normaliza tipos numéricos y aplica deduplicación inteligente por clave compuesta segura
    (URL canónica sin fragmentos de tracking o ID+Título+Precio cuando no hay URL única),
    preservando el 100% de entidades no fungibles (ej. vehículos con igual nombre pero distinto enlace/precio).
    Retorna: (lista_productos_unicos, cantidad_ruido_purgado)
    """
    if not productos:
        return [], 0

    df = pd.DataFrame(productos)
    total_raw = len(df)

    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['timestamp'] = current_time

    # Construir clave primaria canónica inmune a URLs vacías o fragmentos de tracking (#)
    def _build_pk(row):
        raw_url = str(row.get('url', '') or '').strip()
        clean_url = raw_url.split('#')[0].strip()
        item_id = str(row.get('id', '') or '').strip()
        title = str(row.get('title', '') or '').strip()
        price = str(row.get('price', 0.0))

        # Si el adaptador extrajo un ID único real de plataforma (AMZ-B0..., MELI-MCO..., TEMU-60...)
        if item_id and not any(tag in item_id for tag in ('-PLP-', '-FALLBACK-', '-PDP-')):
            return f"ID::{item_id}"
        # Si hay una URL real de producto
        if clean_url.startswith('http') and not clean_url.endswith('/item_1'):
            return f"URL::{clean_url}"
        return f"COMPOSITE::{item_id}||{title}||{price}"

    df['_pk'] = df.apply(_build_pk, axis=1)
    df = df.drop_duplicates(subset=['_pk'], keep='first').drop(columns=['_pk'])

    ruido_eliminado = total_raw - len(df)
    if ruido_eliminado > 0:
        print(f"[TELEMETRÍA] Sensor de Data Lake: {ruido_eliminado} nodos clonados (anuncios patrocinados) purgados.")

    registros_limpios = df.to_dict(orient='records')
    return registros_limpios, ruido_eliminado


def procesar_y_guardar_datos(productos: List[Dict[str, Any]], dataset_name: str = "market_dataset") -> str:
    """
    Recibe la lista de productos, aplica depuración/normalización mediante Pandas
    y los persiste en formato CSV dentro del Data Lake procesado (data_lake/02_processed).
    """
    if not productos:
        print("[ALERTA] La lista de productos está vacía. No hay datos para procesar.")
        return ""

    registros_limpios, _ = depurar_y_normalizar_memoria(productos)
    df = pd.DataFrame(registros_limpios)

    output_dir = os.path.join("data_lake", "02_processed")
    os.makedirs(output_dir, exist_ok=True)

    safe_name = "".join(c for c in dataset_name if c.isalnum() or c in ('_', '-')).rstrip()
    if not safe_name:
        safe_name = "market_dataset"

    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ruta_archivo = os.path.join(output_dir, filename)

    df.to_csv(ruta_archivo, index=False, encoding='utf-8-sig')
    print(f"[ÉXITO] Dataset persistido correctamente en: {ruta_archivo} ({len(df)} registros)")

    return ruta_archivo


def exportar_json_datos(productos: List[Dict[str, Any]], dataset_name: str = "market_dataset") -> str:
    """
    Exporta la matriz depurada en formato JSON estructurado dentro de data_lake/02_processed.
    """
    if not productos:
        return ""

    registros_limpios, _ = depurar_y_normalizar_memoria(productos)
    output_dir = os.path.join("data_lake", "02_processed")
    os.makedirs(output_dir, exist_ok=True)

    safe_name = "".join(c for c in dataset_name if c.isalnum() or c in ('_', '-')).rstrip() or "market_dataset"
    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta_archivo = os.path.join(output_dir, filename)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        json.dump(registros_limpios, f, ensure_ascii=False, indent=2)

    print(f"[ÉXITO] JSON persistido correctamente en: {ruta_archivo} ({len(registros_limpios)} registros)")
    return ruta_archivo