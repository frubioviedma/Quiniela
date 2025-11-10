Administración de Publicidad y Freemium (Mock en desarrollo)

Objetivo

- Definir dónde y cómo se muestran anuncios y upsells en desarrollo (mock) y plan para producción (AdMob con KivMob en Kivy).

Ubicaciones de anuncios (desktop tkinter)

- Control central: `src/anuncios.py`.
- Diálogo `AnuncioDialog`: muestra un espacio de anuncio simulado y botón “✓ Anuncio Visto - Continuar”.
- Diálogo `PremiumDialog`: opciones de suscripción (semanal/temporada/vida) y compra BBDD histórica. En modo DEV permite “simular” pagos.

Puntos del flujo (ya integrados con freemium)

- “Actualizar desde Web” (scraping).
- “Calcular Pronósticos”.
- “Rellenar Automáticamente”.
- “Aplicar Condiciones”.
- “Aplicar Reducción”.
- “Guardar Quiniela” (hoy en pestañas “Pronósticos” y “Reducción”).
- “Comparar Resultados” (pestaña “Análisis”: solo carga/compare).

Modo desarrollo (mock)

- Activado por `QUINIELA_DEV_MODE=1` o desde `PremiumDialog` (simular pagos).
- Permite continuar tras “ver anuncio” simulado y/o simular compras.

Android (Kivy) – plan de producción

- Integrar `kivmob` (AdMob) en la UI Kivy móvil (cuando la UI esté lista).
- Tipos de anuncio: banner fijo en pantallas largas (reducción/análisis) e interstitial entre pasos clave.
- Fallback: si no hay red o falla la carga, permitir continuar y registrar evento.
- El esqueleto `app_android/main.py` ya define navegación (Menú/Jornada/Pronósticos/Reducción/Análisis) para conectar anuncios cuando se implemente la UI final.

Recomendaciones

- No bloquear pruebas internas: mantener DEV_MODE activo en APK debug.
- Configurar IDs de AdMob en variables de entorno o fichero no versionado para production.


