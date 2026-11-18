---
title: How to read a syllabus
description: Schema of a syllabus and rules for interpreting it —codes, blocks, sections, ambiguities and currency checks— without depending on any specific exam.
layer: core
---

# How to read a syllabus

The real syllabus lives in `<profile>/syllabus.md`. This file does not replace it: it defines **what shape it
has** and how it is interpreted when the user asks for topics. If the profile does not exist, here is the
skeleton to create it (`templates/syllabus.md`).

## Minimum schema of a syllabus

A usable syllabus has three things, in this order: provenance, blocks and topics.

```markdown
# Syllabus — <exam name>

Source: <current programme, regulation and publication date>.
Checked: <YYYY-MM-DD>. Link: <gazette URL>.

## <Block 1>
### C1. <Wording of topic 1>
Wording: <literal text, with the normalisations listed at the end under "Notes">
Sections: (a) … · (b) … · (c) …
Terms: <search terms, cited regulations, synonyms>

## <Block 2>
### E1. <Wording of topic 1 in block 2>
```

Schema rules:

- **One block = one group of subjects** (common and specific, theoretical and practical, general and own). The
  block name is free; what matters is that it is stable, because the skill uses it to resolve ambiguities.
- **One topic = one `###` heading** with a code, a dot and the wording. The code is the only thing that is not
  translated: it is the key to the paths (`E7_practice_exam.pdf`) and to cross-topic questions.
- **Sections go in brackets and are separated by `·`.** Each section is a unit of coverage; the scoring table
  scores per section, not per topic.
- **`Terms` is not a summary of the topic**: they are strings to search with (regulations, acronyms, technical
  synonyms, entities). Without them, the search loses half its precision.
- **`Notes` at the end**: older wordings, errata in the original, differences between calls. They are useful for
  recognising old material, not for studying.

## How a request is interpreted

1. **Number without a block.** If the number exists in a single block, it is used. If it exists in two (typical:
   topics 1–6 in common and specific blocks), ask once, grouping all the prompt's ambiguities.
2. **Prefixed code.** If the user says "E7", "specific 7" or "topic VII", normalise it to the syllabus code. If
   the prefix does not exist in that syllabus, say so and offer the available blocks.
3. **Content instead of a number.** Pick the topic whose sections cover it, say so, and name the neighbouring
   topics if the content is spread out. Never invent a topic that is not in the syllabus.
4. **Range or enumeration.** "Topics 6, 7 and 8" are three requests, not one. Apply the difficulty limits in
   `SKILL.md` §1 and respect the prompt's order.
5. **Topic that does not exist.** If the user asks for a number outside the range, answer with the real range and
   do not recycle a similar topic.

## Currency checks

- The syllabus declares `Source` and `Checked`. When starting a session with regulatory topics, if `Checked` is
  more than six months old, check the official gazette for a new programme before searching.
- If a new call appears, compare **wording by wording** and note in `Notes` only the real differences in
  content, not in style (capitals, punctuation, gazette errata).
- If the programme changes, the profile is updated. The core is not touched: the reading method does not change
  because the topics changed.
- A syllabus without a check date is a suspicious syllabus: use it, but say so in the answer.

## Acceptable normalisations

When copying the official programme, you may — and should — note in `Notes`:

- fixing obvious gazette errata;
- unifying capitals and accents;
- replacing abbreviations with their expanded form;
- joining broken lines.

Not allowed: changing the scope of a section, adding topics "that will probably come up", or reordering the
programme. If the original is ambiguous, copy it as is and explain it in `Notes`.

## When to create a syllabus and when not to

- **Create it** when the user provides the official programme (link or PDF) or when the profile will be used
  more than once. The procedure is in `setup.md`.
- **Do not create it** for a one-off lookup: without a programme there is no coverage check, and an invented
  list of sections produces answers that look complete and are not. Work from the prompt, say that coverage
  cannot be checked, and offer to create the profile.
