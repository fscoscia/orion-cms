# Changelog

Todos los cambios relevantes de Orion se registran en este archivo. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen
[Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Paquete `orion` instalable desde GitHub, con extras `postgres` y `mysql`.
- Ajustes base configurables por variables de entorno, con validación al arrancar (clave
  secreta obligatoria fuera de debug, booleanos inválidos, ruta del admin) y valores
  seguros por defecto fuera de debug.
- Chequeo de sistema `orion.E001` para SSL y TLS de email activados a la vez.
- Endpoint de salud en `/health/`.
- Rutas base: admin en ruta configurable (`ORION_ADMIN_PATH`), documentos y páginas.
- Plantilla base `orion/base.html` y plantilla para páginas genéricas.
- Proyecto de ejemplo, pruebas en PostgreSQL y MySQL, Ruff, pre-commit y
  `docker-compose.yml` opcional.
- Multi-idioma: catálogo de idiomas en `LANGUAGES`, idiomas agregados desde el admin
  (wagtail-localize) y publicados desde **Configuración → Idiomas**; el idioma base siempre
  es público.
- URLs por idioma con el idioma base sin prefijo; redirecciones `302` para idiomas no
  públicos y páginas sin traducción publicada.
- Etiquetas de template `{% language_switcher %}` y `{% hreflang_links %}`, incluidas en
  `orion/base.html`.
- Traducción de páginas campo por campo y aviso de textos pendientes con wagtail-localize.
- Chequeos `orion.E002` (idioma base fuera del catálogo) y `orion.E003` (rutas por idioma
  ausentes en el archivo de rutas principal).
- Traducción al español de los textos de la app `orion.localization`.
- Datos fijos del sitio (logos, contacto y redes sociales) en **Propiedades → Datos del
  sitio** (`orion.site_data.SiteSettings`), iguales en todos los idiomas.
- Textos del sitio traducibles (eslogan y texto legal del pie), una versión por idioma
  (`SiteTexts`), con respaldo al idioma base y la etiqueta `{% get_site_texts %}`.
- Menús del encabezado y del pie, de dos niveles y traducibles (`orion.navigation.Menu`),
  con la etiqueta `{% site_menu %}`: oculta ítems a páginas no publicadas, marca el ítem
  actual con `aria-current` y usa el menú del idioma base si falta la traducción.
- `LinkBlock` en `orion.core.blocks`: enlace a página (en el idioma de la visita), URL
  externa, email o teléfono, con un solo destino y rechazo de URLs del propio sitio.
- Encabezado y pie en `orion/base.html` (`orion/includes/header.html` y `footer.html`,
  reemplazables), enlace para saltar al contenido y menú accesible en celular.
- CSS de Orion compilado con Tailwind 4 y versionado, con colores y fuentes como variables
  CSS; comandos `css-build` y `css-watch` (django-tailwind-cli, solo para desarrollo).
- Alpine.js 3.17.4 en su variante compatible con CSP y `orion/js/orion.js`.
- Permisos de textos del sitio y menús para los grupos *Editors* y *Moderators*.
- Traducción al español de los textos de `orion.core`, `orion.site_data` y
  `orion.navigation`.
- Biblioteca de bloques en `orion.core.blocks`: Hero, Texto, Imagen, Galería, Imagen y
  texto, Tarjetas, Cifras, Pestañas, Acordeón, Llamada a la acción, Logos, Datos de
  contacto y Botones, con descripción y vista previa en el editor, y `ContentStreamBlock`
  que los reúne como cuerpo de página.
- Interruptor "Visible" en cada bloque para ocultarlo sin borrarlo, y campo "Estilo" con
  opciones que declara cada proyecto en `ORION_BLOCK_STYLES` (sin migraciones).
- Títulos de bloque con palabras resaltadas en el color de acento (negrita).
- Texto enriquecido con el plugin de tipografía de Tailwind, ligado a las variables de
  color y fuente del tema.
- Imágenes de bloques en WebP con `srcset`, medidas y carga diferida, con texto alternativo
  obligatorio o marca de decorativa.
- Componentes `tabs` y `counter` de Alpine (compatibles con CSP) para las pestañas y las
  cifras animadas; el acordeón usa `<details>` nativo.
- App `demo` del proyecto de ejemplo con una página que usa todos los bloques.
- Tipos de página en `orion.pages`: Portada, Página libre, Página de contacto, Listado de
  artículos y Artículo, con reglas de dónde va cada uno.
- La primera migración reemplaza la página de bienvenida de Wagtail por una Portada, solo
  si sigue intacta.
- Artículos con fecha, resumen, imagen (texto alternativo o decorativa), categorías y
  etiquetas; listados paginados (`ORION_ARTICLES_PER_PAGE`) con filtros por categoría y
  etiqueta, y feed RSS por listado e idioma (`ORION_FEED_ITEMS`).
- Categorías (dos niveles) y etiquetas traducibles, con permisos para los grupos de
  editores y moderadores.
- Bloque "Últimas novedades" y validación de que el Hero sea el primer bloque.
- Mapas con Leaflet 1.9.4 y teselas de OpenStreetMap: ubicación del sitio en Datos del
  sitio (elegida con un clic, arrastrando o con coordenadas), mapa en la Página de
  contacto y bloque Mapa con varios puntos. Se cargan a pedido del visitante; proveedor
  de teselas configurable con `ORION_MAP_TILES`.
- Vista previa en el selector para todos los bloques: los que muestran imágenes o
  artículos usan imágenes y artículos de ejemplo de Orion
  (`orion/core/static/orion/samples/`, generadas con `scripts/make_sample_images.py`), sin
  agregar nada a la biblioteca ni a las páginas.

### Changed

- Los slugs de páginas, categorías y etiquetas van sin tildes
  (`WAGTAIL_ALLOW_UNICODE_SLUGS = False`).
- `orion.core.blocks` pasó de módulo a paquete; las importaciones públicas
  (`from orion.core.blocks import LinkBlock`) no cambian.
- El README indica declarar `TEMPLATES[0]["DIRS"]` en el proyecto para reemplazar
  templates de Orion por nombre.
- El email usa TLS por defecto salvo que `EMAIL_USE_SSL` esté activado. **Atención:** un
  proyecto con `EMAIL_HOST` cuyo servidor SMTP no soporta STARTTLS debe definir
  `EMAIL_USE_TLS=false`.
- **BREAKING:** las rutas de Orion se suman (`urlpatterns += orion_urlpatterns`) en lugar
  de incluirse con `include("orion.urls")`.
- El idioma de cada página lo decide su URL (el idioma base sin prefijo); el idioma del
  navegador del visitante se ignora.

### Fixed

- Pruebas de la ruta del admin que dependían del orden de ejecución, y pruebas de ajustes
  que dependían de las variables del `.env` de quien las corre.
- `.env.example` incluye `DATABASE_CONN_MAX_AGE`; una prueba verifica que lista toda
  variable que leen los ajustes base.
- Documentado que `pipenv run` carga `.env` pisando las variables del shell, y cómo
  apuntar las pruebas a las bases de Docker.
