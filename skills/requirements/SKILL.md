---
name: requirements
description: Turn a rough plan into a traceable requirements.md with stable R-ids and testable EARS acceptance criteria. Use when the user says "/blueprint:requirements", "write requirements", "turn this plan into requirements", "spec this out", or hands over a plan.md / design doc / issue and wants it made rigorous before any code is written.
---

# Blueprint: requirements

Read `${CLAUDE_PLUGIN_ROOT}/FORMAT.md` first (or `FORMAT.md` at the repo root
if you are working inside the blueprint repo itself). It defines the ID
grammar and the exact document shape. Do not improvise a variant.

## Input

Argument is a feature slug or a path. Resolve in this order:

1. Explicit path given (`/blueprint:requirements docs/oauth-plan.md`) → use it.
2. Slug given (`/blueprint:requirements token-refresh`) → read
   `.blueprint/token-refresh/plan.md`.
3. Nothing given → if exactly one `.blueprint/*/plan.md` exists, use it.
   Otherwise ask which.
4. No plan at all → the conversation *is* the plan. Say so, and write
   `plan.md` from what the user has told you before continuing.

## What you do

1. **Read the plan and the codebase it lands in.** Grep for the systems it
   touches. A requirement written without knowing what already exists is how
   you get R-ids for things that shipped last year.

2. **Extract intent, not implementation.** The plan will contain solution
   language ("add a Redis cache"). Requirements record the need behind it
   ("repeat lookups SHALL complete in under 50ms"). If a constraint is
   genuinely fixed by the user (must use their existing Postgres), record it
   under Scope as a stated constraint, not as an AC.

3. **Write one `### R<n>` per user-visible capability.** If two requirements
   always change together and no one would ever want one without the other,
   they are one requirement.

4. **Write ACs in EARS.** Every AC must be assertable by a test that only
   sees the outside of the system. Reject your own AC if you cannot name the
   test that would fail.

5. **Fill `## Out of scope` honestly.** List what a reader would reasonably
   assume is included and is not. This section prevents the most expensive
   kind of rework.

6. **Do not invent answers to gaps.** Anything the plan does not settle goes
   in `## Open questions` as `Q<n>`. Then ask the user the top 1–3 blocking
   ones directly. Guessing here is the single worst failure mode of this
   skill — a wrong assumption at R-level propagates through architecture and
   tasks and is not caught until the code is written.

7. **Write the answers back.** An answer that lives only in the chat is an
   answer the next phase cannot see. When the user settles a question, in the
   same pass:
   - mark it `status: answered — <the answer>`, keeping the `Q<n>`. The
     marker goes on the same line as the id, directly after it — the check is
     line-based, so a marker pushed onto a continuation line reads as
     unanswered. Let the question text wrap underneath instead;
   - fold the consequence into the document. A fixed decision becomes a
     stated constraint under `## Scope`; a new capability becomes a new
     `R<n>` with its own criteria.

   An answered question that changed nothing in the document usually means it
   was not blocking. Say so rather than inventing a requirement for it.

8. **Write the file** to `.blueprint/<slug>/requirements.md`, at the root of
   the repository being built — including when that repository is Blueprint
   itself.

## Updating an existing requirements.md

Append new R-ids. Never renumber. If a requirement changed meaning, that is a
new R-id and the old one gets `status: dropped — superseded by R7`. Then say
which architecture components and tasks now reference a dropped id — the user
needs to know the downstream cost before accepting the change.

## Done

Report: count of requirements and ACs, the out-of-scope list, and any open
questions still unanswered. Then one line:

> Next: `/blueprint:architecture <slug>` — but answer Q1–Q2 first.

If there are no open questions, say the spec is ready and skip the caveat.

## Rules

- No implementation nouns in this file. No class names, no libraries, no file
  paths, no schemas. The one exception is a non-functional requirement where
  the constraint *is* the dependency — portability, operability, a runtime
  that must or must not be present. Name the category, never the product.
- No AC that cannot fail. "The system SHALL be reliable" is not an AC.
- Prefer fewer, sharper requirements. Ten R-ids for a two-day feature means
  you are describing the implementation.
- Never write requirements.md and architecture.md in the same pass. The gap
  between them is where the user gets to disagree cheaply.
