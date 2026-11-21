# Ten measured improvement rounds

Requested 2026-11-03 (America/Los_Angeles). Directory is a stable campaign identifier.

Objective: improve story quality, diversity and reading QA while preserving weighted grammar + executable symbolic kernels + carrier-grounded attention. No runtime LLM, whole-story selection, English repair pass or relaxed physical checks. Baseline: ../luna_short_dialogue_qa_20261103 (140 stories / 815 QA).

Each round needs a concrete implementation change, inspected samples, replay/grounding checks, Luna evaluation using the unchanged prose/QA rubrics, and recorded findings. Development samples use seeds 0–59, selection seed 777, without filtering duplicates. Final evaluation reserves seeds 1000–1059, 20 selected per world. Report development vs held-out scope separately; no fabricated gains or target-score guarantee.

Planned rounds (adapt details to feedback, keep ten completed rounds):
1. QA information density, multi-scene evidence, explicit transformation wording.
2. Rescue: conflict, safe alternative solutions, state-driven ending.
3. Kite: competing goals and material consequences.
4. Key: alternative search/entry solutions and narrative stakes.
5. Music: consent-sensitive choices and satisfying contrasting endings.
6. Greenhouse: competing needs, physical tradeoffs, outcome images.
7. Library: give the atlas decision a visible cost/consequence.
8. Pottery: design choices with meaningful different consequences.
9. Cross-world discourse/attention quality pass based on accumulated evaluations.
10. Final consolidation from evidence; all-world development and fresh held-out evaluation.

Requirements: preserve tokenwise normalized distributions and latent event posterior sampling; pure prediction; physically guarded effects/replay; narrative/QA alignment and evidence spans; dialogue between present characters; short complete stories. Keep frozen portable grammar and historic run artifacts unchanged. Do not optimize false-positive judge flags by making text unnatural. All existing meaningful tests remain green; replace rigid length/padding assertions only with stronger content checks, explaining the change.

Status: complete. All ten rounds measured; matched development and reserved fresh original/final evaluations complete. See FINAL_COMPARISON.md and comparison.json. The final generator stayed unchanged after its round-10 freeze.
