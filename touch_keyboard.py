import tkinter as tk
from tkinter import ttk
import subprocess
import sys

class ProfessionalTouchKeyboard:
    def _init_(self):
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
        self.is_dragging = False  # Nueva variable para detectar arrastre
        self.actually_dragged = False  # Variable para detectar arrastre real
        self.touch_mode = True  # Optimizaciones para pantalla táctil
        
        # Colores del tema
        self.colors = {
            'primary': '#2C3E50',
            'secondary': '#34495E', 
            'accent': '#3498DB',
            'success': '#27AE60',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'light': '#ECF0F1',
            'dark': '#2C3E50',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2'
        }
        
        # Configurar interfaz
        self.root.configure(bg=self.colors['primary'])
        
        # Crear botón flotante
        self.create_floating_button()
        
        # Crear ventana del teclado
        self.create_keyboard_window()
        
        # Hacer solo el botón flotante arrastrable (no el teclado completo)
        self.make_draggable(self.root)
        
        # Configurar eventos
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.keyboard.bind("<Escape>", lambda e: self.hide_keyboard())
        
        self.root.mainloop()
    
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
            command=self.on_button_click  # Cambiado a función personalizada
        )
        self.floating_btn.pack(expand=True, fill='both')
        
        # Efectos hover más visibles para touch
        if self.touch_mode:
            self.floating_btn.bind("<ButtonPress-1>", 
                lambda e: self.floating_btn.config(bg=self.colors['gradient_end']))
            self.floating_btn.bind("<ButtonRelease-1>", 
                lambda e: self.root.after(100, lambda: self.floating_btn.config(bg=self.colors['gradient_start'])))
        else:
            self.floating_btn.bind("<Enter>", 
                lambda e: self.floating_btn.config(bg=self.colors['gradient_end']))
            self.floating_btn.bind("<Leave>", 
                lambda e: self.floating_btn.config(bg=self.colors['gradient_start']))
    
    def on_button_click(self):
        """Manejar click del botón - solo toggle si no se está arrastrando - Optimizado para touch"""
        # NO hacer nada aquí - el toggle se maneja en end_drag
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
            text="TECLADO VIRTUAL PROFESIONAL",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['light'],
            cursor='hand2'
        )
        title_label.pack(side='left', padx=10, pady=5)
        
        # Hacer que el label también sea parte del área de arrastre
        self.make_title_draggable(self.keyboard, title_label)
        
        close_btn = tk.Button(
            self.title_frame,
            text="✕",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['danger'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            cursor='hand2',
            command=self.hide_keyboard
        )
        close_btn.pack(side='right', padx=10, pady=5)
        
        # Frame para las teclas
        self.keys_frame = tk.Frame(main_frame, bg=self.colors['primary'])
        self.keys_frame.pack(expand=True, fill='both')
        
        # Crear todas las teclas
        self.create_all_keys()
    
    def create_all_keys(self):
        """Crear todo el layout del teclado"""
        # Layout completo del teclado
        self.key_layouts = {
            'normal': [
                # Fila de números y símbolos
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
                # Fila QWERTY
                ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
                # Fila ASDF
                ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
                # Fila ZXCV
                ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
            ],
            'shift': [
                # Fila de números con símbolos shift
                ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+'],
                # Fila QWERTY mayúsculas
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],
                # Fila ASDF mayúsculas
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"'],
                # Fila ZXCV mayúsculas
                ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?']
            ]
        }
        
        # Crear filas principales
        self.create_main_rows()
        
        # Crear fila de teclas especiales
        self.create_special_row()
        
        # Crear fila de acentos
        self.create_accent_row()
    
    def create_main_rows(self):
        """Crear las filas principales del teclado"""
        current_layout = self.key_layouts['shift' if self.caps_lock or self.shift_active else 'normal']
        
        for row_idx, row in enumerate(current_layout):
            row_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
            row_frame.pack(fill='x', pady=2)
            
            # Teclas especiales al final de algunas filas
            if row_idx == 0:  # Primera fila - añadir Borrar
                row.append('Borrar')
            elif row_idx == 2:  # Tercera fila - añadir Enter
                row.append('Enter')
            elif row_idx == 3:  # Cuarta fila - añadir Shift
                row.append('Shift')
            
            for col_idx, key in enumerate(row):
                if key in ['Borrar', 'Enter', 'Shift']:
                    # Teclas especiales con colores
                    if key == 'Borrar':
                        btn = self.create_key_button(row_frame, key, self.colors['danger'])
                    elif key == 'Enter':
                        btn = self.create_key_button(row_frame, key, self.colors['success'])
                    elif key == 'Shift':
                        btn = self.create_key_button(row_frame, key, self.colors['accent'])
                    
                    # Teclas especiales más anchas
                    btn.grid(row=0, column=col_idx, padx=2, pady=2, sticky='ew', columnspan=2)
                else:
                    # Teclas normales
                    btn = self.create_key_button(row_frame, key, self.colors['secondary'])
                    btn.grid(row=0, column=col_idx, padx=2, pady=2, sticky='ew')
                
                # Configurar columnas
                row_frame.grid_columnconfigure(col_idx, weight=1)
    
    def create_special_row(self):
        """Crear fila con barra espaciadora y Caps Lock"""
        special_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
        special_frame.pack(fill='x', pady=5)
        
        # Caps Lock
        caps_color = self.colors['warning'] if self.caps_lock else self.colors['secondary']
        caps_btn = self.create_key_button(special_frame, 'Caps', caps_color)
        caps_btn.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        
        # Barra espaciadora (muy ancha)
        space_btn = self.create_key_button(special_frame, 'Espacio', self.colors['success'])
        space_btn.grid(row=0, column=1, padx=2, pady=2, sticky='ew', columnspan=8)
        
        # Configurar pesos de columnas
        special_frame.grid_columnconfigure(0, weight=1)
        special_frame.grid_columnconfigure(1, weight=8)
    
    def create_accent_row(self):
        """Crear fila con acentos y caracteres especiales"""
        accent_frame = tk.Frame(self.keys_frame, bg=self.colors['primary'])
        accent_frame.pack(fill='x', pady=2)
        
        # Caracteres con acentos y especiales del español
        accents = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'ü', '¿', '¡']
        
        for i, accent in enumerate(accents):
            btn = self.create_key_button(accent_frame, accent, self.colors['secondary'])
            btn.grid(row=0, column=i, padx=2, pady=2, sticky='ew')
            accent_frame.grid_columnconfigure(i, weight=1)
    
    def create_key_button(self, parent, text, bg_color):
        """Crear botón de tecla individual"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=bg_color,
            fg='white',
            activebackground=self.colors['light'],
            activeforeground=self.colors['dark'],
            relief='flat',
            bd=1,
            cursor='hand2',
            height=2,
            command=lambda: self.handle_key_press(text)
        )
        
        # Efectos hover
        btn.bind("<Enter>", lambda e: btn.config(bg=self.colors['light'], fg=self.colors['dark']))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color, fg='white'))
        
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
        self.floating_btn.config(bg=self.colors['success'])
    
    def hide_keyboard(self):
        """Ocultar teclado"""
        self.keyboard.withdraw()
        self.keyboard_visible = False
        self.floating_btn.config(bg=self.colors['gradient_start'])
    
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
        """Hacer ventana completamente arrastrable (solo para botón flotante) - Optimizado para touch"""
        self.drag_threshold = 10  # Píxeles mínimos para considerar arrastre
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.actually_dragged = False  # Nueva variable para tracking real de arrastre
        
        def start_drag(event):
            widget.x = event.x
            widget.y = event.y
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.is_dragging = False  # Resetear flag de arrastre
            self.actually_dragged = False  # Resetear flag de arrastre real
        
        def on_drag(event):
            # Calcular distancia desde el punto inicial
            drag_distance = ((event.x_root - self.drag_start_x) ** 2 + 
                           (event.y_root - self.drag_start_y) * 2) * 0.5
            
            # Solo marcar como arrastre si se supera el umbral
            if drag_distance > self.drag_threshold:
                self.is_dragging = True
                self.actually_dragged = True  # Marcar que realmente se arrastró
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

