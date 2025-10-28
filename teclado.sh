#!/bin/bash

echo "🎹 Teclado Virtual Wayland - Iniciador Inteligente"
echo "=================================================="
echo ""

# Función para encontrar el socket de ydotool
find_ydotool_socket() {
    # Posibles ubicaciones del socket
    local socket_locations=(
        "/run/user/$UID/.ydotool_socket"
        "/tmp/.ydotool_socket"
        "/run/ydotool/.ydotool_socket"
        "$HOME/.ydotool_socket"
    )
    
    for socket in "${socket_locations[@]}"; do
        if [ -S "$socket" ]; then
            echo "$socket"
            return 0
        fi
    done
    
    return 1
}

# Verificar que ydotoold esté corriendo
if ! pgrep -x ydotoold > /dev/null; then
    echo "❌ ydotoold no está corriendo"
    echo ""
    echo "🔧 Intentando iniciar..."
    
    # Detener cualquier servicio previo
    sudo systemctl stop ydotoold 2>/dev/null
    systemctl --user stop ydotool 2>/dev/null
    
    # Iniciar con socket en ubicación correcta
    sudo mkdir -p /run/user/$UID
    sudo chown $USER:$USER /run/user/$UID
    
    echo "   Iniciando ydotoold con socket en /run/user/$UID/..."
    YDOTOOL_SOCKET="/run/user/$UID/.ydotool_socket" sudo -E ydotoold &
    
    sleep 2
    
    if ! pgrep -x ydotoold > /dev/null; then
        echo "❌ No se pudo iniciar ydotoold"
        exit 1
    fi
    
    echo "   ✅ ydotoold iniciado"
fi

# Buscar el socket
echo "🔍 Buscando socket de ydotool..."
SOCKET_PATH=$(find_ydotool_socket)

if [ -z "$SOCKET_PATH" ]; then
    echo "❌ No se encontró el socket de ydotool"
    echo ""
    echo "📋 Información de depuración:"
    echo "   ydotoold corriendo: $(pgrep -x ydotoold && echo 'SÍ' || echo 'NO')"
    echo "   UID: $UID"
    echo ""
    echo "🔧 SOLUCIÓN MANUAL:"
    echo "   1. Detener servicio actual:"
    echo "      sudo systemctl stop ydotoold"
    echo ""
    echo "   2. Iniciar con socket correcto:"
    echo "      sudo YDOTOOL_SOCKET=/run/user/$UID/.ydotool_socket ydotoold &"
    echo ""
    echo "   3. Ejecutar este script de nuevo"
    exit 1
fi

echo "   ✅ Socket encontrado: $SOCKET_PATH"

# Exportar variable de entorno
export YDOTOOL_SOCKET="$SOCKET_PATH"

echo "   ✅ Variable YDOTOOL_SOCKET configurada"
echo ""
echo "🚀 Iniciando teclado virtual..."
echo ""

# Obtener directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Iniciar el teclado con la variable de entorno
cd "$SCRIPT_DIR"
python3 wayland_keyboard.py

echo ""
echo "✅ Teclado cerrado"
