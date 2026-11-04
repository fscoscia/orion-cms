# Tasks

## 1. Subida de videos

- [x] 1.1 Sumar `mp4` y `webm` a `DOCUMENT_EXTENSIONS` y `ORION_VIDEO_MAX_UPLOAD_MB` en `settings/base.py`, y verificarlo con un test de la configuración.
- [x] 1.2 Reconocer MP4 y WebM en `core/uploads.py` y verificar con tests que acepta archivos reales y rechaza un ejecutable renombrado.
- [x] 1.3 Aplicar el límite de video en `DocumentForm` y verificar con tests un MP4 dentro del límite, uno por encima y un PDF de 30 MB.
- [x] 1.4 Sumar `client_max_body_size` a la guía de Nginx del README, documentar el límite, el peso recomendado y la privacidad por colección, y comprobar que el README menciona `ORION_VIDEO_MAX_UPLOAD_MB`.

## 2. Bloque Video

- [x] 2.1 Crear `VideoChooserBlock` y verificar con un test que rechaza un PDF con un mensaje claro.
- [x] 2.2 Crear `VideoBlock` (video, portada, título, pie, modo, formato), registrarlo en `ContentStreamBlock` con ayuda y vista previa, y verificarlo con tests de validación y de vista previa sin video.
- [x] 2.3 Crear `orion/blocks/video.html` y `includes/video.html` con `preload="none"`, la portada como `<picture>` y `file.url`, y verificar con tests el HTML de ambos modos y formatos, también bajo `SCRIPT_NAME`.
- [x] 2.4 Agregar el componente Alpine `video` a `orion.js` y verificar en e2e que un video ambiente se pausa fuera de pantalla, respeta `prefers-reduced-motion` y la pausa del visitante, que uno con controles arranca desde su portada, y que no hay errores de CSP.

## 3. Bloque Carrusel

- [x] 3.1 Crear `CarouselSlideBlock` y `CarouselBlock` (2 a 12 diapositivas, título, disposición), registrarlo con ayuda y vista previa, y verificarlo con tests de validación.
- [x] 3.2 Crear `orion/blocks/carousel.html` con `scroll-snap`, títulos de nivel correcto y controles ocultos sin JavaScript, sumar el tamaño `carousel_card`, y verificarlo con tests del HTML.
- [x] 3.3 Agregar el componente Alpine `carousel` a `orion.js` y verificar en e2e flechas, puntos, teclado, botón deshabilitado al final, pausa del video al cambiar de diapositiva y recorrido sin JavaScript.
- [x] 3.4 Sumar los estilos a `core/static_src/orion.css`, compilar con `pipenv run css-build` y comprobar en el navegador ambas disposiciones en escritorio y móvil.

## 4. Carrusel al abrir la página

- [x] 4.1 Agregar `starts_with_full_carousel` y usarlo en `page_header.html`, y verificar con tests que hay un único `h1` en las cuatro combinaciones de la spec.
- [x] 4.2 Pasar `is_leading_block` desde `render_basic`, extender `get_leading_hero_image` y verificar con tests la prioridad, la precarga y la carga diferida del resto.

## 5. Migración, textos y documentación

- [x] 5.1 Generar la migración de `orion.pages`, revisar que solo cambie la definición y verificar con un test que una página existente conserva su cuerpo.
- [x] 5.2 Traducir los textos nuevos al español y verificar con `compilemessages` y una prueba del admin en español.
- [x] 5.3 Comprobar con una prueba que wagtail-localize ofrece los textos de ambos bloques para traducir.
- [x] 5.4 Actualizar README ("diecisiete bloques"), `docs/guias/crear-un-bloque.md`, CHANGELOG y la tabla de videos de `docs/especificacion.md`, y comprobar que no queda "quince bloques".

## 6. Verificación integral

- [x] 6.1 Ejecutar `pipenv run lint`, `makemigrations --check`, la suite y e2e en PostgreSQL y MySQL, y documentar los resultados.
- [x] 6.2 Comprobar en Intervita que `makemigrations` genera solo una migración de definición y que ambos bloques se cargan y publican desde el admin.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
