# Tasks

## 1. Vista previa compartible

- [x] 1.1 Modelo `PreviewLink` y migración `orion_editor.0002_previewlink`; vista pública `_preview/<token>/` en `orion.urls` con sus headers; verificar con `pytest tests/test_shared_preview.py` (muestra el último borrador sin sesión, recarga con el cambio nuevo, headers noindex/no-store/no-referrer, `preview.js` cargado, vencido/revocado/inexistente/página borrada → 404) y `makemigrations --check`
- [x] 1.2 Pantalla de enlaces de una página (crear con 1/7/30 días, copiar, revocar) y botón "Compartir vista previa" en la cabecera; verificar con `pytest tests/test_shared_preview.py` (crear y revocar con permiso de edición; sin permiso → rechazo y nada creado; botón solo con permiso; vencimiento inválido rechazado)

## 2. Programación y calendario

- [x] 2.1 `orion.editor.scheduling` (entradas del mes y conteo de atrasados) y vista del calendario con ítem "Calendario" en el menú; verificar con `pytest tests/test_editorial_calendar.py` (publicación aprobada y baja en su día, solo páginas editables, mes inválido → actual, navegación entre meses, atrasada marcada)
- [x] 2.2 Aviso de cron detenido en el panel de inicio y en el calendario, solo para administradores; verificar con `pytest tests/test_editorial_calendar.py` (atrasada de dos horas avisa, de diez minutos no, editor sin aviso, desaparece tras `publish_scheduled`)

## 3. Lo nativo

- [x] 3.1 Pruebas de autoguardado (el editor lo activa; guardar automáticamente no publica) y de emails del flujo (envío a revisión → Administradores; rechazo → autor; enlaces con `WAGTAILADMIN_BASE_URL`); traducir lo que falte; verificar con `pytest tests/test_editorial_workflow.py tests/test_admin_language.py`

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador: crear y abrir un enlace de vista previa sin sesión, revocarlo; calendario con publicaciones y bajas, cambio de mes y aviso de atraso; autoguardado en el editor; en escritorio y celular
- [x] 4.2 Traducir los textos nuevos; actualizar README (calendario, vista previa compartible, cron de `publish_scheduled` cada 5 minutos con ejemplos para VPS y cPanel, emails del flujo, ruta `_preview/`) y CHANGELOG; marcar la Fase 2 como hecha en `docs/especificacion.md` y `CLAUDE.md`; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_shared_preview.py` 13 passed; `tests/test_editorial_calendar.py` 16
  passed; `tests/test_editorial_workflow.py` 3 passed; `tests/test_admin_language.py` 5
  passed (sin frases nativas sin traducir).
- Navegador (Chrome headless, escritorio 1280 px y celular 390 px): 17/17 comprobaciones.
  Aviso de atraso para administradores y no para editores; calendario de octubre con la
  entrada atrasada y de noviembre con publicaciones y baja, semana desde el lunes, lista
  por día en el celular sin desborde; botón "Compartir vista previa" en el menú de la
  página; enlace creado, autoguardado real del título visto desde el enlace sin sesión,
  página publicada sin cambios; revocado → 404. Corregido: botones de mes vacíos y
  estirados (ahora con texto y ancho automático).
- Traducciones: 0 sin traducir, 0 dudosas.
- `pipenv run test-postgres` 355 passed; `pipenv run test-mysql` 355 passed.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `orion_editor.0002_previewlink` en PostgreSQL y MySQL (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-editorial-workflow` cuando esté aprobado.
