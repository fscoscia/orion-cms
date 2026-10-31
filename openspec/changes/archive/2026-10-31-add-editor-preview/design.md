## Context

Ver proposal.md (Why). En Wagtail 7.4, el panel lateral del editor guarda en el navegador
qué panel quedó abierto (`wagtail:side-panel-open`) y su ancho (`wagtail:side-panel-width`)
y los lee después de `DOMContentLoaded`; el ancho se acota entre el mínimo y el máximo del
panel. Cada modelo previsualizable define `preview_sizes` (celular, tablet, escritorio) y
`default_preview_size` (por defecto, celular). La vista previa marca `request.is_preview`.
En pantallas angostas el panel ocupa todo el ancho, así que abrirlo ya oculta el
formulario. El encabezado del editor tiene el enlace "En vivo" a la página publicada, en otra
pestaña. El prototipo `opcion1-wagtail` abría la vista previa con un script en línea.

## Goals / Non-Goals

**Goals:**
- Usar el panel de vista previa de Wagtail tal cual, ajustando solo su estado inicial,
  su tamaño por defecto y sus textos.
- Scripts como archivos estáticos, sin código en línea (la CSP del admin llega en la
  Fase 5).

**Non-Goals:**
- Una vista previa propia o dividir la pantalla de otra forma.

## Decisions

### Estado inicial con el almacenamiento de Wagtail
`orion/editor/editor.js`, cargado con `insert_editor_js` (sin `defer`, así corre antes del
`DOMContentLoaded` en el que Wagtail lee su estado): si `wagtail:side-panel-open` no existe
y la ventana mide al menos 1200 px, guarda `preview` y un ancho de la mitad de la ventana.
En ventanas de menos de 800 px, si el valor guardado es `preview`, lo vacía, para no tapar el
formulario al entrar, y fija el tamaño celular en `wagtail:preview-panel-device` (la clave
con la que Wagtail recuerda el tamaño elegido): una página de escritorio reducida a un
celular no se lee. Alternativa: abrir el panel por código después de cargar; pelearía con
la restauración de Wagtail.

### Tamaño escritorio
`DesktopPreviewMixin` en `orion.pages` define `default_preview_size = "desktop"` y lo usan
todos los tipos de página de Orion. Los proyectos lo pueden sumar a sus propios tipos.

### Textos de los botones
El script agrega un `<span>` con "Vista previa" al botón de la vista previa y "Editar" al
botón que cierra el panel; los textos llegan traducidos en atributos `data-` del propio
`<script>`. El CSS (`orion/editor/admin.css`) muestra "Editar" solo en pantallas angostas,
donde el panel tapa el formulario.

### Enlaces dentro de la vista previa
`orion/base.html` carga `orion/js/preview.js` solo si `request.is_preview`. El script
cancela, en fase de captura, los clics en enlaces que no son anclas de la misma página y el
envío de formularios. Alternativa: atributo `sandbox` en el iframe de Wagtail; no es
configurable sin reemplazar su template.

### "Ver publicado"
Se usa el enlace "En vivo" que Wagtail ya muestra en el encabezado del editor para páginas
publicadas; abre la página en otra pestaña. No se agrega otro.

## Risks / Trade-offs

- [Wagtail puede cambiar las claves de su almacenamiento o los atributos de los botones] →
  pruebas en el navegador de este cambio y del siguiente que actualice Wagtail.
- [En pantallas entre 800 y 1200 px la vista previa no se abre sola] → el editor la abre con
  el botón y Wagtail la recuerda.

## Migration Plan

Sin migraciones ni cambios en datos.
