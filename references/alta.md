---
title: Alta de una oposición
description: Procedimiento para crear, validar y actualizar el perfil de una oposición sin tocar el núcleo versionado. Es el paso nuevo que convierte la skill en reutilizable.
idioma: es-ES
capa: núcleo
---

# Alta de una oposición

Crear un perfil es la operación que hace que esta skill sirva para un examen concreto. Se hace una vez y se
actualiza cuando cambia la convocatoria. **Todo lo que se escribe va a `oposiciones/<slug>/`, que no se
versiona.** Los comandos de este documento los ejecuta el agente, con el entorno que preparó
`skills/setup/SKILL.md`; el usuario no copia nada.

## Antes de empezar: qué hace falta

| Dato | Por qué | Si falta |
|---|---|---|
| Nombre de la oposición y de la administración que convoca | Da contexto al PDF y a la búsqueda | Se puede poner un nombre de trabajo y corregirlo después |
| Programa oficial (enlace al boletín o PDF) | Es la única fuente legítima del temario | Sin programa no hay alta: se trabaja en modo consulta |
| División del temario en bloques y códigos | Resuelve ambigüedades y nombra las salidas | Se deduce de la estructura del programa |
| Norma del puesto | Temas de categoría, funciones y jornada | Se deja la sección sin documentar y se marca la carencia |
| Dominios de confianza | Orientan la búsqueda | Se parte de `references/fuentes.md` y de los que el usuario nombre |
| Material propio | Base del 80% en examen y audio | Se declara `Propio: 0%` |

## Procedimiento

1. **Elige el slug.** Corto, en minúsculas, sin tildes ni espacios (`mi-oposicion`). Es el primer parámetro y
   el nombre de la carpeta; no se cambia después sin mover el directorio.
2. **Crea el esqueleto.**

   ```bash
   python3 scripts/opositor.py init <slug> --nombre "<nombre>" --ambito "<administración>" [--idioma es-ES]
   ```

   Escribe `config.json`, `temario.md`, `perfil.md`, `fuentes.md` y `materiales/LEEME.md` con marcadores.
3. **Lee el programa oficial y vuelca el temario.** Un bloque por materia, un `###` por tema, con código,
   enunciado, epígrafes y términos. Reglas y normalizaciones en `references/temario.md`. Anota `Fuente` y
   `Comprobado`; sin esas dos líneas el temario no vale.
4. **Documenta el puesto.** Sigue el cuestionario de `references/perfil.md`: norma, vigencia, clasificación,
   definición literal, jornada y formato del ejercicio.
5. **Documenta las fuentes.** Dominios por eje, puertas de entrada, consultas modelo y trampas. Un eje por
   bloque temático, con el nombre del bloque como encabezado. Nada de dominios copiados de otra oposición.
6. **Inventaría el material propio.** `materiales/LEEME.md` describe cada PDF, los temas que cubre, para qué
   sirve y qué erratas se le conocen. Sin ese inventario, el 80% se calcula a ciegas.
7. **Valida.**

   ```bash
   python3 scripts/opositor.py check <slug>
   ```

   El chequeo avisa de marcadores sin sustituir, de un temario sin bloques, de un perfil sin definición literal
   y de un `LEEME` vacío. No inventa contenido: solo dice qué falta.
8. **Anota el alta.** Una línea en `oposiciones/<slug>/log.md` con la fecha, la fuente del programa y qué
   quedó pendiente.

## Actualizar

Cuando salga convocatoria nueva o se reforme la norma:

1. Compara el programa nuevo con `temario.md` **tema por tema** y anota solo diferencias de contenido.
2. Actualiza `Fuente` y `Comprobado`. Si el programa cambió de estructura, añade una sección `Notas` con la
   redacción anterior: sirve para reconocer material viejo.
3. Actualiza el formato del ejercicio en `perfil.md` (partes, tiempo, reservas, penalización).
4. Reejecuta `check`. Las salidas antiguas de `materiales/generados/` se conservan: son histórico, no verdad.

## Privacidad: la regla que no se negocia

- Nada de lo que escribas en el perfil puede acabar en el repositorio. `oposiciones/` está en `.gitignore`; no
  lo saques de ahí, no lo fuerces con `git add -f`, no lo pegues en un issue.
- El núcleo versionado no menciona la oposición, ni la administración, ni el boletín, ni rutas absolutas.
- Antes de publicar cambios en el núcleo:

  ```bash
  printf '%s\n' "<término>" ... > oposiciones/.privacidad.txt
  python3 scripts/opositor.py check --privacidad
  ```

- Si vas a compartir la skill con otra persona, comparte el repositorio, no tu carpeta `oposiciones/`.

## Errores típicos de un alta

| Error | Efecto | Corrección |
|---|---|---|
| Copiar el temario de una web de academia | Erratas, temas que no existen, cobertura falsa | Volver al boletín oficial |
| Un epígrafe por línea en vez de por tema | La puntuación por cobertura deja de funcionar | Agrupar por tema, epígrafes entre paréntesis |
| Perfil sin fecha de comprobación | Se usa normativa derogada sin avisar | Añadir `Comprobado` |
| Dominios copiados de otra oposición | Fuentes que no aplican al ámbito | Rehacer el eje con el perfil delante |
| Material propio sin inventariar | El 80% se declara sin saber qué hay | Escribir `LEEME.md` antes de generar nada |
| Slug con mayúsculas o tildes | Rutas frágiles y comandos incómodos | Minúsculas, guiones, sin tildes |
