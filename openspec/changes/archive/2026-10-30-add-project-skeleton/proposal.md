# Proposal

## Why

Orion todavía no existe como código. Antes de construir el modelo de contenido (Fase 1)
hace falta una base instalable, configurable por entorno y verificable en PostgreSQL y
MySQL, para que cada fase siguiente se apoye en una estructura estable y en pruebas que
corren desde el primer día.

## What Changes

- Paquete Python `orion` (layout `src/`) instalable con pip desde GitHub, con extras
  opcionales para el driver de PostgreSQL y el de MySQL.
- Ajustes base reutilizables que cada proyecto de cliente importa y extiende, leyendo la
  configuración sensible desde variables de entorno.
- Validación al arrancar: el sitio se niega a iniciar con configuración insegura o
  contradictoria (sin clave secreta en producción, SSL y TLS de email a la vez).
- Valores seguros por defecto en producción (cookies seguras, sin modo debug).
- Rutas base: admin de Wagtail en una ruta configurable, documentos y páginas.
- Endpoint de salud para monitoreo.
- Plantilla mínima para que una página de Wagtail sin plantilla propia se muestre.
- Proyecto de ejemplo (fuera del paquete) para desarrollar y probar la base.
- Herramientas de calidad: Ruff, pytest con pytest-django, pre-commit, y la suite
  ejecutable contra PostgreSQL y MySQL. `docker-compose.yml` opcional con las dos bases.
- Documentación de desarrollo: README, AGENTS.md, CHANGELOG y `.env.example`.

**Fuera del alcance:** modelos de contenido, bloques, menús y multi-idioma (Fase 1);
experiencia del editor (Fase 2); medios, caché, Tailwind y SEO (Fase 3); formularios,
buscador e integraciones (Fase 4); headers de seguridad avanzados (HSTS, CSP), 2FA,
backups, instalador y plantilla de proyecto de cliente (Fase 5); integración continua y
publicación del paquete (a futuro).

## Capabilities

### New Capabilities
- `project-configuration`: cómo un proyecto obtiene su configuración del entorno, qué
  valores son obligatorios y qué combinaciones inseguras impiden arrancar.
- `health-check`: endpoint que informa si la aplicación y su base de datos responden.
- `site-routing`: rutas base que Orion expone a cada proyecto (admin configurable,
  documentos, páginas de Wagtail) y la presentación mínima de una página.

### Modified Capabilities
- Ninguna (es el primer cambio del proyecto).

## Impact

- Código nuevo: `src/orion/`, `example/`, `tests/`.
- Dependencias de ejecución: Django 5.2, Wagtail 7.4, dj-database-url; drivers psycopg
  y mysqlclient como extras.
- Dependencias de desarrollo: pytest, pytest-django, ruff, pre-commit.
- Sin migraciones propias de Orion; solo las de Django y Wagtail en bases vacías.
