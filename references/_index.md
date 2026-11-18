---
title: Núcleo transversal
description: Mapa de la capa versionada. Explica qué queda en references (método, agnóstico a la oposición), qué se va al perfil no versionado y qué invariantes hay que respetar para que un temario concreto no toque el repositorio.
idioma: es-ES
capa: núcleo
---

# Núcleo transversal

`references/` es la parte de la skill que **no depende de ninguna oposición**. Contiene el método y los
esquemas; nunca el temario, ni el nombre de una administración, ni una lista de dominios de un sector concreto.
La oposición aporta sus datos en `oposiciones/<slug>/`, que está fuera de git.

## Las tres capas

| Capa | Dónde | Versionada | Qué responde |
|---|---|---|---|
| Núcleo | `SKILL.md`, `references/` | sí | Cómo se busca, se puntúa, se examina y se escucha |
| Perfil | `oposiciones/<slug>/` (o `$OPOSITOR_DATA/<slug>/`) | no | Qué temas hay, qué puesto es, qué dominios son fiables, qué apuntes existen |
| Salidas | `<perfil>/materiales/generados/` | no | PDFs, guiones, páginas y MP3 de esta oposición |

Precedencia: el perfil manda sobre el núcleo **cuando habla de la oposición concreta**; el núcleo manda
**cuando describe un procedimiento**. Si el perfil contradice un procedimiento, gana el procedimiento y se
propone corregir el perfil.

## Qué hay aquí y por qué

| Archivo | Responde a | No contiene |
|---|---|---|
| `temario.md` | Cómo se lee, se valida y se versiona un temario | Temas reales |
| `fuentes.md` | Niveles de autoridad, protocolo de búsqueda, trampas | Dominios de una oposición |
| `perfil.md` | Cómo documentar el puesto y el formato del ejercicio | El convenio de nadie |
| `alta.md` | Cómo se da de alta o se actualiza una oposición | Un temario de ejemplo |
| `audio.md` | Motores de audio, viabilidad y reglas del guion | Nombres de voces de un idioma concreto |
| `plantillas/` | Esqueletos que escribe `scripts/opositor.py init` | Datos reales |

## La decisión: `references` flexible, pero sin versionar la oposición

La skill original tenía tres referencias y las tres eran de una sola oposición: el temario, los dominios de
confianza y el convenio del puesto. Eso la ataba a un examen y hacía imposible reutilizarla sin copiar y
purgar el repositorio entero.

La solución no es «referencias genéricas» a secas —se quedan sin sustancia— ni «referencias por oposición»
—meten datos privados en git—. Es partir cada referencia en dos mitades con el **mismo nombre de archivo**:

1. **En `references/` queda el esquema y el método.** `temario.md` ya no es un temario: es la plantilla de un
   temario, las reglas para leer códigos y epígrafes y los controles de vigencia. `fuentes.md` ya no es una
   lista de webs: son los cuatro niveles de autoridad y el protocolo de búsqueda. `perfil.md` ya no es un
   convenio: es el cuestionario que hay que responder para documentar el puesto y el ejercicio.
2. **En `oposiciones/<slug>/` queda el dato**, con los mismos tres nombres (`temario.md`, `perfil.md`,
   `fuentes.md`) y la misma forma. La carpeta está en `.gitignore`, así que se puede llenar de temario copiado,
   apuntes y exámenes sin que nada de eso llegue al repositorio.

Consecuencias que conviene tener presentes:

- **Un archivo de perfil ausente no rompe la skill.** Se trabaja con el método, se declara la carencia y se
  ofrece el alta. Lo que no se hace es inventar el temario.
- **Comparar perfiles es posible sin tocar el núcleo.** Dos oposiciones con el mismo formato de examen
  reutilizan `references/` tal cual; sus perfiles pueden diferir en todo lo demás.
- **Actualizar es reescribir el perfil, no el repositorio.** Un programa nuevo o un convenio reformado se
  anota en `oposiciones/<slug>/` y en su `log` local; el núcleo solo cambia si cambia el método.
- **Las plantillas son el contrato.** `init` escribe exactamente estos esqueletos; si añades un campo a la
  plantilla, añádelo también a la validación de `scripts/opositor.py check`.

## Cómo leer esta carpeta

1. `SKILL.md`, pasos 0 y 1: resolver la oposición y el tema.
2. `temario.md` si el formato del temario no es evidente o hay códigos ambiguos.
3. `fuentes.md` antes de buscar; después, solo el eje que corresponda.
4. `perfil.md` si el tema trata del puesto, la jornada o el formato del ejercicio.
5. `audio.md` si hay que generar voz; `alta.md` si hay que crear o actualizar un perfil.

## Lo que nunca entra aquí

- Nombres de administraciones, boletines autonómicos o cuerpos concretos.
- Temarios, convenios, ni fragmentos literales de normas.
- Listas de dominios de un sector, salvo como *ejemplo* genérico de nivel de autoridad.
- Rutas absolutas de una máquina (`/home/...`): siempre `<perfil>`.
- Fechas de comprobación de una oposición concreta: van en el perfil.

## Niebla: la versión sin Python

El objetivo a medio plazo es que el único requisito sea un harness que cumpla la
[especificación de Agent Skills](https://agentskills.io/specification) más dos herramientas: una que interactúe
con el sintetizador —con el motor Python y, si falta, la caída al navegador, incluido el MP3— y otra que
escriba el PDF del examen.

Hoy el formato ya cumple: los tres `SKILL.md` validan con `skills-ref`. Lo que no cumple es la dependencia:
`scripts/opositor.py`, `examen_pdf.py` y `tts_page.py` son Python, y el MP3 necesita Piper.

Lo investigado hasta ahora, para no repetirlo:

- **El MP3 en navegador no elimina el servidor.** Un motor de síntesis WASM (~90 MB la primera vez) produce el
  audio en la página, pero su caché necesita un origen `http`, no `file://`. Sirve para quitar Piper, no para
  quitar todo lo demás.
- **El PDF sí es sustituible por completo**, pero no por un script suelto: o lo escribe el harness con sus
  propias herramientas de documento, o se genera HTML imprimible desde una página, que es la vía sin
  dependencias.
- **La validación del perfil no necesita código**: `check` es una lista de reglas que cualquier agente puede
  aplicar leyendo los archivos.
