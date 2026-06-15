# Agent Instructions: Writing a `storyworlds/` Script

This folder holds **standalone "story world" sketches**. Each script takes *one*
TinyStories-style tale and rebuilds it as a tiny **simulated world**: typed
entities with accumulating state, a forward-chaining causal rule engine, a
predict-then-act parent, reasonableness **constraints**, and a renderer that
turns the simulated state into prose. The goal is not broad coverage — it is to
capture the *logic, interactions, and causations* of one story well enough to
generate many **reasonable** variations of it.

The reference implementation is [`worlds/puddles.py`](worlds/puddles.py) (the
Lily / puddles / new-jacket tale, `data00:36242`). Read it end to end before
writing a new one — this guide is the map, `puddles.py` is the territory.

## Layout

```
storyworlds/
  AGENTS.md          <- this guide
  results.py         <- shared result containers (StoryError, QAItem, StorySample)
  asp.py             <- shared clingo helper (fact/solve/one_model/atoms)
  worlds/            <- one self-contained script per story domain
    puddles.py       <- "a child, a mess, a compromise" (reference)
    pirates.py       <- "a child, a forbidden spark, a safe alternative"
    <your_world>.py
```

`results.py` and `asp.py` are the only **shared** modules. `results.py` holds the
**generic, domain-agnostic** containers that every world serializes the same way.
Each script in `worlds/` is otherwise **one self-contained file**: its own
**domain-specific** `StoryParams`, all the prose, AND its clingo rules (inline).
Because the scripts are runnable directly (`python storyworlds/worlds/<name>.py`)
they bootstrap the import path at the top:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402
```

### Required: a clingo (ASP) twin of the gate — your self-contained tests

Every world ships **two implementations of the same logic** and they must agree:

1. the **Python** gate/outcome (`valid_combos`, `prize_at_risk`/`select_gear`,
   `hazard_at_risk`/`sensible_responses`, `would_avert`/`is_contained`/
   `outcome_of`) — the source of truth that drives prose; and
2. a **declarative ASP twin** in the *same file*: the constraint logic (and, for
   `pirates.py`, the outcome model) mirrored in an inline `ASP_RULES = r"""…"""`
   string, with the registries emitted as ASP facts by `asp_facts()` and clingo
   deriving the compatible-story set.

Keeping both is deliberate. The two are written from different angles
(procedural loop vs. declarative rules over the same facts), so `--verify`
comparing them is effectively a **self-contained regression test** — no fixture
files, no golden outputs. If you change the registries or a constraint, the two
sides drift and `--verify` fails until you fix whichever is wrong. Treat a green
`--verify` as part of "done"; it is the cheapest guard that the world's rules are
internally consistent. (It also buys bidirectional queries and future
diversity/optimization via `#minimize`.)

Convention (`import asp` is **lazy** — only inside these functions — so the prose
engine still runs without clingo):

```python
ASP_RULES = r"""valid(...) :- ... ."""   # inline rules (the .lp, in the file)
def asp_facts() -> str: ...               # registries -> facts (import asp locally)
def asp_valid_combos() -> list[tuple]: ...# clingo twin of valid_combos()
def asp_outcome(params) -> str: ...        # (if the world has branching outcomes)
def asp_verify() -> int: ...              # assert clingo == the Python logic; 0 = OK
```

CLI flags every world exposes: `--asp` (list the set), `--verify` (assert parity
— **must exit 0**), and `--show-asp` (dump facts + rules). Run with the venv that
has clingo:

```bash
storyworlds/.venv/bin/python worlds/<name>.py --verify   # must print OK and exit 0
```

What `asp_verify()` should check, at minimum: the ASP `valid/…` set equals the
Python `valid_combos()` set; any common-sense filter matches (e.g. sensible
responses); and, for worlds with branching endings, `asp_outcome(p) ==
outcome_of(p)` over the curated set **plus** a few hundred seeded random
scenarios.

> **North star.** These scripts are a concrete, runnable take on the memeplex
> model in [`../story.py`](../story.py): physical and emotional effects are the
> *same kind* of thing (small magnitudes that **accumulate on carriers** and
> then **drive the prose**); a consequence is narrated only once it is "embedded"
> past a threshold; and the world model should only allow **compatible moves**.
> Keep your script aligned with that — see `../AGENTS.md` for the project north
> star. Unlike `gen6`/`gen7`, a storyworld script is **self-contained** (pure
> stdlib, no LLM, no repo imports) and models a **single story domain**.

---

## What "good" looks like

A finished script:

- Runs with `python storyworlds/worlds/<name>.py` and prints a story close to
  the original, plus `--all`, `-n N --seed S`, and `--trace`.
- Derives prose from **simulated state**, not from one frozen paragraph. The
  parent's warning, the conflict, and the resolution all come from rules firing
  over entities — change a parameter and the consequences re-derive themselves.
- **Refuses to generate unreasonable variants.** This is the whole point of the
  constraint layer. A weak argument that happens to appear in the source dataset
  (e.g. "a *jacket* will get wet → wear *rain boots*") must be rejected, not
  reproduced. Constraints keep generation inside the story's plausible domain.

---

## The architecture (mirror `puddles.py`)

```
parameters (Setting / Activity / Prize / Gear ...)        <- the swappable vocabulary
        |
        v
entities with state  (Entity.meters = physical, Entity.memes = emotional)
        |
        v
verbs (introduce / wants / warn / grab_hand / compromise / accept ...)   <- screenplay beats
        |  each verb mutates state and may narrate
        v
causal rules (CAUSAL_RULES) forward-chained to a fixpoint (propagate)
        |  physical cascade + social/memeplex cascade, one engine
        v
prediction (predict_mess) — the parent simulates on a *copy* before speaking
        |
        v
constraints (prize_at_risk / select_gear / gender ...) — gate what may be told
        |
        v
renderer (World.render over paragraphs)  ->  prose
```

Key types and where to find them in `puddles.py`:

| Piece | In `puddles.py` | Purpose |
|---|---|---|
| `Entity` | `class Entity` (~L79) | character or object; `meters` (physical) + `memes` (emotional), `region`, `covers`, `worn_by`, `caretaker` |
| Parameter dataclasses | `Setting` / `Activity` / `Prize` / `Gear` (~L118–159) | the knobs you vary |
| `World` | `class World` (~L164) | entity store + ordered narration (`paragraphs`) + `copy()` for prediction |
| `Rule` + `CAUSAL_RULES` | (~L218–285) | `_r_soak` (mess spreads), `_r_workload` (mess → caretaker), `_r_grab_conflict` (social) |
| `propagate` | (~L287) | forward-chain all rules to a fixpoint; idempotent via `world.fired` |
| `predict_mess` | (~L326) | run the activity on a clone, read the resulting magnitudes |
| Constraint helpers | `prize_at_risk`, `select_gear` (~L307–319) | the reasonableness gate |
| Verbs | `introduce` … `accept` (~L340–461) | one function per story beat |
| `tell` | (~L467) | the screenplay: wires the verbs into the 3-act shape |
| Registries | `SETTINGS` / `ACTIVITIES` / `GEAR` / `PRIZES` | the content tables |
| `valid_combos` | enumerate only constraint-valid `(place, activity, prize)` triples |
| `StoryParams` | per-world params dataclass (lives in the script) |
| `QAItem` / `StorySample` / `StoryError` | shared result containers (imported from `../results.py`) |
| `build_parser` / `resolve_params` / `generate` / `emit` | the standard interface (see §8) |
| `main` | wires `args -> resolve_params -> generate -> emit`/JSON; `--all` / `-n` / `--trace` / `--qa` / `--json` |

---

## Step-by-step: from a story text to a new script

### 1. Read the source story and extract its skeleton

Identify, in plain words:

- **Cast & roles:** protagonist (the *doer*), and the foil (parent, friend,
  sibling, animal). Note genders.
- **The prized/charged object** and what the protagonist *loves* (an activity,
  an item, a person).
- **The premise → tension → turn → resolution arc.** Most TinyStories tales are
  3 short paragraphs: setup, conflict, resolution.
- **The causal chains.** Write them as arrows. Split into two kinds:
  - *Physical:* `jump in puddles → wet → shoes wet & dirty → mother more work`.
  - *Emotional / memeplex:* `forbidden but wants it → defiance`,
    `grabbed hand → conflict`, `compromise accepted → joy, conflict gone`.
- **The argument the foil makes**, and — critically — **whether it is sound**.
  This is where you find the constraint to enforce (see step 6).

### 2. Choose the parameters (what should be swappable)

Anything you could replace with a sibling concept *without breaking the logic*
becomes a parameter dataclass + a registry entry. In `puddles.py`: `Setting`
(park/garden/playroom…), `Activity` (puddles/rain/mud/paint/sand), `Prize`
(shoes/jacket/dress…), `Gear` (boots/raincoat/smock…). Pick the 3–5 axes that
matter for *your* story. Keep the vocabulary inside the story's domain — far-out
swaps can't be constrained sensibly (the user's rule of thumb: don't simulate
scenarios far from the original).

### 3. Model state on entities (physical vs. emotional)

Use two numeric dicts on `Entity`, exactly as `puddles.py` does:

- `meters` — physical magnitudes (`wet`, `muddy`, `dirty`, `workload`, …).
- `memes` — emotional magnitudes (`joy`, `defiance`, `conflict`, `love`, …).

This is the `story.py` idea made concrete: both are just magnitudes that
accumulate on a carrier. Add structural fields you need for constraints
(`region`, `covers`, `worn_by`, `caretaker`, `owner`).

### 4. Write the causal rules (one engine, both cascades)

Each rule is `(condition over state) → (state delta [+ optional narration])`,
idempotent via a `fired` signature, returning the sentences it produced. Put
**both** physical and social rules in `CAUSAL_RULES` so they read uniformly, and
run them to a fixpoint with `propagate`. Model accumulation with guarded `+= 1`
steps (coarse is fine). See `_r_soak` / `_r_workload` / `_r_grab_conflict`.

### 5. Make the foil *predict*, don't narrate the consequence as fact

A storyworld's signature move: the parent runs the world model **forward on a
throwaway `world.copy()`** (`predict_mess`) and turns the predicted magnitudes
into dialogue ("You'll get your shoes wet…"). The actual mess usually never
happens on-screen — it stays counterfactual. This is what makes the warning
*derived* rather than scripted. Verify with `--trace`: in the real timeline only
the social rule fired (`fired rules: ['conflict']`), the prize stayed clean.

### 6. Add constraints — refuse unreasonable variants

This is the most important quality step, and the reason these scripts exist.
For every "problem → fix" pair, ask *is the fix actually addressing the
problem?* Encode that as a gate that can return **no story**:

- **Relevance gate** (`prize_at_risk`): does the activity actually affect the
  charged object? Puddle-jumping splashes `{feet, legs}`; a jacket is `torso`,
  so it is *not at risk* → no honest warning → no story.
- **Efficacy gate** (`select_gear`): does the proposed fix actually cover/solve
  the problem? Rain boots cover `feet`, so they fix wet *shoes* but not a wet
  *jacket*; a *raincoat* covers `torso`, so `jacket + rain → raincoat` is
  allowed. This is precisely why the dataset's `jacket + puddles → rain boots`
  is rejected while `jacket + rain → raincoat` and `shoes + puddles → rain
  boots` are kept.
- **Plausibility gate** (e.g. `Prize.genders`): a boy in "a pretty new dress" is
  rejected; sand on socks "fixed" by open sandals is removed from the catalog.

Make the model itself enforce the gate where possible (region-aware rules), and
have the CLI print a short *why-rejected* message (`explain_rejection`) so the
constraint is legible. `valid_combos()` must enumerate only combos that pass all
gates; `resolve_params` samples from it (and picks a plausible gender per prize).

### 7. Write the screenplay (`tell`) and the renderer

One verb per beat, assembled into the 3-act shape in `tell`. Verbs mutate state
and call `world.say(...)`; `World.render()` joins `paragraphs` into prose. Only
narrate emotional beats once they're embedded past `THRESHOLD` (see `pout`,
which checks `conflict`). Keep `tell` **deterministic** so pinned outputs are
stable; put variety in the registries, not in random phrasing.

**Outcomes can branch — and not every ending is happy.** Cautionary tales
sometimes go wrong, and the world model should *earn* that rather than bolt on a
sad paragraph. Drive the branch from state, not a coin flip: model a quantity and
its counter-quantity, then let `tell` pick the act. `worlds/pirates.py` does this
with `fire_severity(target, delay)` (a fast target + the head start the fire got)
versus `Response.power`; `is_contained(...)` decides between the calm-rescue acts
and the *burned-down* acts (everyone still escapes — keep failure age-appropriate).
Record the result (`facts["outcome"]`) and make all three Q&A sets read it, so the
questions, the lesson, and even the world-knowledge topics (e.g. swap the safe-light
facts for "get out / call firefighters") match the ending that actually happened.
Expose the tipping-point input as a debug knob (`--delay`) and store it in
`StoryParams` so each ending stays reproducible.

The branch need not be binary. `pirates.py` adds a third **averted** outcome: a
*near-miss* where the danger never happens at all. It too is state-driven —
`would_avert(...)` checks the hidden character state (the cautioner is the older
sibling, so their caution plus the warning beat overrules the instigator's nerve);
when true, `tell` skips the accident entirely (`back_down` → straight to the safe
gift) and the three Q&A sets switch to the no-fire variant. This is also where the
*hidden* character state earns its keep: ages/relationship/trust are never stated
outright, but they decide whether a defiance reads as "the younger didn't stop
him" (fire) or "the older sibling talked him out of it" (averted) — let the memes
and `attrs` pick the wording in the verbs, and keep the structural decision in one
helper that both `tell` and `outcome_of` call so labels never drift.

### 8. Wire the standard interface, CLI, and a trace

Every storyworld script exposes the **same four functions** so tooling (and the
next agent) can drive any script the same way. Match these names/signatures:

```python
def build_parser() -> argparse.ArgumentParser      # only flags; no logic
def resolve_params(args, rng: random.Random) -> StoryParams   # random where unspecified
def generate(params: StoryParams) -> StorySample   # the core: world -> story + 3 Q&A sets
def emit(sample: StorySample, *, trace=False, qa=False, header="") -> None  # human output
```

Keep `build_parser` and `generate` free of each other's concerns: `main` wires
them (`args -> resolve_params -> generate -> emit`/JSON). `generate(params)` must
be **deterministic** — the same `StoryParams` always yields the same
`StorySample`.

**CLI conventions (random-by-default, lightly pinnable):**

- Offer a *small* set (≈3–5) of `choices=` pins for debugging — in `puddles.py`:
  `--place --activity --prize --gender --parent --name`. Don't over-build the
  CLI; an agent can edit code as easily as pass a flag.
- **No defaults on the choice flags.** Any flag left unset is chosen at random by
  `resolve_params` (seeded), keeping the combo constraint-valid. A provided flag
  pins that axis; the rest are still randomized.
- `--seed` is the *base* seed (default: a fresh random seed). Derive a per-story
  seed (`base + i`) and store the concrete seed back into `StoryParams.seed`, so
  every emitted story is independently reproducible (`--seed <that> -n 1`).
- Modes: `-n N` (N random valid stories, deduped on story text), `--all` (the
  curated set), `--trace` (dump entity meters/memes + `fired` rules — your proof
  prose is state-driven), `--qa`, and `--json`.
- If explicit flags describe an *unreasonable* story, raise `StoryError` with a
  human reason (see step 6) instead of emitting a bad story.

### 8b. Generate Q&A — three deliberately separate sets

Treat Q&A as part of the deliverable, not an afterthought (cf. the gen7 QA
guidance in `../AGENTS.md`). Generate each set from the **simulated world**, not
by parsing the rendered English. Record what you need during the screenplay
(`world.facts` in `puddles.py`) and read it back. Provide a `--qa` flag. The
three sets are distinct in *what they depend on*:

1. **Generation prompts** (`generation_prompts`) — the "asks" that would produce
   a story like this. Built from the theme plus the story's key parameters
   (activity keyword, prize, hero). These are inputs, not questions.
   *e.g. "Write a story on 'a child, a mess, a compromise' that includes the
   word \"puddles\"."*
2. **Story-grounded Q&A** (`story_qa`) — questions answerable only from this
   story's text/world. Derive the answers from recorded facts and state: the
   *why* questions should read the **predicted** consequence (the parent's
   forward-simulation) and the conflict/resolution memes, so the answer explains
   cause and effect. Prefer full, multi-sentence answers.
   *e.g. "Explain how the mother was upset and why." → grounded in predicted
   mess + workload + the grabbed-hand conflict.*
3. **World-knowledge Q&A** (`world_knowledge_qa`) — child-level facts about the
   world's *elements*, answerable WITHOUT the story. Keep a small `KNOWLEDGE`
   table keyed by topic tag (`puddle`, `wet`, `rain`, `boots`, …); select the
   entries whose tags appear in this story (`Activity.tags` + the chosen gear).
   *e.g. "What is a puddle?", "Why is it cold when your feet get wet?"*

Keep the three sets separated and labeled (`format_qa`). When you neutralize
dialogue text for answers (e.g. "put on **our** boots" → "their"), replace the
longer token first (`"your "` before `"our "`).

### 8c. Result containers & JSON serialization

The generic containers are **shared** in [`../results.py`](results.py) — import
them, don't redefine them:

```python
from results import QAItem, StoryError, StorySample
```

```python
# storyworlds/results.py (shared, domain-agnostic)
class StoryError(Exception): ...
@dataclass
class QAItem:        # one question/answer pair
    question: str; answer: str
@dataclass
class StorySample:   # the full deliverable for ANY world
    params: Any                   # the script's own StoryParams dataclass
    story: str
    prompts: list[str]            # set (1)
    story_qa: list[QAItem]        # set (2)
    world_qa: list[QAItem]        # set (3)
    world: Optional[Any] = field(default=None, repr=False, compare=False)  # NOT serialized
    def to_dict(self) -> dict: ...     # params + story + 3 sets (uses dataclasses.asdict)
    def to_json(self, indent=2) -> str: ...
```

Each script defines **only** its own `StoryParams` (its fields are
world-specific), and `generate` returns a shared `StorySample`:

```python
# storyworlds/worlds/<name>.py (domain-specific)
@dataclass
class StoryParams:   # everything needed to reproduce ONE story
    place: str; activity: str; prize: str; name: str
    gender: str; parent: str; trait: str; seed: Optional[int] = None
```

Rules of thumb:

- `StoryParams` holds **only** what makes generation deterministic (the pinned
  axes + the resolved random ones + the seed). If a field influences the prose
  (e.g. `trait`), it belongs here so the story is reproducible. It must be a
  `@dataclass` so `StorySample.to_dict` can `asdict` it.
- Keep the live world object on `StorySample.world` for `--trace`, but it is
  excluded from serialization (`repr=False`, not in `to_dict`).
- `--json` emits one object for a single story and a JSON **array** for `-n N` /
  `--all`. Use `ensure_ascii=False`.

### 9. Generate a batch, read it, and fix the recurring issues

Run `python storyworlds/worlds/<name>.py -n 10 --seed <s>` and **read every story**.
Look for: pronoun/agreement bugs, plural mismatches ("wore it" vs "them"),
gender/object mismatches, weak arguments that slipped through a gate, and odd
phrasings (e.g. indoor "went to the playroom" → "were in the playroom", or a
"playing … playing" echo). Tighten the registries/constraints and regenerate
until a fresh batch is clean. (This is exactly how `puddles.py` gained the
gender gate, the raincoat activity, and the honest sand model.)

---

## Conventions & guardrails

- **Self-contained:** stdlib only; no LLM, no importing repo engines. One file.
- **State drives prose:** prefer reading `meters`/`memes` over hard-coding a
  sentence. If you're tempted to print a consequence directly, make a rule
  produce it and let the renderer pick it up.
- **Constraints over coverage:** it is better to generate fewer, fully
  reasonable stories than many that include a weak one — even one present in the
  original dataset.
- **Deterministic `tell`/`generate`:** randomness lives only in `resolve_params`
  (seeded). `generate(params)` is a pure function of its `StoryParams`.
- **Keep it coarse:** `+= 1` magnitudes, a handful of regions/mess kinds, a
  fixpoint loop. Don't build a physics engine; build just enough world to make
  the argument honest.
- **Stay in domain:** model variations close to the source story; don't stretch
  to scenarios you can't constrain plausibly.

## Checklist before finishing

- [ ] `python storyworlds/worlds/<name>.py` reproduces the source tale closely.
- [ ] `--all`, `-n N`, `--seed S`, `--trace`, `--json` all run.
- [ ] Standard interface present: `build_parser` / `resolve_params` / `generate`
      / `emit`, with no default on the choice flags (unset = seeded-random).
- [ ] Same `--seed` reproduces byte-identical output; a single story replays from
      its own `StoryParams.seed`.
- [ ] `--json` round-trips (`StorySample.to_dict`/`to_json`): params + story +
      all three Q&A sets; the live `World` is excluded.
- [ ] A known *unreasonable* combo raises `StoryError` / prints a clear rejection.
- [ ] `valid_combos()` contains only sound problem/fix/wearer combinations.
- [ ] ASP twin present and **`--verify` exits 0**: the inline `ASP_RULES` +
      `asp_facts()` reproduce the Python gate (and `outcome_of`, if any) exactly.
      This is the world's self-contained test — keep it green.
- [ ] A fresh `-n 10` batch reads cleanly (pronouns, plurals, phrasing, logic).
- [ ] `--trace` shows the consequence stayed counterfactual (state-driven prose).
- [ ] `--qa` prints all three sets (prompts / story-grounded / world-knowledge),
      each derived from the simulated world rather than the rendered text.
- [ ] You stated, briefly, how the script honors the `story.py` north star.
