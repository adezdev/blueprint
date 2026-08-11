# Plan — deterministic inspect

Captured from conversation, 2026-08-11. Not hand-written by the user; written
by `/blueprint:requirements` from what was discussed, then used as its input.

## The problem

`/blueprint:inspect` currently instructs the agent to run a handful of `rg`
commands and then compare the resulting id sets in its head. That was a
deliberate shortcut when the skill was written — it keeps the plugin
dependency-free and language-agnostic, and it is accurate enough on a feature
with roughly ten ids.

It does not hold up. Set arithmetic over 40+ ids done by reading grep output
is exactly the kind of task where an agent quietly drops an item or reports a
pass it did not verify. Blueprint's whole claim over the alternatives in the
README is that traceability is *checked* rather than merely intended. If the
checker is unreliable at the sizes where checking actually matters, that claim
is hollow.

## What was asked for

Make `/blueprint:inspect` deterministic — same documents in, same findings
out, every time, at any size.

## The tension

A deterministic checker almost certainly wants a real parser, which means a
runtime the plugin cannot currently assume is installed. The repo has an
explicit zero-dependency stance and the skills are pure markdown. These pull
in opposite directions and the resolution is not obvious, so it is recorded
as an open question rather than decided here.

## Known constraints

- The id grammar in `FORMAT.md` is fixed. This work does not change it.
- `/blueprint:inspect` is read-only and stays read-only.
- Whatever ships must not silently degrade into "looks fine to me".
