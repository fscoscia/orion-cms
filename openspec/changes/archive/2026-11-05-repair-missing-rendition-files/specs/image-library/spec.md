## MODIFIED Requirements

### Requirement: Variants are generated when an image is uploaded
Al subir una imagen, cambiar su archivo o su punto focal, Orion SHALL generar en segundo
plano los recortes de todas las medidas, sin demorar la respuesta del admin. Un comando
SHALL generar los recortes que falten de todas las imágenes, y SHALL considerar faltante un
recorte registrado cuyo archivo no exista en el almacenamiento, regenerándolo. Si un recorte
falta igual al mostrar la página, la página SHALL mostrarse generándolo en el momento.

#### Scenario: Upload
- **WHEN** un editor sube una foto
- **THEN** poco después existen sus recortes AVIF y WebP de todas las medidas

#### Scenario: Existing library
- **WHEN** el desarrollador corre el comando en un sitio con imágenes subidas antes
- **THEN** se generan los recortes faltantes y el comando informa cuántos creó

#### Scenario: Rendition whose file was lost
- **WHEN** un recorte figura en la base de datos pero su archivo no existe en el almacenamiento y el desarrollador corre el comando
- **THEN** el recorte se regenera, su archivo existe y el comando lo cuenta entre los creados

#### Scenario: Complete library
- **WHEN** todos los recortes tienen su archivo y el desarrollador vuelve a correr el comando
- **THEN** no se crea ni se borra ningún recorte y el comando informa cero
