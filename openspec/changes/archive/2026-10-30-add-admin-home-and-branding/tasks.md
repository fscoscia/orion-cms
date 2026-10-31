# Tasks

## 1. Base

- [x] 1.1 Crear la app `orion.editor` en `ORION_APPS`; verificar con `pipenv run manage check`

## 2. Panel, atajos y barra

- [x] 2.1 `WelcomePanel` con acciones según permisos y cambios sin publicar; quitar contadores y paneles de versión; verificar con `pytest tests/test_editor_home.py` (acciones de un editor y de un superusuario, sin listados no hay "escribir un artículo", borrador aparece en cambios sin publicar, paneles de Wagtail quitados por nombre existentes)
- [x] 2.2 Vista "nuevo artículo" y atajos del menú ("Nuevo artículo", "Ver el sitio", Informes y Ayuda solo para superusuarios); verificar con `pytest tests/test_editor_home.py` (uno, varios y ningún listado; menú de editor y de superusuario)
- [x] 2.3 Ítems "Encabezado", "Pie" y "Textos del pie" en la barra del sitio; verificar con `pytest tests/test_editor_home.py` (enlace al menú del idioma activo, crear si falta, sin permiso no aparece)

## 3. Marca

- [x] 3.1 Templates de marca (logo, nombre en login, panel y título) y `ORION_ADMIN_COLORS` con la vista de CSS y los chequeos `orion.E004` y `orion.W001`; verificar con `pytest tests/test_editor_branding.py` (login con logo y nombre, sin logo queda el de Wagtail, CSS con HSL, color inválido y bajo contraste)

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador como editor y como superusuario: panel, acciones, "Nuevo artículo" con uno y dos listados, menú, barra del sitio en `/en/`, login con marca, colores aplicados, en escritorio y celular
- [x] 4.2 Traducir los textos nuevos, actualizar README (panel, atajos, marca y `ORION_ADMIN_COLORS`) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check` y `makemigrations --check`; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-admin-home-and-branding` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 279 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 279 pruebas pasaron.
- `ruff`, `pre-commit run --all-files`, `manage.py check` y `makemigrations --check` en
  ambas bases (sin migraciones) y `msgfmt --check`: sin errores.
- Chrome sin interfaz sobre una SQLite nueva con `ORION_ADMIN_COLORS`, logos e inglés
  público: login con el logo, "Ingresar a Clínica Ejemplo" y los colores cargados (sin
  sesión); como editora del grupo Editors: "Hola, Ana", cinco acciones sin Datos del sitio,
  menú con "Nuevo artículo" y "Ver el sitio" y sin Informes ni Ayuda, título de pestaña y
  del panel con el nombre del sitio, logo claro en el menú lateral, sin contadores, y
  "Escribir un artículo" abre el formulario en el único listado; en `/en/`, la barra
  flotante ofrece el encabezado (alta en inglés), el pie (el menú del pie en inglés) y los
  textos del pie (alta en inglés); como superusuario: seis acciones con Informes y Ayuda;
  panel a 390 px sin desbordes; sin errores de consola.
- Hallazgos que cambiaron la implementación:
  - Los contadores seguían en el panel: el hook se ejecutaba antes que los de imágenes y
    documentos de Wagtail; corre al final con `order=100` (prueba incluida).
  - Las URLs registradas en el admin exigen sesión, así que la hoja de colores se sirve
    desde `orion.urls` para que la use el login.
  - En el sitio, la barra flotante sigue el idioma de la página (en `/en/` dice "Header",
    "Footer"), igual que los ítems propios de Wagtail.
- Pendiente para el cambio 3: frases de Wagtail que siguen en inglés en el admin en
  español ("Search all pages…", "Password", "Page types usage", "Shortcuts").
