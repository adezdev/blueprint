# Blueprint format

The contract every Blueprint skill reads and writes. Markdown is the only
source of truth. Machine-readability comes from stable IDs, not a second file.

## Layout

```
.blueprint/<feature-slug>/
  plan.md            # input, hand-written or pasted. optional.
  requirements.md    # R-ids
  architecture.md    # C-ids, each declaring which R-ids it covers
  tasks.md           # T-ids, each citing a C-id and one or more AC-ids
```

One directory per feature. Slug is kebab-case, short: `token-refresh`, not
`implement-the-token-refresh-flow`.

`.blueprint/` sits at the root of the repository being built — including when
that repository is Blueprint itself.

## IDs

| Prefix | Means | Lives in |
|---|---|---|
| `R<n>` | Requirement | requirements.md |
| `R<n>.AC<m>` | Acceptance criterion | requirements.md |
| `C<n>` | Component | architecture.md |
| `D<n>` | Decision | architecture.md |
| `T<n>` | Task | tasks.md |
| `Q<n>` | Open question | any |

Rules:

- IDs are permanent. **Never renumber, never reuse.** New work appends.
- Numbering gaps are normal and mean something was dropped.
- To drop an item, keep its heading and add `status: dropped — <reason>`.
  Anything referencing it must be updated in the same pass.
- An answered open question keeps its `Q<n>` and gains
  `status: answered — <the answer>`, on the same line as the id and directly
  after it. Not on a continuation line: the check is line-based, and a marker
  that wrapped onto line two reads as unanswered. A question whose answer is
  known but not written down blocks the next phase for no reason.
- IDs are grep-able: `rg '^### R\d+' requirements.md`.

## requirements.md

```markdown
# Requirements — <feature>

Source: `.blueprint/<slug>/plan.md`

## Scope
One paragraph. What this feature is, in user-visible terms.

## Out of scope
- Explicit exclusions. This section is not optional.

## Requirements

### R1 — Short title
One or two sentences of intent. Why a user wants this.

- **R1.AC1** WHEN the access token is expired AND a refresh token exists THEN the system SHALL obtain a new access token without user interaction.
- **R1.AC2** IF the refresh request fails THEN the system SHALL prompt for re-authentication and SHALL NOT exit non-zero.

### R2 — ...

## Open questions
- **Q1** ... (answer before `/blueprint:architecture`)
- **Q2** status: answered — chose X on 2026-01-09, see R4
  The question, and why it mattered, wrapped underneath.
```

Acceptance criteria use EARS:

| Pattern | Shape |
|---|---|
| Ubiquitous | The system SHALL `<response>`. |
| Event | WHEN `<trigger>` THEN the system SHALL `<response>`. |
| State | WHILE `<state>` the system SHALL `<response>`. |
| Unwanted | IF `<condition>` THEN the system SHALL `<response>`. |
| Optional | WHERE `<feature is present>` the system SHALL `<response>`. |

An AC is valid only if a test could assert it from outside the system. No
class names, no library names, no file paths in requirements.md — those are
architecture.

The exception is a non-functional requirement where the constraint *is* the
dependency: portability, operability, a runtime that must or must not be
present. Name the category, never the product — "SHALL run without a
project-specific toolchain", not "SHALL run without Node". The category is
the requirement; which product satisfies it is still architecture's call.

## architecture.md

```markdown
# Architecture — <feature>

Source: `.blueprint/<slug>/requirements.md`

## Approach
2–5 sentences: the shape of the solution, and why this over the obvious
alternative.

## Components

### C1 — TokenStore    covers: R1, R2.AC3
**Files:** `src/auth/token_store.py` (new)
**Responsibility:** One sentence. If it needs two, it is two components.
**Interface:**
```python
def load() -> Token | None: ...
def refresh(t: Token) -> Token: ...
```
**Depends on:** C2, stdlib `sqlite3`

## Data changes
Schema, migrations, file formats. Or `None`.

## Decisions
### D1 — Store tokens in the OS keyring, not a dotfile
Because ... Trade-off: ...

## Risks
- ...
```

The `covers:` list on each component heading is load-bearing —
`/blueprint:inspect` reads it to prove every requirement has a home.

## tasks.md

```markdown
# Tasks — <feature>

Source: `.blueprint/<slug>/architecture.md`

## Phase 1 — Storage
- [ ] **T1** Create TokenStore with load/save → C1 | R1.AC1
      files: `src/auth/token_store.py`
      done-when: `pytest tests/test_token_store.py -k roundtrip` passes
- [ ] **T2** Refresh on expiry → C1 | R1.AC1, R1.AC2  (after T1)
      files: `src/auth/token_store.py`, `tests/test_token_store.py`
      done-when: `pytest tests/test_token_store.py` passes

## Phase 2 — Wiring
- [ ] **T3** ...
```

Task rules:

- One task = one coherent commit. Touches ~3 files or fewer. If it needs
  more, split it.
- Every task cites exactly one `C` and at least one `AC`, except pure chores
  which cite `→ chore` (build config, dep bumps, file moves).
- `done-when` is a runnable command or an externally observable check. Not
  "code is written".
- Dependencies are `(after T1, T2)`. No dependency line means it is unblocked.
- Phases are ordered; tasks inside a phase may be reordered freely.
- `[ ]` todo, `[x]` done. `/blueprint:build` ticks the box only after
  `done-when` actually passes.
