## Context

Ver proposal.md (Why). `orion/base.html` arma hoy el `<title>` (título SEO o título) y la
descripción de la página, y ya incluye `{% hreflang_links %}` y `{% main_image_preload %}`.
Las páginas de Orion son `BodyPage` (Portada, Página, Contacto), `ArticleIndexPage`
(paginado con `?page=`, rutas de categoría y etiqueta) y `ArticlePage` (con imagen y
texto alternativo propios). Los datos fijos están en `SiteSettings` (genérico, pestañas
Identidad, Contacto y Redes) y los traducibles en `SiteTexts`. `orion.localization` ofrece
`get_public_locales` y `get_live_translation`. Los permisos de los roles se dan con
migraciones de `orion_editor` (`0001_roles`). El sitemap de Wagtail recorre solo el árbol
de la raíz del sitio (el idioma base) y el alta de redirecciones de Wagtail no acepta una
ruta inicial por parámetro.

## Goals / Non-Goals

**Goals:**
- Todo el SEO por página en una sola etiqueta del `<head>`, reutilizable por las plantillas
  base de los proyectos.
- Usar `wagtail.contrib.redirects` y `wagtail.contrib.sitemaps` en lugar de construirlos.

**Non-Goals:**
- Un panel de SEO con puntajes o sugerencias.
- Etiquetas de analítica (Fase 4 o a futuro).

## Decisions

### App `orion.seo`
Nueva app (`orion.seo`, label `orion_seo`) con: `SeoMixin` para páginas, etiquetas
`{% seo_tags page %}` y `{% structured_data page %}`, vistas de sitemap, robots.txt y
favicon, el modelo y el middleware del monitor de 404 y su pantalla en el admin. Separada de
`orion.pages` porque los proyectos la usan con sus propios tipos de página.

### Campos
- `SeoMixin` (abstracto): `no_index` y `no_follow` (booleanos, falso por defecto) y
  `social_image` (FK opcional a imagen). Agrega sus paneles a la pestaña Promocionar.
  `get_social_image()` devuelve la imagen social; `ArticlePage` lo sobreescribe para caer a
  su imagen y `BodyPage` para caer a la imagen del Hero inicial (misma lógica que la
  precarga). Se aplica a `BodyPage`, `ArticleIndexPage` y `ArticlePage`.
- `SiteSettings`: pestaña SEO con `favicon` (FK imagen), `social_image` (FK imagen),
  `robots_txt` (texto) y `google_site_verification` (validado con `^[A-Za-z0-9_-]{1,100}$`).
- `SiteTexts`: `description` (hasta 300 caracteres), traducible.
Migraciones con valores por defecto; no tocan datos.

### Etiqueta `{% seo_tags page %}`
Reemplaza en `orion/base.html` el `<title>` y la descripción actuales; emite título,
descripción, canónica, robots, Open Graph, Twitter Card, verificación y favicon.
- Descripción: `get_meta_description()` del mixin (la descripción SEO; en `ArticlePage`,
  su resumen si falta) o la del sitio.
- Título: `seo_title` tal cual; si no, `título | nombre del sitio` (`Site.site_name`, o
  `WAGTAIL_SITE_NAME`), sin repetir si coinciden. `orion/base.html` mantiene el bloque
  `title` para que una plantilla lo reemplace.
- Canónica: `page.get_full_url(request)`; en un listado (cualquier página con contexto
  `articles` paginado) agrega `?page=N` si N > 1; en rutas de `RoutablePageMixin` usa la
  ruta pedida (`request.path`) sobre el dominio del sitio. Nunca se guarda.
- Imagen social: rendición `fill-1200x630|format-jpeg` (los SVG se omiten).
- `og:locale` con el idioma de la página (`es_ES` → formato `ll_CC` desde el código).
Funciona sin `page` (vistas que no son de Wagtail): solo lo del sitio.

### JSON-LD
`{% structured_data page %}` arma una lista `@graph` en Python (`WebSite`,
`Organization`, `BreadcrumbList` con los ancestros publicados desde la raíz del sitio en
el idioma, `Article` en `ArticlePage`) y la serializa con `json.dumps`, reemplazando `<`,
`>` y `&` por sus escapes Unicode (`\u003c`, `\u003e`, `\u0026`), igual que
`json_script`, dentro de `<script type="application/ld+json">`. Solo campos con valor.

### Sitemap
`orion.seo.sitemap.Sitemap` hereda del de Wagtail: `items()` recorre la raíz del sitio y
sus traducciones en los idiomas públicos (`get_public_locales`), páginas live y públicas,
excluyendo `no_index` (en los modelos con el mixin). Ruta `/sitemap.xml` con la vista de
`wagtail.contrib.sitemaps`, fuera de `i18n_patterns`.

### robots.txt y favicon
Vistas en `orion.seo.views`, rutas `/robots.txt` y `/favicon.ico` en `orion.urls` (antes
de las páginas). robots.txt: texto de `SiteSettings` o el de defecto
(`User-agent: *`, `Disallow: /<ORION_ADMIN_PATH>`), más `Sitemap: <url absoluta>` si no
hay una línea `Sitemap:`; `text/plain`. Favicon: redirección 302 a la rendición
`fill-32x32|format-png` (o al SVG), 404 sin favicon.

### Redirecciones
`wagtail.contrib.redirects` en las apps y `RedirectMiddleware` al final de `MIDDLEWARE`.
`WAGTAILREDIRECTS_AUTO_CREATE` queda en su valor por defecto (verdadero). La migración
`orion_editor.0003_redirect_permissions` da a Administradores `add`, `change` y
`delete_redirect` (y la vuelta las quita), con dependencia de las migraciones de
`wagtailredirects`. El README y `roles` documentan el permiso.

### Monitor de 404
Modelo `NotFoundPath`: `site` (FK, CASCADE), `path` (único por sitio, hasta 255),
`hits`, `first_seen`, `last_seen`. `NotFoundMiddleware` va justo antes de
`RedirectMiddleware` en la lista (así ve la respuesta después de las redirecciones): si la
respuesta es 404, el método GET y la ruta no empieza con la del admin, `STATIC_URL`,
`MEDIA_URL` ni `/_preview/`, actualiza `hits` con `F()` o crea la fila si hay menos de
`ORION_404_MAX_PATHS` (1000) filas. Errores de base se registran y no rompen la respuesta.
Pantalla en el admin (`register_admin_urls`, ítem "URLs no encontradas" dentro de
Informes, solo `is_site_administrator`): tabla paginada por visitas; "Redirigir" abre un
formulario con el `RedirectForm` de Wagtail con `old_path` fijo y al guardar borra la
fila; "Descartar" (POST) la borra. Las rutas que ya tienen redirección se borran al
crearla también desde Redirecciones (señal `post_save` de `Redirect`).

### Hallazgos al implementar
- El sitemap de Wagtail itera un queryset (`.iterator()`), así que las páginas sin
  indexar se excluyen por id con una consulta por modelo que tiene el campo.
- `django.contrib.sitemaps` va en las apps por su plantilla `sitemap.xml`.
- Wagtail guarda `old_path` sin la barra final; la señal que limpia el monitor compara
  ambas formas. La redirección automática al cambiar un slug se crea al confirmar la
  transacción (`on_commit`).
- El JSON-LD es un bloque de datos: el navegador no lo ejecuta, así que convive con la
  regla de scripts externos y con una CSP estricta (la prueba de scripts lo excluye).
- La prueba del CSS compilado excluye toda plantilla que extiende una del admin.

## Risks / Trade-offs

- [Un bot genera miles de 404 distintos] → tope de rutas, una consulta por 404 y solo GET.
- [Título con el nombre del sitio al final cambia los títulos actuales] → es lo pedido por
  la especificación; el título SEO lo reemplaza página por página.
- [Canónica de rutas de categoría y etiqueta] → se arma con la ruta pedida; si un proyecto
  agrega rutas con parámetros, las sobreescribe con el bloque de la plantilla.
- [Sitemap grande en sitios con muchas páginas] → el `Sitemap` de Django pagina a 50.000.

## Migration Plan

Migraciones nuevas en `orion_seo`, `orion_pages`, `orion_site_data` y `orion_editor`, más
las de `wagtailredirects`. Ninguna borra datos. Revertir: migrar hacia atrás y quitar las
apps y middlewares.
