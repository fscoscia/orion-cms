# Crear un formulario

Para una persona editora, desde el admin de Wagtail. Un formulario es una página más
(una página de tipo "Formulario"): se crea, se completa y se publica como cualquier
otra página, sin escribir código.

## 1. Antes de empezar: la política de privacidad

El formulario pide aceptar una política de privacidad. Esa página se elige una sola
vez para todo el sitio, en **Propiedades → Datos del sitio**, campo "Página de
política de privacidad". Si no está elegida, el formulario muestra el texto de
consentimiento sin el enlace.

## 2. Crear la página

1. En el explorador de páginas, ubicarse bajo la página de inicio o una página de
   contenido (un formulario no puede tener subpáginas).
2. "Agregar página hija" → elegir el tipo **Formulario**.
3. Completar el título (por ejemplo, "Contacto") y, si se quiere, una introducción
   (texto que aparece arriba del formulario).

## 3. Agregar los campos

En la misma pestaña ("Contenido"), la sección "Campos" (botón "Añadir Campos")
permite agregar uno por uno, con arrastrar y soltar para ordenarlos. Para cada campo:

- **Rótulo**: lo que ve la persona que completa el formulario (por ejemplo,
  "Nombre").
- **Tipo de campo**: texto de una línea, texto de varias líneas, email, teléfono,
  número, lista desplegable, opciones (radio), casillas, casilla, fecha o archivo.
- **Requerido**: si hay que completarlo para poder enviar.
- **Opciones**: para lista desplegable, opciones o casillas, una por línea.
- **Valor por defecto**: opcional, lo que trae completado de entrada.
- **Texto de ayuda**: aclaración que se muestra debajo del campo.

No hace falta agregar un campo de consentimiento ni un campo "trampa" para bots: el
formulario ya los agrega solo, igual que el botón de enviar.

## 4. Qué pasa al enviar ("Después de enviar")

En la pestaña "Después de enviar":

- **Texto de agradecimiento**: lo que ve la persona que envió el formulario, si no se
  elige una página después de enviar.
- **Página después de enviar**: opcional; si se elige, en vez del texto de
  agradecimiento el visitante va a esa página (por ejemplo, una página de "Gracias"
  con más contenido).

## 5. Avisos por email ("Email")

- **A dirección**: la dirección que recibe un aviso por cada envío. Dejarlo vacío si
  no se quiere ningún aviso por email (los envíos de todas formas quedan guardados).
- **Asunto**: el asunto del email de aviso.
- **Nombre del remitente** y **Desde dirección**: opcionales, para identificar el
  remitente del aviso.

El envío por SMTP tiene que estar configurado para que salgan los avisos (ver
README, "Integraciones"); si no, revisar el panel de estado del SMTP.

## 6. Publicar

Como cualquier página: "Publicar" en el menú de acciones. El formulario queda
disponible en su URL de inmediato.

## 7. Dónde quedan los envíos

Cada formulario tiene su propia bandeja: en el admin, dentro de la página del
formulario, "Envíos" (o desde el menú lateral "Formularios"). Ahí se puede:

- Ver cada envío completo, con sus adjuntos para descargar.
- Marcarlo como leído o respondido, y agregar notas internas (no las ve el visitante).
- Buscar y filtrar por fecha o estado.
- Exportar a CSV o Excel.

Los envíos se guardan por 12 meses por defecto (configurable); pasado ese plazo, un
comando programado los borra junto con sus adjuntos.

## 8. Verificar

- Completar el formulario publicado como lo haría un visitante y enviarlo: se ve el
  texto de agradecimiento o la página después de enviar que se haya elegido.
- El envío aparece en la bandeja, y llega el aviso por email si se completó "A
  dirección".
- Un envío sin completar un campo obligatorio muestra su error y no se envía.
