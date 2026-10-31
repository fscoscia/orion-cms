# maps Specification

## Purpose
Define cómo los editores eligen ubicaciones, cómo se muestran los mapas a los visitantes,
cuándo se cargan y de qué proveedor salen las teselas.

## Requirements

### Requirement: Editors pick locations on a map
Cada ubicación SHALL elegirse en el admin haciendo clic en un mapa o arrastrando su
marcador, y SHALL poder escribirse a mano como latitud y longitud. El admin MUST rechazar
una latitud fuera de -90 a 90 o una longitud fuera de -180 a 180.

#### Scenario: Clicking on the map
- **WHEN** un editor hace clic en un punto del mapa de una ubicación
- **THEN** la latitud y la longitud de ese punto quedan cargadas y el marcador se mueve ahí

#### Scenario: Invalid latitude
- **WHEN** un editor escribe la latitud 95
- **THEN** el admin rechaza la ubicación

### Requirement: Maps load only on request
Un mapa SHALL mostrarse primero como un recuadro con los nombres de sus puntos, un botón
"Ver mapa" y un enlace para abrir la ubicación en OpenStreetMap. La biblioteca del mapa y
las teselas MUST NOT pedirse hasta que el visitante presione el botón.

#### Scenario: Page with a map
- **WHEN** un visitante abre una página con un mapa y no presiona el botón
- **THEN** el navegador no pide la biblioteca del mapa ni teselas al proveedor

#### Scenario: Showing the map
- **WHEN** el visitante presiona "Ver mapa"
- **THEN** el mapa se muestra con un marcador por punto y el foco queda en el mapa

#### Scenario: Without JavaScript
- **WHEN** el navegador no ejecuta JavaScript
- **THEN** el recuadro muestra los puntos y el enlace a OpenStreetMap

### Requirement: Maps show every point
Un mapa con un punto SHALL centrarse en él con el zoom elegido; un mapa con varios puntos
SHALL encuadrarlos a todos. Cada marcador SHALL mostrar su nombre y su descripción al
seleccionarlo.

#### Scenario: Three branches
- **WHEN** un bloque Mapa tiene tres puntos
- **THEN** el mapa muestra los tres marcadores dentro de la vista

### Requirement: The tile provider is configurable
El proveedor de teselas SHALL definirse por configuración del proyecto, con la URL de las
teselas, el texto de atribución y el zoom máximo, y SHALL ser OpenStreetMap por defecto. El
mapa SHALL mostrar siempre la atribución del proveedor.

#### Scenario: Default provider
- **WHEN** un proyecto no configura el proveedor
- **THEN** el mapa usa las teselas de OpenStreetMap y muestra su atribución

### Requirement: Maps work under a strict Content Security Policy
El mapa MUST funcionar sin evaluar código ni scripts en línea, con una política que permita
solo los scripts del propio sitio y las imágenes del proveedor de teselas.

#### Scenario: Strict policy
- **WHEN** el sitio se sirve con esa política y el visitante abre el mapa
- **THEN** el mapa se muestra y el navegador no informa violaciones

### Requirement: Map labels are translatable
El nombre y la descripción de cada punto de un bloque Mapa SHALL traducirse con el flujo de
traducción del sitio; las ubicaciones SHALL ser las mismas en todos los idiomas.

#### Scenario: Translated point
- **WHEN** una página con un bloque Mapa se traduce a `en`
- **THEN** wagtail-localize ofrece el nombre del punto para traducir y no su ubicación
