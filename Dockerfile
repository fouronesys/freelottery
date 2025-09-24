# Usar Python 3.11 como imagen base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .
COPY pyproject.toml .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Crear directorio para la configuración de Streamlit
RUN mkdir -p .streamlit

# Crear archivo de configuración de Streamlit
RUN echo '[server]\n\
headless = true\n\
address = "0.0.0.0"\n\
port = 80\n\
enableCORS = false\n\
\n\
[browser]\n\
gatherUsageStats = false' > .streamlit/config.toml

# Exponer puerto 80 (puerto estándar de CapRover)
EXPOSE 80

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=80", "--server.address=0.0.0.0", "--server.headless=true"]