---
title: Creating an exam profile
description: Procedure to create, validate and update an exam profile without touching the versioned core. It is the new step that makes the skill reusable.
layer: core
---

# Creating an exam profile

Creating a profile is the operation that makes this skill work for a specific exam. It is done once and updated
when the call changes. **Everything written goes to the data root, which is not versioned.** The commands in this
document are run by the agent, with the environment prepared by `skills/setup/SKILL.md`; the user copies nothing.

## Before starting: what is needed

| Data | Why | If missing |
|---|---|---|
| Exam and calling administration names | Gives context to the PDF and the search | A working name can be used and fixed later |
| Official programme (gazette link or PDF) | It is the only legitimate source of the syllabus | Without a programme there is no profile: work in lookup mode |
| Division of the syllabus into blocks and codes | Resolves ambiguities and names the outputs | Infer it from the programme's structure |
| Role regulation | Topics on category, duties and working time | Leave the section undocumented and mark the gap |
| Trusted domains | Guide the search | Start from `references/sources.md` and the ones the user names |
| Own material | Basis of the 80% split in exam and audio | Declare `Own material: 0%` |

## Procedure

1. **Pick the slug.** Short, lowercase, no accents or spaces (`my-exam`). It is the first parameter and the
   folder name; it is not changed afterwards without moving the directory.
2. **Create the skeleton.**

   ```bash
   python3 scripts/opositor.py init <slug> --name "<name>" --scope "<administration>" [--language en-US]
   ```

   It writes `config.json`, `syllabus.md`, `role.md`, `sources.md` and `materials/NOTES.md` with placeholders.
3. **Read the official programme and dump the syllabus.** One block per subject area, one `###` per topic, with
   code, wording, sections and terms. Rules and normalisations in `references/syllabus.md`. Note `Source` and
   `Checked`; without those two lines the syllabus is not valid.
4. **Document the role.** Follow the questionnaire in `references/role.md`: regulation, currency, classification,
   literal definition, working time and exercise format.
5. **Document the sources.** Domains per axis, entry points, model queries and traps. One axis per syllabus
   block, with the block name as the heading. No domains copied from another exam.
6. **Inventory the own material.** `materials/NOTES.md` describes each PDF, the topics it covers, what it is for
   and which errata are known. Without that inventory, the 80% is calculated blind.
7. **Validate.**

   ```bash
   python3 scripts/opositor.py check <slug>
   ```

   The check warns about unreplaced placeholders, a syllabus with no blocks, a role profile with no literal
   definition and an empty `NOTES.md`. It does not invent content: it only says what is missing.
8. **Record the creation.** One line in `<profile>/log.md` with the date, the source of the programme and what
   was left pending.

## Updating

When a new call appears or the regulation is amended:

1. Compare the new programme with `syllabus.md` **topic by topic** and note only content differences.
2. Update `Source` and `Checked`. If the programme changed structure, add a `Notes` section with the previous
   wording: it helps recognise old material.
3. Update the exercise format in `role.md` (parts, time, reserves, penalty).
4. Run `check` again. Old outputs in `materials/generated/` are kept: they are history, not truth.

## Privacy: the rule that is not negotiable

- Nothing you write in the profile may end up in the repository. The profile lives outside it; do not move it
  inside, do not force it with `git add -f`, do not paste it into an issue.
- The versioned core names neither the exam, nor the administration, nor the gazette, nor absolute paths.
- Before publishing changes to the core:

  ```bash
  printf '%s\n' "<term>" ... > "$(python3 scripts/opositor.py home)/.privacy.txt"
  python3 scripts/opositor.py check --privacy
  ```

- If you are going to share the skill with someone else, share the repository, not your data directory.

## Typical mistakes when creating a profile

| Mistake | Effect | Fix |
|---|---|---|
| Copying the syllabus from an academy site | Errata, topics that do not exist, false coverage | Go back to the official gazette |
| One section per line instead of per topic | Coverage scoring stops working | Group by topic, sections in brackets |
| Role profile with no check date | Repealed regulations are used without warning | Add `Checked` |
| Domains copied from another exam | Sources that do not apply to the scope | Redo the axis with the profile in front of you |
| Own material not inventoried | The 80% is declared without knowing what exists | Write `NOTES.md` before generating anything |
| Slug with capitals or accents | Fragile paths and awkward commands | Lowercase, hyphens, no accents |
