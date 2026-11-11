# Storyformer candidate catalog

Three linked, versioned catalogs for proposing and learning symbolic features:

| File | Records | Contents |
|---|---:|---|
| [attributes.jsonl](attributes.jsonl) | 1,024 | Named, typed semantic and grammatical dimensions, their scope and missing-value meaning |
| [heads.jsonl](heads.jsonl) | 1,024 | Query/key selection, value projection, residual operation, dependencies and evaluation ideas |
| [grammars.jsonl](grammars.jsonl) | 1,024 | Executable finite grammar seeds or explicit implementation contracts, with positive and contrastive examples |

These are authored hypotheses informed by the existing code and research. They
are proposal material for the learned system, not learned parameters, an exhaustive
ontology, or a claim that a transformer contains these exact units. The requested
1,024-item allocation organizes the search space; training should merge, split,
rename, reject and replace entries. Similar mechanisms can serve different
semantic roles. Counting grammars does not establish transformer-equivalent cost.

## Coverage

Each row has a stable `A`, `H` or `G` ID. Four source modules contain eight families
of 32 entries each:

| IDs | Families |
|---|---|
| 0001–0256 | Identity/annotation, reference, time, quantity, evidence, lexical semantics, contextual retrieval, logic |
| 0257–0512 | Constituents, grammatical relations, valency, agreement, nominal constructions, verbal constructions, clause scope, questions/relatives/coordination |
| 0513–0768 | Space, motion, containment/access, possession/transfer, object state, material/affordance, event structure, physical causality |
| 0769–1024 | Knowledge/belief, goals, affect, social relations, communication, discourse, reasoning/memory, narrative perspective |

The types include strings, booleans, numbers, entity references, arrays and atomic
objects. A boolean is useful for an independent proposition or feature; a
categorical string is preferable to dozens of mutually exclusive boolean names.
An object retains a correlated value with its entity, scope and candidate status.
The catalog does not impose 64 active fields or allocate all 1,024 on each token.
Here 1,024 counts field definitions, not scalar coordinates: an object can contain
several bound values. Any activation budget should also measure payload size and
matching cost.

The [causal annotation contract](../PREFIX_ANNOTATION.md) separately registers
nine extension fields, including the v3 `plot` and `depiction` bundles. These
annotation definitions do not add executable heads or change this catalog's
1,024-entry allocation. Existing goal, belief, social and narrative names are
reused where their meaning and scope agree.

## What can run now

There are **238 native grammars** and **786 adapter contracts**. The latter state
their missing capabilities in `requires`; the loader refuses to install them as
native heads. Among the contracts, 64 preserve executable `seed_matcher` patterns
for reuse, but their full heads need correlated candidate routing and, for some,
resolved participant roles. Native means a bounded seed executes in the current
matcher; it does not imply complete language coverage or a safe automatic world
state update. The machine-readable [validation report](validation.json) is the
authority for current counts.

The native subset uses the existing `Token`, `Seq`, `Alt`, bounded repetition,
capture/reference and finite lookup operations. Recursive parses, fresh IDs,
scope accessibility, graph traversal, latest-state selection, arithmetic and
correlated hypothesis routing are contracts where the runtime lacks them.
Nothing calls an LLM during inference.

```python
from storyformers.catalog.api import CatalogIndex, prepare_context
from storyformers.transformer import Residual

catalog = CatalogIndex()
block = catalog.block(["H0105"], num_heads=16)  # quantity_lower_bound
context = prepare_context([
    {"token": "at"}, {"token": "least"},
    {"token": "three", "cardinal_value": 3},
])
stream, trace = block.forward([Residual(row) for row in context])
assert stream[-1].view()["quantity_lower_bound"] == 3

# Metadata can be passed as Storyformer(features=...). It adds no labels.
registry = catalog.feature_registry(["cardinal_value", "quantity_lower_bound"])
```

Only selected heads are loaded; unused layer slots are NOOP. There is no default
installation of all entries. The existing `GrammarHead` sums matching derivations;
a 64-neuron bank with top-one-or-NOOP routing remains future work. A native head
does not acquire that policy just because its catalog record proposes it.

The same native neuron representation can participate in a `GrammarProjection`,
but most catalog emissions describe context features rather than complete next
tokens. They are **not a fixed 1,024-word unembedding table**. A learned readout
still needs vocabulary-specific rules and projections producing complete next
latents, joint candidate masses and token marginals. The integration test builds
a small full-latent readout on top of a catalog head and checks its distribution.

## Record and residual conventions

- Attribute `key` is the canonical field name; aliases are metadata, not automatic
  runtime rewrites. Reuse an existing key only when meaning, scope and value type
  agree. Stable IDs make later naming revisions traceable.
- `producer_head_ids`, `suppressor_head_ids` and `consumer_head_ids` are computed
  from actual operations. An associated head may consume its associated attribute
  to suppress another field. There is no neuron-equals-attribute assumption.
- Missing or `null` means unknown. A false boolean needs evidence; lack of a
  detector activation does not supply it. For `operation="suppress"`, an expected
  patch identifies the exact value whose evidence is lowered, not an opposite
  assertion. Strength one can reduce an observed value's score without erasing it.
- World/mental hypotheses must retain their carrier, holder, event and scope as
  appropriate. Physical world seeds emit atomic candidate objects. Mental
  multi-field seeds require an adapter because independent field winners can
  assemble a holder/content/event combination that no source supported. Candidate
  status must qualify that hypothesis itself, not compete with the token's status.
- `entity` keeps the annotation's category/label meaning; `entity_id` uses `eN`.
  `event` is the annotation phrase; `event_id` is its anchor. Compact `pos`,
  `event_type` and `factuality` values preserve the current annotation convention.
  The annotation's string-valued `attributes` array is not silently changed to a
  typed wire format; the catalog registry is a separate layer.
- Native fixtures use word/punctuation records. `prepare_context` explicitly
  removes synthetic spaces while preserving original indices, positions and IDs.
  Missing positions are computed before filtering. Training and generation must
  choose this same convention or provide another explicit adapter.
- Every computation reads a prefix and writes only the current query. Existing
  positions are not retrospectively relabeled. This requires upstream causal
  annotations too; a mask cannot remove hindsight already stored in a prefix.

Each grammar provides `reads`, `writes`, `examples`, `learning` statistics and
ambiguity notes. A contrast can either abstain (`expect={}`) or produce a different
valid value. It must not automatically become a negative training label for the
whole semantic function. Contract fixtures illustrate input/output intentions;
their lightweight token records are not a fully annotated training corpus.

## Use in the batch learning loop

The intended use agrees with an interleaved forward/learning process:

1. Run all causal positions in a batch against a frozen model version. Collect
   activations, candidate alternatives, target disagreements and full-latent loss.
2. Update weights; merge support, false activations, scope conflicts and loss
   changes into rolling statistics across batches. Preserve small diverse example
   reservoirs, including counterexamples and previous failure cases.
3. Propose structural changes from those accumulated statistics. Give the LLM
   current-batch examples **plus** the relevant rolling summary, canonical
   attribute definitions and a few replay examples. A single batch alone is weak
   evidence for a new name or a changed meaning.
4. Parse and type-check the proposed grammar/name/binding changes, evaluate a
   staged model on held-out and replay cases, and promote an accepted version at
   a batch boundary. Re-run affected forwards when structure changes; stale
   activations are evidence about the old model, not the new one.

Weights can update every batch while structural proposals and LLM revisions run
at a slower or asynchronous cadence. The catalog supplies vocabulary and candidate
contracts to this process. The existing induction and neuron-review tools remain
separate; this catalog does **not** implement the combined trainer, head-weight
gradients, an activation budget, or automatic checkpoint promotion.

## Research and verification

The review found the relevant local predecessor under `grammarworlds`; there is
no separate `grammarformers` package. Its research inventory has 1,024 behavior
entries, while its authored symbolic catalog has 64 contracts: 15 table-executable
and 49 program-required. See the [local review](research/local.md) and the
[P001–P064 crosswalk](research/head_crosswalk.json). These are related designs,
not one-to-one copies.

The [GF/Codeco review](research/gf.md) motivates typed construction interfaces,
valency, scope and accessible references. The [SAE/circuit review](research/sae.md)
motivates sparse, contextual, testable feature hypotheses and highlights naming,
absorption and binding limitations. It does not validate these exact authored
features or settle the required attribute count. [sources.json](sources.json)
distinguishes local implementation evidence from research motivation.

Rebuild and check from the repository root:

```sh
.venv/bin/python -m storyformers.catalog.build
.venv/bin/python -m storyformers.catalog.build --check
.venv/bin/python -m unittest storyformers.test_catalog
```

Edit [sources/](sources/), not generated JSONL. The builder checks exact counts,
IDs, types, links, declared capabilities, canonical annotation values and native
duplicates; it executes native fixtures, separate adapter seed fixtures, prefix
causality checks and native suppression checks. See [AUDIT.md](AUDIT.md) for
semantic review findings and the limits of those checks.
