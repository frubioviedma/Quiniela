"""Sistema freemium para la aplicación Quiniela"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib

logger = logging.getLogger(__name__)

# Precios
PRECIO_SEMANAL = 2.99
PRECIO_TEMPORADA = 29.99
PRECIO_VIDA = 49.99
PRECIO_BBDD_HISTORICA = 5.99

# Email PayPal
PAYPAL_EMAIL = "frubioviedma@gmail.com"

# Tipos de licencia
LICENCIA_GRATIS = "gratis"
LICENCIA_SEMANAL = "semanal"
LICENCIA_TEMPORADA = "temporada"
LICENCIA_VIDA = "vida"
LICENCIA_BBDD = "bbdd_historica"

# Pasos que requieren premium o anuncio
PASOS_PREMIUM = [
    "descargar_quiniela",
    "crear_pronosticos",
    "generar_quiniela",
    "aplicar_condiciones",
    "aplicar_reduccion",
    "exportar_quinielas",
    "comparar_resultados",
    "descargar_bbdd_historica"
]

class FreemiumManager:
    """Gestor del sistema freemium"""
    
    def __init__(self, data_dir: Path = None):
        """
        Inicializar gestor freemium
        
        Args:
            data_dir: Directorio donde guardar datos de licencia
        """
        if data_dir is None:
            from src.config import DATA_DIR
            data_dir = DATA_DIR
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.license_file = self.data_dir / "licencia.json"
        self.license_data = self._load_license()
    
    def _load_license(self) -> Dict:
        """Cargar datos de licencia desde archivo"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando licencia: {e}")
                return self._create_default_license()
        return self._create_default_license()
    
    def _create_default_license(self) -> Dict:
        """Crear licencia por defecto (gratis)"""
        return {
            "tipo": LICENCIA_GRATIS,
            "fecha_inicio": datetime.now().isoformat(),
            "fecha_fin": None,
            "bbdd_historica": False,
            "anuncios_vistos": 0,
            "ultimo_anuncio": None
        }
    
    def _save_license(self):
        """Guardar datos de licencia en archivo"""
        try:
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(self.license_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando licencia: {e}")
    
    def verificar_licencia(self) -> bool:
        """
        Verificar si la licencia actual es válida
        
        Returns:
            True si tiene licencia premium válida
        """
        tipo = self.license_data.get("tipo", LICENCIA_GRATIS)
        
        if tipo == LICENCIA_GRATIS:
            return False
        
        if tipo == LICENCIA_VIDA:
            return True
        
        if tipo == LICENCIA_BBDD:
            # Solo verifica si tiene BBDD histórica, no es premium completo
            return False
        
        # Verificar fechas para semanal/temporada
        fecha_fin_str = self.license_data.get("fecha_fin")
        if not fecha_fin_str:
            return False
        
        try:
            fecha_fin = datetime.fromisoformat(fecha_fin_str)
            return datetime.now() < fecha_fin
        except Exception as e:
            logger.error(f"Error verificando fecha de licencia: {e}")
            return False
    
    def tiene_bbdd_historica(self) -> bool:
        """Verificar si tiene acceso a BBDD histórica"""
        return self.license_data.get("bbdd_historica", False)
    
    def registrar_pago(self, tipo_licencia: str, dias: int = None):
        """
        Registrar un pago y activar licencia
        
        Args:
            tipo_licencia: Tipo de licencia (semanal, temporada, vida, bbdd_historica)
            dias: Días de duración (solo para semanal/temporada)
        """
        fecha_inicio = datetime.now()
        
        if tipo_licencia == LICENCIA_SEMANAL:
            fecha_fin = fecha_inicio + timedelta(days=7)
        elif tipo_licencia == LICENCIA_TEMPORADA:
            # Temporada de liga: aproximadamente 9 meses (270 días)
            fecha_fin = fecha_inicio + timedelta(days=270)
        elif tipo_licencia == LICENCIA_VIDA:
            fecha_fin = None  # Sin fecha de fin
        elif tipo_licencia == LICENCIA_BBDD:
            # Solo activa BBDD histórica, no cambia tipo de licencia
            self.license_data["bbdd_historica"] = True
            self._save_license()
            return
        else:
            logger.error(f"Tipo de licencia no válido: {tipo_licencia}")
            return
        
        self.license_data["tipo"] = tipo_licencia
        self.license_data["fecha_inicio"] = fecha_inicio.isoformat()
        self.license_data["fecha_fin"] = fecha_fin.isoformat() if fecha_fin else None
        self._save_license()
        logger.info(f"Licencia {tipo_licencia} activada hasta {fecha_fin}")
    
    def registrar_anuncio_visto(self):
        """Registrar que se ha visto un anuncio"""
        self.license_data["anuncios_vistos"] = self.license_data.get("anuncios_vistos", 0) + 1
        self.license_data["ultimo_anuncio"] = datetime.now().isoformat()
        self._save_license()
    
    def puede_acceder_paso(self, paso: str, mostrar_anuncio: bool = True) -> bool:
        """
        Verificar si puede acceder a un paso específico
        
        Args:
            paso: Nombre del paso (ej: "descargar_quiniela")
            mostrar_anuncio: Si True, permite acceso tras ver anuncio
        
        Returns:
            True si puede acceder (premium o tras anuncio)
        """
        if self.verificar_licencia():
            return True  # Premium: acceso directo
        
        if paso not in PASOS_PREMIUM:
            return True  # Paso no requiere premium
        
        # Usuario gratis: requiere anuncio o pago
        if mostrar_anuncio:
            # Permitir acceso tras ver anuncio
            return True
        
        return False
    
    def obtener_info_licencia(self) -> Dict:
        """Obtener información de la licencia actual"""
        tipo = self.license_data.get("tipo", LICENCIA_GRATIS)
        fecha_fin_str = self.license_data.get("fecha_fin")
        
        info = {
            "tipo": tipo,
            "es_premium": self.verificar_licencia(),
            "tiene_bbdd": self.tiene_bbdd_historica(),
            "anuncios_vistos": self.license_data.get("anuncios_vistos", 0)
        }
        
        if fecha_fin_str:
            try:
                fecha_fin = datetime.fromisoformat(fecha_fin_str)
                info["fecha_fin"] = fecha_fin
                info["dias_restantes"] = (fecha_fin - datetime.now()).days
            except:
                info["fecha_fin"] = None
                info["dias_restantes"] = None
        else:
            info["fecha_fin"] = None
            info["dias_restantes"] = None
        
        return info
    
    def generar_enlace_pago(self, tipo_licencia: str) -> str:
        """
        Generar enlace de pago PayPal
        
        Args:
            tipo_licencia: Tipo de licencia (semanal, temporada, vida, bbdd_historica)
        
        Returns:
            URL de PayPal para pago
        """
        precios = {
            LICENCIA_SEMANAL: PRECIO_SEMANAL,
            LICENCIA_TEMPORADA: PRECIO_TEMPORADA,
            LICENCIA_VIDA: PRECIO_VIDA,
            LICENCIA_BBDD: PRECIO_BBDD_HISTORICA
        }
        
        precio = precios.get(tipo_licencia, 0)
        
        # Generar URL de PayPal (formato simplificado)
        # En producción, usar PayPal API o enlace de pago real
        descripcion = {
            LICENCIA_SEMANAL: "Suscripción Semanal Quiniela Premium",
            LICENCIA_TEMPORADA: "Suscripción Temporada Quiniela Premium",
            LICENCIA_VIDA: "Licencia Vitalicia Quiniela Premium",
            LICENCIA_BBDD: "Base de Datos Histórica Completa"
        }.get(tipo_licencia, "Pago Quiniela")
        
        # URL de PayPal (formato para envío de dinero)
        # En producción, usar PayPal Buttons o API
        url = f"https://www.paypal.com/paypalme/frubioviedma/{precio}EUR"
        
        # Alternativa: usar PayPal.me con descripción
        # url = f"https://paypal.me/frubioviedma/{precio}EUR?locale.x=es_ES"
        
        return url

