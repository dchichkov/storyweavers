# Interpretation of Luna's evaluation

This is an agent spot-review of the saved outputs, not a second independent rating or a corrected score. Raw ratings remain unchanged in [the report](REPORT.md).

140 past-tense stories and 815 QA pairs were evaluated with gpt-6-luna, Flex, reasoning none. All 14 responses completed on the requested model/tier. Mean story quality was 5.57/9, grammar 8.57, coherence 7.43, style 4.57, and storytelling 5.11. Mean within-world diversity was 0.86/9. QA quality was 7.30/9 on its separate rubric. Luna marked 806/815 questions answerable and 668/815 answers grounded and usable.

## Findings worth acting on

- Prose is grammatical but compressed into a sequence of actions. Dialogue often supplies instructions or announces an intention, without adding much character interaction. Music's repeated refusal and final instruments-on-shelf image received weak closure ratings.
- Variation is mostly wording or a small branch within the same plot. Mechanical text uniqueness substantially overstates narrative diversity.
- Luna tagged 249 QA pairs `too_shallow`. Many second sentences restate the first. Two-sentence length alone is a poor quality target; a second sentence should add supported cause, context or consequence.
- The pottery thumb-rest branch has a concrete text/QA alignment gap in nine sampled stories: “How did Bea use the dent?” presupposes that she turned the dent into the thumb rest, but the narration only says she shaped a thumb rest. The chosen evidence does not mention the dent. Make that transformation explicit in the semantic-to-text plan, or ask only how she made the thumb rest.
- Several evidence excerpts are narrower than the answer's context. For example, pottery's final thumb-rest answer refers back to Bea making the shape, but cites only the final thumb-location sentence. Attach the earlier scene as additional evidence when the answer uses it.

## Judge limitations visible in this run

The raw 81.96% grounded/usable rate is **not an established factual accuracy rate**. Luna was inconsistent about ordinary inference even though its prompt explicitly allowed straightforward local inference:

- It rejected “used a lantern” when the story says “found the key … with the lantern.” This is a likely false positive for the intended instrumental construction.
- It rejected “on her own” as a paraphrase of performing a solo. This is also overly literal in this setting.
- It rejected the inference that the kite could fly from its successful launch and dancing in the sky. The word “again” does add a prior-history presupposition, so the cleaner answer would omit it, but current flight is supported.
- It rejected the handle giving Grandpa a place to grip, despite stating that he held the handle. That objection is overly literal.
- “Neither character was holding a drum” when the drums are on a shelf is a natural default reading but not logically guaranteed by the text alone. Removing this unnecessary negative claim would be clearer than making it an evidence test.
- Listener identity is inferred from adjacent dialogue, not explicit in every speech sentence. Luna accepted this in some worlds and rejected it in pottery. Explicit addressees or narrower answers would remove the ambiguity.

These repeated template judgments affect many pairs at once. Do not interpret 148 `ungrounded_answer` tags as 148 independent bugs, or automatically rewrite all flagged paraphrases. No adjusted accuracy estimate is claimed.

## Next evaluation gate

Keep these artifacts frozen. Improve causal wording and evidence coverage, replace padded answers with informative context (or one sentence for thin traces), and add genuinely different consequences. Then evaluate matched seeds with the same prose rubric. Before relying on QA pass rates, calibrate the QA judge on a small labeled set that includes valid paraphrases, permissible inferences, unsupported claims, and incomplete evidence. Current and historical scores are not a matched before/after experiment.

All 45 local tests passed after adding offline validation tests for the evaluator. Generation rules were unchanged during this evaluation. Initial API attempts could not resolve the API host in the sandbox; their dispatch/errors are preserved separately, and the successful calls used permitted network access. Full token usage: 98,069 input and 60,753 output tokens across the 14 successful responses; no cost estimate is claimed.
