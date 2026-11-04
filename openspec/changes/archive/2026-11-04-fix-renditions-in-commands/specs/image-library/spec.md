## ADDED Requirements

### Requirement: Variants are complete when a command saves an image
Cuando una imagen se guarda fuera de una petición web, el sistema SHALL generar sus
variantes antes de que termine el guardado, para que no se pierdan al terminar el proceso.

#### Scenario: Image saved by a command
- **WHEN** un comando guarda una imagen nueva y termina
- **THEN** las variantes de todas las medidas existen y el comando no reporta errores

#### Scenario: Image saved in the admin
- **WHEN** un editor sube una imagen desde el admin
- **THEN** las variantes se generan en segundo plano, sin demorar la respuesta
