#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import threading
import time
import re

class ProfessionalTouchKeyboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Teclado Virtual Pro")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.7)  # Más transparente
        self.root.geometry("100x100+50+50")

        # Variables de estado
        self.keyboard_visible = False
        self.caps_lock = False
        self.shift_active = False
        self.is_dragging = False
        self.actually_dragged = False
        self.touch_mode = True
        
        # Variables para WiFi
        self.wifi_signal_strength = 0  # 0=Sin señal, 1=Baja, 2=Media, 3=Alta
        self.wifi_checking = False
        self.wifi_btn = None

        # Colores del tema - Blanco y Negro + WiFi
        self.colors = {
            'primary': '#000000',        # Negro
            'secondary': '#333333',      # Gris oscuro
            'accent': '#666666',         # Gris medio
            'success': '#444444',        # Gris oscuro 2
            'warning': '#555555',        # Gris medio 2
            'danger': '#222222',         # Gris muy oscuro
            'light': '#FFFFFF',          # Blanco
            'dark': '#000000',           # Negro
            'gradient_start': '#333333', # Gris oscuro
            'gradient_end': '#666666',   # Gris medio
            'reload': '#4A4A4A',        # Color específico para recarga
            # Colores WiFi según niveles
            'wifi_high': '#28A745',      # Verde - Señal alta
            'wifi_medium': '#FFC107',    # Amarillo - Señal media  
            'wifi_low': '#DC3545',       # Rojo - Señal baja
            'wifi_none': '#6C757D',      # Gris - Sin señal
            'wifi_checking': '#F39C12'   # Naranja - Verificando
        }

        # Configurar interfaz
        self.root.configure(bg=self.colors['primary'])

        # Crear botón flotante
        self.create_floating_button()

        # Crear ventana del teclado
        self.create_keyboard_window()

        # Hacer solo el botón flotante arrastrable
        self.make_draggable(self.root)

        # Configurar eventos
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.keyboard.bind("<Escape>", lambda e: self.hide_keyboard())

        # Iniciar verificación de WiFi en hilo separado
        self.start_wifi_monitoring()

        self.root.mainloop()

    def get_wifi_signal_strength(self):
        """Obtener nivel de señal WiFi (0=Sin señal, 1=Baja, 2=Media, 3=Alta)"""
        try:
            # Método 1: Usar iwconfig para obtener el nivel de señal
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Buscar información de señal en la salida
                lines = result.stdout.split('\n')
                for line in lines:
                    # Verificar si hay una conexión WiFi activa
                    if 'ESSID:' in line and 'off/any' not in line and '""' not in line:
                        # Buscar nivel de señal en la siguiente línea o líneas cercanas
                        for check_line in lines:
                            # Buscar Link Quality
                            quality_match = re.search(r'Link Quality[=:](\d+)/(\d+)', check_line)
                            if quality_match:
                                current = int(quality_match.group(1))
                                maximum = int(quality_match.group(2))
                                percentage = (current / maximum) * 100
                                
                                if percentage >= 70:
                                    return 3  # Alta
                                elif percentage >= 40:
                                    return 2  # Media
                                elif percentage >= 10:
                                    return 1  # Baja
                                else:
                                    return 0  # Sin señal útil
                            
                            # Buscar Signal level en dBm
                            signal_match = re.search(r'Signal level[=:](-?\d+)', check_line)
                            if signal_match:
                                signal_dbm = int(signal_match.group(1))
                                
                                if signal_dbm >= -50:
                                    return 3  # Alta (-30 a -50 dBm)
                                elif signal_dbm >= -70:
                                    return 2  # Media (-50 a -70 dBm)
                                elif signal_dbm >= -80:
                                    return 1  # Baja (-70 a -80 dBm)
                                else:
                                    return 0  # Muy baja (menos de -80 dBm)
                        
                        # Si encontramos ESSID pero no señal específica, asumir conexión básica
                        return 1
            
            # Método 2: Verificar conectividad básica con ping
            ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'], 
                                       capture_output=True, timeout=4)
            if ping_result.returncode == 0:
                # Si hay ping pero no pudimos medir señal, asumir señal media
                return 2
            
            # Sin conexión
            return 0
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return 0

    def get_wifi_symbol_and_color(self):
        """Obtener símbolo y color según el nivel de señal"""
        if self.wifi_checking:
            return "●●●", self.colors['wifi_checking']
        
        symbols = {
            0: "○○○",  # Sin señal - círculos vacíos
            1: "●○○",  # Baja - 1 círculo lleno
            2: "●●○",  # Media - 2 círculos llenos  
            3: "●●●"   # Alta - 3 círculos llenos
        }
        
        colors = {
            0: self.colors['wifi_none'],    # Gris
            1: self.colors['wifi_low'],     # Rojo
            2: self.colors['wifi_medium'],  # Amarillo
            3: self.colors['wifi_high']     # Verde
        }
        
        return symbols[self.wifi_signal_strength], colors[self.wifi_signal_strength]

    def update_wifi_button(self):
        """Actualizar el botón de WiFi según el estado"""
        if self.wifi_btn is None:
            return
        
        symbol, color = self.get_wifi_symbol_and_color()
        
        self.wifi_btn.config(
            text=symbol,
            bg=color,
            fg='#FFFFFF'
        )

    def wifi_monitor_thread(self):
        """Hilo para monitorear WiFi continuamente"""
        while True:
            try:
                if not self.wifi_checking:
                    self.wifi_checking = True
                    self.root.after(0, self.update_wifi_button)
                    
                    # Verificar nivel de señal
                    self.wifi_signal_strength = self.get_wifi_signal_strength()
                    
                    self.wifi_checking = False
                    self.root.after(0, self.update_wifi_button)
                
                # Esperar 5 segundos antes de la siguiente verificación
                time.sleep(5)
                
            except Exception as e:
                print(f"Error en monitoreo WiFi: {e}")
                self.wifi_signal_strength = 0
                self.wifi_checking = False
                self.root.after(0, self.update_wifi_button)
                time.sleep(8)  # Esperar más tiempo si hay error

    def start_wifi_monitoring(self):
        """Iniciar el monitoreo de WiFi"""
        wifi_thread = threading.Thread(target=self.wifi_monitor_thread, daemon=True)
        wifi_thread.start()

    def on_wifi_click(self):
        """Acción al hacer click en el botón WiFi"""
        try:
            # Abrir configuración de red del sistema
            subprocess.run(['nm-connection-editor'], check=False)
        except:
            try:
                # Alternativa: abrir configuración de GNOME
                subprocess.run(['gnome-control-center', 'network'], check=False)
            except:
                try:
                    # Alternativa: comando nmtui para terminal
                    subprocess.run(['x-terminal-emulator', '-e', 'nmtui'], check=False)
                except:
                    print("No se pudo abrir configuración de red")

    def create_floating_button(self):
        """Crear botón flotante principal - Optimizado para touch"""
        self.btn_frame = tk.Frame(
            self.root,
            bg=self.colors['gradient_start'],
            relief='flat',
            bd=0
        )
        self.btn_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Botón más grande para pantallas táctiles
        button_size = 32 if self.touch_mode else 28

        self.floating_btn = tk.Button(
            self.btn_frame,
            text="⌨",
            font=("Segoe UI", button_size, "bold"),
            bg=self.colors['gradient_start'],
            fg='white',
            activebackground=self.colors['gradient_end'],
            activeforeground='white',
            relief='flat',
            bd=0,
            cursor='hand2',
            command=self.on_button_click
        )
        self.floating_btn.pack(expand=True, fill='both')

        # Efectos hover más visibles para touch
        if self.touch_mode:
            self.floating_btn.bind("<ButtonPress-1>",
                lambda e: self.floating_btn.config(bg='#666666'))
            self.floating_btn.bind("<ButtonRelease-1>",
                lambda e: self.root.after(100, lambda:
                self.floating_btn.config(bg='#333333')))
        else:
            self.floating_btn.bind("<Enter>",
                lambda e: self.floating_btn.config(bg='#666666'))
            self.floating_btn.bind("<Leave>",
                lambda e: self.floating_btn.config(bg='#333333'))

    def on_button_click(self):
        """Manejar click del botón - solo toggle si no se está arrastrando"""
        pass

    def create_keyboard_window(self):
        """Crear ventana principal del teclado"""
        self.keyboard = tk.Toplevel(self.root)
        self.keyboard.withdraw()
        self.keyboard.overrideredirect(True)
        self.keyboard.attributes("-topmost", True)
        self.keyboard.attributes("-alpha", 0.98)
        self.keyboard.geometry("1100x400+100+400")
        self.keyboard.configure(bg=self.colors['primary'])

        # Frame principal
        main_frame = tk.Frame(self.keyboard, bg=self.colors['primary'])
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # Barra de título (área de arrastre)
        self.title_frame = tk.Frame(main_frame, bg=self.colors['secondary'], height=40, relief='raised', bd=1)
        self.title_frame.pack(fill='x', pady=(0, 10))
        self.title_frame.pack_propagate(False)

        # Hacer solo la barra de título arrastrable
        self.make_title_draggable(self.keyboard, self.title_frame)

        title_label = tk.Label(
            self.title_frame,
            text="TECLADO VIRTUAL",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['light'],
            cursor='hand2'
        )
        title_label.pack(side='left', padx=10, pady=5)

        # Hacer que el label también sea parte del área de arrastre
        self.make_title_draggable(self.keyboard, title_label)

        # Frame para botones de control
        control_frame = tk.Frame(
            self.title_frame,
            bg=self.colors['secondary']
        )
        control_frame.pack(side='right', padx=5, pady=5)

        # Botón de WiFi
        self.wifi_btn = tk.Button(
            control_frame,
            text="●●●",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['wifi_checking'],
            fg='#FFFFFF',
            activebackground='#FFFFFF',
            activeforeground='#000000',
            relief='flat',
            bd=0,
            width=4,
            cursor='hand2',
            command=self.on_wifi_click
        )
        self.wifi_btn.pack(side='left', padx=2)

        # Efectos hover para botón WiFi
        def wifi_enter(e):
            current_bg = self.wifi_btn.cget('bg')
            if current_bg == self.colors['wifi_high']:
                self.wifi_btn.config(bg='#34CE57', fg='#FFFFFF')
            elif current_bg == self.colors['wifi_medium']:
                self.wifi_btn.config(bg='#FFD93D', fg='#000000')
            elif current_bg == self.colors['wifi_low']:
                self.wifi_btn.config(bg='#E8596B', fg='#FFFFFF')
            elif current_bg == self.colors['wifi_none']:
                self.wifi_btn.config(bg='#ADB5BD', fg='#000000')
            else:
                self.wifi_btn.config(bg='#E67E22', fg='#FFFFFF')

        def wifi_leave(e):
            symbol, color = self.get_wifi_symbol_and_color()
            self.wifi_btn.config(bg=color, fg='#FFFFFF' if color != self.colors['wifi_medium'] else '#000000')

        self.wifi_btn.bind("<Enter>", wifi_enter)
        self.wifi_btn.bind("<Leave>", wifi_leave)

        # Botón de recarga
        reload_btn = tk.Button(
            control_frame,
            text="⟲",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['reload'],
            fg='#FFFFFF',
            activebackground='#FFFFFF',
            activeforeground='#000000',
            relief='flat',
            bd=0,
            width=3,
            cursor='hand2',
            command=self.reload_page
        )
        reload_btn.pack(side='left', padx=2)

        # Efectos hover para botón de recarga
        reload_btn.bind("<Enter>", lambda e: reload_btn.config(bg='#FFFFFF', fg='#000000'))
        reload_btn.bind("<Leave>", lambda e: reload_btn.config(bg=self.colors['reload'], fg='#FFFFFF'))

        # Botón de cerrar
        close_btn = tk.Button(
            control_frame,
            text="✕",
            font=("Segoe UI", 12, "bold"),
            bg='#222222',
            fg='#FFFFFF',
            activebackground='#FFFFFF',
            activeforeground='#000000',
            relief='flat',
            bd=0,
            width=3,
            cursor='hand2',
            command=self.hide_keyboard
        )
        close_btn.pack(side='left', padx=2)

        # Efectos hover para botón de cerrar
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg='#FFFFFF', fg='#000000'))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg='#222222', fg='#FFFFFF'))

        # Frame para las teclas
        self.keys_frame = tk.Frame(main_frame, bg=self.colors['primary'])
        self.keys_frame.pack(expand=True, fill='both')

        # Crear todas las teclas
        self.create_all_keys()

    def reload_page(self):
        """Función para recargar la página usando Ctrl+R o F5"""
        try:
            subprocess.run(['xdotool', 'key', 'ctrl+r'], check=True)
        except subprocess.CalledProcessError:
            try:
                subprocess.run(['xdotool', 'key', 'F5'], check=True)
            except subprocess.CalledProcessError:
                print("Error: No se pudo recargar la página")

    def create_all_keys(self):
        """Crear todo el layout del teclado"""
        # Layout completo del teclado
        self.key_layouts = {
            'normal': [
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
                ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
                ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ñ', ';', "'"],
                ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
            ],
            'shift': [
                ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+'],
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"'],
                ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?']
            ]
        }

        # Crear filas principales
        self.create_main_rows()

        # Crear fila especial con espaciadora y flechas
        self.create_special_row_with_arrows()

        # Crear fila de acentos(se quito porque no fue necesaria
        # self.create_accent_row()

    def create_main_rows(self):
        """Crear las filas principales del teclado"""
        current_layout = self.key_layouts['shift' if self.caps_lock or self.shift_active else 'normal']

        for row_idx, row in enumerate(current_layout):
            row_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
            row_frame.pack(fill='x', pady=2)

            # Teclas especiales al final de algunas filas
            if row_idx == 0:  # Primera fila - añadir Borrar
                row = row + ['Borrar']
            elif row_idx == 2:  # Tercera fila - añadir Enter
                row = row + ['Enter']
            elif row_idx == 3:  # Cuarta fila - añadir Shift
                row = row + ['Shift']

            for col_idx, key in enumerate(row):
                if key in ['Borrar', 'Enter', 'Shift']:
                    # Teclas especiales con colores en escala de grises
                    if key == 'Borrar':
                        btn = self.create_key_button(row_frame, key, '#222222')
                    elif key == 'Enter':
                        btn = self.create_key_button(row_frame, key, '#444444')
                    elif key == 'Shift':
                        btn = self.create_key_button(row_frame, key, '#666666')

                    # Teclas especiales más anchas
                    btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)
                else:
                    # Teclas normales
                    btn = self.create_key_button(row_frame, key, '#333333')
                    btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

    def create_special_row_with_arrows(self):
        """Crear fila especial con Caps Lock, barra espaciadora y flechas direccionales"""
        special_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
        special_frame.pack(fill='x', pady=5)

        # Caps Lock
        caps_color = '#555555' if self.caps_lock else '#333333'
        caps_btn = self.create_key_button(special_frame, 'Caps', caps_color)
        caps_btn.pack(side='left', padx=2, pady=2, fill='both')

        # Barra espaciadora (ocupará el espacio disponible)
        space_btn = self.create_key_button(special_frame, 'Espacio', '#444444')
        space_btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

        # Flechas direccionales al lado derecho
        # Flecha izquierda
        left_btn = self.create_key_button(special_frame, '←', '#555555')
        left_btn.pack(side='left', padx=2, pady=2, fill='both')

        # Flecha arriba
        up_btn = self.create_key_button(special_frame, '↑', '#555555')
        up_btn.pack(side='left', padx=2, pady=2, fill='both')

        # Flecha abajo
        down_btn = self.create_key_button(special_frame, '↓', '#555555')
        down_btn.pack(side='left', padx=2, pady=2, fill='both')

        # Flecha derecha
        right_btn = self.create_key_button(special_frame, '→', '#555555')
        right_btn.pack(side='left', padx=2, pady=2, fill='both')

    def create_accent_row(self):
        """Crear fila con acentos y caracteres especiales"""
        accent_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
        accent_frame.pack(fill='x', pady=2)

        # Caracteres con acentos y especiales del español
        accents = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'ü', '¿', '¡']

        for accent in accents:
            btn = self.create_key_button(accent_frame, accent, '#333333')
            btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

    def create_key_button(self, parent, text, bg_color):
        """Crear botón de tecla individual"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 12, "bold"),
            bg=bg_color,
            fg='#FFFFFF',
            activebackground='#FFFFFF',
            activeforeground='#000000',
            relief='flat',
            bd=1,
            cursor='hand2',
            height=2,
            command=lambda: self.handle_key_press(text)
        )

        # Efectos hover
        btn.bind("<Enter>", lambda e: btn.config(bg='#FFFFFF', fg='#000000'))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color, fg='#FFFFFF'))

        return btn

    def handle_key_press(self, key):
        """Manejar todas las pulsaciones de teclas"""
        try:
            if key == 'Caps':
                self.toggle_caps_lock()
                return
            elif key == 'Shift':
                self.toggle_shift()
                return
            elif key == 'Espacio':
                subprocess.run(['xdotool', 'key', 'space'], check=True)
                return
            elif key == 'Borrar':
                subprocess.run(['xdotool', 'key', 'BackSpace'], check=True)
                return
            elif key == 'Enter':
                subprocess.run(['xdotool', 'key', 'Return'], check=True)
                return
            # Teclas de flecha
            elif key == '↑':
                subprocess.run(['xdotool', 'key', 'Up'], check=True)
                return
            elif key == '↓':
                subprocess.run(['xdotool', 'key', 'Down'], check=True)
                return
            elif key == '←':
                subprocess.run(['xdotool', 'key', 'Left'], check=True)
                return
            elif key == '→':
                subprocess.run(['xdotool', 'key', 'Right'], check=True)
                return

            # Mapeo para caracteres especiales
            special_map = {
                '!': 'exclam', '@': 'at', '#': 'numbersign', '$': 'dollar',
                '%': 'percent', '^': 'asciicircum', '&': 'ampersand', '*': 'asterisk',
                '(': 'parenleft', ')': 'parenright', '_': 'underscore', '+': 'plus',
                '{': 'braceleft', '}': 'braceright', '|': 'bar', ':': 'colon',
                '"': 'quotedbl', '<': 'less', '>': 'greater', '?': 'question',
                '[': 'bracketleft', ']': 'bracketright', '\\': 'backslash',
                ';': 'semicolon', "'": 'apostrophe', ',': 'comma', '.': 'period',
                '/': 'slash', '-': 'minus', '=': 'equal',
                'á': 'aacute', 'é': 'eacute', 'í': 'iacute', 'ó': 'oacute',
                'ú': 'uacute', 'ñ': 'ntilde', 'ü': 'udiaeresis',
                '¿': 'questiondown', '¡': 'exclamdown'
            }

            if key in special_map:
                subprocess.run(['xdotool', 'key', special_map[key]], check=True)
            else:
                # Tecla normal
                if self.caps_lock or self.shift_active:
                    if key.isalpha():
                        key = key.upper()
                subprocess.run(['xdotool', 'type', key], check=True)

            # Desactivar shift después de usar
            if self.shift_active:
                self.shift_active = False
                self.update_keyboard()

        except subprocess.CalledProcessError:
            print("Error: xdotool no disponible")
        except Exception as e:
            print(f"Error: {e}")

    def toggle_caps_lock(self):
        """Alternar Caps Lock"""
        self.caps_lock = not self.caps_lock
        self.update_keyboard()

    def toggle_shift(self):
        """Alternar Shift temporal"""
        self.shift_active = not self.shift_active
        self.update_keyboard()

    def update_keyboard(self):
        """Actualizar el teclado completo"""
        # Limpiar teclado actual
        for widget in self.keys_frame.winfo_children():
            widget.destroy()

        # Recrear teclado con nuevo estado
        self.create_all_keys()

    def toggle_keyboard(self):
        """Mostrar/ocultar teclado"""
        if self.keyboard_visible:
            self.hide_keyboard()
        else:
            self.show_keyboard()

    def show_keyboard(self):
        """Mostrar teclado"""
        self.keyboard.deiconify()
        self.keyboard_visible = True
        self.floating_btn.config(bg='#444444')

    def hide_keyboard(self):
        """Ocultar teclado"""
        self.keyboard.withdraw()
        self.keyboard_visible = False
        self.floating_btn.config(bg='#333333')

    def make_title_draggable(self, window, title_widget):
        """Hacer ventana arrastrable solo desde la barra de título"""
        def start_drag(event):
            window.x = event.x_root - window.winfo_x()
            window.y = event.y_root - window.winfo_y()

        def on_drag(event):
            x = event.x_root - window.x
            y = event.y_root - window.y
            window.geometry(f"+{x}+{y}")

        title_widget.bind("<Button-1>", start_drag)
        title_widget.bind("<B1-Motion>", on_drag)

    def make_draggable(self, widget):
        """Hacer ventana completamente arrastrable (solo para botón flotante)"""
        self.drag_threshold = 10
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.actually_dragged = False

        def start_drag(event):
            widget.x = event.x
            widget.y = event.y
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.is_dragging = False
            self.actually_dragged = False

        def on_drag(event):
            # Calcular distancia desde el punto inicial
            drag_distance = ((event.x_root - self.drag_start_x) ** 2 +
                           (event.y_root - self.drag_start_y) ** 2) ** 0.5

            # Solo marcar como arrastre si se supera el umbral
            if drag_distance > self.drag_threshold:
                self.is_dragging = True
                self.actually_dragged = True
                x = widget.winfo_pointerx() - widget.x
                y = widget.winfo_pointery() - widget.y
                widget.geometry(f"+{x}+{y}")

        def end_drag(event):
            # Si NO se arrastró realmente, ejecutar toggle
            if not self.actually_dragged:
                self.toggle_keyboard()

            # Resetear flags después de un delay
            def reset_flags():
                self.is_dragging = False
                self.actually_dragged = False

            widget.after(100, reset_flags)

        # Eventos táctiles y de mouse
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", on_drag)
        widget.bind("<ButtonRelease-1>", end_drag)

        # Eventos específicos para touch (si están disponibles)
        try:
            widget.bind("<TouchBegin>", start_drag)
            widget.bind("<TouchMove>", on_drag)
            widget.bind("<TouchEnd>", end_drag)
        except:
            pass  # No todos los sistemas soportan eventos touch

def main():
    """Función principal con verificación de dependencias"""
    try:
        # Verificar xdotool
        subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
        ProfessionalTouchKeyboard()
    except subprocess.CalledProcessError:
        print("Error: xdotool no está instalado")
        print("Instalar con: sudo apt-get install xdotool")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
