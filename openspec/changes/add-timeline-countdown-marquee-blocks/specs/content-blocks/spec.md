## MODIFIED Requirements

### Requirement: The block library offers the base blocks
Orion SHALL ofrecer los bloques Hero, Texto, Imagen, Galería, Imagen + texto, Tarjetas,
Cifras animadas, Pestañas, Acordeón, Llamada a la acción, Logos, Datos de contacto, Botón,
Últimas novedades, Mapa, Video, Carrusel, Pasos, Cuenta regresiva y Cinta, y un cuerpo de
página que los reúne a todos para que un tipo de página lo use sin declararlos uno por uno.

#### Scenario: Adding a block
- **WHEN** un editor agrega un bloque en un campo que usa el cuerpo de página de Orion
- **THEN** el selector ofrece los veinte bloques

#### Scenario: Project with a subset
- **WHEN** un proyecto arma su propio cuerpo de página con algunos bloques de Orion y uno
  propio
- **THEN** el selector ofrece solo esos bloques y cada uno se muestra con su diseño

## ADDED Requirements

### Requirement: The steps block shows numbered steps
El bloque Pasos SHALL mostrar entre dos y doce pasos en orden, numerados automáticamente a
partir de uno, cada uno con título, texto e imagen opcional, y un título y antetítulo
opcionales sobre el conjunto. Al reordenar los pasos en el admin, los números SHALL seguir
el orden nuevo.

#### Scenario: Numbering
- **WHEN** un editor carga tres pasos y publica
- **THEN** la página los muestra numerados 1, 2 y 3 en ese orden

#### Scenario: Too few steps
- **WHEN** un editor guarda el bloque con un solo paso
- **THEN** el admin rechaza el bloque y pide al menos dos

#### Scenario: Reordering
- **WHEN** un editor mueve el último paso al primer lugar
- **THEN** la página lo muestra como el paso 1 y renumera los demás

### Requirement: The countdown block shows the time left to a deadline
El bloque Cuenta regresiva SHALL pedir una fecha y hora límite y mostrar los días, horas,
minutos y segundos que faltan, calculados en el navegador del visitante para que la página
siga siendo cacheable, e incluir un título, un antetítulo y un botón opcionales. Sin
JavaScript SHALL mostrar la fecha límite escrita. Cuando la fecha ya pasó SHALL mostrar el
mensaje opcional del editor en lugar del reloj, y si no lo hay SHALL mostrar ceros. El reloj
SHALL ser un temporizador accesible que no anuncie cada segundo a los lectores de pantalla.

#### Scenario: Time left
- **WHEN** la fecha límite está dentro de tres días y el visitante abre la página
- **THEN** ve los días, horas, minutos y segundos que faltan y los segundos avanzan

#### Scenario: Without JavaScript
- **WHEN** la página se abre sin JavaScript
- **THEN** el bloque muestra la fecha límite escrita y no un reloj vacío

#### Scenario: Deadline passed
- **WHEN** la fecha límite ya pasó y el editor cargó un mensaje de cierre
- **THEN** el bloque muestra ese mensaje en lugar del reloj

#### Scenario: Deadline passed without a message
- **WHEN** la fecha límite ya pasó y no hay mensaje
- **THEN** el reloj muestra ceros y no cuenta hacia atrás en negativo

### Requirement: The marquee block slides phrases and logos with a pause
El bloque Cinta SHALL deslizar en bucle una lista de frases cortas y de logos, con una
velocidad elegible (lenta, normal o rápida), y SHALL ofrecer un botón que el visitante use
para pausar y reanudar el movimiento. El movimiento SHALL pausarse también mientras el
puntero esté sobre la cinta. Sin JavaScript, o con movimiento reducido, la cinta
SHALL mostrarse quieta, con todos sus elementos visibles y sin botón. La copia que cierra el
bucle SHALL ocultarse a los lectores de pantalla.

#### Scenario: Sliding
- **WHEN** un visitante abre una página con una cinta y no pidió movimiento reducido
- **THEN** la cinta se desliza y el botón de pausa está disponible con su teclado

#### Scenario: Pausing
- **WHEN** el visitante pulsa el botón de pausa
- **THEN** la cinta se detiene y el botón ofrece reanudarla

#### Scenario: Reduced motion
- **WHEN** el visitante tiene activado el movimiento reducido
- **THEN** la cinta se muestra quieta, con todos sus elementos visibles y sin botón de pausa

#### Scenario: Without JavaScript
- **WHEN** la página se abre sin JavaScript
- **THEN** la cinta se muestra quieta con todos sus elementos y sin botón

#### Scenario: Screen readers
- **WHEN** un lector de pantalla recorre la cinta
- **THEN** anuncia cada frase y cada logo una sola vez
