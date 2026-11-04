## Why

Hoy una página de Orion solo tiene `<title>` y, si el editor la carga, la descripción. No
hay imagen para redes, URL canónica, sitemap, robots.txt, favicon, datos estructurados ni
redirecciones: un sitio nuevo se indexa mal y una URL vieja da 404. La especificación pide
cubrir lo esencial y sumar JSON-LD, `noindex` por página y un monitor de 404. Es el
cambio 2 de la Fase 3.

## What Changes

- **Título y descripción con respaldos**: el título SEO de la página tal cual o, si no hay,
  "Título | Nombre del sitio"; la descripción de la página o la descripción del sitio en ese
  idioma (nueva, en Textos del sitio).
- **Open Graph y Twitter Card**: título, descripción, URL, tipo, idioma e imagen (imagen
  social de la página → imagen del artículo → imagen del Hero inicial → imagen por defecto
  del sitio), recortada a 1200 × 630.
- **URL canónica** armada en cada visita (sin parámetros, salvo la página de un listado).
- **`noindex` / `nofollow` por página** (pestaña Promocionar); esas páginas no van al
  sitemap.
- **Sitemap** en `/sitemap.xml` con las páginas publicadas de todos los idiomas públicos.
- **robots.txt** en `/robots.txt`, editable en Datos del sitio, con un texto por defecto
  que bloquea el admin y anuncia el sitemap.
- **Favicon** desde Datos del sitio, en los tamaños que piden navegadores y celulares, y
  `/favicon.ico`.
- **Datos estructurados (JSON-LD)**: sitio web y organización en todas las páginas
  (nombre, logo, contacto, redes), artículo en los artículos y migas de pan.
- **Verificación de Search Console**: campo en Datos del sitio que genera la etiqueta meta.
- **Redirecciones** de Wagtail (301/302 desde el admin, importación CSV y creación
  automática al cambiar el slug de una página publicada), para Administradores.
- **Monitor de 404**: cuenta las URLs que dan error, las lista por cantidad para los
  administradores y permite redirigirlas o descartarlas.

**Fuera del alcance:** Google Analytics, Tag Manager, Meta Pixel y métricas en el admin (a
futuro, o con "Scripts desde el admin" de la Fase 4); `hreflang` dentro del sitemap (ya
está en cada página); datos estructurados de negocio local con horarios o reseñas; manifest
de aplicación web; indexación de documentos; bloqueo de indexación por entorno (staging).

## Capabilities

### New Capabilities
- `seo`: metadatos de cada página (título, descripción, redes, canónica, robots, JSON-LD),
  sitemap, robots.txt, favicon y verificación de Search Console, y dónde se editan.
- `redirects`: redirecciones administrables y monitor de URLs que dan 404.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** app `orion.seo` (mixin de páginas, etiquetas del `<head>`, vistas de
  sitemap, robots y favicon, modelo y middleware del monitor de 404, pantalla del monitor).
- **Código modificado:** `SiteSettings` (favicon, imagen social, robots.txt, verificación)
  y `SiteTexts` (descripción); páginas de Orion con el mixin; `orion/base.html`; rutas de
  `orion.urls`; ajustes base (apps `orion.seo`, `wagtail.contrib.redirects`,
  `wagtail.contrib.sitemaps`, middleware); permisos de Administradores; README y CHANGELOG.
- **Dependencias nuevas:** ninguna (todo es Django, Wagtail y sus `contrib`).
- **Migraciones:** columnas nuevas en las páginas de Orion, en `SiteSettings` y en
  `SiteTexts` (con valores por defecto, sin tocar datos); tabla del monitor de 404; permisos
  de redirecciones para Administradores. Las tablas de `wagtailredirects`.
