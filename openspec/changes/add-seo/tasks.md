# Tasks

## 1. Base y metadatos

- [ ] 1.1 App `orion.seo`, `SeoMixin` en las páginas de Orion, campos SEO en `SiteSettings` y descripción en `SiteTexts`, con sus migraciones; verificar con `pytest tests/test_seo.py` (campos en Promocionar y en la pestaña SEO, código de verificación inválido rechazado) y `makemigrations --check`
- [ ] 1.2 `{% seo_tags %}` en `orion/base.html` (título, descripción, canónica, robots, Open Graph, Twitter, verificación, favicon); verificar con `pytest tests/test_seo.py` (respaldos de título y descripción, canónica sin parámetros y con `?page=2`, `noindex`, imagen social en cascada, verificación, favicon) y la suite completa
- [ ] 1.3 `{% structured_data %}`; verificar con `pytest tests/test_seo.py` (WebSite, Organization solo con datos cargados, BreadcrumbList, Article, `</script>` escapado)

## 2. Archivos para buscadores

- [ ] 2.1 Sitemap multi-idioma, `/robots.txt` y `/favicon.ico`; verificar con `pytest tests/test_seo.py` (idiomas públicos sí y no públicos no, sin `noindex` ni privadas; robots por defecto y propio con `Sitemap:`; favicon con y sin imagen)

## 3. Redirecciones y 404

- [ ] 3.1 `wagtail.contrib.redirects`, middleware y migración de permisos para Administradores; verificar con `pytest tests/test_redirects.py` (301 desde el admin, cambio de slug crea redirección, Editor sin acceso, importación CSV disponible)
- [ ] 3.2 Monitor de 404 (modelo, middleware, pantalla con redirigir y descartar); verificar con `pytest tests/test_redirects.py` (conteo, rutas excluidas, tope, redirigir borra la fila y redirige, descartar, solo administradores)

## 4. Navegador y cierre

- [ ] 4.1 Verificar en el navegador: `<head>` de portada, página y artículo (validar el JSON-LD con un parser), sitemap, robots, favicon, pestaña SEO de Datos del sitio, Promocionar, Redirecciones y monitor de 404 (redirigir una ruta), en escritorio y celular
- [ ] 4.2 Traducir los textos nuevos; actualizar README (SEO, pestaña SEO, `SeoMixin` para proyectos, redirecciones, monitor) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-seo` cuando esté aprobado.
