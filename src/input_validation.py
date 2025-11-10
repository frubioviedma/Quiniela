"""
Módulo de validación y saneamiento de entradas de usuario
Protege contra XSS, SQLi, inyección de comandos y otros ataques
"""
import re
import logging
from typing import Any, Optional, List, Dict, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Excepción para errores de validación"""
    pass

class InputValidator:
    """Validador de entradas de usuario"""
    
    # Patrones peligrosos para SQL injection
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bor\b|\band\b)\s+\d+\s*=\s*\d+",
        r"('|;|\"|`|\\|%)",
    ]
    
    # Patrones peligrosos para XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    # Patrones peligrosos para path traversal
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"\.\.%2F",
        r"\.\.%5C",
    ]
    
    @staticmethod
    def sanitize_string(value: Any, max_length: int = 1000, allow_empty: bool = False) -> str:
        """
        Sanitizar string eliminando caracteres peligrosos
        
        Args:
            value: Valor a sanitizar
            max_length: Longitud máxima permitida
            allow_empty: Si True, permite strings vacíos
        
        Returns:
            String sanitizado
        
        Raises:
            ValidationError: Si la validación falla
        """
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError("Valor no puede ser None")
        
        # Convertir a string
        str_value = str(value).strip()
        
        # Verificar longitud
        if len(str_value) > max_length:
            raise ValidationError(f"String demasiado largo (máximo {max_length} caracteres)")
        
        if not allow_empty and len(str_value) == 0:
            raise ValidationError("String no puede estar vacío")
        
        # Eliminar caracteres de control (excepto \n, \r, \t)
        str_value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str_value)
        
        return str_value
    
    @staticmethod
    def validate_sql_safe(value: str, field_name: str = "campo") -> str:
        """
        Validar que un string es seguro para usar en consultas SQL (usar con parámetros)
        
        Args:
            value: String a validar
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            String validado
        
        Raises:
            ValidationError: Si contiene patrones peligrosos
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} debe ser un string")
        
        value_lower = value.lower()
        
        # Verificar patrones de SQL injection
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"⚠️ Intento de SQL injection detectado en {field_name}: {value[:50]}")
                raise ValidationError(f"{field_name} contiene caracteres no permitidos")
        
        return value
    
    @staticmethod
    def validate_xss_safe(value: str, field_name: str = "campo") -> str:
        """
        Validar que un string es seguro contra XSS
        
        Args:
            value: String a validar
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            String validado
        
        Raises:
            ValidationError: Si contiene patrones peligrosos
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} debe ser un string")
        
        # Verificar patrones de XSS
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"⚠️ Intento de XSS detectado en {field_name}: {value[:50]}")
                raise ValidationError(f"{field_name} contiene código peligroso")
        
        return value
    
    @staticmethod
    def validate_path_safe(value: Union[str, Path], field_name: str = "ruta") -> Path:
        """
        Validar que una ruta es segura (sin path traversal)
        
        Args:
            value: Ruta a validar
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Path validado
        
        Raises:
            ValidationError: Si contiene patrones peligrosos
        """
        path_str = str(value)
        
        # Verificar path traversal
        for pattern in InputValidator.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                logger.warning(f"⚠️ Intento de path traversal detectado en {field_name}: {path_str}")
                raise ValidationError(f"{field_name} contiene caracteres no permitidos")
        
        return Path(path_str)
    
    @staticmethod
    def validate_integer(value: Any, min_value: Optional[int] = None, 
                        max_value: Optional[int] = None, field_name: str = "número") -> int:
        """
        Validar y convertir a entero
        
        Args:
            value: Valor a validar
            min_value: Valor mínimo permitido
            max_value: Valor máximo permitido
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Entero validado
        
        Raises:
            ValidationError: Si la validación falla
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} debe ser un número entero")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} debe ser >= {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} debe ser <= {max_value}")
        
        return int_value
    
    @staticmethod
    def validate_float(value: Any, min_value: Optional[float] = None,
                      max_value: Optional[float] = None, field_name: str = "número") -> float:
        """
        Validar y convertir a float
        
        Args:
            value: Valor a validar
            min_value: Valor mínimo permitido
            max_value: Valor máximo permitido
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Float validado
        
        Raises:
            ValidationError: Si la validación falla
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} debe ser un número")
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name} debe ser >= {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name} debe ser <= {max_value}")
        
        return float_value
    
    @staticmethod
    def validate_quiniela_sign(value: Any, field_name: str = "signo") -> str:
        """
        Validar que un signo de quiniela es válido (1, X, 2)
        
        Args:
            value: Signo a validar
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Signo validado
        
        Raises:
            ValidationError: Si el signo no es válido
        """
        str_value = str(value).strip().upper()
        
        if str_value not in ['1', 'X', '2', '0', 'M']:
            raise ValidationError(f"{field_name} debe ser 1, X, 2, 0 o M (obtenido: {value})")
        
        return str_value
    
    @staticmethod
    def validate_quiniela_combination(value: Union[str, List[str]], 
                                      expected_length: int = 14,
                                      field_name: str = "combinación") -> str:
        """
        Validar una combinación de quiniela
        
        Args:
            value: Combinación como string o lista
            expected_length: Longitud esperada (default: 14 para quiniela estándar)
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Combinación validada como string
        
        Raises:
            ValidationError: Si la combinación no es válida
        """
        if isinstance(value, list):
            value = ''.join(str(v) for v in value)
        
        str_value = str(value).strip().upper()
        
        # Verificar longitud
        if len(str_value) != expected_length:
            raise ValidationError(
                f"{field_name} debe tener {expected_length} signos (obtenido: {len(str_value)})"
            )
        
        # Verificar que todos los caracteres son válidos
        valid_chars = set('1X2')
        for i, char in enumerate(str_value):
            if char not in valid_chars:
                raise ValidationError(
                    f"{field_name} contiene carácter inválido en posición {i+1}: '{char}' "
                    f"(debe ser 1, X o 2)"
                )
        
        return str_value
    
    @staticmethod
    def validate_list_of_integers(value: Any, min_value: Optional[int] = None,
                                  max_value: Optional[int] = None,
                                  max_length: Optional[int] = None,
                                  field_name: str = "lista") -> List[int]:
        """
        Validar una lista de enteros
        
        Args:
            value: Lista a validar
            min_value: Valor mínimo permitido para cada elemento
            max_value: Valor máximo permitido para cada elemento
            max_length: Longitud máxima de la lista
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Lista de enteros validada
        
        Raises:
            ValidationError: Si la validación falla
        """
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"{field_name} debe ser una lista")
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"{field_name} no puede tener más de {max_length} elementos")
        
        validated_list = []
        for i, item in enumerate(value):
            try:
                int_item = InputValidator.validate_integer(
                    item, min_value, max_value, f"{field_name}[{i}]"
                )
                validated_list.append(int_item)
            except ValidationError as e:
                raise ValidationError(f"Error en {field_name}[{i}]: {e}")
        
        return validated_list
    
    @staticmethod
    def validate_email(value: str, field_name: str = "email") -> str:
        """
        Validar formato de email
        
        Args:
            value: Email a validar
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            Email validado
        
        Raises:
            ValidationError: Si el email no es válido
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} debe ser un string")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError(f"{field_name} no tiene un formato de email válido")
        
        # Sanitizar contra XSS
        return InputValidator.validate_xss_safe(value, field_name)
    
    @staticmethod
    def validate_api_key(value: str, field_name: str = "API key") -> str:
        """
        Validar formato de API key (alfanumérico y guiones, longitud razonable)
        
        Args:
            value: API key a validar
            field_name: Nombre del campo para mensajes de error
        
        Returns:
            API key validada
        
        Raises:
            ValidationError: Si la API key no es válida
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} debe ser un string")
        
        value = value.strip()
        
        if len(value) == 0:
            return value  # API key vacía es válida (opcional)
        
        if len(value) < 10:
            raise ValidationError(f"{field_name} es demasiado corta (mínimo 10 caracteres)")
        
        if len(value) > 200:
            raise ValidationError(f"{field_name} es demasiado larga (máximo 200 caracteres)")
        
        # Solo caracteres alfanuméricos, guiones y guiones bajos
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError(
                f"{field_name} contiene caracteres no permitidos "
                "(solo letras, números, guiones y guiones bajos)"
            )
        
        return value

