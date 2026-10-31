# articles Specification

## Purpose
Define los artículos (novedades, blog) y sus listados: qué carga el editor, cómo se ordenan,
paginan y filtran, cómo se suscribe un lector por RSS y cómo se muestran los más recientes
en otras páginas.

## Requirements

### Requirement: Articles have a date, a summary and an image
Cada artículo SHALL tener una fecha, un resumen, una imagen opcional con texto alternativo
traducible, categorías, etiquetas y un cuerpo de bloques. La fecha SHALL proponerse con el
día de creación y el editor SHALL poder cambiarla.

#### Scenario: New article
- **WHEN** un editor crea un artículo
- **THEN** la fecha viene cargada con el día de hoy y el resumen se usa en los listados

### Requirement: Listings show their articles newest first
Un Listado de artículos SHALL mostrar los artículos publicados que contiene, en el idioma
de la visita, del más reciente al más antiguo según su fecha, en páginas de un tamaño fijo
con enlaces a la página anterior y la siguiente.

#### Scenario: Second page
- **WHEN** un listado tiene más artículos que el tamaño de página y se visita `?page=2`
- **THEN** se muestran los artículos siguientes y un enlace a la página anterior

#### Scenario: Unpublished article
- **WHEN** un artículo se despublica
- **THEN** el listado deja de mostrarlo

#### Scenario: Page number out of range
- **WHEN** se visita una página del listado que no existe, como `?page=99`
- **THEN** se muestra la última página, sin error

### Requirement: Listings filter by category and tag
Un listado SHALL filtrarse por una categoría o por una etiqueta. El filtro por una
categoría SHALL incluir los artículos de sus subcategorías, y un listado filtrado SHALL
indicar el filtro activo y ofrecer quitarlo.

#### Scenario: Filtering by a parent category
- **WHEN** se filtra por "Salud", que tiene la subcategoría "Prevención"
- **THEN** el listado muestra los artículos de "Salud" y los de "Prevención"

#### Scenario: Unknown filter
- **WHEN** se filtra por una categoría que no existe
- **THEN** el listado responde 404

### Requirement: Listings offer an RSS feed per language
Cada listado SHALL ofrecer un feed RSS con sus artículos publicados más recientes en el
idioma de la URL, con título, resumen, enlace y fecha, y SHALL anunciarlo en el HTML del
listado.

#### Scenario: Subscribing in English
- **WHEN** un lector abre el feed del listado en `/en/news/rss/`
- **THEN** recibe los artículos publicados en inglés, con enlaces a `/en/news/...`

### Requirement: Latest articles can be shown in any page body
El cuerpo de las páginas SHALL ofrecer un bloque "Últimas novedades" que muestre los
artículos publicados más recientes en el idioma de la visita, de todos los listados o de
uno elegido, con una cantidad elegida por el editor. Sin artículos para mostrar, el bloque
MUST NOT mostrarse.

#### Scenario: Home page news
- **WHEN** la Portada tiene el bloque con cantidad 3 y hay cinco artículos publicados
- **THEN** la Portada muestra los tres más recientes con su fecha, imagen y resumen

#### Scenario: Listing chosen in another language
- **WHEN** el bloque elige el listado "Novedades" y se visita `/en/`
- **THEN** muestra los artículos del listado traducido en inglés
