#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import threading
import time
import re
import os

class WaylandTouchKeyboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Teclado Virtual Pro - Wayland")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.7)
        self.root.geometry("100x100+50+50")

        # Variables de estado
        self.keyboard_visible = False
        self.caps_lock = False
        self.shift_active = False
        self.is_dragging = False
        self.actually_dragged = False
        self.touch_mode = True
        
        # Variables para WiFi
        self.wifi_signal_strength = 0
        self.wifi_checking = False
        self.wifi_btn = None

        # Verificar herramientas disponibles
        self.input_method = self.detect_input_method()
        if not self.input_method:
            print("ERROR: No se encontró ningún método de entrada compatible")
            print("Instalando ydotool...")
            self.install_ydotool()
            self.input_method = self.detect_input_method()
            if not self.input_method:
                print("No se pudo instalar ydotool. Saliendo...")
                sys.exit(1)

        # Colores del tema
        self.colors = {
            'primary': '#000000',
            'secondary': '#333333',
            'accent': '#666666',
            'success': '#444444',
            'warning': '#555555',
            'danger': '#222222',
            'light': '#FFFFFF',
            'dark': '#000000',
            'gradient_start': '#333333',
            'gradient_end': '#666666',
            'reload': '#4A4A4A',
            'wifi_high': '#28A745',
            'wifi_medium': '#FFC107',
            'wifi_low': '#DC3545',
            'wifi_none': '#6C757D',
            'wifi_checking': '#F39C12'
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

        # Iniciar verificación de WiFi
        self.start_wifi_monitoring()

        print(f"Teclado iniciado usando: {self.input_method}")
        self.root.mainloop()

    def detect_input_method(self):
        """Detectar qué método de entrada está disponible"""
        methods = ['ydotool', 'wtype', 'dotool']
        
        for method in methods:
            try:
                result = subprocess.run(['which', method], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=2)
                if result.returncode == 0:
                    # Verificar que realmente funcione
                    if method == 'ydotool':
                        # Verificar permisos del daemon
                        test = subprocess.run(['ydotool', 'type', ''], 
                                            capture_output=True, 
                                            timeout=2)
                        if test.returncode == 0 or test.returncode == 1:
                            return method
                    else:
                        return method
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        return None

    def install_ydotool(self):
        """Intentar instalar ydotool"""
        try:
            print("Intentando instalar ydotool...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ydotool'], check=False)
            
            # Iniciar daemon de ydotool
            print("Iniciando daemon de ydotool...")
            subprocess.Popen(['sudo', 'ydotoold'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(2)
        except Exception as e:
            print(f"Error instalando ydotool: {e}")

    def send_key(self, key):
        """Enviar tecla usando el método disponible"""
        try:
            if self.input_method == 'ydotool':
                return self.send_key_ydotool(key)
            elif self.input_method == 'wtype':
                return self.send_key_wtype(key)
            elif self.input_method == 'dotool':
                return self.send_key_dotool(key)
            else:
                print("No hay método de entrada disponible")
                return False
        except Exception as e:
            print(f"Error enviando tecla: {e}")
            return False

    def send_key_ydotool(self, key):
        """Enviar tecla usando ydotool"""
        # Mapeo de teclas especiales para ydotool
        special_keys = {
            'space': '32:1 32:0',
            'BackSpace': '14:1 14:0',
            'Return': '28:1 28:0',
            'Up': '103:1 103:0',
            'Down': '108:1 108:0',
            'Left': '105:1 105:0',
            'Right': '106:1 106:0',
            'Shift_L': '42:1 42:0',
            'Tab': '15:1 15:0'
        }

        if key in special_keys:
            cmd = ['ydotool', 'key'] + special_keys[key].split()
            subprocess.run(cmd, check=True, timeout=1)
        else:
            subprocess.run(['ydotool', 'type', key], check=True, timeout=1)
        
        return True

    def send_key_wtype(self, key):
        """Enviar tecla usando wtype"""
        special_keys = {
            'space': ' ',
            'BackSpace': '-k backspace',
            'Return': '-k return',
            'Up': '-k up',
            'Down': '-k down',
            'Left': '-k left',
            'Right': '-k right'
        }

        if key in special_keys:
            if special_keys[key].startswith('-k'):
                subprocess.run(['wtype'] + special_keys[key].split(), check=True, timeout=1)
            else:
                subprocess.run(['wtype', special_keys[key]], check=True, timeout=1)
        else:
            subprocess.run(['wtype', key], check=True, timeout=1)
        
        return True

    def send_key_dotool(self, key):
        """Enviar tecla usando dotool"""
        special_keys = {
            'space': 'key space',
            'BackSpace': 'key backspace',
            'Return': 'key enter',
            'Up': 'key up',
            'Down': 'key down',
            'Left': 'key left',
            'Right': 'key right'
        }

        if key in special_keys:
            cmd = f"echo '{special_keys[key]}' | dotool"
            subprocess.run(cmd, shell=True, check=True, timeout=1)
        else:
            cmd = f"echo 'type {key}' | dotool"
            subprocess.run(cmd, shell=True, check=True, timeout=1)
        
        return True

    def get_wifi_signal_strength(self):
        """Obtener nivel de señal WiFi"""
        try:
            # Método 1: nmcli (Network Manager)
            result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SIGNAL', 'dev', 'wifi'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('yes:') or line.startswith('sí:'):
                        try:
                            signal = int(line.split(':')[1])
                            if signal >= 70:
                                return 3
                            elif signal >= 40:
                                return 2
                            elif signal >= 10:
                                return 1
                            else:
                                return 0
                        except (ValueError, IndexError):
                            pass
            
            # Método 2: iwconfig
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'ESSID:' in line and 'off/any' not in line and '""' not in line:
                        for check_line in lines:
                            quality_match = re.search(r'Link Quality[=:](\d+)/(\d+)', check_line)
                            if quality_match:
                                current = int(quality_match.group(1))
                                maximum = int(quality_match.group(2))
                                percentage = (current / maximum) * 100
                                
                                if percentage >= 70:
                                    return 3
                                elif percentage >= 40:
                                    return 2
                                elif percentage >= 10:
                                    return 1
                                else:
                                    return 0
            
            # Método 3: Verificar conectividad básica
            ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'], 
                                       capture_output=True, timeout=4)
            if ping_result.returncode == 0:
                return 2
            
            return 0
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return 0

    def get_wifi_symbol_and_color(self):
        """Obtener símbolo y color según el nivel de señal"""
        if self.wifi_checking:
            return "●●●", self.colors['wifi_checking']
        
        symbols = {
            0: "○○○",
            1: "●○○",
            2: "●●○",
            3: "●●●"
        }
        
        colors = {
            0: self.colors['wifi_none'],
            1: self.colors['wifi_low'],
            2: self.colors['wifi_medium'],
            3: self.colors['wifi_high']
        }
        
        return symbols[self.wifi_signal_strength], colors[self.wifi_signal_strength]

    def update_wifi_button(self):
        """Actualizar el botón de WiFi"""
        if self.wifi_btn is None:
            return
        
        symbol, color = self.get_wifi_symbol_and_color()
        
        self.wifi_btn.config(
            text=symbol,
            bg=color,
            fg='#FFFFFF'
        )

    def wifi_monitor_thread(self):
        """Hilo para monitorear WiFi"""
        while True:
            try:
                if not self.wifi_checking:
                    self.wifi_checking = True
                    self.root.after(0, self.update_wifi_button)
                    
                    self.wifi_signal_strength = self.get_wifi_signal_strength()
                    
                    self.wifi_checking = False
                    self.root.after(0, self.update_wifi_button)
                
                time.sleep(5)
                
            except Exception as e:
                print(f"Error en monitoreo WiFi: {e}")
                self.wifi_signal_strength = 0
                self.wifi_checking = False
                self.root.after(0, self.update_wifi_button)
                time.sleep(8)

    def start_wifi_monitoring(self):
        """Iniciar el monitoreo de WiFi"""
        wifi_thread = threading.Thread(target=self.wifi_monitor_thread, daemon=True)
        wifi_thread.start()

    def on_wifi_click(self):
        """Acción al hacer click en el botón WiFi"""
        try:
            # Intentar diferentes herramientas de configuración de red
            tools = [
                ['nm-connection-editor'],
                ['gnome-control-center', 'network'],
                ['nmtui'],
                ['x-terminal-emulator', '-e', 'nmtui']
            ]
            
            for tool in tools:
                try:
                    subprocess.Popen(tool, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except FileNotFoundError:
                    continue
        except Exception as e:
            print(f"No se pudo abrir configuración de red: {e}")

    def create_floating_button(self):
        """Crear botón flotante principal"""
        self.btn_frame = tk.Frame(
            self.root,
            bg=self.colors['gradient_start'],
            relief='flat',
            bd=0
        )
        self.btn_frame.pack(expand=True, fill='both', padx=5, pady=5)

        button_size = 32 if self.touch_mode else 28

        self.floating_btn = tk.Button(
            self.btn_frame,
            text="⌨",
            font=("Sans", button_size, "bold"),
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
        """Manejar click del botón"""
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

        main_frame = tk.Frame(self.keyboard, bg=self.colors['primary'])
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # Barra de título
        self.title_frame = tk.Frame(main_frame, bg=self.colors['secondary'], height=40, relief='raised', bd=1)
        self.title_frame.pack(fill='x', pady=(0, 10))
        self.title_frame.pack_propagate(False)

        self.make_title_draggable(self.keyboard, self.title_frame)

        title_label = tk.Label(
            self.title_frame,
            text=f"TECLADO VIRTUAL - {self.input_method.upper()}",
            font=("Sans", 12, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['light'],
            cursor='hand2'
        )
        title_label.pack(side='left', padx=10, pady=5)

        self.make_title_draggable(self.keyboard, title_label)

        # Botones de control
        control_frame = tk.Frame(
            self.title_frame,
            bg=self.colors['secondary']
        )
        control_frame.pack(side='right', padx=5, pady=5)

        # Botón WiFi
        self.wifi_btn = tk.Button(
            control_frame,
            text="●●●",
            font=("Sans", 10, "bold"),
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

        # Botón de recarga
        reload_btn = tk.Button(
            control_frame,
            text="⟲",
            font=("Sans", 14, "bold"),
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

        reload_btn.bind("<Enter>", lambda e: reload_btn.config(bg='#FFFFFF', fg='#000000'))
        reload_btn.bind("<Leave>", lambda e: reload_btn.config(bg=self.colors['reload'], fg='#FFFFFF'))

        # Botón cerrar
        close_btn = tk.Button(
            control_frame,
            text="✕",
            font=("Sans", 12, "bold"),
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

        close_btn.bind("<Enter>", lambda e: close_btn.config(bg='#FFFFFF', fg='#000000'))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg='#222222', fg='#FFFFFF'))

        # Frame para teclas
        self.keys_frame = tk.Frame(main_frame, bg=self.colors['primary'])
        self.keys_frame.pack(expand=True, fill='both')

        self.create_all_keys()

    def reload_page(self):
        """Recargar página"""
        try:
            if self.input_method == 'ydotool':
                # Ctrl+R en ydotool
                subprocess.run(['ydotool', 'key', '29:1', '19:1', '19:0', '29:0'], timeout=2)
            elif self.input_method == 'wtype':
                subprocess.run(['wtype', '-M', 'ctrl', '-P', 'r', '-m', 'ctrl'], timeout=2)
            elif self.input_method == 'dotool':
                subprocess.run("echo 'keydown leftctrl\nkey r\nkeyup leftctrl' | dotool", 
                             shell=True, timeout=2)
        except Exception as e:
            print(f"Error recargando página: {e}")

    def create_all_keys(self):
        """Crear layout del teclado"""
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
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ñ', ':', '"'],
                ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?']
            ]
        }

        self.create_main_rows()
        self.create_special_row_with_arrows()

    def create_main_rows(self):
        """Crear filas principales"""
        current_layout = self.key_layouts['shift' if self.caps_lock or self.shift_active else 'normal']

        for row_idx, row in enumerate(current_layout):
            row_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
            row_frame.pack(fill='x', pady=2)

            if row_idx == 0:
                row = row + ['Borrar']
            elif row_idx == 2:
                row = row + ['Enter']
            elif row_idx == 3:
                row = row + ['Shift']

            for col_idx, key in enumerate(row):
                if key in ['Borrar', 'Enter', 'Shift']:
                    if key == 'Borrar':
                        btn = self.create_key_button(row_frame, key, '#222222')
                    elif key == 'Enter':
                        btn = self.create_key_button(row_frame, key, '#444444')
                    elif key == 'Shift':
                        btn = self.create_key_button(row_frame, key, '#666666')

                    btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)
                else:
                    btn = self.create_key_button(row_frame, key, '#333333')
                    btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

    def create_special_row_with_arrows(self):
        """Crear fila especial con Caps Lock, barra espaciadora y flechas"""
        special_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
        special_frame.pack(fill='x', pady=5)

        caps_color = '#555555' if self.caps_lock else '#333333'
        caps_btn = self.create_key_button(special_frame, 'Caps', caps_color)
        caps_btn.pack(side='left', padx=2, pady=2, fill='both')

        space_btn = self.create_key_button(special_frame, 'Espacio', '#444444')
        space_btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

        left_btn = self.create_key_button(special_frame, '←', '#555555')
        left_btn.pack(side='left', padx=2, pady=2, fill='both')

        up_btn = self.create_key_button(special_frame, '↑', '#555555')
        up_btn.pack(side='left', padx=2, pady=2, fill='both')

        down_btn = self.create_key_button(special_frame, '↓', '#555555')
        down_btn.pack(side='left', padx=2, pady=2, fill='both')

        right_btn = self.create_key_button(special_frame, '→', '#555555')
        right_btn.pack(side='left', padx=2, pady=2, fill='both')

    def create_key_button(self, parent, text, bg_color):
        """Crear botón de tecla"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Sans", 12, "bold"),
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

        btn.bind("<Enter>", lambda e: btn.config(bg='#FFFFFF', fg='#000000'))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color, fg='#FFFFFF'))

        return btn

    def handle_key_press(self, key):
        """Manejar pulsaciones de teclas"""
        try:
            if key == 'Caps':
                self.toggle_caps_lock()
                return
            elif key == 'Shift':
                self.toggle_shift()
                return
            elif key == 'Espacio':
                self.send_key('space')
                return
            elif key == 'Borrar':
                self.send_key('BackSpace')
                return
            elif key == 'Enter':
                self.send_key('Return')
                return
            elif key == '↑':
                self.send_key('Up')
                return
            elif key == '↓':
                self.send_key('Down')
                return
            elif key == '←':
                self.send_key('Left')
                return
            elif key == '→':
                self.send_key('Right')
                return

            # Teclas normales
            if self.caps_lock or self.shift_active:
                if key.isalpha():
                    key = key.upper()
            
            self.send_key(key)

            if self.shift_active:
                self.shift_active = False
                self.update_keyboard()

        except Exception as e:
            print(f"Error: {e}")

    def toggle_caps_lock(self):
        """Alternar Caps Lock"""
        self.caps_lock = not self.caps_lock
        self.update_keyboard()

    def toggle_shift(self):
        """Alternar Shift"""
        self.shift_active = not self.shift_active
        self.update_keyboard()

    def update_keyboard(self):
        """Actualizar teclado completo"""
        for widget in self.keys_frame.winfo_children():
            widget.destroy()
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
        """Hacer ventana arrastrable desde la barra de título"""
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
        """Hacer ventana arrastrable"""
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
            drag_distance = ((event.x_root - self.drag_start_x) ** 2 +
                           (event.y_root - self.drag_start_y) ** 2) ** 0.5

            if drag_distance > self.drag_threshold:
                self.is_dragging = True
                self.actually_dragged = True
                x = widget.winfo_pointerx() - widget.x
                y = widget.winfo_pointery() - widget.y
                widget.geometry(f"+{x}+{y}")

        def end_drag(event):
            if not self.actually_dragged:
                self.toggle_keyboard()

            def reset_flags():
                self.is_dragging = False
                self.actually_dragged = False

            widget.after(100, reset_flags)

        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", on_drag)
        widget.bind("<ButtonRelease-1>", end_drag)

        try:
            widget.bind("<TouchBegin>", start_drag)
            widget.bind("<TouchMove>", on_drag)
            widget.bind("<TouchEnd>", end_drag)
        except:
            pass

def main():
    """Función principal"""
    print("=== Teclado Virtual para Wayland ===")
    print("Iniciando...")
    
    try:
        WaylandTouchKeyboard()
    except KeyboardInterrupt:
        print("\nTeclado cerrado por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
