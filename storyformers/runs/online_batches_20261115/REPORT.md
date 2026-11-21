# Larger online training runs — 2026-11-15

Three independent runs completed ten live Luna/Flex teacher iterations each, at 1, 4 and 12 complete stories per iteration. Model capacity was unchanged: context 32, one layer, 16 head slots, 60-token vocabulary. Each branch starts from the same sentence checkpoint, not from the earlier online pilot.

The four-story batch performed best in this pilot: test accuracy rose from 17.6% to 45.5%, and joint NLL fell from 5.035 to 1.893. The twelve-story batch reached 35.2%; increasing the batch did not monotonically improve learning. The four-story run also learned a useful name-retrieval head and a new string attribute, rather than only changing output productions.

**Free generation remains poor: 0/15 teacher-model samples passed the complete-framing check.** The models now emit title-like phrases, paragraph breaks, and closing fragments, but often stop early, repeat material, or produce malformed clauses. For example, the best-predicting model generated “Tom’s scissors” followed by “One day.”, and another sample generated “Tom took red apples.” followed by “The End.” These contain pieces of the desired format without a complete title/opening/body/closing structure. Several samples are less coherent than the initial short sentences. Lower teacher-forced next-token loss has not yet produced better complete stories.

The control receives ten small output-weight updates; this comparison measures the added value of teacher structural edits in this particular setup. It is not a comparison against a fully trained neural language model. A useful next experiment is to expose the teacher to model-generated continuations and their errors, plus richer rejection feedback, so repairs are tested on the contexts the model actually creates. No such additional training was done here.

## Protocol

Every causal position in a batch contributes to one averaged log-weight gradient. Luna then sees batch summaries, sampled difficult and boundary examples, revealed training documents, relevant grammar roots, residuals, and earlier replay examples. It proposes one bounded program patch. Adoption compares mean loss across the entire current batch and replay; improvement on the showcased example alone is insufficient. Runtime generation remains classical grammar execution.

The three branches share a seeded shuffled training-document order and consume nested subsets of 10, 40, and 120 stories. Each keeps an independent weight-only control using the same gradient and replay gate. Replay contains twelve sentence-anchor positions and up to 64 randomly selected earlier observed targets, with a fixed seed. The gate permits at most 0.02 nats mean replay regression per iteration, requires no additional observed-attribute conflicts, and penalizes added syntax by 0.001 per node. A rejection retains a weight-only update or the unchanged model. This finite gate does not guarantee absence of forgetting.

The three asynchronous branches overlap API waits, sharing one static prompt and a budget ledger that subtracts the earlier pilot’s conservative spend from $10. Updates remain serial and versioned inside each branch. All training finishes before evaluation of validation/test stories 8–23, excluding the first pilot’s 0–7 subset. These are small synthetic-corpus comparisons, not a new general-language benchmark.

## Results

Loss below is joint token/POS NLL in nats; lower is better. Before-update loss is weighted across all newly revealed targets, not measured after fitting their answers.

| Stories/iteration | Targets | Teacher edits accepted | Weight-only / unchanged | Before-update NLL | Test teacher NLL / accuracy | Test control NLL / accuracy |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 226 | 6/10 | 4 / 0 | 3.968 | 3.107 / 28.0% | 4.970 / 17.6% |
| 4 | 853 | 10/10 | 0 / 0 | 3.318 | 1.893 / 45.5% | 4.962 / 17.6% |
| 12 | 2642 | 9/10 | 1 / 0 | 3.766 | 2.411 / 35.2% | 4.962 / 17.6% |

Initial test baseline: **5.035 NLL**, **17.6% accuracy**, 347 targets across 16 stories.

| Split | Initial NLL | Batch 1 teacher / control | Batch 4 teacher / control | Batch 12 teacher / control |
|---|---:|---:|---:|---:|
| validation | 5.114 | 3.233 / 5.047 | 1.982 / 5.038 | 2.446 / 5.037 |
| test | 5.035 | 3.107 / 4.970 | 1.893 / 4.962 | 2.411 / 4.962 |

[Full evaluation](evaluation.json). More data per call also changes prompt length, data diversity, the averaged gradient and replay membership; this is not a statistically powered causal attribution of batch size. There is one stochastic teacher run per size, not multiple replicates.

## Every iteration

| Batch | Iteration | Adopted | Batch NLL before → after | Teacher explanation |
|---:|---:|---|---:|---|
| 1 | [1](batch_01/step_000/decision.json) | weights_only | 5.089 → 5.078 | The batch contains the continuation “A day with Ben,” but the period rule for any context ending in a noun has very large weight, overwhelming the observed preposition with after “A day.” Reduce that broad punctuation preference and add moderate support for a preposition after a determiner–noun ending. Add support for the observed opening determiner and following noun, and for paragraph boundaries after the opening companion phrase and after the sentence in that opener; the latter is deliberately conditioned on the wider visible structure so it does not make every noun-final period a paragraph break, which would conflict with replay examples. The phrase “Long ago,” also gives a reusable local cue for ago and the following comma. These are provisional generalizations from one document: other continuations after a noun or after “Long” remain possible, and other paragraph-boundary contexts may differ. The replay gate has not been evaluated. |
| 1 | [2](batch_01/step_001/decision.json) | teacher | 4.801 → 1.942 | The batch shows a strong but overly broad period preference after nouns, while several observed continuations require a comma after the introductory “One morning,”, a paragraph break after a standalone opening phrase or a period, and an exclamation after “Until next time”. It also underweights the observed noun after “One” and “next”, and a conjunction after a proper noun. These additions favor those local, reusable constructions without treating them as mandatory in other contexts; punctuation and lexical alternatives remain possible elsewhere. The phrase-specific rules are supported by this single revealed document and may be too narrow or overconfident in other stories. Replay behavior has not been evaluated. |
| 1 | [3](batch_01/step_002/decision.json) | weights_only | 3.991 → 3.983 | The batch shows a structural gap at the end of an introductory prepositional time phrase: the model strongly favors a period after a noun, while the observed phrase ending in “On a sunny day” takes a comma. Add a rule for that reusable phrase shape rather than copying the particular adjective or noun. The title-shaped opening “det + adjective(s) + noun” is followed by a paragraph break in the batch, so add a narrowly scoped rule for that opening pattern. Initial A and The both occur as valid determiner starts (including A in replay), so give each modest initial-context support rather than asserting one required opening. Add modest support for a connective after a paragraph break and for an adjective after a determiner. These rules may overpredict commas after other On-phrases, paragraph breaks after noun phrases, or particular lexical choices; they add evidence without making alternatives impossible. |
| 1 | [4](batch_01/step_003/decision.json) | teacher | 3.188 → 2.777 | The observed prefix ends a sentence-initial prepositional phrase (“In a little village,”), but the model strongly favors a period because its noun-final period rule has very high weight; the comma root has little applicable mass. Add a comma rule for the reusable pattern of a space followed by a preposition, determiner, optional adjectives, and a noun. This also expresses the introductory-phrase structure in examples such as “On a sunny day,” without conditioning on a particular place or name. A noun-final period remains valid in other contexts, and prepositional phrases need not always be introductory or comma-terminated, so the rule is limited to the sentence-boundary-like space plus phrase pattern. This is a provisional repair; replay behavior still needs the gate’s evaluation. |
| 1 | [5](batch_01/step_004/decision.json) | teacher | 4.076 → 3.496 | The batch’s “our story” prefix strongly favored a period, although the observed continuation is “ends”; the existing noun-to-period rule is heavily weighted and the ends root has only a weak general rule. Add a focused rule for the visible phrase “our story,” and a focused period rule after “ends” to support the demonstrated closing sequence. These are narrow lexical cues rather than a claim that every noun or verb ends a sentence. Other continuations remain possible, and phrases such as “our story” may continue differently in other contexts; the replay gate must check that these targeted increases do not harm earlier examples. |
| 1 | [6](batch_01/step_005/decision.json) | teacher | 4.870 → 3.706 | The batch exposes an overly broad period rule: a prefix ending in any noun receives very large period mass, even when the observed continuation is a comma, a paragraph break, or a verb such as “ended.” Reduce that rule and add compact suffix patterns for the observed noun-phrase boundaries and for “the story ended.” The latter is deliberately distinguished from the replayed “our story ends.” These patterns may still overfavor the observed constructions in contexts where another continuation is valid; the replay gate should test that risk. |
| 1 | [7](batch_01/step_006/decision.json) | weights_only | 3.466 → 3.460 | The batch shows low probability for several locally predictable continuations: a pronoun after the copula, a paragraph-opening pronoun after a blank-line separator, the temporal phrase Long ago followed by a comma, a manner adverb after a subject, now after a preposition, and a period after an adverb. The patch adds bounded suffix rules for these reusable local patterns without using future or target-derived attributes. It does not force one proper name after the introductory comma; the observed name continuation remains uncertain. These patterns can overgeneralize: not every verb is followed by all, every blank line begins with That or Long, every adverb is sentence-final, or every preposition is followed by now. The additions are provisional and should be checked against replay behavior. |
| 1 | [8](batch_01/step_007/decision.json) | teacher | 3.877 → 2.478 | The batch shows severe underweighting for several supported continuations: the empty prefix favors names over the observed opening article, and the sequence This is where our story ends has very low probability for its local continuations. Add an empty-context article rule and suffix-conditioned rules for the observed clause, using ordinary token/POS outputs rather than asserting story phases or target-only semantics. The batch target and replay examples also support a reusable comma-to-proper-name continuation, so add the same comma-conditioned rule to the available proper-name roots rather than conditioning on Lily or Ben individually. These are provisional local generalizations from limited evidence: other openings, words after is/where, and continuations after commas can be valid. The gate must check replay behavior; this patch is not claimed to have passed it. |
| 1 | [9](batch_01/step_008/decision.json) | teacher | 3.236 → 1.814 | The batch contains a recurring opening idiom, “Long ago,” but the target ago has extremely low probability; the existing generic ago rule contributes little in that context. Add a reusable Long-to-ago continuation and raise comma after ago, both supported by the observed sequence. The concluding phrase “was the end” also has a very low-probability end target, so add a context-specific noun continuation. Long following a noun and paragraph space generalizes the observed temporal-opening pattern without depending on the particular noun. These rules are limited to observed grammatical contexts; other continuations remain possible, and the batch is too small to establish that every Long or every paragraph break requires these words. Replay behavior has not been verified. |
| 1 | [10](batch_01/step_009/decision.json) | weights_only | 3.189 → 3.182 | The batch contains repeated high-loss choices where the target has only a weak generic output rule: “little” after “a”, “story” after “the”, and “In” after a paragraph break. Add modest context-sensitive evidence for those continuations rather than treating the observed document as a fixed template. Also support an article after a preposition, a noun after an adjective, and sentence-final punctuation after a verb, all patterns represented in the batch. These are lexical or syntactic tendencies, not certainties: other adjectives can follow “a”, other nouns can follow “the” or an adjective, and a verb need not end a sentence. Replay examples include adjectives after “The” and varied paragraph openings, so the additions are restricted to their stated contexts and do not rule out alternatives. |
| 4 | [1](batch_04/step_000/decision.json) | teacher | 4.629 → 3.840 | The batch shows a strong punctuation bias after noun-ending prefixes, including opening title-like noun phrases, while the observed A day prefix should continue with “with”; the existing update barely changed these errors. Add a targeted opening-phrase continuation and paragraph breaks for the recurring initial noun-phrase structures. A lower-mass rule supports paragraph breaks after adjective-modified noun phrases in completed clauses, without overwhelming the existing end-of-story prediction after periods. These are hypotheses from the revealed batch, not universal constraints: other continuations after similar phrases remain possible, and the replay gate must check the added mass. |
| 4 | [2](batch_04/step_001/decision.json) | teacher | 4.386 → 3.979 | The gradient update barely changed the representative error: a broad period rule for any context ending in a noun still dominates, even where the batch shows a continuation is needed. Reduce that rule's weight without ruling out periods after nouns. The batch also supports a narrower story-ending pattern: after “the story,” ended is observed; after “our story,” ends is observed. These suffix rules give those verbal continuations useful mass while preserving alternatives. Counterexamples are possible in other uses of those phrases, and periods remain valid after many noun-final contexts; the replay gate should test both effects. |
| 4 | [3](batch_04/step_002/decision.json) | teacher | 3.938 → 2.991 | The batch repeatedly starts with either a determiner-led description or a name, but the representative continuation after a completed action sentence gives nearly all mass to <END> instead of the observed paragraph break. Add a determiner+noun opening pattern, and a paragraph-break rule for completed object-taking action clauses; its verb set avoids also matching terminal phrases such as “was the end.” Add context-conditioned support for recurring constructions in the revealed documents: capitalized continuation after a paragraph break, conjunction after a one-token name opening, article after a preposition, and the “Long ago,” sequence. These rules generalize over POS or reusable lexical constructions rather than copying whole stories. Counterexamples remain possible: a det+noun phrase need not always end an opening paragraph, a paragraph break need not be followed by And or Long, and not every preposition takes a. The added masses are therefore evidence, not claims that alternatives are impossible; the replay gate must assess the provisional repair. |
| 4 | [4](batch_04/step_003/decision.json) | teacher | 4.234 → 3.600 | The batch exposes an overly broad high-weight <END> rule: it treats any final punctuation, including an introductory comma, as a strong story ending. Narrow that evidence by reducing the generic punctuation rule and restoring strong support for endings after end/End/ends followed by a period and after an exclamation mark. The latter also covers the replayed 'story ends.' ending. Names following an introductory comma often repeat a person already named in the prefix; project that captured name and use it to support the matching proper-name output, without requiring a particular name. The batch also repeatedly has a possessive marker after a proper noun, so add a POS-based rule for that continuation. These patterns may still favor an ending after a genuine non-final exclamation mark, or a repeated name after a comma in a context where another continuation is intended; other continuations remain possible, and the replay gate has not been evaluated. |
| 4 | [5](batch_04/step_004/decision.json) | teacher | 3.895 → 3.184 | The batch shows several recurring continuations whose roots are nearly unweighted: “This is where our…”, “That is all…”, opening “On/In …” clauses after an inventory noun and paragraph break, and coda starts after a completed sentence. The weight-only update barely changed the representative target probability, so add modest context-sensitive lexical evidence rather than asserting a single continuation. The coda and starter contexts can admit alternatives; these rules boost observed choices without making them exclusive. Other prefixes ending in these patterns may legitimately continue differently, and the replay gate must check that the added mass does not materially worsen earlier behavior. |
| 4 | [6](batch_04/step_005/decision.json) | teacher | 3.000 → 2.382 | The batch repeatedly exposes a severe start-of-story imbalance: A is nearly absent at the empty prefix despite two observed A targets, while other start tokens have strong empty-prefix rules. Add a strong A rule only for the empty context; this may reduce probability for other valid starts, including replayed Lily, so the replay gate must assess the tradeoff. The batch also repeatedly uses end/End as a noun after the corresponding definite article, and has the phrase Once upon. Add narrowly contextual output evidence for those continuations rather than making the words generally likely. In is observed after a paragraph boundary; a modest boundary-conditioned rule captures that possibility but could compete with other valid paragraph starters. These are provisional repairs and have not passed replay. |
| 4 | [7](batch_04/step_006/decision.json) | teacher | 2.291 → 2.067 | The batch exposes very low probability for several noun targets immediately after a determiner, including story, scissors, time, and day. The existing strong determiner-conditioned mass is concentrated on a few lexical roots, while these noun roots lack comparable evidence. Add a shared structural context pattern to the observed noun roots rather than encoding a complete sentence or a particular name. This should help other prefixes ending in a determiner too, while retaining alternatives: determiners can also precede adjectives, and these lexical rules do not establish that a noun must follow. |
| 4 | [8](batch_04/step_007/decision.json) | teacher | 2.557 → 1.828 | The batch reveals several recurring structural continuations that receive very little mass from the current output roots: a paragraph break after a possessive noun phrase, a new paragraph beginning with The or One after a break, and sunny in the visible On a context. Add bounded suffix rules for those patterns rather than copying whole sentences or changing semantic attributes. The examples support these as useful hypotheses, not exclusive continuations: a break can also precede And or a pronoun in replay, and other words may follow On a or a possessive noun phrase. Moderate rule weights preserve alternatives. The replay gate must still determine whether these additions retain earlier behavior. |
| 4 | [9](batch_04/step_008/decision.json) | teacher | 2.121 → 1.635 | The batch contains repeated causal patterns that the current roots do not adequately support: an introductory preposition after a noun/name and paragraph break, adjectives after “In a” and “On a,” commas after introductory noun phrases, adverbs after a proper noun, “the” after “so,” and sentence-final periods after nouns or verbs. The proposed modest, context-conditioned output masses generalize these observed forms without using target-only information or asserting future story structure. Noun-final contexts are ambiguous and can also continue a sentence, and multiple adverbs or introductory prepositions may be valid; the punctuation and lexical boosts therefore remain limited rather than making alternatives impossible. No replay-gate result is assumed. |
| 4 | [10](batch_04/step_009/decision.json) | teacher | 1.972 → 1.433 | The batch repeatedly exposes weak lexical continuations in the closing phrase “Until next time!”: the existing roots for next and ! have only tiny weights, and time is poorly supported after next. Add bounded suffix rules for these visible contexts. The batch also contains “a little village” and “The End”; local phrase rules raise the observed continuations without asserting anything from later words. These lexical repairs may be too narrow, and next/time or punctuation have valid alternatives in other contexts; the replay gate should assess whether these additions materially harm earlier behavior. No held-out evaluation is available. |
| 12 | [1](batch_12/step_000/decision.json) | weights_only | 4.799 → 4.793 | The batch shows a recurring structural gap: the model assigns almost no mass to paragraph breaks after an opening noun phrase or after an action sentence, while the very large generic period-after-noun rule can overwhelm other continuations. Add reusable noun-phrase patterns for opening descriptions and an action-clause-plus-punctuation pattern for paragraph breaks; add a corresponding action-clause period rule and reduce, rather than remove, the broad period-after-noun evidence. A period after an action clause can also be terminal, so the paragraph-break rule is deliberately moderate and preserves the existing end-token alternative. These patterns may still overgeneralize to unusual noun phrases or action clauses; the replay gate should check both that risk and the impact of the weight reduction. |
| 12 | [2](batch_12/step_001/decision.json) | teacher | 5.146 → 5.066 | The batch shows a specific underweighted continuation: after a prefix ending in “story,” the observed predicate is “ends” or “ended,” but the period rule for any prefix ending in a noun has overwhelming mass. Add a reusable, lexically anchored story-predicate rule to both observed verb roots, rather than weakening noun-final punctuation globally. This should also support other story-final prefixes; it may overfavor these verbs if a story noun is followed by a different continuation, so the rule is limited to that suffix. No new head or feature is needed. This is a provisional repair and has not passed replay gating. |
| 12 | [3](batch_12/step_002/decision.json) | teacher | 4.778 → 4.381 | The batch repeatedly ends the introductory phrase “A day” with the preposition “with,” including the representative prefix and an earlier replay example. The current “with” root has only a weak context-free rule, while the period rule strongly favors punctuation after any noun. Add a context-specific rule for the literal phrase “A day” rather than promoting “with” after all nouns; that avoids competing with the observed comma after “One day.” The batch also repeatedly uses commas after introductory time or setting phrases, but the current comma root is weak and is overwhelmed by the strong noun-to-period rule. Add rules for the observed introductory patterns “One day,” “Once upon a time,” and a preposition followed by a determiner, adjective, and noun. These compact rules may raise comma probability in other contexts sharing those endings, including cases where a different continuation is appropriate; the replay gate should assess that risk. This proposal has not been replay-gated. |
| 12 | [4](batch_12/step_003/decision.json) | teacher | 4.465 → 3.516 | The batch repeatedly ends the phrase “Until next time” with an exclamation mark, but the existing noun-ending period rule overwhelms the weak generic exclamation output. A suffix rule for that reusable phrase raises the appropriate punctuation without removing alternatives. Newline targets occur after several kinds of opening noun phrases and after action sentences ending in a period; the added rules cover those POS-level patterns rather than memorizing complete documents. The period rule could also match a sentence that is final, so the competing end-token option is deliberately retained. The remaining “One morning,” example supports a narrow temporal-introductory comma rule. These are provisional batch-driven repairs; replay behavior and mean loss still require the replay gate. |
| 12 | [5](batch_12/step_004/decision.json) | teacher | 3.588 → 3.227 | The batch shows a structural overgeneralization in <END>: its very heavy rule for any prefix ending in punctuation also matches commas, making it dominate at introductory commas where a character name follows. Reduce that rule and add moderate support for the observed general pattern of a name after a comma; this should help across character names without asserting which particular name must follow. To preserve endings, add a separate rule for several observed closing constructions before final punctuation (including “story ends.”, “the end.”, “all for now.”, and “time!”). These cues are not proof that every occurrence is final, so the added mass is limited. Other comma contexts and unseen ending forms remain potential counterexamples; replay behavior should be checked by the gate. |
| 12 | [6](batch_12/step_005/decision.json) | teacher | 3.155 → 3.029 | At the empty prefix, the model strongly favors proper names because their roots have high-weight empty-context rules, while the observed batch also begins with A three times and The twice. Add moderate empty-context evidence for those two attested determiner starts, weighted roughly in proportion to their batch counts. The rule applies only at the start, preserving named starts and leaving other contexts unchanged. This may overfavor A or The in stories whose initial determiner differs, and the batch does not establish that either is required at every story start; the existing name alternatives remain available. |
| 12 | [7](batch_12/step_006/decision.json) | teacher | 3.218 → 3.004 | The batch repeatedly observes “This is where our” across different stories, while the current output root for “our” has only a weak context-free rule and competing verb candidates receive strong mass after an adverb. Add evidence for “our” after the visible phrase “This is where,” generalizing across the preceding story rather than copying a full document or relying on names. This should improve the seven repeated clause continuations without changing other contexts. It does not make “our” mandatory after “where”; other uses of “where” and alternative continuations remain possible, and replay evaluation is still needed. |
| 12 | [8](batch_12/step_007/decision.json) | teacher | 3.114 → 2.876 | The batch repeatedly uses the opening phrase “Long ago,” and the alternative opening “Once upon a time,” but the generic low-weight roots for ago and upon leave these continuations far below unrelated verbs. The batch also confirms a comma immediately after “Long ago.” Add narrowly suffix-conditioned lexical rules for these observed phrase continuations rather than changing general adverb or punctuation behavior. This should transfer across story subjects while preserving other valid continuations; the rules could overfavor these phrases in other contexts ending in the same words, and the replay gate must check that risk. |
| 12 | [9](batch_12/step_008/decision.json) | teacher | 2.971 → 2.832 | In the batch, an initial proper noun is followed by either “and” or the possessive suffix, but both targets have extremely low probability under the current roots. Add modest, prefix-local support for both continuations after a one-token proper-noun context; the observations do not justify choosing one continuation deterministically, nor conditioning on a particular name. This will not help other initial-noun constructions, and some names may validly continue with a verb or another phrase, so the added mass is limited. Replay examples do not show this exact context. The replay gate still needs to assess whether this provisional repair improves batch loss without materially harming earlier behavior. |
| 12 | [10](batch_12/step_009/decision.json) | teacher | 2.630 → 2.352 | The batch exposes several recurring phrase continuations whose output roots have only weak context-independent support. In particular, “This is where,” “In a little,” “And so the story,” and “that was the end” recur, while the representative prefix ending in “This is” assigns almost all probability to articles and adjectives. Add moderate lexical-suffix evidence for these phrases, plus “One morning” and “One day.” These suffixes generalize across the visible contexts without asserting anything from later words or copying whole stories. They are not universal rules: “is” can continue differently, “In a” need not always be followed by “little,” and “One” can precede other nouns, so the added evidence should not eliminate alternatives. The replay gate has not yet tested this provisional repair. |

## Unfiltered generations

Empty prompt, seeds 0–4, up to 64 tokens; generated latents and framing checks are saved in [samples.json](samples.json). These show actual free generation rather than target-conditioned prediction.

### initial

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Tom found the red needles.
```

Seed 1:

```text
Ben took the red pears.
```

Seed 2:

```text
Tom took red apples.
```

Seed 3:

```text
Ben slowly found the small apples.
```

Seed 4:

```text
Ben quickly found small apples.
```

### batch_01_teacher

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Tom and scissors.

scissors.

scissors.
```

Seed 1:

```text
The small
```

Seed 2:

```text
Tom took red apples

Long ate small pears

Long ago,
```

Seed 3:

```text
Ben and needles.

red red found small needles

Long took the small apples

Long ago found the red scissors

Long ago took the apples.

took the needles,
```

Seed 4:

```text
Ben quickly found small apples

Long found the red pears

Long ago,
```

### batch_01_weights_only

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Tom found the red needles.
```

Seed 1:

```text
Ben took the red pears.
```

Seed 2:

```text
Tom took red apples.
```

Seed 3:

```text
Ben slowly found the small apples.
```

Seed 4:

```text
Ben quickly found small apples.
```

### batch_04_teacher

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Tom's scissors

One day.
```

Seed 1:

```text
A time

And Lily slowly took apples, Lily found the story, Lily's the time.. Lily slowly used the day.

And scissors.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The day

The scissors, the time!
```

Seed 4:

```text
The small the small red the time.
```

### batch_04_weights_only

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Tom found the red needles.
```

Seed 1:

```text
Ben took the red pears.
```

Seed 2:

```text
Tom took red apples.
```

Seed 3:

```text
Ben slowly found the small apples.
```

Seed 4:

```text
Ben quickly found small apples.
```

### batch_12_teacher

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Mia found the red needles.

needles.
```

Seed 1:

```text
A small
```

Seed 2:

```text
Tom took red apples.

.
```

Seed 3:

```text
A small the small.
```

Seed 4:

```text
A red the red red the small
```

### batch_12_weights_only

Complete framing: 0/5; emitted END: 5/5.

Seed 0:

```text
Tom found the red needles.
```

Seed 1:

```text
Ben took the red pears.
```

Seed 2:

```text
Tom took red apples.
```

Seed 3:

```text
Ben slowly found the small apples.
```

Seed 4:

```text
Ben quickly found small apples.
```

## Learned structure

| Batch | Added output productions | Occupied heads | New declared fields |
|---:|---:|---:|---|
| 1 | 25 | 1 | none |
| 4 | 56 | 2 | preceding_person_token |
| 12 | 29 | 1 | none |

The four-story run's fourth iteration introduced `capture_person_before_comma` and the string field `preceding_person_token`. Its grammar captures a proper noun somewhere earlier in a prefix that ends in a comma, projects the captured surface token onto the current residual position, and lets four name-output rules read that field. It does not infer an actor from future text, and it is not a general coreference resolver or a guarantee of selecting the nearest name.

Four controlled probes changed only the name in “NAME and the pears” followed by a paragraph break and “One day,”. The head returned the corresponding Ben/Lily/Mia/Tom value each time, and that name received about 70.7–70.9% next-token probability. With the final model's output weights and consumers held fixed, disabling this head worsened test NLL from **1.893 to 2.082** and accuracy from **45.5% to 42.1%**. This inference-only ablation supports a measurable contribution from the learned feature. [Probe records and ablation](head_probe.json).

Teacher proposals have access to only a bounded view of the program and replay examples. The previous-decision feedback currently reports adoption/error, not detailed rejected-candidate loss deltas. Richer rejection feedback is a useful next experiment; this run did not change that interface midway.

## Usage and verification

All **30 calls** settled and reported **gpt-6-luna / Flex**. Cache-hit calls: **29/30**; cache reads **85,724 tokens**, writes **2,956 tokens**. Total input **503,460**, output including reasoning **102,891 tokens**. Concurrent initial requests may write the prefix more than once; later requests reuse identical content.

Estimated new API cost: **$0.047075**. Conservative new ledger: **$0.052260**; including the earlier pilot: **$0.059913**, below $10. These are usage-based estimates, not an invoice. See [budget.json](budget.json) and [audit.json](audit.json).

One final request failed during TLS connection setup. The identical request was retried with its original idempotency key; original attempt and failure journals were preserved. The saved response was then processed by the normal replay gate on resume. No committed iteration was repeated. See [recovery record](batch_04/step_009/connection_recovery.json).

All **152 tests passed**, including batch-wide rejection and control/checkpoint resumption. Source files and data hashes match the manifest; all 30 checkpoint transitions, receipts, request fingerprints and shared prefixes were audited. Each branch saves its final teacher and weight-only checkpoints, and each step retains the teacher proposal, evidence, replay, receipt and decision. Raw provider request/response caches remain local.

```sh
.venv/bin/python -m storyformers.online_batches \
  --out storyformers/runs/online_batches_20261115
```

The command resumes the recorded run. A new output directory creates new paid requests with a separate suite ledger. [Protocol](../../ONLINE.md).
