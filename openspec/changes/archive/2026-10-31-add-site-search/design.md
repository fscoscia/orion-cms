## Context

Ver proposal.md (Why). Wagtail 7.4 usa `modelsearch` para la búsqueda en base de datos
(`wagtail.search.backends.database`, ya en los ajustes base sin opciones): en PostgreSQL,
`SEARCH_CONFIG` elige la configuración de texto (sin ella usa la de la base), y la
búsqueda aproximada (`Fuzzy`) necesita `pg_trgm` (comando `enable_trigram`); en MySQL usa
`FULLTEXT`; en SQLite, FTS. El índice se actualiza solo al publicar. `Page.search_fields`
solo indexa el título. Orion tiene `SeoMixin.no_index`, `get_meta_description()`,
`orion.localization` con idiomas públicos, rutas por idioma en `i18n_patterns` y la caché
de página (la página de resultados no lleva CSRF: se guardaría por consulta).

## Goals / Non-Goals

**Goals:**
- Buscar sin servicios externos, en español, con lo que traen Wagtail y la base.
- Que el buscador funcione igual en un hosting sin extensiones de PostgreSQL.

**Non-Goals:**
- Elasticsearch, autocompletado, sinónimos, documentos.

## Decisions

### Índice
`search_fields` en `BodyPage` (`body` como `SearchField`), `ArticlePage` (`summary`,
`body`), `ArticleIndexPage` (`intro`) y `FormPage` (`intro`), más los de `Page` (título,
descripción). `SeoMixin` agrega `FilterField("no_index")` para filtrar. README: correr
`manage.py update_index` tras actualizar.

### Idioma
`WAGTAILSEARCH_BACKENDS["default"]["SEARCH_CONFIG"]` desde `ORION_SEARCH_CONFIG`; por
defecto, el nombre de PostgreSQL del idioma base (`es` → `spanish`, `en` → `english`,
`pt` → `portuguese`, `fr` → `french`, `it` → `italian`, `de` → `german`; otro → `simple`).
Las otras bases ignoran la opción.

### Búsqueda aproximada
`orion.search.backend.has_trigram()`: en PostgreSQL consulta `pg_extension` una vez por
proceso. La vista busca con `PlainText`; si no hay resultados y `has_trigram()`, repite
con `Fuzzy`. README: `manage.py enable_trigram` (requiere permiso de crear extensiones).

### Vista y ruta
App `orion.search`. Vista `search` en `orion.urls` dentro de `i18n_patterns`, antes de
las páginas, con la ruta traducible `path(_("search/"), ...)` (`buscar/` en español,
`search/` en inglés). Consulta `q` (hasta 100 caracteres), `type` (`page` o `article`),
`page`. Queryset: `Page.objects.live().public()` del `Locale` activo, sin `no_index`
(excluidos por id como en el sitemap), filtrado por tipo (`ArticlePage` o el resto),
`.search(q, operator="and")` con `order_by_relevance`. Paginación de 10. Destacados de
`wagtail.contrib.search_promotions` (`get_promotions(q)`) primero, sin repetir, solo los
publicados del idioma. Contexto: resultados con título, URL, resumen
(`get_meta_description()` o `search_description`) y tipo (`verbose_name`). Plantilla con
`<meta name="robots" content="noindex">` (bloque `seo`). La caché de página la guarda por
consulta; se vacía al publicar como el resto.

### Registro
`Query.get(q).add_hit()` de search_promotions en cada búsqueda con término (página 1)
alimenta el informe "Términos de búsqueda" de Wagtail. Búsquedas sin resultados: modelo
`NoResultsQuery` (`query_string` normalizado en minúsculas, único, hasta 255; `hits`;
`last_seen`) actualizado con `F()`, con un tope (`ORION_SEARCH_MAX_NO_RESULTS`, 1000)
como el monitor de 404. Informe propio "Búsquedas" en Informes, solo para
`is_site_administrator` (Informes es de administradores desde la Fase 2; el informe
"Términos de búsqueda" de Wagtail es solo para superusuarios): las más frecuentes de 30
días (`Query.get_most_popular`) y las sin resultados.

### Encabezado
`header.html` incluye `orion/search/includes/header_search.html` si
`ORION_SEARCH_IN_HEADER` (verdadero); en escritorio un campo compacto con etiqueta
oculta visualmente y botón con ícono y texto accesible; en el celular, dentro del panel
del menú. CSS en `orion.css` (Tailwind) y `css-build`.

### Permisos
Migración de `orion_editor`: Editores y Administradores reciben `add`, `change` y
`delete_searchpromotion`, que habilitan el menú de destacados de search_promotions.

### Hallazgos al implementar
- El informe "Términos de búsqueda" de Wagtail es solo para superusuarios y desde la
  Fase 2 Informes es de los administradores del sitio: el informe es propio y para ellos.
- Las etiquetas SEO recibían una cadena vacía en vistas sin `page`; ahora la tratan como
  "sin página".
- En MySQL los índices `FULLTEXT` de InnoDB solo ven filas confirmadas: las pruebas del
  buscador usan transacciones reales (`transaction=True, serialized_rollback=True`).
- La ruta traducible se define en la app (`SEARCH_PATH`) para que `makemessages` la
  extraiga.
- "Search" como botón usa contexto (`verb`, "Buscar"): Wagtail traduce el sustantivo
  ("Búsqueda").
- Los catálogos en español declaran tres formas de plural; faltaba una en dos frases (una
  de la Fase 2): una prueba revisa todos los plurales.
- Con `pg_trgm` (base descartable): "radiografais" y "pediatira" encuentran sus páginas,
  términos sin relación no devuelven nada; "rayos" encuentra "Radiografías" (umbral 0,3,
  ajustable).

## Risks / Trade-offs

- [La caché de página guarda cada consulta distinta] → entradas que vencen en un día; un
  bot que busca mucho llena la caché en disco: se agrega `/buscar/` a las rutas sin caché
  si el tope de archivos resulta un problema (no se hace ahora).
- [MySQL: búsqueda más básica, palabras de menos de 3 letras ignoradas] → documentado.
- [Ruta `buscar/` reservada] → una página con ese slug en la raíz queda tapada; documentado.

## Migration Plan

Migraciones de `wagtailsearchpromotions`, `orion_search.0001` y los permisos. Después,
`update_index`. Revertir: quitar las apps y migrar hacia atrás.
