# Round 3 Review And Release Tasks

Both independent matched audits pass 100/100. Bakery still has 73 exact texts
and greenhouse 45; their outcomes and selected paths are unchanged from round 2.
Bakery changed eleven successful-ending texts. Greenhouse changed 73 texts,
principally speaker attribution and ordinary-action continuity.

Parent read bakery 42/7 and 6/8, greenhouse 6/7 and 1/8 in full, and reviewed
the shared helper and all nine helper tests. The helper's tests pass locally.
The implementation is small, scenario-independent, uses the existing transition
engine, and detaches mutable validator/event payloads. It is ready for the
second consumer. Historical round sources remain untouched.

The greenhouse worker found an additional concrete bug during the requested
ordinary-action audit: Ivo exited after the door closed. Round 3 enacts both
departures before closure. Tea is now consumed rather than remaining in full
cups after the prose says it was drunk. These are actual state fixes, not just
stricter prose descriptions.

## Round 4: Greenhouse

Adopt `storyscenes.mini_adventures.local_play.LocalPlay` with the stable API
from the bakery report. Keep your `world.LocalPlay` subclass/adaptor and its
scenario-specific relay method. Only replace atomic application/trace recording;
do not rewrite story rules, renderer, sampling or inventory to fit the helper.
Do not edit the shared helper, which now has two ownership consumers.

Prove that all 100 frozen round-3 rows still reproduce exactly, including
episodes and prose, using the serialized parameters/path/seed. Add tests for
helper delegation and initial invalid-state rejection. Run your package tests
plus shared-helper tests. Document the minimal authoring API now available to
the next author; report any migration defect before changing semantics.

## Round 4: Bakery

Confirm the stable shared helper's public contract and bakery's adapter. Do a
release check of CLI and documented outcome recipes, preserved reference and
old samples, and exact reproduction of all frozen round-3 rows. Add a focused
regression only if you find a missing boundary. Do not change generation just
to make counts or success rates better, and do not edit greenhouse files.
Write a final release note with commands/results and remaining limitations.

## Parent Release Checks

After both workers stop editing, freeze 100 matched and 100 previously unseen
seed positions per pack (1000-1049, both lengths). Reproduce frozen sources in
fresh interpreters, read complete unseen-seed stories, inspect counterfactual
tests and library adoption, and run the full StoryScenes suite. Workers need not
sample the held-out range before this check. If a new defect requires repair,
record it explicitly and use round 5, not a silent replacement batch.
