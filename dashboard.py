import cv2
import os
import time
import json
import threading
import numpy as np
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from PIL import Image, ImageTk
from ultralytics import YOLO
from collections import deque

# Configurar tema de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class EPPDashboard:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Dashboard Detección EPP - SafeVision EPP")
        # Detectar resolución de pantalla y ajustar tamaño de ventana automáticamente
        try:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            # Usar 90% del tamaño de pantalla (10% menos)
            win_w = int(screen_w * 0.90)
            win_h = int(screen_h * 0.90)
            # Intentar obtener el "work area" (excluye barra de tareas en Windows)
            pos_x = int((screen_w - win_w) / 2)
            pos_y = int((screen_h - win_h) / 2)
            try:
                # Solo en Windows: usar SystemParametersInfo to get work area
                import ctypes
                SPI_GETWORKAREA = 0x0030
                rect = ctypes.wintypes.RECT()
                res = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                if res:
                    work_w = rect.right - rect.left
                    work_h = rect.bottom - rect.top
                    work_x = rect.left
                    work_y = rect.top
                    # Ajustar ventana al 90% del work area y centrar en ella
                    win_w = int(work_w * 0.90)
                    win_h = int(work_h * 0.90)
                    pos_x = work_x + int((work_w - win_w) / 2)
                    pos_y = work_y + int((work_h - win_h) / 2)
            except Exception:
                # si falla la API de Windows, usar el centrado normal
                pass

            self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
            # Ajustar vista previa a 60% de la ventana disponible por defecto
            self.vista_ancho = int(win_w * 0.6)
            self.vista_alto = int(win_h * 0.6)
            # Asegurar límites razonables
            self.vista_ancho = max(320, min(self.vista_ancho, 1920))
            self.vista_alto = max(240, min(self.vista_alto, 1080))
        except Exception:
            # Fallback a valores por defecto
            self.root.geometry("1400x800")
            self.vista_ancho = 640
            self.vista_alto = 480
        
        # Variables
        self.model = None
        self.model_path = None
        # formato del modelo ('pt', 'engine', 'onnx', ...)
        self.model_format = None
        # si el modelo soporta .to() (PyTorch .pt)
        self.supports_to = False
        # dispositivo solicitado para inferencia: 'cpu' o int (gpu index)
        self.requested_device = 'cpu'
        self.camaras = []
        self.detection_active = False
        self.detection_thread = None
        self.frame_cache = {}
        self.fps_history = deque(maxlen=30)
        self.alert_config = {
            'no_hardhat': {'active': True, 'cooldown': 5, 'threshold': 3, 'last_alert': 0, 'count': 0},
            'no_vest': {'active': True, 'cooldown': 5, 'threshold': 3, 'last_alert': 0, 'count': 0},
            'no_mask': {'active': True, 'cooldown': 5, 'threshold': 3, 'last_alert': 0, 'count': 0},
            'no_gloves': {'active': True, 'cooldown': 5, 'threshold': 3, 'last_alert': 0, 'count': 0},
            'no_goggles': {'active': True, 'cooldown': 5, 'threshold': 3, 'last_alert': 0, 'count': 0},
        }
        
        # Cola de detecciones para acumular
        self.detection_buffer = deque(maxlen=30)
        
        # Historial de alertas emitidas
        self.alert_history = deque(maxlen=50)
        
        # Contadores por cámara
        self.camara_violaciones = {}
        
        # Modo prueba
        self.test_mode_active = False
        
        
        # Variables de resolución (agregar estas dos líneas)
        self.vista_ancho = 640
        self.vista_alto = 480
        
        # Colores para cámaras
        self.colores = [
            (0, 255, 0),    # Verde
            (255, 0, 0),    # Rojo
            (0, 255, 255),  # Amarillo
            (255, 0, 255),  # Magenta
            (255, 255, 0),  # Cyan
            (128, 0, 255),  # Púrpura
        ]
        
        # Configurar UI
        self.setup_ui()
        
        # Detectar cámaras locales automáticamente
        self.detectar_camaras_locales()
        
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        
        # Configurar grid principal
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # ===== Panel Izquierdo - Configuración (CON SCROLL) =====
        # Frame contenedor principal para el panel izquierdo
        self.panel_config_container = ctk.CTkFrame(self.root)
        self.panel_config_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.panel_config_container.grid_rowconfigure(0, weight=1)
        self.panel_config_container.grid_columnconfigure(0, weight=1)
        
        # Scrollable frame para la configuración
        self.panel_config = ctk.CTkScrollableFrame(
            self.panel_config_container,
            label_text="⚙️ CONFIGURACIÓN",
            label_font=("Arial", 18, "bold")
        )
        self.panel_config.grid(row=0, column=0, sticky="nsew")
        
        # ===== SECCIONES DENTRO DEL SCROLLABLE FRAME =====
        
        # Sección Modelo
        modelo_frame = ctk.CTkFrame(self.panel_config)
        modelo_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(modelo_frame, text="🤖 Modelo de Detección", 
                    font=("Arial", 14, "bold")).pack(pady=5)
        
        self.btn_cargar_modelo = ctk.CTkButton(
            modelo_frame, 
            text="📁 Cargar Modelo (.pt / .engine)",
            command=self.cargar_modelo,
            height=40
        )
        self.btn_cargar_modelo.pack(pady=5, padx=10, fill="x")
        
        self.lbl_modelo_info = ctk.CTkLabel(
            modelo_frame, 
            text="Ningún modelo cargado",
            text_color="gray"
        )
        self.lbl_modelo_info.pack(pady=5)
        
        # Sección Cámaras
        camaras_frame = ctk.CTkFrame(self.panel_config)
        camaras_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(camaras_frame, text="📹 Cámaras", 
                    font=("Arial", 14, "bold")).pack(pady=5)
        
        # Lista de cámaras (scrollable)
        self.lista_camaras = ctk.CTkScrollableFrame(camaras_frame, height=200)
        self.lista_camaras.pack(fill="both", expand=True, pady=5)
        
        # Botones para cámaras
        btn_frame = ctk.CTkFrame(camaras_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            btn_frame, 
            text="➕ Agregar IP",
            command=self.agregar_camara_ip,
            width=120
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame, 
            text="🖥️ Detectar Locales",
            command=self.detectar_camaras_locales,
            width=120
        ).pack(side="right", padx=2)
        
        # Sección Resolución
        resolucion_frame = ctk.CTkFrame(self.panel_config)
        resolucion_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(resolucion_frame, text="🖥️ Resolución de Vista", 
                    font=("Arial", 14, "bold")).pack(pady=5)
        
        # Frame para resolución
        res_inner = ctk.CTkFrame(resolucion_frame)
        res_inner.pack(fill="x", pady=5)
        
        ctk.CTkLabel(res_inner, text="Ancho:", width=60).pack(side="left", padx=5)
        self.res_ancho = ctk.CTkEntry(res_inner, width=80, placeholder_text="640")
        self.res_ancho.pack(side="left", padx=5)
        self.res_ancho.insert(0, "640")
        
        ctk.CTkLabel(res_inner, text="Alto:", width=60).pack(side="left", padx=5)
        self.res_alto = ctk.CTkEntry(res_inner, width=80, placeholder_text="480")
        self.res_alto.pack(side="left", padx=5)
        self.res_alto.insert(0, "480")
        
        # Botón aplicar resolución
        ctk.CTkButton(
            resolucion_frame,
            text="📐 Aplicar Resolución",
            command=self.aplicar_resolucion,
            height=30,
            fg_color="orange"
        ).pack(pady=5)
        
        ctk.CTkLabel(resolucion_frame, 
                    text="⚠️ Cambia el tamaño de vista previa\n(no afecta el procesamiento)",
                    font=("Arial", 9), text_color="gray").pack()
        
        # ===== Sección Dispositivo (estado y forzar CPU) =====
        device_frame = ctk.CTkFrame(self.panel_config)
        device_frame.pack(fill="x", padx=10, pady=5)

        # Variable para forzar CPU
        self.force_cpu_var = ctk.BooleanVar(value=False)
        self.chk_force_cpu = ctk.CTkCheckBox(
            device_frame,
            text="Forzar CPU (usar solo CPU)",
            variable=self.force_cpu_var,
            command=lambda: self.toggle_force_cpu(self.force_cpu_var.get())
        )
        self.chk_force_cpu.pack(side="left", padx=5)

        # Etiqueta que muestra el dispositivo actual
        self.lbl_device = ctk.CTkLabel(
            device_frame,
            text="Dispositivo: Desconocido",
            text_color="gray",
            font=("Arial", 11)
        )
        self.lbl_device.pack(side="right", padx=5)
        # Botón Iniciar/Detener
        self.btn_iniciar = ctk.CTkButton(
            self.panel_config,
            text="🚀 INICIAR DETECCIÓN",
            command=self.toggle_deteccion,
            height=50,
            fg_color="green",
            font=("Arial", 16, "bold")
        )
        self.btn_iniciar.pack(pady=20, padx=10, fill="x")
        
        # ===== Panel Central - Visualización =====
        self.panel_video = ctk.CTkFrame(self.root)
        self.panel_video.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        
        # Canvas para video
        self.video_label = ctk.CTkLabel(self.panel_video, text="Vista Previa", font=("Arial", 16))
        self.video_label.pack(expand=True, fill="both")
        
        # ===== Panel Derecho - Estadísticas =====
        self.panel_stats = ctk.CTkFrame(self.root)
        self.panel_stats.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        # Título
        ctk.CTkLabel(self.panel_stats, text="📊 ESTADÍSTICAS", 
                    font=("Arial", 18, "bold")).pack(pady=10)
        
        # Métricas
        self.metrics_frame = ctk.CTkFrame(self.panel_stats)
        self.metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_fps = ctk.CTkLabel(
            self.metrics_frame, 
            text="FPS: 0",
            font=("Arial", 14, "bold"),
            text_color="green"
        )
        self.lbl_fps.pack(pady=5)
        
        self.lbl_detecciones = ctk.CTkLabel(
            self.metrics_frame, 
            text="Detecciones Totales: 0",
            font=("Arial", 14)
        )
        self.lbl_detecciones.pack(pady=5)
        
        self.lbl_camaras_activas = ctk.CTkLabel(
            self.metrics_frame, 
            text="Cámaras Activas: 0",
            font=("Arial", 14)
        )
        self.lbl_camaras_activas.pack(pady=5)
        
        # Log de eventos
        ctk.CTkLabel(self.panel_stats, text="📝 Eventos", 
                    font=("Arial", 14, "bold")).pack(pady=5)
        self.log_text = ctk.CTkTextbox(self.panel_stats, height=300)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ===== NUEVA SECCIÓN: ALERTAS EPP - AGREGAR AQUÍ =====
        alertas_frame = ctk.CTkFrame(self.panel_stats)
        alertas_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(alertas_frame, text="🚨 ALERTAS EPP", 
                    font=("Arial", 14, "bold"), text_color="red").pack(pady=5)
        
        # Configuración de umbrales
        config_frame = ctk.CTkFrame(alertas_frame)
        config_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(config_frame, text="Umbral (seg):", 
                    font=("Arial", 10)).pack(side="left", padx=5)
        
        self.umbral_spinbox = ctk.CTkEntry(config_frame, width=60)
        self.umbral_spinbox.insert(0, "3")
        self.umbral_spinbox.pack(side="left", padx=5)
        
        ctk.CTkButton(
            config_frame,
            text="Aplicar",
            command=self.aplicar_umbral,
            width=60,
            height=25
        ).pack(side="left", padx=5)
        
        # Checkbox modo prueba
        self.test_mode_var = ctk.BooleanVar(value=False)
        self.chk_test_mode = ctk.CTkCheckBox(
            alertas_frame,
            text="🎮 Modo Prueba (simular alertas)",
            variable=self.test_mode_var,
            command=self.toggle_test_mode
        )
        self.chk_test_mode.pack(pady=5)
        
        # Frame para alertas activas
        ctk.CTkLabel(alertas_frame, text="Alertas Recientes:", 
                    font=("Arial", 12, "bold")).pack(pady=5)
        
        self.alertas_listbox = ctk.CTkTextbox(alertas_frame, height=100, font=("Arial", 11))
        self.alertas_listbox.pack(fill="x", padx=10, pady=5)
        
        # Contadores por tipo de EPP
        contadores_frame = ctk.CTkFrame(alertas_frame)
        contadores_frame.pack(fill="x", pady=5)
        
        self.lbl_no_hardhat = ctk.CTkLabel(contadores_frame, text="⛑️ Sin Casco: 0", font=("Arial", 11))
        self.lbl_no_hardhat.pack(anchor="w", padx=10)
        
        self.lbl_no_vest = ctk.CTkLabel(contadores_frame, text="🦺 Sin Chaleco: 0", font=("Arial", 11))
        self.lbl_no_vest.pack(anchor="w", padx=10)
        
        self.lbl_no_mask = ctk.CTkLabel(contadores_frame, text="😷 Sin Mascarilla: 0", font=("Arial", 11))
        self.lbl_no_mask.pack(anchor="w", padx=10)
        
        self.lbl_no_gloves = ctk.CTkLabel(contadores_frame, text="🧤 Sin Guantes: 0", font=("Arial", 11))
        self.lbl_no_gloves.pack(anchor="w", padx=10)
        
        self.lbl_no_goggles = ctk.CTkLabel(contadores_frame, text="🥽 Sin Gafas: 0", font=("Arial", 11))
        self.lbl_no_goggles.pack(anchor="w", padx=10)
        # ===== FIN DE NUEVA SECCIÓN =====
        
        
    # Se eliminaron las funciones relacionadas con el cambio de dispositivo.
    def detectar_camaras_locales(self):
        """Detectar cámaras USB conectadas al PC"""
        self.agregar_log("🔍 Buscando cámaras locales...")
        
        for i in range(5):  # Probar índices 0-4
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                nombre = f"Cámara Local {i}"
                url = f"local://{i}"
                self.agregar_camara(nombre, url, i)
                cap.release()
                
        self.agregar_log(f"✅ Detectadas {len([c for c in self.camaras if 'local' in c['url']])} cámaras locales")
        
    def agregar_camara_ip(self):
        """Diálogo para agregar cámara IP manualmente (solo IP:puerto)"""
        dialog = ctk.CTkInputDialog(
            text="Ingrese la dirección de la cámara IP:\n"
                "Ejemplos:\n"
                "• 192.168.18.100:8080\n"
                "• 192.168.1.50:8080\n\n"
                "Formato: IP:PUERTO",
            title="Agregar Cámara IP"
        )
        ip_puerto = dialog.get_input()
        
        if ip_puerto:
            # Construir URL automáticamente
            # Eliminar espacios en blanco
            ip_puerto = ip_puerto.strip()
            
            # Si no tiene http:// al inicio, agregarlo
            if not ip_puerto.startswith("http://") and not ip_puerto.startswith("https://"):
                # Construir URL completa
                url_streaming = f"http://{ip_puerto}/video"
            else:
                # Si ya tiene http://, usarla tal cual
                url_streaming = ip_puerto
            
            # Extraer nombre de la cámara desde la IP
            ip_simple = ip_puerto.split(':')[0] if ':' in ip_puerto else ip_puerto
            nombre = f"IP Cam {ip_simple}"
            
            self.agregar_camara(nombre, url_streaming, ip_original=ip_puerto)
            
            
    def agregar_camara(self, nombre, url, local_index=None, ip_original=None):
        """Agregar una cámara a la lista"""
        # Verificar si ya existe
        for cam in self.camaras:
            if cam['url'] == url:
                self.agregar_log(f"⚠️ La cámara ya existe: {nombre}")
                return
        
        color = self.colores[len(self.camaras) % len(self.colores)]
        
        camara = {
            'nombre': nombre,
            'url': url,
            'color': color,
            'activa': False,
            'local_index': local_index,
            'frame': None,
            'ip_original': ip_original or nombre  # Guardar IP original para mostrar
        }
        
        self.camaras.append(camara)
        self.actualizar_lista_camaras()
        self.agregar_log(f"✅ Cámara agregada: {nombre} ({ip_original or url})")
        
    def actualizar_lista_camaras(self):
        """Actualizar la lista visual de cámaras"""
        # Limpiar lista
        for widget in self.lista_camaras.winfo_children():
            widget.destroy()
        
        for i, cam in enumerate(self.camaras):
            frame = ctk.CTkFrame(self.lista_camaras)
            frame.pack(fill="x", pady=2)
            
            # Mostrar nombre y IP resumida
            if 'ip_original' in cam and cam['ip_original']:
                texto_mostrar = f"{cam['nombre']} ({cam['ip_original']})"
            else:
                texto_mostrar = cam['nombre']
            
            # Checkbox para activar/desactivar
            var = ctk.BooleanVar(value=cam['activa'])
            checkbox = ctk.CTkCheckBox(
                frame, 
                text=texto_mostrar,
                variable=var,
                command=lambda idx=i, v=var: self.toggle_camara(idx, v.get())
            )
            checkbox.pack(side="left", padx=5)
            
            # Botón eliminar
            btn_del = ctk.CTkButton(
                frame,
                text="❌",
                width=30,
                height=30,
                fg_color="red",
                command=lambda idx=i: self.eliminar_camara(idx)
            )
            btn_del.pack(side="right", padx=2)
            
            # Indicador de estado
            estado = "🟢" if cam['activa'] else "🔴"
            ctk.CTkLabel(frame, text=estado, width=30).pack(side="right")
            
    def aplicar_resolucion(self):
        """Aplicar nueva resolución a la vista previa"""
        try:
            ancho = int(self.res_ancho.get())
            alto = int(self.res_alto.get())
            
            # Validar valores mínimos y máximos
            if ancho < 320:
                ancho = 320
                self.res_ancho.delete(0, ctk.END)
                self.res_ancho.insert(0, "320")
            if alto < 240:
                alto = 240
                self.res_alto.delete(0, ctk.END)
                self.res_alto.insert(0, "240")
            if ancho > 1920:
                ancho = 1920
                self.res_ancho.delete(0, ctk.END)
                self.res_ancho.insert(0, "1920")
            if alto > 1080:
                alto = 1080
                self.res_alto.delete(0, ctk.END)
                self.res_alto.insert(0, "1080")
            
            # Guardar valores para usar en actualizar_vista_previa
            self.vista_ancho = ancho
            self.vista_alto = alto
            
            self.agregar_log(f"📐 Resolución cambiada a: {ancho}x{alto}")
            
        except ValueError:
            messagebox.showwarning("Error", "Ingrese valores numéricos válidos")
            
    def toggle_camara(self, idx, estado):
        """Activar/desactivar una cámara"""
        self.camaras[idx]['activa'] = estado
        estado_str = "activada" if estado else "desactivada"
        self.agregar_log(f"📹 Cámara {self.camaras[idx]['nombre']} {estado_str}")
        
    def eliminar_camara(self, idx):
        """Eliminar una cámara de la lista"""
        nombre = self.camaras[idx]['nombre']
        del self.camaras[idx]
        self.actualizar_lista_camaras()
        self.agregar_log(f"🗑️ Cámara eliminada: {nombre}")
        
    def cargar_modelo(self):
        """Cargar modelo YOLO desde archivo"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar modelo",
            filetypes=[
                ("Modelos YOLO", "*.pt *.engine"),
                ("PyTorch models", "*.pt"),
                ("TensorRT engines", "*.engine"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if archivo:
            try:
                # detectar formato por extensión
                ext = Path(archivo).suffix.lower()
                self.model_format = ext.lstrip('.') if ext else None

                self.model = YOLO(archivo)
                self.model_path = archivo
                nombre_modelo = os.path.basename(archivo)
                self.lbl_modelo_info.configure(
                    text=f"✅ {nombre_modelo}",
                    text_color="green"
                )
                self.agregar_log(f"🤖 Modelo cargado: {nombre_modelo} (format={self.model_format})")

                # Determinar si el modelo es PyTorch .pt (soporta .to())
                self.supports_to = (self.model_format == 'pt')

                # Decidir dispositivo solicitado inicial según checkbox y formato
                if self.force_cpu_var.get():
                    self.requested_device = 'cpu'
                else:
                    # Para modelos exportados (TensorRT/ONNX/etc.) no usaremos .to(),
                    # sino que pasaremos device en cada llamada a predict (0 para GPU)
                    if self.supports_to:
                        try:
                            import torch
                            if torch.cuda.is_available():
                                # Intentamos mover el módulo si es PyTorch
                                try:
                                    self.model.to('cuda:0')
                                    self.requested_device = 0
                                    self.lbl_device.configure(text="Dispositivo: GPU (cuda:0)", text_color="green")
                                    self.agregar_log("✅ Modelo movido a GPU (cuda:0)")
                                except Exception as e_move:
                                    # Falla mover a GPU, quedamos en CPU
                                    try:
                                        self.model.to('cpu')
                                    except Exception:
                                        pass
                                    self.requested_device = 'cpu'
                                    self.lbl_device.configure(text="Dispositivo: CPU", text_color="orange")
                                    self.agregar_log(f"⚠️ No se pudo mover el modelo a GPU: {e_move} — usando CPU")
                            else:
                                self.requested_device = 'cpu'
                                self.lbl_device.configure(text="Dispositivo: CPU", text_color="orange")
                                self.agregar_log("ℹ️ GPU no disponible — usando CPU")
                        except ImportError:
                            # torch no disponible: no podemos mover el módulo, usaremos CPU por defecto
                            self.requested_device = 'cpu'
                            self.lbl_device.configure(text="Dispositivo: CPU", text_color="orange")
                            self.agregar_log("ℹ️ 'torch' no instalado — usando CPU por defecto")
                    else:
                        # Modelos exportados (ej. .engine) -> usar GPU por defecto si no se forzó CPU
                        # Para estas cargas no debemos llamar a .to(); Ultralitycs/TensorRT usa GPU cuando se solicita
                        if self.force_cpu_var.get():
                            self.requested_device = 'cpu'
                            self.lbl_device.configure(text="Dispositivo: CPU (forzado)", text_color="orange")
                        else:
                            # preferir GPU index 0
                            self.requested_device = 0
                            # mostrar que es un engine/exportado (puede usar TensorRT en GPU)
                            engine_label = f"Dispositivo: {self.model_format.upper()} (GPU)"
                            self.lbl_device.configure(text=engine_label, text_color="green")
                            self.agregar_log(f"ℹ️ Modelo exportado ({self.model_format}) — irá a inferencia según device en predict")

                # Probar inferencia rápida usando el device seleccionado (si falla, caerá a CPU)
                test_img = np.zeros((640, 640, 3), dtype=np.uint8)
                try:
                    # pasar device explícitamente para manejar formatos exportados
                    self.model.predict(test_img, verbose=False, device=self.requested_device)
                    self.agregar_log("✅ Modelo validado correctamente")
                except Exception as e_pred:
                    # Fallback: intentar predecir sin device o con CPU
                    self.agregar_log(f"⚠️ Validación con device={self.requested_device} falló: {e_pred}")
                    try:
                        self.model.predict(test_img, verbose=False)
                        self.agregar_log("✅ Modelo validado correctamente (sin device)")
                    except Exception as e2:
                        self.agregar_log(f"❌ Error validando modelo: {e2}")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el modelo:\n{str(e)}")
                self.agregar_log(f"❌ Error cargando modelo: {str(e)}")
                
    def toggle_deteccion(self):
        """Iniciar o detener la detección"""
        if not self.detection_active:
            if not self.model:
                messagebox.showwarning("Advertencia", "Primero debe cargar un modelo")
                return
            
            camaras_activas = [c for c in self.camaras if c['activa']]
            if not camaras_activas:
                messagebox.showwarning("Advertencia", "No hay cámaras activas")
                return
            
            self.detection_active = True
            self.btn_iniciar.configure(text="⏹️ DETENER DETECCIÓN", fg_color="red")
            self.detection_thread = threading.Thread(target=self.run_detection, daemon=True)
            self.detection_thread.start()
            self.agregar_log("🚀 Detección iniciada")
            
        else:
            self.detection_active = False
            self.btn_iniciar.configure(text="🚀 INICIAR DETECCIÓN", fg_color="green")
            self.agregar_log("🛑 Detección detenida")
        
    # ===== NUEVOS MÉTODOS DE ALERTAS - AGREGAR A PARTIR DE AQUÍ =====
    
    def toggle_test_mode(self):
        """Activar/desactivar modo prueba para simular alertas"""
        if self.test_mode_var.get():
            self.agregar_log("🎮 Modo prueba activado - Simulando alertas cada 2 segundos")
            self.test_mode_active = True
            if self.detection_active:
                self.simular_alertas_prueba()
        else:
            self.agregar_log("🎮 Modo prueba desactivado")
            self.test_mode_active = False
    
    def simular_alertas_prueba(self):
        """Simular alertas periódicas para modo prueba"""
        if not self.test_mode_var.get() or not self.detection_active:
            return
        
        # Simular detección de faltantes
        tipos = ['no_hardhat', 'no_vest', 'no_mask', 'no_gloves', 'no_goggles']
        tipo = tipos[int(time.time()) % len(tipos)]
        
        self.procesar_alerta(tipo, "Cámara Test", 0.95)
        
        # Programar siguiente simulación
        self.root.after(2000, self.simular_alertas_prueba)
    
    def aplicar_umbral(self):
        """Aplicar nuevo umbral de tiempo para alertas"""
        try:
            nuevo_umbral = float(self.umbral_spinbox.get())
            if nuevo_umbral > 0:
                for key in self.alert_config:
                    self.alert_config[key]['threshold'] = nuevo_umbral
                self.agregar_log(f"⚙️ Umbral de alerta cambiado a {nuevo_umbral} segundos")
            else:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Error", "Ingrese un número válido (mayor a 0)")
    
    def procesar_alerta(self, tipo_falta, camara_nombre, confianza):
        """Procesar una detección de falta de EPP"""
        config = self.alert_config[tipo_falta]
        
        if not config['active']:
            return False
        
        # Incrementar contador para este tipo
        config['count'] += 1
        
        # Verificar si debemos emitir alerta
        tiempo_actual = time.time()
        
        # Si pasó el cooldown, podemos emitir nueva alerta
        if tiempo_actual - config['last_alert'] >= config['cooldown']:
            # Verificar si se superó el umbral
            if self.test_mode_active or config['count'] >= config['threshold']:
                # Emitir alerta
                nombres = {
                    'no_hardhat': '⛑️ SIN CASCO',
                    'no_vest': '🦺 SIN CHALECO',
                    'no_mask': '😷 SIN MASCARILLA',
                    'no_gloves': '🧤 SIN GUANTES',
                    'no_goggles': '🥽 SIN GAFAS'
                }
                
                nombre_alerta = nombres.get(tipo_falta, tipo_falta)
                mensaje = f"🚨 ALERTA: {nombre_alerta} detectado en {camara_nombre} (conf: {confianza:.0%})"
                
                # Agregar al listbox de alertas
                self.agregar_alerta_ui(mensaje)
                
                # Agregar al log del sistema
                self.agregar_log(mensaje)
                
                # Actualizar contadores en UI
                self.actualizar_contadores_ui()
                
                # Resetear contador y actualizar tiempo de última alerta
                config['count'] = 0
                config['last_alert'] = tiempo_actual
                
                return True
        
        return False
    
    def agregar_alerta_ui(self, mensaje):
        """Agregar alerta a la lista visual"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto_alerta = f"[{timestamp}] {mensaje}\n"
        
        self.alertas_listbox.insert("end", texto_alerta)
        self.alertas_listbox.see("end")
        
        # Mantener solo las últimas 10 alertas visibles
        if int(self.alertas_listbox.index('end-1c').split('.')[0]) > 10:
            self.alertas_listbox.delete("1.0", "2.0")
    
    def actualizar_contadores_ui(self):
        """Actualizar los contadores de EPP en la UI"""
        self.lbl_no_hardhat.configure(text=f"⛑️ Sin Casco: {self.alert_config['no_hardhat']['count']}")
        self.lbl_no_vest.configure(text=f"🦺 Sin Chaleco: {self.alert_config['no_vest']['count']}")
        self.lbl_no_mask.configure(text=f"😷 Sin Mascarilla: {self.alert_config['no_mask']['count']}")
        self.lbl_no_gloves.configure(text=f"🧤 Sin Guantes: {self.alert_config['no_gloves']['count']}")
        self.lbl_no_goggles.configure(text=f"🥽 Sin Gafas: {self.alert_config['no_goggles']['count']}")
    
    def mapear_clase_a_falta(self, class_name, confidence):
        """
        Mapear nombres de clases de YOLO a tipos de falta de EPP.
        AJUSTA SEGÚN TUS CLASES REALES.
        """
        mapeo = {
            'hardhat': 'no_hardhat',
            'vest': 'no_vest',
            'mask': 'no_mask',
            'gloves': 'no_gloves',
            'goggles': 'no_goggles'
        }
        return mapeo.get(class_name.lower(), None)
    
    # ===== FIN DE NUEVOS MÉTODOS =====
    def toggle_force_cpu(self, force: bool):
        """Handler para el checkbox 'Forzar CPU'.
        Si force=True moverá el modelo a CPU (si está cargado). Si force=False,
        intentará mover el modelo a GPU (si está disponible).
        """
        try:
            if not self.model:
                # No hay modelo cargado: deshabilitar checkbox y avisar
                self.agregar_log("⚠️ No hay modelo cargado para aplicar Forzar CPU")
                return

            if force:
                self.agregar_log("⚙️ Forzar CPU activado")
                # Actualizar etiqueta y solicitar CPU en predict
                self.requested_device = 'cpu'
                self.lbl_device.configure(text="Dispositivo: CPU (forzado)", text_color="orange")
                # Si es modelo PyTorch, intentar moverlo a CPU para liberar GPU memoria
                if self.supports_to:
                    try:
                        self.model.to('cpu')
                        self.agregar_log("✅ Modelo movido a CPU (forzado)")
                    except Exception as e:
                        self.agregar_log(f"⚠️ No se pudo forzar modelo a CPU: {e}")
            else:
                self.agregar_log("⚙️ Forzar CPU desactivado")
                # Si el modelo es PyTorch y la GPU está disponible, intentar moverlo
                if self.supports_to:
                    try:
                        import torch
                        if torch.cuda.is_available():
                            try:
                                self.model.to('cuda:0')
                                self.requested_device = 0
                                self.lbl_device.configure(text="Dispositivo: GPU (cuda:0)", text_color="green")
                                self.agregar_log("✅ Modelo movido a GPU (cuda:0)")
                            except Exception as e_move:
                                self.requested_device = 'cpu'
                                self.lbl_device.configure(text="Dispositivo: CPU", text_color="orange")
                                self.agregar_log(f"⚠️ No se pudo mover el modelo a GPU: {e_move} — usando CPU")
                        else:
                            self.requested_device = 'cpu'
                            self.lbl_device.configure(text="Dispositivo: CPU", text_color="orange")
                            self.agregar_log("ℹ️ GPU no disponible — usando CPU")
                    except ImportError:
                        self.requested_device = 'cpu'
                        self.lbl_device.configure(text="Dispositivo: CPU", text_color="orange")
                        self.agregar_log("ℹ️ 'torch' no instalado — usando CPU")
                else:
                    # Modelos exportados no admiten .to(); simplemente cambiamos el device que pasamos a predict
                    if self.requested_device == 'cpu':
                        # Si previamente se había forzado CPU, ahora preferimos GPU
                        self.requested_device = 0
                        self.lbl_device.configure(text=f"Dispositivo: {self.model_format.upper()} (GPU)", text_color="green")
                        self.agregar_log(f"ℹ️ Forzar CPU desactivado — {self.model_format.upper()} usará GPU en predict si está disponible")
                    else:
                        # ya estaba en GPU
                        self.agregar_log(f"ℹ️ {self.model_format.upper()} continuará usando GPU en predict si está disponible")
        except Exception as ex:
            self.agregar_log(f"❌ Error gestionando forzar CPU: {ex}")
            
    def run_detection(self):
        """Ejecutar el loop de detección"""
        caps = {}
        frame_count = 0
        ultimo_tiempo = time.time()
        total_detecciones = 0
        
        try:
            # Inicializar capturas
            for cam in self.camaras:
                if cam['activa']:
                    if 'local' in cam['url']:
                        cap = cv2.VideoCapture(cam['local_index'])
                    else:
                        cap = cv2.VideoCapture(cam['url'])
                    
                    if cap.isOpened():
                        caps[cam['nombre']] = cap
                        cam['conectada'] = True
                    else:
                        cam['conectada'] = False
                        self.agregar_log(f"❌ No se pudo conectar: {cam['nombre']}")
            
            # Loop principal
            while self.detection_active:
                frames_procesados = 0
                
                for cam in self.camaras:
                    if not cam['activa'] or cam['nombre'] not in caps:
                        continue
                    
                    cap = caps[cam['nombre']]
                    ret, frame = cap.read()
                    
                    if not ret:
                        if cam.get('conectada', False):
                            self.agregar_log(f"⚠️ Pérdida de conexión: {cam['nombre']}")
                            cam['conectada'] = False
                        continue
                    
                    cam['conectada'] = True
                    
                    # Redimensionar para rendimiento
                    frame = cv2.resize(frame, (640, 480))
                    
                    # Inferencia
                    # Pasamos el device solicitado para formatos exportados y PyTorch
                    predict_kwargs = dict(source=frame, conf=0.4, verbose=False, stream=True)
                    if hasattr(self, 'requested_device') and self.requested_device is not None:
                        # ultralytics acepta device int (GPU index) o 'cpu'
                        predict_kwargs['device'] = self.requested_device

                    results = self.model.predict(**predict_kwargs)
                    
                    for result in results:
                        annotated_frame = result.plot(line_width=1, font_size=0.6)
                        cam['frame'] = annotated_frame
                        frames_procesados += 1
                        
                        # Contar detecciones
                        if result.boxes is not None:
                            detecciones_frame = len(result.boxes)
                            total_detecciones += detecciones_frame
                            
                            # ===== NUEVO: PROCESAR ALERTAS EPP =====
                            # Obtener clases detectadas
                            if hasattr(result, 'names') and result.boxes.cls is not None:
                                for box, cls_id in zip(result.boxes, result.boxes.cls):
                                    class_name = result.names[int(cls_id)]
                                    confidence = float(box.conf[0]) if hasattr(box, 'conf') else 0.9
                                    
                                    # Si está en modo prueba, simular alertas
                                    if self.test_mode_var.get():
                                        tipos = ['no_hardhat', 'no_vest', 'no_mask', 'no_gloves', 'no_goggles']
                                        tipo_random = tipos[int(time.time()) % len(tipos)]
                                        self.procesar_alerta(tipo_random, cam['nombre'], confidence)
                                    else:
                                        # Modo real: mapear clase a falta
                                        falta_tipo = self.mapear_clase_a_falta(class_name, confidence)
                                        if falta_tipo:
                                            self.procesar_alerta(falta_tipo, cam['nombre'], confidence)
                            # ===== FIN DE PROCESAMIENTO ALERTAS =====
                    
                    time.sleep(0.001)
                
                # Actualizar estadísticas
                frame_count += frames_procesados
                tiempo_actual = time.time()
                if tiempo_actual - ultimo_tiempo >= 1.0:
                    fps = frame_count / (tiempo_actual - ultimo_tiempo)
                    self.fps_history.append(fps)
                    fps_promedio = sum(self.fps_history) / len(self.fps_history)
                    
                    # Actualizar UI
                    self.lbl_fps.configure(text=f"FPS: {fps_promedio:.1f}")
                    self.lbl_detecciones.configure(text=f"Detecciones Totales: {total_detecciones}")
                    
                    camaras_activas = sum(1 for c in self.camaras if c.get('conectada', False))
                    self.lbl_camaras_activas.configure(text=f"Cámaras Activas: {camaras_activas}")
                    
                    frame_count = 0
                    ultimo_tiempo = tiempo_actual
                
                # Actualizar vista previa
                self.actualizar_vista_previa()
                
        except Exception as e:
            self.agregar_log(f"❌ Error en detección: {str(e)}")
            
        finally:
            # Limpiar capturas
            for cap in caps.values():
                cap.release()
                
    def actualizar_vista_previa(self):
        """Actualizar la vista previa combinada"""
        camaras_activas = [c for c in self.camaras if c.get('frame') is not None]
        
        if not camaras_activas:
            return
        
        # Usar resolución configurada
        base_w = self.vista_ancho
        base_h = self.vista_alto
        
        # Crear grid dinámico
        num_camaras = len(camaras_activas)
        cols = min(2, num_camaras)  # Máximo 2 columnas
        rows = (num_camaras + cols - 1) // cols
        
        # Tamaño de cada celda basado en resolución configurada
        cell_w = base_w // cols
        cell_h = base_h // rows
        
        canvas = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)
        
        for idx, cam in enumerate(camaras_activas):
            row = idx // cols
            col = idx % cols
            x_offset = col * cell_w
            y_offset = row * cell_h
            
            frame = cv2.resize(cam['frame'], (cell_w, cell_h))
            canvas[y_offset:y_offset+cell_h, x_offset:x_offset+cell_w] = frame
            
            # Añadir nombre (ajustar tamaño de fuente según resolución)
            font_scale = max(0.5, min(1.0, cell_w / 640))
            cv2.putText(canvas, cam['nombre'], 
                    (x_offset + 10, y_offset + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, cam['color'], 2)
        
        # Convertir para Tkinter
        canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(canvas_rgb)
        
        # Redimensionar la imagen para que quepa en el panel si es muy grande
        max_display_w = self.panel_video.winfo_width() - 20
        max_display_h = self.panel_video.winfo_height() - 20
        
        if max_display_w > 100 and max_display_h > 100:
            if canvas.shape[1] > max_display_w or canvas.shape[0] > max_display_h:
                scale = min(max_display_w / canvas.shape[1], max_display_h / canvas.shape[0])
                new_w = int(canvas.shape[1] * scale)
                new_h = int(canvas.shape[0] * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        img_tk = ImageTk.PhotoImage(image=img)
        
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk
        
    def agregar_log(self, mensaje):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {mensaje}\n")
        self.log_text.see("end")
        
    def run(self):
        """Ejecutar el dashboard"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Manejar cierre de la aplicación"""
        self.detection_active = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        self.root.destroy()

# =====================================
# Main
# =====================================
if __name__ == "__main__":
    app = EPPDashboard()
    app.run()