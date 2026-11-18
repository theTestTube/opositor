---
title: Sources and authority
description: Authority levels, search protocol, currency criteria and the usual traps. This is the common method; the specific domains of each exam live in its profile.
layer: core
---

# Sources and authority

This file defines **what a good source is** and **how to search**. The specific domains — which website to go
to for each syllabus block — are in `<profile>/sources.md`, because they change with the exam and the country.

## Authority levels

| Level | What it includes | How to recognise it |
|---|---|---|
| **N1 · Official** | Gazettes and official journals, consolidated texts, portals of the calling administration, plans and protocols it publishes | Institutional domain, publication reference, update date |
| **N2 · Reference entity** | Sector bodies, recognised associations, scientific societies, national reference centres | Identifiable institutional authorship and dated publications |
| **N3 · Academic and professional** | Peer-reviewed articles, university repositories, sector journals, professional colleges, unions | Author, affiliation, review or editorial board |
| **N4 · Popular** | Practitioners' blogs, material from other administrations, specialist press | Only with an author, entity and date, and only if it does not contradict N1–N2 |

Usage rules:

- An N4 source never beats an N1–N2 that covers the same thing. It is for gaps, examples or current affairs.
- Sources from another territorial scope are useful for technical topics, but **not** for the exam's own
  regulations or the role's duties. The profile marks which ones are its own.
- A consolidated text is worth more than the original PDF of the regulation: it includes the amendments. But
  check the last update date.

## Search protocol

1. **Regulatory first.** If the section is a regulation, start with the consolidated text in the official
   gazette and confirm that it is in force. If the regulation is repealed, it is discarded even if it scores
   high.
2. **3 to 6 queries per topic**, grouped: role name, scope, regulation name, technical term and `site:` on the
   domain the profile indicates.
3. **Synonyms before broadening.** If the syllabus term is administrative ("toilet training"), the technical
   term used in guides is often different ("toileting"). Try both.
4. **Open before including.** Confirm that the content covers the section, not just the title.
5. **Broaden only if needed.** Extended search costs more and muddies the ranking; use it when the normal search
   returns fewer than three valid candidates.
6. **Shared budget.** Across several topics, a regulation or common guide is opened and scored once.

## When a source cannot be opened

| Failure | What to do |
|---|---|
| Domain denied by the network policy (proxy 403, `ENOTFOUND`) | Do not retry. List the domain at the end so the user can allow it. |
| Dropped connection, slow or down server | Retry up to 4 times with increasing waits (2, 4, 8, 16 s). |
| Anti-bot challenge (CAPTCHA, JavaScript test) | Do not solve it. Mark `(not opened)`. |
| Paywall or registration | Discard unless it is N1 and the user has access. |
| Redirect to a destination you cannot see | Discard. |

A source included without opening must rest on the title **and** the search excerpt, and carries `(not opened)`
in the answer.

## Currency

- **Regulations:** consolidated version and date of the latest amendment. If a later amendment affects the
  topic, warn in the **Check** block.
- **Clinical guidelines or protocols:** the most recent edition from the issuing entity.
- **Conceptual material** (characteristics, techniques, classifications): it may be old if it uses current
  terminology and does not contradict N1–N2.

## Frequent traps

- Academy notes with repealed articles or no date.
- A loose PDF of the regulation without consolidation, which ignores amendments.
- Material from another administration presented as if it were the caller's.
- Rehosted copies of commercial works (note repositories, public drives, messaging channels).
- Academy pages that describe the role and promise the syllabus: they describe, they are not a study source.
- Outdated terminology in conceptual material: if the field has already changed the term, the old source is
  discarded even if the concept is still valid.
- Method debates presented as the single truth: present the positions, with institutional sources.

## Tests, mock exams and commercial works

- **A test is not a content source.** It is for practice; every answer is checked against the regulation or the
  guide. If the test has no reasoned answers, it is not returned.
- **A commercial work is a bibliographic reference.** Return its legal sale or library record, never a copy. Its
  table of contents can help check which sections it develops.
- **Publishers and academies** identify the work; its content is paid and is not reproduced.

## What is returned

Up to 10 URLs per topic, sorted by the score in `SKILL.md` §3, with the entity, the type, the date and one
sentence about what they add. Fewer than 10 is correct. Two URLs for the same document, no.
