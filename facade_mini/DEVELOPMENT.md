# Second pass: a fuller authored drama

Started October 24, 2026, 16:47 America/Los_Angeles. The user explicitly rejected
the first delivery's small scope. The original source, tests, examples, and review
are frozen in `versions/v1/` for honest comparison.

Acceptance criteria for this pass:

1. Expand the dramatic material substantially, including histories, interests,
   difficult choices, aftermath, and emotionally distinct responses. Inventory
   measures are descriptive, not a target obtained by splitting short beats.
2. Support at least three causally different constructive routes. One must work
   without explicit `reflect` commands and one must involve a practical negotiated
   commitment rather than emotional reconciliation.
3. Model a private conversation, audience-specific knowledge, an explicit promise,
   betrayal, and a consequence that persists beyond one reaction line.
4. Replace once-per-evening apology memory with offense-specific repair. Prevent
   repeated apologies for one incident from farming trust.
5. Let characters initiate disclosure and responsibility-taking from state.
6. Provide a usable local browser interface alongside the terminal and replay.
7. Read complete samples in at least two review/repair rounds, preserve rough
   outputs and defects, run deterministic counterfactuals, and test a predeclared
   final set of seeds 1000–1199 after repairs.

No runtime LLM, external service, or changes outside this standalone directory.
No claim of reproducing Façade's production scale or measuring a labor speedup.

## Completion

Completed the expanded delivery around 17:50 America/Los_Angeles on October 24,
2026, after roughly one hour of implementation, reading, repairs, and checks.
All seven acceptance criteria have concrete witnesses:

1. The loaded inventory grew to 27 short beats, 80 goals, 183 performance slots,
   and eight endings. Exact definitions are in `audit.json`.
2. `examples/initiative.txt`, `private.txt`, and `practical.txt` provide three
   distinct constructive routes alongside direct mediation. The practical route
   requires neither empathy nor reflection; initiative requires no mediation.
3. Private and betrayal demonstrations plus audience regression tests cover
   confidentiality and a persistent breach.
4. Tests cover a new offense permitting a new apology and repeated apologies
   for the same incident giving no additional trust.
5. The initiative demonstration contains voluntary disclosure, accountability,
   and a joint proposal driven by readiness state.
6. The standalone browser player has been opened and visually inspected; local
   HTTP tests cover session isolation and save/load. CLI replay/resume also ran
   from an isolated copy.
7. Two review rounds, frozen source, rough transcripts, and the initial failing
   audit are retained under `reviews/`. Final results: 35 passing tests; 1,000
   passing development sessions and 400 passing reserved sessions. The reserved
   range was not used to tune the implementation.

See `REVIEW.md` for the full results, causal comparison, policy definitions, and
limitations. These checks establish mechanical consistency and demonstrated
routes, not independent literary quality or authoring-cost savings.
