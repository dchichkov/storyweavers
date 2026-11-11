# Catalog review and limits

Reviewed on 2026-11-07 for the standalone Storyformers experiment. The deliverable
is a broad, revisable candidate catalog, with a selected executable subset.
Validation of a witness is not evidence that the proposed semantic function has
been learned or that it generalizes to arbitrary stories.

## Coverage and provenance

- Exactly 1,024 attributes, 1,024 heads and 1,024 grammar records, organized into
  32 families. Every grammar has a positive and a contrastive witness.
- Local review includes the current matcher, residual representation, projection,
  induction/review tooling, Grammarworlds candidate attribute construction,
  symbolic head contracts, research inventory, and physical-carrier design.
- [The predecessor crosswalk](research/head_crosswalk.json) covers every P001–P064
  contract: 24 adaptation routes, 34 partial correspondences and six explicit
  gaps. It records source hashes and actual target operations. A correspondence
  does not imply executable equivalence.
- [GF/Codeco/Attempto research](research/gf.md) and
  [SAE/circuit research](research/sae.md) distinguish source findings from proposed
  symbolic designs. The source manifest identifies research motivation separately
  from local implementation evidence.

The review was divided across linguistic, world and mental-domain authors, then
cross-reviewed. The root implementation and integration checks additionally cover
the core shard and shared catalog interfaces. Per-shard findings are retained in
[review_core.md](research/review_core.md),
[review_linguistic.md](research/review_linguistic.md) and
[review_mind.md](research/review_mind.md), with a further native world audit in
[review_world.md](research/review_world.md). An independent pass over all 192
world adapter contracts and 384 fixtures is recorded in
[review_world_adapters.md](research/review_world_adapters.md).

## Corrections made during review

| Issue | Resulting design |
|---|---|
| Raw `second`, `since`, `about` and unit lookups ignored an explicitly incompatible sense | Selected-sense gates on ambiguous core lookups; adversarial regression cases |
| Lexical sense producers and consumers used different IDs for scissors/rabbit | Shared canonical IDs; an executed sense-to-gloss composition check |
| A modal auxiliary was labeled as grammatical mood | Separate modal meaning and a narrow actual subjunctive seed |
| Negation/punctuation seeds disagreed with the annotation POS convention | Accept the actual compact `part`/`adv` and synthetic `punct` values |
| `themselves` forced plural and `heard singing` forced one parse | Retain the number/parse uncertainty supported by the visible prefix |
| Suppression descriptions only emitted correction metadata | Ten explicit add-versus-suppress contracts; suppression targets exact old values and preserves provenance |
| Mental-field winners could mix two incompatible source tuples | All mental heads require semantic adapters; 64 finite matcher seeds retained separately for reuse |
| Observed token status could defeat a new candidate-status field | Candidate status belongs inside a correlated hypothesis envelope |
| Adjacency was treated as sufficient evidence of an attitude holder | Cue adapters require construction role binding, including the `friend of Mia believes` counterexample |
| Several mental witnesses inferred unstated motives, knowledge, channels or narrative closure | Explicit evidence added or values weakened; written saying no longer implies speech |
| World contrast examples sometimes incorrectly demanded abstention for a different valid state | Contrasts distinguish changed values from absence of a match |
| World output mixed trace provenance into an undeclared patch | Provenance recorded as trace metadata; payload expectations remain explicit |
| Progressive `growing` was tagged as an adjective | Narrow adjectival growth-state seed uses `dormant` |
| A shared event/scope was enough to transfer claim provenance | Require the selected source claim as well; test mismatched events, scopes and missing claim identity |
| Numeric/temporal witnesses omitted promised domain and precision constraints | Explicit interval boundaries, time anchors, original units, conversion provenance and quantity ownership |
| The last nearby entity was treated as a copular subject or movement actor | Explicit equality against supplied subject/actor IDs and role-mismatch contrasts for every native world seed |
| Movement/event words admitted unrelated senses and landmarks | Selected-sense gates; movement type and same-event landmark-role bindings |
| Hyphenated lookup forms and material labels did not match their intended meanings | Remove unreachable forms, distinguish composition from appearance, and use direct absorbency contrasts |
| Requests, permissions and gifts were mistaken for completed custody transfers | Explicit acceptance and physical handoff premises; ownership and holding kept separate |
| Causal and access witnesses asserted stronger conclusions than their premises | Name the counterfactual effect, distinguish necessary/sufficient causes, and state reachability, support-loss and bottleneck premises |
| Some scoped interpretations and role references were lost in contrast cases | Preserve imagined locations and belief holders; bind actual role fillers with visible entity IDs |

These are corrections to the proposed catalog, not changes to gen6, gen7, the
Grammarworlds engine or the existing Storyformer residual algorithm.

## Reproducible checks

[validation.json](validation.json) records counts, capability requirements and
SHA-256 hashes of the generated artifacts. The builder checks IDs, key uniqueness,
types, links, protected fields, support labels, annotation enums and duplicate
native definitions. All native positive/contrastive witnesses are executed. Each
native head is checked through a causal block with an appended unseen future;
native suppressors must actually subtract evidence. Executable matcher seeds
inside adapter contracts are counted and tested separately from complete heads.

The integration tests additionally exercise canonical sense reuse, incompatible
sense rejection, refusal to load adapters, space/position handling, crosswalk
links, suppression producer metadata, deterministic regeneration and a complete
next-latent distribution using a catalog head. The broader Storyformers tests
cover the existing model and annotation/review paths using local mocks. No paid
annotation or training requests are needed for these checks.

Run the commands in [README.md](README.md#research-and-verification) to reproduce
the catalog audit. Run all Storyformers tests from the repository root with:

```sh
.venv/bin/python -m unittest discover -s storyformers -t . -p 'test_*.py'
```

Final verification: **109 tests passed**. Deterministic regeneration and artifact
hashes match. The catalog audit executes **566 native fixtures**, **128 retained
adapter seed fixtures**, **238 causal-prefix checks** and **four native
suppression checks**. The remaining six suppression operations are adapter
contracts. All 602 world witnesses retain their projected entity references in
the visible prefix; this checks binding shape, not the semantic algorithms.

## Remaining limitations

1. **Semantic proposals need corpus evaluation.** Fixtures are authored
   illustrations. They neither measure precision/recall nor establish the right
   granularity of the 1,024 fields. No held-out story quality, generation speed,
   training convergence or transformer-equivalent compute claim is made.
2. **Contracts are not parsers.** Their guards and projections are explicit
   implementation requirements. Most do not run in the current matcher. The 64
   retained mental seeds do not test semantic guards or atomic routing.
3. **Native coverage is deliberately narrow.** Finite lexical tables and short
   patterns support seeds for learning. They are not an exported WordNet lexicon,
   complete GF grammar or robust contextual disambiguator. Nonactivation can
   mean missing coverage. The runtime also has finite matching-state limits.
4. **Scope and correlation need enforcement.** Some scalar fields refer to a
   selected phrase, claim or source rather than the token itself. Consumers must
   respect their declared scope. Current residual competition alone supplies no
   general type system for parse nodes or correlated alternatives.
5. **Causal input remains a data requirement.** Prefix masking cannot detect a
   retrospective annotation. Contract witnesses are not automatically valid
   training records merely because their text is a prefix. In particular, a
   sense attached to an earlier verb cannot have been chosen using its later
   object. Native examples test downstream behavior conditional on supplied
   bindings; they do not prove the upstream annotator can supply those bindings.
6. **Residual inhibition is evidence subtraction.** It is neither logical
   negation nor guaranteed deletion of an observed value. It writes at the
   current query; historical latents and the physical world remain unchanged.
7. **The integrated learning loop is future work.** Rolling multi-batch proposal
   statistics, LLM revision scheduling, head-weight learning, model-version
   replay, bank routing and acceptance thresholds require implementation and
   evaluation. The catalog is prepared to supply candidates and canonical names.
8. **Readout remains vocabulary-dependent.** These grammar templates do not
   independently define a language model. A final projection still needs learned
   complete next-latent bundles, normalized joint masses and token marginals.

The memeplex north star is preserved by treating grammatical expectations,
beliefs and predicted actions as scoped hypotheses. They cannot become committed
physical facts without an explicitly bound carrier and a separately implemented
world transition.
