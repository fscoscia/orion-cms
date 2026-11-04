# Tasks

## 1. Anclas en los enlaces

- [x] 1.1 Crear `AnchorBlock` y sumar `anchor` a `LinkBlock` en `core/blocks/links.py`, con la validación de página y formato, y verificarlo con tests de enlace sin página, con URL externa y con formato inválido.
- [x] 1.2 Agregar el ancla en `LinkValue.href` y verificar con tests la página de inicio, una página traducida, una sin publicar y un enlace guardado sin ancla.
- [x] 1.3 Dejar vacío el `page_path` de los enlaces con ancla al armar el menú y verificar con tests un ítem y un subítem.

## 2. Ancla de los bloques

- [x] 2.1 Sumar `anchor` a `BaseContentBlock` y a sus ajustes, y verificar con tests que un bloque de proyecto lo hereda y que el campo queda en el área de ajustes.
- [x] 2.2 Validar anclas repetidas y reservadas en `ContentStreamBlock.clean` y verificar con tests que se marca el bloque afectado, también entre bloques ocultos.
- [x] 2.3 Dibujar el `id` en `render_basic` y verificar con tests un bloque visible, uno oculto y uno sin ancla.

## 3. Antetítulo

- [x] 3.1 Crear `EyebrowBlock`, sumarlo a los quince bloques con título y verificar con un test que los tienen y que Texto, Imagen y Botones no.
- [x] 3.2 Mostrarlo en `includes/title.html` y `hero.html`, y verificar con tests el HTML con y sin antetítulo, sin título y el `h1` único del Hero.
- [x] 3.3 Sumar `.orion-eyebrow` a `orion.css`, compilar con `pipenv run css-build` y comprobar en el navegador un fondo claro y uno oscuro.

## 4. Migraciones, textos y documentación

- [x] 4.1 Generar las migraciones de `orion.pages`, `orion.navigation` y `demo`, revisar que solo cambien definiciones y verificar con un test que una página y un menú existentes conservan su contenido.
- [x] 4.2 Traducir los textos nuevos al español y verificar con `compilemessages` y los tests del catálogo.
- [x] 4.3 Comprobar con un test que wagtail-localize ofrece el antetítulo y que la traducción conserva el ancla.
- [x] 4.4 Documentar antetítulo, anclas y enlaces a secciones en README, `docs/guias/crear-un-bloque.md` y CHANGELOG, con las notas para proyectos, y comprobar que el README menciona `scroll-padding-top`.

## 5. Verificación integral

- [x] 5.1 Agregar un e2e que siga un enlace de menú a una sección desde otra página, ejecutar lint, `makemigrations --check`, la suite y e2e en PostgreSQL y MySQL, y documentar los resultados.
- [x] 5.2 Comprobar en Intervita y Bolt Emprende que `makemigrations` genera solo migraciones de definición y que sus páginas siguen abriendo.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
- Reemplazar en Bolt Emprende el antetítulo, el ancla y el menú propios por los de Orion.
