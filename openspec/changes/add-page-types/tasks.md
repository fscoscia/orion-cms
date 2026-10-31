# Tasks

## 1. Base

- [x] 1.1 Crear la app `orion.pages` y sumarla a `ORION_APPS` junto con `wagtail.contrib.routable_page`; verificar con `pipenv run manage check`
- [x] 1.2 Validar en `ContentStreamBlock` que el Hero solo vaya primero; verificar con `pytest tests/test_content_blocks.py` (Hero en el medio y dos Heroes rechazados, Hero primero aceptado)

## 2. Páginas

- [x] 2.1 `HomePage`, `ContentPage` y `ContactPage` con sus reglas de ubicación, `starts_with_hero`, el include del encabezado y el include compartido de datos de contacto (extraído del bloque); verificar con `pytest tests/test_page_types.py` (tipos ofrecidos debajo de la Portada, segunda Portada no creable, `h1` con y sin Hero, contacto con los datos del sitio)
- [x] 2.2 Migración `0002_replace_welcome_page`; verificar con `pytest tests/test_page_types.py` (base nueva con Portada como raíz; raíz con hijas, con traducción o con otro título sin cambios) y `migrate` en una base vacía

## 3. Artículos y taxonomías

- [x] 3.1 `ArticleCategory` (dos niveles) y `ArticleTag` traducibles con slug único por idioma, y migración de permisos; verificar con `pytest tests/test_taxonomies.py` (tercer nivel rechazado, slug repetido rechazado, editor puede crear etiquetas)
- [x] 3.2 `ArticlePage` (fecha por defecto hoy, resumen, imagen con texto alternativo o decorativa, categorías limitadas al idioma, etiquetas con `MultipleChooserPanel`, cuerpo sin Hero) y su template; verificar con `pytest tests/test_articles.py` (fecha por defecto, imagen sin alt rechazada, categorías y etiquetas localizadas en `/en/`, sincronización de la clasificación al actualizar la traducción)
- [x] 3.3 `ArticleIndexPage` con orden, paginación, filtros por categoría (con subcategorías) y etiqueta, y 404 para filtros desconocidos; verificar con `pytest tests/test_articles.py` (orden, `?page=2`, `?page=99`, despublicado oculto, filtro por categoría superior, filtro en inglés, filtro inexistente)
- [x] 3.4 Feed RSS por listado con `RoutablePageMixin` y el enlace `alternate` en el listado; verificar con `pytest tests/test_articles.py` (feed en `/en/.../rss/` con artículos en inglés y enlaces absolutos)
- [x] 3.5 Bloque `LatestArticlesBlock` en `ContentStreamBlock` (y migración de `demo`); verificar con `pytest tests/test_articles.py` (cantidad, listado elegido en otro idioma, sin artículos no se muestra) y `makemigrations --check`

## 4. Diseño, navegador y cierre

- [x] 4.1 Estilos de los templates nuevos y `@source` de `orion.pages` en `orion.css`; compilar; verificar con `pipenv run css-build` y `pytest tests/test_site_layout.py`
- [x] 4.2 Verificar en el navegador: crear desde el admin una Página libre, un Listado y un Artículo con categorías y etiquetas; traducir el artículo y sus taxonomías y ver `/en/`; listado con filtros y paginación; RSS; Portada con Últimas novedades; celular y escritorio; sin violaciones de una CSP estricta
- [x] 4.3 Traducir al español los textos nuevos y actualizar README (tipos de página y dónde va cada uno, Portada inicial, artículos, categorías y etiquetas, RSS, `ORION_ARTICLES_PER_PAGE`) y CHANGELOG; verificar con `msgfmt --check` y los ejemplos del README
- [x] 4.4 Ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases (y en una base vacía para la Portada inicial); registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-page-types` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 224 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 224 pruebas pasaron.
- `ruff check`, `ruff format --check`, `pre-commit run --all-files`, `manage.py check` y
  `makemigrations --check`: sin errores.
- `migrate` en PostgreSQL y MySQL de desarrollo: ambas tenían la página de bienvenida de
  Wagtail intacta como raíz y quedaron con una Portada "Inicio"; las bases de prueba (que se
  crean con migraciones) y una SQLite vacía también arrancan con la Portada, conservando
  el mismo `Site`.
- `msgfmt --check` sin errores; los modelos, bloques y textos de los templates salen en
  español.
- Chrome sin interfaz sobre una SQLite nueva con datos de prueba, servida con una CSP
  estricta: Portada con Hero como único `h1` y Últimas novedades (los tres más recientes y
  "Ver todas"); listado con 12 tarjetas, un `h1`, enlace `alternate` al feed y paginación
  por enlace; filtro por categoría superior con subcategorías y por etiqueta; artículo con
  un `h1`, enlaces de categoría y etiqueta e imagen sin carga diferida; contacto con el
  teléfono de Datos del sitio; en `/en/`, Últimas novedades del listado inglés, filtro por
  la categoría traducida, artículo con "Health" y feed RSS con sus 3 artículos; sin
  desbordes a 390 px; sin violaciones de CSP ni errores de consola en el sitio. En el admin
  (servidor sin la CSP de prueba: la del admin es de la Fase 5) se crearon y publicaron una
  Página libre y un Artículo con fecha por defecto de hoy, una categoría elegida entre las
  del idioma y una etiqueta elegida con el elegidor múltiple.
- Hallazgos que cambiaron la implementación:
  - Borrar la página de bienvenida borraba el `Site` en cascada; la migración apunta el
    sitio a la raíz del árbol mientras reemplaza la página.
  - El bloque Últimas novedades sin artículos dejaba su envoltorio vacío; el cuerpo omite
    los bloques que renderizan vacío.
  - Las tarjetas sin imagen no ocupaban el ancho de la grilla y las etiquetas del artículo
    quedaban pegadas a la imagen (corregido en los templates).
  - wagtail-localize publica las traducciones al confirmar la transacción; las pruebas
    ejecutan esos callbacks para verlas publicadas (no afecta al sitio).
