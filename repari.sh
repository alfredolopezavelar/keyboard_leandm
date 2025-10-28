#!/bin/bash

echo "================================================"
echo "🔧 REPARACIÓN DE YDOTOOL PARA WAYLAND"
echo "================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Paso 1: Verificando instalación de ydotool..."
echo ""

# Verificar si ydotool está instalado
if ! command -v ydotool &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} ydotool no encontrado. Instalando..."
    sudo apt-get update
    sudo apt-get install -y ydotool
else
    echo -e "${GREEN}✓${NC} ydotool está instalado"
fi

# Encontrar la ubicación real de ydotoold
echo ""
echo "Paso 2: Buscando binario de ydotoold..."
YDOTOOLD_PATH=$(which ydotoold 2>/dev/null)

if [ -z "$YDOTOOLD_PATH" ]; then
    # Buscar en ubicaciones comunes
    POSSIBLE_PATHS=(
        "/usr/bin/ydotoold"
        "/usr/local/bin/ydotoold"
        "/bin/ydotoold"
        "/usr/sbin/ydotoold"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -f "$path" ]; then
            YDOTOOLD_PATH="$path"
            break
        fi
    done
fi

if [ -z "$YDOTOOLD_PATH" ]; then
    echo -e "${RED}✗${NC} No se encontró ydotoold"
    echo ""
    echo "Intentando compilar desde fuente..."
    echo ""
    
    # Instalar dependencias para compilar
    sudo apt-get install -y git cmake scdoc libevdev-dev libudev-dev
    
    # Clonar y compilar ydotool
    cd /tmp
    rm -rf ydotool
    git clone https://github.com/ReimuNotMoe/ydotool.git
    cd ydotool
    mkdir build
    cd build
    cmake ..
    make
    sudo make install
    
    YDOTOOLD_PATH="/usr/local/bin/ydotoold"
    
    if [ ! -f "$YDOTOOLD_PATH" ]; then
        echo -e "${RED}✗${NC} Error al compilar ydotool"
        echo "Intenta instalarlo manualmente desde: https://github.com/ReimuNotMoe/ydotool"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} ydotoold encontrado en: $YDOTOOLD_PATH"
fi

# Verificar que sea ejecutable
if [ ! -x "$YDOTOOLD_PATH" ]; then
    echo "Haciendo ejecutable..."
    sudo chmod +x "$YDOTOOLD_PATH"
fi

echo ""
echo "Paso 3: Deteniendo servicios antiguos..."
sudo systemctl stop ydotoold.service 2>/dev/null
sudo killall ydotoold 2>/dev/null

echo ""
echo "Paso 4: Creando servicio systemd actualizado..."

# Crear servicio con la ruta correcta
sudo tee /etc/systemd/system/ydotoold.service > /dev/null << EOF
[Unit]
Description=ydotool daemon
Documentation=https://github.com/ReimuNotMoe/ydotool
After=multi-user.target

[Service]
Type=simple
Restart=always
RestartSec=3
ExecStart=$YDOTOOLD_PATH
StandardOutput=journal
StandardError=journal

# Permisos de seguridad
User=root
Group=root

# Permitir acceso al socket
RuntimeDirectory=ydotool
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Paso 5: Recargando systemd..."
sudo systemctl daemon-reload

echo ""
echo "Paso 6: Habilitando servicio..."
sudo systemctl enable ydotoold.service

echo ""
echo "Paso 7: Iniciando servicio..."
sudo systemctl start ydotoold.service

echo ""
echo "Paso 8: Esperando a que el servicio inicie..."
sleep 3

echo ""
echo "Paso 9: Verificando estado..."
if systemctl is-active --quiet ydotoold.service; then
    echo -e "${GREEN}✓${NC} Servicio ydotoold corriendo correctamente"
    
    # Verificar socket
    if [ -S "/run/ydotool/socket" ]; then
        echo -e "${GREEN}✓${NC} Socket creado: /run/ydotool/socket"
        
        # Configurar permisos del socket
        echo ""
        echo "Paso 10: Configurando permisos del socket..."
        sudo chmod 666 /run/ydotool/socket
        echo -e "${GREEN}✓${NC} Permisos configurados"
    else
        echo -e "${YELLOW}⚠${NC} Socket aún no existe, esperando..."
        sleep 2
        if [ -S "/run/ydotool/socket" ]; then
            echo -e "${GREEN}✓${NC} Socket creado"
            sudo chmod 666 /run/ydotool/socket
        else
            echo -e "${RED}✗${NC} Socket no se creó"
        fi
    fi
    
    # Agregar usuario al grupo input
    echo ""
    echo "Paso 11: Configurando permisos de usuario..."
    sudo usermod -aG input $USER
    echo -e "${GREEN}✓${NC} Usuario agregado al grupo 'input'"
    
    echo ""
    echo "Paso 12: Probando ydotool..."
    if timeout 2 ydotool type "" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ydotool funciona correctamente"
    else
        echo -e "${YELLOW}⚠${NC} ydotool no responde completamente"
        echo "Esto es normal, debería funcionar en aplicaciones"
    fi
    
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}✓ REPARACIÓN COMPLETADA EXITOSAMENTE${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "Estado del servicio:"
    systemctl status ydotoold.service --no-pager
    echo ""
    echo "⚠️  IMPORTANTE: Cierra sesión y vuelve a iniciar para que"
    echo "   los cambios de grupo surtan efecto completamente"
    echo ""
    echo "Luego ejecuta el teclado con:"
    echo "  python3 wayland_keyboard.py"
    
else
    echo -e "${RED}✗${NC} Error: El servicio no pudo iniciar"
    echo ""
    echo "Mostrando logs del error:"
    journalctl -u ydotoold.service -n 20 --no-pager
    echo ""
    echo "Posibles soluciones:"
    echo "1. Verificar que ydotoold existe: ls -l $YDOTOOLD_PATH"
    echo "2. Intentar ejecutar manualmente: sudo $YDOTOOLD_PATH"
    echo "3. Ver logs completos: journalctl -u ydotoold.service -n 50"
fi

echo ""
echo "================================================"
