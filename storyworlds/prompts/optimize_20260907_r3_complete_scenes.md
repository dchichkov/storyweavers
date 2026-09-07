For this new world, prioritize complete, fluent stories over a large parameter list.
Author three distinct causal story paths: different trouble, information learned,
decision, and visible resolution. Each path must actually simulate and render
its own events. Add alternatives only when every combination remains coherent.

Write each event as a small finished scene in past tense, with natural dialogue
that changes what another character knows or does. Store full sentences rather
than inserting action labels or clauses into sentence slots. Use the selected
characters' names consistently. The final image and each QA answer must describe
what happened on this path, never enumerate what could happen on other paths.
Let the random seed choose different natural phrasings and optional reactions
within those scenes, while preserving their facts and the required seed words.

Keep the implementation small. A brief exchange between both characters is
enough; do not copy an example's arbitrary speech-count quota. Check the actual
resolved state, not a fixed wording. Return exactly n seeded raw samples for -n,
including duplicates; deduplication belongs downstream. Use stable ordered
sampling choices and find the shared helpers through the target's ancestors.
