# Configuración de AdMob para APK Android

## Requisitos Previos

1. **Cuenta de Google AdMob**: Crear cuenta en https://admob.google.com
2. **App ID de AdMob**: Obtener el App ID desde el panel de AdMob
3. **Unit IDs**: Crear unidades de anuncios (Banner, Interstitial, Rewarded)

## Configuración en Buildozer

### 1. Actualizar `buildozer.spec`

```ini
[app]
# ... otras configuraciones ...

requirements = python3,kivy,requests,beautifulsoup4,plyer

# Añadir permisos de Internet (ya debería estar)
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Añadir dependencias de Google Play Services para AdMob
android.gradle_dependencies = 
    com.google.android.gms:play-services-ads:22.0.0

# Configurar App ID de AdMob
android.meta_data = 
    com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX
```

### 2. Instalar Plyer para AdMob

Plyer es necesario para mostrar anuncios en Kivy:

```bash
pip install plyer
```

## Integración en el Código

### 1. Crear módulo de AdMob (`src/admob.py`)

```python
"""
Integración con AdMob para Android
"""
import os
from plyer import notification
import logging

logger = logging.getLogger(__name__)

# App ID de AdMob (reemplazar con el real)
ADMOB_APP_ID = "ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX"

# Unit IDs (reemplazar con los reales)
BANNER_AD_UNIT_ID = "ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX"
INTERSTITIAL_AD_UNIT_ID = "ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX"
REWARDED_AD_UNIT_ID = "ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX"

def mostrar_anuncio_intersticial():
    """
    Mostrar anuncio intersticial (pantalla completa)
    Se muestra entre cambios de pestaña o acciones premium
    """
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        
        # Verificar si estamos en Android
        if os.environ.get('KIVY_BUILD') != 'android':
            logger.info("No en Android, simulando anuncio")
            return True
        
        # Cargar clases de AdMob
        InterstitialAd = autoclass('com.google.android.gms.ads.InterstitialAd')
        AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
        AdRequestBuilder = autoclass('com.google.android.gms.ads.AdRequest$Builder')
        
        # Crear anuncio intersticial
        interstitial_ad = InterstitialAd(activity)
        interstitial_ad.setAdUnitId(INTERSTITIAL_AD_UNIT_ID)
        
        # Cargar anuncio
        ad_request = AdRequestBuilder().build()
        interstitial_ad.loadAd(ad_request)
        
        # Mostrar cuando esté listo
        if interstitial_ad.isLoaded():
            interstitial_ad.show()
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error mostrando anuncio: {e}")
        return False

def mostrar_anuncio_recompensado(callback):
    """
    Mostrar anuncio recompensado (el usuario obtiene recompensa al verlo)
    
    Args:
        callback: Función a llamar cuando el usuario complete el anuncio
    """
    try:
        from jnius import autoclass
        
        if os.environ.get('KIVY_BUILD') != 'android':
            logger.info("No en Android, simulando anuncio recompensado")
            if callback:
                callback()
            return True
        
        RewardedAd = autoclass('com.google.android.gms.ads.rewarded.RewardedAd')
        AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
        
        # Implementar callback de recompensa
        # ... (código específico de AdMob)
        
        return True
    except Exception as e:
        logger.error(f"Error mostrando anuncio recompensado: {e}")
        return False
```

### 2. Integrar en `gui_moderna.py`

```python
def _on_tab_changed(self, event=None):
    """Interceptar cambios de pestaña para mostrar publicidad"""
    try:
        selected = self.notebook.index(self.notebook.select())
        if selected > 0:  # No mostrar en primera pestaña
            if not self.freemium_manager.verificar_licencia():
                # Mostrar anuncio AdMob
                from src.admob import mostrar_anuncio_intersticial
                mostrar_anuncio_intersticial()
    except Exception as e:
        logger.error(f"Error en cambio de pestaña: {e}")
```

## Pasos para Configurar AdMob

### 1. Crear App en AdMob

1. Ir a https://admob.google.com
2. Crear nueva app: "Quiniela Pro"
3. Seleccionar plataforma: Android
4. Copiar el **App ID** (formato: `ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX`)

### 2. Crear Unidades de Anuncios

#### Banner Ad (opcional, para mostrar en la parte inferior)
- Tipo: Banner
- Nombre: "Quiniela Banner"
- Copiar **Unit ID**

#### Interstitial Ad (para cambios de pestaña)
- Tipo: Interstitial
- Nombre: "Quiniela Interstitial"
- Copiar **Unit ID**

#### Rewarded Ad (para acciones premium)
- Tipo: Rewarded
- Nombre: "Quiniela Rewarded"
- Copiar **Unit ID**

### 3. Configurar en buildozer.spec

Reemplazar los placeholders con los IDs reales:

```ini
android.meta_data = 
    com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-TU_APP_ID_AQUI~TU_APP_ID_AQUI
```

### 4. Actualizar código con Unit IDs

En `src/admob.py`, reemplazar:
- `BANNER_AD_UNIT_ID`
- `INTERSTITIAL_AD_UNIT_ID`
- `REWARDED_AD_UNIT_ID`

## Testing

### Modo de Prueba

AdMob proporciona IDs de prueba:

```python
# IDs de prueba (solo para desarrollo)
TEST_INTERSTITIAL_AD_UNIT_ID = "ca-app-pub-3940256099942544/1033173712"
TEST_REWARDED_AD_UNIT_ID = "ca-app-pub-3940256099942544/5224354917"
```

Usar estos IDs durante el desarrollo y cambiar a los reales antes de publicar.

## Notas Importantes

1. **Política de AdMob**: Asegurarse de cumplir las políticas de AdMob
2. **Límites de anuncios**: No mostrar demasiados anuncios seguidos
3. **Experiencia de usuario**: Los anuncios no deben bloquear el uso básico
4. **Monetización**: Los anuncios deben ser relevantes y no intrusivos

## Alternativa: Mock de Anuncios (Desarrollo)

Para desarrollo sin AdMob real, usar mock:

```python
def mostrar_anuncio_intersticial():
    """Mock de anuncio para desarrollo"""
    if os.environ.get('QUINIELA_DEV_MODE') == '1':
        # En desarrollo, solo mostrar diálogo
        messagebox.showinfo("Anuncio (Mock)", 
            "Aquí se mostraría un anuncio de AdMob.\n"
            "En producción, se mostraría el anuncio real.")
        return True
    # En producción, usar AdMob real
    # ... código de AdMob ...
```

## Referencias

- [Documentación de AdMob](https://developers.google.com/admob/android/quick-start)
- [Kivy + AdMob](https://kivy.org/doc/stable/guide/android.html)
- [Plyer Documentation](https://plyer.readthedocs.io/)

