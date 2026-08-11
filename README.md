# Blueprint

Runs an agent through the SDLC in the order the SDLC actually goes, and keeps
the STLC bolted to it. Requirements before design, design before tasks, tasks
before code — and a traceability matrix that proves nothing fell out between
the phases.

## The mindset

An agent handed a plan will write code. That skips requirements analysis and
design, so nobody can answer the two questions that matter later: *why does
this code exist*, and *what proves it works*. Blueprint refuses to skip.

**SDLC** — each phase produces an artifact the next phase consumes, and only
that artifact. `/blueprint:architecture` designs from `requirements.md`, not
from the original chat. Phase gates are real: unanswered open questions stop
the next phase from starting.

**STLC** — testing is not a phase at the end. Acceptance criteria are written
in EARS during requirements analysis, which makes them the test basis. Every
task cites the criteria it satisfies and carries the command that proves it.
`/blueprint:inspect` is the requirements traceability matrix: every
requirement reaches a component, every criterion reaches a test.

**Verification, not vibes.** A box is ticked when a command exits zero. If
implementation contradicts the design, the agent stops and amends the
document rather than quietly diverging — otherwise the spec becomes a lie and
the traceability is worthless.

## Phases

| SDLC / STLC phase | Command | Artifact |
|---|---|---|
| Requirements analysis + test basis | `/blueprint:requirements [slug]` | `requirements.md` — `R1`, EARS criteria `R1.AC1`, explicit out-of-scope, open questions it refuses to guess at |
| System design | `/blueprint:architecture [slug]` | `architecture.md` — components `C1` with real interfaces, each declaring `covers: R1, R2` |
| Work breakdown + test design | `/blueprint:tasks [slug]` | `tasks.md` — commit-sized `T1 → C1 \| R1.AC1`, each with a runnable `done-when` |
| Traceability review | `/blueprint:inspect [slug]` | Report — orphan requirements, uncovered criteria, dangling ids. Read-only |
| Implementation + test execution | `/blueprint:build [slug\|T<n>]` | Code, passing check, ticked box; `/code-review` and a PR at phase close |

Artifacts live in `.blueprint/<feature-slug>/`, in the repo, so the spec
reviews in the same pull request as the code it produced.

Markdown is the only source of truth. Machine-readability comes from stable
ids (`R1`, `R1.AC2`, `C3`, `T7`), not a parallel data file that drifts.
`FORMAT.md` is the contract all five skills read.

## Install

```
/plugin marketplace add adezdev/blueprint
/plugin install blueprint@blueprint
```

From a local clone, point the first command at the directory instead:

```
/plugin marketplace add /path/to/blueprint
/plugin install blueprint@blueprint
```

Then start a feature — the conversation itself can be the plan:

```
/blueprint:requirements token-refresh
```
