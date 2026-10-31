# Tasks

## 1. Enlaces

- [x] 1.1 Implementar `LinkBlock` en `orion.core.blocks` (un solo destino, rechazo de URLs del propio sitio, `mailto:`/`tel:` normalizados, página en el idioma activo, pestaña nueva con `rel` seguro) con pruebas; verificar con `pytest tests/test_content_links.py`

## 2. Datos y textos del sitio

- [x] 2.1 Crear la app `orion.site_data` con `SiteSettings` (logos, contacto, redes) y `SiteTexts` (traducible, uno por idioma), sus migraciones y la de permisos; verificar con `pytest tests/test_site_data.py` (permisos, unicidad, respaldo al idioma base, red con URL inválida)
- [x] 2.2 Agregar `{% get_site_texts %}` y el procesador de contexto de ajustes; verificar con las pruebas de `tests/test_site_data.py`

## 3. Menús

- [x] 3.1 Crear la app `orion.navigation` con `Menu` (ubicación única por idioma, dos niveles), su migración y la de permisos; verificar con `pytest tests/test_site_navigation.py`
- [x] 3.2 Implementar `{% site_menu %}` con ítems visibles, grupos sin destino, ítem actual con `aria-current` y respaldo al menú del idioma base; verificar con `pytest tests/test_site_navigation.py`

## 4. Diseño base

- [x] 4.1 Agregar django-tailwind-cli 4.8.1 a las dependencias de desarrollo, configurarlo en el proyecto de ejemplo con Tailwind 4.3.3 y crear `orion.css` fuente con el tema en variables; verificar con `pipenv run css-build`
- [x] 4.2 Incluir `@alpinejs/csp` 3.17.4 con su licencia y `orion/js/orion.js` con el componente de navegación; verificar que los archivos se sirven con `runserver`
- [x] 4.3 Reescribir `orion/base.html` con enlace para saltar al contenido, encabezado y pie, compilar el CSS y probar la estructura, el respaldo sin logo y la carga de estilos; verificar con `pytest tests/test_site_layout.py`
- [x] 4.4 Verificar en el navegador el menú en celular (abrir, Escape, foco, `aria-expanded`), la navegación sin JavaScript y el funcionamiento bajo una política CSP estricta de prueba

## 5. Documentación y verificación

- [x] 5.1 Traducir al español los textos nuevos, actualizar README (datos del sitio, menús, cómo cambiar colores y fuentes con variables, cómo recompilar el CSS) y CHANGELOG; verificar que los comandos del README se ejecutan como están escritos
- [x] 5.2 Ejecutar la suite en PostgreSQL y MySQL, `ruff`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-site-data-navigation-layout` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 132 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 132 pruebas pasaron.
- `ruff check`, `ruff format --check`, `pre-commit run --all-files`, `manage.py check` y
  `makemigrations --check`: sin errores.
- `migrate` en PostgreSQL y MySQL: sin errores. En una SQLite temporal: reversión de
  `orion_navigation` y `orion_site_data` a `zero` (quita los permisos de *Editors* y
  *Moderators*) y vuelta a aplicar (los repone).
- `pipenv run css-build` con Tailwind 4.3.3: el CSS compilado coincide con el versionado.
  `css-watch` compila al arrancar (sin minificar; el README pide `css-build` antes de
  versionar).
- Alpine incluido idéntico a `dist/cdn.min.js` de `@alpinejs/csp` 3.17.4 en npm (sha512
  del paquete verificado). `runserver` sirve `orion.css`, `orion.js` y Alpine con 200.
- Chrome sin interfaz (protocolo DevTools) sobre una SQLite temporal con menús y datos,
  servida con `Content-Security-Policy: default-src 'self'; script-src 'self';
  style-src 'self'; …`: en 390 px el panel arranca cerrado con `aria-expanded="false"`,
  el primer Tab enfoca el enlace "Saltar al contenido", el botón abre el panel, Escape lo
  cierra y devuelve el foco al botón; el submenú informa `aria-expanded` y Escape cierra
  solo el submenú; en 1280 px el botón se oculta, el ancestro actual se marca y un clic
  afuera cierra el submenú; sin JavaScript los enlaces del menú y del submenú quedan
  visibles. Sin violaciones de CSP ni errores de consola (salvo `/favicon.ico` 404, fuera
  del alcance). Redefinir `--color-primary-700` y `--color-primary-900` en una hoja
  propia cambia el encabezado y el pie sin recompilar.
- Hallazgos que cambiaron la implementación:
  - En los templates, `link.url` y `link.page` devolvían los campos crudos del bloque (los
    templates buscan primero claves del diccionario), así que los enlaces a páginas salían
    con `href="None"`. Las propiedades resueltas pasaron a llamarse `href` y `linked_page`
    (design actualizado); los campos y los datos guardados no cambian.
  - Escape dentro de un submenú abierto cerraba también el panel del celular; ahora cierra
    una capa por vez.
  - El texto de respaldo "Home" del logo no estaba marcado para traducción.
  - El README indicaba "Configuración" para el menú de ajustes; en el admin en español es
    "Propiedades" (y "Locales" es "Regiones").
