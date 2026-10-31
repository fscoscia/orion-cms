# Spec Delta

## MODIFIED Requirements

### Requirement: Blocks explain themselves in the editor
Cada bloque SHALL mostrarse en el selector con un nombre en el idioma del admin, un ícono,
una descripción de para qué sirve y una vista previa con contenido de ejemplo y los
estilos del sitio. Los bloques que muestran imágenes o artículos SHALL usar en su vista
previa imágenes y artículos de ejemplo que trae Orion, y la vista previa MUST NOT agregar
imágenes a la biblioteca ni crear páginas.

#### Scenario: Choosing a block
- **WHEN** un editor abre el selector de bloques
- **THEN** cada bloque muestra su nombre, su descripción y una vista previa

#### Scenario: Gallery preview on a new site
- **WHEN** un editor de un sitio sin imágenes cargadas mira la vista previa de la Galería
- **THEN** ve la galería con las imágenes de ejemplo de Orion y la biblioteca de imágenes
  sigue vacía
