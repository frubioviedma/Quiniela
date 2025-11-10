"""
Gestor de banners y popups promocionales con imágenes
"""
import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class PromocionalManager:
    """Gestor de banners y popups promocionales"""
    
    def __init__(self, base_dir: Path = None):
        """
        Inicializar gestor promocional
        
        Args:
            base_dir: Directorio base de la aplicación
        """
        if base_dir is None:
            from src.config import BASE_DIR
            base_dir = BASE_DIR
        
        self.base_dir = Path(base_dir)
        self.imagen_promocional = self.base_dir / "assets" / "promocional.png"
        self.imagen_promocional_vip = self.base_dir / "assets" / "promocional_vip.png"
        self.imagen_fondo = self.base_dir / "assets" / "fondo_promocional.png"
        
        # Verificar si existen imágenes
        self.tiene_imagen_promocional = self.imagen_promocional.exists()
        self.tiene_imagen_vip = self.imagen_promocional_vip.exists()
        self.tiene_imagen_fondo = self.imagen_fondo.exists()
    
    def crear_banner_premium(self, parent, callback: Optional[Callable] = None) -> Optional[ttk.Frame]:
        """
        Crear banner promocional premium
        
        Args:
            parent: Widget padre
            callback: Función a llamar al hacer click
        
        Returns:
            Frame con banner o None si no hay imagen
        """
        if not self.tiene_imagen_promocional:
            return None
        
        try:
            from PIL import Image, ImageTk
            
            banner_frame = ttk.Frame(parent, style='Surface.TFrame')
            
            # Cargar y redimensionar imagen
            img = Image.open(self.imagen_promocional)
            # Ancho máximo: 800px, mantener aspecto
            max_width = 800
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            # Label con imagen
            img_label = ttk.Label(banner_frame, image=photo, cursor='hand2')
            img_label.image = photo  # Mantener referencia
            img_label.pack()
            
            # Bind click
            if callback:
                img_label.bind('<Button-1>', lambda e: callback())
                banner_frame.bind('<Button-1>', lambda e: callback())
            
            return banner_frame
            
        except Exception as e:
            logger.warning(f"No se pudo cargar imagen promocional: {e}")
            return None
    
    def crear_popup_vip(self, parent, callback: Optional[Callable] = None):
        """
        Crear popup de invitación VIP
        
        Args:
            parent: Widget padre
            callback: Función a llamar al hacer click en "Hacerme VIP"
        """
        popup = tk.Toplevel(parent)
        popup.title("¡Hazte Premium/VIP!")
        popup.geometry("600x700")
        popup.resizable(False, False)
        popup.transient(parent)
        popup.grab_set()
        
        # Centrar ventana
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (600 // 2)
        y = (popup.winfo_screenheight() // 2) - (700 // 2)
        popup.geometry(f"600x700+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(popup, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Imagen promocional VIP
        if self.tiene_imagen_vip:
            try:
                from PIL import Image, ImageTk
                img = Image.open(self.imagen_promocional_vip)
                img = img.resize((580, 400), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_label = ttk.Label(main_frame, image=photo)
                img_label.image = photo
                img_label.pack(pady=10)
            except Exception as e:
                logger.warning(f"No se pudo cargar imagen VIP: {e}")
        
        # Texto promocional
        texto_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        texto_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            texto_frame,
            text="🔥 OFERTA ESPECIAL: 20% DE DESCUENTO 🔥",
            font=('Segoe UI', 16, 'bold'),
            foreground='#FF6B00',
            style='Modern.TLabel'
        ).pack(pady=5)
        
        ttk.Label(
            texto_frame,
            text="Aprovecha la oferta de la semana, un 20% si te haces premium ahora mismo\n"
                 "y acceso full a todas las opciones que te harán millonario",
            font=('Segoe UI', 11),
            style='Modern.TLabel',
            justify=tk.CENTER
        ).pack(pady=10)
        
        # Botones
        btn_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        btn_frame.pack(pady=20)
        
        if callback:
            from gui_moderna import ModernButton, COLOR_PREMIUM
            btn_vip = ModernButton(
                btn_frame,
                "⭐ Hacerme Premium/VIP",
                command=lambda: (callback(), popup.destroy()),
                bg=COLOR_PREMIUM,
                fg="#000000",
                width=300,
                height=50
            )
            btn_vip.pack(pady=10)
        
        btn_cerrar = ttk.Button(
            btn_frame,
            text="Quizá más tarde",
            command=popup.destroy,
            width=20
        )
        btn_cerrar.pack(pady=5)
        
        return popup
    
    def crear_fondo_promocional(self, parent) -> Optional[tk.Label]:
        """
        Crear fondo promocional para diálogos
        
        Args:
            parent: Widget padre
        
        Returns:
            Label con fondo o None
        """
        if not self.tiene_imagen_fondo:
            return None
        
        try:
            from PIL import Image, ImageTk
            
            # Cargar imagen de fondo
            img = Image.open(self.imagen_fondo)
            # Redimensionar al tamaño del parent
            parent.update_idletasks()
            width = parent.winfo_width() or 800
            height = parent.winfo_height() or 600
            
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Label de fondo
            bg_label = tk.Label(parent, image=photo)
            bg_label.image = photo
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()  # Enviar al fondo
            
            return bg_label
            
        except Exception as e:
            logger.warning(f"No se pudo cargar imagen de fondo: {e}")
            return None
    
    def usar_imagen_como_icono(self) -> Optional[Path]:
        """
        Obtener ruta de imagen para usar como icono
        
        Returns:
            Path de imagen o None
        """
        # Prioridad: logo.png > promocional.png
        logo_path = self.base_dir / "assets" / "logo.png"
        if logo_path.exists():
            return logo_path
        
        if self.tiene_imagen_promocional:
            return self.imagen_promocional
        
        return None

