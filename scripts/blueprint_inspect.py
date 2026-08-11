"""Parse Blueprint feature documents into an explicit id model.

Standard library only, on purpose: this runs from a git hook and from CI, on
machines that have nothing installed for the project being inspected.

Markers are recognised only where FORMAT.md puts them — at the start of their
line, in the document that owns them. Blueprint's own documents describe
Blueprint's grammar, so `files:`, `covers:` and `status: dropped` all occur
inside ordinary prose. Matching those would invent ids that were never
declared, which is worse than missing one: it sends a reader hunting for
something that does not exist.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterator, Sequence

DOCS = ("requirements.md", "architecture.md", "tasks.md")

RE_HEADING = re.compile(r"^### (?P<id>[RCD]\d+)\b")
RE_CRITERION = re.compile(r"^- \*\*(?P<id>R\d+\.AC\d+)\*\*")
RE_QUESTION = re.compile(r"^\s*- \*\*(?P<id>Q\d+)\*\*(?P<rest>.*)$")
RE_TASK = re.compile(r"^- \[(?P<box>[ xX])\] \*\*(?P<id>T\d+)\*\*(?P<rest>.*)$")
RE_PHASE = re.compile(r"^## (?P<name>Phase .+?)\s*$")
RE_STATUS = re.compile(r"^\s*status: (?P<value>dropped|answered)\b")
RE_COVERS = re.compile(r"covers: *(?P<ids>.+?)\s*$")
RE_FILES = re.compile(r"^\s+files:")
RE_DONE_WHEN = re.compile(r"^\s+done-when:")

# R1.AC1 must win over R1 at the same position, so it comes first.
RE_ID = re.compile(r"\b(?:R\d+\.AC\d+|[RCDTQ]\d+)\b")


@dataclass(frozen=True)
class Item:
    """One declared id, and where it was declared."""

    id: str
    kind: str  # requirement | criterion | component | decision | task | question
    doc: str
    line: int  # 1-indexed
    refs: tuple[str, ...] = ()  # ids this item cites
    status: str = ""  # "" | "dropped" | "answered"
    flags: frozenset[str] = frozenset()  # done-when | files | chore | done


@dataclass(frozen=True)
class Spec:
    """Everything the checks are allowed to look at."""

    slug: str
    items: tuple[Item, ...]  # declaration order
    phases: tuple[str, ...]  # phase heading text, in order
    missing: tuple[str, ...]  # documents that do not exist


# A standalone `status:` line belongs to a heading. Criteria, tasks and
# questions carry their status inline, on the id's own line.
HEADING_KINDS = frozenset({"requirement", "component", "decision"})


def _ids(text: str) -> tuple[str, ...]:
    return tuple(RE_ID.findall(text))


def _with_status(items: list[Item], value: str) -> None:
    """Attach a standalone `status:` line to the heading it sits under.

    Only when that heading is the last thing declared. A marker written below
    a heading's criteria would otherwise land on the final criterion, marking
    the wrong id dropped and leaving the real one live — which check 7 then
    reads exactly backwards.
    """
    if items and items[-1].kind in HEADING_KINDS:
        items[-1] = replace(items[-1], status=value)


def _question(match: re.Match, doc: str, lineno: int) -> Item:
    """A question's answer marker is inline or it does not count.

    FORMAT.md pins it to the id's own line, because the check is line-based
    and a marker that wrapped onto line two reads as unanswered.
    """
    marker = RE_STATUS.match(match.group("rest").lstrip())
    return Item(
        match.group("id"),
        "question",
        doc,
        lineno,
        status=marker.group("value") if marker else "",
    )


def parse_requirements(text: str) -> Iterator[Item]:
    doc = "requirements.md"
    items: list[Item] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        heading = RE_HEADING.match(line)
        if heading and heading.group("id").startswith("R"):
            items.append(Item(heading.group("id"), "requirement", doc, lineno))
            continue
        criterion = RE_CRITERION.match(line)
        if criterion:
            items.append(Item(criterion.group("id"), "criterion", doc, lineno))
            continue
        question = RE_QUESTION.match(line)
        if question:
            items.append(_question(question, doc, lineno))
            continue
        status = RE_STATUS.match(line)
        if status:
            _with_status(items, status.group("value"))
    return iter(items)


def parse_architecture(text: str) -> Iterator[Item]:
    doc = "architecture.md"
    items: list[Item] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        heading = RE_HEADING.match(line)
        if heading:
            declared = heading.group("id")
            covers = RE_COVERS.search(line)
            items.append(
                Item(
                    declared,
                    "component" if declared.startswith("C") else "decision",
                    doc,
                    lineno,
                    refs=_ids(covers.group("ids")) if covers else (),
                )
            )
            continue
        question = RE_QUESTION.match(line)
        if question:
            # FORMAT.md's id table puts Q<n> in any document, and a question
            # recorded here is exactly the kind that blocks the next phase.
            items.append(_question(question, doc, lineno))
            continue
        status = RE_STATUS.match(line)
        if status:
            _with_status(items, status.group("value"))
    return iter(items)


def parse_tasks(text: str) -> Iterator[Item]:
    doc = "tasks.md"
    items: list[Item] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        task = RE_TASK.match(line)
        if task:
            rest = task.group("rest")
            _, _, cited = rest.partition("→")
            flags = {"done"} if task.group("box").lower() == "x" else set()
            if cited.strip().startswith("chore"):
                flags.add("chore")
            items.append(
                Item(
                    task.group("id"),
                    "task",
                    doc,
                    lineno,
                    refs=_ids(cited),
                    flags=frozenset(flags),
                )
            )
            continue
        if not items:
            continue
        if RE_FILES.match(line):
            items[-1] = replace(items[-1], flags=items[-1].flags | {"files"})
        elif RE_DONE_WHEN.match(line):
            items[-1] = replace(items[-1], flags=items[-1].flags | {"done-when"})
        else:
            status = RE_STATUS.match(line)
            if status:
                _with_status(items, status.group("value"))
    return iter(items)


PARSERS = {
    "requirements.md": parse_requirements,
    "architecture.md": parse_architecture,
    "tasks.md": parse_tasks,
}


def parse_feature(root: Path) -> Spec:
    missing = tuple(doc for doc in DOCS if not (root / doc).is_file())
    items: list[Item] = []
    phases: list[str] = []
    for doc in DOCS:
        if doc in missing:
            continue
        text = (root / doc).read_text(encoding="utf-8")
        items.extend(PARSERS[doc](text))
        if doc == "tasks.md":
            phases = [
                match.group("name")
                for match in (RE_PHASE.match(line) for line in text.splitlines())
                if match
            ]
    return Spec(
        slug=root.name,
        items=tuple(items),
        phases=tuple(phases),
        missing=missing,
    )


@dataclass(frozen=True)
class Finding:
    """One violation, at the place a reader can go and look at it."""

    check: int  # 1..12, matching the table in the inspect skill
    severity: str  # "fail" | "warn"
    id: str
    doc: str
    line: int
    message: str
    fix: str = ""  # the cheapest repair, a few words


PHASE_OF = {
    "requirements.md": "requirements",
    "architecture.md": "architecture",
    "tasks.md": "tasks",
}

# Which documents a check cannot run without. A check whose inputs are absent
# is skipped, not failed: a feature that has not reached the architecture
# phase is incomplete, not broken, and reporting forty dangling references
# because architecture.md does not exist yet tells the reader nothing.
CHECK_REQUIRES: dict[int, tuple[str, ...]] = {
    1: ("requirements.md",),
    2: ("requirements.md", "architecture.md"),
    3: ("requirements.md", "tasks.md"),
    4: ("architecture.md", "tasks.md"),
    5: DOCS,
    6: (),  # duplicates are real within whatever is present
    7: (),  # so are references to something already dropped
    8: ("tasks.md",),
    9: ("tasks.md",),
    10: (),  # questions are declared in whatever documents exist
    11: ("tasks.md",),
    12: ("tasks.md",),
}

# Populated in phase 2, one entry per check, in check order.
CHECKS: tuple = ()


def applicable_checks(spec: Spec) -> tuple[int, ...]:
    """The checks whose inputs are all present."""
    return tuple(
        number
        for number, required in sorted(CHECK_REQUIRES.items())
        if not any(doc in spec.missing for doc in required)
    )


def skipped_checks(spec: Spec) -> tuple[int, ...]:
    runnable = set(applicable_checks(spec))
    return tuple(number for number in sorted(CHECK_REQUIRES) if number not in runnable)


def run_checks(spec: Spec) -> tuple[Finding, ...]:
    runnable = set(applicable_checks(spec))
    findings: list[Finding] = []
    for number, check in enumerate(CHECKS, 1):
        if number in runnable:
            findings.extend(check(spec))
    return tuple(findings)


KINDS = ("requirement", "criterion", "question", "component", "decision", "task")


def counts(spec: Spec) -> dict[str, int]:
    tally = dict.fromkeys(KINDS, 0)
    for item in spec.items:
        tally[item.kind] += 1
    return tally


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def render(spec: Spec, findings: Sequence[Finding]) -> str:
    """The whole report, as text a person reads and a machine can grep."""
    tally = counts(spec)
    lines = [
        f"Blueprint: {spec.slug}",
        "",
        f"  requirements   {tally['requirement']} R, {tally['criterion']} AC, "
        f"{tally['question']} Q",
        f"  architecture   {tally['component']} C, {tally['decision']} D",
        f"  tasks          {tally['task']} T, {len(spec.phases)} phases",
        "",
    ]
    for doc in spec.missing:
        lines.append(f"  not run   the {PHASE_OF[doc]} phase -- {doc} does not exist")
    if spec.missing:
        skipped = skipped_checks(spec)
        listed = ", ".join(str(number) for number in skipped)
        lines.append(f"            {_plural(len(skipped), 'check')} skipped: {listed}")
        lines.append("")
    for finding in findings:
        label = "FAIL" if finding.severity == "fail" else "WARN"
        line = (
            f"  {label}  [{finding.check}]  {finding.id}  "
            f"{finding.doc}:{finding.line}  {finding.message}"
        )
        if finding.fix:
            line += f" -- {finding.fix}"
        lines.append(line)
    if findings:
        lines.append("")
    failures = sum(1 for finding in findings if finding.severity == "fail")
    warnings = len(findings) - failures
    lines.append(f"  {_plural(failures, 'failure')}, {_plural(warnings, 'warning')}.")
    return "\n".join(lines)


def exit_code(findings: Sequence[Finding], spec: Spec) -> int:
    """Failures are worth blocking on. Warnings are not."""
    del spec  # part of the declared contract; nothing needs it yet
    return 1 if any(finding.severity == "fail" for finding in findings) else 0


def resolve(target: str) -> Path | None:
    """Accept a slug under .blueprint/, or a path to a feature directory.

    The slug wins. Otherwise a directory in the working tree that happens to
    share a feature's name would shadow the feature itself.
    """
    for candidate in (Path(".blueprint") / target, Path(target)):
        if candidate.is_dir():
            return candidate
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="blueprint_inspect",
        description="Validate a Blueprint feature's traceability chain.",
    )
    parser.add_argument(
        "feature",
        help="feature slug under .blueprint/, or a path to a feature directory",
    )
    args = parser.parse_args(argv)

    root = resolve(args.feature)
    if root is None:
        print(
            f"blueprint_inspect: no feature directory for {args.feature!r} -- did not check",
            file=sys.stderr,
        )
        return 2
    try:
        spec = parse_feature(root)
    except (OSError, UnicodeDecodeError) as exc:
        # A document saved as cp1252 by an editor must not crash into exit 1,
        # which a caller reads as "found failures" rather than "did not check".
        print(f"blueprint_inspect: cannot read {root} -- did not check: {exc}", file=sys.stderr)
        return 2

    if len(spec.missing) == len(DOCS):
        print(
            f"blueprint_inspect: {root} holds no Blueprint documents -- did not check",
            file=sys.stderr,
        )
        return 2

    findings = run_checks(spec)
    print(render(spec, findings))
    return exit_code(findings, spec)


if __name__ == "__main__":
    raise SystemExit(main())
