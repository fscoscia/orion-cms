## Context

Ver proposal.md (Why). Wagtail crea en su migración inicial los grupos "Editors" (agregar y
modificar páginas desde la raíz, imágenes, documentos) y "Moderators" (además publicar,
bloquear y desbloquear), y el flujo "Moderators approval" con una tarea de aprobación por
grupo asignada a la raíz. Las migraciones de Orion ya suman a ambos grupos los permisos de
menús, textos del sitio, categorías y etiquetas (`orion.core.permissions`, por nombre de
grupo). Los catálogos en español que trae Wagtail omiten las frases sin traducir; comparados
con los catálogos en inglés faltan 365 frases de Python y 17 de JavaScript. Django suma al
final, con mayor prioridad, los catálogos de `LOCALE_PATHS`, también en el dominio
`djangojs` que Wagtail sirve solo con los catálogos de `wagtail.admin`. El formulario de
login de Wagtail no le pone etiqueta a la contraseña, así que Django usa el nombre del campo
sin traducir.

## Goals / Non-Goals

**Goals:**
- Reusar los grupos, permisos y flujo de Wagtail, renombrados, sin crear otros paralelos.
- Que el criterio de "administrador" del menú sea el rol, no ser superusuario.

**Non-Goals:**
- Traducir textos que escribe el usuario (nombres de grupos o flujos creados después).

## Decisions

### Renombrar en lugar de crear
Una migración de datos (`orion_editor.0001_roles`, después de las migraciones de permisos
de Orion y de todas las de Wagtail que buscan los grupos por su nombre en inglés para
otorgar permisos: `wagtailcore`, `wagtailadmin`, `wagtailimages` y `wagtaildocs`) renombra "Editors" a "Editores" y "Moderators" a
"Administradores", y el flujo y la tarea "Moderators approval" a "Aprobación de
administradores", solo si conservan el nombre original y el nombre nuevo no existe. Así se
conservan usuarios, permisos y la asignación del flujo. `orion.core.permissions` busca los
grupos por los nombres nuevos y los viejos, para las migraciones futuras.

### Permisos de Administradores
La misma migración agrega a "Administradores" (sin quitar nada):
- páginas: `bulk_delete_page` sobre la raíz (publicar, bloquear y desbloquear ya los tiene);
- fragmentos de Orion: borrar menús, textos del sitio, categorías y etiquetas;
- ajustes: datos del sitio e idiomas (`change_sitesettings`, `change_languagesettings`);
- idiomas de Wagtail: agregar, modificar y borrar regiones (`wagtailcore.*_locale`) y
  enviar traducciones (`wagtail_localize.submit_translation`);
- usuarios: agregar, modificar y borrar (`auth.*_user`).
No recibe permisos de sitios, colecciones, flujos ni grupos. Editores recibe
`submit_translation` para preparar traducciones. Wagtail ya impide que quien no es
superusuario marque a otro como superusuario.

### Rol en el código
`orion.editor.roles` define `EDITORS_GROUP` y `ADMINISTRATORS_GROUP` e
`is_site_administrator(user)` (superusuario o miembro de Administradores), que reemplaza a
`is_superuser` en el menú (Informes y Ayuda).

### Catálogo de traducciones de Wagtail
`src/orion/editor/wagtail_locale/es/LC_MESSAGES/django.po` y `djangojs.po` con las frases
que faltan, y `LOCALE_PATHS = [ORION_DIR / "editor" / "wagtail_locale"]` en los ajustes
base (los proyectos lo extienden con `+=`). Un directorio aparte del catálogo de la app,
porque `makemessages` borraría esas entradas como obsoletas. Traducciones en español neutro
(sin voseo; "usted" solo donde la frase lo exige), con "región" para *locale* como el resto
de Wagtail en español.

`orion.editor.translations.missing_wagtail_translations(language)` compara los catálogos en
inglés de las apps instaladas de Wagtail y wagtail-localize con lo que gettext encuentra en
ejecución (los catálogos de Django y de todas las apps instaladas, más el de Orion) y
devuelve lo que falta; `redundant_orion_translations` controla que el catálogo de Orion no
repita frases ya traducidas (con `LOCALE_PATHS` las pisaría); lo usan una prueba y el script
`scripts/missing_wagtail_translations.py`, que genera las entradas nuevas cuando se
actualiza Wagtail.

### Textos escritos en inglés en plantillas
La columna "Uso" del listado de regiones de wagtail-localize está escrita en inglés en su
plantilla, sin pasar por gettext. `orion.editor` reemplaza el bloque `listing` de
`wagtaillocales/index.html` con una copia que la traduce con plurales.

### Etiqueta de la contraseña
`orion.editor.forms.LoginForm` hereda del de Wagtail y pone las etiquetas traducidas;
`WAGTAILADMIN_USER_LOGIN_FORM` en los ajustes base. El cambio 4 (2FA) parte de este
formulario.

## Risks / Trade-offs

- [Un proyecto que ya renombró los grupos] → la migración no toca grupos con otro nombre ni
  pisa nombres existentes; `is_site_administrator` busca el nombre nuevo.
- [`LOCALE_PATHS` tiene prioridad sobre todo] → el catálogo solo contiene frases que
  Wagtail no traduce; una prueba controla que no repita frases que Wagtail sí traduce.
- [Wagtail puede agregar frases en cada versión] → la prueba de frases faltantes lo detecta.

## Migration Plan

`orion_editor.0001_roles`: renombra y agrega permisos; la reversa devuelve los nombres
originales y quita solo los permisos que agregó. No toca contenido.
