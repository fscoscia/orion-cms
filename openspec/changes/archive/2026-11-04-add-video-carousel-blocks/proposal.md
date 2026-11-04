# Proposal

## Why

Orion no puede mostrar video propio ni carruseles, y sitios como FlavsMedia (reels,
testimonios en video) y Enex (hero que rota entre mensajes) dependen de esas dos piezas.
Hoy cada proyecto tendría que reescribirlas, con su accesibilidad y su compatibilidad con
la política de seguridad de contenido.

## What Changes

- Nuevo bloque **Video**: un archivo MP4 o WebM de la biblioteca de documentos con imagen
  de portada obligatoria. Dos modos: con controles (lo inicia el visitante) o ambiente
  (sin sonido, en bucle, solo mientras está en pantalla). Formato horizontal o vertical.
- Nuevo bloque **Carrusel**: diapositivas con imagen, video opcional, título, texto y
  enlace. Dos disposiciones: una diapositiva a todo el ancho o varias tarjetas visibles.
  Navegación con flechas, puntos, teclado y gesto táctil; sin JavaScript se recorre con
  scroll.
- Una página que abre con un Carrusel a todo el ancho no muestra el encabezado visible
  de la página: conserva su título como `h1` solo para lectores de pantalla, y la primera
  imagen se carga de inmediato.
- La biblioteca de documentos acepta MP4 y WebM, con su propio límite
  (`ORION_VIDEO_MAX_UPLOAD_MB`, 100 por defecto) y comprobación del contenido real.
- La guía de Nginx del README declara `client_max_body_size`: sin esa línea, Nginx
  rechaza toda subida de más de 1 MB, incluidas las imágenes de hoy.
- Sin dependencias nuevas. Ningún cambio rompe contenido existente.

### Fuera del alcance

- Videos de YouTube, Vimeo u otras plataformas (siguen a futuro en la especificación).
- Transcodificar o comprimir video en el servidor: el editor sube el archivo ya
  preparado.
- Subtítulos (pistas VTT) y almacenamiento externo de medios.
- Avance automático del carrusel: se puede sumar después como un campo más, sin romper
  contenido.
- Localizador de estaciones, promociones, popups y animaciones de scroll: quedan en cada
  proyecto.

## Capabilities

### New Capabilities

Ninguna: los bloques pertenecen a las capacidades existentes.

### Modified Capabilities

- `content-blocks`: la biblioteca suma Video y Carrusel, con sus campos y validaciones.
- `block-presentation`: cómo se reproduce el video y cómo se usa el carrusel, con mouse,
  teclado, gesto táctil y sin JavaScript.
- `page-types`: el `h1` de una página que abre con un Carrusel a todo el ancho.
- `site-security`: formatos y límite de los videos en la biblioteca de documentos.

## Impact

- **Código:** `core/blocks/content.py`, `core/uploads.py`, `core/document_forms.py`,
  `core/images.py`, `core/templatetags/orion_core.py`, `settings/base.py`,
  `pages/models.py`, `page_header.html`, plantillas de bloques nuevas, `orion.js` y
  `orion.css` (recompilado).
- **Migraciones:** una en `orion.pages` que solo actualiza la definición de los bloques;
  no toca datos.
- **Proyectos:** quien define `ORION_DOCUMENT_EXTENSIONS` debe sumar `mp4` y `webm` para
  usar el bloque. Los proyectos con su propio cuerpo de página no cambian.
- **Operación:** los videos ocupan disco y agrandan los respaldos, que incluyen
  `MEDIA_ROOT`.
- **Documentación:** README, `docs/guias/crear-un-bloque.md` y CHANGELOG.
