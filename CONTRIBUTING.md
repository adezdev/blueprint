# Contributing

Blueprint is five markdown files that tell an agent how to behave. There is no
build and no test runner — the review is reading the prose and running the
skill on a real feature.

## Setup

```
git clone https://github.com/adezdev/blueprint
cd blueprint
git config core.hooksPath .githooks
```

That last line is not optional. `commit-msg` rejects a subject that is not a
Conventional Commit, and `pre-commit` rejects a change to `skills/`,
`FORMAT.md` or `.claude-plugin/` that forgets `CHANGELOG.md`.

To run your working copy instead of the published plugin:

```
/plugin marketplace add /path/to/your/clone
/plugin install blueprint@blueprint
/reload-plugins
```

## Changing a skill

Prompts fail differently from code. A skill that reads well can still produce
the wrong document, so:

- **Run it end to end on a real feature** before opening a PR. Not a toy one —
  something with at least a handful of requirements, where coverage gaps can
  actually appear.
- **Check what it wrote against `FORMAT.md`.** If your change makes a skill
  emit a shape `FORMAT.md` does not describe, either the skill is wrong or
  `FORMAT.md` needs updating in the same PR. They must not disagree.
- **Run `/blueprint:inspect` on the output.** It is the cheapest signal that
  the traceability still holds.
- **Prefer cutting instructions to adding them.** These files are read into a
  context window on every invocation. An instruction that restates something
  the model already does is a cost with no effect.

Changing the id grammar or a document shape is a breaking change: it invalidates
`.blueprint/` directories people already have. It needs a `!` in the commit
subject and a note in the changelog under **Changed**.

## Commits

Strict [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add a phase gate to the tasks skill
fix(build): stop ticking the box when done-when is skipped
docs: clarify how dropped ids work
```

Lowercase imperative subject, no trailing period, under 72 characters. Use the
body for reasoning — the diff already lists the files. No `Co-Authored-By`
trailers.

## Changelog

Every user-visible change gets an entry under `## [Unreleased]`, in the same
commit as the change. Categories are the Keep a Changelog set: Added, Changed,
Deprecated, Removed, Fixed, Security. Skip it only for changes nobody using
the plugin could notice.

## CI

`.github/workflows/validate.yml` checks that the manifests parse, that
`plugin.json`'s version matches the newest version heading in `CHANGELOG.md`,
and that every skill's frontmatter `name:` matches its directory and carries a
description. A skill with no description never autoloads, and nothing else
would catch that. Run it locally with `jq` installed if you want the result
before pushing.

## Releasing

1. Rename `## [Unreleased]` to `## [x.y.z] - YYYY-MM-DD` and add the link
   reference at the bottom of the changelog.
2. Bump `version` in `.claude-plugin/plugin.json` to match. CI fails if these
   drift.
3. Commit as `chore: release x.y.z`, then `git tag -a vx.y.z -m "vx.y.z"`.
4. Push both, and `gh release create vx.y.z --verify-tag` with the changelog
   section as the notes.

Semver against the documents, not the code: a change that invalidates existing
`.blueprint/` directories is major, a new skill or new section is minor,
wording and fixes are patch.
