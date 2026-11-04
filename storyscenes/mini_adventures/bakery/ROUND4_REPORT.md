# Bakery: Round 4 Report

Read `round_03/REVIEW.md` and the shared board. Completed a verification-only
pass; no bakery production or test source changed, no helper edits, and no greenhouse
files touched. No new regression was added because no genuine missing boundary
was found. The detailed release note is `RELEASE_NOTES.md`; machine-readable
evidence and preserved artifact hashes are in `release_checks.json`.

## Evidence

1. Shared-helper and bakery tests: 27 pass, 7.391 seconds on the final rerun.
2. Stable helper/adapter signatures, keyword-only Parameters, CLI success/help/
   invalid-count rejection, and three README recipes verified.
3. All 100 Round 3 frozen rows equal current full generation. Each saved path's
   replay also equals every saved episode. Parameters agree with seeded sampling.
   Repeated the complete checks from frozen Round 3 source in a fresh interpreter.
4. Previous examples verified against their own independent frozen interpreters:
   six `first_draws` from Round 1; six `round_02_samples` plus two explicitly
   targeted counterfactuals from Round 2; ten `round_03_samples` from Round 3.
   All 24 JSONL rows match exactly, and the corresponding Markdown prose matches.
5. The original reference equals all three frozen references byte-for-byte.
   Current `world.py`, `prose.py`, `test_world.py`, `__init__.py`, inventory,
   and shared `local_play.py` equal frozen Round 3 bytes.

An external concurrent change to shared `test_local_play.py` was detected between
the initial comparison and final hash check: exactly two mock patch targets now
use `LocalPlay.__module__` rather than a literal module name. This worker neither
made nor reverted it. The exact replacement was verified, recorded in the JSON
receipt with before/after hashes, and followed by another passing 27-test run.
No helper implementation or bakery behavior changed.

The matched outcome distribution remains 89/8/3 (postponed/surprise/shared).
No new story samples or batches were created; release verification only used
previously sampled seeds and existing diagnostic recipes. Seeds 1000-1049 were
not generated or read. No API calls, commits, agents, sampling adjustments, or
full-suite/held-out claims. Remaining limitations are in the release note.

## Changed Paths

- Added `bakery/RELEASE_NOTES.md`.
- Added `bakery/ROUND4_REPORT.md`.
- Added generated verification metadata `bakery/release_checks.json`.
- Appended the Round 4 status to `bakery/PROGRESS.md`.

All earlier reference, sample, and round-report artifacts are preserved. Bakery
is ready for the parent's external release gate; no further worker edits remain.
