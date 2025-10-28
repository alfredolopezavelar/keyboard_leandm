#!/usr/bin/env python3
"""
Teclado Virtual para Wayland - Versión Sin Daemon
Esta versión usa métodos alternativos que no requieren ydotoold corriendo
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import threading
import time
import re
import os

class SimplifiedWaylandKeyboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Teclado Virtual - Wayland (Simplificado)")
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

        # Detectar método de entrada disponible
        self.input_method = self.detect_input_method()
        
        if not self.input_method:
            print("ADVERTENCIA: No se encontró método de entrada óptimo")
            print("El teclado funcionará en modo básico usando wtype o entrada directa")
            self.input_method = "basic"

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

        self.root.configure(bg=self.colors['primary'])
        
        self.create_floating_button()
        self.create_keyboard_window()
        self.make_draggable(self.root)

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.keyboard.bind("<Escape>", lambda e: self.hide_keyboard())

        self.start_wifi_monitoring()

        print(f"Teclado iniciado - Método: {self.input_method}")
        self.root.mainloop()

    def detect_input_method(self):
        """Detectar método de entrada disponible sin requerir daemon"""
        methods = ['wtype', 'dotool', 'ydotool']
        
        for method in methods:
            try:
                result = subprocess.run(['which', method], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=2)
                if result.returncode == 0:
                    # Para wtype y dotool, verificar que funcionen
                    if method == 'wtype':
                        test = subprocess.run(['wtype', '-h'], 
                                            capture_output=True, 
                                            timeout=2)
                        if test.returncode in [0, 1]:  # 0 o 1 son ok para -h
                            return method
                    elif method == 'dotool':
                        return method
                    elif method == 'ydotool':
                        # Verificar si funciona sin daemon (algunos sistemas)
                        test = subprocess.run(['ydotool', 'type', ''], 
                                            capture_output=True, 
                                            timeout=2)
                        if test.returncode in [0, 1]:
                            return method
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        return None

    def send_key(self, key):
        """Enviar tecla usando el método más simple disponible"""
        try:
            if self.input_method == 'wtype':
                return self.send_key_wtype(key)
            elif self.input_method == 'dotool':
                return self.send_key_dotool(key)
            elif self.input_method == 'ydotool':
                return self.send_key_ydotool(key)
            else:
                # Modo básico: copiar al portapapeles
                return self.send_key_clipboard(key)
        except Exception as e:
            print(f"Error enviando tecla: {e}")
            return False

    def send_key_wtype(self, key):
        """Enviar tecla usando wtype (no requiere daemon)"""
        special_keys = {
            'space': ['-k', 'space'],
            'BackSpace': ['-k', 'backspace'],
            'Return': ['-k', 'return'],
            'Up': ['-k', 'up'],
            'Down': ['-k', 'down'],
            'Left': ['-k', 'left'],
            'Right': ['-k', 'right'],
            'Tab': ['-k', 'tab']
        }

        try:
            if key in special_keys:
                subprocess.run(['wtype'] + special_keys[key], 
                             check=True, timeout=1,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['wtype', '--', key], 
                             check=True, timeout=1,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def send_key_dotool(self, key):
        """Enviar tecla usando dotool"""
        special_keys = {
            'space': 'key space',
            'BackSpace': 'key backspace',
            'Return': 'key enter',
            'Up': 'key up',
            'Down': 'key down',
            'Left': 'key left',
            'Right': 'key right',
            'Tab': 'key tab'
        }

        try:
            if key in special_keys:
                cmd = f"echo '{special_keys[key]}' | dotool"
            else:
                # Escapar caracteres especiales
                escaped_key = key.replace("'", "'\\''")
                cmd = f"echo 'type {escaped_key}' | dotool"
            
            subprocess.run(cmd, shell=True, check=True, timeout=1,
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def send_key_ydotool(self, key):
        """Enviar tecla usando ydotool (puede funcionar sin daemon en algunos casos)"""
        special_keys = {
            'space': '32:1 32:0',
            'BackSpace': '14:1 14:0',
            'Return': '28:1 28:0',
            'Up': '103:1 103:0',
            'Down': '108:1 108:0',
            'Left': '105:1 105:0',
            'Right': '106:1 106:0',
            'Tab': '15:1 15:0'
        }

        try:
            if key in special_keys:
                cmd = ['ydotool', 'key'] + special_keys[key].split()
                subprocess.run(cmd, check=True, timeout=1,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['ydotool', 'type', '--', key], 
                             check=True, timeout=1,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def send_key_clipboard(self, key):
        """Método de respaldo: copiar al portapapeles"""
        if key in ['space', 'BackSpace', 'Return', 'Up', 'Down', 'Left', 'Right', 'Tab']:
            print(f"Modo básico: no se pueden enviar teclas especiales ({key})")
            return False
        
        try:
            # Usar wl-copy si está disponible
            subprocess.run(['wl-copy', '--', key], 
                         check=True, timeout=1,
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            print(f"Copiado al portapapeles: {key} (presiona Ctrl+V para pegar)")
            return True
        except:
            try:
                # Alternativa con xclip (funciona en algunos casos)
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=key.encode(), 
                             check=True, timeout=1,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                return True
            except:
                print(f"No se pudo enviar la tecla: {key}")
                return False

    def get_wifi_signal_strength(self):
        """Obtener nivel de señal WiFi"""
        try:
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
            
            ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'], 
                                       capture_output=True, timeout=4)
            if ping_result.returncode == 0:
                return 2
            
            return 0
            
        except:
            return 0

    def get_wifi_symbol_and_color(self):
        """Obtener símbolo y color según el nivel de señal"""
        if self.wifi_checking:
            return "●●●", self.colors['wifi_checking']
        
        symbols = {0: "○○○", 1: "●○○", 2: "●●○", 3: "●●●"}
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
        self.wifi_btn.config(text=symbol, bg=color, fg='#FFFFFF')

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
            except:
                self.wifi_signal_strength = 0
                self.wifi_checking = False
                self.root.after(0, self.update_wifi_button)
                time.sleep(8)

    def start_wifi_monitoring(self):
        """Iniciar el monitoreo de WiFi"""
        wifi_thread = threading.Thread(target=self.wifi_monitor_thread, daemon=True)
        wifi_thread.start()

    def on_wifi_click(self):
        """Abrir configuración de red"""
        tools = [
            ['nm-connection-editor'],
            ['gnome-control-center', 'network'],
            ['x-terminal-emulator', '-e', 'nmtui']
        ]
        
        for tool in tools:
            try:
                subprocess.Popen(tool, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            except:
                continue

    def create_floating_button(self):
        """Crear botón flotante"""
        self.btn_frame = tk.Frame(self.root, bg=self.colors['gradient_start'], relief='flat', bd=0)
        self.btn_frame.pack(expand=True, fill='both', padx=5, pady=5)

        button_size = 32 if self.touch_mode else 28

        self.floating_btn = tk.Button(
            self.btn_frame, text="⌨",
            font=("Sans", button_size, "bold"),
            bg=self.colors['gradient_start'], fg='white',
            activebackground=self.colors['gradient_end'],
            activeforeground='white', relief='flat', bd=0,
            cursor='hand2', command=self.on_button_click
        )
        self.floating_btn.pack(expand=True, fill='both')

    def on_button_click(self):
        pass

    def create_keyboard_window(self):
        """Crear ventana del teclado"""
        self.keyboard = tk.Toplevel(self.root)
        self.keyboard.withdraw()
        self.keyboard.overrideredirect(True)
        self.keyboard.attributes("-topmost", True)
        self.keyboard.attributes("-alpha", 0.98)
        self.keyboard.geometry("1100x400+100+400")
        self.keyboard.configure(bg=self.colors['primary'])

        main_frame = tk.Frame(self.keyboard, bg=self.colors['primary'])
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        self.title_frame = tk.Frame(main_frame, bg=self.colors['secondary'], 
                                    height=40, relief='raised', bd=1)
        self.title_frame.pack(fill='x', pady=(0, 10))
        self.title_frame.pack_propagate(False)

        self.make_title_draggable(self.keyboard, self.title_frame)

        title_label = tk.Label(
            self.title_frame,
            text=f"TECLADO WAYLAND - {self.input_method.upper()}",
            font=("Sans", 12, "bold"),
            bg=self.colors['secondary'], fg=self.colors['light'],
            cursor='hand2'
        )
        title_label.pack(side='left', padx=10, pady=5)
        self.make_title_draggable(self.keyboard, title_label)

        control_frame = tk.Frame(self.title_frame, bg=self.colors['secondary'])
        control_frame.pack(side='right', padx=5, pady=5)

        self.wifi_btn = tk.Button(
            control_frame, text="●●●", font=("Sans", 10, "bold"),
            bg=self.colors['wifi_checking'], fg='#FFFFFF',
            activebackground='#FFFFFF', activeforeground='#000000',
            relief='flat', bd=0, width=4, cursor='hand2',
            command=self.on_wifi_click
        )
        self.wifi_btn.pack(side='left', padx=2)

        reload_btn = tk.Button(
            control_frame, text="⟲", font=("Sans", 14, "bold"),
            bg=self.colors['reload'], fg='#FFFFFF',
            activebackground='#FFFFFF', activeforeground='#000000',
            relief='flat', bd=0, width=3, cursor='hand2',
            command=self.reload_page
        )
        reload_btn.pack(side='left', padx=2)

        close_btn = tk.Button(
            control_frame, text="✕", font=("Sans", 12, "bold"),
            bg='#222222', fg='#FFFFFF',
            activebackground='#FFFFFF', activeforeground='#000000',
            relief='flat', bd=0, width=3, cursor='hand2',
            command=self.hide_keyboard
        )
        close_btn.pack(side='left', padx=2)

        self.keys_frame = tk.Frame(main_frame, bg=self.colors['primary'])
        self.keys_frame.pack(expand=True, fill='both')

        self.create_all_keys()

    def reload_page(self):
        """Recargar página web"""
        try:
            if self.input_method == 'wtype':
                subprocess.run(['wtype', '-M', 'ctrl', '-P', 'r', '-m', 'ctrl'], timeout=2)
            elif self.input_method == 'dotool':
                subprocess.run("echo 'keydown leftctrl\nkey r\nkeyup leftctrl' | dotool", 
                             shell=True, timeout=2)
            elif self.input_method == 'ydotool':
                subprocess.run(['ydotool', 'key', '29:1', '19:1', '19:0', '29:0'], timeout=2)
        except:
            print("No se pudo recargar")

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

            for key in row:
                if key in ['Borrar', 'Enter', 'Shift']:
                    colors = {'Borrar': '#222222', 'Enter': '#444444', 'Shift': '#666666'}
                    btn = self.create_key_button(row_frame, key, colors[key])
                    btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)
                else:
                    btn = self.create_key_button(row_frame, key, '#333333')
                    btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

    def create_special_row_with_arrows(self):
        """Crear fila especial"""
        special_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
        special_frame.pack(fill='x', pady=5)

        caps_color = '#555555' if self.caps_lock else '#333333'
        caps_btn = self.create_key_button(special_frame, 'Caps', caps_color)
        caps_btn.pack(side='left', padx=2, pady=2, fill='both')

        space_btn = self.create_key_button(special_frame, 'Espacio', '#444444')
        space_btn.pack(side='left', padx=2, pady=2, fill='both', expand=True)

        for arrow in ['←', '↑', '↓', '→']:
            btn = self.create_key_button(special_frame, arrow, '#555555')
            btn.pack(side='left', padx=2, pady=2, fill='both')

    def create_key_button(self, parent, text, bg_color):
        """Crear botón de tecla"""
        btn = tk.Button(
            parent, text=text, font=("Sans", 12, "bold"),
            bg=bg_color, fg='#FFFFFF',
            activebackground='#FFFFFF', activeforeground='#000000',
            relief='flat', bd=1, cursor='hand2', height=2,
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
            elif key in ['↑', '↓', '←', '→']:
                arrow_map = {'↑': 'Up', '↓': 'Down', '←': 'Left', '→': 'Right'}
                self.send_key(arrow_map[key])
                return

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
        self.caps_lock = not self.caps_lock
        self.update_keyboard()

    def toggle_shift(self):
        self.shift_active = not self.shift_active
        self.update_keyboard()

    def update_keyboard(self):
        for widget in self.keys_frame.winfo_children():
            widget.destroy()
        self.create_all_keys()

    def toggle_keyboard(self):
        if self.keyboard_visible:
            self.hide_keyboard()
        else:
            self.show_keyboard()

    def show_keyboard(self):
        self.keyboard.deiconify()
        self.keyboard_visible = True
        self.floating_btn.config(bg='#444444')

    def hide_keyboard(self):
        self.keyboard.withdraw()
        self.keyboard_visible = False
        self.floating_btn.config(bg='#333333')

    def make_title_draggable(self, window, title_widget):
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
        self.drag_threshold = 10

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
            widget.after(100, lambda: setattr(self, 'is_dragging', False) or 
                              setattr(self, 'actually_dragged', False))

        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", on_drag)
        widget.bind("<ButtonRelease-1>", end_drag)

def main():
    print("=== Teclado Virtual Simplificado para Wayland ===")
    try:
        SimplifiedWaylandKeyboard()
    except KeyboardInterrupt:
        print("\nCerrado por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
