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

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterator

DOCS = ("requirements.md", "architecture.md", "tasks.md")

RE_HEADING = re.compile(r"^### (?P<id>[RCD]\d+)\b")
RE_CRITERION = re.compile(r"^- \*\*(?P<id>R\d+\.AC\d+)\*\*")
RE_QUESTION = re.compile(r"^\s*- \*\*(?P<id>Q\d+)\*\*(?P<rest>.*)$")
RE_TASK = re.compile(r"^- \[(?P<box>[ x])\] \*\*(?P<id>T\d+)\*\*(?P<rest>.*)$")
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


def _ids(text: str) -> tuple[str, ...]:
    return tuple(RE_ID.findall(text))


def _with_status(items: list[Item], value: str) -> None:
    """Attach a standalone `status:` line to the item it follows."""
    if items:
        items[-1] = replace(items[-1], status=value)


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
            marker = RE_STATUS.match(question.group("rest").lstrip())
            items.append(
                Item(
                    question.group("id"),
                    "question",
                    doc,
                    lineno,
                    status=marker.group("value") if marker else "",
                )
            )
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
            flags = {"done"} if task.group("box") == "x" else set()
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
