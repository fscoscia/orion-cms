## Why

Las páginas de Orion se arman con bloques que el editor agrega, reordena y oculta; es la
principal ventaja sobre las secciones fijas. Los tipos de página del cambio 4
necesitan esa biblioteca ya hecha, con estilos base, accesible y traducible (cambio 3 de la
Fase 1, ver `docs/especificacion.md`).

## What Changes

- **Biblioteca de bloques** con estilos base de Tailwind: Hero, Texto, Imagen, Galería,
  Imagen + texto, Tarjetas, Cifras animadas, Pestañas, Acordeón (preguntas frecuentes),
  Llamada a la acción, Logos, Datos de contacto y Botón.
- **Un cuerpo de página listo para usar** que reúne todos los bloques; cada proyecto puede
  armar el suyo con un subconjunto o sumar bloques propios.
- **Ocultar un bloque sin borrarlo**: interruptor "Visible" en cada bloque.
- **Estilos por proyecto**: cada bloque tiene un campo "Estilo" cuyas opciones declara
  cada proyecto en sus ajustes y cuyo aspecto decide el template del proyecto; con una sola
  opción, el campo no se muestra. Así un diseño ofrece variantes sin crear bloques nuevos
  ni migrar contenido.
- **Títulos con palabras resaltadas**: la negrita de un título se pinta con el color de
  acento.
- **Botones con destino semántico**: usan el enlace del cambio 2 (página en el idioma de
  la visita, URL, email o teléfono; nunca la URL absoluta del propio sitio).
- **Datos de contacto** que muestran los datos del sitio elegidos por el editor y admiten
  datos extra cargados en el bloque (por ejemplo, horarios), con etiqueta y texto.
- **Pestañas y acordeón** con título y texto enriquecido en cada panel; el acordeón no
  necesita JavaScript y las pestañas muestran todos los paneles sin JavaScript.
- **Cifras animadas** que cuentan al aparecer, sin animación si el visitante pidió
  movimiento reducido y con el número final sin JavaScript.
- **Texto enriquecido** con el plugin oficial de tipografía de Tailwind (incluido en el
  binario que ya se usa), heredando la fuente del sitio; los títulos usan la fuente de
  títulos del tema.
- **Imágenes** con texto alternativo obligatorio o marca de decorativa, responsivas en
  WebP con `srcset`, medidas y carga diferida.
- **Editor**: cada bloque con ícono, descripción y vista previa en el selector, con los
  estilos de Orion; textos del admin en español.
- **Página de demostración** solo en el proyecto de ejemplo, con todos los bloques, para
  desarrollar y probar; Orion no agrega tipos de página en este cambio.

**Fuera del alcance:** tipos de página de Orion (Portada, Página libre, Contacto,
Artículos; cambio 4); bloque Mapa (cambio 5); bloque Formulario (Fase 4); AVIF,
`<picture>`, recortes generados al subir y precarga del hero (Fase 3); videos embebidos y
ampliación de imágenes de la galería en pantalla completa (a futuro); búsqueda en el texto
de los bloques (Fase 4); límite de consultas por página (Fase 3); íconos elegibles por el
editor (las tarjetas admiten imagen; un proyecto que necesite íconos reemplaza el template
o suma un bloque propio); SVG subidos por editores (Fase 3, "SVG seguros").

## Capabilities

### New Capabilities
- `content-blocks`: catálogo de bloques, qué carga el editor en cada uno, cómo se ocultan,
  cómo se resaltan los títulos y cómo se traducen.
- `block-presentation`: cómo ve el visitante los bloques: accesibilidad, imágenes,
  comportamiento interactivo con y sin JavaScript y compatibilidad con una CSP estricta.

### Modified Capabilities
- Ninguna. Los botones reutilizan `content-links` sin cambiar sus requisitos.

## Impact

- **Código nuevo:** bloques y cuerpo de página en `orion.core.blocks` (que pasa de módulo
  a paquete sin cambiar sus importaciones), templates de los bloques, template de vista
  previa de bloques, componentes de Alpine en `orion/js/orion.js`; app `demo` en el
  proyecto de ejemplo con una página de demostración y su migración.
- **Código modificado:** `orion.css` fuente y compilado, íconos, etiquetas de template de
  `orion.core`, ajustes del proyecto de ejemplo, traducciones, README y CHANGELOG.
- **Dependencias:** ninguna nueva.
- **Migraciones:** ninguna en Orion (los bloques no crean tablas); una inicial en la app
  `demo` del proyecto de ejemplo, que nunca se despliega. Los nombres de los bloques y de
  sus campos pasan a ser un contrato: cambiarlos después requiere migración de datos.
