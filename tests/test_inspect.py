"""Self-check for the Blueprint inspector. Run: python tests/test_inspect.py

Plain asserts, no framework — the repo has no dependencies and this is not the
place to start.
"""

from __future__ import annotations

import ast
import contextlib
import io
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


FAILURE = bi.Finding(2, "fail", "R4", "requirements.md", 64, "covered by no component", "add a component or drop it")
WARNING = bi.Finding(9, "warn", "T5", "tasks.md", 31, "has no files: line")


def feature_dir(tmp: str, name: str = "sample-feature") -> Path:
    root = Path(tmp) / name
    root.mkdir()
    (root / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
    (root / "architecture.md").write_text(ARCHITECTURE, encoding="utf-8")
    (root / "tasks.md").write_text(TASKS, encoding="utf-8")
    return root


def test_exit_code_blocks_on_failures_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        spec = bi.parse_feature(feature_dir(tmp))
    assert bi.exit_code([], spec) == 0, "clean run must exit 0"
    assert bi.exit_code([WARNING], spec) == 0, "warnings alone must exit 0"
    assert bi.exit_code([WARNING, FAILURE], spec) == 1, "a failure must exit non-zero"


def test_render_locates_every_finding() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        spec = bi.parse_feature(feature_dir(tmp))
    report = bi.render(spec, [FAILURE, WARNING])

    fail_line = next(line for line in report.splitlines() if "FAIL" in line)
    for fragment in ("[2]", "R4", "requirements.md:64", "covered by no component"):
        assert fragment in fail_line, f"{fragment!r} missing from: {fail_line!r}"
    assert "add a component or drop it" in fail_line, fail_line

    warn_line = next(line for line in report.splitlines() if "WARN" in line)
    for fragment in ("[9]", "T5", "tasks.md:31"):
        assert fragment in warn_line, f"{fragment!r} missing from: {warn_line!r}"

    assert "1 failure, 1 warning." in report, report


def test_render_reports_what_it_examined() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        spec = bi.parse_feature(feature_dir(tmp))
    report = bi.render(spec, [])

    assert "2 R, 3 AC, 2 Q" in report, report
    assert "2 C, 1 D" in report, report
    assert "3 T, 2 phases" in report, report
    assert "0 failures, 0 warnings." in report, report


def test_main_reports_when_it_did_not_check() -> None:
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = bi.main(["no-such-feature-anywhere"])
    assert code == 2, f"unreadable feature must exit 2, got {code}"
    assert "did not check" in err.getvalue(), err.getvalue()


def test_main_runs_end_to_end() -> None:
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as tmp:
        root = feature_dir(tmp)
        with contextlib.redirect_stdout(out):
            code = bi.main([str(root)])
    assert code == 0, f"a feature with no checks run must exit 0, got {code}"
    assert "Blueprint: sample-feature" in out.getvalue(), out.getvalue()


def partial_feature(tmp: str) -> Path:
    """A feature that has had requirements written and nothing else."""
    root = Path(tmp) / "half-done"
    root.mkdir()
    (root / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
    return root


def test_absent_documents_name_the_phase_that_has_not_run() -> None:
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as tmp:
        root = partial_feature(tmp)
        with contextlib.redirect_stdout(out):
            code = bi.main([str(root)])
    report = out.getvalue()

    assert code == 0, f"an unfinished feature is incomplete, not broken; got {code}"
    assert "the architecture phase -- architecture.md does not exist" in report, report
    assert "the tasks phase -- tasks.md does not exist" in report, report


def test_absent_documents_skip_their_checks_instead_of_failing_them() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        spec = bi.parse_feature(partial_feature(tmp))
        complete = bi.parse_feature(feature_dir(tmp))

    runnable = bi.applicable_checks(spec)
    # 5 is the dangling-reference check: every task cites a component, and with
    # architecture.md absent every one of those would read as dangling.
    assert 5 not in runnable, "dangling refs would be reported as a consequence of absence"
    for number in (2, 3, 4, 8, 9, 11, 12):
        assert number not in runnable, f"check {number} needs a document that is absent"
    for number in (1, 6, 7, 10):
        assert number in runnable, f"check {number} needs only requirements.md"

    assert bi.applicable_checks(complete) == tuple(range(1, 13)), bi.applicable_checks(complete)
    assert bi.skipped_checks(complete) == (), bi.skipped_checks(complete)


def test_report_survives_a_narrow_console() -> None:
    """The hook and CI pipe this through whatever encoding the machine has.

    An em dash in the report raises UnicodeEncodeError on a cp1252 pipe, which
    turns "here are your findings" into a crash.
    """
    with tempfile.TemporaryDirectory() as tmp:
        spec = bi.parse_feature(feature_dir(tmp))
    report = bi.render(spec, [FAILURE, WARNING])
    try:
        report.encode("ascii")
    except UnicodeEncodeError as exc:
        raise AssertionError(f"report is not ascii-safe: {exc}") from None


def test_imports_only_the_standard_library() -> None:
    source = Path(bi.__file__).read_text(encoding="utf-8")
    roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    assert roots, "found no imports at all — the scan is broken, not the module"
    outside = sorted(root for root in roots if root not in sys.stdlib_module_names)
    assert not outside, f"non-stdlib imports would break the no-toolchain guarantee: {outside}"


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
