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
- Admin (`orion.editor`): panel de inicio con saludo, acciones según permisos y cambios
  sin publicar; atajos "Nuevo artículo" y "Ver el sitio"; Informes y Ayuda solo para
  administradores; accesos al encabezado y al pie desde la barra del sitio; logo y nombre
  del cliente en el admin y colores con `ORION_ADMIN_COLORS` (chequeos `orion.E004` y
  `orion.W001`).
- `WAGTAIL_ENABLE_UPDATE_CHECK = False`: el admin no consulta nuevas versiones de Wagtail.
- Vista previa del editor: abierta por defecto a media pantalla en pantallas anchas, en
  tamaño escritorio para las páginas de Orion, botón con su nombre, enlaces que no navegan
  dentro de ella y modo "Vista previa / Editar" en celular.
- Roles: los grupos de Wagtail pasan a "Editores" y "Administradores" (migración
  `orion_editor.0001_roles`, conserva usuarios y permisos); Administradores publica, borra
  y administra datos del sitio, idiomas y usuarios, sin acceso a sitios, colecciones,
  flujos ni grupos; el flujo de aprobación pasa a "Aprobación de administradores".
- Admin completo en español: catálogo con las frases que Wagtail y wagtail-localize no
  traducen (`LOCALE_PATHS`), etiquetas del login y columna de uso de las regiones; prueba
  y script para detectar frases nuevas sin traducir.
- Verificación en dos pasos obligatoria en el admin (django-otp y segno): alta con código
  QR en el primer ingreso, 10 códigos de respaldo de un solo uso, "Verificación en dos
  pasos" en el menú de la cuenta (regenerar códigos, otro teléfono) y "Restablecer 2FA"
  en la lista de usuarios para los administradores. `ORION_2FA_REQUIRED` lo apaga en
  desarrollo y `orion.W002` avisa si está apagado sin `DEBUG`.
- Calendario de publicaciones en el admin: publicaciones y bajas programadas del mes, de
  las páginas que cada usuario puede editar, con lista por día en el celular.
- Vista previa compartible: enlaces temporales (1, 7 o 30 días, revocables) en
  `/_preview/<código>/` que muestran el último borrador sin cuenta, sin indexarse ni
  guardarse en caché (migración `orion_editor.0002_previewlink`).
- Aviso a los administradores, en el panel y el calendario, cuando una publicación o baja
  programada lleva más de una hora de atraso (la tarea `publish_scheduled` no corre);
  el README documenta el cron.
- Imágenes en AVIF con WebP de respaldo (`<picture>`), con medidas con nombre
  (`orion.core.images`, `ORION_IMAGE_SIZES`) y la etiqueta `{% responsive_image %}`; la
  imagen del Hero y la del artículo se piden primero y el Hero inicial se precarga
  (`{% main_image_preload %}`).
- Biblioteca de imágenes: recortes generados en segundo plano al subir, originales
  reducidos a 2048 px, SVG aceptados y limpiados, límite de peso configurable
  (`ORION_IMAGE_MAX_UPLOAD_MB`), comandos `orion_generate_renditions` y
  `orion_unused_images`; los ajustes del sitio entran al índice de referencias (el uso
  de los logos se ve en el admin).
- SEO (`orion.seo`): título con el nombre del sitio, descripción con respaldos, canónica,
  Open Graph, Twitter Card, JSON-LD (sitio, organización, migas de pan, artículo),
  "No indexar" y "No seguir los enlaces" por página (`SeoMixin`), `/sitemap.xml` con los
  idiomas públicos, `/robots.txt` editable, favicon y verificación de Search Console en
  **Datos del sitio → SEO**, y descripción del sitio por idioma en **Textos del sitio**.
- Redirecciones de Wagtail para los Administradores (con importación CSV y creación
  automática al cambiar un slug) y monitor de URLs que dan 404 en **Informes**.
- Caché de página completa para visitas sin sesión (`orion.core.cache`), que se vacía
  sola al publicar o editar datos del sitio, con `ORION_PAGE_CACHE`,
  `ORION_PAGE_CACHE_MODELS` y el comando `orion_clear_page_cache`; menús calculados una
  vez por idioma; `ETag` y `Last-Modified` con respuestas 304.
- Caché configurable con `CACHE_URL` (archivos por defecto, Redis con `orion[redis]`,
  memoria), con claves propias de cada proyecto.
- Archivos estáticos con WhiteNoise: Brotli y gzip, nombres con hash e `immutable`.
- `ORION_FONT_PRELOAD` precarga las fuentes woff2 del proyecto.
- Pruebas con un presupuesto de consultas por tipo de página.
- Formularios (`orion.forms`): página Formulario con el constructor de Wagtail más
  teléfono y archivo adjunto (guardado en privado y descargable solo desde el admin),
  texto de agradecimiento o redirección, bloque Formulario, antispam siempre activo
  (CSRF, campo trampa, tiempo mínimo y límite por IP), consentimiento con enlace a la
  política de privacidad (**Datos del sitio**), límites de campos por proyecto, aviso por
  email con remitente, respuesta a quien envió y prueba desde el admin, y el comando
  `orion_create_example_forms`.
- Bandeja de envíos: estado (nuevo, leído, respondido) con filtro, búsqueda, detalle con
  notas internas, exportación CSV y Excel limpia, retención de 12 meses
  (`ORION_FORMS_RETENTION_MONTHS`, comando `orion_purge_submissions`) y borrado de los
  adjuntos al borrar envíos.
- Buscador del sitio (`orion.search`): índice del texto de los bloques, resúmenes e
  introducciones; configuración de idioma de PostgreSQL según el idioma base
  (`ORION_SEARCH_CONFIG`); búsqueda aproximada si `pg_trgm` está activo; página de
  resultados en `/buscar/` con filtro por tipo y paginación; formulario en el
  encabezado (`ORION_SEARCH_IN_HEADER`); resultados destacados para Editores y
  Administradores; informe de búsquedas frecuentes y sin resultados.
- Fragmentos de código desde el admin (`orion.snippets`): ubicación, activar y
  desactivar, alcance por páginas, tipos de página e idiomas, historial con
  restauración, permiso sin grupos (solo superusuarios por defecto), nunca en el admin ni
  en vistas previas, e interruptor de emergencia `ORION_SCRIPTS_DISABLED`.
- Pantalla **Integraciones** (`orion.integrations`) para administradores: estado del
  email (apagado, sin probar, activo o con errores), configuración sin la contraseña,
  último envío y último error, email de prueba, guía de activación con cPanel y
  proveedor de mapas. Registro de cada envío por SMTP y aviso en el panel de inicio
  cuando los emails no salen.
- Los envíos de formularios guardan si su aviso por email salió; el comando
  `orion_retry_form_emails` reenvía los pendientes de los últimos
  `ORION_FORMS_EMAIL_RETRY_DAYS` días (3 por defecto).
- Checklist de alta de cliente en `docs/alta-de-cliente.md`.
- Límite de intentos de login con django-axes: 5 contraseñas incorrectas bloquean al
  usuario desde esa IP por 15 minutos (`ORION_LOGIN_FAILURE_LIMIT`,
  `ORION_LOGIN_LOCKOUT_MINUTES`), con pantalla de bloqueo traducida y desbloqueo por
  comando; sin registro de cada ingreso.
- `ORION_TRUSTED_PROXIES`: la IP del visitante se lee de `X-Forwarded-For` detrás de
  proxies propios, para el límite de login y el de envíos de formularios.
- Recuperar la contraseña desde el login solo cuando hay servidor de email (o en
  desarrollo).
- Cambiar el email de una cuenta cierra sus otras sesiones, como ya pasaba con la
  contraseña.
- HTTPS forzado fuera de debug (salvo `/health/`) y HSTS de un año
  (`ORION_HSTS_SECONDS`); `X-Forwarded-Proto` solo con `ORION_TRUSTED_PROXIES`.
- Política de seguridad de contenido en el sitio público con un nonce nuevo por respuesta
  (también en la caché de página), `ORION_CSP` y `ORION_CSP_REPORT_ONLY`; los scripts de
  Orion, la barra de Wagtail y los fragmentos de código llevan el nonce.
- Documentos limitados por extensión (`ORION_DOCUMENT_EXTENSIONS`) y peso
  (`ORION_DOCUMENT_MAX_UPLOAD_MB`); documentos y adjuntos de formularios se validan por
  su contenido.

### Changed

- **Atención:** con django-axes, `client.login()` no funciona en las pruebas de los
  proyectos; usar `client.force_login()`.
- **Atención:** las plantillas de un proyecto con scripts propios necesitan
  `nonce="{{ request.csp_nonce }}"`, y los fragmentos de código con `onclick=` o enlaces
  `javascript:` dejan de ejecutarlos.
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

- El aviso de publicación programada detenida salía en inglés con dos o más atrasadas:
  faltaba una forma del plural en español; una prueba revisa todos los plurales.
- Leaflet incluido con sus imágenes y sin la referencia a un mapa de código ausente, que
  hacía fallar `collectstatic` con nombres con hash.
- Pruebas de la ruta del admin que dependían del orden de ejecución, y pruebas de ajustes
  que dependían de las variables del `.env` de quien las corre.
- `.env.example` incluye `DATABASE_CONN_MAX_AGE`; una prueba verifica que lista toda
  variable que leen los ajustes base.
- Documentado que `pipenv run` carga `.env` pisando las variables del shell, y cómo
  apuntar las pruebas a las bases de Docker.
