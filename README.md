# NOVUX // ARES GRID - CYBER SCRAPER & PRICING ENGINE

> Extractor y minería de datos web en tiempo real con arquitectura híbrida de evasión perimetral, interfaz gráfica Cyberpunk (Tron Red) y persistencia automatizada en Data Lake.

---

## ⚡ Descripción General

**Ares Scraper** es una plataforma desktop diseñada para la extracción industrial de catálogos y precios en marketplaces de alta fricción defensiva (Cloudflare, WAFs y protecciones perimetrales). Combina un transporte estático optimizado para peticiones masivas con un motor dinámico indetectable basado en perfiles persistentes.

---

## 🛠️ Stack Tecnológico

* **Lenguaje Base:** Python 3.10+
* **Motor Dinámico / Evasión:** `undetected-chromedriver` (Selenium) con persistencia de cookies.
* **Motor Estático:** `Requests` con rotación y sanitización de cabeceras.
* **Procesamiento de DOM:** `BeautifulSoup4` (lxml).
* **Data Lake Pipeline:** `Pandas` (deduplicación por clave primaria, sanitización monetaria y guardado en CSV).
* **Interfaz Gráfica (GUI):** `pywebview` renderizando un frontend local optimizado con Canvas Matrix, SFX sintético y Web Speech API.

---

## 📐 Arquitectura del Sistema

[ URL Objetivo ]
                       │
                       ▼
              [ adapters/router.py ]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[ Adaptador Estático ]       [ Adaptador Dinámico ]
   (Requests/HTTP)             (Selenium Stealth)
       │                               │
       └───────────────┬───────────────┘
                       ▼
             [ Raw DOM Capture ]
                       │
                       ▼
            [ Marketplace Parser ]
        (MercadoLibre / Temu / Amazon)
                       │
                       ▼
             [ analyzer.py Pipeline ]
       (Deduplicación & Limpieza Monetaria)
                       │
                       ▼
           [ Data Lake / CSV Export ]

---

## 🚀 Instalación y Despliegue

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tavodf/ARES-SCRAPER.git
cd ARES-SCRAPER
