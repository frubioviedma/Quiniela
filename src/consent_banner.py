"""
Banner de consentimientos RGPD - Primera ejecución
Muestra consentimientos para cookies, publicidad y datos personales
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ConsentBanner:
    """Banner de consentimientos RGPD"""
    
    def __init__(self, data_dir: Path = None):
        """
        Inicializar banner de consentimientos
        
        Args:
            data_dir: Directorio donde guardar consentimientos
        """
        if data_dir is None:
            from src.config import DATA_DIR
            data_dir = DATA_DIR
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.consent_file = self.data_dir / "consentimientos.json"
        self.consent_data = self._load_consents()
    
    def _load_consents(self) -> Dict:
        """Cargar consentimientos guardados"""
        if self.consent_file.exists():
            try:
                with open(self.consent_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando consentimientos: {e}")
                return {}
        return {}
    
    def _save_consents(self):
        """Guardar consentimientos"""
        try:
            with open(self.consent_file, 'w', encoding='utf-8') as f:
                json.dump(self.consent_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando consentimientos: {e}")
    
    def ya_ha_consentido(self) -> bool:
        """Verificar si ya se han dado los consentimientos"""
        return self.consent_data.get("consentido", False)
    
    def tiene_consentimiento_cookies(self) -> bool:
        """Verificar consentimiento de cookies"""
        return self.consent_data.get("cookies", False)
    
    def tiene_consentimiento_publicidad(self) -> bool:
        """Verificar consentimiento de publicidad"""
        return self.consent_data.get("publicidad", False)
    
    def tiene_consentimiento_datos(self) -> bool:
        """Verificar consentimiento de datos personales"""
        return self.consent_data.get("datos_personales", False)
    
    def mostrar_banner(self, parent: tk.Tk) -> bool:
        """
        Mostrar banner de consentimientos
        
        Args:
            parent: Ventana padre
        
        Returns:
            True si se aceptaron todos los consentimientos, False si se canceló
        """
        if self.ya_ha_consentido():
            return True
        
        # Crear ventana modal
        dialog = tk.Toplevel(parent)
        dialog.title("Consentimientos - RGPD")
        dialog.geometry("700x600")
        dialog.configure(bg="#1a1a1a")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"700x600+{x}+{y}")
        
        # Variables de consentimiento
        var_cookies = tk.BooleanVar(value=False)
        var_publicidad = tk.BooleanVar(value=False)
        var_datos = tk.BooleanVar(value=False)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="Consentimientos de Privacidad",
            font=('Segoe UI', 18, 'bold'),
            bg="#1a1a1a",
            fg="#ffffff"
        )
        title_label.pack(pady=(0, 20))
        
        # Texto introductorio
        intro_text = (
            "Para cumplir con el Reglamento General de Protección de Datos (RGPD), "
            "necesitamos su consentimiento para:\n\n"
            "Por favor, revise cada opción y marque las casillas correspondientes."
        )
        intro_label = tk.Label(
            main_frame,
            text=intro_text,
            font=('Segoe UI', 10),
            bg="#1a1a1a",
            fg="#cccccc",
            justify=tk.LEFT,
            wraplength=650
        )
        intro_label.pack(pady=(0, 30))
        
        # Frame de scroll para consentimientos
        canvas = tk.Canvas(main_frame, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Consentimiento 1: Cookies
        frame1 = ttk.Frame(scrollable_frame, padding=15)
        frame1.pack(fill=tk.X, pady=10)
        
        check1 = ttk.Checkbutton(
            frame1,
            text="Acepto el uso de cookies técnicas necesarias",
            variable=var_cookies,
            style='TCheckbutton'
        )
        check1.pack(anchor=tk.W)
        
        text1 = (
            "Las cookies técnicas son necesarias para el funcionamiento de la aplicación. "
            "No recopilamos información personal mediante cookies. "
            "Puede consultar nuestra política de cookies en cualquier momento."
        )
        label1 = tk.Label(
            frame1,
            text=text1,
            font=('Segoe UI', 9),
            bg="#1a1a1a",
            fg="#aaaaaa",
            justify=tk.LEFT,
            wraplength=600
        )
        label1.pack(anchor=tk.W, pady=(5, 0))
        
        link1 = tk.Label(
            frame1,
            text="Ver Política de Cookies",
            font=('Segoe UI', 9, 'underline'),
            bg="#1a1a1a",
            fg="#0078d4",
            cursor="hand2"
        )
        link1.pack(anchor=tk.W, pady=(5, 0))
        link1.bind("<Button-1>", lambda e: self._abrir_politica_cookies(dialog))
        
        # Consentimiento 2: Publicidad
        frame2 = ttk.Frame(scrollable_frame, padding=15)
        frame2.pack(fill=tk.X, pady=10)
        
        check2 = ttk.Checkbutton(
            frame2,
            text="Acepto la visualización de publicidad (AdMob)",
            variable=var_publicidad,
            style='TCheckbutton'
        )
        check2.pack(anchor=tk.W)
        
        text2 = (
            "La aplicación muestra publicidad mediante Google AdMob para mantener el servicio gratuito. "
            "Puede desactivar la publicidad adquiriendo una suscripción premium. "
            "Los datos de publicidad son gestionados por Google según su política de privacidad."
        )
        label2 = tk.Label(
            frame2,
            text=text2,
            font=('Segoe UI', 9),
            bg="#1a1a1a",
            fg="#aaaaaa",
            justify=tk.LEFT,
            wraplength=600
        )
        label2.pack(anchor=tk.W, pady=(5, 0))
        
        link2 = tk.Label(
            frame2,
            text="Ver Política de Privacidad de Google",
            font=('Segoe UI', 9, 'underline'),
            bg="#1a1a1a",
            fg="#0078d4",
            cursor="hand2"
        )
        link2.pack(anchor=tk.W, pady=(5, 0))
        link2.bind("<Button-1>", lambda e: self._abrir_politica_google(dialog))
        
        # Consentimiento 3: Datos personales
        frame3 = ttk.Frame(scrollable_frame, padding=15)
        frame3.pack(fill=tk.X, pady=10)
        
        check3 = ttk.Checkbutton(
            frame3,
            text="Acepto el tratamiento de datos personales",
            variable=var_datos,
            style='TCheckbutton'
        )
        check3.pack(anchor=tk.W)
        
        text3 = (
            "La aplicación NO recopila ni almacena datos personales en servidores externos. "
            "Todos los datos (quinielas, configuraciones) se almacenan localmente en su dispositivo. "
            "Solo procesamos datos necesarios para el funcionamiento de la aplicación. "
            "Puede consultar nuestra política de privacidad completa."
        )
        label3 = tk.Label(
            frame3,
            text=text3,
            font=('Segoe UI', 9),
            bg="#1a1a1a",
            fg="#aaaaaa",
            justify=tk.LEFT,
            wraplength=600
        )
        label3.pack(anchor=tk.W, pady=(5, 0))
        
        link3 = tk.Label(
            frame3,
            text="Ver Política de Privacidad",
            font=('Segoe UI', 9, 'underline'),
            bg="#1a1a1a",
            fg="#0078d4",
            cursor="hand2"
        )
        link3.pack(anchor=tk.W, pady=(5, 0))
        link3.bind("<Button-1>", lambda e: self._abrir_politica_privacidad(dialog))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        resultado = {'aceptado': False}
        
        def aceptar():
            if not var_cookies.get():
                messagebox.showwarning(
                    "Consentimiento Requerido",
                    "Debe aceptar el uso de cookies técnicas para continuar."
                )
                return
            
            # Guardar consentimientos
            from datetime import datetime
            self.consent_data = {
                "consentido": True,
                "cookies": var_cookies.get(),
                "publicidad": var_publicidad.get(),
                "datos_personales": var_datos.get(),
                "fecha": datetime.now().isoformat()
            }
            self._save_consents()
            resultado['aceptado'] = True
            dialog.destroy()
        
        def cancelar():
            respuesta = messagebox.askyesno(
                "Confirmar Salida",
                "¿Está seguro de que desea salir? La aplicación requiere consentimientos para funcionar."
            )
            if respuesta:
                dialog.destroy()
        
        # Botones
        btn_aceptar = tk.Button(
            button_frame,
            text="Aceptar y Continuar",
            command=aceptar,
            bg="#0078d4",
            fg="#ffffff",
            font=('Segoe UI', 10, 'bold'),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        btn_aceptar.pack(side=tk.RIGHT, padx=(10, 0))
        
        btn_cancelar = tk.Button(
            button_frame,
            text="Cancelar",
            command=cancelar,
            bg="#444444",
            fg="#ffffff",
            font=('Segoe UI', 10),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        btn_cancelar.pack(side=tk.RIGHT)
        
        # Esperar a que se cierre el diálogo
        dialog.wait_window()
        
        return resultado['aceptado']
    
    def _abrir_politica_cookies(self, parent):
        """Abrir política de cookies"""
        try:
            from pathlib import Path
            import webbrowser
            import os
            
            # Intentar abrir archivo local
            legal_dir = Path(__file__).parent.parent / "LEGAL"
            cookie_file = legal_dir / "AVISO_COOKIES.md"
            
            if cookie_file.exists():
                # En Windows, abrir con aplicación predeterminada
                os.startfile(str(cookie_file))
            else:
                # Si no existe, mostrar mensaje
                messagebox.showinfo(
                    "Política de Cookies",
                    "Puede consultar la política de cookies en:\n"
                    "LEGAL/AVISO_COOKIES.md\n\n"
                    "O visitar: https://1x2futbol.com"
                )
        except Exception as e:
            logger.error(f"Error abriendo política de cookies: {e}")
            messagebox.showinfo(
                "Política de Cookies",
                "Visite: https://1x2futbol.com para consultar nuestra política de cookies."
            )
    
    def _abrir_politica_privacidad(self, parent):
        """Abrir política de privacidad"""
        try:
            from pathlib import Path
            import webbrowser
            import os
            
            legal_dir = Path(__file__).parent.parent / "LEGAL"
            priv_file = legal_dir / "POLITICA_PRIVACIDAD.md"
            
            if priv_file.exists():
                os.startfile(str(priv_file))
            else:
                messagebox.showinfo(
                    "Política de Privacidad",
                    "Puede consultar la política de privacidad en:\n"
                    "LEGAL/POLITICA_PRIVACIDAD.md\n\n"
                    "O visitar: https://1x2futbol.com"
                )
        except Exception as e:
            logger.error(f"Error abriendo política de privacidad: {e}")
            messagebox.showinfo(
                "Política de Privacidad",
                "Visite: https://1x2futbol.com para consultar nuestra política de privacidad."
            )
    
    def _abrir_politica_google(self, parent):
        """Abrir política de privacidad de Google"""
        import webbrowser
        webbrowser.open("https://policies.google.com/privacy")

