import os

html_path = os.path.join(os.path.dirname(__file__), "index.html")

with open(html_path, "r", encoding="utf-8") as f:
    c = f.read()

nova_css = """
        /* ====================================================================
         * NOVA TOUR BOT // ARES CYBER EDITION
         * ==================================================================== */
        #aresTourPill {
            position: fixed; bottom: 22px; right: 22px; z-index: 95;
            display: flex; align-items: center; gap: 8px;
            padding: 8px 16px; border-radius: 25px;
            background: rgba(14, 0, 0, 0.94);
            border: 1px solid #ff3333; color: #ffd700;
            font-family: 'Consolas', monospace; font-size: 11px; font-weight: bold;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
            cursor: pointer; transition: all 0.25s ease;
        }
        #aresTourPill:hover {
            transform: translateY(-2px) scale(1.04);
            border-color: #ffd700; box-shadow: 0 0 25px rgba(255, 215, 0, 0.6);
        }
        #aresTourCard {
            display: none; position: fixed; z-index: 98;
            width: min(92vw, 460px);
            background: rgba(10, 0, 0, 0.96);
            border: 2px solid #ff0000; border-radius: 12px;
            box-shadow: 0 0 40px rgba(255, 0, 0, 0.55), 0 20px 50px rgba(0, 0, 0, 0.95);
            padding: 20px; font-family: 'Consolas', monospace; color: #fff;
            backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        }
        .tour-header {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid #440000; padding-bottom: 10px; margin-bottom: 12px;
        }
        .tour-avatar {
            width: 32px; height: 32px; border-radius: 8px;
            background: rgba(255, 0, 0, 0.2); border: 1px solid #ff0000;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; color: #ffd700;
        }
        .tour-badge {
            display: inline-block; font-size: 9.5px; color: #ffd700;
            background: rgba(255, 215, 0, 0.15); border: 1px solid rgba(255, 215, 0, 0.4);
            padding: 2px 8px; border-radius: 12px; margin-bottom: 8px; text-transform: uppercase;
        }
        .tour-title { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 8px; line-height: 1.3; }
        .tour-text { font-size: 11px; color: #ffcccc; line-height: 1.5; margin-bottom: 16px; }
        .tour-footer {
            display: flex; justify-content: space-between; align-items: center;
            border-top: 1px solid #330000; padding-top: 10px;
        }
        .tour-dots { display: flex; gap: 4px; }
        .tour-dot { width: 6px; height: 6px; border-radius: 50%; background: #440000; }
        .tour-dot.active { width: 14px; border-radius: 4px; background: #ffd700; }
        .tour-btn {
            background: #ff0000; color: #000; border: none; padding: 6px 14px;
            font-family: 'Consolas', monospace; font-size: 11px; font-weight: bold; cursor: pointer;
            box-shadow: 0 0 10px #ff0000;
        }
        .tour-btn-prev {
            background: #220000; color: #ff6666; border: 1px solid #660000;
            margin-right: 6px; box-shadow: none;
        }
        .tour-btn-wa {
            background: linear-gradient(135deg, #10b981, #059669); color: #fff;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.5); text-decoration: none;
            display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px;
            font-size: 11px; font-weight: bold; border-radius: 4px;
        }
"""

nova_html_and_js = """
    <!-- BOT GUIA NOVA // ARES CYBER EDITION -->
    <div id="aresTourPill" onclick="iniciarNovaTour()">
        <span style="color:#00ff66;">🤖</span>
        <span>Tour Guiado con Nova</span>
    </div>

    <div id="aresTourCard">
        <div class="tour-header">
            <div style="display:flex; align-items:center; gap:8px;">
                <div class="tour-avatar">🤖</div>
                <div>
                    <div style="font-size:11.5px; font-weight:bold; color:#ffd700;">Nova // Consultora NOVUX</div>
                    <div style="font-size:8.5px; color:#ff6666;">DATA FACTORY &amp; L7 MINING</div>
                </div>
            </div>
            <button onclick="cerrarNovaTour()" style="background:none; border:none; color:#ff6666; font-size:16px; cursor:pointer;">✕</button>
        </div>
        <div class="tour-badge" id="novaStepBadge">PASO 1 DE 5</div>
        <div class="tour-title" id="novaStepTitle">Minería Web sin Bloqueos WAF</div>
        <div class="tour-text" id="novaStepText">Texto</div>
        <div class="tour-footer">
            <div class="tour-dots" id="novaDotsContainer"></div>
            <div id="novaActionsContainer"></div>
        </div>
    </div>

    <script>
        const NOVA_STEPS = [
            {
                badge: "Paso 1 de 5 • El Dolor en Scraping",
                title: "Guerra contra Cloudflare, DataDome & Captchas",
                text: "¡Hola! Soy <b>Nova</b>, asesora de arquitectura en <b>NOVUX</b>. Si extraes precios masivos o catálogos, sabes que los sitios objetivo bloquean tus IPs o te saturan de Captchas. ARES GRID penetra defensas Layer 7 con rotación de huella TLS y headers aleatorios.",
                nextLabel: "Ver Blanco @URL →"
            },
            {
                badge: "Paso 2 de 5 • Conexión Táctica",
                title: "Handshake Stealth y Selección de Adaptador",
                text: "Pega la URL de cualquier e-commerce (MercadoLibre, Amazon, Éxito, Alkosto). El sistema reconoce automáticamente la estructura del catálogo y ejecuta un handshake encubierto simulando navegación humana.",
                nextLabel: "Ver Purga de Ruido →"
            },
            {
                badge: "Paso 3 de 5 • Calidad de Datos",
                title: "Eliminación de Clones y Anuncios Ruido",
                text: "Un scraping sucio llena tu base de datos de basura. El motor de ARES purga en memoria duplicados, banners promocionales y recomendaciones falsas, garantizando 100% registros limpios.",
                nextLabel: "Ver Terminal de Datos →"
            },
            {
                badge: "Paso 4 de 5 • Data Lake Inmutable",
                title: "Exportación Directa a CSV y JSON Columnar",
                text: "Una vez completado el barrido masivo, puedes ordenar por precio menor/mayor y exportar el dataset a CSV para Excel o JSON para pipelines de Machine Learning y Power BI.",
                nextLabel: "Cierre Comercial →"
            },
            {
                badge: "Paso 5 de 5 • Clúster Dedicado",
                title: "¿Listo para desplegar ARES en tus Servidores?",
                text: "Implementamos clústeres de extracción dedicados con proxies residenciales rotativos ilimitados, sincronización directa a tu ERP o Data Lake privado. ¡Hablemos hoy mismo!",
                isFinal: true
            }
        ];

        let novaCurrentStep = 0;

        function iniciarNovaTour(step = 0) {
            playBeep(900, 0.08);
            novaCurrentStep = step;
            document.getElementById("aresTourCard").style.display = "block";
            document.getElementById("aresTourPill").style.display = "none";
            renderNovaStep();
        }

        function cerrarNovaTour() {
            playBeep(450, 0.06);
            document.getElementById("aresTourCard").style.display = "none";
            document.getElementById("aresTourPill").style.display = "flex";
            sessionStorage.setItem("novux_ares_tour_seen", "true");
        }

        function renderNovaStep() {
            const s = NOVA_STEPS[novaCurrentStep];
            document.getElementById("novaStepBadge").innerText = s.badge;
            document.getElementById("novaStepTitle").innerHTML = s.title;
            document.getElementById("novaStepText").innerHTML = s.text;

            // Render dots
            let dots = "";
            for (let i = 0; i < NOVA_STEPS.length; i++) {
                dots += '<div class="tour-dot ' + (i === novaCurrentStep ? 'active' : '') + '"></div>';
            }
            document.getElementById("novaDotsContainer").innerHTML = dots;

            // Actions
            let actions = "";
            if (s.isFinal) {
                actions = `
                    <button class="tour-btn tour-btn-prev" onclick="iniciarNovaTour(0)">Reiniciar</button>
                    <a href="https://wa.me/573196300410?text=Hola%20Gustavo%2C%20vi%20la%20gu%C3%ADa%20de%20Nova%20en%20ARES%20GRID%20y%20me%20interesa%20implementar%20el%20extractor%20en%20mi%20empresa." target="_blank" rel="noopener noreferrer" class="tour-btn-wa">
                        <span>📲 Agendar por WhatsApp</span>
                    </a>
                `;
            } else {
                actions = `
                    ${novaCurrentStep > 0 ? '<button class="tour-btn tour-btn-prev" onclick="novaPrev()">← Atrás</button>' : ''}
                    <button class="tour-btn" onclick="novaNext()">${s.nextLabel || 'Siguiente →'}</button>
                `;
            }
            document.getElementById("novaActionsContainer").innerHTML = actions;

            // Posicionar card centrado abajo
            const card = document.getElementById("aresTourCard");
            const w = window.innerWidth;
            card.style.bottom = "80px";
            card.style.right = Math.max(16, (w > 500 ? 24 : 10)) + "px";
        }

        function novaNext() {
            if (novaCurrentStep < NOVA_STEPS.length - 1) {
                playBeep(800, 0.06);
                novaCurrentStep++;
                renderNovaStep();
            } else {
                cerrarNovaTour();
            }
        }

        function novaPrev() {
            if (novaCurrentStep > 0) {
                playBeep(600, 0.06);
                novaCurrentStep--;
                renderNovaStep();
            }
        }

        // Auto-iniciar tour a los 1.8s si no lo ha visto
        setTimeout(() => {
            const hasSeen = sessionStorage.getItem("novux_ares_tour_seen");
            if (!hasSeen) {
                iniciarNovaTour(0);
            }
        }, 1800);
    </script>
"""

c = c.replace("</style>", nova_css + "\n    </style>", 1)
c = c.replace("</body>", nova_html_and_js + "\n</body>", 1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(c)

print("Nova Bot inyectado con éxito en ARES index.html!")
