## Context

Ver proposal.md (Why). Ya existen: `SiteSettings` (ajuste genérico con pestañas Identidad,
Contacto y Redes), `ContactPage` con los datos de contacto, `ContentStreamBlock` con
`BaseContentBlock` (estilo y visibilidad), Alpine.js en su variante CSP con componentes en
`orion/js/orion.js`, el CSS de Orion compilado y el hook `insert_global_admin_css`. Wagtail
7.4 expone `window.StimulusModule` y `window.wagtail.app` para registrar controladores
Stimulus en el admin, y su adaptador genérico de widgets (`WidgetAdapter`) dibuja cualquier
widget de Django dentro de un StreamField y suma su `Media`.

## Goals / Non-Goals

**Goals:**
- Un único widget de ubicación para Datos del sitio y para el bloque Mapa.
- Ningún pedido a servidores externos hasta que el visitante abre el mapa.
- Cambiar de proveedor de teselas sin tocar código de Orion.

**Non-Goals:**
- Geocodificación (buscar una dirección y obtener la ubicación).
- Estilos de mapa propios por proyecto más allá del proveedor de teselas.

## Decisions

### Valor de una ubicación
Una ubicación es un objeto JSON `{"lat": float, "lng": float}`. En `SiteSettings` se guarda
en `location` (`JSONField`, opcional) junto a `map_zoom` (entero de 1 a 19, por defecto
16). En el bloque es un `FieldBlock` (`LocationBlock`) con el mismo campo de formulario.
`LocationField` (un `forms.JSONField`) valida que sea un objeto con `lat` entre -90 y 90 y
`lng` entre -180 y 180, y redondea a seis decimales (unos 10 cm). Alternativa: dos campos
numéricos; no se pueden editar con un solo mapa en un `FieldPanel` y, en el bloque,
obligarían a un `StructBlock` con JavaScript propio por campo.

### Widget de ubicación en el admin
`LocationWidget` dibuja un input oculto con el JSON (el que lee y escribe el adaptador
genérico de widgets de Wagtail), dos inputs numéricos de latitud y longitud y un div para
el mapa, dentro de un elemento con `data-controller="orion-location"`. El controlador
Stimulus (`orion/admin/location.js`, registrado con `window.wagtail.app.register`) crea el
mapa de Leaflet, mueve el marcador con un clic o al arrastrarlo, y mantiene sincronizados
el JSON y los inputs numéricos en ambos sentidos. Al usar Stimulus, el controlador se
conecta solo cuando el widget aparece, incluso dentro de un bloque agregado después en el
StreamField. El `Media` del widget carga Leaflet, su CSS y el controlador, así que solo se
cargan en los formularios que lo usan. Sin ubicación, el mapa del admin arranca centrado en
`ORION_MAP_DEFAULT_CENTER` (por defecto Asunción, zoom 12). Para `SiteSettings`, el panel
usa `FieldPanel("location", widget=LocationWidget)` y la validación de rangos vive en
`SiteSettings.clean`, porque el campo de formulario del modelo es el `JSONField` de Django.

### Mapa público con carga a pedido
`orion/includes/map.html` recibe una lista de puntos (`lat`, `lng`, nombre, descripción) y
un zoom, y dibuja:
- un `<figure>` con la lista de nombres de los puntos, un enlace "Abrir en OpenStreetMap"
  (al primer punto) y un botón "Ver mapa";
- los datos del mapa en un `<script type="application/json">` (con `json_script`), que el
  navegador no ejecuta y por eso no choca con la CSP;
- la configuración de teselas en atributos `data-`.

El componente `map` de Alpine, al presionar el botón, agrega `leaflet.css` y `leaflet.js`
(del propio sitio) si todavía no están, espera a que carguen, crea el mapa con un marcador
por punto (un `L.divIcon` con un SVG, así no depende de las imágenes de marcador de
Leaflet), centra en el punto o encuadra todos con `fitBounds`, muestra la atribución, oculta
el botón y pasa el foco al mapa. Leaflet aplica estilos con la API de CSSOM, que la CSP no
restringe; no usa `eval` ni estilos en línea en el HTML.

### Bloque Mapa
`MapBlock` (clave `map`, en `ContentStreamBlock`): título opcional, "Incluir la ubicación
del sitio" (por defecto activado), puntos (`ListBlock` de `MapPointBlock`: ubicación,
nombre y descripción opcional) y zoom (1 a 19, por defecto 16, usado con un solo punto). Su
`get_context` arma la lista de puntos (la del sitio primero, con el nombre del sitio y la
dirección) y no dibuja nada si no queda ninguno. wagtail-localize traduce el nombre y la
descripción (`CharBlock` y `TextBlock`) e ignora la ubicación (`FieldBlock`), que queda
sincronizada.

### Página de contacto
`ContactPage.get_context` agrega el punto del sitio si `SiteSettings.location` está cargada
y el template incluye `orion/includes/map.html` después de los datos de contacto.

### Proveedor de teselas
`ORION_MAP_TILES` en los ajustes base: `url`
(`https://tile.openstreetmap.org/{z}/{x}/{y}.png`), `attribution` (enlace a los
colaboradores de OpenStreetMap) y `max_zoom` (19). Un proyecto lo reemplaza entero. El
README recuerda la política de uso de OpenStreetMap (atribución visible, sin tráfico alto)
y que la CSP del sitio tiene que permitir el dominio de las teselas en `img-src`.

### Leaflet incluido como archivo estático
Leaflet 1.9.4 (BSD-2-Clause, la última estable; la 2.0 sigue en alfa) en
`orion/vendor/leaflet-1.9.4/` (`leaflet.js`, `leaflet.css` y la licencia), copiado del
paquete de npm y verificado contra su hash de integridad, igual que Alpine. Lo usan el
mapa público y el widget del admin.

## Risks / Trade-offs

- [El adaptador genérico de widgets podría fijar el valor después de que se conecta el
  controlador Stimulus] → el controlador también escucha `change` en el input oculto; la
  verificación en el navegador cubre un bloque agregado a mano.
- [OpenStreetMap no admite tráfico alto] → la carga a pedido reduce los pedidos; el
  proveedor es configurable y el README lo advierte.
- [Los visitantes sin JavaScript no ven el mapa] → ven los puntos y el enlace a
  OpenStreetMap.
- [El JSON de ubicación no se puede consultar por rango en la base] → no hace falta en la
  v1; se lee entero.

## Migration Plan

`orion_site_data.0003` agrega `location` (nulo) y `map_zoom` (con valor por defecto);
`orion_pages.0004` y la app `demo` registran el bloque nuevo en los cuerpos de página (solo
cambia la definición del StreamField, no los datos). Revertir es revertir esas migraciones;
no tocan contenido existente.
