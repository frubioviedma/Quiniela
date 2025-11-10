"""
Gestor de actualizaciones para la aplicación
"""
import requests
import logging
import json
from pathlib import Path
from typing import Optional, Dict
import webbrowser

logger = logging.getLogger(__name__)


class UpdateManager:
    """Gestor de actualizaciones de la aplicación"""
    
    def __init__(self, current_version: str = "1.0.0", version_url: str = None):
        """
        Inicializar gestor de actualizaciones
        
        Args:
            current_version: Versión actual de la app
            version_url: URL donde verificar versiones (opcional)
        """
        self.current_version = current_version
        self.version_url = version_url or "https://tudominio.com/api/version.json"
        self.check_interval = 86400  # 24 horas
    
    def verificar_actualizacion(self) -> Optional[Dict]:
        """
        Verificar si hay actualización disponible
        
        Returns:
            Dict con info de actualización o None
        """
        try:
            response = requests.get(self.version_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            version_nueva = data.get('version', '0.0.0')
            
            if self._comparar_versiones(version_nueva, self.current_version) > 0:
                return {
                    'hay_actualizacion': True,
                    'version': version_nueva,
                    'url_apk': data.get('url_apk', ''),
                    'force': data.get('force_update', False),
                    'mensaje': data.get('mensaje', 'Nueva versión disponible'),
                    'changelog': data.get('changelog', [])
                }
        except requests.exceptions.RequestException as e:
            logger.debug(f"Error verificando actualización: {e}")
        except Exception as e:
            logger.error(f"Error inesperado verificando actualización: {e}")
        
        return None
    
    def _comparar_versiones(self, v1: str, v2: str) -> int:
        """
        Comparar dos versiones (formato: MAJOR.MINOR.PATCH)
        
        Returns:
            >0 si v1 > v2, <0 si v1 < v2, 0 si iguales
        """
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        try:
            return (version_tuple(v1) > version_tuple(v2)) - (version_tuple(v1) < version_tuple(v2))
        except:
            return 0
    
    def mostrar_dialogo_actualizacion(self, parent, info_actualizacion: Dict):
        """
        Mostrar diálogo de actualización
        
        Args:
            parent: Ventana padre
            info_actualizacion: Info de la actualización
        """
        from tkinter import messagebox
        
        mensaje = f"🆕 Nueva versión disponible: {info_actualizacion['version']}\n\n"
        mensaje += info_actualizacion.get('mensaje', '')
        
        if info_actualizacion.get('changelog'):
            mensaje += "\n\nCambios:\n"
            for cambio in info_actualizacion['changelog'][:5]:  # Máximo 5
                mensaje += f"• {cambio}\n"
        
        if info_actualizacion.get('force', False):
            # Actualización forzada
            respuesta = messagebox.showwarning(
                "Actualización Requerida",
                mensaje + "\n\nDebes actualizar para continuar usando la aplicación."
            )
            # Abrir URL de descarga
            if info_actualizacion.get('url_apk'):
                webbrowser.open(info_actualizacion['url_apk'])
        else:
            # Actualización opcional
            respuesta = messagebox.askyesno(
                "Actualización Disponible",
                mensaje + "\n\n¿Deseas actualizar ahora?"
            )
            if respuesta and info_actualizacion.get('url_apk'):
                webbrowser.open(info_actualizacion['url_apk'])

