---
name: tasks
description: Turn an architecture.md into a traceable tasks.md — phased, commit-sized T-ids, each citing its component and acceptance criteria with a runnable done-when check. Use when the user says "/blueprint:tasks", "break this into tasks", "make a task list", "what's the build order", or has an architecture.md and wants an executable plan.
---

# Blueprint: tasks

Read `${CLAUDE_PLUGIN_ROOT}/FORMAT.md` first (or `FORMAT.md` at the repo root
if you are working inside the blueprint repo itself). It defines the ID
grammar and the exact document shape. Do not improvise a variant.

## Input

`.blueprint/<slug>/architecture.md` and `requirements.md` — you need both,
because tasks cite acceptance criteria, not just components. Resolve the slug
from the argument, the single existing feature directory, or ask.

## What you do

1. **One task per commit-sized change.** Roughly ≤3 files. A task a reviewer
   cannot hold in their head in one sitting is two tasks.

2. **Cite the chain on every task:** `→ C2 | R1.AC1, R1.AC2`. This is what
   makes `/blueprint:build` able to make a focused change — it reads only the
   cited component and criteria, not the whole spec. A task with no citation
   is either a chore (`→ chore`) or a task nobody asked for.

3. **Every task gets a `done-when` that is a command.** `pytest tests/x.py -k
   y` passes, `curl localhost:8000/health` returns 200, `npm run build`
   succeeds. If a task genuinely has no automatable check, write the exact
   manual observation — but treat that as a smell, and prefer restructuring
   so it has one.

4. **Tests are part of the task, not a phase at the end.** The task that
   implements `R1.AC1` is the task that writes the test asserting `R1.AC1`.
   Never emit a "write all the tests" phase.

5. **Phase by shippability, not by layer.** Each phase should end somewhere
   the branch could be reviewed and merged. "All models, then all handlers,
   then all routes" is a layer plan and produces one enormous unreviewable
   PR. Prefer thin vertical slices.

6. **Order by dependency, mark it explicitly.** `(after T1)`. Tasks with no
   `after` line are unblocked and may be done in any order.

7. **Cover every AC.** Before writing the file, check both directions: every
   `R<n>.AC<m>` in requirements.md is cited by at least one task, and every
   `C<n>` in architecture.md is implemented by at least one task. Report any
   that are not — do not paper over the gap.

8. **Write the file** to `.blueprint/<slug>/tasks.md`.

## Updating an existing tasks.md

Append. Never renumber, never rewrite a completed `[x]` task. If a task is no
longer needed, leave it unchecked and add `status: dropped — <reason>`.

## Done

Report: task count, phase count, coverage check (any uncovered AC or
unimplemented component?), and the first unblocked task. Then:

> Next: `/blueprint:inspect <slug>` to validate the chain, then
> `/blueprint:build <slug>` to execute T1.

## Rules

- No task larger than a reviewable commit.
- No `done-when: code is written`. That is not a check.
- No dedicated "testing" or "documentation" phase at the end.
- No task that exists only because it seemed like good hygiene. If no
  component or criterion asks for it, cut it.
