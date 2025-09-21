#!/bin/bash

# Script de inicio para deployment en Render
echo "Iniciando aplicación Streamlit..."

# Crear directorio .streamlit si no existe
mkdir -p .streamlit

# Crear archivo de configuración de Streamlit para deployment
cat > .streamlit/config.toml << EOF
[server]
headless = true
address = "0.0.0.0"
port = 5000

[browser]
gatherUsageStats = false

[theme]
base = "light"
EOF

# Ejecutar la aplicación Streamlit
# Usar puerto de entorno de Render o default 5000 
PORT=${PORT:-5000}
echo "Iniciando Streamlit en puerto $PORT"
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true