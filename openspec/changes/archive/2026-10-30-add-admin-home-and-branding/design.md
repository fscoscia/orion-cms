## Context

Ver proposal.md (Why). Wagtail 7.4 ofrece, sin modificar su código: hooks para los paneles
del inicio (`construct_homepage_panels`, `construct_homepage_summary_items`), el menú
lateral (`register_admin_menu_item`, `construct_main_menu`), la barra del sitio
(`construct_wagtail_userbar`), URLs propias del admin (`register_admin_urls`) y CSS global
(`insert_global_admin_css`); y bloques de marca en sus templates (`branding_logo`,
`branding_login`, `branding_welcome`, `branding_title`). El admin pinta sus colores con
variables CSS en HSL (`--w-color-primary-hue`, `-saturation`, `-lightness` y las
equivalentes `secondary`). Las apps de Orion van antes que las de Wagtail en
`INSTALLED_APPS`, así que sus templates reemplazan a los de Wagtail con el mismo nombre. El
prototipo `opcion1-wagtail` resolvió panel, menú y marca para un cliente; se toma su UX,
no su código.

## Goals / Non-Goals

**Goals:**
- Todo con hooks y bloques de template de Wagtail, sin copiar ni parchear templates enteros.
- Acciones y atajos que respetan los permisos de Wagtail, así sirven para cualquier rol.

**Non-Goals:**
- Definir los roles (cambio 3): por ahora "administrador" es `is_superuser`.
- Personalizar la tipografía o el diseño general del admin más allá de los colores.

## Decisions

### App `orion.editor`
La experiencia del editor vive en una app nueva, `orion.editor` (etiqueta `orion_editor`,
sin modelos), en `ORION_APPS`. Los cambios siguientes de la Fase 2 (vista previa, roles,
2FA, flujo editorial) suman ahí lo suyo. Alternativa: `orion.core`; ya concentra bloques y
templates del sitio y mezclaría dos audiencias.

### Panel de inicio
`WelcomePanel` (un `Component` de Wagtail, primero en el orden) con
`orion/editor/home/welcome_panel.html`. Calcula las acciones con los permisos del usuario:
- "Crear una página": vista de Wagtail para agregar una página debajo de la Portada, si el
  usuario puede agregar ahí.
- "Escribir un artículo": la vista "nuevo artículo" (abajo), si hay listados donde pueda
  agregar.
- "Editar la portada": si puede editar la Portada del sitio.
- "Subir imágenes": la carga múltiple de Wagtail, con permiso de agregar imágenes.
- "Menús": el listado de menús, con permiso de modificar menús.
- "Datos del sitio": el ajuste, con su permiso.
- "Cambios sin publicar": las 8 páginas más recientes con `has_unpublished_changes` que el
  usuario puede editar (`PagePermissionPolicy.instances_user_has_permission_for`), con su
  tipo y la fecha de su última revisión.

`construct_homepage_summary_items` (con `order=100`, para correr después de los hooks de
imágenes y documentos de Wagtail, que suman sus contadores después de las apps de Orion)
vacía los contadores y `construct_homepage_panels`
quita los paneles de novedad y aviso de versión de Wagtail, y conserva aprobaciones,
páginas bloqueadas y ediciones recientes. Los estilos van en `orion/editor/admin.css` y usan
las variables del admin, así respetan el modo oscuro.

### "Nuevo artículo"
Una URL del admin (`orion_editor_new_article`) busca los listados donde el usuario puede
agregar páginas: con uno, redirige al formulario de Wagtail para crear un artículo ahí; con
varios, muestra una página con los listados para elegir; sin ninguno, 404. El atajo del
menú lateral (orden 1) y la acción del panel apuntan a esa URL y solo se muestran cuando hay
listados disponibles.

### Menú lateral
`register_admin_menu_item` agrega "Ver el sitio" (al final, abre la raíz del sitio en otra
pestaña). `construct_main_menu` quita "reports" y "help" para quien no es superusuario.

### Barra del sitio
`construct_wagtail_userbar` agrega tres ítems (un `BaseItem` con template propio cada uno):
"Encabezado" y "Pie" llevan a editar el `Menu` de esa ubicación en el idioma activo (o a
crearlo si no existe), y "Textos del pie" al `SiteTexts` de ese idioma. Cada uno aparece
solo con permiso de modificar (o agregar) ese modelo.

### Marca
- Templates que extienden los de Wagtail: `wagtailadmin/base.html` (`branding_logo`: el
  logo del pie como imagen pequeña, si existe), `wagtailadmin/login.html`
  (`branding_login`: "Ingresar a <sitio>"; `branding_logo`: el logo),
  `wagtailadmin/home.html` (`branding_welcome`: "Panel de <sitio>") y
  `wagtailadmin/admin_base.html` (`branding_title`: el nombre del sitio).
- Nombre: el `site_name` del sitio por defecto o, si está vacío, `WAGTAIL_SITE_NAME`.
- Colores: `ORION_ADMIN_COLORS = {"primary": "#...", "secondary": "#..."}` (vacío por
  defecto). Una vista (`orion_admin_colors`, en `<ruta del admin>orion/colors.css`, declarada
  en `orion.urls` antes del admin porque Wagtail exige sesión en las URLs que se registran
  dentro del admin y el login también la necesita) convierte cada color a HSL y entrega
  `:root { --w-color-primary-hue: ...; ... }` como CSS, enlazado con
  `insert_global_admin_css`. Un archivo y no un `<style>` en línea, para no complicar la
  CSP del admin en la Fase 5.
- Chequeos: `orion.E004` si un color no es hexadecimal de 6 dígitos o la clave no es
  `primary`/`secondary`; `orion.W001` si el contraste del blanco sobre el color es menor
  que 4.5:1 (fórmula de luminancia relativa de WCAG).

## Risks / Trade-offs

- [Los nombres de paneles y elementos de menú de Wagtail pueden cambiar en otra versión] →
  se quitan por nombre y una prueba falla si dejan de existir.
- [El logo del pie puede no verse sobre el menú lateral si no es claro] → el texto de ayuda
  del logo del pie ya pide una versión clara; el README lo recuerda.
- [Superusuario como sinónimo de administrador hasta el cambio 3] → el cambio 3 reemplaza
  ese criterio por el rol.

## Migration Plan

Sin migraciones. La app se suma a `ORION_APPS`; quitarla devuelve el admin de Wagtail.
