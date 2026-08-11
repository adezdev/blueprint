---
name: build
description: Execute the next unblocked task from a Blueprint tasks.md — read only that task's component and acceptance criteria, make the focused change, prove it with the done-when check, tick the box. Use when the user says "/blueprint:build", "do the next task", "implement T4", "continue the blueprint", or wants the spec turned into code one reviewable commit at a time.
---

# Blueprint: build

Read `${CLAUDE_PLUGIN_ROOT}/FORMAT.md` first (or `FORMAT.md` at the repo root
if you are working inside the blueprint repo itself).

One task per invocation. Stop when it is done. That boundary is the point of
this skill — it is what keeps a diff reviewable.

## Select the task

Argument may be a slug, a task id (`T4`), both, or nothing.

1. Resolve the feature: argument slug → single `.blueprint/*/tasks.md` → ask.
2. Explicit `T<n>` given → use it, but refuse if its `(after ...)`
   dependencies are unchecked. Say which.
3. Otherwise take the first `[ ]` task, in phase order, whose dependencies
   are all `[x]`.
4. All tasks checked → say so, and go to **Phase close** below.

## Load only what the task cites

This is the discipline that makes the change focused. For task
`T7 ... → C2 | R1.AC1, R1.AC2`, read:

- the `### C2` section of architecture.md — files, interface, dependencies
- the `R1.AC1` and `R1.AC2` lines of requirements.md
- the files the task names, and their existing tests
- whatever those files actually call, as far as you need to understand them

Do **not** read the whole spec, and do not implement anything that is not in
the cited component. Work you notice is needed but that no task covers is a
finding, not a licence — note it and raise it at the end.

## Execute

1. If on the repository's default branch, create a feature branch first
   (`blueprint/<slug>`). Do not commit to `main` directly.
2. Make the change. Match the surrounding code — its naming, its error
   handling, its test style. The component interface in architecture.md is a
   contract; if you must deviate from the declared signature, that is a spec
   change, see **Escalate**.
3. Write the test that asserts the cited ACs, in the same pass. A task whose
   `done-when` is a test command is not done until that test exists and
   fails for the right reason before it passes.
4. Run `done-when`. Paste the real output. If it fails, fix and rerun. If it
   fails for a reason outside this task's scope, stop and report — do not
   widen the diff to make a check go green.
5. Only after `done-when` genuinely passes, tick the box in tasks.md:
   `- [x] **T7** ...`. Never tick a box on the strength of "the code looks
   right".
6. Do not commit unless the user asked. Report what changed and let them
   look.

## Escalate, do not improvise

Stop and ask if, while implementing, you find that:

- the component's declared interface does not work
- the task depends on something no earlier task built
- an acceptance criterion is untestable or contradicts another
- the change needs files outside the component's declared set

Say which document is wrong and what the amendment would be
(`/blueprint:architecture <slug>` to add C7, or a new R-id). Silently
deviating from the spec destroys the traceability that the rest of this
plugin depends on — the docs stop describing the code and become a lie.

## Phase close

When the last task in a phase is ticked:

1. Run the full test suite, not just this task's check.
2. Run `/code-review` on the branch diff. Report the findings; apply only
   what the user approves.
3. Offer a PR. If accepted, `gh pr create` with a body that lists the phase's
   task ids and the requirements they satisfy, so a reviewer can check the
   claim:

   ```
   ## Phase 1 — Storage
   - T1, T2 → C1 (TokenStore)
   Satisfies R1.AC1, R1.AC2, R3.AC1
   ```

## Done

Report, in this order: task id and title, files changed, the `done-when`
output, anything you escalated, and the next unblocked task. No summary of
code the user can read in the diff.

## Rules

- One task per run. Continue only if the user says continue.
- Never tick a box without a passing check.
- Never edit requirements.md or architecture.md from this skill. Escalate
  instead.
- Scope is the cited component. Refactors, cleanups, and improvements you
  spot along the way get reported, not committed.
