# Usar Python 3.11 como imagen base
FROM python:3.11-slim

WORKDIR /app

# Instalar gcc/g++ solo si tus paquetes lo requieren
RUN apt-get update && apt-get install -y gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias
COPY requirements.txt .
COPY pyproject.toml .

# Instalar paquetes de Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la app
COPY . .

# Exponer el puerto nativo de Streamlit
EXPOSE 8501

# Ejecutar la app usando la configuración de .streamlit/config.toml
CMD ["streamlit", "run", "app.py"]
