# Usar Python 3.11 como base
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instalar gcc/g++ solo si alguna dependencia lo requiere
RUN apt-get update && apt-get install -y gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias
COPY requirements.txt .
COPY pyproject.toml .

# Instalar Python packages
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copiar código de la app
COPY . .

# Exponer el puerto de Streamlit
EXPOSE 8501

# CMD simplificado: usa configuración de .streamlit/config.toml
CMD ["streamlit", "run", "app.py"]
