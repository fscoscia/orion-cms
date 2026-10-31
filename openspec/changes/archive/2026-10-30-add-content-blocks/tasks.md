# Tasks

## 1. Base de los bloques

- [x] 1.1 Convertir `orion/core/blocks.py` en el paquete `orion.core.blocks` (`links.py` con `LinkBlock` sin cambios y `__init__.py` que reexporta); verificar con `pytest tests/test_content_links.py tests/test_site_navigation.py` y `makemigrations --check` sin cambios
- [x] 1.2 Crear la app `demo` del proyecto de ejemplo con `DemoPage` (cuerpo `ContentStreamBlock`, por ahora vacío salvo Texto) y su migración; verificar con `pipenv run manage makemigrations --check` y una prueba que renderiza una `DemoPage`
- [x] 1.3 Implementar `BaseContentBlock` (`is_visible` y `style` con opciones de `ORION_BLOCK_STYLES`), `ContentStreamBlock` (omite ocultos y pasa `block_id`), `HighlightedTitleBlock` (solo negrita, un párrafo) con su filtro `highlighted_title`, `ButtonBlock` y el bloque Texto con texto enriquecido acotado; verificar con `pytest tests/test_content_blocks.py` (bloque oculto, estilo declarado por el proyecto que llega al template, campo oculto con una sola opción, estilo quitado de los ajustes que cae en el por defecto sin error, `makemigrations --check` sin cambios al modificar `ORION_BLOCK_STYLES`, título resaltado, título con dos párrafos rechazado, botón a página despublicada, formatos del texto)

## 2. Bloques

- [x] 2.1 Hero, Imagen, Galería e Imagen + texto con `ImageBlock` y `{% srcset_image %}` WebP (Hero sin carga diferida y con `h1`); verificar con `pytest tests/test_content_blocks.py` (imagen sin alt rechazada, decorativa con `alt=""`, `srcset`/`width`/`height`/`loading`, jerarquía `h1`/`h2`)
- [x] 2.2 Tarjetas, Llamada a la acción, Logos y Botones; verificar con `pytest tests/test_content_blocks.py` (columnas, enlaces con `rel` seguro en pestaña nueva, logo con nombre accesible, lista de botones vacía sin marcado)
- [x] 2.3 Datos de contacto (datos del sitio elegidos con sus íconos fijos en `orion/includes/icon.html`, y datos extra con etiqueta y texto); verificar con `pytest tests/test_content_blocks.py` (dato elegido no cargado omitido, cambio en los datos del sitio reflejado, dato extra)
- [x] 2.4 Acordeón con `<details>`, Pestañas (componente `tabs`) y Cifras (componente `counter`) en `orion/js/orion.js`; verificar con `pytest tests/test_content_blocks.py` (marcado ARIA, ids únicos por bloque, número final en el HTML)
- [x] 2.5 Completar `ContentStreamBlock` con los trece bloques, `icon`, `description` y `preview_value` en cada uno, y el template de vista previa que carga el CSS y los scripts de Orion; verificar con `pytest tests/test_content_blocks.py` (los trece en el cuerpo, cada uno con descripción y vista previa que responde 200 en el admin)

## 3. Diseño y verificación en el navegador

- [x] 3.1 Estilos base de los bloques, `@plugin "@tailwindcss/typography"` con los colores de `prose` ligados a las variables del tema y sus `h2`/`h3` en `--font-display`, y `.orion-title` en `orion.css`; compilar el CSS; verificar con `pipenv run css-build` (sin instalar nada) y `pytest tests/test_site_layout.py`
- [x] 3.2 Verificar en el navegador una `DemoPage` con los trece bloques bajo una CSP estricta: pestañas con flechas, Inicio y Fin; acordeón con teclado; cifras con y sin movimiento reducido; sin JavaScript (paneles visibles, cifras finales); sin violaciones de CSP; cambio de color principal y de acento y de `--font-sans`/`--font-display` por variables (el texto enriquecido toma la fuente del sitio y sus subtítulos la de títulos); un estilo declarado en `ORION_BLOCK_STYLES` elegido en el admin; celular y escritorio

## 4. Traducción, documentación y cierre

- [x] 4.1 Verificar la traducción: segmentos extraídos por wagtail-localize de una página con todos los bloques y botón a página traducida en `/en/`; verificar con `pytest tests/test_content_blocks.py`
- [x] 4.2 Traducir al español los textos nuevos, actualizar README (bloques disponibles, cómo usar `ContentStreamBlock` o un subconjunto, `include_block` y bloques ocultos, cómo declarar estilos con `ORION_BLOCK_STYLES` y usarlos en el template, cómo reemplazar el template de un bloque, fuentes propias) y CHANGELOG; verificar que `msgfmt --check` pasa y que los ejemplos del README funcionan como están escritos
- [x] 4.3 Ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-content-blocks` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 178 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 178 pruebas pasaron.
- `ruff check`, `ruff format --check`, `pre-commit run --all-files`, `manage.py check` y
  `makemigrations --check` (también con `ORION_BLOCK_STYLES` modificado): sin errores.
- `migrate` en PostgreSQL y MySQL: aplica `demo.0001_initial` sin errores; Orion no suma
  migraciones.
- `pipenv run css-build` compila con el plugin de tipografía incluido en el binario de
  Tailwind 4.3.3, sin instalar nada.
- `msgfmt --check` sin errores; las etiquetas y descripciones de los bloques salen en
  español en el admin.
- Chrome sin interfaz (protocolo DevTools) sobre una SQLite temporal con una `DemoPage` de
  los trece bloques, servida con `Content-Security-Policy: default-src 'self';
  script-src 'self'; style-src 'self'; …`: bloque oculto omitido; estilo `split` del Hero
  declarado en `ORION_BLOCK_STYLES` en el HTML; un solo `h1`; pestañas con flechas
  (incluida la vuelta), Inicio, Fin, clic y `tabindex` itinerante; acordeón que abre y
  cierra con Enter; cifras en 0 fuera de pantalla que llegan a 41, 186 y 98 al aparecer, y
  finales de entrada con movimiento reducido; imágenes WebP con `srcset`, medidas y carga
  diferida salvo el Hero; `rel="noopener noreferrer"` en pestaña nueva; `prose` aplicado;
  redefinir `--color-primary-700`, `--color-accent-600`, `--font-sans` y `--font-display`
  cambia botones, resaltados, texto enriquecido y títulos; sin desbordes a 390 px; sin
  JavaScript, todas las pestañas con su título y cifras finales; sin violaciones de CSP ni
  errores de consola en el sitio. En el admin, "Estilo" se ve como lista solo en el Hero y
  su fila queda oculta en los demás; guardar la página conserva el estilo y "Visible".
- Hallazgos que cambiaron la implementación:
  - Wagtail 7.4 calcula el `form_layout` del `StructBlock` en su constructor: los campos
    agregados después no aparecían en el editor. "Estilo" y "Visible" se pasan al
    constructor y van al área de ajustes plegable del bloque (prueba de regresión
    incluida).
  - El adaptador de `Select` del editor fallaba con el campo oculto; `BlockStyleSelect`
    usa el adaptador genérico de widgets.
  - El hook `insert_editor_css` ya no existe en Wagtail 7.4; se usa
    `insert_global_admin_css`.
  - En la variante CSP de Alpine, un método invocado desde un elemento hijo recibe ese
    elemento como `$el`; las pestañas no respondían hasta usar `$root`.
  - wagtail-localize ignora las listas guardadas en el formato viejo (sin ids). El admin
    siempre guarda el formato nuevo; las pruebas validan el cuerpo como el admin.
  - Con `TEMPLATES[0]["DIRS"]` vacío, un template del proyecto no reemplaza al de Orion;
    el README ahora pide declarar esa carpeta (afectaba también al encabezado y el pie).
  - pre-commit agregaba un salto de línea al CSS compilado que cada compilación quitaba; se
    excluyen el CSS compilado y `vendor/` de esos dos hooks.
