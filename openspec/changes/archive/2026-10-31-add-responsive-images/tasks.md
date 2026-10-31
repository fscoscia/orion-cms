# Tasks

## 1. Componente de imagen

- [x] 1.1 `orion.core.images` (medidas, `ORION_IMAGE_SIZES`, error por nombre inexistente) y etiqueta `{% responsive_image %}` (vacía, de ejemplo, SVG, AVIF+WebP, principal); verificar con `pytest tests/test_responsive_images.py` (fuentes AVIF y WebP, ancho y alto, lazy, principal con fetchpriority, medida de proyecto, medida inexistente)
- [x] 1.2 Pasar todas las plantillas de Orion a la etiqueta y agregar `{% main_image_preload %}` en `orion/base.html`; actualizar las pruebas de bloques que esperan WebP; verificar con `pytest tests/test_responsive_images.py tests/test_content_blocks.py tests/test_page_types.py` (galería con `<picture>`, Hero sin lazy y precargado, decorativa con alt vacío, artículo y tarjeta de artículo) y la suite completa

## 2. Biblioteca

- [x] 2.1 Ajustes de formatos y peso; reducción del original a 2048 px; generación de recortes al guardar (hilo y modo síncrono) y comando `orion_generate_renditions`; verificar con `pytest tests/test_image_library.py` (6000×4000 → 2048×1365 con ancho, alto y peso actualizados, formato no permitido rechazado, recortes creados al subir, comando informa cuántos creó)
- [x] 2.2 SVG: validador en el formulario de imágenes y limpieza al guardar con `defusedxml` (declarado en `pyproject.toml`); verificar con `pytest tests/test_image_library.py` (script, `onload`, `foreignObject`, `javascript:` y href externo quitados; dibujo conservado; archivo inválido rechazado en el admin; SVG mostrado como SVG en un bloque)
- [x] 2.3 Comando `orion_unused_images`; verificar con `pytest tests/test_image_library.py` (huérfana listada; usada en un bloque, en un artículo y en el logo del sitio no listadas; no borra nada)

## 3. Navegador y cierre

- [x] 3.1 Verificar en el navegador: subir una foto grande y un SVG con script desde el admin, ver la portada con Hero (AVIF cargado, precarga sin doble descarga, sin lazy), galería y tarjetas diferidas, en escritorio y celular; medir el peso de la portada antes y después
- [x] 3.2 Traducir los textos nuevos; actualizar README (medidas y `ORION_IMAGE_SIZES`, etiqueta, comandos, límites, SVG) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check` y `makemigrations --check`; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_responsive_images.py` 7 passed; `tests/test_image_library.py` 15
  passed; `tests/test_content_blocks.py` y `tests/test_articles.py` con las pruebas
  nuevas de `<picture>`, Hero priorizado y precargado, artículo y tarjeta.
- Navegador (Chrome headless, 1280 px y 390 px): subida desde el admin de una foto de
  6000 × 4000 (2,9 MB) → 2048 × 1365 (147 KB); SVG con `<script>` y `onload` guardado
  limpio; recortes generados en segundo plano (28 filtros por foto). Portada de prueba:
  Hero en AVIF con `fetchpriority="high"`, precargado y descargado una sola vez; resto de
  las imágenes con `loading="lazy"`; logo SVG servido como SVG; sin desborde ni errores
  de JavaScript. Peso de las 8 imágenes: AVIF 26 KB contra 38 KB en WebP en escritorio
  (31 % menos) y 22 KB contra 32 KB en celular (31 % menos). Chrome descarga las
  imágenes diferidas cercanas a la pantalla (página corta): comportamiento normal.
- Traducciones: 0 sin traducir, 0 dudosas.
- `pipenv run test-postgres` 380 passed; `pipenv run test-mysql` 380 passed.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases (el cambio no tiene
  migraciones).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-responsive-images` cuando esté aprobado.
