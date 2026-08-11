# Architecture — deterministic inspect

Source: `.blueprint/deterministic-inspect/requirements.md`

## Approach

Parse the three documents into an explicit id model, run the twelve checks as
pure functions over that model, and print findings in a fixed order with a
meaningful exit status. The skill stops doing arithmetic and becomes a caller
that runs the checker and interprets its output for a human.

The alternative is to keep the work in the prompt and make the `rg` recipes
sharper — no dependency, no new files, and the skill stays pure markdown. It
is rejected because the failure mode is not imprecise greps, it is an agent
comparing two forty-element sets from scrollback and reporting a pass it did
not perform. No prompt makes that repeatable, and R1.AC1 asks for exactly
that. Grep finds candidate lines; it cannot answer "which of these forty ids
appears in none of those twelve places" the same way twice.

Everything lives in one Python module using only the standard library. The
components below are responsibilities within that module, not separate files
— at roughly 300 lines, splitting parse, check and report across three
modules would buy nothing but import statements.

## Components

### C1 — Parser    covers: R1, R3.AC1
**Files:** `scripts/blueprint_inspect.py` (new)
**Responsibility:** Turn a feature directory into an immutable set of ids,
each carrying where it came from.
**Interface:**
```python
@dataclass(frozen=True)
class Item:
    id: str                              # "R1", "R1.AC2", "C3", "T7", "Q1"
    kind: str                            # requirement|criterion|component|task|question
    doc: str                             # "requirements.md"
    line: int                            # 1-indexed
    refs: tuple[str, ...] = ()           # ids this item cites
    status: str = ""                     # "" | "dropped" | "answered"
    flags: frozenset[str] = frozenset()  # "done-when" | "files" | "chore"

@dataclass(frozen=True)
class Spec:
    slug: str
    items: tuple[Item, ...]              # declaration order
    phases: tuple[str, ...]              # phase heading text, in order
    missing: tuple[str, ...]             # documents that do not exist

def parse_feature(root: Path) -> Spec: ...
def parse_requirements(text: str) -> Iterator[Item]: ...
def parse_architecture(text: str) -> Iterator[Item]: ...
def parse_tasks(text: str) -> Iterator[Item]: ...
```
**Depends on:** stdlib `re`, `pathlib`, `dataclasses`

Line numbers are captured at parse time because they cannot be recovered
later, and R3.AC1 needs them on every finding.

### C2 — Check suite    covers: R1, R2, R4.AC1
**Files:** `scripts/blueprint_inspect.py`
**Responsibility:** Decide which findings a `Spec` warrants.
**Interface:**
```python
@dataclass(frozen=True)
class Finding:
    check: int          # 1..12, matching the documented table
    severity: str       # "fail" | "warn"
    id: str
    doc: str
    line: int
    message: str
    fix: str            # the cheapest repair, a few words

CHECKS: tuple[Callable[[Spec], Iterator[Finding]], ...]   # index 0 is check 1

def run_checks(spec: Spec) -> tuple[Finding, ...]: ...
def applicable_checks(spec: Spec) -> tuple[int, ...]: ...
```
**Depends on:** C1

Each check is a separate function over the whole `Spec`, so a fixture with one
planted violation exercises exactly one of them (R2.AC1). `applicable_checks`
is how R4.AC1 is honoured: with `architecture.md` absent, the checks that
depend on it are excluded rather than run and failed.

### C3 — Result output    covers: R1.AC1, R3, R5.AC1, R6
**Files:** `scripts/blueprint_inspect.py`
**Responsibility:** Render findings identically every run, and translate them
into a process exit status.
**Interface:**
```python
def render(spec: Spec, findings: Sequence[Finding]) -> str: ...
def exit_code(findings: Sequence[Finding], spec: Spec) -> int: ...
def main(argv: Sequence[str]) -> int: ...   # python blueprint_inspect.py [slug]
```
**Depends on:** C1, C2, stdlib `sys`, `argparse`

Findings sort by `(severity_rank, check, doc, line, id)` before rendering.
Dict and set iteration order is not relied on anywhere — that sort is what
makes R1.AC1 true rather than usually true.

Exit codes: `0` no failures (warnings included), `1` at least one failure,
`2` could not run — no such feature, or a required document unreadable.
`2` is deliberately distinct from `1` so a caller can tell "found problems"
from "did not check", which is what R5.AC2 turns on.

### C4 — Skill delegation    covers: R5.AC2
**Files:** `skills/inspect/SKILL.md` (rewrite of the Gather and Checks
sections)
**Responsibility:** Make the skill run the checker and report its output,
never re-derive the answer itself.
**Interface:** prose. The skill must:
- run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/blueprint_inspect.py <slug>`,
  falling back to `python` when `python3` is absent;
- on exit `2`, or when no interpreter is found, report that validation did
  **not run** — never summarise the documents by hand and call it a pass;
- keep the existing behaviour of naming the cheapest fix and asking before
  editing.

**Depends on:** C3

The check semantics leave this file. It keeps intent and the severity table
for a human reader, and stops being a second specification of the same logic.

### C5 — Automation wiring    covers: R6.AC1, R6.AC3
**Files:** `.github/workflows/validate.yml`, `.githooks/pre-commit`
**Responsibility:** Run the checker where no agent is present.
**Interface:**
```sh
# pre-commit: only for feature directories with staged changes
python3 scripts/blueprint_inspect.py "$slug" || exit 1

# validate.yml: every feature directory in .blueprint/
for d in .blueprint/*/; do python3 scripts/blueprint_inspect.py "$(basename "$d")"; done
```
**Depends on:** C3

CI has `python3` guaranteed. The hook does not, so it skips silently when the
interpreter is missing — a contributor without Python still gets the commit-msg
and changelog guards. That is the one place a missing interpreter is not
reported, because a hook that blocks commits on an unrelated missing tool gets
disabled within a day.

### C6 — Self-check    covers: R1.AC2, R1.AC3, R2
**Files:** `tests/fixtures/clean/{requirements,architecture,tasks}.md` (new),
`tests/test_inspect.py` (new)
**Responsibility:** Prove each check fires on its own violation and stays
silent otherwise.
**Interface:**
```python
def mutate(clean: Path, dest: Path, edit: Callable[[str], str], doc: str) -> Path: ...
def synthesize(n_requirements: int, dest: Path) -> Path: ...   # for the 40+ id case
def main() -> int: ...   # assert-based, run as: python tests/test_inspect.py
```
**Depends on:** C1, C2, C3

One clean fixture on disk; every violation case is produced by copying it into
a temp directory and editing one line. Twelve fixture directories would drift
out of sync with `FORMAT.md` the first time the grammar moves. Plain asserts,
no test framework — the repo has no dependencies and this is not the place to
start.

## Data changes

None. No schema, no state, no cache. The documents remain the only source of
truth and the checker holds nothing between runs.

## Decisions

### D1 — Python 3, standard library only
Q1 permitted one interpreter. Python is already required by the toolchain this
repo runs in, ships on the GitHub runner, and is present on the maintainer's
machine. Node would serve equally well but would be the only JavaScript in a
repo that has none. Stdlib-only keeps `pip install` out of the contributor
path, which is most of what the zero-dependency stance was protecting.
Trade-off: the plugin gains an install prerequisite, and README and
CONTRIBUTING must say so plainly.

### D2 — The code owns the check list
Twelve checks currently live in `skills/inspect/SKILL.md` as a table. Once
they are also code, one of the two is wrong the moment they disagree. The
functions in `CHECKS` become the definition; the table in the skill keeps only
the human-readable intent and severity. A check number appears in every
finding so the two can be lined up by eye.
Trade-off: reading the skill no longer tells you exactly what runs.

### D3 — Exit 2 means "did not check"
A checker that cannot run must not be indistinguishable from a clean run.
Splitting `2` out from `1` is what lets C4 and C5 tell the difference without
parsing output text. R5.AC2 is otherwise unimplementable.

### D4 — Findings are sorted, not merely collected
Determinism is a property of the output, not of the checks. Sorting on a total
key at the boundary means no check has to care about iteration order, and
R1.AC1 holds even if a check is rewritten carelessly later.

## Risks

- **Parser strictness against hand-written documents.** These files are
  written by an agent but edited by people. A heading indented by one space,
  or `covers:` on the line below the heading, parses as absent and produces a
  confident false failure — worse than the vagueness being replaced. Cheapest
  signal: run it against `.blueprint/deterministic-inspect/` and every example
  in `FORMAT.md` before wiring it into the hook. If those need touching up to
  pass, the parser is too strict, not the documents.
- **The missing-interpreter path is the untested one.** R5.AC2 matters most
  exactly when it cannot be exercised on the machine writing it. Worth
  checking by hand with the interpreter renamed out of `PATH`.
- **Check 12 (phases) and check 9 (`files:`) encode style, not truth.** They
  will fire on documents that are perfectly correct but formatted loosely. If
  they turn out noisy in practice, demoting or dropping them is a requirements
  change, not a bug fix.
- **This is the first code in a repo that is otherwise prose.** It brings a
  test file, an interpreter, and a CI step that can fail for reasons unrelated
  to the plugin's behaviour. If that overhead starts costing more than the
  determinism buys, the honest response is to revisit Q1, not to bolt on more
  tooling.
