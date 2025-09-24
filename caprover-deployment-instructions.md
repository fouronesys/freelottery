# Instrucciones para Desplegar en CapRover

## Requisitos Previos

1. **CapRover instalado** en tu VPS
2. **CapRover CLI** instalado en tu máquina local
3. **Git** para clonar/subir el código

## Pasos para el Despliegue

### 1. Preparar el Código

Asegúrate de que tu proyecto esté listo con los archivos necesarios:
- ✅ `Dockerfile`
- ✅ `captain-definition`
- ✅ `.dockerignore`
- ✅ `requirements.txt`

### 2. Conectar con CapRover

```bash
# Instalar CapRover CLI (si no lo tienes)
npm install -g caprover

# Conectar con tu servidor CapRover
caprover serversetup
```

### 3. Crear la Aplicación

```bash
# Crear una nueva aplicación en CapRover
caprover deploy
```

Durante el proceso:
- **Nombre de la app**: `quiniela-loteka` (o el que prefieras)
- **Branch**: `main` o `master`
- **Repository**: Tu repositorio Git

### 4. Configurar Variables de Entorno (Opcional)

En el panel de CapRover, puedes configurar variables como:
- `STREAMLIT_SERVER_HEADLESS=true`
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`

### 5. Configurar Dominio

1. Ve al panel de CapRover
2. Selecciona tu aplicación
3. En la pestaña "HTTP Settings"
4. Habilita HTTPS y configura tu dominio personalizado (opcional)

## Características de la Configuración

### Puerto
- La aplicación se ejecuta en el **puerto 80** dentro del contenedor
- CapRover maneja automáticamente el routing externo

### Base de Datos
- Usa **SQLite** integrada (se crea automáticamente)
- Los datos se persisten en el contenedor
- Para datos persistentes, considera configurar un volumen en CapRover

### Recursos
- **Memoria**: 512MB recomendados mínimo
- **CPU**: 1 core suficiente para uso básico

## Solución de Problemas

### Error de Construcción
```bash
# Ver logs de construcción
caprover logs --app quiniela-loteka
```

### Error de Ejecución
```bash
# Ver logs de la aplicación
caprover logs --app quiniela-loteka --follow
```

### Reconstruir la Aplicación
```bash
# Forzar nueva construcción
caprover deploy --default
```

## Actualizaciones

Para actualizar la aplicación:

```bash
# Desde tu repositorio local
git add .
git commit -m "Actualización"
git push

# Redesplegar
caprover deploy
```

## Notas Importantes

1. **Persistencia de Datos**: Los datos de SQLite se guardan dentro del contenedor. Si necesitas persistencia, configura un volumen en CapRover.

2. **Memoria**: La aplicación usa análisis estadísticos que pueden requerir memoria adicional con datasets grandes.

3. **Tiempo de Construcción**: La primera construcción puede tomar 5-10 minutos debido a las dependencias científicas de Python.

4. **Dominio**: CapRover proporciona un dominio automático, pero puedes configurar uno personalizado.

## Comandos Útiles

```bash
# Ver estado de la aplicación
caprover list

# Ver logs en tiempo real
caprover logs --app quiniela-loteka --follow

# Reiniciar aplicación
caprover restart --app quiniela-loteka

# Eliminar aplicación
caprover remove --app quiniela-loteka
```