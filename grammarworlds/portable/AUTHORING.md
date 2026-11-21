# Small authoring contract

Use `Language(world, tense)` from `grammarworlds.portable.language`. It produces
typed phrases that lower into the existing weighted grammar, never strings to
be spliced into arbitrary sentence slots.

```python
g = Language(world, tense)
return g.s("hero", g.v("hope", g.v("play", g.n("duet", det="a"))))
```

`plan(world, frame, tense)` returns a `Sentence`. World guards and effects live
in `candidates(world)` and `commit(world, frame, sentence)`, separately from
grammar. Never infer state from generated English.

| Function | Contract |
| --- | --- |
| `g.ref(entity_id, subject=False)` | Grounded entity NP; feature-aware reference alternatives |
| `g.n(word, *adjectives, det="the", number="singular")` | Lexical noun phrase; `a`, `the`, or `bare` |
| `g.cn(word, *adjectives)` | Common noun, without determiner |
| `g.v(verb, *complements)` | VP; checks declared lexical valency |
| `g.s(subject, vp, negative=False, tense=None)` | Sentence; subject is an entity ID or NP |
| `g.be(adjective_or_location)` | Copular VP |
| `g.can(vp)` | Modal VP with bare infinitive |
| `g.pp(preposition, np)` | Prepositional modifier; object case |
| `g.adv(vp, *modifiers)` | Add registered manner words or prepositional modifiers |
| `g.join(sentence, sentence, "and"/"but"/"because")` | Clause composition |
| `g.both(np, np)` | Coordinated NP with plural agreement |
| `g.possess(owner_np, common_noun)` | Possessive determiner; agreement follows the possessed noun |
| `g.either(*sentences, weights=...)` | Weighted semantic-equivalent paraphrases |
| `g.reporting(actor, verb, lambda who: sentence)` | Introduces speaker, supplies locally bound NP for reported content |
| `g.sequence(actor, first_vp, second_vp)` | Same actor, second clause uses a locally bound pronoun |

`g.v` supports V (no object), V2 (NP), VV (VP), VS (Sentence), V3 (NP, NP), and
V2V (NP, VP with `to`). The verb's lexicon entry must explicitly license the
requested signature. `hope` permits VP/Sentence, so `hope(duet_np)` fails instead
of generating “hoped a duet.” Unknown vocabulary fails explicitly.

Add domain vocabulary in a separate `lexicon/*.json` module. Regular nouns need
`{}`; irregular nouns need `{"plural": "leaves"}`; mass nouns need
`{"mass": true}`. Verbs need `{"valencies": ["V2"]}` and optional principal
parts, e.g. `{"forms": ["find", "found", "found"], "valencies": ["V2"]}`.
Duplicate entries are rejected. Do not hide whole clauses in lexical strings.

Retrieve the relevant rule signatures/examples with `portable.catalog`; don't
paste the entire library into an author prompt. If a type is missing, inspect
`features.py`. If a construction is missing, supply its intended type and a few
positive/negative examples before changing one focused rule module. Tests should
exercise agreement, complements, references, world interventions, and prefix
probabilities rather than only checking that a string was produced.

Physically meaningful descriptions must be warranted by world state or by the
event being committed. Vocabulary availability alone never makes an event true.
