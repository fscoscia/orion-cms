# Orion: especificación funcional

Especificación funcional del CMS base Orion, sobre Wagtail 7.4 LTS y Django 5.2 LTS. Toma
como punto de partida el prototipo "opción 1" (Wagtail amigable), iguala lo que ofrece
ruweb-cms y lo supera en rendimiento, SEO y seguridad. Cada funcionalidad indica si entra
en la versión 1 (v1) o queda a futuro. Todo lo que depende de una plataforma externa está
marcado a futuro, salvo los mapas de OpenStreetMap, que entran por decisión expresa.

Este documento es la fuente del alcance. Cada fase se implementa como uno o varios cambios
de OpenSpec (`openspec/changes/`); al archivarse, sus comportamientos pasan a
`openspec/specs/`, que es la referencia de lo ya construido.

## Plan de fases

| Fase | Contenido | Estado |
| --- | --- | --- |
| 0. Esqueleto | Paquete instalable, configuración por entorno, chequeo de salud, rutas, proyecto de ejemplo, pruebas en PostgreSQL y MySQL, herramientas | Hecha y archivada (`add-project-skeleton`, `fix-skeleton-qa-findings`) |
| 1. Contenido y multi-idioma | Cinco cambios, en este orden: 1) base multi-idioma (idiomas, URLs por idioma, selector, hreflang); 2) datos del sitio, menús y layout base con Tailwind 4; 3) biblioteca de bloques; 4) tipos de página, artículos, taxonomías y RSS; 5) mapas. El multi-idioma va primero porque los modelos de los demás dependen de él | Hecha y archivada (`add-multilingual-foundation`, `add-site-data-navigation-layout`, `add-content-blocks`, `add-page-types`, `add-maps`, `fix-block-previews-and-slugs`) |
| 2. Experiencia del editor | Cinco cambios, en este orden: 1) panel de inicio, navegación y marca del cliente en el admin; 2) vista previa; 3) roles y admin completo en español; 4) doble factor (2FA); 5) flujo editorial (calendario, vista previa compartible, flujos de aprobación, publicación programada, autoguardado) | Hecha y archivada (`add-admin-home-and-branding`, `add-editor-preview`, `add-roles-and-admin-spanish`, `add-two-factor-auth`, `add-editorial-workflow`) |
| 3. Medios, rendimiento y SEO | Tres cambios, en este orden: 1) imágenes (AVIF y WebP con `<picture>`, carga diferida, hero priorizado, recortes al subir, límites de subida, SVG limpios, imágenes huérfanas); 2) SEO (meta y respaldos, Open Graph, canónica, sitemap, robots.txt, favicon, JSON-LD, noindex, Search Console, redirecciones y monitor de 404); 3) rendimiento (caché de página completa que se vacía entera al publicar, caché de encabezado y pie, límite de consultas, WhiteNoise con Brotli, ETag, fuentes propias precargadas). Caché en archivos por defecto, Redis opcional | En curso |
| 4. Formularios, buscador, scripts e integraciones | Constructor de formularios con antispam, buscador, scripts desde el admin, pantalla de Integraciones, SMTP | Pendiente |
| 5. Seguridad y operación | Headers de seguridad (HSTS, CSP), límite de intentos de login, backups, instalador, plantilla de proyecto, guías de deploy, presupuesto de Lighthouse | Pendiente |
| 6. Validación | Construir el sitio de Intervita sobre Orion como primer sitio real | Pendiente |

## Alcance y decisiones

La v1 es la base genérica, sin contenido de ningún cliente; Intervita sirve solo como sitio
de prueba. Estas decisiones ya están tomadas:

| Decisión | Elección | Motivo |
| --- | --- | --- |
| Producto | CMS base reutilizable, distribuido como paquete versionado en GitHub (se instala desde el repositorio, sin publicarlo en PyPI) más una plantilla de proyecto | Cada sitio se construye encima y se actualiza cambiando la versión, sin copiar código entre proyectos como en ruweb |
| Stack | Python 3.12, Django 5.2 LTS, Wagtail 7.4 LTS | Versiones con soporte largo y parches de seguridad |
| Base de datos | PostgreSQL como principal; MySQL 8 / MariaDB 10.5+ también soportado (por ejemplo, en cPanel) | PostgreSQL da mejor búsqueda en español y migraciones más seguras |
| Entrega del sitio público | Dinámica, con caché de página completa que se borra al publicar | Formularios y buscador funcionan sin servicios externos |
| Front | HTML generado en el servidor (templates de Django), estilos con Tailwind 4 y JS sin framework o Alpine.js | Libertad total de diseño sin una segunda aplicación |
| Multi-idioma | Entra en v1, con el modelo de ruweb | Pedido explícito |
| Flujo de aprobación | El que trae Wagtail (workflows) | Suficiente; no se construye uno propio |
| Formularios | Armados por el editor con el constructor de Wagtail; antispam, consentimiento y límites fijados por la base | Decisión del equipo |
| MCP y API para agentes | A futuro | Se deja la arquitectura preparada |
| Plataformas externas | A futuro (CDN, reCAPTCHA, analytics, proveedores de email, traducción automática), salvo los mapas de OpenStreetMap | Criterio de alcance de la v1 |

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│ Núcleo: paquete versionado en GitHub (este repositorio)              │
│  Contenido        Admin y editor      Servicios          Rendimiento │
│  tipos de página  panel, vista previa formularios,       caché,      │
│  bloques, menús   revisiones, flujos  buscador, scripts, AVIF,       │
│  datos del sitio  roles y permisos    SEO, multi-idioma  2FA, headers│
└──────────────────────────────────────────────────────────────────────┘
                          ▲ usa y extiende
┌──────────────────────────────────────────────────────────────────────┐
│ Proyecto de cada cliente (su propio repositorio)                     │
│  Diseño: templates, CSS, fuentes   Bloques propios   Configuración   │
└──────────────────────────────────────────────────────────────────────┘
                          ▼ se despliega en
┌──────────────────────────────────────────────────────────────────────┐
│ Infraestructura: VPS o cPanel con Python · PostgreSQL o MySQL 8 ·    │
│ caché en archivos o base (Redis opcional) · a futuro: CDN, MCP       │
└──────────────────────────────────────────────────────────────────────┘
```

El núcleo concentra todo lo genérico y se actualiza cambiando su versión; cada cliente
solo escribe su diseño, sus bloques y su configuración. Los templates del proyecto
reemplazan a los de la base con el mismo nombre, sin tocar el paquete.

## Contenido y páginas

Las páginas se arman con bloques que el editor agrega, reordena y oculta; es la principal
ventaja sobre las secciones fijas de ruweb. En "Cómo": *Wagtail* = viene incluido,
*Paquete* = librería existente, *A construir* = código propio de la base.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Tipos de página base | Portada, Página libre, Página de contacto, Listado de artículos y Artículo, con reglas de dónde puede ir cada una | A construir | v1 |
| Biblioteca de bloques | Hero, Texto, Imagen, Galería, Imagen + texto, Tarjetas, Cifras animadas, Pestañas, Acordeón (FAQ), Llamada a la acción, Logos, Datos de contacto, Botón | A construir sobre StreamField | v1 |
| Ocultar un bloque sin borrarlo | Interruptor "Visible" en cada bloque, como `is_visible` de ruweb | A construir | v1 |
| Títulos con palabras resaltadas | La negrita en un título se pinta con el color de acento | A construir (ya está en la opción 1) | v1 |
| Destino de botón semántico | Elegir una página interna, una URL, un email o un teléfono; nunca la URL absoluta del propio sitio | A construir | v1 |
| Colección de artículos (blog o novedades) | Listado paginado, artículo con fecha, resumen, imagen y categorías; RSS | A construir | v1 |
| Taxonomías | Categorías jerárquicas y etiquetas, filtrables en los listados | A construir + django-taggit | v1 |
| Menús | Menú del encabezado y del pie con ítems anidados, editables por separado del árbol de páginas | A construir (fragmento) | v1 |
| Datos del sitio | Logo, logo del pie, contacto, redes sociales, enlaces y texto legal, en un solo lugar ("un dato, un lugar") | Wagtail settings | v1 |
| Contenido reutilizable | Fragmentos que se cargan una vez y se usan en varias páginas (convenios, testimonios, equipo) | Wagtail snippets | v1 |
| Plantillas de contenido inicial | Al instalar, páginas de ejemplo con imágenes de relleno en la proporción correcta | A construir | v1 |
| Mapas | Ubicación del negocio elegida haciendo clic en un mapa dentro de Datos del sitio, y bloque "Mapa" con uno o varios puntos; el proveedor de teselas se cambia por configuración | A construir con Leaflet + teselas de OpenStreetMap | v1 |

## Experiencia del editor

El objetivo es que un editor sin capacitación cargue contenido el primer día. Toma lo que
ya funciona en la opción 1 y suma el contrato de UX del editor de ruweb.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Panel de inicio | Saludo, acciones grandes (crear página o artículo, editar portada, subir fotos) y cambios sin publicar | A construir (ya está en la opción 1) | v1 |
| Menú lateral simplificado | Cada rol ve solo lo que usa; atajos a "Nuevo artículo" y "Ver el sitio" | A construir (ya está en la opción 1) | v1 |
| Vista previa en vivo | Abierta por defecto, en tamaño escritorio, a media pantalla, con botón "Vista previa" visible; tamaños celular y tablet | Wagtail + ajustes (ya está en la opción 1) | v1 |
| Enlaces bloqueados en la vista previa | Los enlaces no navegan dentro de la vista previa; hay un "Ver publicado" aparte | A construir | v1 |
| Bloques con vista previa y descripción | Al elegir un bloque se ve cómo queda y para qué sirve | Wagtail | v1 |
| Nombres y ayudas en español | Etiquetas, textos de ayuda y mensajes del admin traducidos y completos (hoy Wagtail deja frases en inglés) | A construir (traducciones) | v1 |
| Editor de texto acotado | Solo negrita, itálica, enlaces, listas y subtítulos; perfiles distintos por campo | Wagtail (Draftail) | v1 |
| Edición desde el sitio | Barra flotante para editar la página que se está mirando; accesos a Encabezado y Pie | Wagtail userbar + a construir | v1 |
| Roles | Administrador (todo) y Editor (prepara contenido); permisos por sección del árbol | Wagtail | v1 |
| Marca del cliente en el admin | Logo, colores y nombre del cliente en el login y el panel | A construir (ya está en la opción 1) | v1 |
| Modo "Editar / Vista previa" en celular | En pantallas chicas, alternar entre formulario y vista previa en vez de apretar las dos | A construir | v1 |

## Flujo editorial

Casi todo lo trae Wagtail 7.4 y cubre lo que ofrece ruweb; solo hay que configurarlo y
traducirlo. Lo único que falta es compartir una vista previa con alguien sin cuenta.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Borrador y publicado | Los cambios se guardan como borrador sin tocar lo publicado | Wagtail | v1 |
| Historial de versiones | Cada guardado queda como revisión, con autor; se comparan y se restaura una anterior | Wagtail | v1 |
| Flujo de aprobación | El editor envía a revisión y un administrador aprueba, rechaza o pide cambios; flujos distintos por sección | Wagtail workflows | v1 |
| Comentarios en el editor | Comentarios anclados a un campo, con respuestas y resolución | Wagtail | v1 |
| Programar publicación y vencimiento | Fecha de salida y fecha de baja por página | Wagtail + cron de `publish_scheduled` | v1 |
| Autoguardado | Guarda el borrador solo mientras se edita | Wagtail (`WAGTAIL_AUTOSAVE_INTERVAL`) | v1 |
| Aviso de edición simultánea | Avisa si otra persona está editando la misma página; bloqueo manual de páginas | Wagtail | v1 |
| Registro de actividad | Quién creó, editó, publicó o borró qué y cuándo, con filtros | Wagtail (informe de actividad) | v1 |
| Calendario de publicaciones | Vista mensual de lo programado y lo que vence | A construir | v1 |
| Vista previa compartible | Enlace temporal para que alguien sin cuenta vea un borrador | A construir o paquete | v1 |
| Notificaciones por email del flujo | Aviso al aprobador y al autor | Wagtail (requiere un servidor de email; ver Integraciones) | v1 |

## Multi-idioma

Mismo modelo que ruweb: idiomas ilimitados que se activan desde el admin, una página por
idioma vinculada a sus traducciones y el sitio arranca en un solo idioma. La traducción la
hace una persona; la automática queda a futuro.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Idiomas activables | Catálogo de idiomas; se agregan desde el admin; idioma base elegido al instalar | Wagtail i18n (`Locale`) | v1 |
| Activo y público por separado | Un idioma puede editarse sin verse todavía en el sitio | A construir | v1 |
| URLs por idioma | Base sin prefijo (`/servicios`), resto con prefijo (`/en/services`); traducción faltante o en borrador redirige al idioma base | Django i18n + a construir | v1 |
| Traducción de páginas y fragmentos | Crear la traducción desde la página original, campo por campo | wagtail-localize | v1 |
| Traducciones desactualizadas | Si cambia el original, la traducción se marca para revisar | wagtail-localize | v1 |
| Menús y datos del sitio por idioma | Menú, enlaces del pie, textos legales y etiquetas traducibles | A construir (Wagtail no traduce los settings) | v1 |
| Texto alternativo de imágenes por idioma | Una misma imagen con alt distinto en cada idioma | A construir | v1 |
| Selector de idioma y hreflang | Selector en el encabezado y etiquetas `hreflang` para SEO | A construir | v1 |
| Textos fijos del template traducibles | Ningún texto visible fijo en el código: todo sale del admin o de archivos de traducción | A construir | v1 |
| Traducción automática | Sugerencias con DeepL o Google Translate | wagtail-localize + servicio externo | A futuro |

## Medios

Las imágenes se sirven en AVIF con WebP de respaldo y en el tamaño justo para cada
pantalla. ruweb solo usa WebP: acá está la mayor ganancia de peso de página.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Biblioteca de imágenes | Búsqueda, colecciones, etiquetas, subida múltiple arrastrando | Wagtail | v1 |
| Punto focal | El recorte respeta la zona importante de la foto | Wagtail | v1 |
| AVIF + WebP responsivos | `<picture>` con `srcset` en AVIF y WebP, y medidas de 320 a 1920 px | Wagtail (`{% picture %}`) | v1 |
| Recortes generados al subir | Las variantes se crean al subir la imagen, no en la primera visita | A construir | v1 |
| Carga diferida y medidas | `loading="lazy"`, `decoding="async"`, `width` y `height` en todas menos la principal | A construir (componente de imagen) | v1 |
| Texto alternativo obligatorio | Alt requerido o marca explícita de "imagen decorativa" | Wagtail (`ImageBlock`) | v1 |
| Límites de subida | Tipos y peso máximo configurables; reducción del original a 2048 px | Wagtail + ajustes | v1 |
| SVG seguros | Se aceptan SVG, limpiando scripts y atributos peligrosos | A construir | v1 |
| Dónde se usa cada imagen | Lista de páginas que usan una imagen; aviso antes de borrarla | Wagtail (índice de referencias) | v1 |
| Imágenes huérfanas | Comando que lista las que no se usan en ningún lado | A construir | v1 |
| Documentos | PDF y Word con permisos y enlaces de descarga | Wagtail | v1 |
| Videos embebidos | YouTube y Vimeo por URL | Wagtail embeds (depende de YouTube o Vimeo) | A futuro |
| Almacenamiento externo | Guardar medios en S3 u otro servicio | django-storages | A futuro |

## SEO y redirecciones

Iguala lo de ruweb y suma datos estructurados y control de indexación por página, que su
`reqs.md` marca como faltantes. Las conexiones con Google y Meta quedan a futuro; mientras
tanto se cargan con "Scripts desde el admin".

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Título y descripción SEO | Por página, con valores de respaldo (título de la página, descripción del sitio) | Wagtail + a construir | v1 |
| Open Graph y Twitter Card | Imagen social por página y una imagen por defecto del sitio | A construir | v1 |
| URL canónica | En todas las páginas, armada en el momento (nunca guardada fija) | A construir | v1 |
| Sitemap | `sitemap.xml` con todas las páginas publicadas y sus idiomas | Wagtail contrib sitemaps | v1 |
| robots.txt editable | Desde Datos del sitio | A construir | v1 |
| Favicon | Desde Datos del sitio, con todos los tamaños | A construir | v1 |
| Datos estructurados (JSON-LD) | Organización, sitio web, artículo y migas de pan; supera a ruweb | A construir | v1 |
| No indexar por página | Casilla `noindex` / `nofollow` en cada página; supera a ruweb | A construir | v1 |
| Verificación de Search Console | Campo para la etiqueta meta de verificación | A construir | v1 |
| Redirecciones 301 y 302 | Desde el admin, con importación CSV | Wagtail contrib redirects | v1 |
| Redirección automática al cambiar una URL | Si se cambia el slug de una página publicada, se crea la redirección sola | Wagtail (`WAGTAILREDIRECTS_AUTO_CREATE`) | v1 |
| Monitor de 404 | Lista de URLs que dan error, con cantidad de visitas y botón para redirigirlas | A construir | v1 |
| Google Analytics 4, Meta Pixel, Tag Manager | Campos dedicados que generan el código y el aviso de cookies | A construir + servicio externo | A futuro |
| Métricas dentro del admin | Visitas y búsquedas de Search Console o Analytics en el panel | Servicio externo | A futuro |

## Formularios públicos

El editor crea y modifica formularios desde el admin con el constructor de Wagtail:
agrega campos, elige su tipo, marca los obligatorios y define a quién avisar. La base pone
lo que el editor no puede romper: antispam en todos, consentimiento de datos y retención.
Contacto y "Trabajá con nosotros" vienen armados como ejemplo. reCAPTCHA o Turnstile quedan
a futuro porque dependen de Google o Cloudflare.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Constructor de formularios | Página de tipo Formulario donde el editor agrega campos (texto, email, teléfono, número, área de texto, lista, casillas, fecha), los ordena, marca obligatorios y escribe ayudas | Wagtail contrib forms | v1 |
| Campo de archivo adjunto | Tipo de campo extra para CVs y documentos, con tipos y peso máximo permitidos; Wagtail no lo trae | A construir | v1 |
| Formularios de ejemplo | Contacto y Trabajá con nosotros ya armados al instalar, editables como cualquier otro | A construir | v1 |
| Mensaje de éxito | Texto de agradecimiento editable o redirección a una página | Wagtail + a construir | v1 |
| Formulario dentro de cualquier página | Bloque "Formulario" que inserta uno ya creado en una página libre o en la portada | A construir | v1 |
| Bandeja de envíos | Envíos de cada formulario con búsqueda, filtro por fecha y exportación CSV o Excel | Wagtail | v1 |
| Notas y estado de cada envío | Notas internas y estado (nuevo, leído, respondido) | A construir | v1 |
| Aviso por email | Destinatarios, asunto y remitente por formulario, con prueba de envío desde el admin | Wagtail + SMTP | v1 |
| Antispam siempre activo | CSRF, campo trampa (honeypot), límite de envíos por IP y tiempo mínimo de llenado; vive en la base y el editor no puede apagarlo | A construir | v1 |
| Límites al editor | Tipos de campo permitidos y cantidad máxima de campos, configurables por proyecto | A construir | v1 |
| Consentimiento de datos | Casilla de política de privacidad agregada sola a todo formulario, con enlace editable | A construir | v1 |
| Retención de datos | Borrado automático de envíos y archivos después de N meses (configurable) | A construir | v1 |
| reCAPTCHA v3 o Cloudflare Turnstile | Capa extra contra bots | Servicio externo | A futuro |
| Envío por API de email | Brevo, Amazon SES u otro por API; casi nunca hace falta, porque todos aceptan SMTP | Servicio externo | A futuro |

## Buscador del sitio

Usa la propia base de datos, sin servicios externos; en PostgreSQL entiende el español y
ordena por relevancia. ruweb no tiene buscador público.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Búsqueda en páginas y artículos | Incluye el texto de los bloques; respeta idioma y estado publicado | Wagtail search (base de datos) | v1 |
| Español y tolerancia a errores | Plurales y variantes ("médicos" encuentra "médico"); búsqueda aproximada | Wagtail + PostgreSQL (en MySQL es más básica) | v1 |
| Página de resultados | Resultados paginados con título, resumen y tipo; filtro por tipo de contenido | A construir | v1 |
| Resultados destacados | El editor fija qué página aparece primero para una búsqueda | Wagtail contrib search promotions | v1 |
| Búsquedas frecuentes y sin resultados | Informe para el editor | Wagtail (registro de consultas) + a construir | v1 |
| Buscador dedicado | Elasticsearch u OpenSearch para sitios grandes | Servicio externo | A futuro |

## Scripts desde el admin

Permite pegar código de terceros (analytics, píxeles, chats) sin tocar el repositorio, con
los mismos resguardos que ruweb. Es la vía para usar Google o Meta mientras sus
integraciones dedicadas están a futuro.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Fragmentos de código | Nombre, código y ubicación: `<head>`, inicio o final de `<body>` | A construir | v1 |
| Alcance | Todo el sitio, solo ciertas páginas o tipos de página, y por idioma | A construir | v1 |
| Permiso especial | Solo usuarios con un permiso dedicado pueden crear o activar fragmentos | A construir | v1 |
| Activar y desactivar | Cada fragmento se prende o apaga sin borrarlo | A construir | v1 |
| Interruptor de emergencia | Variable de entorno que apaga todos los fragmentos si uno rompe el sitio | A construir | v1 |
| Historial | Quién cambió qué fragmento y cuándo, con restauración | A construir (revisiones de Wagtail) | v1 |
| Nunca en el admin | Los fragmentos no se cargan en las pantallas del admin ni en la vista previa compartible | A construir | v1 |

## Rendimiento

Meta de la v1: Lighthouse 95 o más en celular y LCP menor a 2,5 s en la portada de
ejemplo, con las páginas en caché respondiendo en menos de 20 ms. La caché de página
completa, AVIF y los headers de caché son justo lo que el `reqs.md` de ruweb marca como
faltante.

| Punto | Funcionalidad | Detalle | Versión |
| --- | --- | --- | --- |
| Velocidad | Caché de página completa | El HTML se arma una vez y se guarda; al publicar, se borra solo lo afectado (la página, sus listados, la portada si muestra novedades). Supera a ruweb | v1 |
| Velocidad | Caché de encabezado, pie y menús | Se calculan una vez por idioma y se invalidan al editar menús o datos del sitio | v1 |
| Velocidad | Consultas optimizadas | Sin consultas repetidas por bloque; prueba automática que limita la cantidad de consultas por página | v1 |
| Velocidad | Conexiones persistentes a la base | `CONN_MAX_AGE` en producción (ya configurado en la Fase 0) | v1 |
| Recursos | Servidor de aplicación ajustado | Gunicorn con pocos procesos e hilos, reciclado periódico; con la caché, casi ninguna visita llega a Django | v1 |
| Recursos | Caché sin servicios extra | Caché en archivos o en la base por defecto; Redis opcional si el servidor lo tiene | v1 |
| Peso | Imágenes AVIF + WebP responsivas | Ver Medios | v1 |
| Peso | Imagen principal priorizada | El hero como `<img>` con `fetchpriority="high"` y precarga, no como fondo CSS | v1 |
| Peso | Fuentes propias | woff2 servidas por el sitio, solo los pesos usados, precargadas y con `font-display: swap`; sin Google Fonts | v1 |
| Peso | CSS y JS mínimos | Tailwind 4 compilado y purgado (solo las clases usadas), JS sin framework, cargado con `defer` | v1 |
| Peso | Compresión y caché de archivos | Brotli y gzip, nombres con hash y `Cache-Control: immutable` | v1 (WhiteNoise) |
| Peso | Headers de caché del HTML | `ETag` y `Last-Modified` para que el navegador revalide sin descargar | v1 |
| Control | Presupuesto de rendimiento | Script que corre Lighthouse sobre las páginas de ejemplo y falla si baja de la meta | v1 |
| Velocidad | CDN con purga al publicar | Cloudflare u otro, con `wagtail.contrib.frontend_cache` | A futuro |
| Recursos | Exportación estática | Generar el sitio en HTML para hosting sin Python | A futuro |

## Seguridad

Iguala a ruweb (2FA, URL de login configurable, límite de intentos) y suma headers de
seguridad y HTTPS forzado, que ruweb no tiene en la aplicación.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Doble factor (2FA) | Código de una app autenticadora (TOTP) y códigos de respaldo; obligatorio para administradores | django-otp / paquete 2FA para Wagtail | v1 |
| Límite de intentos de login | Bloqueo temporal por usuario e IP después de 5 intentos | django-axes | v1 |
| URL de login configurable | Cambiar `/admin/` por otra ruta | Hecho en la Fase 0 (`ORION_ADMIN_PATH`) | v1 |
| Recuperar contraseña | Por email, con enlace de un solo uso | Wagtail | v1 |
| Política de contraseñas | Largo mínimo, contraseñas comunes bloqueadas | Django | v1 |
| Cerrar sesiones | Al cambiar la contraseña o el email se cierran las demás sesiones | Django + a construir | v1 |
| Headers de seguridad | HSTS, Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, X-Frame-Options; supera a ruweb | Django + django-csp | v1 |
| HTTPS forzado y cookies seguras | Redirección a HTTPS y cookies `Secure`/`HttpOnly` en producción (las cookies ya están desde la Fase 0); supera a ruweb | Django | v1 |
| HTML de contenido saneado | Todo HTML que escriben los editores pasa por un filtro de etiquetas permitidas | Wagtail + a construir | v1 |
| Subidas validadas | Tipo real del archivo (no solo la extensión), peso y SVG limpios | A construir | v1 |
| Registro de actividad | Ver Flujo editorial | Wagtail | v1 |
| Claves de API con alcance | Solo lectura, solo borradores o completo; para el MCP | A construir | A futuro |

## Operación, deploy y calidad

Un sitio nuevo se instala con un comando y se actualiza cambiando la versión de la base,
sin copiar código a mano entre proyectos como pasa con ruweb.

| Funcionalidad | Detalle | Cómo | Versión |
| --- | --- | --- | --- |
| Plantilla de proyecto nuevo | Un comando crea el proyecto de un cliente con la base ya conectada | A construir | v1 |
| Instalador | Comando que valida requisitos, migra, crea el administrador, elige el idioma base y carga contenido de ejemplo | A construir | v1 |
| Actualizaciones de la base | La base es un paquete con changelog y etiquetas de versión en GitHub; cada proyecto la instala con pip desde el repositorio fijando la etiqueta (`git+https://…@v1.2.0`), y actualizar = cambiar la etiqueta y migrar. Si el repositorio es privado, el servidor necesita una clave de acceso de solo lectura | A construir | v1 |
| Backups y restauración | Comando que empaqueta base de datos y medios en un archivo, lo inspecciona y lo restaura en otro servidor | A construir | v1 |
| Tareas programadas | Cron para publicar y dar de baja contenido programado, purgar envíos vencidos y limpiar sesiones | Comandos de Wagtail y Django | v1 |
| Deploy en VPS | Guía con Gunicorn, Nginx, PostgreSQL y certificado HTTPS | A construir (documentación) | v1 |
| Deploy en cPanel con Python | Guía para "Setup Python App": `passenger_wsgi.py`, archivos estáticos, MySQL y cron | A construir (documentación) | v1 |
| Configuración por variables de entorno | Claves, base de datos y dominio fuera del código; `.env.example` | Hecho en la Fase 0 | v1 |
| Chequeo de salud | URL `/health/` para monitorear que el sitio y la base responden | Hecho en la Fase 0 | v1 |
| Tests | Unitarios, de integración y de punta a punta con Playwright para el admin y el sitio; la suite corre en PostgreSQL y en MySQL | Unitarios e integración desde la Fase 0; Playwright a construir | v1 |
| Chequeo de convenciones | Comando que detecta textos fijos en templates, imágenes sin alt y traducciones faltantes | A construir | v1 |
| Linters | Ruff para Python y formato automático; hooks de git | Hecho en la Fase 0 | v1 |
| Documentación para desarrolladores y agentes | Guías por tarea (crear bloque, tipo de página, formulario) y un `AGENTS.md`, preparando el MCP | `AGENTS.md` desde la Fase 0; guías a construir | v1 |
| Integración continua | Tests y presupuesto de rendimiento en cada cambio | GitHub Actions u otro | A futuro |
| Monitoreo de errores | Alertas de errores en producción | Sentry u otro | A futuro |
| Deploy en plataformas gestionadas | Railway, Render, Fly.io | Servicio externo | A futuro |

## Integraciones externas

Toda integración externa es opcional, viene apagada y el CMS funciona completo sin
ninguna: si el cliente no tiene la cuenta, esa función se desactiva o la reemplaza la
versión propia de la base. Las cuentas son del cliente y la agencia entra como usuario
invitado.

| Funcionalidad | Detalle | Versión |
| --- | --- | --- |
| Pantalla de Integraciones | Estado de cada una (apagada, activa, mal configurada), botón de prueba y aviso en el panel si una activa falla | v1 |
| Se activa solo si está completa | Una integración se enciende cuando tiene todas sus claves y la prueba pasa; si no, sigue apagada | v1 |
| Claves por proyecto | Cada sitio carga las suyas; ninguna clave fija en el código de la base | v1 |
| Claves públicas en el admin, secretas en el servidor | Las públicas (ID de Analytics, clave de sitio del antispam) se cargan desde el admin con un permiso especial; las secretas (clave secreta del antispam, API de email) van en variables de entorno y nunca quedan en la base de datos ni en los backups | v1 |
| Si el servicio externo se cae | El sitio sigue: el antispam vuelve a la capa propia, los emails se reintentan con el cron y el envío queda guardado en la bandeja | v1 |
| Checklist de alta de cliente | Guía con las cuentas que crea el cliente, cómo invita a la agencia y qué datos pasa | v1 |
| Email por SMTP configurable | Servidor, puerto, usuario, contraseña, SSL o TLS y remitente por variables de entorno (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_SSL`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, `EMAIL_TIMEOUT`). Sirve con el email del hosting, Google Workspace, Microsoft 365 o el SMTP de Brevo, SES o Mailgun. Nombre del remitente, respuesta y destinatarios se editan en el admin; prueba de envío en Integraciones; SSL y TLS juntos se rechazan al arrancar (hecho en la Fase 0) | v1 |
| Casilla de cPanel como opción por defecto | El checklist recomienda crear una casilla para el sitio en cPanel (por ejemplo `no-responder@dominio`) y usar sus datos SMTP. Un proveedor dedicado (Brevo, SES) queda para mucho volumen o problemas de spam. La guía advierte sobre los límites de envío del hosting, la reputación compartida, SPF y DKIM si el DNS está en otro lado, y hostings que obligan a usar localhost | v1 |
| Guía dentro de cada integración | Cada integración trae en su pantalla los pasos para activarla, con enlaces al servicio: crear la casilla en cPanel, obtener las claves de Turnstile, el ID de Analytics, etc. Indica qué dato va en el admin y cuál en las variables de entorno. Tomado de ruweb, que lo hace para Brevo | v1 |

Qué pasa con cada integración si el cliente no la tiene:

| Integración | Sin la cuenta, el CMS usa | Cuenta de |
| --- | --- | --- |
| CDN (Cloudflare) | La caché de página completa del servidor | Cliente |
| Turnstile o reCAPTCHA | El antispam propio: CSRF, campo trampa, límite por IP y tiempo mínimo | Cliente |
| Analytics, Tag Manager, Meta Pixel | Nada se inserta; siguen disponibles los Scripts desde el admin | Cliente |
| Email por API (Brevo) | SMTP configurable (por defecto, una casilla de cPanel; u otro proveedor); sin SMTP, los envíos quedan en la bandeja y el panel avisa que no salen emails | Cliente |
| Traducción automática (DeepL) | Traducción manual; el botón de sugerir traducción no aparece | Cliente o agencia |
| Buscador dedicado | El buscador sobre la base de datos | Cliente o agencia |
| Almacenamiento externo (R2, S3) | Disco del servidor | Cliente |
| Mapas comerciales | OpenStreetMap; si los mapas están apagados, la dirección en texto con un enlace a abrirla en un mapa | Cliente |
| Monitoreo de errores (Sentry) | Registro en archivos y email a los administradores | Agencia |

## A futuro

Todo lo que depende de una plataforma externa, más el MCP. La v1 deja el lugar preparado
para cada uno. La mayoría tiene plan gratuito suficiente para un sitio institucional
(Cloudflare, Turnstile, Google, Brevo, DeepL, Sentry, GitHub Actions); lo único realmente
pago es el hosting gestionado.

| Funcionalidad | Depende de | Qué deja preparado la v1 |
| --- | --- | --- |
| MCP y API para agentes, con claves de alcance limitado | Decisión de producto (no es externo) | Operaciones de contenido reutilizables desde el admin y desde una futura API, y `AGENTS.md` |
| CDN con purga al publicar | Cloudflare, CloudFront u otro | Caché de página completa con invalidación por página |
| reCAPTCHA v3 o Turnstile | Google o Cloudflare | Antispam propio en todos los formularios |
| Google Analytics 4, Meta Pixel, Tag Manager, métricas en el admin | Google, Meta | Scripts desde el admin y campo de verificación de Search Console |
| Envío de email por API | Brevo, SendGrid, Amazon SES | Envío por SMTP |
| Traducción automática | DeepL o Google Translate | wagtail-localize instalado |
| Buscador dedicado | Elasticsearch u OpenSearch | Buscador sobre la base de datos con la API de búsqueda de Wagtail |
| Videos embebidos | YouTube, Vimeo | Biblioteca de bloques extensible |
| Almacenamiento de medios externo | S3 u otro | Medios detrás de la capa de almacenamiento de Django |
| Exportación estática | Hosting de archivos o CDN | Sitio público sin estado por visita |
| Integración continua y monitoreo de errores | GitHub Actions, Sentry | Tests y presupuesto de rendimiento ejecutables en local |
| Deploy en plataformas gestionadas | Railway, Render, Fly.io | Configuración por variables de entorno |
| Proveedor de mapas comercial o propio | Google Maps, Mapbox o un servidor de teselas propio | Mapas con OpenStreetMap y proveedor configurable; la política de uso de OSM no admite tráfico alto |

## Decisiones tomadas

- **Formularios:** armados por el editor con el constructor de Wagtail, con antispam,
  consentimiento y límites fijados por la base.
- **Distribución:** paquete versionado en GitHub más plantilla de proyecto; actualizar un
  cliente es cambiar una versión.
- **Base de datos:** PostgreSQL como principal, con MySQL 8 / MariaDB 10.5+ también
  soportado y probado.
- **Mapas:** entran en la v1, con Leaflet y teselas de OpenStreetMap, como ruweb.
- **CSS:** Tailwind 4, desde la Fase 1 (cada bloque nace con estilos base).
- **Datos del sitio por idioma:** lo que no cambia por idioma (logos, teléfonos, email,
  redes, ubicación) en ajustes del sitio; lo traducible (texto legal, eslogan, etiquetas
  del pie) en un fragmento traducible con wagtail-localize.
- **Entorno de desarrollo:** pipenv; Docker Compose opcional para las bases.

## Referencias

- **Prototipos:** `../orion-prototipos/` (fuera de este repositorio). La opción 1
  (`opcion1-wagtail`) es la réplica de Intervita sobre Wagtail: de ahí se reutilizan los
  bloques, los hooks del admin (panel de inicio, menú, vista previa abierta por defecto),
  el componente de íconos y los templates, reescritos dentro de la estructura de Orion.
- **ruweb-cms:** el CMS en Laravel con el que se comparó Orion. De ruweb se toman el
  modelo multi-idioma, la visibilidad por sección, el contrato de UX del editor, las guías
  dentro de cada integración y el antispam obligatorio.
