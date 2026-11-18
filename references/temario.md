---
title: Cómo leer un temario
description: Esquema de un temario y reglas para interpretarlo —códigos, bloques, epígrafes, ambigüedades y control de vigencia— sin depender de ninguna oposición concreta.
idioma: es-ES
capa: núcleo
---

# Cómo leer un temario

El temario real vive en `<perfil>/temario.md`. Este archivo no lo sustituye: define **qué forma tiene** y cómo
se interpreta cuando el usuario pide temas. Si el perfil no existe, aquí está el esqueleto para crearlo
(`plantillas/temario.md`).

## Esquema mínimo de un temario

Un temario utilizable tiene tres cosas, en este orden: procedencia, bloques y temas.

```markdown
# Temario — <nombre de la oposición>

Fuente: <programa vigente, norma y fecha de publicación>.
Comprobado: <AAAA-MM-DD>. Enlace: <URL del boletín>.

## <Bloque 1>
### C1. <Enunciado del tema 1>
Enunciado: <texto literal, con las normalizaciones que se indiquen al final en «Notas»>
Epígrafes: (a) … · (b) … · (c) …
Términos: <términos de búsqueda, normas citadas, sinónimos>

## <Bloque 2>
### E1. <Enunciado del tema 1 del bloque 2>
```

Reglas del esquema:

- **Un bloque = un grupo de materias** (comunes y específicas, teóricas y prácticas, generales y propias).
  El nombre del bloque es libre; lo importante es que sea estable, porque la skill lo usa para resolver
  ambigüedades.
- **Un tema = un encabezado `###`** con código, punto y enunciado. El código es lo único que no se traduce:
  es la clave de las rutas (`E7_examen_test.pdf`) y de las preguntas cruzadas.
- **Los epígrafes van entre paréntesis y separados por `·`.** Cada epígrafe es una unidad de cobertura; la
  tabla de puntuación puntúa por epígrafe, no por tema.
- **`Términos` no es un resumen del tema**: son cadenas que sirven para buscar (normas, siglas, sinónimos
  técnicos, entidades). Si no hay, la búsqueda pierde la mitad de su precisión.
- **`Notas` al final**: redacciones antiguas, erratas del original, diferencias entre convocatorias. Sirven
  para reconocer material viejo, no para estudiar.

## Cómo se interpreta una petición

1. **Número sin bloque.** Si el número existe en un solo bloque, se usa. Si existe en dos (típico: temas 1–6
   en comunes y específicas), se pregunta una vez, agrupando todas las ambigüedades del prompt.
2. **Código con prefijo.** Si el usuario dice «E7», «específico 7» o «tema VII», normaliza al código del
   temario. Si el prefijo no existe en ese temario, dilo y ofrece los bloques disponibles.
3. **Contenido en lugar de número.** Elige el tema cuyos epígrafes lo cubren, dilo y nombra los temas vecinos
   si el contenido está repartido. Nunca inventes un tema que no esté en el temario.
4. **Rango o enumeración.** «Temas 6, 7 y 8» son tres peticiones, no una. Se aplican los topes de dificultad
   de `SKILL.md` §1 y se respeta el orden del prompt.
5. **Tema que no existe.** Si el usuario pide un número fuera del rango, responde con el rango real y no
   recicles un tema parecido.

## Control de vigencia

- El temario declara `Fuente` y `Comprobado`. Al empezar una sesión con temas normativos, si `Comprobado`
  tiene más de seis meses, comprueba en el boletín oficial si hay programa nuevo antes de buscar.
- Si aparece una convocatoria nueva, compara **enunciado por enunciado** y anota en `Notas` solo las
  diferencias reales de contenido, no las de estilo (mayúsculas, puntuación, erratas del boletín).
- Si el programa cambia, el perfil se actualiza. El núcleo no se toca: el método de lectura no cambia porque
  cambien los temas.
- Un temario sin fecha de comprobación es un temario sospechoso: úsalo, pero dilo en la respuesta.

## Normalizaciones aceptables

Al copiar el programa oficial se permite, y conviene anotar en `Notas`:

- corregir erratas evidentes del boletín;
- unificar mayúsculas y tildes;
- sustituir abreviaturas por su forma desarrollada;
- unir líneas partidas.

No se permite: cambiar el alcance de un epígrafe, añadir temas «que seguramente caen», ni reordenar el
programa. Si el original es ambiguo, se copia tal cual y se explica en `Notas`.

## Cuándo crear un temario y cuándo no

- **Créalo** cuando el usuario aporte el programa oficial (enlace o PDF) o cuando el perfil vaya a usarse más
  de una vez. El procedimiento está en `alta.md`.
- **No lo crees** para una consulta suelta: sin programa no hay verificación de cobertura, y una lista de
  epígrafes inventada produce respuestas que parecen completas y no lo están. Trabaja con el prompt, di que la
  cobertura no se puede comprobar y ofrece el alta.
