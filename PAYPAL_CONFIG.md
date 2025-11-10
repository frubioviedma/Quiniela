# Configuración de PayPal

## Email de PayPal

El email de PayPal está configurado en `src/freemium.py`:

```python
PAYPAL_EMAIL = "frubioviedma@gmail.com"
```

## Configuración de Credenciales (Opcional)

Para integración completa con PayPal API, editar `src/config_paypal.py`:

### Opción 1: Variables de Entorno (Recomendado)

```bash
# Windows PowerShell
$env:PAYPAL_CLIENT_ID="tu_client_id"
$env:PAYPAL_SECRET="tu_secret"
$env:PAYPAL_SANDBOX="true"  # false para producción

# Linux/Mac
export PAYPAL_CLIENT_ID="tu_client_id"
export PAYPAL_SECRET="tu_secret"
export PAYPAL_SANDBOX="true"
```

### Opción 2: Archivo .env

Crear archivo `.env` en la raíz del proyecto:

```
PAYPAL_CLIENT_ID=tu_client_id_aqui
PAYPAL_SECRET=tu_secret_aqui
PAYPAL_SANDBOX=true
```

### Opción 3: Editar Directamente (No recomendado para producción)

Editar `src/config_paypal.py`:

```python
PAYPAL_CLIENT_ID = "tu_client_id_aqui"
PAYPAL_SECRET = "tu_secret_aqui"
PAYPAL_SANDBOX = True  # False para producción
```

## Obtener Credenciales de PayPal

1. Ir a https://developer.paypal.com/
2. Iniciar sesión con tu cuenta de PayPal
3. Ir a "My Apps & Credentials"
4. Crear una nueva aplicación
5. Copiar Client ID y Secret

## Modo Actual

Actualmente, la app usa **PayPal.me** para pagos simples:
- URL: `https://www.paypal.com/paypalme/frubioviedma/{precio}EUR`
- Email: `frubioviedma@gmail.com`

Los usuarios realizan el pago y luego envían el comprobante por email para activar la licencia.

## Para Integración Completa con API

Si quieres integración automática con PayPal API:

1. Configurar credenciales (ver arriba)
2. Implementar webhook para recibir notificaciones de pago
3. Activar licencias automáticamente tras pago confirmado

Por ahora, el sistema funciona con PayPal.me y activación manual tras comprobante.

