# Design

## Context

Ver `proposal.md` para el motivo. Lo que condiciona el enfoque:

- Los bloques heredan de `BaseContentBlock` (Estilo y Visible) y se reúnen en
  `ContentStreamBlock`. `BodyStreamField` describe solo los bloques de Orion, así que
  sumar uno genera una migración en `orion.pages`.
- `ArticleStreamBlock` hereda de `ContentStreamBlock`: los bloques nuevos llegan también
  a los artículos.
- El sitio público usa Alpine en su versión CSP: `orion.js` define los componentes y las
  plantillas solo los nombran. `media-src` ya admite `'self'`, así que la política no
  cambia.
- Los documentos se sirven por una vista de Django, que no responde pedidos de rango
  (`Range`). Safari los exige para reproducir video y sin ellos no se puede adelantar.
  `MEDIA_URL`, en cambio, lo sirve directo el servidor web en las dos guías de deploy.
- `matches_extension` compara firmas al inicio del archivo; la de MP4 está en el byte 4.
- `page.starts_with_hero` decide si se muestra el encabezado de la página y
  `get_leading_hero_image` decide la precarga.

## Goals / Non-Goals

**Goals:**

- Dos bloques que funcionen con el diseño base, sin compilar CSS, y que cada proyecto
  adapte con `ORION_BLOCK_STYLES`.
- Cero peso de video al abrir la página y ningún script nuevo aparte de `orion.js`.

**Non-Goals:**

- Un modelo o una biblioteca propia de videos, y un reproductor propio.
- Generar la portada a partir del video.

## Decisions

### Los videos viven en la biblioteca de documentos

Se usa `DocumentChooserBlock` y se suman `mp4` y `webm` a `DOCUMENT_EXTENSIONS`. Reutiliza
permisos, colecciones, búsqueda, referencias de uso y la validación de `DocumentForm`, sin
tablas ni migraciones de datos.

Alternativas: `wagtailmedia` agrega una dependencia y una biblioteca paralela para algo
que los documentos ya cubren; una URL externa no valida nada y deja a los editores
gestionando otro servicio.

### El reproductor usa la URL directa del archivo

La plantilla usa `document.file.url`, no `document.url`, para que el servidor web atienda
los pedidos de rango. Esto saltea la vista de documentos y, con ella, las restricciones
de privacidad por colección: un video público no debe estar en una colección privada.
Bajo `SCRIPT_NAME`, `MEDIA_URL` ya incluye el prefijo.

Alternativa: implementar rangos en una vista propia, lo que ocupa un proceso de Python
por cada reproducción.

### Un solo límite aparte para video

`DocumentForm.clean_file` elige `ORION_VIDEO_MAX_UPLOAD_MB` (100) para `mp4` y `webm`.
100 MB alcanza para reels y testimonios bien exportados, y en un hosting compartido no
conviene más. Cada proyecto lo ajusta por entorno.

### Firmas con posición

`SIGNATURES` sigue igual y `matches_extension` suma un caso para MP4 (`ftyp` en el byte 4)
y WebM (`1A 45 DF A3` al inicio). `.mov` no entra: no es reproducible en todos los
navegadores y conviene que el editor exporte a MP4.

### Validación del video en un bloque compartido

`VideoChooserBlock(DocumentChooserBlock)` valida la extensión en `clean`. Lo usan el bloque
Video y las diapositivas, y `orion/blocks/includes/video.html` dibuja el reproductor en
ambos casos, con `preload="none"`.

### La portada es un `<picture>` debajo del video

`poster` se descarga siempre al abrir la página y no ofrece AVIF ni varias medidas. La
portada es un `<picture>` diferido, y el video va encima. Un video ambiente sin datos es
transparente, pero uno con controles se pinta como un panel oscuro. Por eso el componente
lo oculta y muestra un botón de reproducir sobre la portada; sin JavaScript el video queda
visible, con sus controles, y sin portada.

### Los videos de las diapositivas son ambiente

Unos controles chocan con el texto superpuesto en una diapositiva a todo el ancho, y un
campo más de modo complicaría el formulario. Los testimonios con sonido van en bloques
Video. Sumar el modo a la diapositiva después no rompe contenido.

### Un componente Alpine `video`

Con `IntersectionObserver` reproduce y pausa los videos ambiente, respeta
`prefers-reduced-motion` y, al salir de pantalla, pausa también los de controles. Esto
cubre además la regla de las diapositivas: una diapositiva que se va deja de intersectar,
sin coordinación con el carrusel. Sin JavaScript, el video ambiente queda en su portada
porque la plantilla no usa `autoplay`. Tiene un botón de pausa por WCAG 2.2.2, que también
aplica a un video en bucle.

### Carrusel con scroll nativo

La pista es un contenedor con `scroll-snap`; el componente Alpine `carousel` solo agrega
flechas, puntos y teclado, llamando a `scrollTo`. El gesto táctil y el modo sin JavaScript
salen gratis, y los controles arrancan ocultos, como en las pestañas.

Alternativa: Swiper o Splide agregan una dependencia y peso a cada página para lo que el
navegador ya hace.

### Sin avance automático

Obliga a un botón de pausa y a detenerse con foco y con hover para cumplir WCAG 2.2.2, y
rara vez mejora la lectura. Sumarlo después es agregar un campo.

### El `h1` de una página que abre con carrusel

`BodyPage` suma `starts_with_full_carousel`, y `page_header.html` muestra el título con
`sr-only` en ese caso. Los títulos de las diapositivas son `h2`, o `h3` si el bloque
tiene título.

Alternativa: usar como `h1` el título de la primera diapositiva. Es opcional, cambia con
el orden que elija el editor y las diapositivas son mensajes, no el tema de la página.

### Precarga

`get_leading_carousel_image` devuelve la imagen de la primera diapositiva y la usa solo la
precarga: `get_leading_hero_image` queda igual porque también define la imagen social. Para
que el bloque sepa que abre la página, `render_basic` le pasa `is_leading_block` en el
contexto. Las diapositivas a todo el ancho usan el tamaño de imagen `hero`, y las tarjetas,
uno nuevo llamado `carousel_card`.

### Una sola migración de definición

`makemigrations` genera la de `orion.pages`, que solo cambia la definición de los bloques
y no lee ni escribe páginas.

## Risks / Trade-offs

- [Nginx rechaza subidas grandes] → `client_max_body_size` en la guía. También corrige las
  imágenes de hasta 10 MB, que hoy fallan con la configuración documentada.
- [cPanel o Passenger limitan la subida o el tiempo] → sin comprobar en un hosting real;
  se documenta el límite y se prueba en la validación del deploy.
- [Disco y respaldos crecen] → límite por archivo y nota en el README.
- [Video público en una colección privada] → nota en la ayuda del campo y en el README.
- [`ORION_DOCUMENT_EXTENSIONS` definido sin `mp4`] → el documento se rechaza con el
  mensaje habitual; nota en el CHANGELOG.
- [`runserver` no atiende rangos] → en desarrollo Safari puede no reproducir; se prueba
  con Chromium y se documenta.
- [Un archivo pesado arruina la experiencia móvil] → el editor es responsable; el README
  recomienda resolución y peso.

## Migration Plan

1. `pipenv run manage migrate` aplica la migración de definición. Un proyecto con tipos de
   página propios sobre `BodyPage` ejecuta antes `makemigrations`: su campo `body` describe
   los bloques de Orion, así que recibe también una migración de definición.
2. En Nginx, sumar `client_max_body_size 120m;` y recargar.
3. Reversión: quitar los bloques exige antes sacarlos de las páginas que los usan, porque
   Wagtail dejaría de mostrar ese contenido. Los videos quedan en la biblioteca.
