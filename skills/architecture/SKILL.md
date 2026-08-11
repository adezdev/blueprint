---
name: architecture
description: Turn a requirements.md into a traceable architecture.md — components with stable C-ids, each declaring which R-ids it covers, plus decisions and risks. Use when the user says "/blueprint:architecture", "design this", "how should we build this", "turn the requirements into a design", or has a requirements.md and needs the technical shape before tasks are cut.
---

# Blueprint: architecture

Read `${CLAUDE_PLUGIN_ROOT}/FORMAT.md` first (or `FORMAT.md` at the repo root
if you are working inside the blueprint repo itself). It defines the ID
grammar and the exact document shape. Do not improvise a variant.

## Input

`.blueprint/<slug>/requirements.md`. Resolve the slug from the argument, or
from the single existing `.blueprint/*/requirements.md`, or ask.

Stop before you start if `## Open questions` still has unanswered `Q<n>`
items — unanswered meaning no `status: answered` on the line. Surface them
and ask, then have `/blueprint:requirements` record the answers before you
design. Designing around an unresolved question produces a component that
gets deleted.

## What you do

1. **Read the existing codebase properly.** Where does this feature attach?
   What patterns, helpers, and types already exist that this should reuse?
   The most common failure is an architecture that reinvents something living
   three files over. Grep before you design.

2. **Pick the approach and justify it against one real alternative.** Two
   sentences on the alternative and why not. If you cannot name an
   alternative, you have not thought about it yet.

3. **Cut components at responsibility boundaries.** One `### C<n>` per unit
   with a single responsibility, a named file, and a concrete interface —
   real signatures, not prose. If a component's responsibility needs the word
   "and", split it. That applies to the heading too: a name like "Model and
   parser" describes two things even when the responsibility line underneath
   describes one, and the heading is what every later citation reads.

4. **Declare coverage on every component heading:** `covers: R1, R2.AC3`.
   Then verify the other direction: every requirement in requirements.md must
   appear in at least one `covers:` list. A requirement no component covers
   is either a missed component or a requirement that should be dropped —
   say which, do not silently leave it.

5. **Record decisions as `D<n>`** only where a future reader would otherwise
   ask "why on earth". Not every choice is a decision.

6. **Record risks** — what could make this design wrong, and the cheapest
   early signal that it is.

7. **Write the file** to `.blueprint/<slug>/architecture.md`.

## Scope discipline

Design for the requirements in front of you. No extension points for
requirements nobody wrote, no interface with one implementation, no
configuration for a value that has one caller. If you believe a requirement is
about to arrive that changes the shape, say so in `## Risks` — do not build
for it.

Prefer, in order: what the codebase already has → the standard library →
an already-installed dependency → new code. A new dependency needs a line in
`## Decisions` justifying it.

## Updating an existing architecture.md

Append new C-ids, never renumber. If implementation proved a component wrong,
mark it `status: dropped — <reason>`, add the replacement as a new C-id, and
list which tasks in tasks.md now point at a dropped component.

## Done

Report: component count, the coverage check result (every R covered? which
are not?), any new dependency you are proposing, and the top risk. Then:

> Next: `/blueprint:tasks <slug>`

## Rules

- Every component names its files. "The auth layer" is not a component.
- Two components may name the same file. Components are units of
  responsibility, not units of filesystem — splitting a small module three
  ways to satisfy a one-to-one rule produces files that exist only to import
  each other. When components share a file, say why in `## Approach`. What
  they may never share is a responsibility.
- Interfaces are code, not description.
- No component without a `covers:` list. If it covers nothing, it should not
  exist.
- Do not write tasks here. Ordering and sequencing belong to
  `/blueprint:tasks`.
