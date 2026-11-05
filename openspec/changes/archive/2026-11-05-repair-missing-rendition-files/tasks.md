## 1. Reparación

- [x] 1.1 En `generate_renditions`, tratar como faltante el recorte registrado cuyo archivo no existe en el almacenamiento: borrar su fila y regenerarlo; si la consulta al almacenamiento falla, no borrar nada y dejar que el error llegue al comando.
- [x] 1.2 Sumar los reparados al conteo que devuelve y que el comando informa.

## 2. Pruebas

- [x] 2.1 Prueba: un recorte con archivo borrado se regenera, su archivo existe y se cuenta (SVG y raster).
- [x] 2.2 Prueba: con todos los archivos presentes, el comando informa cero y no borra filas.
- [x] 2.3 Prueba: si el almacenamiento falla al consultar, el recorte no se borra y la imagen se informa como fallida.
- [x] 2.4 Ejecutar la suite completa en PostgreSQL y MySQL, y Ruff.

## 3. Cierre

- [x] 3.1 Mencionar en la ayuda del comando y en el README (si describe el comando) que también repara recortes con archivo perdido, y en CHANGELOG.
