#!/bin/bash

# Script de inicio optimizado para deployment en Render
echo "🚀 Iniciando aplicación Streamlit optimizada..."

# Crear directorio .streamlit si no existe
mkdir -p .streamlit

# Crear archivo de configuración optimizado de Streamlit
cat > .streamlit/config.toml << EOF
[server]
headless = true
address = "0.0.0.0"
port = \$PORT
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
base = "light"

[logger]
level = "error"

[client]
caching = true
displayEnabled = true
EOF

# Verificar variables de entorno
PORT=\${PORT:-5000}
echo "📍 Puerto asignado: \$PORT"
echo "🔧 Configuración de producción aplicada"

# Ejecutar la aplicación Streamlit con configuración optimizada
echo "▶️ Iniciando servidor Streamlit..."
exec streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false