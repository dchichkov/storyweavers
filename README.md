# Storyweavers

**Narrative Algebra: Extracting and Composing Story Kernels**

Storyweavers explores whether stories can be decomposed into compact, algebraic "kernels" — composable narrative patterns that can generate surface text. The project extracts these kernels from the TinyStories dataset (~2M children's stories) and investigates whether a small library of ~1-5K kernels can reconstruct coherent story datasets.

## ⭐ North Star: The Memeplex Model — see [`story.py`](story.py)

The canonical design lives in **[`story.py`](story.py)** (the "Storyweavers Design Summary"). Everything in this repo should be measured against it. The core idea:

- **Everything is a memeplex, and a memeplex *is* a story.** A concept (`Love`, `Fear`, `Envy`), a verb/action, a character, and a whole narrative are the *same kind of object* — composable via the algebra (`+` composition / co-occurrence, `+=` accumulation, `/` attention dilution). They differ only in scale, not in kind.
- **Memeplexes are platonic forms; they only matter once *embedded* in a physical carrier.** A memeplex must be embedded in something physical — captured in a *book*, alive in a *person*, or alive across *many people* — to affect the narrative. *"Stories need to have associated physical objects, or story weight is zero"* (`story.py`). An un-embedded concept has **zero weight** and must not change the story.
- **Track the physical level and how much of each concept is present.** Each physical carrier holds *magnitudes* of the concepts embedded in it (`Entity.memes` in `gen6.py` is the seed of this). The story is the evolving state of these embedded magnitudes.
- **The world model should only allow *compatible* moves.** Generation must be consistent with the memeplexes already present and how they interact. Example: declare a lion `Scar(Character, lion)` and max out its `Envy` memeplex — the world model should then only permit Envy-compatible moves, and the generated narrative must stay consistent with a maxed-Envy character (no out-of-character kindness unless something first changes the embedded state).

> **Worked example.** `Listen(animal, other, Content)` embeds a fraction of `Content` into `animal` (`animal.Story += Content / 10`) and weakly merges group identity (`animal.We += other.We / 100`). The `/` keeps weak influences weak; only embedded, sufficiently-weighted memeplexes surface in the narrative. See the `Listen` / `Purr` / `Tell` / `Care` sketches in `story.py`.
>
> **Runnable proof-of-concept on gen6:** [`memeplex_demo.py`](memeplex_demo.py) implements `Listen` / `Purr` as gen6 kernels that move `Story`/`Love`/`We` magnitudes between carriers (attention-diluted as in `story.py`). Crucially the **accumulated weights drive the prose**: more purrs raise the listener's `Love`, which escalates the narration and changes a state-chosen ending (`Closeness` reads the pair's total `Love` + shared `Story` links). It also reframes `Tell → Listen` with an AST rewrite. Run `python memeplex_demo.py`.

**Where the implementation stands vs. the north star** (honest):

| Principle | Status in `gen6.py` |
|---|---|
| Per-carrier concept magnitudes (`Entity.memes`) | ✅ partial — exists and accumulates |
| Concept embedding via `+=` (`@REGISTRY.addition`) | ✅ partial — some concepts attach to carriers |
| **Embed-or-zero-weight** (drop un-embedded concepts) | ✅ partial — `+` chains/fallback now embed bare concepts into the current carrier or drop them; remaining leaks are mostly missing-kernel/template cases |
| **Memeplex == story** (one uniform representation) | ❌ kernels, concepts, characters are still three things |
| **Compatibility / only-allow-compatible-moves** | ❌ not built — concrete layered plan in [Composing Kernels](#composing-kernels-typed-slots-world-gated-rewrites-optional-asp) (typed signatures + optional ASP overlay); backlog item: `TODO.md` → `constraint_pass` |
| Physical / plausibility model | ❌ minimal (object owner/status only) |

See [`TODO.md`](TODO.md) for the north-star backlog that closes these gaps, and [`QUALITY.md`](QUALITY.md) for how quality/fidelity is measured against it.

## TODO
**[TODO.md](TODO.md)** For gaps and next steps. The top of TODO.md has a status update on the unified `gen6.py` engine.

### `gen6.py` — Unified Engine (typed world + rewrites + coherency) ⭐ New

`gen6.py` assembles the experiments below into a single, self-contained engine:

```
source --[declarative rewrites]--> --[coherence tagging]--> --[typed-world execution]--> --[narrate]--> story
```

- **Typed kernels + dispatch** (from `wrld6.py`): kernels declare typed params (`Character`, `Physical`, `Actor`); a backtracking binder selects the matching variant; uppercase "meme" slots carry concept-specific `+=` behaviour; effects and narration are traced automatically.
- **AST → AST rewrites** (from `rewr6.py`): declarative rules rewrite kernel source **before** execution (normalization, enrichment, prerequisites). Patterns use kernel calls + `+` composition with `__`-prefixed metavariables (e.g. `__C`, `__S`).
- **Coherency layer**: a single AST pass (`tag_coherence`) tracks narration order and tags repeated-subject kernels so the renderer uses **pronouns** (and `_transition` connectors) — instead of every kernel deciding this on its own.

```bash
python gen6.py
```

```python
from gen6 import generate
print(generate("""
Lily(Character, girl, Curious)
Fear(Lily, dog) + Brave(Lily)
Joy(Lily)
"""))
# "Once upon a time, there was a little curious girl named Lily.
#  Lily became afraid of the dog. Even though she was afraid, she was brave.
#  She felt full of joy."
```

**Kernel packs & tooling.** Additional kernels live in `gen6kXX.py` packs and are auto-loaded by `gen6registry.py`. The analysis tools run on gen6:

```bash
python coverage.py --brief --execute 3000         # measure dataset coverage
python sample.py -k Quest -n 3 --seed 42 --show-source
python check_duplicates.py                         # find duplicate typed variants
python gen6registry.py                             # list loaded packs + kernel/variant counts
```

gen6 executes ~all parseable stories end-to-end (the typed dispatch degrades unknown kernels to a readable fallback instead of raising). The remaining work is growing the kernel library; see [TODO.md](TODO.md) for the roadmap and current metrics. `wrld6.py` / `rewr6.py` are the reference demos `gen6.py` was built from. The previous engine (`gen5.py` and its `gen5kXX` / `char5kXX` packs) now lives in [`legacy/`](legacy/) for reference only — it is no longer wired into the tooling.

### `gen7.py` — MUD-Like StoryWorld Prototype

`gen7.py` is a clean-break prototype that treats kernels as world-level commands
before rendering English. It does **not** import gen6 kernel packs. The flow is:

```
kernel AST -> semantic Frame list -> persistent StoryWorld -> discourse render
```

The first vertical slice focuses on role preservation, object status/ownership,
simple meme magnitudes, and ordered event history rather than broad coverage.
The core now loads small gen7 semantic packs (`gen7packs.actions`,
`gen7packs.renderers`) so frame-name lowering and high-frequency renderers can
move out of the monolith incrementally while the pinned stories stay stable.

```bash
python gen7.py --story-id data00:36222
python gen7.py --story-id data00:36222 --qa
python gen7_story_tests.py --run
python gen7_story_tests.py --run-qa --qa-limit 12
python gen7_story_tests.py --sample 10 --seed 777 --scan 20000 --show-qa --qa-limit 8 --show-kernel
```

The gen7 snapshot runner pins 294 representative stories, including known problem
cases from both `data00` and `data01`, so quality/world-model changes can improve
the semantic slice without silently regressing it. Use `--sample N` during quality
passes to inspect deterministic unpinned candidates; promote 5-10 reviewed stories
into `STORY_IDS` plus snapshots each iteration so the suite grows with the failure
surface. `gen7.generate_qa(...)` and `--show-qa` generate deterministic templated
questions/answers from the simulated `StoryWorld` trace, so QA quality can be
reviewed beside the generated text.

QA should now be treated as part of gen7 quality, not an afterthought. During
sampling passes, inspect generated questions and answers alongside the story,
kernel, and original text; improve repeated QA failures the same way narrative
failures are improved. The target answer is a full natural-language response,
usually two or more sentences when the world trace supports it, rather than a
bare noun phrase. Question generation should stay tied to `StoryWorld.history`,
entity state, relations, meme magnitudes, and frame metadata instead of becoming
post-processing over rendered prose.

`--run-qa` is the smoke gate today. It checks nonempty QA, question syntax,
full-response answers, multi-sentence answers, minimum question-kind diversity,
duplicate-question rate, and generic second-sentence rate. Run it after every QA
change, and keep extending it from sampled defects: answerability from
`StoryWorld`, grounded entity/frame ids, causal answers, role/object-state
questions, and shallow-question detection. A good sampled batch should show a
mix of who/what/where/how/why/what-next plus role, object-state, instrument,
lesson, and causal questions. Multi-turn QA is a desired next milestone:
follow-up questions should carry the referenced entity/event forward through the
same simulated world state, not through a free-form chat over rendered prose.

### AST → AST Transforms (Reference Demos)

`rewr6.py` (which composes with `wrld6.py`) is the rewrite prototype `gen6.py` was built from:

- **Purpose**: apply declarative “story algebra” rewrite rules to the kernel source **before** execution (pronouns, transitions, prerequisites, normalization).
- **Rule syntax**: write patterns and outputs using kernel calls and `+` composition; use `__`-prefixed names (e.g. `__C`, `__OBJ`) as metavariables inside rewrite patterns.

Try them:

```bash
python wrld6.py
python rewr6.py
```

`ast_rewrite_transform_demo.py` shows the next step: a candidate AST transform
that only applies after both structural and world-model checks pass. The demo
tries to rewrite `Friendship(__A, __B)` into `Lovers(__A, __B)`, but skips the
rewrite when the second endpoint is not a declared character, or when executing
the story up to the old ending leaves too little embedded `Love` in either
carrier. When mutual hugs have already embedded enough `Love`, the generated
ending changes from "became good friends" to "let their friendship grow into
love."

```bash
python ast_rewrite_transform_demo.py
```

### Composing Kernels: Typed Slots, World-Gated Rewrites, Optional ASP

How do you splice one kernel into another — insert a `Detective(...)` into the
`event=` slot of a `Cautionary(...)`, replace a `Friendship` ending with
`Lovers`, wrap a story as a sub-kernel — *without* writing a one-off Python gate
per pair? Most of the pieces are already in the repo; they need to be layered.

**1. Phase kwargs are already slots.** Real kernels in the dataset use keyword
arguments as named insertion points:

```python
Cautionary(ball,
    event=Accident(ball, process=Roll(hill) + Step(worker)),
    setting=factory(loud + machine),
    consequence=Death(ball))
```

`state=` / `event=` / `consequence=` / `lesson=` are typed holes the renderer
already reads (`gen6k01.py`). "Insert Detective into Cautionary" can be as
simple as putting `Detective(...)` in `event=` — no engine change.

**2. `Rewrite` is the add/replace/remove primitive.** `gen6.py` ships
pattern→template rewrites with `__VAR` metavars (`DEFAULT_RULES`,
`match_pattern`, `substitute`, `rewrite_tree`). Compose operations are
one-liners:

```python
Rewrite(
    pattern_src="Cautionary(__S, event=__E, **__R)",
    output_src ="Cautionary(__S, event=__E + Detective(Sherlock, "
                "case=Aftermath(__S, __E)), **__R)",
)
```

Insert / replace / remove / wrap are the same machinery; only the templates
differ.

**3. World-gated rewrites are the safety layer.** Pure pattern matching
produces nonsense (Lovers grafted onto strangers who never met).
[`ast_rewrite_transform_demo.py`](ast_rewrite_transform_demo.py) shows the
right pattern: probe-execute the host with the candidate subtree replaced by a
no-op, read the resulting `World`, and only commit the rewrite when accumulated
state allows it.

**4. The systematic shape — type system first, ASP on top.** Per-pair Python
gates do not scale. The correct factoring is a *typed signature* per kernel:

```python
@dataclass(frozen=True)
class KernelSignature:
    name: str                       # "Detective"
    kind: str                       # this kernel's tag when used as a guest, e.g. "Mystery"
    slots: tuple[SlotType, ...]     # each slot: name + set of accepted kinds
    requires: tuple[Effect, ...]    # what must hold in the host: Carrier, Unresolved, Magnitude(...)
    produces: tuple[Effect, ...]    # what this kernel adds: Embedded(meme, role), Absorbs(...)
```

Three checks fall out of the signatures, each with the right tool:

| check | tool | when it runs | example |
|---|---|---|---|
| **kind** (`guest.kind ∈ slot.accepts`) | dict/set lookup | every sample | "Detective is a Mystery, fits `event=`" |
| **requires** (effects in probe world) | small Python predicate over `World` | per-sample, after kind passes | "`embedded(love, A)` holds for both endpoints" |
| **global queries** (compat matrix, enumeration, UNSAT diagnostics) | ASP / clingo | offline / batch | "which hosts can take Detective in *any* slot?" |

The type system is the daily check (microseconds, replaces the demo's
hand-rolled `allow_lovers` with one uniform predicate). ASP is a power tool
that *consumes the same signatures*, serialised as facts — the `asp.py` +
inline `ASP_RULES` idiom from [`storyworlds/worlds/puddles.py`](storyworlds/worlds/puddles.py)
and [`storyworlds/worlds/pirates.py`](storyworlds/worlds/pirates.py) already
proves the clingo pattern at the storyworld level (a Python gate plus an
inline declarative twin kept in lockstep by `--verify`); lifting that idiom
from "rules per storyworld" to "rules per kernel" is the next step.

**5. ASP rules: per kernel; standalone rulesets per world.** The declarative
twin pattern is already proven at the storyworld level. From
[`storyworlds/worlds/puddles.py`](storyworlds/worlds/puddles.py):

```prolog
% A prize is at risk when the activity splashes the region it is worn on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a compatible fix only when it both neutralises the mess kind AND
% covers the at-risk region (rain boots guard wet but cover only feet).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P)     :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
```

That works because the world is *closed*: every `splashes/2`, `worn_on/2`,
`guards/2`, `covers/2` fact comes from that one world's own registries (emitted
by `asp_facts()`, kept in lockstep with the Python gate by `--verify`).
[`storyworlds/worlds/pirates.py`](storyworlds/worlds/pirates.py) extends the
same idiom with an *outcome model* (`averted | contained | burned`) — the ASP
twin derives the branch from the scenario's facts, and `asp_verify()` asserts
parity across curated and randomized cases.

The right factoring going forward is **two layers**, not one:

- **Per-kernel rules** live alongside each `@REGISTRY.kernel(...)` Python
  function. They are *open* — they don't know what they'll compose with — so
  they quantify over kinds (`unresolved(case)`, `has_carrier(observer)`) rather
  than over specific facts. The reusable unit:

  ```prolog
  % gen6kXX_detective.lp -- ships next to @REGISTRY.kernel("Detective")
  kernel(detective).
  kind_of(detective, mystery).

  slot(detective, case).
  slot(detective, clue).
  slot(detective, reveal).
  slot_accepts(detective, case,   loss).
  slot_accepts(detective, case,   theft).
  slot_accepts(detective, case,   mystery).
  slot_accepts(detective, clue,   evidence).
  slot_accepts(detective, reveal, confession).

  pre(detective, has_carrier(observer)).
  pre(detective, unresolved(case)).

  produces(detective, embedded(justice, observer)).
  produces(detective, embedded(wisdom,  victim)).
  absorbs(detective,  unresolved(case)).
  ```

  A single shared `compose.lp` derives every legal `(host, slot, guest)` from
  these per-kernel facts — no per-pair Python gate, no per-pair ASP rule
  either. Adding a kernel = adding ~20 lines of facts; the composition layer
  re-derives every legal insertion involving it.

- **Per-world standalone rulesets** (the inline `ASP_RULES` from each
  storyworld) stay *closed*: they ground out specific entities, registries,
  and a single outcome model. They consume the shared kernel layer above but
  add domain-specific predicates (`splashes/2`, `worn_on/2`, `spread/2`,
  `sense/2`) that only make sense inside that story. `--verify` keeps each
  world's Python gate and its ASP twin in lockstep, exactly as `puddles.py`
  and `pirates.py` already do.

The two layers compose: a story is legal iff its kernel composition checks
under the shared per-kernel rules **and** every per-world fact remains
satisfiable. Per-kernel rules are *narrative type discipline* (open, reusable);
per-world rulesets are *domain physics* (closed, instance-level).

**6. Bootstrap per-kernel rules from an encyclopedia / Wikidata.** Authoring
the `slot_accepts/3` and `kind_of/2` facts by hand for every kernel is the
labour-intensive part of this scheme. Most of it is *general-purpose common
sense* — "a Theft is a kind of Crime, a Crime is a kind of Event, a Footprint
can be a Clue, a Detective investigates a Crime" — and that knowledge already
exists, machine-readable, in external sources. Three complementary sources at
three granularities:

- **Wikidata (taxonomic).** SPARQL `wdt:P279*` hypernym chains give the
  `kind_of/2` lattice directly: `Theft → Crime → Event`,
  `Detective → Investigator → Profession`,
  `Forest → Wilderness → Geographical_Feature`. A one-shot extract per
  kernel-relevant concept produces ~50 lines of facts and gives every kernel
  a shared cultural ontology for free.
- **ConceptNet (functional).** `/r/UsedFor`, `/r/CapableOf`, `/r/HasA`,
  `/r/CausedBy` edges populate `slot_accepts/3`: what can *play the role* of
  a clue, a reveal, a setting, an instrument. Wikidata is taxonomic;
  ConceptNet is functional; both are useful and they don't overlap much.
- **TinyStories itself (empirical).** Crawling `TinyStories_kernels/*.jsonl`
  for every `Host(..., slot=Guest(...), ...)` shape emits
  `observed_slot/3(host, slot, guest)` facts. Intersect those with the
  Wikidata/ConceptNet lattice to keep only senses *actually used* in real
  stories, and frequency-threshold against typos. This grounds the type
  system in real dataset usage rather than in what one author imagined.

**Worked example — ConceptNet on `giraffe`.** A condensed slice of the
ConceptNet entry, picking the relations relevant to the type system and
dropping synonyms / cross-lingual entries:

```
giraffe IsA            ruminant, mammal, animal, herd animal, giraffidae
giraffe AtLocation     a zoo, a drawer
giraffe HasA           long neck, a nose
giraffe CapableOf      drink water
giraffe DefinedAs      tallest land animal, biggest ruminant on earth
giraffe HasProperty    male, female
giraffe Symbol         🦒
```

Each row maps mechanically to per-kernel ASP facts:

```prolog
% Taxonomic (IsA -> kind_of; transitive closure feeds slot_accepts).
kind_of(giraffe, ruminant).      kind_of(ruminant, mammal).
kind_of(mammal,  animal).        kind_of(giraffidae, mammal).

% Functional (AtLocation, HasA, CapableOf -> role facts).
at_location(giraffe, zoo).       at_location(giraffe, drawer).
has_part(giraffe, long_neck).    capable_of(giraffe, drink_water).
defined_as(giraffe, tallest_land_animal).

% Renderer hook (Symbol) -- not used by the gate, used by prose.
symbol(giraffe, "🦒").
```

These facts immediately make a `Visit(zoo, hero, giraffe)` shape derivable:
the `things_seen` slot of `Visit` can accept anything with
`at_location(X, zoo)` and `kind_of*(X, animal)`, so a single ConceptNet pass
populates dozens of legal guests at once with no per-pair authoring. The same
`kind_of` chain also makes `giraffe` a valid `mammal` / `animal` wherever an
upstream slot already accepts those kinds — Wikidata-style taxonomic reuse
falls out for free.

The `at_location(giraffe, drawer)` edge also shows *why* the curation step
matters: ConceptNet conflates senses — a real giraffe lives in a zoo, a *toy*
giraffe lives in a drawer. A small split into `giraffe_animal` and
`giraffe_toy` keeps both useful and neither leaking into the wrong slot. The
intersection with `observed_slot/3` from the TinyStories crawl is the cheap
filter: only senses actually used in real stories survive into the per-kernel
rules.

**Counterexample — `ostrich`.** ConceptNet coverage is uneven: popular,
iconic concepts get rich entries; close neighbours of the same kind often do
not. The `ostrich` entry returns the taxonomic chain (`IsA: bird, ratite,
flightless bird, animal`) and exactly *one* functional edge
(`CapableOf: lay an egg`) — no `HasA`, no `AtLocation`, no `DefinedAs`, no
`Symbol`. An ostrich does have a long neck, long legs, and lives on the
savannah; none of that is in ConceptNet:

```prolog
% From ConceptNet, complete:
kind_of(ostrich, bird).         kind_of(bird, animal).
kind_of(ostrich, ratite).       kind_of(ratite, flightless_bird).
capable_of(ostrich, lay_egg).
% Missing vs. giraffe: at_location, has_part, defined_as, symbol.
```

The one functional edge that *is* present — `CapableOf: lay an egg` — sits at
the wrong level of the hierarchy: egg-laying is a property of every `bird`,
not something specific to ostriches. A disciplined ontology would assert
`capable_of(bird, lay_egg)` once and let subtypes inherit it through
`kind_of/2`; ConceptNet's crowdsourced edges land wherever a contributor put
them, with no inheritance push-up. The bootstrap pass therefore needs a
**lift** step alongside the prune step: when a property holds for several
siblings under a common parent, hoist it to the parent and drop the leaves.
Wikidata's `wdt:P279` lattice plus `wdt:P31` instance facts is much better
factored on this axis, which is why the layered approach matters — ConceptNet
fills functional gaps, Wikidata enforces taxonomic discipline.

The same entry also exposes an idiomatic WordNet sense — `IsA: person` (from
"ostrich politics" / a person who denies facts). Imported uncritically,
`kind_of(ostrich, person)` would let an ostrich fill any slot that accepts
characters. Curation has to *prune* idiomatic senses, not only *merge*
synonymous ones.

So treat ConceptNet as one source among several: Wikidata for stable
taxonomy, ConceptNet for crowdsourced functional edges *where they exist*,
the TinyStories crawl for actually-used senses, and a small manual top-up
per kernel pack for the holes both corpora share (a tracked
`missing_facts.lp` per pack is enough — gaps stay legible). The bootstrap
closes the long tail; it does not eliminate authoring.

This fits the project's "LLMs at synthesis time, never at runtime" rule:
extraction + curation runs once, offline, against external corpora; the
resulting `.lp` snippets ship with each kernel pack and the runtime engine
sees only static facts. A free coverage signal also falls out — any dataset
use of a kernel that is *not* derivable under the imported lattice is a
checklist entry for what `slot_accepts` / `kind_of` facts are still missing.

A kernel author then writes ~5 lines of bespoke `pre` / `produces` effects per
kernel, and the slot/kind ontology is *inherited* from the shared commons.
The same lattice is reusable across the whole kernel library — adding
`Mystery` as a kind doesn't just help `Detective`; it automatically makes
every other host with a `slot_accepts(_, _, mystery)` legal to compose with.

**Where this lands against the north star.** The
*Compatibility / only-allow-compatible-moves* row in the status table above is
the gap this design closes:

- *Embed-or-zero-weight* becomes a static rule: an unsatisfied `Embedded(M, carrier)`
  precondition blocks any kernel that references it. An un-embedded meme can
  never satisfy a later kernel's `requires`.
- *Only compatible moves* becomes typing: `kind ∉ slot.accepts` → static
  reject; `requires` unmet in the probe world → dynamic reject. The maxed-`Envy`
  `Scar(Character, lion)` cannot fill a slot whose accepted kinds include only
  kind-acts.

**Order of work** (smallest first, in keeping with YAGNI):

1. `KernelSignature` dataclass attached to existing kernels via an optional
   `signature=` argument on `@REGISTRY.kernel`. Unsignatured kernels keep
   working; signatures opt-in pack-by-pack.
2. `can_fill(host, slot, guest)` + `requires_met(world, guest)` as two short
   Python predicates. Together they replace every hand-rolled `allow_*` gate
   from `ast_rewrite_transform_demo.py` with one uniform check.
3. `to_asp(sig)` + a shared `compose.lp` for the global queries you actually
   want (compatibility matrices, optimisation, UNSAT diagnostics). ASP becomes
   a serialised view of the same signatures, not a parallel rulebase.

Pilot the whole stack on one kernel family (e.g. Cautionary × Detective), in
the spirit of `storyworlds/worlds/`, before touching `gen6` core.

## Core Concept: Story Kernels

A **story kernel** is a symbolic, algebraic representation of a narrative's structure. It captures characters, their traits, narrative arcs, and emotional transformations in a composable format.

### Example

**Original Story:**
> Once upon a time, there was a big whale. The whale loved to swim in the deep blue sea. The whale was very delicate and kind to all the little fish. One day, the whale wanted to test how fast he could swim...

**Extracted Kernel:**
```python
Whale(Character, Imaginary, Delicate + Kind)
Test(Speed) + Community(Support, cheered) + Happy
Identity(Whale,
         new=Shark,
         reaction=Acceptance + Community(Support, Liked))
```

### Kernel Syntax

| Syntax | Meaning |
|--------|---------|
| `Name(...)` | Story kernel (uppercase = composable pattern) |
| `object` | Physical/concrete object (lowercase = terminal node) |
| `+` | Composition, co-occurrence |
| `/` | Attention dilution (e.g., `Fear / 10`) |
| `\n` | Sequence, temporal progression |
| `[a, b, c]` | Lists |

## Project Pipeline

```
TinyStories Dataset (2M stories)
         │
         ▼
    ┌─────────────┐
    │  kernel.py  │  ← LLM-based kernel extraction
    └─────────────┘
         │
         ▼
   .kernels.jsonl files
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌───────────┐
│sample.py│ │ AGENTS.md │  ← Analysis & Implementation
└─────────┘ └───────────┘
                │
                ▼
    Story Generation Engine and Kernels implementation
         │
         ▼
    ┌──────────┐
    │  gen6.py │  ← Classical NLG generation engine (typed world + rewrites)
    └──────────┘
         │
         ▼
   Generated stories
```

## Key Components

### `kernel.py` — Kernel Extraction
Uses LLMs (via OpenAI-compatible API) to extract story kernels from raw text. Processes the TinyStories dataset with async concurrency.

### `gen6.py` — Classical Generation Engine ⭐

The generation engine converts kernels to stories **without LLMs at runtime**. Uses:
- Python AST parsing (kernels are valid Python)
- Declarative AST → AST rewrites (normalize / enrich before execution)
- A coherence pass that tags repeated subjects for pronoun use
- Typed-world execution with a backtracking variant binder and traced narration

**Key design:** Kernels ARE valid Python code. They're parsed with `ast.parse()`, rewritten, then executed against a registry of typed kernel variants.

## Generation Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KERNEL STRING                                │
│  "Lily(Character, girl, Curious)                                    │
│   Journey(Lily, catalyst=Discovery(rainbow), transformation=Happy)" │
└─────────────────────────────────────────────────────────────────────┘
                                 │  ast.parse()
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Declarative rewrites (DEFAULT_RULES)               │
│   pattern → output over kernel calls + `+` composition; metavars     │
│   (`__C`, `__OBJ`) normalize / enrich the AST before execution       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Coherence pass (tag_coherence)                     │
│   tags repeated-subject kernels so the renderer uses pronouns        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Executor (typed world)                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ eval(node)                                                   │   │
│  │   ├── ast.Call → backtracking binder picks a typed Variant  │   │
│  │   ├── ast.BinOp(+) → _combine() traces / concepts           │   │
│  │   ├── ast.BinOp(/) → attention dilution                     │   │
│  │   └── ast.Name → resolve Entity, concept, or bare kernel    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
          ┌─────────────┐ ┌───────────┐ ┌─────────────┐
          │  Registry   │ │   World   │ │  NLGUtils    │
          │ name→[typed │ │ entities  │ │ past_tense   │
          │  Variants]  │ │ memes     │ │ article      │
          │ @kernel()   │ │ actor /   │ │ join_list    │
          │ + additions │ │ traces    │ │ meta_story   │
          └─────────────┘ └───────────┘ └─────────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            Trace                                     │
│  { kernel: "Discovery", text: "Lily discovered a rainbow.",         │
│    effects: [...] }   ← appended to world.traces for top-level stmts │
└─────────────────────────────────────────────────────────────────────┘
                                 │  narrate(traces)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENERATED STORY                               │
│  "Once upon a time, there was a little curious girl named Lily.     │
│   Lily discovered a rainbow. She felt happy."                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Data Structures

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `Entity` | Character or physical object with meme state | `name`, `kind`, `traits`, meme slots (`Joy`, `Fear`, `Love`, …), `pronoun` |
| `Trace` | Narration + effects produced by a kernel call | `kernel`, `text`, `effects` |
| `World` | Execution state for generation | `entities`, `actor`, `current_object`, `traces`, memes/links |
| `Variant` | One typed implementation of a kernel name | `name`, `fn`, `signature`, `hints` |
| `Registry` | Maps kernel names → list of typed variants | `kernels`, `additions` |
| `Executor` | AST interpreter (binds + executes variants) | `eval()`, `execute_tree()` |

### Kernel Function Pattern (typed dispatch)

```python
from gen6 import REGISTRY, World, Actor, Physical

@REGISTRY.kernel("KernelName")
def KernelName(ctx: World, hero: Actor, thing: Physical = None) -> str:
    """Kernel that does something.

    Parameters are *typed*: the binder selects this variant when the args
    match (e.g. a character + an object). `Actor` falls back to the current
    protagonist when no character is passed.
    """
    hero.Joy += 1                     # meme update on the world model
    if thing is not None:
        return f"{ctx.say(hero)} did something with {thing}."
    return f"{ctx.say(hero)} did something."
```

### Helper Functions

| Function | Purpose |
|----------|---------|
| `to_phrase(value)` | Convert any value to natural language phrase |
| `state_to_phrase(value)` | Convert state/emotion to descriptive phrase |
| `action_to_phrase(value)` | Convert action to past-tense verb phrase |
| `event_to_phrase(value)` | Convert event to "One day, X happened" format |
| `meta_story(world, hero, kw)` | Render a multi-phase structural kernel with coherent pronouns |
| `coherent(world, hero, sentences)` | Collapse repeated subjects to pronouns |
| `NLGUtils.past_tense(verb)` | Conjugate verb to past tense |
| `NLGUtils.article(word)` | Get "a" or "an" for word |
| `NLGUtils.join_list(items)` | Join with Oxford comma |

```python
from gen6 import generate

kernel = '''
Lily(Character, girl, Resourceful)
Encounter(Lily, wolf, forest)
Fear(Lily)
Brave(Lily)
Run(wolf)
'''

print(generate(kernel))
# "Once upon a time, there was a little resourceful girl named Lily.
#  Lily came across a wolf in the forest. She became afraid.
#  Even so, she was brave. The wolf ran away."
```


### `sample.py` `parse.py` `coverage.py` — Kernel Analysis
Parses extracted kernels, computes statistics, and identifies the most common narrative patterns.

### `story.py` — ⭐ Canonical Design (Memeplex Model / North Star)
The **design summary and reference for the whole project** (see [North Star](#-north-star-the-memeplex-model--see-storypy)). Defines the memeplex model: `Story` (memetic, composable, uppercase) vs `physical` (atomic, terminal, lowercase); characters inherit from both; **a `Story` has weight only when embedded in a physical carrier** ("Stories need to have associated physical objects, or story weight is zero"); attention algebra (`+`, `+=`, `/`); and a physics/plausibility model for consistency. `gen6.py` currently realizes only part of this — `story.py` is the north star the engine is being pulled back toward.

## Adding New Kernels (Coding Agent Workflow)

The approach for expanding kernel coverage is **interactive development with a coding agent** (like Claude, Cursor, etc.) rather than automated LLM synthesis.
See `AGENTS.md`


## Goals

**Current:**
- Extract ~1-5K executable kernels from TinyStories (2M samples)
- Test if coherent datasets can be reconstructed from < 5K kernels
- Train LLMs on kernel-generated stories and compare performance

**Future:**
- Evaluate impact of present/absent kernels on LLM capabilities
- Extract kernels from diverse sources (children's books, movies, religious texts)
- Map to existing narrative taxonomies (ATU-AT-Motif, etc.)
- Apply to non-narrative data (intent analysis, etc.)

## Data

- **`TinyStories_all_data/`**: Original TinyStories JSON files (data00-data49.json)
- **`TinyStories_kernels/`**: Extracted kernels in JSONL format
- **`bak/`**: Backup kernel files

## Usage

### Extract Kernels (requires LLM)
```bash
export LOCALHOST_BASE_URL="http://localhost:8001/v1"
export LOCALHOST_API_KEY="your-key"
python kernel.py
```

### Analyze Kernels
```bash
python parse.py
```

### Cluster Story Patterns
```bash
python cluster.py
```

### Generate Stories (no LLM needed)
```bash
python gen6.py                 # run the engine demo
python gen6registry.py         # list loaded packs + kernel/variant counts
```

### Generate from Custom Kernel
```python
from gen6 import generate

kernel = '''
Tim(Character, boy, Brave)
Monster(Character, scary)
Encounter(Tim, Monster)
Fear(Tim)
Brave(Tim)
Run(Monster)
Joy(Tim)
'''

print(generate(kernel))
```

> To use the full kernel library (all packs), import from `gen6registry`:
> `from gen6registry import generate_story`.

## Philosophy

The project is grounded in the **memeplex model** (canonical statement in [`story.py`](story.py); summarized in [North Star](#-north-star-the-memeplex-model--see-storypy) above): narratives are reusable **memetic objects** that propagate through culture, where a concept, an action, a character, and a whole story are the *same kind of composable object* — and a memeplex only affects the narrative once it is **embedded in a physical carrier** (book / person / many people); un-embedded memeplexes have zero weight. By decomposing stories into kernels, we can:

1. **Compress** narrative knowledge into a small, interpretable library
2. **Compose** new stories by combining kernels algebraically
3. **Analyze** what fundamental patterns make stories work
4. **Train** models on structured narrative representations

The generation engine should let **embedded memeplex state drive the prose** and only permit **compatible moves** (consistent with the concepts already present and how they interact), rather than executing kernels blindly.

**LLM usage is restricted to synthesis time** (extracting kernels, clustering, defining new kernel implementations). At generation time, stories are produced through classical execution — no LLM calls, just template filling and compositional algebra.

This is an exploration of story as code — where narrative structure becomes executable algebra.

## File Overview

| File | Purpose | LLM Required |
|------|---------|--------------|
| `kernel.py` | Extract kernels from stories | ✅ Yes |
| `parse.py` | Analyze kernel statistics | ❌ No |
| `cluster.py` | Cluster similar stories | ❌ No |
| `sample.py` | Sample & explore kernel usage (gen6) | ❌ No |
| `coverage.py` | Check kernel implementation coverage (gen6) | ❌ No |
| `quality.py` | Story-quality eval harness (agent-as-judge; see `QUALITY.md`) | ❌ No |
| `check_duplicates.py` | Find duplicate typed variants (gen6) | ❌ No |
| `gen6.py` | Unified engine: typed world + AST→AST rewrites + coherency layer | ❌ No |
| `gen6registry.py` | Auto-loads `gen6kXX` / `char6kXX` packs into one registry | ❌ No |
| `gen6k01.py`, `gen6k02.py`, … | Kernel packs (added kernels) | ❌ No |
| `wrld6.py` | Typed world / dispatch prototype (demo `gen6` builds on) | ❌ No |
| `rewr6.py` | AST→AST rewrite engine prototype (demo `gen6` builds on) | ❌ No |
| `story.py` | ⭐ **Canonical design / north star** — the memeplex model (memeplex == story, embed-or-zero-weight, physical carriers, compatibility) | ❌ No |
| `AGENTS.md` | Instructions for coding agents | ❌ No |
| `legacy/` | Previous engine (`gen5.py`, `gen5kXX`, `char5kXX`, older `gen*.py`) — reference only | ❌ No |

## For Coding Agents

See **[AGENTS.md](AGENTS.md)** for detailed instructions on implementing new kernels.
