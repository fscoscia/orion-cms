# Tasks

## 1. Vistas previas con contenido de ejemplo

- [x] 1.1 Generar las imágenes de ejemplo con `scripts/make_sample_images.py` en `orion/core/static/orion/samples/`; verificar que el script las regenera idénticas y que pesan menos de 100 KB en total
- [x] 1.2 `SampleImage`, `get_preview_value` de Hero, Imagen, Galería, Imagen y texto, Tarjetas y Logos, `get_preview_context` de Últimas novedades y templates que dibujan imágenes de ejemplo; verificar con `pytest tests/test_content_blocks.py` (los quince bloques con vista previa, la vista previa de cada uno responde 200 con imágenes de ejemplo donde corresponde y la biblioteca de imágenes y las páginas no cambian)

## 2. URLs sin tildes

- [x] 2.1 `WAGTAIL_ALLOW_UNICODE_SLUGS = False` en los ajustes base y slugs ASCII en `TaxonomyMixin`; verificar con `pytest tests/test_page_types.py tests/test_taxonomies.py` (slug automático de página sin tildes, etiqueta "Prevención" con `prevencion`, nombre en cirílico con slug válido, slug con tilde rechazado)

## 3. Verificación y cierre

- [x] 3.1 Verificar en el navegador las vistas previas de los bloques en el selector y el slug que arma el admin para un título con tildes
- [x] 3.2 Traducir los textos nuevos, actualizar README y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check` y `makemigrations --check`; registrar los resultados

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 255 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 255 pruebas pasaron.
- `ruff`, `pre-commit run --all-files`, `manage.py check`, `makemigrations --check` (sin
  migraciones nuevas) en ambas bases y `msgfmt --check`: sin errores.
- `scripts/make_sample_images.py` regenera las siete imágenes idénticas (mismo hash);
  pesan 48 KB en total.
- Prueba: los quince bloques son previsualizables; las vistas previas de Hero, Imagen,
  Galería, Imagen y texto, Tarjetas, Logos y Últimas novedades muestran imágenes de
  `orion/samples/` y no crean imágenes ni páginas.
- Chrome sin interfaz en el admin: el selector de bloques muestra el ícono de vista previa
  en los quince; la vista previa de la Galería se abre con las imágenes de ejemplo; al
  escribir el título "Artículo de prueba" en una página nueva, el admin arma el slug
  `articulo-de-prueba`.
- Ninguna base de desarrollo tenía slugs con tildes, así que no cambió contenido.
- Pendiente fuera del alcance: los textos de ejemplo de las vistas previas siguen en
  inglés.
