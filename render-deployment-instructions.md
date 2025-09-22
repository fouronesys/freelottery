# 🚀 Instrucciones de Deployment para Render - Sistema Optimizado

## 📋 Configuración Automática (Recomendada)

El sistema está configurado para despliegue automático usando el archivo `render.yaml`. 

### Método 1: Deploy Automático con render.yaml
1. **Subir código a GitHub**
2. **Conectar repositorio en Render**
3. **El archivo `render.yaml` configurará automáticamente:**
   - Build Command: `python -m pip install --upgrade pip && pip install -r render-requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
   - Plan: Starter (optimizado para aplicaciones científicas)
   - Variables de entorno necesarias

## ⚙️ Configuración Manual (Alternativa)

### 1. Build Command:
```bash
python -m pip install --upgrade pip && pip install -r render-requirements.txt
```

### 2. Start Command:
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### 3. Variables de Entorno:
- `PYTHON_VERSION`: `3.11`
- `STREAMLIT_SERVER_HEADLESS`: `true`
- `STREAMLIT_SERVER_PORT`: `$PORT`
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: `false`

### 4. Configuración de Runtime:
- **Runtime**: Python 3
- **Region**: Oregon (recomendado para mejor rendimiento)
- **Plan**: Starter o superior
- **Auto-Deploy**: Habilitado

## 🎯 Características del Sistema Optimizado

### ✅ Mejoras Implementadas:
- **ID de Usuario Automático**: Sistema de notificaciones sin requerir entrada manual
- **Persistencia de Sesión**: URLs personalizadas para mantener acceso a predicciones
- **Base de Datos Optimizada**: SQLite con WAL mode y configuraciones de rendimiento
- **Cache Inteligente**: Análisis complejos cacheados por 1 hora
- **Configuración de Producción**: Streamlit optimizado para deployment

### ⚡ Optimizaciones de Rendimiento:
- SQLite WAL mode para mejor concurrencia
- Cache expandido (10MB) y memory mapping
- Índices optimizados en todas las tablas críticas
- Configuraciones de Streamlit para producción

## 🔧 Comandos Principales

### Start Command (Producción):
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### Build Command (Optimizado):
```bash
python -m pip install --upgrade pip && pip install -r render-requirements.txt
```

### Local Development:
```bash
streamlit run app.py --server.port 5000
```

## 📂 Archivos de Configuración

- **`render.yaml`**: Configuración automática de deployment
- **`render-requirements.txt`**: Dependencias optimizadas para Render
- **`start.sh`**: Script de inicio con configuración automática
- **`app.py`**: Aplicación principal con sistema de ID automático
- **`.streamlit/config.toml`**: Se genera automáticamente en deployment

## 🚨 Troubleshooting

### Errores Comunes:
1. **Build Timeout**: Usar plan Starter en lugar de Free
2. **Memory Issues**: Verificar que render-requirements.txt esté siendo usado
3. **Port Issues**: El sistema usa automáticamente `$PORT` de Render

### Verificaciones:
- ✅ Archivo `render.yaml` en la raíz del repositorio
- ✅ Archivo `render-requirements.txt` presente
- ✅ Script `start.sh` con permisos de ejecución
- ✅ Repository conectado en Render dashboard

## 🎉 Post-Deployment

### Funcionalidades Automáticas:
- Sistema de notificaciones funciona automáticamente
- Base de datos SQLite se inicializa en el primer acceso
- URLs personalizadas se generan para cada usuario
- Cache optimizado para análisis estadísticos

### Monitoreo:
- Logs disponibles en Render Dashboard
- Métricas de rendimiento automáticas
- Auto-restart en caso de errores