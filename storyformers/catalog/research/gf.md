# GF, Codeco and causal grammar-neuron design

Research date: 2026-11-07. Primary sources were consulted directly. The catalog
recommendations below are design proposals, not claims that GF or Codeco already
implements Storyformers. Current local evidence: `storyformers/grammar.py`,
`storyformers/neuron_spec.py`, `storyformers/GRAMMAR.md`, and `story.py`.

## Findings grounded in the sources

**GF separates construction from realization.** An abstract syntax declares
categories and typed constructors; concrete syntaxes map their trees to
language-specific records/tables and eventually strings. Abstract tree formation
can be recursive. Concrete linearization is compositional and reversible, subject
to restrictions needed for parsing. Finite parameter types and tables are useful
for agreement/inflection; dependent types and higher-order abstract syntax are
stronger facilities, not synonyms for ordinary JSON attributes. For our catalog,
retain an abstract construction identity independently of the English trigger
pattern and emitted semantic record. GF does not make an application-specific
syntax tree a verified physical event merely by assigning it a type.
[GF language reference, overview and declarations](https://www.grammaticalframework.org/doc/gf-refman.html).

**GF's RGL is a useful construction inventory.** It distinguishes noun phrases,
common nouns, clauses, sentences, questions, relative clauses, and incomplete
verb phrases. Verb categories distinguish argument requirements: `V`, `V2`,
`V3`, `VS`, `VQ`, `VV`, and mixed complement types such as `V2V`. `VPSlash` and
`ClSlash` represent structures missing complements. Tense, polarity, anteriority,
quantification, coordination, comparison, and embedding are explicit parts of
the interface. Catalog slots such as `expected_complement_type` therefore have a
stronger linguistic motivation than a large collection of unrelated word-pair
flags. This is an inventory source, not a mandate to port its full constructor
API or count each overload as a distinct learned neuron.
[Current RGL synopsis](https://www.grammaticalframework.org/lib/doc/synopsis/).

**Codeco makes discourse dependencies explicit.** Its flat feature structures
support unification; special forward references introduce antecedents, backward
references retrieve them, and scope operators control their accessibility.
Resolution uses accessibility, proximity, and left-dependence: later bindings
cannot determine an earlier reference. Strong references can survive ordinary
scope closure. Predictive completion is derived from the parser's active states,
including feature restrictions, rather than from a bag of recent words. The
result is a set of grammar-compatible continuation options; probabilities over
those options require an additional scoring model. Codeco targets controlled
languages with deterministic interpretation, so its choices should be treated
as candidate constraints for open-ended stories rather than universal laws of
English.
[Kuhn, 2012, sections 3–4](https://arxiv.org/html/1211.3643v1).

**Attempto provides concrete reference-resolution examples.** ACE's documented
rules distinguish reflexive from non-reflexive pronouns, filter antecedents by
agreement and accessibility, and consider recency and specificity. Negation,
modality, subordination, questions, and commands affect accessibility; proper
names are treated differently from ordinary introduced noun phrases. These
rules show why `nearest_entity_id` alone is insufficient. However, ACE's
deterministic conventions are deliberate restrictions: ordinary stories can
retain several plausible antecedents, use cataphora, or employ pragmatic
bridging. Also, a later pronoun can refine an earlier entity interpretation in
whole-text ACE processing; Storyformers must represent that refinement at the
later position instead of silently revising causal training inputs.
[ACE 6.5 interpretation rules](https://attempto.ifi.uzh.ch/site/docs/ace/6.5/ace_interpretationrules.html).

**The deployed grammar demonstrates compact reuse.** AceWiki's published Codeco
grammar separates text, sentence, relative-clause, noun-phrase, verb-phrase, and
reference mechanisms. Its noun phrases share features for identity, number,
human/gender agreement, quantification, and reference status; introduction and
retrieval are compositional operations. Use this as evidence for reusable
parameterized families, not for copying an old ontology editor's lexical
restrictions into a story model.
[AceWiki grammar, dated 2010-12-10](https://attempto.ifi.uzh.ch/site/docs/acewikijava/ch/uzh/ifi/attempto/acewiki/aceowl/acewiki_grammar.html).

## Important differences from the current implementation

| Capability | Current Storyformers evidence | Catalog consequence |
| --- | --- | --- |
| Typed literal tests, membership, presence | `Token`, `OneOf`, `Present` | Native patterns; use registry types. |
| Left-to-right capture and equality | A later test can read an earlier `Ref`; a repeated binding requires whole-record equality | Use entity-id equality explicitly; two mentions of one entity are not equal records. |
| Copy and finite lookup | `Ref` and `Lookup` in projected dictionaries | Native semantic retrieval, given an earlier captured record or `query`. |
| Bounded patterns | `Seq`, weighted `Alt`, finite `Repeat`, explicit `Gap` | Native finite-context recognizers; do not call them arbitrary recursive parsers. |
| Whole-context consumption | Activation requires the pattern to consume all supplied records | Include explicit leading/trailing gaps when describing substring evidence. |
| Native recursive nonterminals | Absent | Recursive tree constructions require compilation/unrolling or an extension. |
| Scope stack, accessible antecedent set, binding domains | Absent | Mark scope-aware retrieval as requiring preprocessing or runtime support. |
| Variable unification | Equality/copy from an already bound record only | General flat-feature unification is an extension. |
| Negative or ordered predicates | No general absence, inequality, numeric comparison, closest-match selector | Declare required capability; do not hide it in a prose condition while labelling the rule native. |
| Whole-span capture and constituent composition | Captures bind one terminal record | Phrase-head approximations are native; span/tree assembly needs an extension or earlier attributes. |
| Atomic evidence for a bundle | Final projection retains joint bundles; intermediate residuals compete per field | Coordinated actor/event/scope hypotheses need a shared hypothesis identity or structured bundle field to avoid mixing incompatible interpretations. |
| Head routing | One neuron per head; all derivations currently contribute | Nearest antecedent or top-one grammar selection is a proposed routing policy, not current behavior. |
| Residual edits | Add/suppress evidence on current query slot only | A catalog operation is not permission to rewrite old tokens or commit external world state. |
| Causal availability | Each head reads only its prefix and previous-layer snapshot | Every proposed input feature needs its own causal provenance; merely masking token positions does not remove annotation leakage. |

For example, after `Lily took`, a head can copy Lily's already established entity
identifier into an actor hypothesis. It cannot know that the object will be
scissors or that the purpose is repair. An output candidate for `scissors` can
carry a candidate patient role and actor link; it becomes the next observed
latent only if selected. `factuality`, modality, quotation, and negation still
determine whether that event is asserted in the story world.

## Suggested catalog record contract

Keep IDs separate from editable names. Treat all entries as hypotheses to test,
with `status: "candidate"` until learned/evaluated. Recommended grammar fields:

- `id`, `name`, `family`, `intent`, `construction` (abstract typed role signature).
- `reads` and `writes`, referring to canonical attribute IDs and expected types.
- `match` (readable DSL where expressible), `captures`, `projection`.
- `prefix_condition` and `availability` (when evidence first becomes available).
- `scope` (current token, clause, discourse, event, entity, or candidate bundle).
- `runtime_support` (`native`, `needs_features`, `needs_extension`) and an exact
  `requires` list; do not use one vague compatibility flag.
- `positive_examples`, `near_miss_examples`, and `ambiguity_notes`.
- `source_ids`, `evidence_level`, and separate learnable `prior_weight` metadata.

Semantic identity needs a field contract: `actor_id` denotes an entity, while
`actor_token_index` denotes a mention position. `grammatical_subject_id` is not
always the actor (passives, experiencer predicates, expletives). A detector for
`pos == "v"` should reuse that predicate; a detector for `a finite verb is
currently expected` names a distinct contextual feature. Unknown is not false.
An evidence-suppressing head does not establish the logical negation of a fact.

## Proposed construction taxonomy

This allocation is a coverage plan for 1024 candidates, not a scientific claim
that English has 1024 constructions. Counts are deliberately uneven. Each
candidate should differ in an interpretable condition, target role, scope, or
operation; reject copies that merely exchange lexical examples or wording.

| Family | Suggested candidates | Distinct subfamilies worth covering |
| --- | ---: | --- |
| Lexical and morphological evidence | 96 | Word classes; finite/nonfinite distinctions; number/person/case; inflectional ambiguity; compound boundaries; lexical sense candidates. |
| Nominal construction | 80 | Determiner–noun composition; adjective restriction; relational nouns; possessives; partitives; apposition; measure phrases; coordinated NPs. |
| Verbal valency and role realization | 96 | Intransitive/transitive/ditransitive; experiencer/stimulus; subject/object complements; prepositional arguments; particles; resultatives; argument alternations. |
| Clause construction and embedding | 96 | Declarative/clausal subject; copular/existential; complementizer; finite/nonfinite embedding; relative attachment; control/raising hypotheses; missing complements. |
| Agreement and grammatical relations | 64 | Subject–verb agreement; pronoun agreement; determiner agreement; coordination agreement; passive role mapping; expletive handling; local binding. |
| Tense, aspect, modality and polarity | 80 | Tense anchoring; anteriority; progressivity; habituality; auxiliaries; modal scope; ability/permission/obligation; local and clausal negation. |
| Quantification and comparison | 64 | Universal/existential/no quantifiers; distributive/collective readings; cardinality; degree; comparative standard; superlative domain; proportional phrases. |
| Reference and discourse entities | 96 | Introduction; name reuse; pronoun candidates; reflexive binding; definite descriptions; demonstratives; bridging candidates; group references; mention salience. |
| Scope and hypothetical contexts | 64 | Conditional antecedent/consequent; negated scope; modal worlds; quotation scope; attribution; attitude embedding; accessible antecedents; asserted versus mentioned facts. |
| Questions and information gaps | 64 | Yes/no and wh; subject/object questions; embedded questions; indirect questions; alternative questions; requested role; answer-type expectation. |
| Coordination and ellipsis | 48 | NP/VP/clause coordination; shared arguments; disjunction; contrast; correlative pairs; gapping hypotheses; omitted repeated subjects; scope alignment. |
| Temporal, causal and discourse links | 64 | Before/after/while; event ordering; cause/reason/result; concession; elaboration; contrast; correction; explanation; purpose without asserted success. |
| Dialogue and perspective | 48 | Speaker/addressee attribution; speech-act candidates; quotation boundaries; reported speech; deictic center; commitment source; questions versus assertions. |
| Event and state construction | 64 | Acquisition/transfer; movement/path; containment/location; creation/destruction; change of state; perception; intention/action/outcome; carrier-grounded concept evidence. |
| **Total** | **1024** | |

The last four families bridge grammar and narrative semantics. Their semantics
must be supported by corpus annotations or other explicit evidence, rather than
presented as consequences of GF syntax alone. Uncertainty is especially important
for discourse relations, control, ellipsis, causal links, and implicit motives.

## Useful head-function families implied by this review

1. Detect a local construction and emit its shared canonical feature.
2. Retrieve the head of a preceding phrase and copy its typed identifier.
3. Fill a grammatical relation while preserving uncertainty about semantic role.
4. Map a validated construction plus verb frame to semantic role candidates.
5. Propagate agreement constraints to the current prefix's expected complement.
6. Track an unresolved typed slot (object, recipient, clausal complement, answer).
7. Filter antecedents by accessibility, local binding, agreement, and salience.
8. Introduce, enter, exit, or retrieve a scope/hypothesis identifier.
9. Preserve reported/negated/hypothetical provenance when copying event facts.
10. Construct candidate next-token bundles consistent with one interpretation.
11. Suppress incompatible candidate evidence without turning unknown into false.
12. Detect insufficient evidence and preserve alternatives or abstain.

Items requiring scope state, selection, constraints, or bundle-level inference
need the capability labels above. Source-inspired names are not evidence that
those capabilities are already implemented or that a learned neuron performs
them reliably.
