## Context

Ver proposal.md (Why). Ya existen: multi-idioma con wagtail-localize (URLs por idioma,
redirección de páginas servidas en otro idioma con `before_serve_page`, raíz resuelta con
`site.root_page`), `SiteSettings` con los datos de contacto, `ContentStreamBlock` con los
trece bloques (`orion.core.blocks`), `LinkBlock` que resuelve páginas en el idioma activo y
la plantilla `orion/base.html`. La raíz del sitio es la página de bienvenida que crea la
migración inicial de Wagtail (`wagtailcore.Page`, profundidad 2). wagtail-localize
sincroniza las relaciones hijas no traducibles copiándolas del original e ignora los
`ManyToManyField` salvo que se declaren en `override_translatable_fields`.

## Goals / Non-Goals

**Goals:**
- Tipos de página creables con reglas claras, usando lo nativo de Wagtail
  (`parent_page_types`, `subpage_types`, `RoutablePageMixin`, snippets traducibles).
- Que la clasificación de un artículo sea una sola para todos sus idiomas y se muestre en
  el idioma de la visita.
- Una instalación nueva que arranca con una Portada usable.

**Non-Goals:**
- Varios sitios con portadas distintas en un mismo proyecto.
- URLs propias para categorías y etiquetas (`/novedades/categoria/salud/`): el filtro es un
  parámetro del listado; las URLs propias pueden llegar con el SEO de la Fase 3.

## Decisions

### App `orion.pages`
Una app nueva (`orion.pages`, etiqueta `orion_pages`) con los modelos de página, los
fragmentos de categorías y etiquetas, el feed y sus templates en
`orion/pages/<tipo>.html` (atributo `template` explícito, reemplazable desde el proyecto
como los demás templates de Orion). Se suma a `ORION_APPS` en los ajustes base, junto con
`wagtail.contrib.routable_page`. Alternativa: ponerlos en `orion.core`; mezclaría modelos de
contenido con la infraestructura compartida.

### Tipos y reglas de ubicación
| Tipo | Clase | Va debajo de | Admite |
| --- | --- | --- | --- |
| Portada | `HomePage` | raíz (`wagtailcore.Page`) | Página libre, Contacto, Listado |
| Página libre | `ContentPage` | Portada, Página libre | Página libre, Contacto, Listado |
| Página de contacto | `ContactPage` | Portada, Página libre | nada |
| Listado de artículos | `ArticleIndexPage` | Portada, Página libre | Artículo |
| Artículo | `ArticlePage` | Listado de artículos | nada |

`HomePage.can_create_at` devuelve falso si ya existe una Portada: las traducciones las crea
wagtail-localize con `copy_for_translation`, que no pasa por esa regla, así que cada idioma
tiene la suya y el admin no deja crear una segunda a mano.

Portada, Página libre y Página de contacto tienen `body = StreamField(ContentStreamBlock())`.
El Artículo usa `ArticleStreamBlock`, que hereda de `ContentStreamBlock` sin Hero (el
artículo tiene su propio encabezado) ni Últimas novedades.

### Encabezado principal y Hero primero
`ContentStreamBlock.clean` rechaza un Hero que no sea el primer bloque (error en el bloque,
con el mensaje "El Hero tiene que ser el primer bloque"), lo que también impide dos Heroes.
Los modelos de página exponen `starts_with_hero` (el primer bloque visible es un Hero), y
el include `orion/pages/includes/page_header.html` muestra el título como `h1` solo cuando
es falso. Alternativa: un campo "ocultar título"; dejaría al editor la responsabilidad de no
duplicar ni omitir el `h1`.

### Página de contacto
`ContactPage` muestra los datos de `SiteSettings` con un include compartido con el bloque
Datos de contacto (`orion/includes/contact_details.html`, extraído del template del bloque)
y después su cuerpo. El formulario de la Fase 4 y el mapa del cambio 5 serán campos o
secciones nuevas del mismo modelo, sin migrar contenido.

### Portada inicial
Migración de datos `orion_pages.0002_replace_welcome_page`, igual que la plantilla de
proyecto de Wagtail: si la raíz del sitio por defecto es un `wagtailcore.Page` sin hijas,
con el título original de Wagtail y sin otras páginas con su `translation_key` (sin
traducciones), apunta el `Site` a la raíz del árbol (borrar su página raíz borraría el
`Site` en cascada), la borra, crea una `HomePage` en su lugar (misma ruta del árbol, mismo
idioma, publicada, título "Inicio" traducido al idioma base), la asigna al mismo `Site` y
recalcula las hijas de la raíz. En
cualquier otro caso no hace nada. La migración inversa no hace nada: la página de
bienvenida no tiene contenido que recuperar.

### Categorías y etiquetas
`ArticleCategory` y `ArticleTag` son snippets con `TranslatableMixin`, `name` y `slug`, con
una restricción única de `slug` por `locale`. `ArticleCategory` tiene `parent` (FK opcional
a sí misma, solo categorías sin superior); su `clean` rechaza un tercer nivel. Al traducir,
wagtail-localize traduce el nombre y el slug, y apunta el `parent` a la traducción.

En `ArticlePage`:
- `categories`: `ParentalManyToManyField` con casillas, limitado a las categorías del
  idioma de la página por el formulario de edición (`base_form_class`).
- `tags`: relación hija `ArticlePageTag` (`Orderable` con `ParentalKey` y FK a la etiqueta)
  editada con `MultipleChooserPanel`, que abre el elegidor de fragmentos con búsqueda.

Las traducciones guardan las mismas filas que el original: las etiquetas porque
wagtail-localize sincroniza las relaciones hijas no traducibles, y las categorías porque se
declaran en `override_translatable_fields` como `SynchronizedField`. Los templates muestran
`categoría.localized` y `etiqueta.localized`. Los filtros resuelven el slug en el idioma de
la visita (o en el base si no está traducido) y filtran por `translation_key`, incluyendo
las subcategorías, así un filtro en inglés encuentra artículos clasificados con la versión
española. Alternativa: etiquetas libres de django-taggit; wagtail-localize las copiaría del
original sin que el traductor pueda cambiarlas (descartado al planificar).

### Listado, paginación y filtros
`ArticleIndexPage.get_context` arma la consulta: hijos `ArticlePage` publicados del mismo
idioma, ordenados por `-date` y `-first_published_at`, filtrados por `?category=` o
`?tag=` (404 si el slug no existe) y paginados con `Paginator.get_page`, que lleva números
fuera de rango a la última página. El tamaño de página sale de `ORION_ARTICLES_PER_PAGE`
(12 por defecto). La paginación conserva el filtro en sus enlaces.

### RSS
`ArticleIndexPage` usa `RoutablePageMixin` con la ruta `rss/`, que devuelve un `Feed` de
`django.contrib.syndication` con los últimos `ORION_FEED_ITEMS` (20) artículos del listado:
título, resumen, enlace absoluto, fecha y categorías. Como el listado ya es el del idioma de
la URL, el feed también. El template del listado anuncia el feed con
`<link rel="alternate" type="application/rss+xml">` en `extra_head`.

### Últimas novedades
`LatestArticlesBlock` en `orion.core.blocks` (clave `latest_articles`): título opcional,
cantidad (1 a 12, por defecto 3) y un listado opcional (`PageChooserBlock` de
`orion_pages.ArticleIndexPage`). Su `get_context` importa `ArticlePage` dentro de la
función (como `ContactBlock` con `SiteSettings`), filtra artículos publicados del idioma
activo, debajo de `listado.localized` si se eligió uno, y los ordena como el listado. Sin
artículos no dibuja nada, y `ContentStreamBlock` no agrega el envoltorio de un bloque
que renderiza vacío. Las tarjetas comparten el include de tarjeta de artículo con el
listado.

### Artículo
Campos: `date` (`DateField`, por defecto hoy), `summary` (`TextField`, hasta 300
caracteres, obligatorio), `image` (FK a imagen, opcional) e `image_alt` (texto alternativo
traducible, obligatorio si hay imagen salvo que se marque `image_is_decorative`),
`categories`, `tags` y `body`. Las imágenes usan los mismos `srcset_image` WebP del cambio 3.

### Permisos
Migración de datos `orion_pages.0003` con `grant_to_editor_groups` (de `orion.core`) para
agregar y modificar categorías y etiquetas. Los permisos sobre páginas siguen siendo los de
Wagtail por sección del árbol.

## Risks / Trade-offs

- [La migración de la Portada borra una página] → solo la de bienvenida intacta de Wagtail,
  con condiciones estrictas y una prueba por cada condición; autorizado al planificar.
- [La sincronización del `ParentalManyToManyField` declarada a mano podría no comportarse
  como la de relaciones hijas] → prueba que traduce un artículo, cambia las categorías del
  original, sincroniza y verifica la traducción.
- [`MultipleChooserPanel` dentro de una página traducida] → la traducción no se edita en el
  formulario normal; prueba de que las etiquetas sincronizadas se muestran localizadas.
- [El selector de categorías con casillas crece con muchas categorías] → aceptable para
  sitios institucionales; si molesta, se pasa a un elegidor como el de etiquetas.
- [Consultas por tarjeta en listados (imágenes, categorías)] → `select_related` de la imagen
  y `prefetch_related` de categorías y etiquetas; la caché llega en la Fase 3.
- [Las pruebas existentes usan la raíz como `Page` genérica] → pasan a recibir una
  `HomePage`; se ajustan los fixtures si alguna prueba depende del template genérico.

## Migration Plan

Migraciones de `orion_pages`: `0001` (tablas), `0002` (Portada inicial, condicional, sin
reversa) y `0003` (permisos, reversible). La app `demo` del ejemplo genera una migración por
el bloque nuevo. Ninguna toca páginas existentes salvo la página de bienvenida intacta.
Revertir: revertir `orion_pages` a `0001` y quitar la app; la Portada creada no se
convierte de vuelta en la página de bienvenida.
