---
name: inspect
description: Validate a Blueprint feature's traceability chain — orphan requirements, uncovered acceptance criteria, dangling C/R ids, components nothing builds, unanswered open questions. Use when the user says "/blueprint:inspect", "check the spec", "validate the blueprint", "does everything trace", or after hand-editing any of requirements.md / architecture.md / tasks.md.
---

# Blueprint: inspect

Read `${CLAUDE_PLUGIN_ROOT}/FORMAT.md` first (or `FORMAT.md` at the repo root
if you are working inside the blueprint repo itself).

Read-only. This skill reports; it does not edit. Offer fixes, apply none
without being asked.

## Gather

Run these against `.blueprint/<slug>/` and work from the output — do not
eyeball the documents:

```bash
rg -o '^### (R\d+)'            requirements.md   # declared requirements
rg -o '\*\*(R\d+\.AC\d+)\*\*'  requirements.md   # declared criteria
rg -o '^### (C\d+)'            architecture.md   # declared components
rg -o 'covers: *(.+)$'         architecture.md   # coverage claims
rg -o '\*\*(T\d+)\*\*'         tasks.md          # declared tasks
rg -o '→ *(C\d+|chore) *\| *(.+)$' tasks.md      # task citations
rg -o '\*\*(Q\d+)\*\*'         requirements.md architecture.md
rg -n 'status: answered'       requirements.md architecture.md
rg -n 'status: dropped'        requirements.md architecture.md tasks.md
```

## Checks

| # | Check | Severity |
|---|---|---|
| 1 | Every `R<n>` has ≥1 AC | fail |
| 2 | Every `R<n>` appears in ≥1 component `covers:` | fail |
| 3 | Every `R<n>.AC<m>` is cited by ≥1 task | fail |
| 4 | Every `C<n>` is cited by ≥1 task | fail |
| 5 | Every id cited anywhere actually exists (no dangling refs) | fail |
| 6 | No id declared twice | fail |
| 7 | Nothing references an id marked `status: dropped` | fail |
| 8 | Every task has a `done-when` line | fail |
| 9 | Every task has a `files:` line | warn |
| 10 | No unanswered `Q<n>` — `rg '^\s*- \*\*Q\d+\*\* status: answered'` matches every declared `Q` | warn |
| 11 | No task cites more than one `C<n>` | warn |
| 12 | Phases exist and each has ≥1 task | warn |

If a document is missing, report which step has not run yet and stop — do not
report 40 failures because architecture.md does not exist.

## Output

A short table, then the specifics. Nothing else.

```
Blueprint: token-refresh

  requirements   7 R, 19 AC
  architecture   5 C
  tasks          12 T, 3 phases

  FAIL  R4 covered by no component
  FAIL  T9 cites C6, which does not exist
  FAIL  R2.AC3 cited by no task
  WARN  Q2 unanswered
  WARN  T5 has no files: line

  3 failures, 2 warnings.
```

When everything passes, say so in one line with the counts. Do not pad.

For each failure, name the cheapest fix in a few words ("R4: add a component
or drop the requirement"). Then ask whether to apply them. Do not start
editing.
