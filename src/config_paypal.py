"""
Configuración de PayPal para pagos
Documentación: Configura tus credenciales de PayPal aquí
"""
import os
from pathlib import Path

# ========== CONFIGURACIÓN PAYPAL ==========
# IMPORTANTE: Configura tus credenciales de PayPal aquí

# Email de PayPal (ya configurado)
PAYPAL_EMAIL = "admin@1x2futbol.com"

# PayPal Client ID (obtener desde https://developer.paypal.com/)
# Para producción, usar credenciales de producción
# Para desarrollo, usar credenciales de sandbox
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")

# Modo sandbox (True para pruebas, False para producción)
PAYPAL_SANDBOX = os.getenv("PAYPAL_SANDBOX", "true").lower() == "true"

# URLs de PayPal
if PAYPAL_SANDBOX:
    PAYPAL_BASE_URL = "https://api.sandbox.paypal.com"
    PAYPAL_WEB_URL = "https://www.sandbox.paypal.com"
else:
    PAYPAL_BASE_URL = "https://api.paypal.com"
    PAYPAL_WEB_URL = "https://www.paypal.com"

# ========== INSTRUCCIONES DE CONFIGURACIÓN ==========
"""
Para configurar PayPal:

1. Crear cuenta de desarrollador en https://developer.paypal.com/
2. Crear una aplicación en el dashboard
3. Obtener Client ID y Secret
4. Configurar de una de estas formas:

   OPCIÓN A: Variables de entorno (recomendado para producción)
   - Windows: set PAYPAL_CLIENT_ID=tu_client_id
   - Linux/Mac: export PAYPAL_CLIENT_ID=tu_client_id
   
   OPCIÓN B: Archivo .env (crear en la raíz del proyecto)
   PAYPAL_CLIENT_ID=tu_client_id
   PAYPAL_SECRET=tu_secret
   PAYPAL_SANDBOX=true
   
   OPCIÓN C: Editar directamente este archivo (no recomendado para producción)
   PAYPAL_CLIENT_ID = "tu_client_id_aqui"
   PAYPAL_SECRET = "tu_secret_aqui"

5. Para producción, cambiar PAYPAL_SANDBOX a False

NOTA: Por ahora, la app usa PayPal.me para pagos simples.
Para integración completa con API, usar las credenciales arriba.
"""

# ========== CONFIGURACIÓN ADMOB ==========
# App ID de AdMob (obtener desde https://admob.google.com)
ADMOB_APP_ID = os.getenv("ADMOB_APP_ID", "ca-app-pub-1991167012133291~XXXXXXXXXX")

# Unit IDs de AdMob
ADMOB_BANNER_UNIT_ID = os.getenv("ADMOB_BANNER_UNIT_ID", "ca-app-pub-1991167012133291/XXXXXXXXXX")
ADMOB_INTERSTITIAL_UNIT_ID = os.getenv("ADMOB_INTERSTITIAL_UNIT_ID", "ca-app-pub-1991167012133291/XXXXXXXXXX")
ADMOB_REWARDED_UNIT_ID = os.getenv("ADMOB_REWARDED_UNIT_ID", "ca-app-pub-1991167012133291/XXXXXXXXXX")

# app-ads.txt (para incluir en el servidor web)
APP_ADS_TXT_CONTENT = """google.com, pub-1991167012133291, DIRECT, f08c47fec0942fa0"""

# ========== MODO ADMIN ==========
# Modo admin permite bypass de bloqueos premium (solo para desarrollo)
# Configurar con variable de entorno: QUINIELA_ADMIN_MODE=1
ADMIN_MODE = os.getenv("QUINIELA_ADMIN_MODE", "0").lower() in ("1", "true", "yes", "si", "on")

# Email del admin (para verificación adicional si es necesario)
ADMIN_EMAIL = "admin@1x2futbol.com"

