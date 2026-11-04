## Why

Un sitio Orion no tiene buscador público. La especificación pide uno sobre
la propia base de datos, sin servicios externos, que entienda el español en PostgreSQL,
respete idioma y estado publicado, permita al editor destacar resultados y le muestre qué
busca la gente y qué no encuentra. Hoy el índice de Wagtail solo guarda el título de las
páginas. Es el cambio 3 de la Fase 4.

## What Changes

- **Índice completo**: el texto de los bloques del cuerpo, el resumen y la introducción
  de páginas, artículos, listados y formularios.
- **Español**: en PostgreSQL, la búsqueda usa la configuración de idioma del idioma base
  ("médicos" encuentra "médico"); configurable por proyecto. En MySQL usa su búsqueda de
  texto completo, más básica.
- **Búsqueda aproximada opcional**: si la base tiene la extensión `pg_trgm` (se activa con
  `manage.py enable_trigram` cuando el hosting lo permite), una búsqueda sin resultados
  se repite tolerando errores de tipeo.
- **Página de resultados** en `/buscar/` (y su equivalente traducido en cada idioma):
  solo páginas publicadas y públicas del idioma de la visita, con título, resumen y tipo,
  paginadas, con filtro por tipo (páginas o artículos) y resultados destacados primero.
- **Buscador en el encabezado**, que puede apagarse por proyecto.
- **Resultados destacados** (`wagtail.contrib.search_promotions`): Editores y
  Administradores eligen qué páginas aparecen primero para una búsqueda.
- **Informe de búsquedas** en Informes, para los administradores del sitio: las más
  frecuentes de los últimos 30 días y las que no dieron resultados.

**Fuera del alcance:** Elasticsearch u OpenSearch (a futuro); autocompletado mientras se
escribe; búsqueda en documentos PDF o en imágenes; sinónimos; búsqueda dentro de los
envíos de formularios (ya está en la bandeja).

## Capabilities

### New Capabilities
- `site-search`: qué se indexa, cómo se busca en cada base, la página de resultados, el
  buscador del encabezado, los resultados destacados y el informe de búsquedas.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** app `orion.search` (vista y plantilla de resultados, modelo de
  búsquedas sin resultados, informe, configuración de idioma) y la ruta traducida en
  `orion.urls`.
- **Código modificado:** `search_fields` de las páginas de Orion y de `FormPage`,
  `WAGTAILSEARCH_BACKENDS` en los ajustes base, encabezado (`header.html`), permisos de
  Editores y Administradores para destacados, README y CHANGELOG.
- **Dependencias nuevas:** ninguna (`wagtail.search` y `wagtail.contrib.search_promotions`).
- **Migraciones:** las de `wagtailsearchpromotions`, la tabla de búsquedas sin resultados
  y los permisos de destacados. Después de actualizar, correr `manage.py update_index`
  para indexar el contenido existente.
