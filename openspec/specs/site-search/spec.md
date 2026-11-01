# site-search Specification

## Purpose
Define el buscador público del sitio: qué contenido encuentra, cómo trata el idioma y los
errores de tipeo, cómo se muestran los resultados, cómo los ordena el editor y qué informe
recibe de las búsquedas.

## Requirements

### Requirement: Search finds the text of pages and articles
La búsqueda SHALL encontrar páginas, artículos, listados y formularios por su título, su
descripción, su resumen o introducción y el texto de los bloques de su cuerpo. SHALL
devolver solo páginas publicadas, públicas y del idioma de la visita, y MUST NOT devolver
páginas marcadas para no indexar.

#### Scenario: Text inside a block
- **WHEN** alguien busca "radiografías" y esa palabra solo está en un bloque de texto de
  "Servicios"
- **THEN** "Servicios" aparece en los resultados

#### Scenario: Other language
- **WHEN** alguien busca en `/en/search/` una palabra que solo está en la versión en
  español
- **THEN** no aparece ningún resultado en español

#### Scenario: Draft
- **WHEN** una palabra solo está en un borrador sin publicar
- **THEN** la búsqueda no lo encuentra

### Requirement: Search understands Spanish and tolerates typos when possible
En PostgreSQL la búsqueda SHALL usar la configuración de idioma del idioma base del
sitio (español por defecto), para que plurales y variantes coincidan; el proyecto SHALL
poder cambiarla. Si la base tiene la extensión de trigramas activa y una búsqueda no da
resultados, SHALL repetirse en forma aproximada. Sin la extensión, la búsqueda MUST
seguir funcionando sin la parte aproximada. En MySQL SHALL usar la búsqueda de texto
completo de MySQL.

#### Scenario: Plural
- **WHEN** en PostgreSQL alguien busca "médicos" y la página dice "médico"
- **THEN** la página aparece

#### Scenario: Typo with the extension
- **WHEN** la extensión está activa y alguien busca "radiografais"
- **THEN** aparecen las páginas sobre radiografías

### Requirement: The results page shows paginated results by type
La página de resultados SHALL estar en `/buscar/` para el idioma base y en la ruta
traducida de cada idioma, SHALL mostrar cada resultado con su título enlazado, un
resumen y su tipo, de a 10 por página, y SHALL permitir filtrar por tipo (páginas o
artículos). Sin término de búsqueda SHALL mostrar solo el formulario; sin resultados,
un mensaje. La página MUST NOT indexarse.

#### Scenario: Results
- **WHEN** alguien busca "turnos"
- **THEN** ve los resultados con título, resumen y tipo, y el término en el campo

#### Scenario: Only articles
- **WHEN** filtra por "Artículos"
- **THEN** solo ve artículos

#### Scenario: Nothing found
- **WHEN** busca algo que no existe
- **THEN** ve un mensaje que lo dice y sugiere revisar la escritura

### Requirement: The header offers search
El encabezado SHALL incluir un formulario de búsqueda accesible (con etiqueta y botón)
que lleva a la página de resultados del idioma de la visita; en el celular SHALL estar
dentro del menú. Un proyecto SHALL poder quitarlo con un ajuste.

#### Scenario: From any page
- **WHEN** alguien escribe "turnos" en el buscador del encabezado
- **THEN** llega a la página de resultados de su idioma con esa búsqueda

### Requirement: Editors promote results
Editores y Administradores SHALL poder elegir, para un término de búsqueda, qué páginas
aparecen primero, con un texto opcional. Esas páginas SHALL encabezar los resultados,
marcadas como destacadas, aunque la búsqueda normal no las encuentre.

#### Scenario: Promoted page
- **WHEN** una editora destaca "Turnos online" para "turnos"
- **THEN** quien busca "turnos" la ve primero, marcada como destacada

### Requirement: Administrators see what visitors search
Cada búsqueda con término SHALL registrarse. Un informe en Informes SHALL mostrar las
búsquedas más frecuentes de los últimos 30 días y las búsquedas que no dieron
resultados, con su cantidad (y, en las segundas, la fecha de la última), para los
administradores del sitio (Informes es solo para ellos desde la Fase 2).

#### Scenario: No results
- **WHEN** tres personas buscan "estacionamiento" y no hay resultados
- **THEN** el informe de búsquedas sin resultados muestra "estacionamiento" con 3
