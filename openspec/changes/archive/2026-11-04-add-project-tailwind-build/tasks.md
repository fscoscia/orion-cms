## 1. Archivo fuente de Tailwind del proyecto

- [x] 1.1 Crear `src/orion/project_template/static_src/project.css` con
  `@import "tailwindcss" source(none);`, `@import "__ORION_STATIC_SRC__/orion.css";` y
  `@source` apuntando a `../home` y `../templates`; verificar con `ls` que queda junto a
  `home/` y `templates/` en la raíz de la plantilla.
- [x] 1.2 En `src/orion/bin.py`, agregar la resolución de `__ORION_STATIC_SRC__` (ruta
  absoluta a `orion.core.static_src`, usando el mismo mecanismo que ya resuelve
  `__ORION_VERSION__` en el `Pipfile`) y reemplazarla en el archivo generado; verificar
  corriendo `orion-start` sobre un directorio temporal y leyendo el `@import` resultante
  (debe ser una ruta absoluta existente, no el placeholder).

## 2. Ajustes y dependencias generados

- [x] 2.1 En `src/orion/project_template/project_name/settings.py-tpl`, agregar
  `STATICFILES_DIRS`, `INSTALLED_APPS += ["django_tailwind_cli"]`
  y los ajustes `TAILWIND_CLI_VERSION`, `TAILWIND_CLI_SRC_CSS` (apuntando a
  `BASE_DIR / "static_src" / "project.css"`), `TAILWIND_CLI_DIST_CSS` (`"project/css/project.css"`)
  y `TAILWIND_CLI_PATH` (`BASE_DIR / ".tailwind"`); verificar que `manage.py check` sigue
  sin errores sobre un proyecto generado. Ajuste sobre el diseño: `STATICFILES_DIRS`
  usa `BASE_DIR / "assets"`, no `"static"` (ya es `STATIC_ROOT`; Django no permite que
  coincidan — error real de `django-tailwind-cli` al probarlo). El directorio `assets/`
  se crea en `bin.py` después de copiar la plantilla (no se empaqueta un placeholder
  vacío: colisionaría con el propio `.gitignore` de la plantilla, que también ignora
  `assets/` dentro del repositorio de Orion).
- [x] 2.2 En `src/orion/project_template/Pipfile`, agregar `django-tailwind-cli` con la
  misma versión que fija el `Pipfile` de este repositorio, y los scripts `css-build`
  (`python manage.py tailwind build`) y `css-watch` (`python manage.py tailwind watch`);
  verificar leyendo el `Pipfile` generado.
- [x] 2.3 Agregar `.tailwind/` al `.gitignore` de la plantilla
  (`src/orion/project_template/.gitignore`, agregado en `add-project-template-gitignore`);
  verificar con `grep`. También se agregó `assets/` (la salida compilada de Tailwind,
  un artefacto de build como `static/`, no algo para versionar).

## 3. Template que carga el CSS propio

- [x] 3.1 Crear `src/orion/project_template/templates/orion/base.html` que extiende
  `orion/base.html` y agrega, en `{% block extra_css %}`, el `<link>` a
  `project/css/project.css` vía `{% static %}`; verificar con `ls` que queda junto a
  `templates/README.md`. Verificado sirviendo un proyecto generado de verdad: las dos
  hojas de estilo (`orion/css/orion.css` y `project/css/project.css`) aparecen en el
  HTML; el patrón "extender un template del mismo nombre" de Django (`DIRS` antes que
  `APP_DIRS`) resuelve sin recursión.

## 4. Pruebas

- [x] 4.1 En `tests/test_project_template.py`, extender `test_scaffolds_a_new_project`
  (o agregar un caso dedicado) para verificar que el proyecto generado incluye
  `static_src/project.css`, `templates/orion/base.html` y que el `Pipfile` tiene
  `django-tailwind-cli`; verificar con `pipenv run test -k test_project_template`.
- [x] 4.2 Agregar un caso que corra `python manage.py tailwind build` sobre un proyecto
  generado en un directorio temporal (con el entorno virtual de la propia suite, que ya
  tiene `django-tailwind-cli` instalado vía el `Pipfile` de Orion) y verifique que el
  archivo de salida (`static/project/css/project.css`) existe y no está vacío, y que el
  CSS compilado de Orion (`src/orion/core/static/orion/css/orion.css`) no cambió;
  verificar con `pipenv run test -k test_project_template`. Salida real:
  `assets/project/css/project.css` (ajustado del diseño por la colisión con
  `STATIC_ROOT`, ver tarea 2.1). Las 9 pruebas de `test_project_template.py` pasan.
- [x] 4.3 Correr la suite completa en PostgreSQL (`pipenv run test-postgres`) y en
  MySQL (`pipenv run test-mysql`), y verificar que ambas terminan en verde. PostgreSQL:
  742 passed, 5 deselected. MySQL: 741 passed, 1 skipped, 5 deselected.
- [x] 4.4 Correr `pipenv run lint` y verificar que no reporta hallazgos. "All checks
  passed!"

## 5. Guía corregida

- [x] 5.1 En `docs/guias/crear-un-tipo-de-pagina.md`, quitar `class="orion-lead"` del
  ejemplo (no es una clase real de Orion); dejar el párrafo de bajada sin clase o con
  una nota de que el estilo lo define el proyecto. Verificar leyendo el archivo.
- [x] 5.2 Encontrado al verificar visualmente sobre Intervita (tarea 6.1): el ejemplo de
  la misma guía no envolvía el contenido en ningún contenedor (`mx-auto max-w-* px-4`) ni
  agregaba tamaño/peso al `<h1>` — `orion-title` por sí sola solo define la tipografía,
  igual que en `orion.css`. Corregido para que el ejemplo siga el mismo patrón que
  `orion/pages/includes/page_header.html` (el que usan los tipos de página de Orion):
  contenedor `mx-auto max-w-6xl px-4 pt-12 md:pt-16`, `text-4xl font-bold tracking-tight
  md:text-5xl` en el `<h1>`, y la bajada con `mt-4 max-w-3xl text-lg text-ink-muted`.
  Verificar leyendo el archivo.
- [x] 5.3 Mismo hallazgo en `docs/guias/crear-un-bloque.md`: el ejemplo de
  `testimonial.html` tampoco envolvía el bloque en `mx-auto max-w-* px-4 py-*` — todos
  los bloques reales de Orion lo hacen (`text.html`, `call_to_action.html`…).
  Corregido con `mx-auto max-w-3xl px-4 py-10` en el elemento de más afuera. Verificar
  leyendo el archivo.

## 6. Verificación manual sobre Intervita

- [x] 6.1 Sobre el proyecto Intervita (`/Users/fscoscia/Proyectos/intervita`), aplicar
  a mano los mismos cambios (o regenerar con `orion-start` en un directorio aparte y
  copiar las piezas nuevas), instalar `django-tailwind-cli`, correr
  `python manage.py tailwind build` y verificar visualmente que
  `/servicio-de-prueba/` (la página creada en `validate-intervita-site`) se ve con
  estilos. `manage.py check` sin errores; compiló `assets/project/css/project.css`
  (36 KB); el HTML de `/servicio-de-prueba/` carga ambas hojas de estilo
  (`orion/css/orion.css` y `project/css/project.css`), servidas con 200. La primera
  pasada seguía viéndose sin diseño por los hallazgos de las tareas 5.2 y 5.3 (los dos
  templates, de página y de bloque, sin contenedor ni tipografía): corregidos ambos
  templates en Intervita con el mismo patrón que las guías ya corregidas, recompilado,
  y confirmado en el HTML servido que el `<header>` y el `<section>` del testimonio
  tienen sus contenedores y clases de tamaño/peso.
