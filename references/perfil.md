---
title: El perfil del puesto
description: Esquema para documentar la categoría profesional, la norma que la define y el formato del ejercicio. Sustituye al viejo «convenio» de una oposición concreta; aquí solo queda el cuestionario.
idioma: es-ES
capa: núcleo
---

# El perfil del puesto

Muchos temarios dedican varios temas a lo que hace el puesto y a la norma que lo crea. Este archivo dice **qué
hay que documentar** de esa norma y **cómo se usa** en las respuestas y en los exámenes. El contenido real está
en `<perfil>/perfil.md`; si no existe, se avisa y se trabaja con lo que haya.

## Qué documentar

Un perfil de puesto completo responde a estas preguntas, con la cita literal y el enlace oficial:

1. **Norma.** Título completo, código o referencia, boletín, fecha de publicación y enlace al texto oficial.
   Si hay texto consolidado, ese.
2. **Vigencia.** Artículo que fija la duración y el régimen de prórroga, transcrito. Fecha de la última
   comprobación y si hay negociación o prórroga no publicada.
3. **Categoría.** Grupo, nivel o clasificación, y su ubicación en el anexo o tabla correspondiente.
4. **Definición literal.** El párrafo que define el puesto, entrecomillado, sin retocar. Es la fuente que se
   usa como N1 cuando el tema trata de funciones.
5. **Elementos de la definición, en tabla.** Titulación exigida, destinatarios, finalidad, actividades,
   supervisión, necesidades que atiende, principios, lugares y periodo. Esta tabla es la que genera preguntas
   de detalle literal.
6. **Jornada y condiciones.** Artículos aplicables, porcentajes (atención directa frente a otras tareas),
   turnos y jornadas especiales.
7. **Convocatoria y ejercicio.** La convocatoria más reciente: norma, boletín, fecha, número de preguntas por
   parte, tiempo, número de reservas, opciones por pregunta y regla de penalización.

## Esquema de `perfil.md`

```markdown
# <Puesto> en la norma vigente

Comprobado contra el boletín el <AAAA-MM-DD>.

## La norma
- Título: …
- Publicación: …
- Texto oficial: …
- No usar: <versiones sustituidas y por qué>

## Vigencia
- Artículo …: «…»
- Prórrogas o negociaciones: …

## Clasificación y definición
- Grupo: …
- Definición literal:
  > …

| Elemento | Texto de la norma |
|---|---|

## Jornada

## Convocatoria más reciente
- …

## Dónde se usa
- Temas …
```

## Cómo se usa

- **En la lista de fuentes.** Cuando el tema trata de la categoría, las funciones o la jornada, la norma es
  fuente N1: vigencia 2 y especificidad 2. Se cita con la definición literal, no con un resumen.
- **En el examen `high`.** El formato del ejercicio oficial (partes, tiempos, reservas, penalización) define la
  estructura del banco: supuestos prácticos si el ejercicio real los tiene, detalle literal si el real lo pide.
  Si el perfil no documenta el formato, dilo y usa el formato por defecto de `SKILL.md` §9.
- **En la respuesta.** Si el usuario pregunta por el puesto y el perfil no está documentado, no cites un
  convenio de memoria ni el de otra administración: ofrece documentarlo y sigue con lo que haya.

## Trampas

- **Normas de otras administraciones.** Definen el puesto con otro nombre, otras funciones y otra titulación.
  No se importan, ni siquiera cuando el nombre coincide.
- **Versiones sustituidas.** Circulan copias de la versión anterior en webs sindicales y de academia. Si la
  norma se sustituyó, la copia antigua no es fuente.
- **Prórrogas sin publicar.** Un acuerdo de prórroga puede existir sin publicación oficial: se cita como
  indicio, se dice que no está comprobado y no se da por vigente.
- **Definiciones parafraseadas.** La definición literal se transcribe; si se resume, deja de servir para
  preguntas de detalle.
- **Confundir puesto con categoría.** El nombre del puesto en el temario y el de la categoría en la norma
  pueden no coincidir: recoge la equivalencia explícitamente.

## Actualizar

Cuando se publique norma nueva, prórroga o convocatoria: se reescribe la sección afectada, se actualiza la
fecha de comprobación y se anota en el `log` del perfil. La lista de «No usar» crece; no se borra, porque sirve
para reconocer material antiguo que el usuario pueda encontrar.
