# Compact authoring and scene algebra

`compact_workshop.py` is an opt-in authoring path. Luna writes one executable
JSON world, the compiler builds and validates it, three previews run, then Luna
fills named prose slots. Finished worlds run offline. Existing Python workshop
commands and previous frozen runs remain available.

```bash
python -m unittest discover -s storyscenes -p 'test_*.py'
python storyscenes/compact_workshop.py --out storyscenes/runs/my_compact_trial \
  --campaign storyscenes/improvements/20260908 --count 3 --seed 20260907 \
  --api-key-file .API_KEY --evaluate
python storyscenes/verify.py --run storyscenes/runs/my_compact_trial
```

Luna/Flex authoring uses one medium-effort world request (5,500 output cap), up
to three low-effort world patches (2,500 each), one low-effort text request
(9,000), and up to three low-effort text patches (3,000 each). Caps include
reasoning. The existing $15 campaign ledger and $0.15 per-world dispatch guard
apply; use only one process per campaign ledger. `--evaluate` invokes the
unchanged, separately priced Terra/Flex set judge. No stronger-model authoring
fallback or semantic critic is used. STOP files, uncertain paid outcomes and
incomplete API responses stop new stages; they are not semantic repair requests.

## Algebra and physical carriers

`algebra.py` supplies immutable `Pattern` and `Kernel` definitions:

```python
from algebra import compose

wind_news = compose({"wind": {
    "op": "DiscoverAndShare", "args": ["ada", "dragon", "garden.wind"]
}})
wish_news = compose({"wish": {
    "op": "DiscoverAndShare", "args": ["dragon", "ada", "neighbor.want"]
}})
opportunities = wind_news + wish_news / 2
```

Addition combines candidate opportunities. It does not concatenate finished
stories or prescribe a route. Guards and accumulated world state determine which
opportunities occur and how their effects interact. Definition order is preserved
for deterministic seeded sampling, but it is not an execution order. Division
lowers search attention while preserving effects and legality. `+=` rebinds a
composed value rather than mutating its existing definition.

Local kernels bind roles, can contain other kernels, and get namespaced instance
IDs. Recursive expansion, unbound roles, duplicate IDs, unknown fields and
unembedded state fail closed. Each build creates fresh entity state. Knowledge
slots are declared automatically, but explicit starting knowledge and false
beliefs take precedence. Tell copies the speaker's belief, not omniscient truth.
Lend/Return track ownership and the recorded lender; Move updates object location.
Act supports custom guards and atomic set/inc/copy effects. Embedded meme
magnitudes can gate actions. Tests remove communication or lower the lender's
Care, making the composed goal unreachable; other tests demonstrate two legal
orders of independent discoveries.

This advances the memeplex north star by separating immutable definitions from
their physical carriers and changing state, and by letting role-bound patterns
compose and be attenuated. It remains an operational subset: concepts, characters
and whole narratives are not yet all represented by one universal type. The
compiler does not invent a physical carrier or a missing fact to make a draft
pass. Whether an authored carrier is semantically physical still needs review.

## Prose and repairs

`compact_prose.py` derives stable card IDs and factual conditions from executed
traces. Luna writes wording; the library builds conditional catalogs and Python
wrappers. Named text patches include the expected old text, so stale edits and
wrong card IDs fail instead of changing a different array entry. World repairs
replace bounded named components rather than entire scripts.

Endings are grouped by the world's declared outcome fields. The model sees only
the facts common to all traces in each group, preventing incidental knowledge or
leftover preparation from multiplying closing paragraphs. The default is one
wording per slot; causal and initial-state variation still produce different
stories. This avoids paying for multiple cosmetic phrasings of every card.

Every finite initial configuration is checked with four search seeds; another
100 sampled seeds enrich the prose inventory. This is not exhaustive search over
every reachable ordering. Unseen prose conditions fail closed. Free English can
still make unsupported claims: guard facts are evidence for card selection, not
a proof of each sentence. Semantic review remains necessary. More than 64 initial
configurations or 120 prose cases is rejected rather than silently truncated.

## Reproducibility and measurement

`port_example.py` converts the existing pond-concert world without changing its
semantics: 300 exact trace replays and 600 exact prose/QA replays passed. Its
definition went from 7,279 Python characters to 4,722 compact JSON characters.
This is a character measurement, not a claim about billed tokens. The definition
and replay evidence are in `examples/pond_concert_compact/`.

`compact_report.py` compares runs using the same briefs/seeds and set judge.
All returned output includes reasoning, failed drafts and repairs; authoring
and evaluation costs are separated. Completion rates stay visible alongside
scores for the common successfully judged worlds. Three pairs are a pilot, not
an acceptance estimate for 20,000 worlds.

The initial control attempt, `runs/compact_control_v1`, exhausted disk space while
saving a paid response. Its three completed plans are reused by
`runs/compact_control_v2`, without another planning call, and counted once in
that control's token totals. Three interrupted mechanics requests have unknown
paid outcomes and retain their reservations in the campaign ledger. Their
unknown usage is separate from measured successful-run tokens. See
`improvements/compact_v1/interrupted_control.json` for provenance.

Full contract: [AUTHORING_COMPACT.md](AUTHORING_COMPACT.md). Comparison artifacts:
`improvements/compact_v1/`. The prior ten-world frozen run passed 1,000 fresh
samples and 30 pinned replays; evidence is saved there without changing its
original artifacts.

The completed comparison, including failed drafts and bounded recovery, used
**20,773 output tokens versus 27,671** (24.93% fewer). Both pipelines completed
2/3 worlds; the quality mean on the same two worlds was **7.75 versus 6.75/9**.
See [the report](improvements/compact_v1/REPORT.md) for costs, the development
trial and interrupted requests. This is a small pilot, not a production gate.

`recover_compact.py` is an explicit authoring-only utility for a known returned
JSON draft truncated at its output cap. Luna supplies a bounded suffix, then
the normal mechanics checks and patch limits apply. It refuses unknown paid
outcomes and preserves the original prefix. In this trial it completed the
JSON in 575 tokens, but subsequent constraints still failed; the world remained
quarantined. The recovered draft and all follow-up patches count in the totals.
