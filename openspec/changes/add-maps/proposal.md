## Why

Los sitios institucionales muestran dónde está el negocio, y la especificación incluye los
mapas en la v1 con Leaflet y teselas de OpenStreetMap, sin servicios pagos. Es el último
cambio de la Fase 1 (cambio 5, ver `docs/especificacion.md`) y completa la Página de
contacto, que dejó lugar para el mapa.

## What Changes

- **Ubicación del sitio** en Datos del sitio, elegida haciendo clic en un mapa o
  arrastrando el marcador, con latitud y longitud editables a mano y un nivel de zoom.
- **Bloque "Mapa"** con uno o varios puntos (cada uno elegido en un mini mapa, con nombre y
  descripción opcional) y la opción de incluir la ubicación del sitio.
- **Página de contacto** que muestra sola el mapa de la ubicación del sitio cuando está
  cargada.
- **Carga a pedido**: el mapa se muestra como un recuadro con los nombres de los puntos, un
  botón "Ver mapa" y un enlace para abrirlo en OpenStreetMap. Leaflet y las teselas se
  cargan solo cuando el visitante lo pide; sin JavaScript queda el enlace.
- **Proveedor de teselas configurable** por ajustes (`ORION_MAP_TILES`: URL, atribución y
  zoom máximo), con OpenStreetMap por defecto.
- **Leaflet 1.9.4** incluido como archivo estático versionado, con su licencia, como
  Alpine.js.

**Fuera del alcance:** búsqueda de direcciones (geocodificación, depende de un servicio
externo); rutas o indicaciones para llegar; mapas con capas, polígonos o agrupación de
marcadores; proveedores con clave de API (Google Maps, Mapbox), que quedan a futuro; la
política CSP que habilita el servidor de teselas, que llega con los headers de seguridad
de la Fase 5 (el README indica qué dominio permitir).

## Capabilities

### New Capabilities
- `maps`: cómo se eligen las ubicaciones, cómo se muestran los mapas al visitante, cuándo
  se cargan y de dónde salen las teselas.

### Modified Capabilities
- `site-data`: los datos fijos suman la ubicación del sitio.
- `page-types`: la Página de contacto suma el mapa de la ubicación del sitio.
- `content-blocks`: el catálogo suma el bloque Mapa.

## Impact

- **Código nuevo:** widget de ubicación del admin (campo de formulario, widget y
  controlador Stimulus) y bloque de mapa en `orion.core`; componente `map` de Alpine en
  `orion/js/orion.js`; templates del mapa; Leaflet en `orion/vendor/`.
- **Código modificado:** `SiteSettings` (campos `location` y `map_zoom`),
  `ContentStreamBlock`, template de la Página de contacto, `orion.css`, migración de la app
  `demo`, traducciones, README y CHANGELOG.
- **Dependencias:** Leaflet 1.9.4 (BSD-2-Clause) como archivo estático, sin gestor de
  paquetes; ninguna dependencia de Python.
- **Migraciones:** aditiva en `orion_site_data` (dos campos opcionales); `orion_pages` y
  `demo` registran el bloque nuevo en los cuerpos de página (solo la definición). No modifican contenido existente.
