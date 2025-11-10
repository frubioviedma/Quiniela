"""Sistema de anuncios para la aplicación freemium"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Optional
import webbrowser

from src.freemium import (
    FreemiumManager,
    PRECIO_SEMANAL,
    PRECIO_TEMPORADA,
    PRECIO_VIDA,
    PRECIO_BBDD_HISTORICA,
    PAYPAL_EMAIL,
    LICENCIA_SEMANAL,
    LICENCIA_TEMPORADA,
    LICENCIA_VIDA,
    LICENCIA_BBDD,
)

logger = logging.getLogger(__name__)

class AnuncioDialog:
    """Diálogo de anuncio publicitario"""
    
    def __init__(self, parent, paso: str, callback: Callable, freemium_manager: FreemiumManager):
        """
        Inicializar diálogo de anuncio
        
        Args:
            parent: Ventana padre
            paso: Nombre del paso que requiere premium/anuncio
            callback: Función a llamar si se permite acceso
            freemium_manager: Gestor freemium
        """
        self.parent = parent
        self.paso = paso
        self.callback = callback
        self.freemium_manager = freemium_manager
        self.resultado = False
        
        # Crear ventana de anuncio
        self.window = tk.Toplevel(parent)
        self.window.title("Anuncio Publicitario")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")
        
        self._crear_ui()
    
    def _crear_ui(self):
        """Crear interfaz del anuncio"""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(
            main_frame,
            text="Anuncio Publicitario",
            font=('Segoe UI', 16, 'bold')
        )
        titulo.pack(pady=(0, 10))
        
        # Mensaje
        mensaje = ttk.Label(
            main_frame,
            text="Para continuar, por favor visualiza este anuncio publicitario.\n"
                 "O bien, actualiza a Premium para disfrutar sin anuncios.",
            font=('Segoe UI', 10),
            justify=tk.CENTER
        )
        mensaje.pack(pady=10)
        
        # Área de anuncio (simulado)
        anuncio_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        anuncio_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        anuncio_text = ttk.Label(
            anuncio_frame,
            text="[ÁREA DE ANUNCIO PUBLICITARIO]\n\n"
                 "Aquí se mostraría un anuncio real\n"
                 "de nuestros patrocinadores.\n\n"
                 "Gracias por tu apoyo.",
            font=('Segoe UI', 12),
            justify=tk.CENTER,
            foreground='gray'
        )
        anuncio_text.pack(expand=True)
        
        # Botones
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill=tk.X, pady=10)
        
        # Botón "Ver Anuncio" (simulado - cuenta como visto)
        btn_ver = ttk.Button(
            botones_frame,
            text="✓ Anuncio Visto - Continuar",
            command=self._anuncio_visto,
            width=25
        )
        btn_ver.pack(side=tk.LEFT, padx=5)
        
        # Botón "Actualizar a Premium"
        btn_premium = ttk.Button(
            botones_frame,
            text="Actualizar a Premium",
            command=self._mostrar_premium,
            width=25
        )
        btn_premium.pack(side=tk.LEFT, padx=5)
        
        # Botón "Cancelar"
        btn_cancelar = ttk.Button(
            botones_frame,
            text="Cancelar",
            command=self._cancelar,
            width=15
        )
        btn_cancelar.pack(side=tk.RIGHT, padx=5)
    
    def _anuncio_visto(self):
        """Registrar que se ha visto el anuncio y continuar"""
        self.freemium_manager.registrar_anuncio_visto()
        self.resultado = True
        self.window.destroy()
        if self.callback:
            self.callback()
    
    def _mostrar_premium(self):
        """Mostrar opciones de premium"""
        self.window.destroy()
        PremiumDialog(self.parent, self.freemium_manager, self.callback)
    
    def _cancelar(self):
        """Cancelar operación"""
        self.resultado = False
        self.window.destroy()


class PremiumDialog:
    """Diálogo de opciones premium"""
    
    def __init__(self, parent, freemium_manager: FreemiumManager, callback: Optional[Callable] = None):
        """
        Inicializar diálogo premium
        
        Args:
            parent: Ventana padre
            freemium_manager: Gestor freemium
            callback: Función a llamar tras pago (opcional)
        """
        self.parent = parent
        self.freemium_manager = freemium_manager
        self.callback = callback
        
        # Crear ventana
        self.window = tk.Toplevel(parent)
        self.window.title("Actualizar a Premium")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"600x700+{x}+{y}")
        
        # Añadir fondo promocional si existe
        try:
            from src.promocional_manager import PromocionalManager
            from src.config import BASE_DIR
            promocional_mgr = PromocionalManager(BASE_DIR)
            promocional_mgr.crear_fondo_promocional(self.window)
        except Exception as e:
            logger.debug(f"No se pudo añadir fondo promocional: {e}")
        
        self._crear_ui()
    
    def _crear_ui(self):
        """Crear interfaz premium"""
        # Frame principal con scroll
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Banner de descuento
        descuento_frame = ttk.Frame(main_frame)
        descuento_frame.pack(fill=tk.X, pady=(0, 15))
        
        from src.freemium import DESCUENTO_PORCENTAJE
        descuento_label = ttk.Label(
            descuento_frame,
            text=f"🔥 OFERTA ESPECIAL: {int(DESCUENTO_PORCENTAJE * 100)}% DE DESCUENTO PERMANENTE 🔥",
            font=('Segoe UI', 14, 'bold'),
            foreground='#FF6B00'
        )
        descuento_label.pack(pady=10, padx=10)
        
        oferta_text = ttk.Label(
            descuento_frame,
            text="Aprovecha la oferta de la semana, un 20% si te haces premium ahora mismo\n"
                 "y acceso full a todas las opciones que te harán millonario",
            font=('Segoe UI', 10, 'italic'),
            justify=tk.CENTER,
            foreground='#E65100'
        )
        oferta_text.pack(pady=(0, 10))
        
        # Título
        titulo = ttk.Label(
            main_frame,
            text="La quiniela 1X2 - Premium",
            font=('Segoe UI', 18, 'bold')
        )
        titulo.pack(pady=(0, 10))
        
        # Descripción
        desc = ttk.Label(
            main_frame,
            text="Disfruta de todas las funcionalidades sin anuncios.\n"
                 "Elige el plan que mejor se adapte a ti:",
            font=('Segoe UI', 10),
            justify=tk.CENTER
        )
        desc.pack(pady=10)
        
        # Opción 1: Semanal
        self._crear_opcion_premium(
            main_frame,
            "Suscripción Semanal",
            f"{PRECIO_SEMANAL}€",
            "7 días de acceso premium",
            "semanal",
            "Ideal para probar"
        )
        
        # Opción 2: Temporada
        self._crear_opcion_premium(
            main_frame,
            "Suscripción Temporada",
            f"{PRECIO_TEMPORADA}€",
            "Toda la temporada de liga",
            "temporada",
            "Recomendado"
        )
        
        # Opción 3: Vida
        self._crear_opcion_premium(
            main_frame,
            "Licencia Vitalicia",
            f"{PRECIO_VIDA}€",
            "Acceso de por vida + BBDD histórica GRATIS",
            "vida",
            "Mejor valor"
        )
        
        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        # BBDD Histórica
        self._crear_opcion_premium(
            main_frame,
            "Base de Datos Histórica",
            f"{PRECIO_BBDD_HISTORICA}€",
            "Descarga completa de datos históricos\n(más de 100 años de datos)",
            "bbdd_historica",
            "Una sola vez"
        )
        
        # Información PayPal
        info_frame = ttk.LabelFrame(main_frame, text="Información de Pago", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        info_text = ttk.Label(
            info_frame,
            text=f"Pagos seguros vía PayPal\n"
                 f"Email: {PAYPAL_EMAIL}\n\n"
                 f"Tras realizar el pago, contacta con nosotros\n"
                 f"para activar tu licencia premium.",
            font=('Segoe UI', 9),
            justify=tk.CENTER
        )
        info_text.pack()
        
        # Herramientas de modo desarrollo
        if self.freemium_manager.esta_en_modo_desarrollo():
            dev_frame = ttk.LabelFrame(main_frame, text="Modo desarrollo (simulaciones)", padding=10)
            dev_frame.pack(fill=tk.X, pady=10)

            ttk.Label(
                dev_frame,
                text="Simula compras para probar el flujo sin realizar pagos reales.",
                font=('Segoe UI', 9),
                justify=tk.CENTER
            ).pack(pady=5)

            botones_dev = ttk.Frame(dev_frame)
            botones_dev.pack(pady=5)

            ttk.Button(
                botones_dev,
                text="Simular Semanal",
                command=lambda: self._simular_pago_dev(LICENCIA_SEMANAL),
                width=18
            ).pack(side=tk.LEFT, padx=3)

            ttk.Button(
                botones_dev,
                text="Simular Temporada",
                command=lambda: self._simular_pago_dev(LICENCIA_TEMPORADA),
                width=18
            ).pack(side=tk.LEFT, padx=3)

            ttk.Button(
                botones_dev,
                text="Simular Vitalicia",
                command=lambda: self._simular_pago_dev(LICENCIA_VIDA),
                width=18
            ).pack(side=tk.LEFT, padx=3)

            ttk.Button(
                dev_frame,
                text="Simular compra BBDD histórica",
                command=lambda: self._simular_pago_dev(LICENCIA_BBDD),
                width=28
            ).pack(pady=5)

            ttk.Button(
                dev_frame,
                text="Alternar modo desarrollo",
                command=self._toggle_dev_mode,
                width=28
            ).pack(pady=(5, 0))

        # Botón cerrar
        btn_cerrar = ttk.Button(
            main_frame,
            text="Cerrar",
            command=self.window.destroy,
            width=20
        )
        btn_cerrar.pack(pady=10)
        
        # Configurar scroll
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _crear_opcion_premium(self, parent, titulo: str, precio: str, descripcion: str, 
                             tipo: str, badge: str = None):
        """Crear opción de premium"""
        frame = ttk.LabelFrame(parent, text=titulo, padding=15)
        frame.pack(fill=tk.X, pady=10)
        
        # Badge si existe
        if badge:
            badge_label = ttk.Label(
                frame,
                text=badge,
                font=('Segoe UI', 9, 'bold'),
                foreground='white',
                background='#FF6B00',
                padding=(5, 2)
            )
            badge_label.pack(anchor='e', pady=(0, 5))
        
        # Precio destacado con descuento
        precio_frame = ttk.Frame(frame)
        precio_frame.pack(pady=5)
        
        from src.freemium import PRECIO_SEMANAL_ORIGINAL, PRECIO_TEMPORADA_ORIGINAL, PRECIO_VIDA_ORIGINAL, PRECIO_BBDD_HISTORICA_ORIGINAL
        
        precios_originales = {
            "semanal": PRECIO_SEMANAL_ORIGINAL,
            "temporada": PRECIO_TEMPORADA_ORIGINAL,
            "vida": PRECIO_VIDA_ORIGINAL,
            "bbdd_historica": PRECIO_BBDD_HISTORICA_ORIGINAL
        }
        
        precio_original = precios_originales.get(tipo, 0)
        if precio_original > 0:
            precio_antiguo_label = ttk.Label(
                precio_frame,
                text=f"{precio_original:.2f}€",
                font=('Segoe UI', 12),
                foreground='gray',
                style='Modern.TLabel'
            )
            precio_antiguo_label.pack(side=tk.LEFT, padx=5)
            # Tachar precio antiguo
            ttk.Label(
                precio_frame,
                text="~~",
                font=('Segoe UI', 12),
                foreground='gray'
            ).pack(side=tk.LEFT)
        
        precio_label = ttk.Label(
            precio_frame,
            text=precio,
            font=('Segoe UI', 20, 'bold'),
            foreground='#0078d4'
        )
        precio_label.pack()
        
        # Badge
        if badge:
            badge_label = ttk.Label(
                frame,
                text=badge,
                font=('Segoe UI', 8, 'italic'),
                foreground='#10b981'
            )
            badge_label.pack()
        
        # Descripción
        desc_label = ttk.Label(
            frame,
            text=descripcion,
            font=('Segoe UI', 9),
            justify=tk.CENTER
        )
        desc_label.pack(pady=5)
        
        # Botón pagar
        btn_pagar = ttk.Button(
            frame,
            text="Pagar con PayPal",
            command=lambda: self._abrir_paypal(tipo),
            width=20
        )
        btn_pagar.pack(pady=5)
    
    def _abrir_paypal(self, tipo_licencia: str):
        """Abrir enlace de PayPal"""
        enlace = self.freemium_manager.generar_enlace_pago(tipo_licencia)
        
        try:
            webbrowser.open(enlace)
            messagebox.showinfo(
                "Pago",
                f"Se ha abierto PayPal en tu navegador.\n\n"
                f"Tras realizar el pago de {self._obtener_precio(tipo_licencia)}€, "
                f"envía un email a {PAYPAL_EMAIL} con el comprobante de pago "
                f"para activar tu licencia premium."
            )
        except Exception as e:
            logger.error(f"Error abriendo PayPal: {e}")
            messagebox.showerror(
                "Error",
                f"No se pudo abrir PayPal.\n\n"
                f"Por favor, realiza el pago manualmente a:\n"
                f"{PAYPAL_EMAIL}\n\n"
                f"Importe: {self._obtener_precio(tipo_licencia)}€"
            )
    
    def _obtener_precio(self, tipo: str) -> float:
        """Obtener precio según tipo"""
        precios = {
            "semanal": PRECIO_SEMANAL,
            "temporada": PRECIO_TEMPORADA,
            "vida": PRECIO_VIDA,
            "bbdd_historica": PRECIO_BBDD_HISTORICA
        }
        return precios.get(tipo, 0)

    def _simular_pago_dev(self, tipo_licencia: str):
        """Simular pago en modo desarrollo"""
        self.freemium_manager.simular_pago(tipo_licencia)
        mensaje = "Simulación completada. Licencia aplicada (solo modo desarrollo)."
        if tipo_licencia == LICENCIA_BBDD:
            mensaje = "Simulación completada. BBDD histórica activada (modo desarrollo)."
        messagebox.showinfo("Simulación de pago", mensaje)
        if self.callback:
            self.callback()

    def _toggle_dev_mode(self):
        """Activar o desactivar modo desarrollo"""
        nuevo_estado = not self.freemium_manager.esta_en_modo_desarrollo()
        self.freemium_manager.configurar_modo_desarrollo(nuevo_estado)
        estado_texto = "activado" if nuevo_estado else "desactivado"
        messagebox.showinfo("Modo desarrollo", f"Modo desarrollo {estado_texto}. Reinicia la app para aplicar totalmente el cambio.")
        if self.callback:
            self.callback()


def verificar_acceso_premium(parent, paso: str, callback: Callable, 
                            freemium_manager: FreemiumManager) -> bool:
    """
    Verificar acceso premium y mostrar anuncio si es necesario
    
    Args:
        parent: Ventana padre
        paso: Nombre del paso
        callback: Función a llamar si se permite acceso
        freemium_manager: Gestor freemium
    
    Returns:
        True si tiene acceso (premium o tras anuncio)
    """
    # Verificar si es premium
    if freemium_manager.verificar_licencia():
        # Premium: acceso directo
        if callback:
            callback()
        return True
    
    # Verificar si el paso requiere premium
    if not freemium_manager.puede_acceder_paso(paso, mostrar_anuncio=False):
        # Paso no requiere premium
        if callback:
            callback()
        return True
    
    # Usuario gratis: mostrar anuncio
    AnuncioDialog(parent, paso, callback, freemium_manager)
    return False  # Se llamará callback desde el diálogo

