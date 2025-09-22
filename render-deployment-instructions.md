# Instrucciones de Deployment para Render

## Configuración Recomendada

### 1. Build Command (en Render Dashboard):
```bash
python -m pip install --upgrade pip && pip install -r render-requirements.txt
```

### 2. Start Command:
```bash
streamlit run app.py --server.headless true --server.address 0.0.0.0
```

### 3. Variables de Entorno (Environment Variables):
- `PYTHON_VERSION`: `3.11`
- `STREAMLIT_SERVER_HEADLESS`: `true`
- `STREAMLIT_SERVER_PORT`: `$PORT` (Render lo asigna automáticamente)

### 4. Runtime Configuration:
- Runtime: **Python 3**
- Region: **Oregon** (más rápido para aplicaciones científicas)
- Plan: **Starter** o superior (librerías científicas necesitan más memoria)

## Explicación de Versiones Optimizadas

- **scikit-learn>=1.2.0**: Compatible con Cython 3.0+, evita errores de compilación
- **scipy>=1.9.0**: Versión con wheels precompilados para la mayoría de plataformas
- **statsmodels>=0.13.0**: Versión estable con dependencias resueltas
- **numpy>=1.21.0**: Base compatible con todas las librerías científicas
- **pandas>=1.5.0**: Versión optimizada que funciona bien con numpy moderno

## Troubleshooting

Si aún hay errores de compilación:

1. **Verificar Python Version**: Asegurar que esté usando Python 3.10 o 3.11
2. **Aumentar Plan**: Usar plan Standard si Starter no tiene suficiente memoria
3. **Build Timeout**: Aumentar timeout de build a 20 minutos en configuración avanzada

## Archivos Necesarios

- `render-requirements.txt`: Dependencias optimizadas para Render
- `app.py`: Aplicación principal
- `.streamlit/config.toml`: Configuración de Streamlit (ya existente)