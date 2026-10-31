## Why

El objetivo de la Fase 2 es que un editor sin capacitación cargue contenido el primer día.
Hoy el admin abre con el panel genérico de Wagtail (contadores y novedades de la versión),
el menú muestra lo mismo a todos, no hay atajos a lo que más se hace y el admin dice
"Wagtail" en lugar del nombre y la marca del cliente. Es el cambio 1 de la Fase 2 (ver
`docs/especificacion.md`).

## What Changes

- **Panel de inicio**: saludo con el nombre del usuario, acciones grandes (crear una
  página, escribir un artículo, editar la portada, subir imágenes, menús, datos del sitio)
  según los permisos de cada uno, y la lista de páginas con cambios sin publicar. Se quitan
  los contadores y la novedad de versión de Wagtail; se conservan los paneles de
  aprobaciones pendientes y páginas bloqueadas.
- **Menú lateral**: atajos "Nuevo artículo" (si hay un listado de artículos) y "Ver el
  sitio"; Informes y Ayuda solo para administradores (los roles completos llegan en el
  cambio 3).
- **Barra del sitio**: accesos a editar el menú del encabezado, el menú del pie y los
  textos del pie del idioma que se está mirando.
- **Marca del cliente**: el logo del pie en el menú lateral, el logo en el login, el nombre
  del sitio en el login, el panel y el título de las pestañas, y los colores del admin
  definidos en los ajustes del proyecto (`ORION_ADMIN_COLORS`), con un chequeo que avisa si
  el texto blanco no se lee sobre ellos.

**Fuera del alcance:** vista previa (cambio 2); roles, permisos por sección y frases del
admin que siguen en inglés (cambio 3); favicon (SEO, Fase 3); tipografía propia del admin.

## Capabilities

### New Capabilities
- `admin-home`: panel de inicio, atajos del menú lateral y accesos desde la barra del sitio.
- `admin-branding`: logo, nombre y colores del cliente en el admin.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** app `orion.editor` (sin modelos) con el panel de inicio, los hooks del
  admin, los templates que extienden los de Wagtail, la vista que entrega el CSS de colores,
  la vista "nuevo artículo" y los chequeos de colores.
- **Código modificado:** ajustes base (`ORION_ADMIN_COLORS`), traducciones, README y
  CHANGELOG.
- **Dependencias:** ninguna.
- **Migraciones:** ninguna.
