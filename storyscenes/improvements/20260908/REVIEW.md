# Baseline review and improvement hypotheses

Baseline: 10 worlds, 100 uniformly selected judge samples, overall 6.68/9,
style 5.93/9, coherence 6.75/9, diversity 2.20/9. Seventeen samples scored below
6 overall. The original judge protocol and calibration remain unchanged.

Manual review this pass read additional pool samples and the exact lowest-rated
judge inputs for bakery, museum, and library. Judge IDs are zero-based pool
positions (`s000047` means source_index 47); use frozen `quality/inputs.json`
to join notes to text, not an inferred one-based offset.

| Evidence | Shared cause | Intervention |
|---|---|---|
| Bakery, s000047: an accurate label is followed by an ending describing a fresh label. | A renderer's ending is insufficiently conditional on state. | Select complete ending cards against final facts; keep tested bindings and add a trace-aware critic. |
| Museum, s000047: “borrowed borrowed button”, “its condition sound”, “to be pad”. | Raw enum interpolation and grammatical composition are delegated to bespoke code. | Explicit full-phrase lexicon; no raw fallback; common slot expansion and prose lint. |
| Library, s000096: books are balanced before the mayor presents his grand sketch; unused rope/chock loans remain. | The planner accepts any eligible action, while the author omits causal prerequisites for the inciting event. | Backward causal relevance plus replay; authoring contract requires inciting knowledge/promises to enable responses. |
| Puppet, seed 1000 and s000029 family: “held—or did not hold”, “she said, or”. | Conditional alternatives were written into prose instead of executable conditions. | Data-only conditional cards, complete alternatives, deterministic rejection of unresolved branches. |
| Pond, seed 1002: a sail ending mentions linked pads and an anchored log that never happened. | Event IDs are citations, not proof of English entailment. | State-specific endings and fact binding plus semantic review over actual state changes. |
| Most worlds: 49–100 ordered paths but only 1–4 judged plot groups. | Random ordering and alternate routes inflate apparent diversity. | Report order-free scene sets/causal graphs and actual outcome values; require three distinct initial problems and consequences; keep semantic diversity judging. |
| Hill picnic is strongest at 8/9, but dialogue repeatedly explains the method. | The earlier authoring prompt encourages inspection/permission narratives. | Character desires and playful dialogue, shorter support passages, endings that show rather than announce the lesson. |

The changes operationalize the memeplex model: definitions stay fixed, physical
carriers hold changing values, knowledge is copied through observation/telling,
and prose selection reads those values. The prototype still lacks a universal
algebra for every concept, character and whole narrative.

The baseline's one prose-seed control was too weak: seed 1000 and seed 8675309
can choose the same first alternative from a two-item list. The code does use
the supplied RNG in several renderers. This pass checks four prose seeds with
the same world state rather than interpreting one unchanged result as an unused RNG.

Comparison limits: the new batch keeps theater briefs, design seed, sample pool
seeds and judge selection seed fixed. The world plans, authoring interface,
runtime and critic change together. Scores measure the combined intervention;
they do not identify a causal contribution from each individual change.
