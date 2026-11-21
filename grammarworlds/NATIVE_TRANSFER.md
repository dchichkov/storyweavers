# Native mechanics transfer across twenty grammarworlds

[`memory_transfer.py`](memory_transfer.py) adds a permissive transfer path beside
the strict correspondence bank. It searches intact annotated stories for a named
event or a lexical cue, samples a source branch and role binding, imports missing
physical companions, and executes the source's existing guarded mechanics on the
receiving world. The receiving grammar generates fresh words and joint token
attributes. It does not copy an observed source after-state or paste source prose.

[Samples and measured coverage](runs/joined_transfer_20261107_v3/report.md).

## Requesting a transfer

```python
from grammarworlds.story_memory import load_documents
from grammarworlds.memory_transfer import run, receiving_world
from grammarworlds.world import Entity

memory = load_documents('grammarworlds/runs/seed_worlds_20261107_v4')
world = receiving_world()  # Nia, Omar, and a shared workshop; no authored plot
world.entities['trolley'] = Entity(
    'trolley', 'garden trolley', 'object', 'nia',
    properties={'portable'}, state={'rattling'})

row = run(memory, [
    {'event': 'refit_and_test', 'bindings': {'cart': 'trolley'}},
    {'event': 'controlled_trial'},
    {'scenario': 'music', 'extent': 'story'},
], world, seed=7)
print(row['story'])
```

`event` matches an annotated event name or kind. By default the adapter imports
its observed prerequisite prefix, stopping after that event. `extent: story`
continues to the source ending. `query: wheel repair` retrieves through annotated
action lemmas, event names and carrier nouns. Maximal whole-document cue coverage
prevents a generic repair verb from outweighing a more specific wheel context.
This is lexical retrieval, not an open-ended intent parser.

The source pool is the twenty seed worlds. The older rescue/kite/key prototypes
remain in the strict mapping/continuation path; they are not part of this new
native-transfer inventory.

A command-line example:

```sh
.venv/bin/python -m grammarworlds.memory_transfer \
  --request '{"event":"refit_and_test"}' \
  --request '{"event":"controlled_trial"}' --seed 7
```

`--out result.json` saves the complete replayable program, attachment distribution,
import ledger, target world, causal trace, word choices and token attributes.
No language model runs during generation.

## What comes with an event

The source's protagonist/helper roles prefer existing receiving characters.
Other physical carriers can reuse a unique object with the same description and
required properties, or be imported. The source target can also bind to a unique
receiving object with the same nonempty initial problem states, kind and required
properties: a rattling garden trolley can inherit the rattling cart mechanism.
This is a deliberately loose, logged analogy; kind alone is not enough. Both bindings can compete when feasible;
import count mildly penalizes the score, and reuse of an existing target gets
a fourfold preference. Explicit bindings take precedence and
cannot silently fall back to a different object. A bare receiver can import the
source people too.

Source-specific tools, locations, supporting characters, properties and initial
motives may accompany a transfer. This is the intentional leakage. Every imported
carrier, inherited character attribute and renamed-object analogy is recorded in
`options.transfer.units[*].leakage`. A supplied garden trolley can occupy the blue
cart role while retaining its receiving identity and live state.

Existing objects are never reset to the donor's initial state. An already-repaired
trolley cannot run the source's rattling-wheel prefix. Source guards run again on
a temporary view of the current receiving carriers at every event. A successful
commit mirrors that execution into the persistent receiving world; a failed
commit leaves it unchanged. Original input worlds/documents are not mutated.

`leak=False` rejects inherited character attributes and renamed-object analogies;
it still permits explicitly logged imports of missing source entities. It is not
a no-import mode.

## Distribution and annotations

Attachment candidates are deduplicated by source frame sequence and source
options, so duplicate source samples do not inflate their probability. Weights
combine lexical match and a small import penalty. These are manual heuristics.
The attachment distribution is sampled reproducibly by seed. Within a selected
bundle, the observed event order is fixed; grammar choices and annotated words
remain probabilistic. This is not yet autonomous event-by-event interleaving
between arbitrary worlds.

Surface references and semantic entity IDs are rebound before sampling. State
attributes describe the receiving prefix, not the source ending. Locational,
state, meme, flag and prior-event causal references refer to receiving carriers
and history. The result can be replayed and exported with `story_memory.annotate`
as another intact token document, with references back to the original source
text/token IDs retained in its transfer specification.

Source QA often contains hardcoded names and motives, so it is not copied into
receiving reading-comprehension claims. `world_qa` instead checks executed target
state/location changes and records its event/entity evidence. Silent physical
steps can support these questions: they are world-state QA, not a claim that all
answers are visible in the prose.

Live receiving snapshots with prior history are supported. Prior events remain
unchanged and new event IDs continue from them. The receiver must not have an
`ended` flag; clearing that flag is an explicit decision to resume a finished
world. Repeated attachments allocate fresh namespaces rather than overwriting
previous events or flags.

## Limits and next step

The adapter currently retains the entire observed prerequisite prefix and donor
cast, rather than finding a minimal causal subgraph. Typical imports include
several objects and places, so the amount of leakage is substantial. Mixed
samples read as successive mini-stories sharing people; they do not establish
an integrated plot or improved literary quality. Some donor surface constructions
still contain source-specific scenery and unnamed props.

The native guards preserve the donor's authored assumptions and simplifications.
A coarse object role is not a universal physics theorem; an explicit analogy can
be semantically loose even when it passes those guards. The strict operation bank
remains the better option when the receiver already has the necessary mechanics
and should import no extra context.

Next: identify smaller sufficient prerequisites, reuse already-executed prefixes,
and let a state-aware policy choose when to continue or leave a source mechanism.
Do not remove dependency flags merely to make a fragment appear independent.

## Verification

```sh
.venv/bin/python -m unittest grammarworlds.test_memory_transfer -q
.venv/bin/python -m grammarworlds.memory_transfer_experiment \
  --out /tmp/joined-transfer-audit
```

The audit covers every distinct observed path in the 400-document twenty-world
archive, verifies native replay and intact-token reconstruction, checks all causal
references, and removes a live actor at each event to verify rejection without
mutation. Additional samples exercise existing-object analogy, mixed mechanisms,
and lexical retrieval. These are mechanical measurements, not Luna ratings.
