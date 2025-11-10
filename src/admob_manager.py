"""
Gestor de AdMob con modo admin para bypass
"""
import os
import logging
from typing import Callable, Optional

from src.config_paypal import ADMIN_MODE, ADMOB_APP_ID, ADMOB_INTERSTITIAL_UNIT_ID, ADMOB_REWARDED_UNIT_ID

logger = logging.getLogger(__name__)


class AdMobManager:
    """Gestor de anuncios AdMob con modo admin"""
    
    def __init__(self):
        self.is_android = os.environ.get('KIVY_BUILD') == 'android'
        self.admin_mode = ADMIN_MODE
        self.anuncios_mostrados = 0
    
    def mostrar_anuncio_intersticial(self, callback: Optional[Callable] = None) -> bool:
        """
        Mostrar anuncio intersticial (pantalla completa)
        
        Args:
            callback: Función a llamar cuando se cierre el anuncio
        
        Returns:
            True si se mostró (o se simuló en admin mode)
        """
        # Modo admin: bypass completo
        if self.admin_mode:
            logger.info("🔓 Modo admin: anuncio intersticial omitido")
            if callback:
                callback()
            return True
        
        # Modo desarrollo: simular
        if os.environ.get('QUINIELA_DEV_MODE') == '1':
            logger.info("🔧 Modo desarrollo: anuncio intersticial simulado")
            if callback:
                callback()
            return True
        
        # Android: mostrar anuncio real
        if self.is_android:
            try:
                from jnius import autoclass, PythonJavaClass, java_method
                
                InterstitialAd = autoclass('com.google.android.gms.ads.InterstitialAd')
                AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
                AdRequestBuilder = autoclass('com.google.android.gms.ads.AdRequest$Builder')
                
                # Obtener actividad actual
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                
                # Crear anuncio
                interstitial_ad = InterstitialAd(activity)
                interstitial_ad.setAdUnitId(ADMOB_INTERSTITIAL_UNIT_ID)
                
                # Listener para cuando se cierra
                class AdListener(PythonJavaClass):
                    __javainterfaces__ = ['com/google/android/gms/ads/AdListener']
                    
                    def __init__(self, callback):
                        super().__init__()
                        self.callback = callback
                    
                    @java_method('()V')
                    def onAdClosed(self):
                        if self.callback:
                            self.callback()
                
                listener = AdListener(callback)
                interstitial_ad.setAdListener(listener)
                
                # Cargar y mostrar
                ad_request = AdRequestBuilder().build()
                interstitial_ad.loadAd(ad_request)
                
                if interstitial_ad.isLoaded():
                    interstitial_ad.show()
                    self.anuncios_mostrados += 1
                    return True
                
                # Si no está cargado, llamar callback de todas formas
                if callback:
                    callback()
                return False
                
            except Exception as e:
                logger.error(f"Error mostrando anuncio AdMob: {e}")
                # Fallback: llamar callback
                if callback:
                    callback()
                return False
        
        # Desktop: simular
        logger.info("🖥️ Desktop: anuncio intersticial simulado")
        if callback:
            callback()
        return True
    
    def mostrar_anuncio_recompensado(self, callback: Optional[Callable] = None) -> bool:
        """
        Mostrar anuncio recompensado
        
        Args:
            callback: Función a llamar cuando el usuario complete el anuncio
        
        Returns:
            True si se mostró (o se simuló)
        """
        # Modo admin: bypass
        if self.admin_mode:
            logger.info("🔓 Modo admin: anuncio recompensado omitido")
            if callback:
                callback()
            return True
        
        # Modo desarrollo: simular
        if os.environ.get('QUINIELA_DEV_MODE') == '1':
            logger.info("🔧 Modo desarrollo: anuncio recompensado simulado")
            if callback:
                callback()
            return True
        
        # Android: mostrar anuncio real
        if self.is_android:
            try:
                from jnius import autoclass
                
                RewardedAd = autoclass('com.google.android.gms.ads.rewarded.RewardedAd')
                AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
                
                # Implementar callback de recompensa
                # ... (código específico de AdMob Rewarded)
                
                if callback:
                    callback()
                return True
                
            except Exception as e:
                logger.error(f"Error mostrando anuncio recompensado: {e}")
                if callback:
                    callback()
                return False
        
        # Desktop: simular
        if callback:
            callback()
        return True
    
    def puede_mostrar_anuncio(self) -> bool:
        """Verificar si se puede mostrar anuncio (no en modo admin)"""
        return not self.admin_mode


# Instancia global
admob_manager = AdMobManager()

