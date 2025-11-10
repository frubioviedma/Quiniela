"""
Gestor de sonidos para la aplicación
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Intentar importar pygame para sonidos
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame no disponible - los sonidos estarán deshabilitados")


class SoundManager:
    """Gestor de sonidos de la aplicación"""
    
    def __init__(self, base_dir: Path = None):
        """
        Inicializar gestor de sonidos
        
        Args:
            base_dir: Directorio base de la aplicación
        """
        if base_dir is None:
            from src.config import BASE_DIR
            base_dir = BASE_DIR
        
        self.base_dir = Path(base_dir)
        self.sounds_dir = self.base_dir / "assets" / "sounds"
        self.enabled = PYGAME_AVAILABLE
        
        if self.enabled:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.enabled = True
            except Exception as e:
                logger.warning(f"No se pudo inicializar pygame.mixer: {e}")
                self.enabled = False
        
        # Cargar sonidos
        self.sounds = {}
        self._load_sounds()
    
    def _load_sounds(self):
        """Cargar archivos de sonido"""
        if not self.enabled:
            return
        
        sound_files = {
            'click': 'click.wav',
            'success': 'success.wav',
            'error': 'error.wav',
            'hover': 'hover.wav'  # Opcional
        }
        
        for name, filename in sound_files.items():
            sound_path = self.sounds_dir / filename
            if sound_path.exists():
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(sound_path))
                    logger.debug(f"Sonido cargado: {name}")
                except Exception as e:
                    logger.warning(f"No se pudo cargar sonido {name}: {e}")
            else:
                logger.debug(f"Sonido no encontrado: {sound_path}")
    
    def play(self, sound_name: str):
        """
        Reproducir un sonido
        
        Args:
            sound_name: Nombre del sonido ('click', 'success', 'error', 'hover')
        """
        if not self.enabled:
            return
        
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                logger.warning(f"Error reproduciendo sonido {sound_name}: {e}")
    
    def play_click(self):
        """Reproducir sonido de click"""
        self.play('click')
    
    def play_success(self):
        """Reproducir sonido de éxito"""
        self.play('success')
    
    def play_error(self):
        """Reproducir sonido de error"""
        self.play('error')
    
    def play_hover(self):
        """Reproducir sonido de hover (opcional)"""
        self.play('hover')


# Instancia global
_sound_manager: Optional[SoundManager] = None

def get_sound_manager(base_dir: Path = None) -> SoundManager:
    """Obtener instancia global del gestor de sonidos"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager(base_dir)
    return _sound_manager

