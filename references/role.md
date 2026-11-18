---
title: The role profile
description: Schema for documenting the professional category, the regulation that defines it and the format of the exercise. It replaces the old regulation file of a specific exam; here only the questionnaire remains.
layer: core
---

# The role profile

Many syllabi devote several topics to what the role does and to the regulation that creates it. This file says
**what has to be documented** about that regulation and **how it is used** in answers and exams. The real
content is in `<profile>/role.md`; if it does not exist, say so and work with what is there.

## What to document

A complete role profile answers these questions, with the literal quote and the official link:

1. **Regulation.** Full title, code or reference, gazette, publication date and link to the official text. If
   there is a consolidated text, that one.
2. **Currency.** The article that sets the duration and the extension regime, transcribed. Date of the last
   check, and whether there is an unpublished negotiation or extension.
3. **Category.** Group, level or classification, and its place in the corresponding annex or table.
4. **Literal definition.** The paragraph that defines the role, in quotes, unedited. It is the source used as N1
   when the topic is about duties.
5. **Elements of the definition, in a table.** Required qualification, recipients, purpose, activities,
   supervision, needs it addresses, principles, places and period. This table is what generates literal-detail
   questions.
6. **Working time and conditions.** Applicable articles, percentages (direct care versus other tasks), shifts
   and special schedules.
7. **Call and exercise.** The most recent call: regulation, gazette, date, number of questions per part, time,
   number of reserve questions, options per question and penalty rule.

## Schema of `role.md`

```markdown
# <Role> in the current regulation

Checked against the gazette on <YYYY-MM-DD>.

## The regulation
- Title: …
- Publication: …
- Official text: …
- Do not use: <superseded versions and why>

## Currency
- Article …: "…"
- Extensions or negotiations: …

## Classification and definition
- Group: …
- Literal definition:
  > …

| Element | Text of the regulation |
|---|---|

## Working time

## Most recent call
- …

## Where it is used
- Topics …
```

## How it is used

- **In the list of sources.** When the topic is about the category, the duties or the working time, the
  regulation is an N1 source: currency 2 and specificity 2. It is cited with the literal definition, not with a
  summary.
- **In the `high` and `max` exams.** The format of the official exercise (parts, times, reserves, penalty) defines the
  structure of the bank: practical scenarios if the real exercise has them, literal detail if the real one asks
  for it. If the profile does not document the format, say so and use the default format in `SKILL.md` §9.
- **In the answer.** If the user asks about the role and the profile is not documented, do not cite a regulation
  from memory or from another administration: offer to document it and continue with what is there.

## Traps

- **Regulations from other administrations.** They define the role with another name, other duties and another
  qualification. They are not imported, even when the name matches.
- **Superseded versions.** Copies of the previous version circulate on union and academy sites. If the
  regulation was replaced, the old copy is not a source.
- **Unpublished extensions.** An extension agreement may exist without official publication: it is cited as an
  indication, it is said to be unverified, and it is not treated as in force.
- **Paraphrased definitions.** The literal definition is transcribed; if it is summarised, it stops being useful
  for detail questions.
- **Confusing role with category.** The role name in the syllabus and the category name in the regulation may
  not match: record the equivalence explicitly.

## Updating

When a new regulation, extension or call is published: rewrite the affected section, update the check date and
note it in the profile's log. The "Do not use" list grows; it is not deleted, because it helps recognise old
material the user may find.
