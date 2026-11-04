# Shared Authoring Board

Parent owns this file. Each worker owns `PROGRESS.md` and
`LIBRARY_PROPOSALS.md` inside its pack. No concurrent edits to the same file.

## Round 1

- Shared runtime is read-only during the first round; use its atomic transition
  API. Scenario-local helper additions are welcome.
- Parent is implementing registry, cross-pack export/snapshotting, and audit.
- Follow the saved integration contract. No source work by the parent inside
  worker-owned packs while the worker is active.
- Current prototype is an example, not proof that all its limitations should
  be copied. In particular, create two genuinely different outcomes.

## Round 2

- Both round-1 packs are frozen and all 200 saved positions reproduce from
  independent source trees. Do not modify `round_01/`.
- Workers own repairs in their packs only; specific feedback is in the two
  parent review files under `round_01/`.
- Shared audit is available via `python -m storyscenes.mini_adventures audit`.
  No need to create another exporter. Parent will save matched final batches.
- Initial prompt v1 remains fixed; v2 records purpose/consequence checks learned
  from the first samples. High mechanical validity did not catch these defects.

## Round 3 Ownership Extension

- Bakery additionally owns `mini_adventures/local_play.py` and
  `mini_adventures/test_local_play.py` to contribute the shared atomic-action
  helper specified in `round_02/REVIEW.md`.
- Greenhouse may read those files but must not edit or adopt them until the
  parent confirms the API is stable. Its round-3 task stays pack-local.
- Parent still owns inventory/review/CLI. No changes to legacy engines.
- Round 4 integrates both consumers and tests held-out seeds. Four rounds total.

## Round 4: Stable Helper Released

- `LocalPlay(state, *, actors, validate)` and `act(name, requires=None, **changes)`
  approved for adoption after parent code review and nine passing helper tests.
- Shared helper files are now frozen for this round. Greenhouse owns only its
  adapter/tests/docs. Bakery owns its release checks/docs.
- Parent owns final matched/held-out snapshots and full-suite verification.
- See `round_03/REVIEW.md` for exact migration-preservation requirements.

Parent integration fix during round 4: shared-helper test mocks now target
`LocalPlay.__module__` rather than a fixed package name. Repository discovery
loads `mini_adventures.*`, whereas direct tests load `storyscenes.mini_adventures.*`.
The fixed-path mocks falsely reported no delegation under discovery. Runtime
code and generated behavior are unchanged; both invocation forms are tested.

## Round 5 And Closure

- Bakery fixed one additional test-only package-identity mismatch found by the
  full suite. Greenhouse independently checked discovery-mode adapter tests.
- All 660 current StoryScenes tests now pass. Parent's final bakery recheck
  matches the preserved new-seed batch byte-for-byte; no prose changed in round 5.
- Both worker handles are completed and closed. No further paid work or edits
  are queued. See RESULTS.md for the final audit and explicit remaining limits.
