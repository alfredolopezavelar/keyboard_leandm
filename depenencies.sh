#!/bin/bash

echo "================================================"
echo "Instalador de Teclado Virtual para Wayland"
echo "Raspberry Pi Edition"
echo "================================================"
echo ""

# Verificar si se ejecuta como root para instalación de paquetes
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Algunas funciones requieren permisos de root"
    echo "Se solicitará contraseña cuando sea necesario"
fi

echo "📦 Paso 1: Actualizando repositorios..."
sudo apt-get update

echo ""
echo "📦 Paso 2: Instalando dependencias básicas..."
sudo apt-get install -y python3 python3-tk

echo ""
echo "📦 Paso 3: Instalando ydotool (herramienta principal para Wayland)..."
sudo apt-get install -y ydotool

echo ""
echo "🔧 Paso 4: Configurando ydotool..."

# Crear directorio para el socket si no existe
sudo mkdir -p /run/ydotool

# Verificar si ydotoold ya está corriendo
if pgrep -x "ydotoold" > /dev/null; then
    echo "✓ ydotoold ya está en ejecución"
else
    echo "Iniciando ydotoold..."
    sudo ydotoold &
    sleep 2
    
    if pgrep -x "ydotoold" > /dev/null; then
        echo "✓ ydotoold iniciado correctamente"
    else
        echo "⚠️  Error al iniciar ydotoold"
    fi
fi

# Configurar ydotool para que inicie automáticamente
echo ""
echo "🔧 Paso 5: Configurando inicio automático de ydotoold..."

# Crear servicio systemd para ydotoold
sudo tee /etc/systemd/system/ydotoold.service > /dev/null << 'EOF'
[Unit]
Description=ydotool daemon
After=multi-user.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/ydotoold
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl enable ydotoold.service
sudo systemctl start ydotoold.service

echo ""
echo "🔧 Paso 6: Configurando permisos..."

# Agregar usuario actual al grupo input (puede ser necesario para ydotool)
sudo usermod -aG input $USER

echo ""
echo "📦 Paso 7: Instalando herramientas de red opcionales..."
sudo apt-get install -y network-manager nmtui

# Intentar instalar herramientas alternativas (wtype como backup)
echo ""
echo "📦 Paso 8: Instalando herramientas alternativas..."
sudo apt-get install -y wtype 2>/dev/null || echo "wtype no disponible en repositorios"

echo ""
echo "✅ Instalación completada!"
echo ""
echo "================================================"
echo "INSTRUCCIONES DE USO:"
echo "================================================"
echo ""
echo "1. Hacer el script ejecutable:"
echo "   chmod +x wayland_keyboard.py"
echo ""
echo "2. Ejecutar el teclado:"
echo "   python3 wayland_keyboard.py"
echo "   o"
echo "   ./wayland_keyboard.py"
echo ""
echo "3. Para autoejecutar al inicio:"
echo "   - Agregar a Autostart de tu entorno de escritorio"
echo "   - O agregar a ~/.config/autostart/"
echo ""
echo "================================================"
echo "IMPORTANTE:"
echo "================================================"
echo ""
echo "⚠️  Puede que necesites CERRAR SESIÓN y volver a"
echo "   iniciar para que los cambios de grupo surtan efecto"
echo ""
echo "Si el teclado no funciona:"
echo "1. Verifica que ydotoold esté corriendo:"
echo "   systemctl status ydotoold"
echo ""
echo "2. Reinicia el servicio si es necesario:"
echo "   sudo systemctl restart ydotoold"
echo ""
echo "3. Verifica que estés usando Wayland:"
echo "   echo \$XDG_SESSION_TYPE"
echo "   (debe mostrar 'wayland')"
echo ""
echo "================================================"
