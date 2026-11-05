## Context

Ver `proposal.md` para el motivo. Lo que condiciona el enfoque, comprobado en el código:

- Los bloques heredan de `BaseContentBlock` (estilo, ancla y visibilidad) y se reúnen en
  `ContentStreamBlock`. `BodyStreamField` describe solo los bloques de Orion, así que sumar
  uno genera una migración de definición en `orion.pages`. `ArticleStreamBlock` hereda de
  `ContentStreamBlock`: los bloques nuevos llegan también a los artículos.
- Los bloques con título llevan `EyebrowBlock` (convención desde `add-block-eyebrow-and-anchors`).
- El sitio usa Alpine en su variante CSP: `orion.js` define los componentes con
  `Alpine.data` y las plantillas solo los nombran. Ya existe `counter` (Cifras), que respeta
  `prefers-reduced-motion` y muestra el valor final si no hay `IntersectionObserver`.
- Las páginas se sirven con caché de página completa: nada que dependa de la hora actual
  puede calcularse en el servidor.
- El CSS base de Orion está compilado y versionado; cada bloque nace con estilos base y
  `.orion-on-dark` ya existe para texto claro sobre fondo oscuro.
- Bolt Emprende escribió estos tres bloques como bloques de proyecto: sirven de referencia
  de campos y de marcado, no se copian tal cual.

## Goals / Non-Goals

**Goals:**
- Tres bloques que funcionen con el diseño base y que cada proyecto adapte con
  `ORION_BLOCK_STYLES` o reemplazando el template.
- Funcionar sin JavaScript, con movimiento reducido y bajo `SCRIPT_NAME`.
- Cero dependencias nuevas.

**Non-Goals:**
- Efectos de scroll, parallax o animaciones ligadas al desplazamiento.
- Una cuenta regresiva recurrente o sincronizada con el servidor.

## Decisions

### Pasos: lista ordenada, numeración por el navegador y no por el editor
El bloque usa `<ol>`; el número sale de `forloop.counter` y no es un campo, así que no se
desordena al mover pasos. Una línea decorativa une los pasos con CSS. Alternativa descartada:
una barra de progreso que se llena al bajar, porque exige `animation-timeline` o JavaScript
y es una decisión de diseño de cada proyecto.

### Cuenta regresiva: el servidor entrega la fecha, el navegador calcula
El template escribe la fecha límite como instante absoluto (ISO 8601 con zona) en un
atributo `data-*` y la fecha legible dentro del bloque; el componente Alpine `countdown`
calcula días, horas, minutos y segundos y actualiza el reloj cada segundo, sin consultar al
servidor (la página está en caché). El reloj es `role="timer"` y no `aria-live`: un lector de
pantalla no debe anunciar cada segundo. Pasada la fecha, el componente se detiene y muestra
el mensaje del editor o ceros. Sin JavaScript queda la fecha legible, sin un reloj vacío.
Alternativa descartada: consultar la hora del servidor, porque obliga a un endpoint y rompe
la caché de página.

### Cinta: movimiento solo si hay JavaScript y no hay movimiento reducido
La cinta se renderiza quieta, con todos sus elementos; el componente `marquee` agrega la clase
que activa el desplazamiento CSS (solo `transform`) y revela el botón de pausa, y solo cuando
`prefers-reduced-motion` no pide lo contrario. Así se cumple WCAG 2.2.2 (todo movimiento
automático se puede pausar) y no queda movimiento que el visitante no pueda detener. El bucle
duplica el grupo de elementos; la copia lleva `aria-hidden="true"`. Se pausa también con
`:hover` sobre la cinta por CSS; no lleva `:focus-within` porque la cinta no tiene elementos
enfocables (los logos no son enlaces) y el botón de pausa queda fuera de ella. La velocidad (lenta, normal, rápida) es un `ChoiceBlock`
que cambia la duración de la animación. Los logos reutilizan `LogoBlock`.

### Estructura y estilos
Los tres se registran en `ContentStreamBlock` y se exportan en `blocks/__init__.py`. Los
estilos base van en `orion.css` y se recompilan con `pipenv run css-build`. Los textos nuevos
("días", "horas", "minutos", "segundos", "Pausar la cinta", "Reanudar la cinta") van con
gettext y traducción al español.

## Risks / Trade-offs

- [Sumar bloques alarga el selector del editor] → Un proyecto con cuerpo de página propio
  elige cuáles ofrecer; queda como está, sin cambio.
- [La migración de definición afecta a los proyectos con tipos de página propios] →
  `makemigrations` genera solo la definición; se verifica en el proyecto de ejemplo y en
  Intervita, y se avisa en el CHANGELOG.
- [Un reloj que actualiza cada segundo es movimiento] → Es información, no decoración, y no
  anima a nada que se desplace; con movimiento reducido el reloj se mantiene (cambia el
  número, sin transiciones).
- [El desplazamiento de la cinta puede ser pesado con muchos logos] → Se limitan frases y
  logos del bloque y las imágenes usan los tamaños con nombre de Orion.

## Migration Plan

Una migración de definición en `orion.pages` y la del proyecto de ejemplo; ningún contenido
cambia. Los proyectos con tipos de página propios corren `makemigrations`.
