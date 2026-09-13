import os
import time
import undetected_chromedriver as uc

def obtener_dom_dinamico(url: str, tiempo_espera_max: int = 30) -> str:
    """
    Motor de extracción sigilosa con Sensor de Sesión Inteligente.
    Reduce los tiempos de espera si la Cookie de Confianza está activa.
    """
    print(f"\n[STEALTH] Desplegando motor indetectable. Blanco: {url}")
    
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    
    # [INFRAESTRUCTURA] Creación de perfil persistente local para almacenar Cookies de Confianza
    perfil_ruta = os.path.join(os.getcwd(), "chrome_profile")
    options.add_argument(f"--user-data-dir={perfil_ruta}")
    
    # Se fija la versión 152 para sincronizar con el binario local
    driver = uc.Chrome(options=options, version_main=152)
    html_content = ""
    
    try:
        driver.get(url)
        print("[STEALTH] Verificando estado de sesión y barreras WAF (5s)...")
        time.sleep(5) # Tiempo base de hidratación de red
        
        # --- INICIO DE SENSOR DE SESIÓN INTELIGENTE ---
        titulo_pagina = driver.title.lower() if driver.title else ""
        fuente_html = driver.page_source.lower()
        
        # Matriz de fricción: Palabras clave que indican bloqueo o pérdida de sesión
        barreras = ["iniciar sesión", "verificación", "captcha", "security", "robot", "login"]
        
        if any(barrera in titulo_pagina for barrera in barreras) or "verify" in fuente_html:
            print(f"[ALERTA OPERADOR] Barrera detectada. Intervenga manualmente AHORA ({tiempo_espera_max}s).")
            time.sleep(tiempo_espera_max)
        else:
            print("[STEALTH] Sesión activa y verificada. Omitiendo espera prolongada.")
            time.sleep(2) # Pausa mínima para asegurar que el DOM reaccione
        # --- FIN DE SENSOR DE SESIÓN INTELIGENTE ---
        
        # Emulación biomecánica
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
        time.sleep(2)
        
        html_content = driver.page_source
        print("[STEALTH] Extracción de DOM completada.")
        
    except Exception as e:
        print(f"[ERROR CRÍTICO] Falla en motor dinámico: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass # Silenciar WinError 6
            
    return html_content

# Bloque de auditoría aislada para pruebas unitarias
if __name__ == "__main__":
    url_prueba = "https://www.temu.com/search_result.html?search_key=teclado+mecanico"
    html_resultante = obtener_dom_dinamico(url_prueba)
    print(f"[AUDITORÍA] Longitud de HTML: {len(html_resultante)}")