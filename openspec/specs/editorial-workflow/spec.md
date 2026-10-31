# editorial-workflow Specification

## Purpose
Define cómo se programa y se da de baja el contenido, cómo se ve lo programado en un
calendario, cómo se avisa si la publicación programada no está corriendo, y qué garantiza
Orion del autoguardado y de los avisos por email del flujo de aprobación.

## Requirements

### Requirement: The admin has a publication calendar
El admin SHALL ofrecer un calendario mensual, en el menú lateral, con las páginas
programadas para publicarse y las páginas publicadas que tienen fecha de baja, cada una
en el día de su fecha y con enlace a su edición. Cada usuario MUST ver solo las páginas
que puede editar. El calendario SHALL permitir pasar al mes anterior y al siguiente y
volver al mes actual, y en pantallas chicas MUST mostrarse como una lista por día sin
desbordar el ancho.

#### Scenario: Scheduled publication
- **WHEN** una Administradora aprueba un cambio de "Nosotros" programado para el 12 de
  noviembre y abre el calendario de noviembre
- **THEN** "Nosotros" aparece el día 12 como publicación programada, con enlace a su
  edición

#### Scenario: Expiry date
- **WHEN** una página publicada tiene fecha de baja el 20 de noviembre
- **THEN** aparece el día 20 como baja programada

#### Scenario: Pages the user cannot edit
- **WHEN** un usuario de un grupo limitado a Novedades abre el calendario
- **THEN** no ve las páginas programadas fuera de Novedades

#### Scenario: Changing month
- **WHEN** el usuario pasa al mes siguiente
- **THEN** ve lo programado en ese mes y puede volver al mes actual

#### Scenario: Invalid month in the address
- **WHEN** alguien abre el calendario con un mes que no existe en la dirección
- **THEN** ve el mes actual

### Requirement: A stopped scheduled publishing is visible
Si hay páginas cuya publicación o baja programada venció hace más de una hora y no se
aplicó, el admin SHALL avisar a los administradores del sitio, en el panel de inicio y
en el calendario, que la tarea periódica de publicación no está corriendo. En el
calendario, esas entradas MUST mostrarse como atrasadas para todos.

#### Scenario: Cron not running
- **WHEN** una página debía publicarse hace dos horas y sigue sin publicar
- **THEN** una Administradora ve el aviso en el panel de inicio y en el calendario

#### Scenario: Recently due
- **WHEN** una página debía publicarse hace diez minutos
- **THEN** no hay aviso (la tarea corre cada pocos minutos)

#### Scenario: Editor
- **WHEN** un editor abre el panel de inicio en esa situación
- **THEN** no ve el aviso, y en el calendario ve la entrada marcada como atrasada

#### Scenario: Cron applied
- **WHEN** la tarea periódica publica la página
- **THEN** el aviso desaparece

### Requirement: Autosave is on
El editor de páginas SHALL guardar el borrador solo mientras se edita, sin publicar, y
mostrar su estado. Un proyecto MAY cambiar el intervalo o apagarlo con
`WAGTAIL_AUTOSAVE_INTERVAL`.

#### Scenario: Editing without saving
- **WHEN** un editor cambia el título de una página y no aprieta "Guardar borrador"
- **THEN** el cambio queda guardado como borrador y lo publicado no cambia

### Requirement: The approval flow notifies by email
Cuando un editor envía una página a revisión, los administradores del sitio que deben
aprobar SHALL recibir un email, y el autor SHALL recibir otro cuando se aprueba o se
rechaza, siempre que el servidor de email esté configurado. Los enlaces del email MUST
apuntar a la dirección del admin del sitio.

#### Scenario: Submitted for review
- **WHEN** un editor envía "Nosotros" a revisión
- **THEN** cada Administrador con email recibe un aviso con el enlace a la revisión

#### Scenario: Changes requested
- **WHEN** una Administradora rechaza el cambio con un comentario
- **THEN** el editor recibe un email con el aviso
