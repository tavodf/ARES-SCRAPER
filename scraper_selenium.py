import os
import re
import time
from typing import List, Optional
import undetected_chromedriver as uc

ULTIMO_ERROR_STEALTH: str = ""


def _detectar_version_chrome_local() -> Optional[int]:
    """
    Detecta dinámicamente la versión principal (major version) del binario activo de Google Chrome
    instalado en Windows mediante metadatos de chrome.exe y el registro de Windows,
    evitando que carpetas de actualización pendientes generen SessionNotCreatedException.
    """
    # 1. Inspeccionar metadatos reales del ejecutable chrome.exe via Win32 ctypes
    rutas_exe = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe_path in rutas_exe:
        if os.path.isfile(exe_path):
            try:
                import ctypes
                from ctypes import wintypes
                size = ctypes.windll.version.GetFileVersionInfoSizeW(exe_path, None)
                if size:
                    res = ctypes.create_string_buffer(size)
                    ctypes.windll.version.GetFileVersionInfoW(exe_path, None, size, res)
                    lplpBuffer = wintypes.LPVOID()
                    puLen = wintypes.UINT()
                    if ctypes.windll.version.VerQueryValueW(res, r"\\", ctypes.byref(lplpBuffer), ctypes.byref(puLen)):
                        class VS_FIXEDFILEINFO(ctypes.Structure):
                            _fields_ = [
                                ('dwSignature', wintypes.DWORD),
                                ('dwStrucVersion', wintypes.DWORD),
                                ('dwFileVersionMS', wintypes.DWORD),
                                ('dwFileVersionLS', wintypes.DWORD),
                                ('dwProductVersionMS', wintypes.DWORD),
                                ('dwProductVersionLS', wintypes.DWORD),
                            ]
                        pffi = ctypes.cast(lplpBuffer, ctypes.POINTER(VS_FIXEDFILEINFO))
                        major = pffi.contents.dwProductVersionMS >> 16
                        if major > 0:
                            return major
            except Exception:
                pass

    # 2. Respaldo por Registro de Windows (versión activa reportada por Chrome)
    try:
        import winreg
        for hive, subkey in [
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Chrome\BLBeacon")
        ]:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    val, _ = winreg.QueryValueEx(key, "version")
                    if val:
                        return int(val.split(".")[0])
            except Exception:
                pass
    except Exception:
        pass

    # 3. Fallback: carpetas en disco (preferir versión menor activa si hay staging)
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
                    return min(versiones)
            except Exception:
                continue
    return None


def _es_pantalla_de_barrera(driver) -> bool:
    """Evalúa si la ventana activa se encuentra en un formulario de login, reto WAF o verificación."""
    try:
        curr_url = driver.current_url.lower()
        barreras_url = [
            "account-verification", "checkpoint", "/login", "identification",
            "challenge_id", "security", "captcha"
        ]
        if any(b in curr_url for b in barreras_url):
            return True

        titulo = (driver.title or "").lower()
        barreras_texto = [
            "iniciar sesión", "iniciar sesion", "ingresa a tu cuenta", "verificación",
            "verificacion", "captcha", "security", "robot", "login"
        ]
        if any(b in titulo for b in barreras_texto):
            return True

        # Chequeo en primeros 2500 caracteres del DOM para detectar formularios y retos
        fuente_muestra = driver.page_source[:2500].lower()
        if any(b in fuente_muestra for b in ["ingresa a tu cuenta", "no soy un robot", "g-recaptcha", "cf-turnstile"]):
            return True

        return False
    except Exception:
        return False


def _hidratar_pagina_actual(driver, url: str, tiempo_espera_max: int = 60, es_primera: bool = True) -> str:
    driver.get(url)
    espera_base = 5 if es_primera else 3
    print(f"[STEALTH] Verificando estado de sesión y barreras WAF ({espera_base}s)...")
    time.sleep(espera_base)

    # --- INICIO DE SENSOR DE SESIÓN INTELIGENTE ---
    es_barrera = _es_pantalla_de_barrera(driver)

    if es_barrera:
        print(f"\n[ALERTA OPERADOR] Barrera WAF / Verificación de identidad detectada ({driver.current_url}).")
        print(f"[ALERTA OPERADOR] Por favor, ingrese a su cuenta o complete el captcha en la ventana de Chrome ({tiempo_espera_max}s)...")
        # Monitoreo activo: esperar hasta que el operador realmente supere la pantalla de login/reto
        t_inicio = time.time()
        barrera_resuelta = False
        while time.time() - t_inicio < tiempo_espera_max:
            time.sleep(2)
            if not _es_pantalla_de_barrera(driver):
                print("[STEALTH] ¡Sesión verificada y barrera superada con éxito! Continuando extracción...")
                barrera_resuelta = True
                time.sleep(3)
                break

        if not barrera_resuelta and _es_pantalla_de_barrera(driver):
            print(f"[ALERTA OPERADOR] Tiempo límite ({tiempo_espera_max}s) alcanzado aún en pantalla de verificación.")
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


def obtener_dom_dinamico(url: str, tiempo_espera_max: int = 60) -> str:
    """
    Motor de extracción sigilosa con Sensor de Sesión Inteligente.
    Reduce los tiempos de espera si la Cookie de Confianza está activa.
    """
    res = obtener_multiples_doms_dinamicos([url], tiempo_espera_max=tiempo_espera_max)
    return res[0] if res else ""


def obtener_multiples_doms_dinamicos(urls: List[str], tiempo_espera_max: int = 60) -> List[str]:
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
    perfil_ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
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