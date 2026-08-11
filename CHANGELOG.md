# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version here tracks `.claude-plugin/plugin.json`.

## [Unreleased]

### Added

- `.githooks/commit-msg` — rejects subjects that are not Conventional Commits
  and blocks `Co-Authored-By` trailers.
- `.githooks/pre-commit` — blocks a change to `skills/`, `FORMAT.md` or
  `.claude-plugin/` that ships without a changelog entry.
- `.github/workflows/validate.yml` — checks the manifests parse, the plugin
  version matches the changelog, and every skill has a directory name and
  description that will actually load.
- `.github/PULL_REQUEST_TEMPLATE.md` and issue forms for bugs and feature
  requests.
- `CONTRIBUTING.md` — setup, how to test a skill change, commit and changelog
  rules, and the release steps.

### Changed

- `status: answered — <the answer>` now marks a resolved open question, so an
  answer that was only ever spoken is written down where the next phase can
  read it. `/blueprint:requirements` records answers and folds their
  consequences into the document; `/blueprint:architecture` and
  `/blueprint:inspect` read the marker instead of guessing.
- Requirements may now name a *category* of dependency where portability or
  operability is itself the requirement — never a product. Previously the
  no-implementation-nouns rule had no room for non-functional requirements.
- `FORMAT.md` states that `.blueprint/` lives at the root of the repository
  being built, including when that repository is Blueprint itself.
- `/blueprint:architecture` applies the "no *and* in a responsibility" rule to
  the component heading, not just the responsibility line — the heading is
  what every later citation reads.
- `/blueprint:architecture` permits two components to name the same file, with
  the reason recorded in `## Approach`. Components are units of responsibility;
  splitting a small module to satisfy a one-to-one rule produces files that
  exist only to import each other.

## [0.1.0] - 2026-08-11

### Added

- `/blueprint:requirements` — turns a plan into `requirements.md` with stable
  `R` ids and EARS acceptance criteria. Records open questions instead of
  guessing at them.
- `/blueprint:architecture` — turns requirements into `architecture.md` with
  `C` ids, real interfaces, and a `covers:` list per component.
- `/blueprint:tasks` — turns architecture into `tasks.md` with commit-sized
  `T` ids, each citing a component and criteria, each with a runnable
  `done-when`.
- `/blueprint:inspect` — validates the chain: orphan requirements, uncovered
  criteria, dangling ids, components no task builds. Read-only.
- `/blueprint:build` — executes one task, reading only the component and
  criteria it cites. Ticks the box when `done-when` passes; hands to
  `/code-review` and opens a PR at phase close.
- `FORMAT.md` — the id grammar and document shapes all five skills read.
- Plugin manifest and marketplace entry, installable via
  `/plugin marketplace add adezdev/blueprint`.
- MIT license.

[0.1.0]: https://github.com/adezdev/blueprint/releases/tag/v0.1.0
