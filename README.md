🖥️ Teclado Virtual Profesional para Raspberry Pi

Un teclado virtual moderno y minimalista diseñado especialmente para pantallas táctiles en Raspberry Pi (u otros sistemas Linux con entorno gráfico).
Incluye un indicador dinámico de señal WiFi, soporte para transparencia, arrastre, y teclas interactivas simuladas mediante xdotool.

🚀 Características principales

✅ Diseño optimizado para pantallas táctiles (botones grandes y cómodos).

💡 Interfaz translúcida (glass effect) con escala de grises profesional.

🔠 Soporte completo para teclas especiales: Shift, Caps Lock, Enter, Backspace, Espacio, Flechas.

📶 Indicador de señal WiFi con detección automática cada 5 segundos:

🔴 Baja señal

🟡 Media señal

🟢 Alta señal

⚪ Sin conexión

🔄 Botón de recarga de página (Ctrl+R o F5) mediante xdotool.

⚙️ Acceso rápido a la configuración de red (nm-connection-editor, gnome-control-center o nmtui).

📦 Sin dependencias externas de interfaz gráfica (usa solo tkinter).

🧰 Requisitos del sistema

Este teclado está pensado para ejecutarse en Raspberry Pi OS (o cualquier distribución Linux con entorno gráfico).
Asegúrate de tener instaladas las siguientes dependencias:

sudo apt update
sudo apt install python3 python3-tk xdotool wireless-tools network-manager

🧠 Estructura del proyecto
📁 virtual-keyboard/
├── teclado_virtual.py    # Script principal del teclado
├── README.md             # Documentación del proyecto

🖱️ Uso

Clona este repositorio:

git clone https://github.com/<tu-usuario>/virtual-keyboard.git
cd virtual-keyboard


Ejecuta el teclado:

python3 teclado_virtual.py


Interacción:

Presiona el botón ⌨ flotante para mostrar/ocultar el teclado.

Usa las teclas táctiles para escribir en cualquier campo de texto activo.

El botón ✕ cierra el teclado.

El icono de WiFi abre la configuración de red.

El botón ⟲ recarga la ventana activa (como presionar F5).

🧩 Personalización

Puedes ajustar parámetros en el código:

Parámetro	Descripción	Valor por defecto
self.root.attributes("-alpha", 0.7)	Transparencia del botón flotante	0.7
self.keyboard.attributes("-alpha", 0.98)	Transparencia del teclado	0.98
self.colors	Paleta de colores personalizada	Escala de grises
self.touch_mode	Modo táctil (botones grandes)	True
⚡ Consejos

Si xdotool no funciona correctamente, asegúrate de tener entorno gráfico activo (X11).

Puedes agregar un autostart para lanzar el teclado al iniciar tu Raspberry Pi:

nano ~/.config/lxsession/LXDE-pi/autostart


Y agrega al final:

@python3 /home/pi/virtual-keyboard/teclado_virtual.py

🧑‍💻 Autor

Desarrollado por Jesus Alejandro Ocegueda Melin
📘 Estudiante de Ingeniería en Mecatrónica
🔗 GitHub
