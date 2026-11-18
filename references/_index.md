---
title: Cross-cutting core
description: Map of the versioned layer. Explains what stays in references (method, exam-agnostic), what belongs in the unversioned profile, and which invariants keep a specific syllabus out of the repository.
layer: core
---

# Cross-cutting core

`references/` is the part of the skill that **depends on no exam**. It holds the method and the schemas; never
the syllabus, nor the name of an administration, nor a list of domains from a specific sector. The exam supplies
its data in its own profile, outside git.

## The three layers

| Layer | Where | Versioned | What it answers |
|---|---|---|---|
| Core | `SKILL.md`, `references/` | yes | How to search, score, examine and listen |
| Profile | `<data root>/<slug>/` (or `$OPOSITOR_DATA/<slug>/`) | no | Which topics exist, which role it is, which domains are reliable, which notes exist |
| Outputs | `<profile>/materials/generated/` | no | PDFs, scripts, pages and MP3s for this exam |

Precedence: the profile wins over the core **when it speaks about the specific exam**; the core wins **when it
describes a procedure**. If the profile contradicts a procedure, the procedure wins and you offer to fix the
profile.

## What is here and why

| File | Answers | Does not contain |
|---|---|---|
| `syllabus.md` | How a syllabus is read, validated and versioned | Real topics |
| `sources.md` | Authority levels, search protocol, traps | Domains of one exam |
| `role.md` | How to document the role and the exam format | Anybody's regulation |
| `setup.md` | How to create or update an exam profile | An example syllabus |
| `audio.md` | Audio engines, feasibility and script rules | Voice names of a specific language |
| `templates/` | Skeletons written by `scripts/opositor.py init` | Real data |

## The decision: flexible references, but never versioning the exam

The original skill had three references and all three belonged to a single exam: the syllabus, the trusted
domains and the role's regulation. That tied it to one exam and made reuse impossible without copying and
purging the whole repository.

The solution is neither "generic references" on their own — they end up with no substance — nor "references per
exam" — they put private data into git. It is splitting every reference into two halves with the **same file
name**:

1. **`references/` keeps the schema and the method.** `syllabus.md` is no longer a syllabus: it is the template
   for one, the rules for reading codes and sections, and the currency checks. `sources.md` is no longer a list
   of websites: it is the four authority levels and the search protocol. `role.md` is no longer a regulation: it
   is the questionnaire to answer in order to document the role and the exercise.
2. **The profile keeps the data**, with the same three names (`syllabus.md`, `role.md`, `sources.md`) and the
   same shape. The profile lives outside git, so it can be filled with a copied syllabus, notes and exams
   without any of that reaching the repository.

Consequences worth keeping in mind:

- **A missing profile file does not break the skill.** You work with the method, declare the gap and offer to
  create the profile. What you never do is invent the syllabus.
- **Profiles can be compared without touching the core.** Two exams with the same format reuse `references/`
  as is; their profiles may differ in everything else.
- **Updating means rewriting the profile, not the repository.** A new programme or an amended regulation is
  noted in the profile and in its local log; the core only changes if the method changes.
- **Templates are the contract.** `init` writes exactly these skeletons; if you add a field to a template, add it
  to the validation in `scripts/opositor.py check` too.

## How to read this folder

1. `SKILL.md`, steps 0 and 1: resolve the exam and the topic.
2. `syllabus.md` if the syllabus format is not obvious or the codes are ambiguous.
3. `sources.md` before searching; afterwards, only the axis that applies.
4. `role.md` if the topic is about the role, working time or the exercise format.
5. `audio.md` if voice has to be generated; `setup.md` if a profile has to be created or updated.

## What never goes in here

- Names of administrations, regional gazettes or specific bodies.
- Syllabi, regulations, or literal fragments of legal texts.
- Domain lists from one sector, except as a generic *example* of an authority level.
- Absolute machine paths (`/home/...`): always `<profile>`.
- Check dates for a specific exam: those go in the profile.

## Fog: the version without Python

The medium-term goal is for the only requirement to be a harness that complies with the
[Agent Skills specification](https://agentskills.io/specification) plus two tools: one that talks to the
synthesizer — the Python engine and, if it is missing, the browser fallback, MP3 included — and one that writes
the exam PDF.

The format already complies: all three `SKILL.md` files validate with `skills-ref`. What does not comply is the
dependency: `scripts/opositor.py`, `exam_pdf.py` and `tts_page.py` are Python, and MP3 needs Piper.

What has been researched so far, so it is not repeated:

- **MP3 in the browser does not remove the server.** A WASM synthesis engine (~90 MB the first time) produces
  the audio in the page, but its cache needs an `http` origin, not `file://`. It removes Piper, not everything
  else.
- **The PDF is fully replaceable**, but not by a loose script: either the harness writes it with its own
  document tools, or printable HTML is generated from a page, which is the dependency-free route.
- **Profile validation needs no code**: `check` is a list of rules that any agent can apply by reading the
  files.
