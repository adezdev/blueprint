# Requirements — deterministic inspect

Source: `.blueprint/deterministic-inspect/plan.md`

## Scope

Traceability validation of a Blueprint feature must return the same findings
every time it runs, and must stay correct as the number of ids grows past the
point where a person — or an agent reading grep output — can hold the sets in
working memory. Today the answer depends on who is reading; it should depend
only on the documents.

Stated constraints, fixed by the user and not up for negotiation here:

- The id grammar in `FORMAT.md` does not change.
- Validation is read-only. It reports; it never edits a document.
- Validation may depend on a single general-purpose interpreter being present
  on the machine. It may not depend on the toolchain of the project being
  specified. (Answer to Q1, 2026-08-11.)

## Out of scope

- **Fixing anything.** Suggesting the cheapest fix stays; applying it does not.
- **Judging prose quality.** Whether an acceptance criterion is *genuinely*
  testable, whether a component's responsibility is really singular, whether a
  requirement is well written — all judgment, none of it mechanical. Those
  stay with the agent reading the document.
- **Checking code against tasks.** Validation covers the three documents only.
  Whether the implementation actually satisfies `R1.AC1` is what `done-when`
  is for.
- **Cross-feature validation.** One feature directory at a time. No checking
  that two features contradict each other.
- **New checks.** The set of checks is the twelve already specified. Making
  them reliable is this work; adding to them is not.

## Requirements

### R1 — Repeatable results

The same documents produce the same findings, regardless of who runs the
check or how large the feature has grown.

- **R1.AC1** WHEN validation runs twice against unchanged documents THEN the
  system SHALL report an identical set of findings.
- **R1.AC2** WHEN a feature contains at least 40 ids THEN the system SHALL
  report every violation present in the documents, omitting none.
- **R1.AC3** The system SHALL NOT report a violation that is not present in
  the documents.

### R2 — Every specified check is enforced

Twelve checks are written down. All twelve must actually run — a check that
is documented but skipped is worse than one that was never promised.

- **R2.AC1** WHEN the documents contain a single violation of any one
  specified check THEN the system SHALL report that check as failed.
- **R2.AC2** WHEN the documents are fully consistent THEN the system SHALL
  report zero failures and zero warnings.
- **R2.AC3** The system SHALL report each violation at its specified
  severity, distinguishing failures from warnings.

### R3 — Findings are actionable without re-reading the documents

A finding that says something is wrong but not where is a second search task.

- **R3.AC1** WHEN a violation is reported THEN the system SHALL name the
  offending id, the document containing it, and the line it appears on.
- **R3.AC2** WHEN a violation is reported THEN the system SHALL state which
  check failed.
- **R3.AC3** WHEN validation completes THEN the system SHALL report the count
  of requirements, criteria, components and tasks it examined.

### R4 — Missing phases are reported as missing, not as failure

A feature that has not reached the architecture phase yet is incomplete, not
broken.

- **R4.AC1** IF a document the checks depend on is absent THEN the system
  SHALL report which phase has not run, and SHALL NOT report violations that
  are consequences of that absence.

### R5 — Honest about its own limits

The dangerous outcome is not a check that cannot run. It is a check that
cannot run and says everything looks fine.

- **R5.AC1** The system SHALL complete validation on a machine with no
  project-specific toolchain installed.
- **R5.AC2** IF validation cannot be performed THEN the system SHALL report
  that it did not run, and SHALL NOT report a pass.

### R6 — Runnable without an agent

Traceability breaks are cheapest to catch before review, which means the same
check has to run where no agent is present.

- **R6.AC1** WHEN validation is run from a shell THEN the system SHALL exit
  non-zero if any failure-severity violation is present, and zero otherwise.
- **R6.AC2** WHEN only warning-severity violations are present THEN the
  system SHALL exit zero.
- **R6.AC3** WHEN validation is run from a shell THEN the system SHALL report
  its findings without an agent needing to interpret them.

## Open questions

All answered. Kept for the record — the answers are constraints now.

- **Q1** status: answered — yes, one general-purpose interpreter is permitted (2026-08-11)
  May validation depend on a runtime that is not guaranteed to be present?
  Determinism at scale wants a real parser, and the alternative was weakening
  R1.AC2 to best-effort. Recorded as a stated constraint under Scope. The
  plugin gains an install prerequisite; that cost was accepted.
- **Q2** status: answered — yes, in CI and from the `pre-commit` hook (2026-08-11)
  Must validation be runnable outside Claude Code? This added R6, and its
  need for a machine-readable exit status is what forced Q1.
