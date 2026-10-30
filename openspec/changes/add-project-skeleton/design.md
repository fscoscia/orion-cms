# Design

## Context

El repositorio está vacío salvo la configuración de OpenSpec. Ver proposal.md (Why). La base
debe poder instalarse en proyectos de clientes distintos, así que nada del paquete puede
depender de rutas, dominios o claves de un proyecto concreto.

## Goals / Non-Goals

**Goals:**
- Un paquete instalable cuyo uso por un proyecto sea: instalarlo, importar sus ajustes base,
  incluir sus rutas.
- Configuración por entorno con validación temprana y valores seguros por defecto.
- Una suite de pruebas que corra igual contra PostgreSQL y MySQL.

**Non-Goals:**
- Plantilla de proyecto de cliente (Fase 5); por ahora el proyecto de ejemplo cumple ese rol
  para desarrollo.
- Integración continua (a futuro): los comandos quedan listos para ejecutarse en local.

## Decisions

### Layout `src/` con hatchling
El código vive en `src/orion/` para que las pruebas usen el paquete instalado y no el
directorio de trabajo, evitando que algo funcione en desarrollo y falle instalado. Backend
de build: hatchling, que soporta `src/` sin configuración extra. Alternativa considerada:
setuptools, equivalente pero con más configuración para el mismo resultado.

### Ajustes base importables
`orion.settings.base` define apps, middleware, templates, Wagtail y seguridad a partir del
entorno. Cada proyecto hace `from orion.settings.base import *` y agrega lo propio
(`ROOT_URLCONF`, rutas de archivos, apps del proyecto). Las rutas en disco (`STATIC_ROOT`,
`MEDIA_ROOT`, directorios de templates) las define el proyecto, porque solo él conoce su
`BASE_DIR`. Alternativa considerada: una función que construya los ajustes; más indirecta y
menos familiar para quien conoce Django.

### Lectura del entorno sin librería
Funciones propias y pequeñas en `orion.settings.env` (`env_str`, `env_bool`, `env_list`)
que fallan con `ImproperlyConfigured` ante valores inválidos. Alternativa considerada:
django-environ; agrega una dependencia para algo que son pocas líneas fáciles de probar.

### Dependencia nueva: dj-database-url
Convierte `DATABASE_URL` en el diccionario `DATABASES` para PostgreSQL y MySQL con una sola
variable, que es la convención de casi todos los hostings. Es pequeña, sin dependencias y
mantenida por Jazzband. Alternativa: una variable por dato (motor, host, puerto, usuario,
contraseña, nombre); más variables y más errores de configuración.

### Drivers como extras
`orion[postgres]` instala psycopg (binario) y `orion[mysql]` instala mysqlclient. Cada
proyecto instala solo el que usa; mysqlclient requiere librerías de MySQL para compilarse y
no debe imponerse a quien usa PostgreSQL.

### Validación al arrancar
- Clave secreta faltante, booleanos inválidos y ruta de admin inválida: `ImproperlyConfigured`
  al importar los ajustes, porque sin esos valores la aplicación no puede funcionar.
- SSL y TLS de email a la vez: chequeo del framework de checks de Django
  (`orion.E001`), porque es el mecanismo que Django usa para validar combinaciones de
  ajustes y se ejecuta en `manage.py check` y al arrancar el servidor.

### Endpoint de salud
Vista de Django sin dependencias: abre la conexión, ejecuta `SELECT 1`, responde JSON.
Decorada con `require_safe` (solo GET y HEAD) y `never_cache`. El error se registra en el
log del servidor y no se devuelve al cliente.

### Rutas
`orion.urls` expone la salud, el admin en la ruta configurada, los documentos y, al final,
las páginas de Wagtail. El proyecto incluye `orion.urls` después de sus rutas propias, porque
las páginas de Wagtail capturan cualquier URL.

### Plantilla mínima
Wagtail trae su propia `wagtailcore/page.html` para el tipo de página genérico, con idioma y
título pero sin barra de edición ni `viewport`. La app `orion.core` la reemplaza por una que
extiende `orion/base.html`, el documento base que usarán las fases siguientes. `orion.core`
se instala antes que las apps de Wagtail para que su plantilla tenga prioridad.

### Pruebas en dos bases
pytest + pytest-django usando el proyecto de ejemplo. La base se elige con `DATABASE_URL`;
los scripts de pipenv `test-postgres` y `test-mysql` fijan esa variable. `docker-compose.yml`
levanta PostgreSQL 17 y MySQL 8.4 en puertos 5433 y 3307 para no chocar con bases locales.

### Dependencias de desarrollo
- pytest y pytest-django: estándar para probar proyectos Django.
- ruff: formato y lint en una sola herramienta (convención del proyecto).
- pre-commit: ejecuta Ruff y chequeos básicos antes de cada commit.

## Risks / Trade-offs

- [mysqlclient no compila sin las librerías de MySQL] → documentado en el README; es un
  extra, no afecta a proyectos con PostgreSQL.
- [Versiones locales distintas a producción (MySQL 9 o PostgreSQL 14 instalados con
  Homebrew)] → `docker-compose.yml` con las versiones de referencia; la suite debe pasar en
  ambas.
- [Cambiar la ruta del admin en un sitio en uso rompe marcadores] → solo afecta a usuarios
  del admin; se documenta.
- [El proyecto de ejemplo diverge de un proyecto real] → la plantilla de proyecto de la
  Fase 5 se derivará de él.

## Migration Plan

Sin migraciones propias. Se aplican solo las de Django y Wagtail sobre bases vacías.
