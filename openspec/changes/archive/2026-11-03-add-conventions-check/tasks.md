# Tasks

## 1. Descubrimiento

- [x] 1.1 `orion.core.conventions`: listar los templates y los archivos `.po` de las apps
  propias del proyecto (no de sus dependencias: se filtra por si la app vive dentro de
  `site-packages`, ver design.md) más `settings.TEMPLATES[0]["DIRS"]` y
  `settings.LOCALE_PATHS`; verificar con `pytest tests/test_conventions.py` (encuentra
  templates y `.po` de las apps propias, sin duplicar lo que está en dos apps, y sin
  traer los de Django/Wagtail/django-axes)

## 2. Texto fijo e imágenes sin alt

- [x] 2.1 Enmascarado del template sin etiquetas de Django (`tag_re`, reemplazo por
  espacios manteniendo líneas, blanqueando el tramo completo de
  `blocktrans`/`blocktranslate`); verificar con `pytest tests/test_conventions.py`
  (números de línea exactos tras el reemplazo)
- [x] 2.2 Texto fijo con `html.parser.HTMLParser` sobre esa reconstrucción, sin contar
  `<script>`, `<style>`, texto sin ninguna letra (separadores) ni lo que esté dentro de
  `blocktrans`/`blocktranslate`; verificar con `pytest tests/test_conventions.py` (texto
  sin marcar reportado con archivo y línea; el mismo texto dentro de `{% blocktrans %}`
  o pasado a `{% trans %}` no se reporta; texto dentro de `<script>` no se reporta)
- [x] 2.3 Imágenes sin `alt`: `<img>` sin el atributo (vía el mismo `HTMLParser`) y
  llamados a `{% responsive_image %}` sin `alt` o con `alt=""` (sobre las etiquetas que
  encuentra `tag_re`); verificar con `pytest tests/test_conventions.py` (cada caso
  reportado, y no reportado cuando `alt` tiene un valor, literal o variable)

## 3. Traducciones faltantes

- [x] 3.1 Parser de `.po` que concatena continuaciones de `msgid`/`msgstr`, salta
  `msgctxt` y formas plurales, y detecta `msgstr` vacío y la marca `#, fuzzy`,
  descartando el encabezado del archivo; verificar con `pytest tests/test_conventions.py`
  (entrada vacía, entrada `fuzzy`, entrada completa, encabezado ignorado,
  `msgid`/`msgstr` multilínea)

## 4. Comando y cierre

- [x] 4.1 `manage.py orion_check_conventions`: corre los tres chequeos, imprime los
  hallazgos agrupados por categoría con archivo y línea, un resumen al final, y siempre
  termina con código de salida 0; verificar con
  `pytest tests/test_conventions.py` (sin hallazgos lo informa; con hallazgos de los tres
  tipos los lista y termina en 0) y corriéndolo sobre el propio Orion
  (`pipenv run manage orion_check_conventions`), registrando cuántos hallazgos reales
  deja (deuda conocida, sin corregir en este cambio)
- [x] 4.2 README (qué hace el comando, que solo reporta, que no hay `--strict` todavía);
  CHANGELOG; traducir los textos nuevos; ejecutar la suite en PostgreSQL y MySQL, `ruff`,
  pre-commit, `manage.py check`, `makemigrations --check`; registrar los resultados

## Resultados de verificación (2026-11-03)

- `pytest tests/test_conventions.py`: 25 passed, tanto en PostgreSQL como en MySQL —
  enmascarado de etiquetas con líneas exactas, `blocktrans`/`blocktranslate` blanqueado
  completo, texto fijo reportado y no reportado cuando corresponde, texto dentro de
  `<script>` ignorado, `<img>` y `{% responsive_image %}` sin `alt` reportados (literal,
  variable y `alt=""`), parser de `.po` (vacío, `fuzzy`, completo, encabezado,
  multilínea), descubrimiento de templates y catálogos sin traer los de Django/Wagtail,
  comando sin hallazgos y con hallazgos, siempre en 0.
- Al implementar: `apps.get_app_configs()` sin filtrar traía las apps de Django, Wagtail,
  django-axes y cada dependencia (un solo paquete, `wagtail_localize`, suma traducciones
  en más de ochenta idiomas); se filtró por si la app vive dentro de `site-packages` (ver
  design.md). El parser de `.po` entraba en un bucle infinito con una entrada `msgctxt`
  (usada por Wagtail en sus propios catálogos); se agregó el salto de esa línea. El texto
  fijo reportaba separadores sueltos (`·`, `*`, `:`); se exige al menos una letra.
- Corrida real sobre Orion (`pipenv run manage orion_check_conventions`): 12 hallazgos,
  ninguno de traducciones (una revisión manual previa con `grep` sugería deuda de
  traducciones que no existe: confundía la continuación multilínea de `.po` con una
  traducción vacía). Quedan sin corregir, como deuda conocida: "WhatsApp" y "login" sin
  marcar en tres templates, una imagen sin `alt` en `header.html`, y ocho nombres de
  variables de entorno mostrados en `integrations.html` (falso positivo esperado: son
  identificadores, no texto a traducir).
- `pipenv run test-postgres`: 737 passed. `pipenv run test-mysql`: 736 passed, 1 skipped
  (prueba de stemming de PostgreSQL de `test_site_search.py`, preexistente).
- `ruff check` y `ruff format --check`: sin errores. `pre-commit` sobre los archivos
  nuevos y modificados: sin errores. `manage.py check`: sin problemas.
  `makemigrations --check --dry-run`: sin cambios.
- Traducciones: la salida del comando es texto de consola en inglés, igual que el resto
  de los comandos de gestión de Orion (no usan `gettext`); no hay nada para traducir.
