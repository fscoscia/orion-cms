# conventions-check Specification

## Purpose

Detecta, en los templates y los archivos de traducción de un proyecto construido sobre
Orion, texto fijo sin marcar para traducir, imágenes sin texto alternativo y traducciones
sin completar, para que el equipo las revise antes de publicar.

## Requirements

### Requirement: A command reports hardcoded text in templates
Un comando SHALL recorrer los templates del proyecto (los de Orion y los del proyecto que
la instala) y reportar, con archivo y línea, el texto visible entre etiquetas HTML que no
está dentro de `{% trans %}` ni `{% blocktrans %}`, sin contar lo que esté dentro de
`<script>` o `<style>` ni los espacios en blanco.

#### Scenario: Texto sin marcar
- **WHEN** un template tiene `<p>Hello world</p>` fuera de cualquier bloque de traducción
- **THEN** el comando lo reporta con el archivo y la línea

#### Scenario: Texto marcado para traducir
- **WHEN** el mismo texto está dentro de `{% blocktrans %}` o pasado a `{% trans %}`
- **THEN** el comando no lo reporta

### Requirement: A command reports images without alternative text
Un comando SHALL reportar, con archivo y línea, una etiqueta `<img>` sin el atributo
`alt`, y un llamado a la etiqueta de template que arma imágenes responsivas sin el
argumento `alt` o con `alt=""`.

#### Scenario: Imagen sin alt
- **WHEN** un template tiene `<img src="...">` sin `alt`
- **THEN** el comando lo reporta

#### Scenario: Imagen con alt
- **WHEN** la misma etiqueta tiene `alt="Algo"`, o el llamado a la etiqueta de imágenes
  responsivas pasa `alt` con un valor no vacío
- **THEN** el comando no la reporta

### Requirement: A command reports incomplete translations
Un comando SHALL recorrer los archivos `.po` del proyecto (los de Orion y los del
proyecto que la instala) y reportar, con archivo y línea, cada entrada con `msgstr` vacío
o marcada `fuzzy`, sin contar el encabezado del archivo.

#### Scenario: Entrada sin traducir
- **WHEN** un archivo `.po` tiene una entrada con `msgstr ""`
- **THEN** el comando la reporta

#### Scenario: Entrada dudosa
- **WHEN** una entrada está marcada `#, fuzzy`
- **THEN** el comando la reporta

#### Scenario: Entrada completa
- **WHEN** una entrada tiene `msgstr` con texto y no está marcada `fuzzy`
- **THEN** el comando no la reporta

### Requirement: The command only reports; it never fails
El comando MUST terminar siempre con código de salida 0, haya o no hallazgos: es
informativo, no un gate que bloquee nada.

#### Scenario: Con hallazgos
- **WHEN** el comando encuentra texto fijo, imágenes sin alt o traducciones faltantes
- **THEN** los imprime y termina con código de salida 0

#### Scenario: Sin hallazgos
- **WHEN** el comando no encuentra nada que reportar
- **THEN** lo informa y termina con código de salida 0
