## Why

La especificación define dos roles, Administrador (todo el contenido) y Editor (prepara
contenido), con aprobación del administrador antes de publicar. Hoy Orion depende de los
grupos que crea Wagtail en inglés ("Editors", "Moderators") y de que el cliente sea
superusuario para administrar, lo que le da acceso a la configuración técnica. Además, el
admin en español todavía muestra unas 380 frases de Wagtail en inglés ("Search all
pages…", "Password", "Shortcuts", "Add a locale"). Es el cambio 3 de la Fase 2.

## What Changes

- **Roles**: los grupos de Wagtail pasan a llamarse "Editores" y "Administradores" (los
  permisos ya dados se conservan). Administradores suma permisos para publicar, borrar,
  administrar fragmentos, datos del sitio, idiomas y usuarios, sin acceso a lo técnico
  (sitios, colecciones, flujos, grupos). El flujo de aprobación de Wagtail pasa a llamarse
  "Aprobación de administradores": el Editor envía a revisión y el Administrador aprueba.
- **Menú por rol**: Informes y Ayuda se muestran a Administradores y superusuarios.
- **Permisos por sección**: se documenta cómo limitar un grupo a una sección del árbol
  (función nativa de Wagtail).
- **Admin en español completo**: un catálogo de Orion traduce las frases que Wagtail y
  wagtail-localize dejan sin traducir (también las de JavaScript), y la etiqueta de la
  contraseña del login; una prueba falla si una versión nueva de Wagtail agrega frases sin
  traducir.

**Fuera del alcance:** 2FA (cambio 4); calendario, vista previa compartible y publicación
programada (cambio 5); roles adicionales (por ejemplo, solo lectura).

## Capabilities

### New Capabilities
- `roles`: qué puede hacer cada rol y cómo se aprueba lo que prepara un Editor.
- `admin-language`: el admin en español sin frases en inglés.

### Modified Capabilities
- Ninguna. Las specs `site-data` y `taxonomies` hablan de "editores y moderadores": los
  grupos se renombran, pero los permisos no cambian.

## Impact

- **Código nuevo:** migración de datos en `orion.editor` (renombra grupos y flujo, suma
  permisos), catálogo de traducciones de Wagtail en `orion/editor/wagtail_locale/`,
  formulario de login, script que lista las frases que faltan.
- **Código modificado:** ajustes base (`LOCALE_PATHS`, formulario de login), helper de
  permisos de migraciones (nombres nuevos), menú por rol, pruebas que usan los nombres de
  los grupos, README y CHANGELOG.
- **Dependencias:** ninguna.
- **Migraciones:** una de datos que renombra grupos y el flujo de Wagtail y agrega permisos
  a Administradores; no quita permisos ni borra datos. Reversible.
