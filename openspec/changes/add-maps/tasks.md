# Tasks

## 1. Base

- [x] 1.1 Incluir Leaflet 1.9.4 (`leaflet.js`, `leaflet.css` y licencia) en `orion/vendor/leaflet-1.9.4/`, verificado contra el hash del paquete de npm; verificar con `cmp` contra el paquete y `runserver`
- [x] 1.2 `LocationField` y `LocationWidget` con el controlador Stimulus `orion-location`; verificar con `pytest tests/test_maps.py` (valor válido, latitud y longitud fuera de rango, redondeo, widget con input oculto y `data-controller`)

## 2. Ubicación del sitio y mapa público

- [x] 2.1 Campos `location` y `map_zoom` en `SiteSettings` con su panel y migración; verificar con `pytest tests/test_maps.py` (rango rechazado en `clean`, migración sin cambios con `makemigrations --check`)
- [x] 2.2 `ORION_MAP_TILES`, el include `orion/includes/map.html` y el componente `map` de Alpine; verificar con `pytest tests/test_maps.py` (recuadro con puntos, enlace a OpenStreetMap, JSON de puntos, configuración de teselas, sin `<script src>` de Leaflet en la página)
- [x] 2.3 Mapa del sitio en la Página de contacto; verificar con `pytest tests/test_maps.py` (con y sin ubicación)

## 3. Bloque Mapa

- [x] 3.1 `MapBlock` con puntos, ubicación del sitio opcional y zoom, en `ContentStreamBlock` (y migración de `demo`); verificar con `pytest tests/test_maps.py` y `pytest tests/test_content_blocks.py` (quince bloques, sin puntos no se muestra, segmentos de traducción con nombre y sin ubicación)

## 4. Navegador y cierre

- [x] 4.1 Estilos y compilación del CSS; verificar con `pipenv run css-build` y `pytest tests/test_site_layout.py`
- [x] 4.2 Verificar en el navegador: elegir la ubicación del sitio con un clic y arrastrando, y en un bloque Mapa agregado a mano; en el sitio, sin pedidos a Leaflet ni a teselas antes del botón, mapa con un punto y con varios, foco, atribución, sin JavaScript, celular, y sin violaciones con una CSP que permita solo el propio sitio y las imágenes del proveedor
- [x] 4.3 Traducir al español los textos nuevos, actualizar README (ubicación, bloque Mapa, `ORION_MAP_TILES`, política de OpenStreetMap y dominio para la CSP) y CHANGELOG; verificar con `msgfmt --check`
- [x] 4.4 Ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-maps` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 245 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 245 pruebas pasaron.
- `ruff check`, `ruff format --check`, `pre-commit run --all-files`, `manage.py check`,
  `makemigrations --check` y `msgfmt --check`: sin errores.
- `migrate` en PostgreSQL y MySQL: aplica `orion_site_data.0003`, `orion_pages.0004` y
  `demo.0003` sin errores.
- Leaflet 1.9.4: el paquete de npm coincide con su hash de integridad y `leaflet.js` y
  `leaflet.css` son idénticos a los de `dist/`; `runserver` los sirve con 200.
- Chrome sin interfaz sobre una SQLite nueva, con la CSP `default-src 'self';
  script-src 'self'; style-src 'self'; img-src 'self' data: https://tile.openstreetmap.org`
  en el sitio (las teselas se interceptaron y respondieron con una imagen vacía): antes del
  botón no hay pedidos a Leaflet ni a teselas; el recuadro lista los tres puntos con el
  enlace a OpenStreetMap; al presionar "Ver mapa" se piden Leaflet y teselas de
  `tile.openstreetmap.org`, los tres marcadores quedan dentro del mapa, el foco pasa al
  mapa, se ve la atribución y el globo de un marcador muestra su nombre y descripción; un
  solo punto usa su zoom (14); la Página de contacto muestra el punto del sitio; sin
  JavaScript se ven los puntos y el enlace y no el botón; a 390 px sin desbordes; sin
  violaciones de CSP ni errores de consola. En el admin: el selector de Datos del sitio
  muestra la ubicación guardada, el clic y el arrastre la mueven, las coordenadas escritas
  la actualizan y se guarda; un bloque Mapa agregado a mano en una Página libre ofrece el
  selector dentro del punto nuevo, el clic fija la ubicación y la página se publica con el
  punto guardado.
- Hallazgos que cambiaron la implementación:
  - Con el admin en español, los atributos numéricos del widget salían con coma decimal
    (`-25,2637`) y el JavaScript no podía leerlos; se usa `unlocalize` (prueba incluida).
  - El bloque recibía la ubicación del formulario como texto JSON y al validarla la volvía
    a codificar, así que rechazaba toda ubicación enviada desde el admin; `LocationBlock`
    decodifica el texto del formulario (prueba que simula el envío incluida).
  - Los cuerpos de `orion.pages` también necesitaron migración por el bloque nuevo.
  - El bloque Mapa tiene vista previa con un punto de ejemplo. Imagen, Galería, Imagen y
    texto, Logos y Últimas novedades siguen sin vista previa en el selector porque necesitan
    imágenes o artículos cargados.
