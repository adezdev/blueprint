# Tasks — deterministic inspect

Source: `.blueprint/deterministic-inspect/architecture.md`

Run every `done-when` from the repository root. `python` here means whichever
of `python3` or `python` resolves on the machine.

## Phase 1 — A checker that runs and is honest about what it saw

Ends mergeable: the script parses a feature, prints what it found, and exits
with a status that distinguishes "clean" from "could not check". No checks
yet, so it cannot fail anything — but nothing lies either.

- [x] **T1** Parse a feature directory into the `Spec` model → C1 | R3.AC1
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes, asserting id, kind,
      doc, line, refs and status for every item parsed from an inline
      document held in the test

- [x] **T2** Render findings and translate them to an exit status → C3 | R3.AC2, R3.AC3, R5.AC1, R6.AC1, R6.AC2, R6.AC3  (after T1)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes, asserting exit 0 with
      no findings, 0 with warnings only, 1 with a failure, 2 for an unreadable
      feature, that each rendered line carries its check number and location,
      that the counts line reports R/AC/C/T totals, and that every module the
      script imports is in `sys.stdlib_module_names`

      `main` accepts either a slug under `.blueprint/` or a directory path, so
      fixtures can be checked without living in `.blueprint/`.

      Introduced the `Finding` shape, which C2 owns, because rendering cannot
      be written or tested without it and this task precedes every C2 task.
      Declared verbatim from C2's interface, nothing added. The alternative
      was moving `Finding` to C3, which would have made C2 depend on C3 to
      produce what C3 depends on C2 to receive.

- [x] **T3** Report an absent document as a phase not yet run → C2 | R4.AC1  (after T2)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes, asserting a feature
      holding only `requirements.md` names the architecture phase as not run,
      emits no dangling-reference findings, and exits 0

      Added the not-run lines to `render`, which belongs to C3. Deciding
      which checks are skipped is C2's; saying so on stdout is C3's, and the
      criterion needs both. Recorded rather than split into two tasks.

## Phase 2 — The twelve checks

Ends mergeable: every documented check runs and is proven to fire on its own
violation. This is the phase that makes the tool worth having.

- [ ] **T4** Add the clean fixture and prove it produces nothing → C6 | R1.AC3, R2.AC2  (after T3)
      files: `tests/fixtures/clean/requirements.md`,
      `tests/fixtures/clean/architecture.md`, `tests/fixtures/clean/tasks.md`,
      `tests/test_inspect.py`
      done-when: `python scripts/blueprint_inspect.py tests/fixtures/clean`
      exits 0 and prints zero failures and zero warnings

      The fixture is adversarial on purpose. It must contain prose mentioning
      `files:` and `status: dropped` inside ordinary sentences, and one
      requirement covered only through its criteria rather than by name. All
      three occur in this feature's own documents and all three would produce
      a false failure under a naive scan, so a fixture without them proves
      less than it appears to.

- [ ] **T5** Checks 1–4, the coverage checks → C2 | R2.AC1, R2.AC3  (after T4)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes, asserting that a copy
      of the clean fixture with one line edited to plant each of checks 1–4
      reports that check as failed, at the right severity, and that no other
      check fires on it

- [ ] **T6** Checks 5–7, the referential checks → C2 | R1.AC3, R2.AC1  (after T4)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes for planted dangling
      references, duplicate ids, and references to a `status: dropped` id

- [ ] **T7** Checks 8, 9 and 11, the task-shape checks → C2 | R2.AC1, R2.AC3  (after T4)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes for a task missing
      `done-when` (fail), a task missing `files:` (warn), and a task citing
      two components (warn)

- [ ] **T8** Checks 10 and 12, the document-hygiene checks → C2 | R2.AC1  (after T4)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes for a `Q<n>` without
      `status: answered` on its own line, and for a phase containing no tasks

## Phase 3 — Determinism where it is actually claimed

Ends mergeable: the guarantee in the README is a tested property rather than
an intention.

- [ ] **T9** Sort findings on a total key before rendering → C3 | R1.AC1  (after T5, T6, T7, T8)
      files: `scripts/blueprint_inspect.py`, `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes, asserting two runs
      over the same feature produce byte-identical output, and that reordering
      whole items within each document changes neither the findings nor their
      order

- [ ] **T10** Prove it holds at forty-plus ids → C6 | R1.AC2  (after T9)
      files: `tests/test_inspect.py`
      done-when: `python tests/test_inspect.py` passes, synthesizing a feature
      of at least 40 ids with a known set of planted violations and asserting
      the reported findings equal that set exactly — no omissions, no extras

## Phase 4 — Put it where the checking happens

Ends mergeable: the skill, the hook and CI all use the checker, and the
prerequisite is written down.

- [ ] **T11** Make the skill call the checker instead of doing the arithmetic → C4 | R5.AC2  (after T9)
      files: `skills/inspect/SKILL.md`
      done-when: `rg 'rg -o' skills/inspect/SKILL.md` finds nothing, and the
      file instructs the agent to report that validation did not run on exit
      2 or a missing interpreter

- [ ] **T12** Run the checker from the hook and from CI → C5 | R6.AC1, R6.AC3  (after T9)
      files: `.githooks/pre-commit`, `.github/workflows/validate.yml`
      done-when: staging a feature with a planted failure makes
      `.githooks/pre-commit` exit 1, staging a clean one exits 0, the hook
      exits 0 when no interpreter is on `PATH`, and the workflow runs the
      checker over every directory under `.blueprint/`

- [ ] **T13** Document the interpreter prerequisite → chore  (after T11)
      files: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
      done-when: `rg -i 'python' README.md CONTRIBUTING.md` matches an install
      prerequisite in both, and `CHANGELOG.md` carries the entry under
      `## [Unreleased]`

      Required by D1: the plugin stops being pure markdown, and the two places
      a user reads before installing must say so.
