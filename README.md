# Blueprint

Spec-driven development for Claude Code, with the traceability actually
enforced. A rough plan becomes requirements, then an architecture, then a task
list — and every task can name the component and the acceptance criterion it
exists to satisfy. Then it builds them, one reviewable commit at a time.

Markdown is the only source of truth. Machine-readability comes from stable
IDs (`R1`, `R1.AC2`, `C3`, `T7`), not a parallel JSON file that drifts.

## Flow

```
plan.md ──/blueprint:requirements──▶ requirements.md   R1, R1.AC1 …
                                          │
        ──/blueprint:architecture──▶ architecture.md   C1 covers: R1, R2
                                          │
        ──/blueprint:tasks────────▶ tasks.md           T1 → C1 | R1.AC1
                                          │
        ──/blueprint:inspect──────▶ chain validated
                                          │
        ──/blueprint:build────────▶ code, test, ✓, review, PR
```

## Skills

| Command | Does |
|---|---|
| `/blueprint:requirements [slug]` | Plan → `requirements.md`. R-ids, EARS acceptance criteria, explicit out-of-scope, open questions it refuses to guess at. |
| `/blueprint:architecture [slug]` | Requirements → `architecture.md`. Components with real interfaces, each declaring the requirements it covers. |
| `/blueprint:tasks [slug]` | Architecture → `tasks.md`. Commit-sized tasks in shippable phases, each with a runnable `done-when`. |
| `/blueprint:inspect [slug]` | Validates the chain: orphan requirements, uncovered criteria, dangling ids, components nothing builds. Read-only. |
| `/blueprint:build [slug\|T<n>]` | Executes one task. Reads only what that task cites, makes the change, proves it, ticks the box. Reviews and opens a PR at phase close. |

## Layout

```
.blueprint/<feature-slug>/
  plan.md            # your input. optional — the conversation can be the plan.
  requirements.md
  architecture.md
  tasks.md
```

Lives in the repo, so the spec reviews in the same PR as the code.

## Format

`FORMAT.md` is the contract all five skills read. Change it there and every
skill follows.

## Install

```
/plugin marketplace add /path/to/blueprint
/plugin install blueprint@blueprint
```

## Why the chain matters

Three documents with nothing checking them is a waterfall with extra steps.
The ids are what make it not that: `/blueprint:inspect` can prove that no
requirement was quietly dropped and no task was quietly invented, and
`/blueprint:build` can load one component instead of the whole spec — which
is what keeps the diff small enough to actually review.
