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
        self.root.title("Teclado Virtual Wayland")
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

        self.root.mainloop()

    def type_text_wayland(self, text):
        """Escribir texto usando ydotool (compatible con Wayland)"""
        try:
            subprocess.run(['ydotool', 'type', text], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error con ydotool: {e}")
            return False
        except FileNotFoundError:
            print("ydotool no está instalado o no está en PATH")
            return False

    def press_key_wayland(self, key):
        """Presionar una tecla usando ydotool"""
        try:
            subprocess.run(['ydotool', 'key', key], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error con ydotool: {e}")
            return False
        except FileNotFoundError:
            print("ydotool no está instalado")
            return False

    def get_wifi_signal_strength(self):
        """Obtener nivel de señal WiFi"""
        try:
            # Intentar con nmcli (más común en Wayland)
            result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SIGNAL', 'dev', 'wifi'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('yes:'):
                        signal = line.split(':')[1]
                        try:
                            signal_value = int(signal)
                            if signal_value >= 70:
                                return 3  # Alta
                            elif signal_value >= 40:
                                return 2  # Media
                            elif signal_value >= 10:
                                return 1  # Baja
                        except ValueError:
                            pass
            
            # Método alternativo con iwconfig
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
                        return 1
            
            # Verificar conectividad con ping
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
            # Para GNOME en Wayland
            subprocess.run(['gnome-control-center', 'wifi'], check=False)
        except:
            try:
                # Alternativa con nmcli TUI
                subprocess.run(['gnome-terminal', '--', 'nmtui'], check=False)
            except:
                try:
                    subprocess.run(['nm-connection-editor'], check=False)
                except:
                    print("No se pudo abrir configuración de red")

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
            text="TECLADO VIRTUAL WAYLAND",
            font=("Segoe UI", 12, "bold"),
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

        close_btn.bind("<Enter>", lambda e: close_btn.config(bg='#FFFFFF', fg='#000000'))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg='#222222', fg='#FFFFFF'))

        # Frame para las teclas
        self.keys_frame = tk.Frame(main_frame, bg=self.colors['primary'])
        self.keys_frame.pack(expand=True, fill='both')

        self.create_all_keys()

    def reload_page(self):
        """Recargar página usando ydotool"""
        try:
            # Ctrl+R para Wayland
            self.press_key_wayland('29:1 19:1 19:0 29:0')  # Ctrl+R
        except:
            try:
                # Alternativa F5
                self.press_key_wayland('63:1 63:0')  # F5
            except:
                print("Error: No se pudo recargar la página")

    def create_all_keys(self):
        """Crear todo el layout del teclado"""
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
        """Crear las filas principales del teclado"""
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
        """Crear fila especial con Caps, espacio y flechas"""
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

        btn.bind("<Enter>", lambda e: btn.config(bg='#FFFFFF', fg='#000000'))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color, fg='#FFFFFF'))

        return btn

    def handle_key_press(self, key):
        """Manejar pulsaciones de teclas con ydotool"""
        try:
            if key == 'Caps':
                self.toggle_caps_lock()
                return
            elif key == 'Shift':
                self.toggle_shift()
                return
            elif key == 'Espacio':
                self.press_key_wayland('57:1 57:0')  # Space
                return
            elif key == 'Borrar':
                self.press_key_wayland('14:1 14:0')  # Backspace
                return
            elif key == 'Enter':
                self.press_key_wayland('28:1 28:0')  # Enter
                return
            elif key == '↑':
                self.press_key_wayland('103:1 103:0')  # Up
                return
            elif key == '↓':
                self.press_key_wayland('108:1 108:0')  # Down
                return
            elif key == '←':
                self.press_key_wayland('105:1 105:0')  # Left
                return
            elif key == '→':
                self.press_key_wayland('106:1 106:0')  # Right
                return

            # Para caracteres normales, usar type
            if self.caps_lock or self.shift_active:
                if key.isalpha():
                    key = key.upper()
            
            self.type_text_wayland(key)

            # Desactivar shift después de usar
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
        """Alternar Shift temporal"""
        self.shift_active = not self.shift_active
        self.update_keyboard()

    def update_keyboard(self):
        """Actualizar el teclado completo"""
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
        """Hacer ventana completamente arrastrable"""
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

def main():
    """Función principal con verificación de dependencias"""
    try:
        # Verificar ydotool
        result = subprocess.run(['which', 'ydotool'], check=True, capture_output=True)
        
        # Verificar que el servicio ydotoold esté corriendo
        result = subprocess.run(['pgrep', '-x', 'ydotoold'], capture_output=True)
        if result.returncode != 0:
            print("⚠️  ADVERTENCIA: El demonio ydotoold no está corriendo.")
            print("   Inicia el servicio con: sudo systemctl start ydotool")
            print("   O ejecuta manualmente: sudo ydotoold")
            print("\nIntentando iniciar de todas formas...")
        
        WaylandTouchKeyboard()
        
    except subprocess.CalledProcessError:
        print("❌ ERROR: ydotool no está instalado")
        print("\n📦 Instalar ydotool:")
        print("   Ubuntu/Debian: sudo apt install ydotool")
        print("   Arch: sudo pacman -S ydotool")
        print("   Fedora: sudo dnf install ydotool")
        print("\n🔧 Después de instalar, iniciar el servicio:")
        print("   sudo systemctl enable --now ydotool")
        print("   O manualmente: sudo ydotoold &")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
