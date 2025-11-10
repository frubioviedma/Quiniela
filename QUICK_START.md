# Quick Start - La quiniela 1X2

## 🚀 Inicio Rápido

### 1. Preparar Assets

```bash
# Crear directorios
mkdir assets
mkdir assets\sounds

# Colocar tu logo como:
# assets/logo.png (200x200px recomendado)
# assets/logo_small.png (64x64px para iconos)
# assets/logo_icon.png (512x512px para Play Store)
```

### 2. Configurar Modo Admin (Opcional)

```powershell
# Windows PowerShell
$env:QUINIELA_ADMIN_MODE="1"

# Para desactivar
$env:QUINIELA_ADMIN_MODE="0"
```

### 3. Ejecutar App

```bash
# Windows
python gui_moderna.py

# O usar script
.\run_app.ps1
```

### 4. Generar APK

```bash
# Verificar buildozer.spec
# Asegurarse de que versión está actualizada

# Generar APK debug (pruebas)
buildozer android debug

# Generar APK release (producción)
buildozer android release
```

## 📋 Checklist Pre-Deployment

- [ ] Logo colocado en `assets/logo.png`
- [ ] Modo admin desactivado
- [ ] Versión actualizada en `buildozer.spec`
- [ ] PayPal configurado
- [ ] AdMob configurado
- [ ] Probado en dispositivo real
- [ ] APK firmado

## 📚 Documentación Completa

- **Deployment**: Ver `DEPLOYMENT_GUIDE.md`
- **Logo**: Ver `LOGO_CONFIG.md`
- **PayPal**: Ver `PAYPAL_CONFIG.md`
- **Admin Mode**: Ver `ADMIN_MODE.md`
- **Play Store**: Ver `PLAY_STORE_CHECKLIST.md`

