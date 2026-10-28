import os
import re
import time
from typing import List, Optional
import undetected_chromedriver as uc

ULTIMO_ERROR_STEALTH: str = ""


def _detectar_version_chrome_local() -> Optional[int]:
    """
    Detecta dinámicamente la versión principal (major version) de Google Chrome instalada
    en Windows (ej. 152, 155, 156...) para evitar que las actualizaciones automáticas
    de Chrome rompan el arranque de ChromeDriver (SessionNotCreatedException).
    """
    rutas_chrome = [
        r"C:\Program Files\Google\Chrome\Application",
        r"C:\Program Files (x86)\Google\Chrome\Application",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application"),
    ]
    for ruta in rutas_chrome:
        if os.path.isdir(ruta):
            try:
                versiones = [
                    int(d.split(".")[0])
                    for d in os.listdir(ruta)
                    if re.match(r"^\d+\.\d+\.\d+\.\d+$", d)
                ]
                if versiones:
                    return max(versiones)
            except Exception:
                continue
    return None


def _hidratar_pagina_actual(driver, url: str, tiempo_espera_max: int = 30, es_primera: bool = True) -> str:
    driver.get(url)
    espera_base = 5 if es_primera else 3
    print(f"[STEALTH] Verificando estado de sesión y barreras WAF ({espera_base}s)...")
    time.sleep(espera_base)

    # --- INICIO DE SENSOR DE SESIÓN INTELIGENTE ---
    titulo_pagina = driver.title.lower() if driver.title else ""
    fuente_html = driver.page_source.lower()

    barreras = ["iniciar sesión", "verificación", "captcha", "security", "robot", "login"]

    if any(barrera in titulo_pagina for barrera in barreras) or "verify" in fuente_html:
        print(f"[ALERTA OPERADOR] Barrera detectada. Intervenga manualmente AHORA ({tiempo_espera_max}s).")
        time.sleep(tiempo_espera_max)
    else:
        print("[STEALTH] Sesión activa y verificada. Omitiendo espera prolongada.")
        time.sleep(1.5)
    # --- FIN DE SENSOR DE SESIÓN INTELIGENTE ---

    # Emulación biomecánica completa (3 tercios hasta el final del DOM para hidratar Lazy-Loading)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.33);")
    time.sleep(1.2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.66);")
    time.sleep(1.2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.92);")
    time.sleep(1.5)

    return driver.page_source


def obtener_dom_dinamico(url: str, tiempo_espera_max: int = 30) -> str:
    """
    Motor de extracción sigilosa con Sensor de Sesión Inteligente.
    Reduce los tiempos de espera si la Cookie de Confianza está activa.
    """
    res = obtener_multiples_doms_dinamicos([url], tiempo_espera_max=tiempo_espera_max)
    return res[0] if res else ""


def obtener_multiples_doms_dinamicos(urls: List[str], tiempo_espera_max: int = 30) -> List[str]:
    """
    Recorre una o múltiples URLs reutilizando la misma instancia de navegador y perfil persistente
    para evitar colisiones de bloqueo en chrome_profile y pérdida de datos entre páginas.
    """
    global ULTIMO_ERROR_STEALTH
    ULTIMO_ERROR_STEALTH = ""

    if not urls:
        return []

    version_detectada = _detectar_version_chrome_local()
    print(
        f"\n[STEALTH] Desplegando motor indetectable (Chrome v{version_detectada or 'Auto'}) "
        f"para {len(urls)} página(s). Blanco inicial: {urls[0]}"
    )

    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")

    # [INFRAESTRUCTURA] Creación de perfil persistente local para almacenar Cookies de Confianza
    perfil_ruta = os.path.join(os.getcwd(), "chrome_profile")
    options.add_argument(f"--user-data-dir={perfil_ruta}")

    driver = None
    doms: List[str] = []

    try:
        if version_detectada:
            driver = uc.Chrome(options=options, version_main=version_detectada)
        else:
            driver = uc.Chrome(options=options)

        for idx, target_url in enumerate(urls):
            print(f"[STEALTH] Navegando lote dinámico ({idx + 1}/{len(urls)}) -> {target_url}")
            html_content = _hidratar_pagina_actual(
                driver, target_url, tiempo_espera_max=tiempo_espera_max, es_primera=(idx == 0)
            )
            if html_content:
                doms.append(html_content)
        print(f"[STEALTH] Extracción de {len(doms)} DOM(s) completada.")
    except Exception as e:
        ULTIMO_ERROR_STEALTH = f"{type(e).__name__}: {str(e).splitlines()[0] if str(e) else str(e)}"
        print(f"[ERROR CRÍTICO STEALTH] {ULTIMO_ERROR_STEALTH}")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass  # Silenciar WinError 6

    return doms


# Bloque de auditoría aislada para pruebas unitarias
if __name__ == "__main__":
    url_prueba = "https://www.temu.com/search_result.html?search_key=teclado+mecanico"
    html_resultante = obtener_dom_dinamico(url_prueba)
    print(f"[AUDITORÍA] Longitud de HTML: {len(html_resultante)}")