# Checklist para Publicación en Google Play Store

## Información de la App

- **Nombre**: La quiniela 1X2
- **Paquete**: com.quiniela1x2.app (configurar en buildozer.spec)
- **Versión**: 1.0.0 (inicial)

## Configuración Requerida

### 1. buildozer.spec

```ini
[app]
title = La quiniela 1X2
package.name = quiniela1x2
package.domain = com.quiniela1x2
version = 1.0.0
requirements = python3,kivy,requests,beautifulsoup4,plyer,pygame

# Icono
icon.filename = %(source.dir)s/assets/logo_small.png

# Permisos
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# AdMob
android.gradle_dependencies = 
    com.google.android.gms:play-services-ads:22.0.0

android.meta_data = 
    com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-1991167012133291~XXXXXXXXXX

# Incluir assets
source.include_exts = py,kv,png,jpg,ttf,txt,db,json,wav,mp3
```

### 2. app-ads.txt

Crear archivo `app-ads.txt` en el servidor web (si tienes uno):

```
google.com, pub-1991167012133291, DIRECT, f08c47fec0942fa0
```

O incluir en la descripción de la app en Play Store.

### 3. PayPal Configuration

Editar `src/config_paypal.py`:

```python
PAYPAL_EMAIL = "frubioviedma@gmail.com"
PAYPAL_CLIENT_ID = "tu_client_id_aqui"  # O usar variable de entorno
PAYPAL_SECRET = "tu_secret_aqui"  # O usar variable de entorno
```

### 4. Modo Admin (Solo para desarrollo)

Para activar modo admin (bypass de bloqueos):
```bash
export QUINIELA_ADMIN_MODE=1
```

**IMPORTANTE**: NO incluir modo admin en la versión de producción.

### 5. Assets Requeridos

Crear directorio `assets/` con:
- `logo.png` (200x200px)
- `logo_small.png` (64x64px para icono)
- `sounds/click.wav` (opcional)
- `sounds/success.wav` (opcional)
- `sounds/error.wav` (opcional)

### 6. Permisos y Privacidad

- **Política de Privacidad**: ✅ Creada en `LEGAL/POLITICA_PRIVACIDAD.md`
  - Debe alojarse en URL accesible
  - URL requerida en Play Console
- **Términos y Condiciones**: ✅ Creados en `LEGAL/TERMINOS_Y_CONDICIONES.md`
  - Recomendado alojar en URL
- **Aviso Legal**: ✅ Creado en `LEGAL/AVISO_LEGAL.md`
- **Aviso de Cookies**: ✅ Creado en `LEGAL/AVISO_COOKIES.md`
- **Información del Desarrollador**:
  - Nombre: Fernando Manuel Rubio
  - Profesión: Ingeniero de Sistemas
  - NIF: 75108544C
  - Email: frubioviedma@gmail.com
- **Permisos justificados**: Solo los necesarios

### 7. Testing

- [ ] Probar en dispositivo Android real
- [ ] Verificar que AdMob funciona
- [ ] Verificar que PayPal funciona
- [ ] Probar todas las funcionalidades premium
- [ ] Verificar que el modo admin NO está activo en producción
- [ ] Probar sin conexión a internet
- [ ] Verificar que la BBDD histórica se descarga correctamente

### 8. Screenshots para Play Store

Preparar:
- 2-8 screenshots (mínimo 320px, máximo 3840px)
- Icono de alta resolución (512x512px)
- Feature graphic (1024x500px)
- Video promocional (opcional)

### 9. Descripción de la App

```
La quiniela 1X2 - Sistema inteligente de análisis y pronósticos

Características:
- Análisis probabilístico avanzado
- Reducción inteligente de quinielas
- Base de datos histórica completa
- Condiciones avanzadas premium
- Sin anuncios con suscripción premium

Ofertas especiales:
- 20% de descuento permanente
- Licencia vitalicia incluye BBDD histórica gratis
```

### 10. Categoría

- **Categoría principal**: Deportes
- **Categoría secundaria**: Entretenimiento

### 11. Clasificación de Contenido

- PEGI: 3+ (o según contenido)
- Contenido: Sin restricciones de edad

### 12. Precios

Configurados en `src/freemium.py`:
- Semanal: 2.39€ (descuento 20%)
- Temporada: 23.99€ (descuento 20%)
- Vitalicia: 39.99€ (descuento 20%)
- BBDD Histórica: 4.79€ (descuento 20%)

### 13. Verificaciones Finales

- [ ] Nombre de app correcto: "La quiniela 1X2"
- [ ] Logo visible en todas las pantallas
- [ ] Sonidos funcionan (si se incluyen)
- [ ] Todos los botones premium funcionan
- [ ] Descuento del 20% visible en todos los diálogos
- [ ] Usuarios de por vida reciben BBDD gratis
- [ ] Modo admin desactivado en producción
- [ ] AdMob configurado correctamente
- [ ] PayPal configurado correctamente
- [ ] Sin errores en logs
- [ ] App funciona offline (con datos locales)

### 14. Build Final

```bash
buildozer android release
```

Firmar APK y subir a Play Store Console.

