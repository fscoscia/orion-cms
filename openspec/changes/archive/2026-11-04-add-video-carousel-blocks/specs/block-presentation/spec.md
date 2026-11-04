# Spec Delta

## ADDED Requirements

### Requirement: Videos do not load until they are needed
Un video MUST NOT descargarse al abrir la página: SHALL mostrar su portada y empezar a
descargarse cuando el visitante lo inicia o, en modo ambiente, cuando entra en pantalla.
La portada SHALL declarar su ancho y su alto para que la página no salte.

#### Scenario: Video below the fold
- **WHEN** una página tiene un video fuera de la pantalla
- **THEN** el navegador no pide el archivo de video y la portada es diferida

### Requirement: Controlled videos are started by the visitor
Un video con controles SHALL mostrar su portada con un botón de reproducir e iniciarse
solo por acción del visitante, con sonido y con los controles nativos del navegador,
usables con el teclado. Sin JavaScript SHALL mostrar los controles nativos.

#### Scenario: Pressing play
- **WHEN** un visitante pulsa el botón de reproducir sobre la portada
- **THEN** el video se reproduce con sonido y puede pausarlo con el teclado

#### Scenario: Controlled video without JavaScript
- **WHEN** un visitante abre un video con controles sin JavaScript
- **THEN** puede iniciarlo con los controles nativos

### Requirement: Ambient videos respect the visitor
Un video ambiente SHALL reproducirse sin sonido y en bucle solo mientras esté en pantalla.
Con `prefers-reduced-motion` o sin JavaScript MUST NOT reproducirse: SHALL quedar la
portada.

#### Scenario: Leaving the screen
- **WHEN** un visitante desplaza la página hasta sacar un video ambiente de la pantalla
- **THEN** el video se pausa, y vuelve a reproducirse cuando regresa

#### Scenario: Reduced motion
- **WHEN** el visitante tiene activado `prefers-reduced-motion`
- **THEN** el video ambiente no se reproduce y se ve su portada

### Requirement: Visitors can pause ambient videos
Un video ambiente en reproducción SHALL ofrecer un botón de pausa usable con el teclado, y
lo que el visitante pausa MUST NOT reanudarse solo.

#### Scenario: Pausing
- **WHEN** un visitante pausa un video ambiente y vuelve a pasar por él
- **THEN** el video sigue pausado hasta que pulsa el botón otra vez

### Requirement: Carousels are operable by every input
El carrusel SHALL recorrerse con botones de anterior y siguiente, con puntos que indican
la posición, con las flechas del teclado y con gesto táctil. Los controles SHALL tener
nombre accesible y la posición actual SHALL anunciarse.

#### Scenario: Keyboard
- **WHEN** el foco está en el carrusel y el visitante pulsa la flecha derecha
- **THEN** el carrusel avanza a la siguiente diapositiva

#### Scenario: Last slide
- **WHEN** el carrusel está en la última diapositiva
- **THEN** el botón de siguiente queda deshabilitado

### Requirement: Carousels degrade to scrolling
Sin JavaScript todas las diapositivas SHALL ser accesibles con desplazamiento horizontal
y los botones y los puntos MUST NOT mostrarse.

#### Scenario: No JavaScript
- **WHEN** un visitante abre un carrusel sin JavaScript
- **THEN** recorre las diapositivas desplazándolas y no ve controles que no funcionan

### Requirement: Slides pause what leaves the screen
Una diapositiva que deja de verse MUST NOT seguir reproduciendo su video.

#### Scenario: Moving to another slide
- **WHEN** un visitante pasa a otra diapositiva con un video en reproducción
- **THEN** ese video se pausa

### Requirement: A leading carousel loads its first image first
Cuando el primer bloque visible de una página es un Carrusel a todo el ancho, la imagen
de su primera diapositiva MUST NOT ser diferida, SHALL tener prioridad alta y la página
SHALL precargarla, como la del Hero. Las demás imágenes SHALL ser diferidas.

#### Scenario: Page opening with a carousel
- **WHEN** una página empieza con un Carrusel a todo el ancho
- **THEN** la primera imagen tiene `fetchpriority="high"`, el `<head>` la precarga en AVIF
  y las demás tienen `loading="lazy"`

#### Scenario: Carousel further down
- **WHEN** un Carrusel no es el primer bloque de la página
- **THEN** todas sus imágenes son diferidas
