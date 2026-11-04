## Why

No hay forma de saber, sin leer cada template y cada archivo de traducción a mano, si un
proyecto construido sobre Orion dejó un texto en inglés sin marcar para traducir, una
imagen sin texto alternativo o una traducción sin completar. Hoy el repo mismo tiene
ejemplos de los tres (ver design.md). Es el primer cambio de la Fase 6 (calidad y
documentación), antes de las pruebas de punta a punta y las guías para desarrolladores:
da una base rápida de revisar sin agregar herramientas nuevas.

## What Changes

- **Un comando (`manage.py orion_check_conventions`)** que recorre los templates y los
  archivos de traducción del proyecto (los de Orion y los del proyecto que lo instala, de
  la misma forma en que Django encuentra templates y catálogos de cualquier app) y
  reporta tres cosas, cada una con el archivo y la línea:
  - **Texto fijo en templates:** contenido visible entre etiquetas HTML que no está
    dentro de `{% trans %}`/`{% blocktrans %}`, fuera de `<script>` y `<style>`.
  - **Imágenes sin texto alternativo:** una etiqueta `<img>` sin `alt`, o un llamado a
    `{% responsive_image %}` sin el argumento `alt` o con `alt=""`.
  - **Traducciones faltantes:** entradas de un archivo `.po` con `msgstr` vacío o
    marcadas `fuzzy` (sin contar el encabezado del archivo).
- El comando solo reporta: termina con código de salida 0 tenga o no hallazgos, igual que
  `orion_unused_images`. No bloquea nada ni se agrega a ningún chequeo automático todavía.
- No se corrige ningún hallazgo existente en este cambio (ver Fuera del alcance).

**Fuera del alcance:** traducir o corregir lo que el comando encuentre hoy en Orion (el
repo ya tiene texto en inglés sin traducir en varios módulos; queda como deuda conocida,
listada por el propio comando, para resolver aparte); un modo que falle con código de
salida distinto de cero (`--strict` o similar, para usarlo como gate de CI); revisar
atributos además del texto visible y `alt` (`title`, `aria-label`, `placeholder`);
detectar texto fijo dentro de literales pasados como argumento a otras etiquetas de
template; integración con editores o con el admin.

## Capabilities

### New Capabilities
- `conventions-check`: comando que detecta texto fijo sin marcar para traducir, imágenes
  sin texto alternativo y traducciones faltantes, en los templates y catálogos del
  proyecto.

### Modified Capabilities
(ninguna: no cambia ningún requisito existente)

## Impact

- **Código nuevo:** comando de gestión, módulo de análisis de templates y de archivos
  `.po`, pruebas.
- **Código modificado:** ninguno (no toca lo que ya existe; el hallazgo de traducciones
  faltantes en Orion mismo queda como lo encuentra el comando, sin tocarlas).
- **Dependencias nuevas:** ninguna (ver justificación en design.md).
- **Migraciones:** ninguna.
- **Compatibilidad:** ninguna: es un comando nuevo que solo lee.
