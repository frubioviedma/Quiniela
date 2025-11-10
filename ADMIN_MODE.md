# Modo Admin - Bypass de Bloqueos Premium

## ¿Qué es el Modo Admin?

El modo admin permite al desarrollador/admin usar todas las funcionalidades premium sin restricciones, sin necesidad de pagar o ver anuncios.

## Cómo Activar Modo Admin

### Opción 1: Variable de Entorno

```bash
# Windows PowerShell
$env:QUINIELA_ADMIN_MODE="1"

# Linux/Mac
export QUINIELA_ADMIN_MODE=1
```

### Opción 2: Archivo .env

Crear archivo `.env` en la raíz del proyecto:

```
QUINIELA_ADMIN_MODE=1
```

### Opción 3: Editar Código (No recomendado)

Editar `src/config_paypal.py`:

```python
ADMIN_MODE = True
```

## Funcionalidades con Bypass

Cuando el modo admin está activo:
- ✅ Acceso a todas las condiciones avanzadas
- ✅ Reducción sin anuncios
- ✅ Sin anuncios entre pestañas
- ✅ Acceso a BBDD histórica
- ✅ Todas las funciones premium desbloqueadas

## Verificación

El modo admin se verifica en:
- `src/freemium.py`: `verificar_licencia()` y `puede_acceder_paso()`
- `src/admob_manager.py`: `mostrar_anuncio_intersticial()` y `mostrar_anuncio_recompensado()`

## ⚠️ IMPORTANTE PARA PRODUCCIÓN

**NO incluir modo admin activado en la versión de producción para Play Store.**

Antes de generar el APK final:
1. Verificar que `ADMIN_MODE = False` en `src/config_paypal.py`
2. O asegurarse de que `QUINIELA_ADMIN_MODE` no esté configurado
3. Probar que los bloqueos funcionan correctamente

## Logs

Cuando el modo admin está activo, verás en los logs:
```
🔓 Modo admin activo: acceso premium completo
🔓 Modo admin: anuncio intersticial omitido
```

