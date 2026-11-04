# STORYBOOK mini: an expanded prose-generation experiment

Open [the research notebook](examples/research.html): select a story and a
configuration, read its actual generated text, and inspect the sentence plans
and reference decisions. [All outputs](examples/comparison.html),
[mechanical measurements](examples/report.md), and [pipeline traces](examples/traces.json)
are saved locally. Python 3.9+, standard library only; no runtime LLMs or network.

The original ten outputs are preserved in [baseline_v1/](baseline_v1/comparison.html).
The expansion remains inside `storybook_mini/`.

## What expanded

There are now four narrative streams and seven configurations. The original
lantern/kite sketches remain. Two longer stories, **Supper Before Six** and
**The Measure Left for the Steps**, exercise a borrowed lamp, three female
characters, ownership versus custody, a resource reserve, permission, a desire,
dialogue, and two different outcomes.

The longer streams contain 50 and 43 facts. Full realization produces 38 and 33
sentence units, approximately 380 and 350 words. Both leave the lamp usable in
its owner's hands; only one accomplishes the supper. They are two authored paths
through one small content family, not independent plot generators or evidence of
broad diversity. [Local reading notes and next gates](RESEARCH_NOTES.md).

| Layer | Current implementation |
|---|---|
| Content | Physical entities, numeric embedded emotions, ordered facts, causal/contrast links, action contracts, goals and utterances |
| Sentence planning | Functional clause structures with subject/object/target roles, tense, polarity, and embedded propositions |
| Lexical choice | Sense-specific verb alternatives; `replied` is available only for an adjacent, grounded reply |
| Discourse history | Two-sentence competitor window, scene resets, local binding, shortened descriptions, ownership, speaker/hearer deixis, active conversation |
| Revision | Shared-subject coordination, shared-verb object conjunction, descriptive relative clauses, causal subordination, contrast |
| Surface realization | Bounded English morphology, negation, agreement, quotation punctuation and reporting tags |
| Paragraph planning | Scene/topic changes, speaker changes, response actions, and a soft sentence budget |

References resolve against the final revised clauses. A relative clause cannot
attach to the wrong noun or use a pronoun for the noun it modifies. Negated
actions cannot perform success effects. Object conjunction is blocked under
negation to avoid changing its scope. Shared-verb contraction is limited to
simple, affirmative, target-free clauses. A desire or future utterance never
executes its embedded action.

Ownership-aware noun phrases use the **before-state of each event**. Lending a
lamp changes custody while preserving its owner; giving the invitation changes
ownership. Referring to the lamp as the borrower's property would be wrong.
Grammatical reflexives and speech's `I`/`you` remain in discourse ablations.
Logs distinguish those from optional narrative pronouns.

## Research lineage and interpretation

[Callaway & Lester 2001, Narrative Prose Generation](https://intellimedia.ncsu.edu/wp-content/uploads/sites/42/npg-ijcai01.pdf)
motivates separate linguistic components and fixed-content ablations. Their
experiment used two stories, five versions, twenty readers, and nine A–F factors.
This prototype implements that experimental pattern, not their Lisp code,
FUF/SURGE grammar, narrative plans, or human results.

[Callaway & Lester 2002, Pronominalization in Generated Discourse and Dialogue](https://aclanthology.org/P02-1012/)
motivates tracking distance, boundaries, competing referents, local binding and
speaker/hearer context. Our conservative two-sentence rule is a smaller design,
not a reproduction of their numerical algorithm or its evaluation.

[Callaway 2003, Integrating Discourse Markers into a Pipelined NLG Architecture](https://aclanthology.org/P03-1034/)
motivates choosing markers together with revision, because aggregation changes
where a connective belongs. Here an authored contrast can become an inline
`but` or a standalone `However`; a direct cause can become `Because` or
`As a result`. Neither is inferred from English or invented from adjacency.

## Run

From the repository root:

```sh
python3 -m storybook_mini show lamp_supper
python3 -m storybook_mini show lamp_return --version no_revision
python3 -m storybook_mini show lamp_return --trace
python3 -m storybook_mini demo
python3 -m unittest discover -s storybook_mini/tests -v
```

`demo` regenerates `examples/`; `--out /tmp/storybook-demo` preserves it.
`--suite mini`, `--suite extended`, and `--suite all` select the original pair,
the longer pair, or all four. Default: all.

## Add declarative content

Each story exports a standalone content file containing entities and facts:

```sh
python3 -m storybook_mini render storybook_mini/examples/lamp_return.content.json
python3 -m storybook_mini render storybook_mini/examples/lamp_return.content.json \
  --version no_discourse --trace
```

`story_io.py` loads these files as data, constructs typed entities/facts, and
rejects unknown fields. There is no Python evaluation or dynamic import from
content. The vocabulary and grammar must already support the predicates used.
`extended_content.py` is a compact example author that produces two streams from
one resource choice; the prose pipeline does not see that choice.

The core content types are:

```python
Proposition("bake", "nell", "loaf")  # content of a wish; not an executed bake
Fact("wish", "kitchen", "want", "nell", goal=...)
Fact("speech", "loan", "say", "nell", listener="iris",
     speech=Proposition("return", "nell", "lamp", "iris", tense="future"))
```

The latter realizes “I will return your lamp to you,” with the speaker, hearer
and owner supplied by structured content and state. Opaque authored dialogue is
also supported for richer wording. It remains identical across conditions apart
from reporting-tag placement and punctuation.

## Ablations

| Treatment | Discourse | Lexical choice | Revision |
|---|---|---|---|
| `full` | on | on | on |
| `no_revision` | on | on | off |
| `no_lexical` | on | off | on |
| `no_discourse` | off | on | on |
| `all_off` | off | off | off |

Marker generation and paragraph layout stay enabled across these five main
treatments. The expansion adds two separate controls:

- `no_markers` removes causal/contrast connectives and the aggregations needing
  them. This intentionally tests their interaction with revision.
- `no_organization` flattens paragraph layout only. Semantic scene/topic/dialogue
  barriers still protect revision and reference resolution.

Each configuration retains the same ordered fact IDs, entity roles, embedded
proposition roles, and content SHA-256. Ellipsis is explicit in the reference
trace. These checks detect structural omission, duplication and substitution;
they are not proof of complete semantic equivalence of the English. Causal
relations can remain implicit with markers removed. Authored cues and opaque
quotes are not independently decomposed into world assertions.

## Human ratings

```sh
python3 -m storybook_mini study --out storybook_mini/study \
  --suite extended --participants 20 --seed 2001
mkdir -p storybook_mini/responses
# Distribute only each reader's pNN.html. They download completed pNN.json.
# Put the completed files in responses/.
python3 -m storybook_mini evaluate --study storybook_mini/study \
  --responses storybook_mini/responses
```

The default study uses the two longer streams and the five main treatments:
ten readings per participant. `--suite mini` retains the original pair;
`--suite all` gives twenty readings. Exact position and first-order carryover
balance uses complete Williams-design cycles: participant counts should be a
multiple of the reading count. This ordering design is our addition.

Keep `private_manifest.json` with the organizer. It locks stimulus text hashes,
content hashes, selected stories/versions, and generation-source hashes. Each
HTML packet contains opaque item IDs and blank ratings. It works locally,
performs no upload, and loses unsaved answers when closed. Packet generation
refuses to overwrite an existing directory.

Evaluation rejects incomplete ratings, duplicate readers, missing/duplicate
readings, and changed text. A/B/C/D/F map to 4/3/2/1/0. Per-story and pooled
contrasts compare full versus ablated prose within participant; pooling averages
stories within each participant first. Reports are descriptive, with no ANOVA
or significance claim. Blank packets are not results. Synthetic ratings exist
only in tests of the analysis code.

## Limits and next gates

This remains a bounded English grammar and an authored content experiment.
Action contracts do not constitute general physics, and a narrator's declared
fact or causal link is not independently discovered. The reference policy is
conservative; the longer pair deliberately stresses same-gender ambiguity and
still repeats names. Revision uses a local, heuristic two-clause pass; its word
budget is an estimate, not an exact maximum. There is no temporal inference,
event migration, passive voice, multilingual grammar, plot search or literary
quality score. The longer examples still contain some event-log prose.

Physical carriers, guarded state changes, and emotion magnitudes follow the
repository's memeplex direction. The full `+`, `+=`, `/` algebra remains outside
this experiment. gen6, gen7 and the scene runtimes are untouched.

The next useful test is a blinded reading comparison, followed by a held-out
content family. A later scene integration should freeze narrated details and
dialogue as well as events; equal world traces alone do not fix story content.
