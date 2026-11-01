# Spec Delta

## Purpose

Define cómo se trabajan los envíos de los formularios en el admin: estado, notas,
búsqueda y exportación, y cuánto tiempo se guardan los envíos y sus archivos.

## ADDED Requirements

### Requirement: Submissions have a status
Cada envío SHALL tener un estado: nuevo (al llegar), leído o respondido. Abrir el detalle
de un envío nuevo SHALL marcarlo leído. Desde el detalle SHALL poder cambiarse a
cualquier estado. La lista de envíos de un formulario SHALL mostrar el estado y poder
filtrarse por él.

#### Scenario: New submission
- **WHEN** llega un envío de "Contacto"
- **THEN** figura como nuevo en la lista

#### Scenario: Opened
- **WHEN** una Administradora abre su detalle
- **THEN** pasa a leído

#### Scenario: Pending filter
- **WHEN** filtra por "Nuevo"
- **THEN** ve solo los envíos que nadie abrió

### Requirement: Submissions have internal notes
El detalle de un envío SHALL mostrar todos sus datos, los adjuntos para descargar y las
notas internas, y permitir agregar una nota, que SHALL guardar su autor y su fecha. Las
notas MUST NOT mostrarse al visitante ni enviarse por email.

#### Scenario: Note
- **WHEN** un editor anota "Llamé, vuelve a escribir el lunes"
- **THEN** la nota figura en el detalle con su nombre y la fecha

### Requirement: Submissions can be searched
La lista de envíos de un formulario SHALL buscar un texto en los datos de los envíos,
combinable con el filtro por fecha y por estado.

#### Scenario: By email
- **WHEN** se busca "ana@example.com"
- **THEN** la lista muestra los envíos que contienen ese email

### Requirement: Exports are clean
La exportación CSV y Excel de un formulario SHALL incluir la fecha, el estado y cada
campo, con los adjuntos como nombre de archivo (nunca HTML), respetando la búsqueda y
los filtros aplicados.

#### Scenario: Export with a CV
- **WHEN** se exporta "Trabajá con nosotros" a Excel
- **THEN** la columna del CV tiene el nombre del archivo y hay una columna de estado

### Requirement: Submissions are kept for a limited time
Los envíos más viejos que el plazo configurado (12 meses por defecto) SHALL borrarse, con
sus adjuntos, al correr el comando de retención, pensado para un cron diario. Sin plazo
configurado, el comando MUST NOT borrar nada. El comando SHALL informar cuántos envíos y
archivos borró.

#### Scenario: Old submission
- **WHEN** el comando corre y hay un envío de hace 13 meses con un CV
- **THEN** el envío y el archivo del CV dejan de existir

#### Scenario: Recent submission
- **WHEN** hay un envío de hace 11 meses
- **THEN** sigue ahí

### Requirement: Deleting a submission deletes its files
Borrar un envío, uno o varios desde la lista o al borrar la página del formulario,
SHALL borrar sus adjuntos del almacenamiento privado.

#### Scenario: Bulk delete
- **WHEN** una Administradora borra tres envíos con CV desde la lista
- **THEN** los tres archivos dejan de existir
