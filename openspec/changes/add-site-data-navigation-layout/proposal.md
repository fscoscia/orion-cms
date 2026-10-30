# Proposal

## Why

Todo sitio necesita un encabezado y un pie con su marca, sus datos de contacto y sus menús,
editables sin tocar código y en cada idioma. Es también el primer lugar donde Orion muestra
diseño, así que este cambio fija cómo se integran Tailwind 4 y Alpine.js antes de construir
la biblioteca de bloques (cambio 3 de la Fase 1, ver `docs/especificacion.md`).

## What Changes

- **Datos del sitio fijos** (un solo lugar, iguales en todos los idiomas): logo, logo del
  pie, teléfono, WhatsApp, email, dirección y redes sociales.
- **Textos del sitio traducibles**: eslogan y texto legal del pie, una versión por idioma,
  traducibles con wagtail-localize.
- **Menús** del encabezado y del pie, de dos niveles, traducibles. Cada ítem enlaza a una
  página interna, una URL externa, un email o un teléfono; las páginas se muestran en el
  idioma de la visita y los ítems a páginas no publicadas no se muestran.
- **Enlaces semánticos**: el mismo tipo de enlace lo usarán los bloques del cambio 3. Una URL
  absoluta del propio sitio se rechaza y se pide elegir la página.
- **Layout base**: encabezado (logo, menú, selector de idioma), pie (logo, eslogan,
  contacto, redes, menú, texto legal), enlace para saltar al contenido y menú en celular
  accesible.
- **Tailwind 4**: Orion trae su CSS ya compilado para sus templates, con colores y fuentes
  como variables CSS que cada proyecto cambia sin compilar. El repositorio de Orion compila
  ese CSS con el binario de Tailwind sin Node.
- **Alpine.js** (variante compatible con CSP) incluido en Orion para la interacción del
  menú y, después, de los bloques.
- Los grupos de editores y moderadores de Wagtail reciben permiso para editar menús y
  textos del sitio; los datos fijos quedan para quien tenga el permiso de ajustes.

**Fuera del alcance:** ubicación en mapa (cambio 5); favicon, imagen social y robots.txt
(SEO, Fase 3); caché del encabezado y el pie (Fase 3); fuentes propias (Fase 3); panel de
inicio y marca en el admin (Fase 2); configuración de Tailwind para los proyectos de
clientes (plantilla de proyecto, Fase 5).

## Capabilities

### New Capabilities
- `site-data`: datos de identidad y contacto del sitio, cuáles son iguales en todos los
  idiomas, cuáles se traducen y quién los edita.
- `site-navigation`: menús del encabezado y del pie, su estructura, su traducción y qué
  ítems se muestran.
- `content-links`: destinos de enlace que eligen los editores (página, URL, email,
  teléfono) y cómo se validan y resuelven.
- `site-layout`: estructura, accesibilidad y personalización visual del encabezado y el
  pie que toda página hereda.

### Modified Capabilities
- Ninguna. El selector de idioma conserva su comportamiento; solo cambia de lugar.

## Impact

- **Código nuevo:** apps `orion.site_data` y `orion.navigation`; bloque de enlace en
  `orion.core`; templates del encabezado, el pie y el menú; CSS fuente de Tailwind,
  CSS compilado, Alpine.js y el JS de los componentes.
- **Código modificado:** `orion/base.html`, ajustes base (apps, procesador de contexto de
  ajustes), ajustes del proyecto de ejemplo, Pipfile, README y CHANGELOG.
- **Dependencias:** django-tailwind-cli solo para desarrollo (compilar el CSS de Orion).
  Alpine.js se incluye como archivo estático versionado, sin gestor de paquetes.
- **Migraciones:** aditivas (tablas nuevas) y una de datos que agrega permisos a los grupos
  de editores y moderadores si existen. No modifican contenido existente.
