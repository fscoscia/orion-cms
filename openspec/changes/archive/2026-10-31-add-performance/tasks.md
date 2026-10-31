# Tasks

## 1. Caché

- [x] 1.1 `CACHE_URL` en los ajustes (archivos por defecto, Redis, memoria, dummy, prefijo por proyecto, esquema inválido), `.env.example` y extra `redis`; verificar con `pytest tests/test_performance.py` (cada esquema, prefijo distinto con otra clave secreta, error claro)
- [x] 1.2 `PageCacheMiddleware`, generación, `ConditionalGetMiddleware`, señales de invalidación y comando `orion_clear_page_cache`; verificar con `pytest tests/test_performance.py` (segunda visita en caché, sesión, CSRF, vista previa, admin, 404, HEAD, 304 con ETag y con Last-Modified, publicar/despublicar/borrar/publicación programada/menú/datos del sitio vacían, `ORION_PAGE_CACHE_MODELS`, otras claves intactas) y la suite completa
- [x] 1.3 Menús en caché por ubicación e idioma; verificar con `pytest tests/test_performance.py tests/test_site_navigation.py` (sin consultas de menú en la segunda página, ítem actual marcado, cambio de menú visible)

## 2. Consultas

- [x] 2.1 Medir y fijar el presupuesto de consultas; corregir lo que crezca por ítem; verificar con `pytest tests/test_query_budget.py` (portada, página con bloques e imágenes, listado de 2 y de 12 artículos con la misma cantidad, artículo)

## 3. Estáticos y fuentes

- [x] 3.1 WhiteNoise con Brotli (dependencia en `pyproject.toml` y lock, `STORAGES` según `DEBUG`) y `ORION_FONT_PRELOAD`; verificar con `pytest tests/test_performance.py` (precarga con URL de estáticos, nada sin el ajuste) y, con `DEBUG=false` y `collectstatic` en una carpeta temporal, `curl` de la hoja de estilos con `Accept-Encoding: br` (Brotli e `immutable`)

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador y con `curl`: tiempo de respuesta de una página en caché (< 20 ms), `X-Orion-Cache`, 304 al recargar, publicar desde el admin y ver el cambio sin sesión, editora con sesión sin caché, estáticos comprimidos
- [x] 4.2 Actualizar README (caché, `CACHE_URL`, comando, `ORION_PAGE_CACHE_MODELS`, `collectstatic`, fuentes) y CHANGELOG; marcar la Fase 3 como hecha en `docs/especificacion.md` y `CLAUDE.md`; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check` y `makemigrations --check`; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_performance.py` 47 passed; `tests/test_query_budget.py` 4 passed
  (portada ≤ 20, página ≤ 28 igual con 2 y 6 imágenes, listado ≤ 29 igual con 2 y 12
  artículos, artículo ≤ 31).
- Con `DEBUG=false`, `collectstatic` (244 archivos, 1156 procesados) y servidor local:
  hoja de estilos con hash servida con `Content-Encoding: br` (5.787 bytes), gzip (6.548)
  o sin comprimir (33.742), y `Cache-Control: max-age=315360000, public, immutable`.
  Página sin caché 26 ms; en caché, 20 visitas entre 0,9 y 1,3 ms (mediana 1,05 ms),
  `X-Orion-Cache: hit`; 304 con `If-None-Match`; publicar desde otro proceso vació la
  caché y la visita siguiente mostró el título nuevo. Navegador: visita anónima desde la
  caché, editora con sesión sin caché y con la barra de Wagtail, admin con estáticos con
  hash, sin errores de JavaScript ni de estáticos (los de `/media/` son esperables: sin
  `DEBUG` los sirve el servidor web). Hallado y corregido: Leaflet hacía fallar
  `collectstatic` (mapa de código e imágenes faltantes).
- `pipenv run test-postgres` 475 passed; `pipenv run test-mysql` 475 passed.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas, `makemigrations --check` sin cambios y nada para migrar en ambas bases
  (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-performance` cuando esté aprobado.
