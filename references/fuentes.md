---
title: Fuentes y autoridad
description: Niveles de autoridad, protocolo de búsqueda, criterios de vigencia y trampas habituales. Es el método común; los dominios concretos de cada oposición viven en su perfil.
idioma: es-ES
capa: núcleo
---

# Fuentes y autoridad

Este archivo define **qué es una buena fuente** y **cómo se busca**. Los dominios concretos —a qué web se va
para cada bloque del temario— están en `<perfil>/fuentes.md`, porque cambian con la oposición y con el país.

## Niveles de autoridad

| Nivel | Qué incluye | Cómo reconocerlo |
|---|---|---|
| **N1 · Oficial** | Boletines y diarios oficiales, textos consolidados, portales de la administración convocante, planes y protocolos publicados por ella | Dominio institucional, referencia de publicación, fecha de actualización |
| **N2 · Entidad de referencia** | Organismos del sector, asociaciones reconocidas, sociedades científicas, centros estatales de referencia | Autoría institucional identificable y publicaciones con fecha |
| **N3 · Académico y profesional** | Artículos revisados, repositorios universitarios, revistas del sector, colegios profesionales, sindicatos | Autor, filiación, revisión o comité editorial |
| **N4 · Divulgativo** | Blogs de profesionales, materiales de otras administraciones, prensa especializada | Solo si hay autor, entidad y fecha, y no contradice a N1–N2 |

Reglas de uso:

- Una fuente N4 nunca gana a una N1–N2 que cubra lo mismo. Sirve para huecos, ejemplos o actualidad.
- Las fuentes de otro ámbito territorial sirven para los temas técnicos, pero **no** para la normativa propia
  de la oposición ni para las funciones del puesto. El perfil marca cuáles son propios.
- Un texto consolidado vale más que el PDF original de la norma: incluye las reformas. Pero comprueba la fecha
  de la última actualización.

## Protocolo de búsqueda

1. **Normativo primero.** Si el epígrafe es una norma, empieza por el texto consolidado en el boletín oficial y
   confirma la vigencia. Si la norma está derogada, se descarta aunque puntúe alto.
2. **De 3 a 6 consultas por tema**, agrupadas: nombre del puesto, ámbito, nombre de la norma, término técnico y
   `site:` sobre el dominio que indique el perfil.
3. **Sinónimos antes que ampliar.** Si el término del temario es administrativo («control de esfínteres»), el
   término técnico de las guías suele ser otro («entrenamiento en el uso del inodoro»). Prueba los dos.
4. **Abre antes de incluir.** Confirma que el contenido cubre el epígrafe, no solo el título.
5. **Amplía solo si hace falta.** La búsqueda extendida gasta más y ensucia el ranking; úsala cuando la normal
   devuelva menos de tres candidatas válidas.
6. **Presupuesto compartido.** Entre varios temas, una norma o una guía común se abre y se puntúa una vez.

## Cuando una fuente no se puede abrir

| Fallo | Qué hacer |
|---|---|
| Dominio denegado por la política de red (403 del proxy, `ENOTFOUND`) | No reintentar. Listar el dominio al final para que el usuario lo permita. |
| Conexión cortada, servidor lento o caído | Reintentar hasta 4 veces con espera creciente (2, 4, 8, 16 s). |
| Reto antibots (CAPTCHA, prueba de JavaScript) | No sortearlo. Marcar `(no abierta)`. |
| Muro de pago o registro | Descartar salvo que sea N1 y el usuario lo tenga. |
| Redirección a un destino que no se puede ver | Descartar. |

Una fuente incluida sin abrir debe apoyarse en el título **y** el extracto del buscador, y lleva `(no abierta)`
en la respuesta.

## Vigencia

- **Normas:** versión consolidada y fecha de la última reforma. Si hay una reforma posterior que afecta al
  tema, se avisa en el bloque **Comprueba**.
- **Guías clínicas o protocolos:** la edición más reciente de la entidad que los emite.
- **Material conceptual** (características, técnicas, clasificaciones): puede ser antiguo si usa la
  terminología vigente y no contradice a N1–N2.

## Trampas frecuentes

- Apuntes de academia con artículos derogados o sin fecha.
- PDF suelto de la norma sin consolidar, que ignora reformas.
- Material de otra administración presentado como si fuera de la convocante.
- Copias rehospedadas de obras comerciales (repositorios de apuntes, drives públicos, canales de mensajería).
- Páginas de academia que describen el puesto y prometen el temario: describen, no son fuente de estudio.
- Terminología desfasada en el material conceptual: si el campo ya cambió el término, la fuente antigua se
  descarta aunque el concepto siga siendo válido.
- Debates de método presentados como verdad única: se presentan las posturas, con fuentes institucionales.

## Tests, simulacros y obras comerciales

- **Un test no es una fuente de contenido.** Sirve para practicar; cada respuesta se contrasta con la norma o
  la guía. Si el test no trae respuestas razonadas, no se devuelve.
- **Una obra comercial es una referencia bibliográfica.** Se devuelve su ficha legal de venta o de biblioteca,
  nunca una copia. Su índice puede servir para comprobar qué epígrafes desarrolla.
- **Las editoriales y academias** identifican la obra; su contenido es de pago y no se reproduce.

## Qué se devuelve

Hasta 10 URL por tema, ordenadas por la puntuación de `SKILL.md` §3, con la entidad, el tipo, la fecha y una
frase sobre lo que aportan. Menos de 10 es correcto. Dos URL del mismo documento, no.
