# Trabajar con IA sobre Orion

Para quien construye un sitio sobre Orion con un asistente de código (Claude Code u otro).
Orion resuelve lo estructural; la IA acelera el diseño y los bloques propios. Esta guía dice
cómo repartir el trabajo, qué skills usar en cada fase y qué revisar siempre a mano.

Un proyecto generado con `orion-start` trae un `AGENTS.md` con las reglas esenciales. Esta
guía las explica y suma lo que no cabe allí. Para instalar Orion, crear el proyecto y
comprobar que el asistente cargó esas reglas, empezar por [Empezar](empezar.md); para el CSS,
los estilos de bloque y las imágenes, ver [Estilos y diseño](estilos-y-diseno.md); para el
favicon, la imagen para redes y los buscadores, [Identidad y SEO](identidad-y-seo.md); para
que el asistente consulte el sitio, [Usar el MCP](usar-el-mcp.md).

## 1. Qué le toca a cada uno

| Orion (ya resuelto) | Proyecto (donde ayuda la IA) |
|---|---|
| Admin, permisos, SEO, formularios, caché, seguridad | Diseño: tokens, CSS y templates sobrescritos |
| Bloques de contenido y sus campos | Bloques propios, cuando el diseño los pide |
| Accesibilidad de lo que ya trae (pausa de la cinta, temporizador, títulos) | Accesibilidad de lo propio |

La IA empieza leyendo el `AGENTS.md` del proyecto. Si el agente no lo carga solo, hay que
indicárselo.

### Formularios

Los formularios no se programan: se crean desde el admin como una página de tipo
**Formulario**, con sus campos, su texto de agradecimiento y el aviso por email, y Orion ya
agrega el consentimiento y el campo trampa para bots. El paso a paso está en [Crear un
formulario](crear-un-formulario.md). El reparto:

- **El asistente** propone los campos, los textos y a qué email avisa cada formulario, a partir
  del diseño y del contenido. No se le pide escribir esos datos en la base.
- **Una persona** los carga en el admin y elige la página de política de privacidad (una sola
  vez, en Datos del sitio).

```text
Con el diseño [enlace de Figma] y docs/contenido.md, lista los formularios del sitio:
campos, tipo, si es requerido, texto de agradecimiento y a qué email avisa. Una tabla por
formulario, para cargarla en el admin. No escribas código.
```

Un formulario se da por listo cuando se envió uno real como visitante: queda en la bandeja de
**Envíos** y el aviso llega a una casilla fuera de spam. Si no hay SMTP configurado, el aviso
no sale (el panel de integraciones del admin lo muestra) aunque el envío quede guardado.

## 2. Bloques de Orion o propios

Un sitio hecho solo con bloques de Orion sale coherente, pero más plano. Las composiciones y
los comportamientos propios mejoran mucho el diseño, a cambio de mantenerlos. El criterio:

| Situación | Qué usar |
|---|---|
| El contenido tiene la forma de un bloque de Orion y el aspecto se logra con CSS, un estilo de bloque o un template propio | Bloque de Orion |
| El diseño necesita datos que el bloque no tiene: un campo más por elemento (una etiqueta, una segunda imagen, un enlace) | Bloque propio |
| El diseño necesita un comportamiento propio: una interacción o animación atada al scroll, al puntero o al tiempo | Bloque propio |
| El diseño necesita una composición que Orion no ofrece: una columna fija junto a contenido que se desplaza, una disposición que no es una rejilla | Bloque propio |
| Pieza común del sitio: texto, imagen, botones, formulario, mapa | Bloque de Orion |

- Cada bloque propio lleva en su clase una línea que dice qué necesita que Orion no ofrece. Si
  no se puede escribir, no hace falta el bloque.
- Si un patrón se repite en varios proyectos, es candidato a pasar a Orion: se propone como
  cambio y deja de mantenerse en cada sitio.
- Para crear uno, seguir [Crear un bloque de contenido propio](crear-un-bloque.md).

## 3. Las skills, por fase

Se probaron con Orion en noviembre de 2026. Las versiones observadas están entre paréntesis;
cambian por su cuenta, así que conviene revisarlas antes de apoyarse en ellas.

| Fase | Skill | Para qué |
|---|---|---|
| Estructura | Ninguna | Mapear el contenido a bloques de Orion tal cual, con el `AGENTS.md` y las guías |
| Dirección | **Impeccable** (`init`, `concept-seed`, `overdrive`) o **taste** (`deal`) | Impeccable: producto, usuario y dirección visual a fondo; `overdrive` propone cuán lejos ir y espera una elección. Taste: paleta y tipografía rápido. Se elige **una** de las dos para decidir la dirección; la otra solo verifica |
| Construcción | La IA con Orion | Bloques de Orion, más CSS y bloques propios según la sección 2 |
| Refinado | **Impeccable** (`critique`, `typeset`, `layout`, `polish`) | De una sección por vez |
| Movimiento | **Emil Kowalski** (`animate`, `find-animation-opportunities`) | Dónde animar, con qué curva y duración, y qué no animar. Va al final |
| Verificación | `impeccable detect`, `perf` de taste y la revisión manual | Ver la sección 5 |

Una skill por fase: cargar varias a la vez hace que el agente mezcle sus reglas. La
estructura y la construcción no necesitan skill. Con un diseño ya definido (Figma), la
dirección tampoco: ya está decidida. Cuando solo hay referencias o ningún diseño, la skill de
dirección **propone** y **una persona aprueba** antes de aplicar nada; ver [Estilos y
diseño](estilos-y-diseno.md#si-todavía-no-hay-diseño).

### Qué se probó y qué no

- **Taste** (`design-taste-frontend`, v2): `deal` dio una paleta y una tipografía coherentes en
  un paso, y `perf` es fiable. Su `consistency` mezcla defectos reales (contraste sobre foto,
  imágenes ampliadas, jerarquía de títulos, contenido que queda oculto, botones inconsistentes)
  con reglas propias de taste (altura de las secciones, `.wrap`, tarjetas distintas entre sí,
  copy) que no encajan con el marcado de Orion. Usarlo como informe y filtrar. No dejar que
  decida la estructura de la página.
- **Taste en un proyecto real (Bolt Emprende):** se usó solo para la dirección de arte, no
  para armar la página. `deal` repartió la paleta y la tipografía, y `css` generó los tokens
  de color y de fuente. No se encargó de la estructura.
- **Impeccable** (4.8.0, motor 0.1.18): `init`, `concept-seed`, `overdrive` y `detect`
  funcionaron. `detect` encontró un error de JavaScript que el HTML no mostraba. Su `critique`
  pide subagentes aislados; sin ellos es una crítica en un solo contexto (degradada). No se
  probaron `polish`, `typeset` ni `layout` por separado, ni su hook de revisión por edición.
- **Emil Kowalski:** sirve para filtrar qué no animar y da curvas y duraciones exactas. Se
  aplicó leyendo las tablas de su skill `animate`.

### Antes de instalar una skill de terceros

El instalador de impeccable descarga un binario y su telemetría viene activada. Antes de usarla:

1. Verificar el hash del binario contra el que publica el propio paquete (`engine-checksums.txt`).
2. Apagar la telemetría: `DO_NOT_TRACK=1` e `IMPECCABLE_NO_TELEMETRY=1` en cada comando.
3. Instalarla solo en el proyecto donde se usa, nunca dentro de Orion.

### Instalar una skill en el proyecto

Requiere Node.js 20.19 o más. Desde la raíz del proyecto (nunca desde el repositorio de Orion),
con la telemetría apagada en el mismo comando, por ejemplo para impeccable:

```bash
DO_NOT_TRACK=1 IMPECCABLE_NO_TELEMETRY=1 npx impeccable@latest install
```

Las skills quedan en `.agents/skills/` del proyecto. Antes de usarlas, verificar el binario
(punto 1 de arriba) y decidir con el equipo si `.agents/` se versiona o se ignora. Cada skill
trae sus propios comandos; los de impeccable que se probaron están en la sección anterior.

## 4. Choques entre skills y cómo resolverlos

- **Movimiento al entrar en pantalla:** taste lo prohíbe en páginas que no son tecnológicas,
  Emil lo recomienda e impeccable descarta una misma entrada repetida en cada sección. Se
  decide como producto, se escribe en `DESIGN.md` y no se enciende `ORION_BLOCK_REVEAL`. Es
  mejor un movimiento puntual que una entrada repetida.
- **Dos autoridades visuales:** si dos skills deciden la paleta, el resultado es incoherente.
  La dirección la decide una y la otra solo verifica.
- **Etiquetas sobre los títulos:** impeccable las prohíbe y Orion las ofrece (`eyebrow`, `tag`).
  Dejarlas vacías salvo que el contenido las pida.
- **Reglas pensadas para otro marcado:** muchos avisos de `consistency` suponen una estructura
  distinta a la de Orion. Contrastarlos con el `AGENTS.md` antes de "corregirlos".

## 5. Qué revisar siempre a mano

- **Navegador, recorriendo la página entera.** Las imágenes con carga perezosa no cargan si
  solo se mira el HTML o la primera pantalla. Mirar a 390 y a 1280 px y esperar a que se
  decodifiquen las imágenes antes de capturar.
- **Accesibilidad:** contraste del texto sobre fotos, `alt`, orden de títulos, foco visible y
  movimiento pausable.
- **Rendimiento:** LCP, cambio de diseño y que la imagen de la portada tenga el tamaño correcto.
  Las tipografías de Google pueden mover el diseño en una carga en frío: medirlo con un perfil
  limpio.
- **Contenido real:** todo texto del diseño es un campo editable y se puede cargar desde cero,
  no solo con el contenido de demostración.
- **Formato:** las cifras con el formato del idioma del sitio (en español, `2.200`). El bloque
  de estadísticas de Orion muestra el número sin separador de miles; un bloque propio con
  texto sí puede.
- **Textos de relleno:** enlaces a `example.com`, teléfonos y correos de prueba.
- **Formularios:** un envío real de cada uno, en la bandeja y en el email.
- **Identidad y SEO:** favicon, imagen para redes, título y descripción de cada página; ver
  [Identidad y SEO](identidad-y-seo.md).

## 6. Problemas típicos de los bloques propios con IA

- **Clave que choca:** si Orion incorpora un bloque con la clave de uno propio, gana el propio
  sin avisar. Comparar las claves al actualizar.
- **Quitar un bloque con contenido:** Wagtail descarta el contenido de un bloque que ya no
  está declarado. Respaldar y migrar antes. Pedirle a la IA que nunca elimine un bloque ni
  renombre una clave sin una migración de datos y un respaldo.
- **Duplicar lo que Orion ya hace:** que compare con la lista de bloques antes de crear uno.
- **Componentes de Alpine con el nombre de los de Orion:** se pisan y falla sin avisar. Usar un
  prefijo del proyecto.
- **CSS dentro de `@layer`:** pierde contra las utilidades de Tailwind de los templates de
  Orion. El CSS propio va fuera de cualquier capa.
- **Imágenes cortadas:** las tarjetas y los pasos se recortan a 8:5 en el servidor (la
  rendición `card`). Para ilustraciones, declarar un tamaño sin recorte en `ORION_IMAGE_SIZES`
  y encuadrar con CSS; después correr `orion_generate_renditions`.
- **Portada propia:** Orion solo reconoce como portada un bloque con la clave `hero`. Con otra
  clave la página repite el título y pierde la precarga de la imagen principal y la imagen
  para redes. Registrar la portada propia con esa clave reemplaza a la de Orion, a propósito.
- **Anclas duplicadas:** el contenedor de Orion ya dibuja el `id`; el template no lo repite.

## 7. Actualizar Orion en un proyecto con bloques propios

1. Leer el CHANGELOG de Orion y comprobar que ninguna clave nueva de bloque choque con las
   propias.
2. Correr `makemigrations --check` y `migrate`. Los bloques nuevos de Orion traen migraciones
   de definición del campo `body`; no tocan el contenido.
3. Abrir la portada y revisar que los bloques propios sigan viéndose bien.

## 8. Cómo pedir bien

Dar el objetivo, qué bloque de Orion se espera usar (o por qué hace falta uno propio), qué no
tocar, cómo comprobar el resultado ("abrilo a 390 y 1280 px, recorriendo la página, y pasa
`orion_check_conventions`") y que informe lo que no pudo verificar. Pedir una sección por vez y
revisarla antes de seguir.

## 9. Qué nunca delegar sin revisión

Migraciones, borrado de datos, ajustes de seguridad, claves y variables de entorno, y
publicación o cambios de dominio.
