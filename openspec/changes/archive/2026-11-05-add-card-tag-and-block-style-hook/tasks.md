# Tasks

## 1. Etiqueta e imagen de las tarjetas

- [x] 1.1 Agregar `tag` a `CardBlock` y `image_fit` a `CardsBlock`, con ayuda, y verificar con tests de validación (etiqueta de 41 caracteres, valor por defecto del ajuste).
- [x] 1.2 Mostrar la etiqueta sobre el título y aplicar el ajuste en `cards.html`, y verificar con tests el HTML con y sin etiqueta y con `cover` y `contain`.
- [x] 1.3 Comprobar con una prueba que una página con tarjetas existentes se muestra igual tras la migración.

## 2. Gancho de estilo en la envoltura

- [x] 2.1 Agregar `data-block-style` a la envoltura en `ContentStreamBlock.render_basic` solo con un estilo que no sea el por defecto, y verificar con tests de HTML: sin estilo, con un estilo del proyecto y con un estilo que ya no existe.
- [x] 2.2 Verificar con una prueba que las clases de la envoltura y de la sección interna, y el `id` del ancla, no cambian.

## 3. Migración, textos y documentación

- [x] 3.1 Generar la migración de `orion.pages` y la del proyecto de ejemplo, y revisar que solo cambie la definición.
- [x] 3.2 Traducir los textos nuevos al español, verificar con `compilemessages` y comprobar con una prueba que wagtail-localize ofrece la etiqueta para traducir.
- [x] 3.3 Documentar el atributo en `docs/guias/crear-un-bloque.md` y el README (estilos de bloque) y actualizar el CHANGELOG.

## 4. Verificación integral

- [x] 4.1 Ejecutar `pipenv run lint`, `makemigrations --check`, la suite y e2e en PostgreSQL y MySQL, y documentar los resultados.
- [x] 4.2 Comprobar en Intervita que `makemigrations` genera solo una migración de definición.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
