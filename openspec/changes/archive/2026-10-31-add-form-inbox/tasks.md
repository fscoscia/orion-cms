# Tasks

## 1. Estado y notas

- [x] 1.1 `FormSubmission.status`, `SubmissionNote` y migración `orion_forms.0002`; vista de detalle (datos, adjuntos, estado, notas, marca leído al abrir) con permiso de `get_forms_for_user`; verificar con `pytest tests/test_form_inbox.py` (nuevo al llegar, leído al abrir, cambio a respondido, nota con autor y fecha, sin permiso no accede) y `makemigrations --check`

## 2. Lista y exportación

- [x] 2.1 `OrionSubmissionsListView` con columna y filtro de estado, búsqueda y enlace al detalle; exportación CSV y Excel limpia; verificar con `pytest tests/test_form_inbox.py` (filtro por estado, búsqueda por email combinada con fecha, CSV y XLSX con estado y nombre del adjunto sin HTML)

## 3. Archivos y retención

- [x] 3.1 Borrado de adjuntos al borrar envíos y comando `orion_purge_submissions` con `ORION_FORMS_RETENTION_MONTHS`; verificar con `pytest tests/test_form_inbox.py` (borrado desde la lista de Wagtail, al borrar la página, envío de 13 meses borrado con su CV, de 11 meses intacto, plazo 0 no borra, cálculo al fin de mes)

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador: lista con estados, filtro y búsqueda, detalle con nota y cambio de estado, exportación, borrado desde la lista, en escritorio y celular
- [x] 4.2 Traducir los textos nuevos; actualizar README (bandeja, retención y cron diario) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_form_inbox.py` 22 passed (nuevo al llegar, leído al abrir, cambio de
  estado, estado inválido ignorado, nota con autor y fecha, nota vacía, editores ven los
  envíos, sin permiso no, valores vacíos en blanco, columna y enlace, filtro por estado,
  búsqueda, búsqueda con fecha, CSV y XLSX limpios, borrado múltiple y en cascada con sus
  archivos, retención de 13 y 11 meses, plazo 0, cálculo de meses).
- Navegador (Chrome headless, 1280 px y 390 px) sobre la base de la prueba anterior:
  lista con estado y enlace al CV; detalle con datos, consentimiento, nota con autor,
  cambio a Respondido; filtro "Nuevo"; búsqueda de un email; CSV con estado y nombre del
  archivo sin HTML; Excel descargado; borrado múltiple de dos envíos con CV (archivos
  borrados del disco, el tercer envío intacto); detalle sin desborde en el celular.
  Hallado y corregido: los valores opcionales vacíos se mostraban como "None".
- Traducciones de `forms`: 0 sin traducir (las frases compartidas con Wagtail usan su
  traducción).
- `pipenv run test-postgres` 527 passed; `pipenv run test-mysql` 527 passed.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `orion_forms.0002_inbox` en PostgreSQL y MySQL (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-form-inbox` cuando esté aprobado.
