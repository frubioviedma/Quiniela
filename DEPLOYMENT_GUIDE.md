# Guía Completa de Deployment y Actualizaciones

## Tabla de Contenidos

1. [Preparación Antes de Generar APK](#preparación-antes-de-generar-apk)
2. [Configuración de Buildozer](#configuración-de-buildozer)
3. [Generación del APK](#generación-del-apk)
4. [Firma del APK](#firma-del-apk)
5. [Publicación en Play Store](#publicación-en-play-store)
6. [Sistema de Actualizaciones](#sistema-de-actualizaciones)
7. [Notificaciones Push](#notificaciones-push)
8. [Actualización Automática](#actualización-automática)

---

## Preparación Antes de Generar APK

### 1. Verificar Assets

```bash
# Verificar que existen los assets necesarios
ls assets/logo.png
ls assets/logo_small.png
ls assets/logo_icon.png
```

### 2. Configurar Variables de Entorno

**IMPORTANTE**: Desactivar modo admin y dev mode antes de producción:

```bash
# Windows PowerShell
$env:QUINIELA_ADMIN_MODE="0"
$env:QUINIELA_DEV_MODE="0"

# Linux/Mac
unset QUINIELA_ADMIN_MODE
unset QUINIELA_DEV_MODE
```

### 3. Verificar Configuración

Editar `src/config_paypal.py`:
- `ADMIN_MODE = False` (o verificar variable de entorno)
- `PAYPAL_SANDBOX = False` (para producción)
- Verificar `ADMOB_APP_ID` y Unit IDs

### 4. Actualizar Versión

Editar `buildozer.spec`:
```ini
version = 1.0.0  # Incrementar para cada release
```

### 5. Limpiar Caché

```bash
# Limpiar buildozer
buildozer android clean

# Limpiar Python
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## Configuración de Buildozer

### buildozer.spec

```ini
[app]
title = La quiniela 1X2
package.name = quiniela1x2
package.domain = com.quiniela1x2
version = 1.0.0
requirements = python3,kivy,requests,beautifulsoup4,plyer,pygame,sqlite3

# Icono
icon.filename = %(source.dir)s/assets/logo_icon.png

# Permisos
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# AdMob
android.gradle_dependencies = 
    com.google.android.gms:play-services-ads:22.0.0

android.meta_data = 
    com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-1991167012133291~XXXXXXXXXX

# Incluir assets
source.include_exts = py,kv,png,jpg,ttf,txt,db,json,wav,mp3
source.include_patterns = assets/*

# Orientación
orientation = portrait

# Logs
log_level = 2
```

### Verificar buildozer.spec

```bash
buildozer android debug  # Primero probar en modo debug
```

---

## Generación del APK

### 1. APK Debug (Para Pruebas)

```bash
buildozer android debug
```

El APK se genera en: `.buildozer/android/platform/build/dists/quiniela1x2/bin/`

### 2. APK Release (Para Producción)

```bash
buildozer android release
```

### 3. Verificar APK

```bash
# Instalar en dispositivo
adb install -r bin/quiniela1x2-1.0.0-arm64-v8a-release.apk

# Verificar permisos
aapt dump badging bin/quiniela1x2-1.0.0-arm64-v8a-release.apk | grep uses-permission
```

---

## Firma del APK

### 1. Generar Keystore (Primera Vez)

```bash
keytool -genkey -v -keystore quiniela-release.keystore -alias quiniela -keyalg RSA -keysize 2048 -validity 10000
```

**IMPORTANTE**: Guardar la contraseña y datos del keystore de forma segura.

### 2. Firmar APK

```bash
# Usar jarsigner (incluido en JDK)
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore quiniela-release.keystore bin/quiniela1x2-1.0.0-arm64-v8a-release-unsigned.apk quiniela

# O usar apksigner (recomendado)
apksigner sign --ks quiniela-release.keystore --ks-key-alias quiniela bin/quiniela1x2-1.0.0-arm64-v8a-release-unsigned.apk
```

### 3. Verificar Firma

```bash
apksigner verify --verbose bin/quiniela1x2-1.0.0-arm64-v8a-release.apk
```

---

## Publicación en Play Store

### 1. Crear App en Play Console

1. Ir a https://play.google.com/console
2. Crear nueva aplicación
3. Completar información básica:
   - Nombre: "La quiniela 1X2"
   - Idioma: Español
   - Tipo: App
   - Gratis/Pago: Gratis (con compras in-app)

### 2. Subir APK

1. Ir a "Producción" → "Crear nueva versión"
2. Subir APK firmado
3. Completar notas de versión

### 3. Contenido de la App

- **Descripción corta**: "Sistema inteligente de análisis y pronósticos de quinielas"
- **Descripción completa**: Ver `PLAY_STORE_DESCRIPTION.md`
- **Categoría**: Deportes
- **Clasificación**: PEGI 3

### 4. Screenshots

Preparar:
- 2-8 screenshots (mínimo 320px, máximo 3840px)
- Feature graphic (1024x500px)
- Icono de alta resolución (512x512px)

### 5. Política de Privacidad y Documentos Legales

**Documentos Requeridos:**
- ✅ Política de Privacidad (`LEGAL/POLITICA_PRIVACIDAD.md`)
- ✅ Términos y Condiciones (`LEGAL/TERMINOS_Y_CONDICIONES.md`)
- ✅ Aviso Legal (`LEGAL/AVISO_LEGAL.md`)
- ✅ Aviso de Cookies (`LEGAL/AVISO_COOKIES.md`)

**Información del Desarrollador:**
- Nombre: Fernando Manuel Rubio
- Profesión: Ingeniero de Sistemas
- NIF: 75108544C
- Email: frubioviedma@gmail.com

**Alojamiento:**
1. Crear sitio web o usar servicio de alojamiento
2. Convertir documentos Markdown a HTML
3. Alojar en URLs accesibles
4. Añadir URLs en Play Console

**URLs Requeridas en Play Store:**
- Política de Privacidad: `https://tudominio.com/legal/privacidad`
- Términos y Condiciones: `https://tudominio.com/legal/terminos` (recomendado)

---

## Sistema de Actualizaciones

### Opción 1: Actualización Manual (Recomendado para Inicio)

La app verifica actualizaciones al iniciar:

```python
# En gui_moderna.py o main.py
def verificar_actualizacion(self):
    try:
        # URL donde está el APK más reciente
        url_version = "https://tudominio.com/api/version.json"
        response = requests.get(url_version, timeout=5)
        data = response.json()
        
        version_actual = "1.0.0"  # Desde buildozer.spec
        version_nueva = data.get('version', '1.0.0')
        
        if version_nueva > version_actual:
            self.mostrar_dialogo_actualizacion(data)
    except:
        pass  # Si falla, continuar sin actualizar
```

### Opción 2: Actualización Automática con Firebase

1. **Configurar Firebase Cloud Messaging (FCM)**

```python
# src/fcm_manager.py
from plyer import notification

class FCMManager:
    def __init__(self):
        self.fcm_token = None
    
    def inicializar(self):
        # Obtener token FCM
        pass
    
    def verificar_actualizacion_push(self):
        # Escuchar notificaciones de actualización
        pass
```

2. **Servidor de Actualizaciones**

Crear API simple que devuelva:
```json
{
  "version": "1.0.1",
  "url_apk": "https://tudominio.com/apk/quiniela-1.0.1.apk",
  "force_update": false,
  "mensaje": "Nueva versión disponible con mejoras"
}
```

### Opción 3: Actualización desde Play Store (Automática)

Si publicas en Play Store, las actualizaciones son automáticas:
- Play Store notifica a usuarios
- Actualización automática si está habilitada
- No requiere código adicional

---

## Notificaciones Push

### Configuración FCM

1. **Crear Proyecto Firebase**
   - Ir a https://console.firebase.google.com
   - Crear proyecto
   - Añadir app Android
   - Descargar `google-services.json`

2. **Configurar en Buildozer**

```ini
# buildozer.spec
android.gradle_dependencies = 
    com.google.firebase:firebase-messaging:23.0.0
    com.google.android.gms:play-services-ads:22.0.0
```

3. **Implementar en App**

```python
# src/notifications.py
from plyer import notification

class NotificationManager:
    def mostrar_notificacion(self, titulo, mensaje):
        notification.notify(
            title=titulo,
            message=mensaje,
            app_name="La quiniela 1X2"
        )
```

---

## Actualización Automática

### Implementar en la App

```python
# src/update_manager.py
import requests
import subprocess
from pathlib import Path

class UpdateManager:
    def __init__(self):
        self.version_url = "https://tudominio.com/api/version.json"
        self.current_version = "1.0.0"
    
    def verificar_actualizacion(self):
        try:
            response = requests.get(self.version_url, timeout=5)
            data = response.json()
            
            if data['version'] > self.current_version:
                return {
                    'hay_actualizacion': True,
                    'version': data['version'],
                    'url_apk': data['url_apk'],
                    'force': data.get('force_update', False),
                    'mensaje': data.get('mensaje', '')
                }
        except:
            pass
        
        return {'hay_actualizacion': False}
    
    def descargar_actualizacion(self, url_apk):
        # Descargar APK
        apk_path = Path("downloads") / "update.apk"
        response = requests.get(url_apk, stream=True)
        apk_path.write_bytes(response.content)
        
        # Instalar (requiere permisos)
        subprocess.run(["adb", "install", "-r", str(apk_path)])
```

### Diálogo de Actualización

```python
def mostrar_dialogo_actualizacion(self, info_actualizacion):
    from tkinter import messagebox
    
    mensaje = f"Nueva versión disponible: {info_actualizacion['version']}\n\n"
    mensaje += info_actualizacion.get('mensaje', '')
    
    if info_actualizacion.get('force', False):
        # Actualización forzada
        respuesta = messagebox.showwarning(
            "Actualización Requerida",
            mensaje + "\n\nDebes actualizar para continuar."
        )
        # Abrir URL de descarga
        webbrowser.open(info_actualizacion['url_apk'])
    else:
        # Actualización opcional
        respuesta = messagebox.askyesno(
            "Actualización Disponible",
            mensaje + "\n\n¿Deseas actualizar ahora?"
        )
        if respuesta:
            webbrowser.open(info_actualizacion['url_apk'])
```

---

## Checklist Pre-Deployment

- [ ] Modo admin desactivado
- [ ] Modo dev desactivado
- [ ] Versión actualizada en buildozer.spec
- [ ] Assets (logo, iconos) presentes
- [ ] PayPal configurado (sandbox desactivado)
- [ ] AdMob configurado
- [ ] APK firmado correctamente
- [ ] Probado en dispositivo real
- [ ] Política de privacidad creada
- [ ] Términos de servicio creados
- [ ] Screenshots preparados
- [ ] Descripción de Play Store lista

---

## Proceso de Actualización para Usuarios

### Actualización Manual

1. Usuario recibe notificación (si está implementado)
2. Usuario descarga nuevo APK
3. Instala sobre versión anterior (mantiene datos)

### Actualización desde Play Store

1. Play Store notifica automáticamente
2. Usuario acepta actualización
3. Descarga e instalación automática
4. Datos se mantienen

### Actualización Forzada

Si `force_update: true`:
- App muestra diálogo obligatorio
- Usuario debe actualizar para continuar
- Redirige a descarga

---

## Mantenimiento

### Versionado

Usar Semantic Versioning:
- **MAJOR.MINOR.PATCH** (ej: 1.0.0)
- MAJOR: Cambios incompatibles
- MINOR: Nuevas funcionalidades compatibles
- PATCH: Correcciones de bugs

### Logs de Versiones

Mantener `CHANGELOG.md`:
```markdown
# Changelog

## [1.0.1] - 2024-01-15
### Añadido
- Nuevas condiciones avanzadas
- Mejoras visuales

### Corregido
- Bug en reducción
- Error en carga de datos
```

---

## Contacto y Soporte

Para problemas de deployment:
- Revisar logs: `buildozer android logcat`
- Verificar permisos
- Comprobar configuración de red
- Revisar certificados y firmas

