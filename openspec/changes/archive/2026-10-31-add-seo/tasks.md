# Tasks

## 1. Base y metadatos

- [x] 1.1 App `orion.seo`, `SeoMixin` en las páginas de Orion, campos SEO en `SiteSettings` y descripción en `SiteTexts`, con sus migraciones; verificar con `pytest tests/test_seo.py` (campos en Promocionar y en la pestaña SEO, código de verificación inválido rechazado) y `makemigrations --check`
- [x] 1.2 `{% seo_tags %}` en `orion/base.html` (título, descripción, canónica, robots, Open Graph, Twitter, verificación, favicon); verificar con `pytest tests/test_seo.py` (respaldos de título y descripción, canónica sin parámetros y con `?page=2`, `noindex`, imagen social en cascada, verificación, favicon) y la suite completa
- [x] 1.3 `{% structured_data %}`; verificar con `pytest tests/test_seo.py` (WebSite, Organization solo con datos cargados, BreadcrumbList, Article, `</script>` escapado)

## 2. Archivos para buscadores

- [x] 2.1 Sitemap multi-idioma, `/robots.txt` y `/favicon.ico`; verificar con `pytest tests/test_seo.py` (idiomas públicos sí y no públicos no, sin `noindex` ni privadas; robots por defecto y propio con `Sitemap:`; favicon con y sin imagen)

## 3. Redirecciones y 404

- [x] 3.1 `wagtail.contrib.redirects`, middleware y migración de permisos para Administradores; verificar con `pytest tests/test_redirects.py` (301 desde el admin, cambio de slug crea redirección, Editor sin acceso, importación CSV disponible)
- [x] 3.2 Monitor de 404 (modelo, middleware, pantalla con redirigir y descartar); verificar con `pytest tests/test_redirects.py` (conteo, rutas excluidas, tope, redirigir borra la fila y redirige, descartar, solo administradores)

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador: `<head>` de portada, página y artículo (validar el JSON-LD con un parser), sitemap, robots, favicon, pestaña SEO de Datos del sitio, Promocionar, Redirecciones y monitor de 404 (redirigir una ruta), en escritorio y celular
- [x] 4.2 Traducir los textos nuevos; actualizar README (SEO, pestaña SEO, `SeoMixin` para proyectos, redirecciones, monitor) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_seo.py` 27 passed; `tests/test_redirects.py` 17 passed.
- Navegador (Chrome headless, 1280 px y 390 px), 18/18 comprobaciones: título con el
  nombre del sitio, descripción del sitio como respaldo y resumen en el artículo,
  `og:image` desde el Hero, JSON-LD válido (`JSON.parse`) con `WebSite`, `Organization`,
  `BreadcrumbList` y `Article`, `noindex` en "Gracias"; pestaña SEO de Datos del sitio y
  campos en Promocionar; Redirecciones y "URLs no encontradas" para la Administradora y no
  para la Editora; el monitor listó `/promo-2024/` con 3 visitas, se redirigió desde el
  monitor a "Servicios", salió del listado y la ruta responde con redirección; listado sin
  desborde en el celular. Hallado y corregido: un artículo sin descripción SEO usaba la
  del sitio en lugar de su resumen.
- `curl`: `/robots.txt` con `Disallow: /admin/` y `Sitemap:`, `/sitemap.xml` sin la página
  `noindex` y con la portada en inglés, `/favicon.ico` → 302 al PNG de 32 px.
- Traducciones de `seo`, `site_data`, `pages`, `core` y `editor`: 0 sin traducir, 0
  dudosas.
- `pipenv run test-postgres` 424 passed; `pipenv run test-mysql` 424 passed.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `wagtailredirects` 0001–0008, `orion_editor.0003_redirect_permissions`,
  `orion_pages.0005_seo_fields`, `orion_seo.0001_initial` y
  `orion_site_data.0004_seo_fields` en PostgreSQL y MySQL; `orion_editor.0003` probada
  hacia atrás (0 permisos) y adelante (`add`, `change`, `delete_redirect`) en PostgreSQL
  (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-seo` cuando esté aprobado.
