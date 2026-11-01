# Tasks

## 1. Índice y configuración

- [x] 1.1 `search_fields` de las páginas de Orion y de `FormPage`, `FilterField` de `no_index`, `SEARCH_CONFIG` desde el idioma base (`ORION_SEARCH_CONFIG`) y detección de `pg_trgm`; verificar con `pytest tests/test_site_search.py` (texto de un bloque encontrado, resumen de artículo, configuración por idioma, sin extensión no falla)

## 2. Resultados

- [x] 2.1 App `orion.search`: vista, ruta traducida, plantilla con resultados, paginación, filtro por tipo, destacados primero y `noindex`; verificar con `pytest tests/test_site_search.py` (solo publicadas, públicas, del idioma y sin `noindex`; filtro de artículos; paginación de 10; sin término; sin resultados; destacada primero; `/en/search/`; plural en PostgreSQL; aproximada con la extensión, si la base de pruebas la tiene)
- [x] 2.2 Buscador en el encabezado con `ORION_SEARCH_IN_HEADER`; verificar con `pytest tests/test_site_search.py tests/test_site_layout.py` y `pipenv run css-build`

## 3. Destacados e informe

- [x] 3.1 `wagtail.contrib.search_promotions`, permisos para Editores y Administradores, registro de búsquedas, `NoResultsQuery` con tope e informe; verificar con `pytest tests/test_site_search.py` (editora crea un destacado, búsqueda registrada, sin resultados contada, tope, informe visible para administradores y no para editores)

## 4. Navegador y cierre

- [x] 4.1 `manage.py update_index` en la base de desarrollo y verificar en el navegador: buscar desde el encabezado, resultados con tipo y resumen, filtro, paginación, destacado, búsqueda sin resultados y su informe, en escritorio y celular; probar `enable_trigram` y una búsqueda con error de tipeo en PostgreSQL
- [x] 4.2 Traducir los textos nuevos; actualizar README (buscador, `update_index`, `enable_trigram`, `ORION_SEARCH_*`, ruta reservada, MySQL) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_site_search.py` 22 passed en PostgreSQL (incluye plural "médicos" →
  "médico"); en MySQL 21 passed y 1 omitida (la de plurales, propia de PostgreSQL).
  `tests/test_translations.py` (nueva) revisa que todos los plurales en español tengan
  sus tres formas.
- Navegador (Chrome headless, 1280 px y 390 px), 14/14: búsqueda desde el encabezado,
  "13 resultados para…", tipo y resumen, filtro de artículos, página 2, destacado
  primero, mensaje sin resultados, buscador dentro del menú del celular, informe con las
  frecuentes y las sin resultados para el administrador, destacados para la editora y el
  informe no. Hallado y corregido: el contador salía en inglés (faltaba la tercera forma
  del plural), igual que un aviso de la Fase 2.
- `enable_trigram` en una base PostgreSQL descartable (borrada después): "radiografais",
  "radografias" y "pediatira" encuentran sus páginas; "estacionamiento" y "zzzz", nada;
  "rayos" encuentra "Radiografías" (umbral 0,3 de Wagtail, documentado).
- Traducciones: 0 sin traducir ni dudosas en los catálogos de Orion.
- `pipenv run test-postgres` 550 passed; `pipenv run test-mysql` 549 passed, 1 skipped.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `wagtailsearchpromotions` 0001–0008, `orion_editor.0004_search_promotion_permissions` y
  `orion_search.0001_initial`, y `update_index` indexó el contenido, en PostgreSQL y
  MySQL (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-site-search` cuando esté aprobado.
