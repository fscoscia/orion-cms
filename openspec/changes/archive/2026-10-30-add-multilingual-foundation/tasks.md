# Tasks

## 1. Dependencia y ajustes

- [x] 1.1 Agregar wagtail-localize a `pyproject.toml`, reinstalar con `pipenv install --dev` y verificar con `pipenv run python -c "import wagtail_localize"`
- [x] 1.2 Activar `WAGTAIL_I18N_ENABLED`, definir el catálogo `LANGUAGES` y `WAGTAIL_CONTENT_LANGUAGES`, volver a agregar `LocaleMiddleware` y sumar las apps de wagtail-localize y `orion.localization`; verificar con `pipenv run manage check` y las pruebas de ajustes existentes

## 2. Idiomas del sitio

- [x] 2.1 Crear la app `orion.localization` con `LanguageSettings` (idiomas públicos), su migración y la función que devuelve los idiomas públicos incluyendo siempre el base; verificar con pruebas de idiomas públicos y permisos en `tests/test_site_languages.py`
- [x] 2.2 Agregar el chequeo `orion.E002` (idioma base fuera del catálogo) con pruebas; verificar con `pytest tests/test_checks.py`

## 3. Rutas y redirecciones

- [x] 3.1 Rehacer `orion.urls` con `i18n_patterns(prefix_default_language=False)`, actualizar `example/example/urls.py` y el chequeo `orion.E003`; verificar con `pytest tests/test_routing.py` (incluidos los escenarios de idioma por URL)
- [x] 3.2 Implementar el middleware de redirecciones (idioma no público, traducción faltante, inicio sin publicar) con pruebas; verificar con `pytest tests/test_localized_routing.py`

## 4. Selector, hreflang y traducción

- [x] 4.1 Implementar `{% language_switcher %}` y `{% hreflang_links %}`, incluirlos en `orion/base.html` y probarlos; verificar con `pytest tests/test_localized_routing.py`
- [x] 4.2 Probar la traducción con wagtail-localize: crear una traducción, editar el original, sincronizar y ver textos pendientes sin cambiar lo publicado; verificar con `pytest tests/test_content_translation.py`
- [x] 4.3 Traducir al español los textos nuevos de Orion y compilar los `.mo`; verificar que el admin muestra "Idiomas" con `LANGUAGE_CODE=es`

## 5. Documentación y verificación

- [x] 5.1 Actualizar README (rutas sumadas en lugar de `include`, cómo agregar y publicar un idioma), `.env.example` si corresponde y CHANGELOG; verificar que el ejemplo del README coincide con `example/example/urls.py`
- [x] 5.2 Ejecutar la suite en PostgreSQL y MySQL, `ruff check`, `ruff format --check`, `manage.py check` y `migrate` en ambas bases, y una prueba manual con `runserver` de `/`, `/en/` y el admin de idiomas; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-multilingual-foundation` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 94 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 94 pruebas pasaron.
- `ruff check`, `ruff format --check`, `makemigrations --check` y pre-commit sobre los
  archivos modificados: sin errores.
- `manage.py check` y `migrate` en PostgreSQL y MySQL: sin errores (en MySQL sigue el aviso
  conocido `models.W036` de Wagtail).
- Recorrido con el cliente de pruebas sobre la base de desarrollo, dentro de una transacción
  revertida: `/` 200; `/en/` con `en` no público 302 a `/`; `/en/` público 200 con
  `lang="en"`, `hreflang` con `x-default` y selector; `/no-existe/` 404; `/en/no-existe/`
  302 a `/en/`; admin de idiomas y de "Idiomas" 200 con textos en español. La base quedó
  sin cambios.
- `runserver`: `/health/`, `/` y `/admin/login/` 200; `/en/` 302 a `/` (sin inglés).
- Hallazgos que cambiaron la implementación: Wagtail sirve contenido del idioma base bajo un
  prefijo cuando falta la traducción del inicio (resuelto con `before_serve_page`), y
  wagtail-localize exige su propio permiso de traducir en lugar del permiso de edición (la
  spec se ajustó a ese comportamiento nativo).
