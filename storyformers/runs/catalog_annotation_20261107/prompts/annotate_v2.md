# Whole-story annotation trial — batch prompt v2

You are annotating one complete story into symbolic per-word latents. Read the
whole story and interpret every occurrence in context. This trial deliberately
permits later text to resolve earlier references, intentions, quotation speakers
and narrative functions. There is NO causal-prefix filter. Still preserve what
is true at each narrated time: a later repair does not make the earlier object
already repaired, and a character's false belief is not narrator truth.

## Inputs

Read the assigned `inputs/STORY_ID/story.txt` and `indexed_words.txt`. The latter
gives paragraph numbers and zero-based word ordinals `w`; exact lossless token
indices and positions are in `tokens.json`. Do not change source text or split
contractions. Words, punctuation and whitespace must reconstruct the story.

Read ALL FOUR feature-description files in this directory:
`features_core.txt`, `features_linguistic.txt`, `features_world.txt`,
`features_mind.txt`. Together they define the 1,024 available attributes per
word. `feature_index.tsv` is a compact navigation aid. Consult the original
`storyformers/catalog/attributes.jsonl` for more metadata when necessary.
Catalog availability/prefix restrictions describe the future causal model;
they do not restrict this explicitly retrospective annotation experiment.
Read `catalog_overrides.json` too: `patients` and `instruments` contain eN IDs,
as required by the existing annotation pipeline. The original catalog's claim
that these arrays contain display names is a documented erratum. Other meanings
and types remain those of the supplied catalog.

## What to annotate

Use sparse dictionaries over all 1,024 available fields. Omitted means unknown,
not applicable or not annotated, never false. Do not emit 1,024 nulls per word,
force a feature quota, or invent unsupported facts to use more fields. Keep
boolean false when the text actually supports a negative proposition.

1. Give EVERY word an explicitly chosen POS and lemma, including function words,
   dialogue, contractions and numbers. POS is `n v adj adv pron det adp conj num
   part intj unknown`. Proper names use `n`. Use contextual POS; do not use a
   global surface-word POS dictionary, suffix guesser, or default-all-nouns.
2. Resolve important named people, places, objects, groups and their anaphoric
   mentions to stable eN identities. Distinguish old/replacement objects, picture
   objects and actual objects, a puppet character and the puppeteer, owner and
   current holder. Unknown unnamed referents can remain unresolved with feedback.
3. Annotate predicates, including physical action, state, perception, speech,
   desire, thought, negation, plans and conditions. Events use evN IDs. Assign
   actor/patient/instrument/recipient roles from syntax and meaning, not proximity.
   `event_type` uses obtain/transfer/repair/move/perceive/speak/feel/state/other.
   `factuality` uses asserted/negated/desired/hypothetical/reported.
4. Annotate supported grammatical and semantic features on the words that
   express them: tense/aspect, determiners, number, modality, negation, quantities,
   time, spatial relations, object changes, possession, goals, affect, beliefs,
   dialogue acts, discourse links and narrative changes. Function words are
   meaningful too: their grammatical/semantic feature can be the main label.
5. Maintain quotation, imagined, conditional, remembered and belief scopes.
   Register the speaker/holder. An actual act of saying or believing is distinct
   from the truth of its content. Repeated sentences or reports need distinct
   utterance instances, while a recalled or repeatedly mentioned underlying
   repair keeps its original event identity. Use `a.mention_event` for a new
   mention of an existing event. Separate actual repetitions (three knocks,
   rehearsal versus performance) into new events. Auxiliaries, negation and
   condition markers are usually operators, not extra events. Retain ambiguity
   rather than silently picking an unsupported
   identity, motivation or outcome.
6. Preserve correlated object-valued features using the catalog's bundle shape
   where shown: entity/holder + scope + status + value. Participant IDs must refer
   to registered entities. Add evidence word anchors and a note for substantial
   inferred, retrospective, ambiguous, mental or narrative interpretations.

Teacher-label status: explicit narrator facts use `assertion_status="asserted"`;
character assertions/beliefs use `"attributed_claim"` in their scope; uncertain
annotator interpretations use `"candidate"` with an evidence note. The catalog's
candidate-status examples describe proposed model outputs; do not mechanically
mark every teacher fact candidate. An explicitly narrated fictional fact can be
asserted within a fictional scope while remaining separate from physical reality.
Keep uncertainty, event factuality and holder belief truth distinct.
Use only these three `assertion_status` values, including inside object bundles.
Keep desired/hypothetical/negated/reported in `factuality`; keep promises in
`plan_commitment_status` and their quotation/scope. A quoted promise can have
`assertion_status="attributed_claim"`, `factuality="desired"` and
`plan_commitment_status="promised"`; it does not assert completed action.

Contraction policy: keep the token, POS of its leading syntactic component, and
lemma of that component. `I'd` has pos=pron, lemma=`I`, expansion `["I","would"]`
or `["I","had"]` as context decides; `couldn't` has pos=v, lemma=`can`, expansion
`["could","not"]`; `won't` has lemma=`will`. A possessive `Nia's` has pos=n,
lemma=`Nia` and possessive morphology, not an invented auxiliary expansion.
Preserve proper-name capitalization in lemmas. Explicitly correct inflected verb
and plural noun lemmas; lowercased spelling alone is only sufficient for an
already uninflected common word. Do not invent dollar/cents units for copper
coins, or turn an added half-hour detour into a total journey duration.

Shared lemma convention: normalize modal forms `could→can`, `would→will`,
`should→shall`, `might→may`; preserve their contextual force/tense separately.
Normalize objective personal pronouns `me→I`, `him→he`, `her→she`, `us→we`,
`them→they`. The subject pronoun `I` stays capitalized. Possessive determiners
`my/her/his/our/their` keep their own forms; do not treat determiner `her` as the
object pronoun. Reflexives and independent possessives keep their own forms.

Do not blanket-copy an event, physical location, emotion or goal onto an entire
sentence or every occurrence of a word. Annotate the appropriate lexical head,
operator or explicitly linked mention. An adjective can refer to its modified
entity when that binding is clear. Multiword proper names may share an entity ID.

The trial provisionally adds `event_bindings: array` to preserve every
`{event_id, role, scope_id}` membership when one mention serves several predicates.
The singular `event_id`/`role` prioritizes the word's first trigger event, otherwise
its first participant association; the array is
authoritative for multiple associations. This is different from the catalog's
`event_role_conflict` diagnostic. Further new attributes are welcome when a real
meaning is missing: register type, definition, scope, example and why existing
fields do not express it. Do not rename a known meaning just for convenience.

## Small consistency examples

In `Nia borrowed a can. She returned it to Bell.`, the same can ID appears at
`can` and `it`; Nia is the borrower and Bell can be the return recipient if the
story establishes that. Borrowing does not establish ownership. The borrow and
return predicates receive different event IDs and state-appropriate holders.

In `Ben believed the star was lost. Later Nia found it.`, belief holder is Ben;
the belief-content proposition and the actual finding are separate records.
Full-story context may resolve `it` to the star, but it does not erase Ben's
earlier belief or imply that he knew the later result.

For `couldn't`, preserve the exact token, annotate its contextual verb POS and
`contraction_expansion=["could","not"]`; attach the negation to its actual
predicate/scope. Do not turn every negative word into a globally false event.
For `I'd`, inspect context before choosing `I would` versus `I had`.

## Authoring and deliverables

Work only in `annotations/STORY_ID/`. Keep a reproducible `author.py` and use
the provided `authoring.py` helper, which assembles positions/gaps and validates
types/links; it does not infer POS, entities or events. You may write direct JSON
instead if it obeys the same schema and verification. Do not call any paid API.

Example setup (author.py is two directories below this run directory):

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a = Annotation("STORY_ID", prompt_version="v2")
# Each paragraph receives one manually chosen POS tag per word.
a.tag(0, "n v det n", {"borrowed": "borrow", "Nia": "Nia"})
a.entity("e1", "Nia", "person", [0])
a.entity("e2", "watering can", "watering_can", [3])
a.event("ev1", 1, "borrow watering can", type="obtain", actor="e1",
        patients=["e2"], roles={"actor": [0], "patient": [3]})
a.feature(2, determiner_kind="indefinite_article", definiteness="indefinite")
# Define scopes before the events contained in them. scope(words=range(...))
# uses explicit word ordinals, end exclusive. Explicit feature writes can
# include evidence=[word_ids] and note="why this interpretation".
a.save({"summary": "...", "ambiguities": [], "feature_gaps": [],
        "prompt_feedback": [], "coverage_notes": "...", "reviewed_all_words": True})
```

Read the helper for signatures. `a.tag` requires exact per-paragraph tag counts;
lemma overrides can use a word ordinal or exact surface token. Its unoverridden
lemma is just lowercased spelling, so explicitly fix inflections, plurals,
possessives, proper names and contractions. `a.entity` mention lists are explicit
word ordinals, not string searches. `a.feature` can attach additional typed
attributes. `a.proposition` registers pN content; `a.extension` registers a new
field. Its generated spaces/punctuation have no invented semantic labels.

Run your authoring script, inspect annotations against the whole text, repair
failures and save these outputs: annotations.jsonl, entities.json, events.json,
scopes.json, propositions.json, evidence.json, new_attributes.json, feedback.json,
metadata.json and validation.json. Every word must be represented; substantial
content words must have contextual semantic annotation, not just POS. Review
all paragraphs for missed references, predicates, operators and state changes.
If a hard case remains, mark it in feedback with concrete word IDs and options.

Your final message should report counts, meaningful feature/naming gaps,
uncertainties, prompt improvements and verification. Do not claim machine
validation proves semantic correctness. Preserve uncertainty and give actionable
feedback for the next batch.

Anchor units: helper word arguments, evidence and support use zero-based word
ordinals `w`. `index` and `position.token` count all lossless tokens including
spaces. Catalog `tN` anchors are one-based nonspace tokens including punctuation;
use `a.anchor(w)` when writing these. Do not subtract or compare unlike units.
Multiple real/fictional events at one trigger may use `primary=False`; the
secondary event stays correlated in the event table and `event_bindings`.
Its scalar participant fields must not overwrite the primary event's fields.


## Lessons from the two reviewed pilots (v1)

Read `pilot_examples_v1.json` for concrete excerpts of the reviewed pilots, and
`extension_registry_v2.json` for agreed provisional fields beyond the 1,024-item
catalog. Reuse these exact definitions with `a.use_extension("appearance_color")`
(or another listed key) when needed. Only `event_bindings` is preinstalled.
New meanings can still be proposed with `a.extension`; explain why neither the
catalog nor this registry covers them. Existing meanings must not acquire a
fresh name just because another story expresses them differently.

- Separate the attitude/utterance from its content. For `Lily wants Ben to have
  scissors`, the desire event has holder Lily; its content proposition is `Ben
  has scissors`. Do not make goal_content_id point to `Lily wants Ben to have
  scissors`. The latter can be a separate proposition used when reporting her
  desire. Apply the same rule to promises, obligations and beliefs.
- `I do not want X` establishes absence of a positive desire. It does not by
  itself establish an active goal to avoid X. Negated desire, avoidance, factual
  negation, prohibition and desired future absence are different analyses.
- Semantic actor and grammatical subject are separate. In `That money buys a
  cake`, the money is the grammatical subject even if a person is the buyer.
  Select grammatical_subject_id from syntax; never copy actor_id unconditionally.
- Give distinct IDs to actual utterances; reuse an underlying event across
  recalls, reported clauses and ellipsis. Repeated enactments/tests are different
  events. A repeated scripted direction can refer to the same scripted event
  while its readings are separate physical utterances.
- Separate physical performer, puppet/prop, fictional character/object and
  performance world using `enactment` when needed. Voicing a character does not
  establish who physically moved its prop. Likewise, preserve an explicit
  metonymic/realization bridge when a role mention names a part or physical prop
  but the event participant is a whole or represented character.
- Scalar fields describe the primary event. Keep secondary event participants
  together in the event table/bindings. Label a content event by the intended
  action/state, and record offer/request/promise on the separate communication
  event so the actor does not accidentally become the speaker.
- Restricted emptiness is not universal absence: an empty delivery basket can
  still hold its towel; an empty theatre can still contain the friends. A pocket
  lining is a part of a pocket, not an object contained in it.
- Distinguish color from material, reflected light from emitted light, and
  figurative comparison from literal identity. Use `appearance_color` for bound
  color facts; brass material does not entail a gold material object.
- Preserve source continuity gaps and unresolved reference alternatives in
  feedback. Do not invent a retrieval, handoff, construction, return or recovery
  merely because an object changes position or reappears later. Endpoint states
  can be explicit even when the transition is absent from the text.
- Status must remain consistent inside bundles: assertion_status is asserted,
  attributed_claim or candidate. Keep factuality, commitment and scope separate.
  Bodily cues may support an explicitly marked interpretation; they do not prove
  a permanent trait, exact emotional intensity or complete recovery.

After writing the output, check these high-risk distinctions paragraph by
paragraph. Record unresolved cases in feedback rather than filling them by
analogy with another borrowing/repair story. Stop at supported sparse annotation;
coverage is not a quota and the 1,024 fields are not all expected to be active.


## Lessons from the first six-story batch (v2)

1. **Content and polarity.** A negation operator targets a positive proposition
   such as “Tomas finishes the race.” A statement reporting nonfinish may instead
   reference a separate negative proposition. Do not negate that negative
   proposition a second time. Event labels describe the underlying predicate;
   factuality/polarity carry the negation. The actual act of denying has its own
   utterance event. “Not my whale” reports a rejected candidate, not merely the
   broad problem of the book being missing.
2. **Information goals.** “I want to see if the sled can keep up” desires an
   answer, not that the sled succeeds. Keep the information-seeking goal separate
   from the open test proposition. A conditional “would have to admit” describes
   a consequence/requirement, not an intention to admit. Mark a conjunctive goal
   achieved only when every required part is supported: watching an anemone open
   does not establish having watched it open and close.
3. **Quotation inheritance.** A condition or question inside a quote remains
   attributed even if its scope ID is sN rather than qN. Inspect scope ancestry,
   not spelling. A later quoted mention of a narrator-established event retains
   the event's factuality but gets the quote's local assertion attribution.
   Check quotation audiences against utterance recipients. A joint obligation
   group is not automatically the speaker's audience.
4. **Beliefs as causes.** An actual attitude of certainty can cause an action;
   its false content must not be promoted to an actual-world causal fact. Bind
   the causal relation to the attitude event and keep the believed proposition
   as its content.
5. **Physical distinctions.** A carrier supporting an object differs from a
   weight restraining it from above. Support capacity differs from actual
   placement. Accept the proposed `affordance_supporting` field with a bound
   surface/object and explicit `can_support: true`; omit unknown placement.
   Prefer an existing typed field such as `object_temperature` over an ad hoc
   legacy description when the meanings coincide.
6. **Syntax and roles.** A prepositional complement is not a grammatical direct
   object. A body part can be the grammatical subject while its person is the
   semantic perceiver. An individual can be credited for a contribution to a
   joint event without becoming identical to its collective actor. Retain an
   explicit contribution/divided-labor bridge. Past morphology does not prove
   an anticipated or prevented event actually happened.
7. **Source gaps and evidence.** Keep endpoint states with missing transitions:
   bookmark on floor versus later inside book, sign in reeds versus folded
   blanket, jug on blanket versus in basket. Never invent a repair transition.
   Also keep unresolved event identity and chronology in earlier reports. A
   named label owner does not identify the label's author.
8. **Wire format and common values.** Legacy `attributes` is an array of
   `{"name": "...", "value": "..."}` pairs with string values, not strings or
   booleans. True/false semantic features belong in their typed catalog fields.
   Use `goal_polarity=achieve/avoid`, `belief_polarity=accepts/rejects`, and
   `proposition_polarity=positive/negative` for these distinct meanings. Keep
   assertion status limited to asserted/attributed_claim/candidate throughout
   nested bundles.

9. **Consent and participation.** A refusal of program participation does not
   prohibit later tapping from a seat or joining an informal duet. Bind consent
   to the specific proposed action, place and audience. Body cues can support a
   marked interpretation, not a diagnosis or permanent trait. Keep unnamed
   instrument players unknown and distinguish musical pattern identity from
   successive physical sound occurrences. Possessive ellipsis in a size
   comparison needs the omitted object, not its human possessor.

10. **Anaphora and occurrence identity.** An overt pronoun referring to an
    event or proposition remains a pronominal subject; it is not an overt
    clausal subject. Keep an abstract musical pattern, its successive sound
    occurrences, the arrangement's plural pauses, and one particular pause
    distinct when the text distinguishes them.

Read `batch1_examples_v2.json` alongside the pilot examples. These are actual
corrected records with their referenced registries, not hypothetical model
outputs. Story-local IDs must never be copied as identities into another story.
The full catalog remains available; no feature-density quota is introduced.
