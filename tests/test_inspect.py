"""Self-check for the Blueprint inspector. Run: python tests/test_inspect.py

Plain asserts, no framework — the repo has no dependencies and this is not the
place to start.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import blueprint_inspect as bi  # noqa: E402

# Line 4 mentions a marker inside prose. Line 13 declares one. Only the second
# is a declaration, and the parser has to tell them apart.
REQUIREMENTS = """\
# Requirements — sample

## Scope
Prose mentioning status: dropped inside a sentence, declaring nothing.

## Requirements

### R1 — First
- **R1.AC1** WHEN a thing happens THEN the system SHALL respond.
- **R1.AC2** The system SHALL persist across restarts.

### R2 — Second
status: dropped — superseded by R1
- **R2.AC1** WHILE idle the system SHALL wait.

## Open questions
- **Q1** status: answered — yes (2026-08-11)
  Wrapped text under the question.
- **Q2** Still open?
"""

ARCHITECTURE = """\
# Architecture — sample

## Components

### C1 — Parser    covers: R1, R2.AC1
**Files:** `a.py`

### C2 — Reporter    covers: R1.AC2
status: dropped — folded into C1

## Decisions

### D1 — Chose a thing
"""

# T2 names `files:` only inside prose on line 9, so it has no files: line.
TASKS = """\
# Tasks — sample

## Phase 1 — Start
- [x] **T1** Do the first thing → C1 | R1.AC1
      files: `a.py`
      done-when: `python x.py` passes
- [ ] **T2** Do the next → C1 | R1.AC2, R2.AC1  (after T1)
      done-when: `python y.py` passes
      Prose naming `files:` without declaring one.

## Phase 2 — Finish
- [ ] **T3** Housekeeping → chore  (after T2)
      files: `b.py`
      done-when: `rg x` finds it
"""


def shape(item: bi.Item) -> tuple:
    return (
        item.id,
        item.kind,
        item.doc,
        item.line,
        item.refs,
        item.status,
        tuple(sorted(item.flags)),
    )


def check(actual: list, expected: list, label: str) -> None:
    assert len(actual) == len(expected), (
        f"{label}: parsed {len(actual)} items, expected {len(expected)}\n"
        f"  parsed:   {[a[0] for a in actual]}\n"
        f"  expected: {[e[0] for e in expected]}"
    )
    for got, want in zip(actual, expected):
        assert got == want, f"{label}: {want[0]}\n  got:  {got}\n  want: {want}"


def test_requirements() -> None:
    parsed = [shape(i) for i in bi.parse_requirements(REQUIREMENTS)]
    check(
        parsed,
        [
            ("R1", "requirement", "requirements.md", 8, (), "", ()),
            ("R1.AC1", "criterion", "requirements.md", 9, (), "", ()),
            ("R1.AC2", "criterion", "requirements.md", 10, (), "", ()),
            ("R2", "requirement", "requirements.md", 12, (), "dropped", ()),
            ("R2.AC1", "criterion", "requirements.md", 14, (), "", ()),
            ("Q1", "question", "requirements.md", 17, (), "answered", ()),
            ("Q2", "question", "requirements.md", 19, (), "", ()),
        ],
        "requirements",
    )


def test_architecture() -> None:
    parsed = [shape(i) for i in bi.parse_architecture(ARCHITECTURE)]
    check(
        parsed,
        [
            ("C1", "component", "architecture.md", 5, ("R1", "R2.AC1"), "", ()),
            ("C2", "component", "architecture.md", 8, ("R1.AC2",), "dropped", ()),
            ("D1", "decision", "architecture.md", 13, (), "", ()),
        ],
        "architecture",
    )


def test_tasks() -> None:
    parsed = [shape(i) for i in bi.parse_tasks(TASKS)]
    check(
        parsed,
        [
            (
                "T1",
                "task",
                "tasks.md",
                4,
                ("C1", "R1.AC1"),
                "",
                ("done", "done-when", "files"),
            ),
            (
                "T2",
                "task",
                "tasks.md",
                7,
                ("C1", "R1.AC2", "R2.AC1", "T1"),
                "",
                ("done-when",),
            ),
            ("T3", "task", "tasks.md", 12, ("T2",), "", ("chore", "done-when", "files")),
        ],
        "tasks",
    )


def test_prose_declares_nothing() -> None:
    """The traps, stated as the properties they protect."""
    tasks = {i.id: i for i in bi.parse_tasks(TASKS)}
    assert "files" not in tasks["T2"].flags, "prose `files:` counted as a declaration"

    requirements = [i for i in bi.parse_requirements(REQUIREMENTS)]
    assert all(
        i.status != "dropped" or i.id == "R2" for i in requirements
    ), "prose `status: dropped` attached to the wrong item"

    ids = [i.id for i in requirements]
    assert ids.count("R1") == 1, "an id was invented from prose"


def test_parse_feature() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sample-feature"
        root.mkdir()
        (root / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
        (root / "tasks.md").write_text(TASKS, encoding="utf-8")

        spec = bi.parse_feature(root)

        assert spec.slug == "sample-feature", spec.slug
        assert spec.missing == ("architecture.md",), spec.missing
        assert spec.phases == ("Phase 1 — Start", "Phase 2 — Finish"), spec.phases
        assert [i.doc for i in spec.items].count("architecture.md") == 0
        assert [i.id for i in spec.items] == [
            "R1",
            "R1.AC1",
            "R1.AC2",
            "R2",
            "R2.AC1",
            "Q1",
            "Q2",
            "T1",
            "T2",
            "T3",
        ], [i.id for i in spec.items]


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {test.__name__}\n      {exc}")
    passed = len(tests) - failed
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
