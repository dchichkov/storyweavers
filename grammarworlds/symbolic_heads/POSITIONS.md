# Symbolic rotary positions

`positions.py` is an opt-in experiment for annotated token memory. It allows
repeated semantic event names and distinguishes their occurrences by story and
position. Token units may be multiword; no whitespace splitting, POS tagging,
semantic annotation, or world-state execution is performed by this module.

```bash
.venv/bin/python -m grammarworlds.symbolic_heads.positions --demo
.venv/bin/python -m unittest grammarworlds.test_symbolic_positions -q
```

## Representation

A token carries a story namespace, global token-unit index, sentence index, and
sentence-local token-unit index. For each axis, its position advances four
symbolic clocks with ring lengths 7, 11, 13 and 17. The stored phases represent
implicit one-hot vectors rotated by cyclic permutations; allocating dense vectors
is unnecessary.

For a ring of length L:

```
phase(p) = p mod L
rotate(phase(p), shift) = phase(p + shift)
relative(query, key) = (phase(key) - phase(query)) mod L
```

This preserves the rotation identity `R(q)^T R(k) = R(k-q)`. Moving both tokens
by the same amount preserves their relative phases. `offset_match` computes the
average implicit one-hot dot product after a requested relative rotation.

This is a discrete analogue of the relative-position rotation algebra in
[RoFormer / RoPE](https://arxiv.org/abs/2104.09864), not an implementation of its
continuous sinusoidal rotations over learned query/key vector pairs. It does not
inherit neural RoPE's empirical results or provide learned semantic geometry.

The clocks repeat after 17,017 steps. Chinese-remainder reconstruction decodes
signed relative distances uniquely within ±8,508 units. Explicit coordinate
checks enforce that window, story scope and consistent sentence ordering; phases
alone cannot detect an out-of-window alias. Local offsets are compared only
inside the same sentence because the local counter resets at each sentence.

## Attention adapter

`positional_memory` turns annotated tokens into the existing `Source` records:

- Event name and patient form the semantic lookup key.
- Story plus token position forms the occurrence reference; event names need
  not be unique.
- An explicit causal mask excludes the query token and future tokens by default.
- An authored positional gate `1/(1 + absolute token distance)` prefers nearby
  eligible memories. Same-sentence and maximum-distance restrictions are optional.
- The existing table head selects semantic matches, projects values, and reweights
  only the words already supported by the grammar.

Recency decay and causality are explicit rules on top of rotary encoding; they
are not produced automatically by rotation. The adapter supplies the positional
gate through the existing confidence field, so distance also reduces the head's
overall influence. This is an implementation choice, not a calibrated certainty.

The demo includes three occurrences named `obtain repair tool`. At a repair
query, the earlier scissors acquisition is 12 units back and the tape acquisition
is 4 units back. The later glue acquisition is masked. Semantic attention assigns
27.78% to scissors and 72.22% to tape. A four-word prior is then reweighted:

| Next-word candidate | Before | After |
|---|---:|---:|
| patch | 25.00% | 27.80% |
| cut | 25.00% | 25.10% |
| ask | 25.00% | 23.55% |
| wait | 25.00% | 23.55% |

These are authored demonstration weights, not corpus-trained estimates. The
main story generators are unchanged; only the demo connects the new adapter to
the existing lookup-head runtime. The full trace is saved in
[`demo.json`](../runs/symbolic_rotary_20261106/demo.json).

## Percentages and exclusion

`percentages()` provides optional completed-text display coordinates on a
0–100 endpoint scale. A token halfway through a three-unit text moves to 25%
when that text grows to five units. Absolute unit positions remain stable under
appending; percentages and indices may change under edits/re-tokenization.
A story namespace should identify the relevant text version for stored references.

An exclusion rule can enforce that one *specific commitment* is applied once,
using story position and the engine's execution trace. Making semantic event
names unique would prevent ordinary repeated actions and weaken shared retrieval.
Multiple words describing one event can later share an anchor-token position;
this prototype does not yet aggregate such multi-token descriptions or decide
whether two annotations describe one physical event.

## Generated-story integration

The seven `storytelling` worlds can now export real positioned token annotations:

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario kite --seed 7 --token-annotations --json
```

Or call `generate(..., token_annotations=True)`. This is opt-in metadata;
word probabilities, sampled prose, commits and QA remain unchanged. See
[annotated kite sample](../runs/symbolic_rotary_20261106/kite_tokens.json) and
[seven-world summary](../runs/symbolic_rotary_20261106/generated_summary.json).

Each token carries `position`, `rotary`, `grammar_tags`, `entities`,
`entity_state`, and `event_context`. An occurrence is addressed by the story
namespace and `event_context.anchor_token`; its human-readable `name` comes
from the source kernel kind with underscores replaced by spaces. Names need
not be unique. These are source-kernel labels, not a newly normalized ontology.
The namespace includes scenario, seed and text hash; give separate copies their
own namespace if they must represent distinct memories.

The exporter traverses the selected grammar tree and retains only token-local
labels shared by all derivations matching the sampled words. It does not guess
POS from grammar ancestry: some noun constructions flatten phrase boundaries.
Entity references label noun-phrase tokens (including their determiners), not
necessarily just the head noun. Clause subjects and dialogue labels retain their
original grammar scope; they are not reassigned as each word's referent.

`event_context.scope = committed_scene` is deliberate. One scene can describe
several actions, including intentions in speech. The scene's frame roles are
coarse contextual roles, not asserted grammatical roles of every word. Its
anchor is the first sampled scene token, not a guessed action verb. Consumers
retrieving event occurrences should deduplicate by anchor, rather than count
every word as another event. No separate semantic event object is required.

Entity tokens carry `before` and `after` physical snapshots explicitly scoped to
`scene_boundary_observation`. These are observations after a scene is committed,
not executable changes at the word, and must not be exposed to online attention
before that commit. This ties annotations to physical carriers and persistent
state, consistent with the memeplex design. Operations without narrated words
remain trace references under `unnarrated_operations`; no synthetic token is
inserted. Further lexical action annotations will need explicit authored tags.

Positions use the generator's actual units, including punctuation. The exporter
preserves multiword terminals but does not merge existing word tokens. Sentence
coordinates split on terminal punctuation and retain closing quotes with the
preceding sentence. Percentages remain optional derived display coordinates.
The rotary coordinates are available for retrieval experiments; this integration
does not yet feed them back into the main story heads or demonstrate a quality gain.
