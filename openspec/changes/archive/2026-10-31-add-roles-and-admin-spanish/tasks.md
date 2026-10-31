# Tasks

## 1. Roles

- [x] 1.1 `orion.editor.roles`, migración `0001_roles` (renombrar grupos, flujo y tarea; permisos de Administradores y Editores) y `orion.core.permissions` con los nombres nuevos; actualizar pruebas que usan "Editors"; verificar con `pytest tests/test_roles.py` (grupos renombrados con sus usuarios, editor no publica, administrador publica y edita datos del sitio, sin acceso a sitios, aprobación de un envío) y `migrate` hacia atrás y adelante en una base temporal
- [x] 1.2 Menú por rol con `is_site_administrator`; verificar con `pytest tests/test_editor_home.py`

## 2. Admin en español

- [x] 2.1 Catálogo `wagtail_locale` (django y djangojs) en `LOCALE_PATHS`, `missing_wagtail_translations` y su script; verificar con `pytest tests/test_admin_language.py` (no faltan frases, el catálogo no repite frases que Wagtail traduce, el catálogo de JavaScript sirve las frases nuevas)
- [x] 2.2 `LoginForm` con etiquetas traducidas en `WAGTAILADMIN_USER_LOGIN_FORM`; verificar con `pytest tests/test_admin_language.py` (login con "Contraseña")

## 3. Navegador y cierre

- [x] 3.1 Verificar en el navegador como Editor y como Administrador: envío a aprobación y aprobación, menú, pantallas del admin sin frases en inglés (login, panel, edición, regiones, imágenes)
- [x] 3.2 Actualizar README (roles, grupo por sección, regiones) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-roles-and-admin-spanish` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 302 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 302 pruebas pasaron.
- `ruff`, `pre-commit run --all-files`, `manage.py check`, `makemigrations --check` y
  `msgfmt --check`: sin errores.
- `migrate` en PostgreSQL y MySQL de desarrollo: `orion_editor.0001_roles` dejó los grupos
  "Editores" y "Administradores" y el flujo "Aprobación de administradores". En una
  SQLite temporal: reversa a `zero` (vuelven "Editors", "Moderators" y "Moderators
  approval" con sus usuarios) y vuelta a aplicar.
- `scripts/missing_wagtail_translations.py`: ninguna frase sin traducir.
- Chrome sin interfaz sobre una SQLite nueva: la editora solo puede enviar a aprobación y
  el envío se confirma en español; la administradora (grupo, no superusuario) ve la página
  pendiente en su panel, tiene Informes, Ayuda y Documentos y no llega a Sitios; en login,
  panel, explorador, edición, imágenes, fragmentos, cuenta, regiones, usuarios, datos del
  sitio, flujos, grupos e informes no aparece ninguna de las 910 frases de Wagtail que
  tienen traducción; sin errores de consola.
- Hallazgos que cambiaron la implementación:
  - En una instalación nueva, el renombre corría antes que las migraciones de Wagtail que
    dan los permisos de imágenes y documentos por nombre de grupo, y Editores y
    Administradores quedaban sin documentos; la migración depende ahora de ellas (prueba
    incluida).
  - La comparación por paquete marcaba como faltantes frases que otra app instalada ya
    traduce; se compara con lo que gettext encuentra en ejecución y se quitaron 8 entradas
    redundantes (tres pisaban traducciones de Orion, como "items").
  - "Add a locale" seguía en inglés porque `wagtail.locales` no está instalada
    (wagtail-localize la reemplaza) y su catálogo no se carga.
  - La columna de uso de las regiones estaba escrita en inglés en la plantilla de
    wagtail-localize; Orion reemplaza ese bloque.
  - El campo de contraseña del login no tenía etiqueta; `LoginForm` de Orion la traduce.
