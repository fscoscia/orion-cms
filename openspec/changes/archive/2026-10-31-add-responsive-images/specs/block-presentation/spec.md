## MODIFIED Requirements

### Requirement: Images are responsive and lightweight
Las imágenes de los bloques SHALL servirse en AVIF, con WebP de respaldo, en varias
medidas para que el navegador elija la adecuada, SHALL declarar ancho y alto y SHALL
cargarse en forma diferida, salvo la imagen del Hero, que se carga de inmediato con
prioridad alta. Cuando el primer bloque de una página es un Hero con imagen, la página
SHALL precargar esa imagen. Una imagen decorativa SHALL tener texto alternativo vacío.

#### Scenario: Gallery images
- **WHEN** una página tiene una Galería
- **THEN** cada imagen es un `<picture>` con una fuente AVIF con `srcset` y un `<img>` de
  respaldo con `srcset` en WebP, `width`, `height` y `loading="lazy"`

#### Scenario: Hero image
- **WHEN** una página empieza con un Hero con imagen
- **THEN** la imagen no es diferida, tiene `fetchpriority="high"` y el `<head>` la
  precarga en AVIF con las mismas medidas

#### Scenario: Decorative image
- **WHEN** una imagen está marcada como decorativa
- **THEN** su `alt` está vacío
