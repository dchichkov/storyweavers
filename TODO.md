# Storyweavers Engine Improvements TODO

Engine improvements inspired by interactive fiction systems (Ink, ChoiceScript, Inform 7, Twine, TADS).

---

## ⭐ North Star — The Memeplex Model (canonical design: [`story.py`](story.py))

Keep every change pointed at the core idea in **[`story.py`](story.py)** (and the
[README North Star](README.md#-north-star-the-memeplex-model--see-storypy)).
Don't let coverage/quality work quietly drift away from it:

1. **Memeplex == story.** Concepts (`Love`, `Fear`, `Envy`), actions/verbs,
   characters, and whole narratives are the *same kind* of composable object
   (algebra: `+`, `+=`, `/`). They differ in scale, not kind.
2. **Embed-or-zero-weight.** A memeplex is a platonic form; it only affects the
   narrative once **embedded in a physical carrier** (book / person / many
   people). *"Stories need to have associated physical objects, or story weight
   is zero."* Un-embedded concepts must **not** surface.
3. **Track the physical level + concept magnitudes.** Each carrier holds how much
   of each concept is present (`Entity.memes` is the seed). The story is the
   evolving state of these embedded magnitudes.
4. **Only allow compatible moves.** Generation must stay consistent with the
   memeplexes already present and how they interact. *Example:* max out `Envy` on
   `Scar(Character, lion)` → the world model should permit only Envy-compatible
   moves and never narrate out-of-character kindness unless the embedded state
   changes first.

### North-star backlog (the gaps between `gen6.py` and `story.py`)

- [ ] **Embed-or-zero-weight rule (engine).** A bare concept must bind to a
      carrier (`ctx.actor` / `ctx.current_object`) as a meme and render its
      *physical manifestation*; if it can't embed, **drop it** (weight zero).
      This is the principled fix for the **`literal_concept`** defect (today the
      engine leaks un-embedded platonic forms as "There was bravery."). Fix in
      `_combine` / `fallback_text`; re-measure with `quality.py` (seed 42).
      **Partial:** `_combine` and concept-only fallback now embed bare concepts
      into the current carrier (or drop them when there is no carrier). Only
      readable abstract states surface as "X felt indifference"; action-like
      concepts such as `HelpOthers` are recorded as memes but no longer leak as
      bad prose. Still needs a full seed-42 `quality.py` regrade and broader
      missing-kernel cleanup.
- [ ] **Compatibility / constraint pass.** Lift the `constraint_pass` /
      `StoryIR` sketch below (search "World Model Constraints") into a real
      AST/execution gate: rescue-needs-danger, fly-needs-a-flying-creature,
      forgiveness-needs-prior-conflict, **plus meme-gated moves** (e.g. a
      maxed-`Envy` carrier resists pro-social kernels). Start with ~4 rules.
- [ ] **Unify representation toward `memeplex == story`.** Today kernels (typed
      Python fns), concepts (float slots), and characters (entities) are three
      different things; converge them toward one composable `Story`/memeplex
      object (see the `@Stories` algebra + deferred execution in `story.py`).
- [ ] **Physical / plausibility model.** Grow the physical layer beyond object
      owner/status (started) toward `story.py`'s `physical()` consistency model
      (real / fantasy / story-world physics, plausibility of moves).
- [x] **Shared weight-reading mechanism (read side).** Added the *general*
      half of weight-driven narration to `gen6.py`: `pick(value, bands)` (a
      magnitude->variant selector), `MOOD_MODIFIERS` (emotion -> manner adverb
      lexicon), and `World.mood()` / `World.mood_lead()` (the actor's dominant
      *transient* emotion as a ready-to-splice adverb, with a per-entity
      anti-repeat guard). Wired into a curated set (`See`, `Walk`, `Observe`/
      `Look`/`Watch`, `Eat`, `Climb`) and the gen6k03 `transitive` factory.
      Design note (confirmed in discussion): the *syntax* generalizes (read via
      `meme()`/`MemeSlot`, select via `pick`, write via `+=`/`@addition`) but the
      *semantics* stay kernel-local — `mood()` covers the common "flavor by
      dominant emotion" case in one line; bespoke kernels still read memes
      directly. **Measured:** fires on **22%** of 3,000 stories (758 adverbs),
      adjacent-dup spam **0.1%**, coverage/execution unchanged. Impact is gated
      upstream — emotions must be embedded densely enough and an action must
      follow — so it grows as coverage/quality improve.
- [ ] **Keep it visible.** Re-read this section before large engine passes;
      record alignment (or deliberate deviation) in PRs.

**Proof-of-concept:** [`memeplex_demo.py`](memeplex_demo.py) already runs `Listen`
/ `Purr` on gen6 — memeplex magnitudes (`Story`/`Love`/`We`) transmit between
carriers via the world model (visible in `generate_world().state()`), and an AST
rewrite reframes `Tell → Listen`. Two gaps it surfaces to fold into the engine:
(a) gen6's `/` operator is **binary suppress** (`X / n`, n≥3 drops `X`), not the
**fractional attention weight** story.py uses (`Content / 10`) — the demo does the
dilution in Python; a real fractional-weight model is still TODO (see "Fragment
weights"); (b) the 3-arg memeplex `Listen` ties with the generic intransitive
`Listen` and only wins because the demo reorders variants — dispatch should prefer
the more *specific* typed variant on ties.

> Status table (which principles are realized today) is in the
> [README North Star](README.md#-north-star-the-memeplex-model--see-storypy).

---

## Status Update — `gen6.py` (unified engine)

Much of the design below has now been prototyped and assembled into a single
self-contained engine: **`gen6.py`**. It fuses the two `*6` prototypes plus a
coherency layer:

```
source --[declarative rewrites]--> --[coherence tagging]--> --[typed-world execution]--> --[narrate]--> story
```

| Capability | Where | State |
|------------|-------|-------|
| Typed kernels + backtracking dispatch | `gen6.py` (from `wrld6.py`) | ✅ Done |
| World/Entity state, meme `+=`, effect + narration trace | `gen6.py` (from `wrld6.py`) | ✅ Done |
| AST → AST declarative rewrites (`Rewrite`, `+`-chain windowing, meta call-names) | `gen6.py` (from `rewr6.py`) | ✅ Done |
| **Coherency layer**: pronoun tagging pass (`tag_coherence`) + central `_use_pronoun`/`_transition` handling | `gen6.py` | ✅ Done |
| Minimal typed kernel set (~35) ported from `gen5.py` | `gen6.py` | ✅ Done |
| `generate()` / `generate_world()` entrypoints | `gen6.py` | ✅ Done |

This directly addresses the **"Fundamental Problem: Direct Interpretation"**
below: instead of every kernel deciding pronouns/transitions/prerequisites, a
single AST pass tags continuation sentences and the renderer (`World.say`)
honours the tag. Kernel bodies stay tiny and typed.

**`gen6.py` is now the engine** and all tooling runs on it. The previous engine
(`gen5.py` + its `gen5kXX` / `char5kXX` packs, rich NLG, 800+ kernels) has been
moved to `legacy/` for reference only. `wrld6.py` / `rewr6.py` remain at top level
as the reference demos that `gen6.py` was assembled from.

Run it:

```bash
python gen6.py
```

## Status Update — `gen7.py` (MUD-like StoryWorld prototype)

`gen7.py` is a clean-break vertical slice that parses TinyStories kernel ASTs
into semantic `Frame` commands, applies them to a persistent `StoryWorld`, and
renders from event/state history. It intentionally does **not** import gen6
kernel packs; the goal is to test whether MUD-like world simulation at the
kernel/AST level produces better tiny stories than template-first execution.

Run it:

```bash
python gen7.py --story-id data00:36222
python gen7_story_tests.py --run
python gen7_story_tests.py --sample 10 --seed 777 --scan 20000
```

Current slice:

| Capability | Where | State |
|------------|-------|-------|
| Standalone parser/world/renderer entrypoints (`parse_story`, `generate_world`, `generate`, `render`) | `gen7.py` | ✅ first prototype |
| Pack registry for distributed gen7 semantics (`direct_alias`, `direct_handler`, `renderer`) | `gen7.py`, `gen7packs/` | ✅ first extraction |
| Physical carriers with object status/owner/location, relation edges, and meme magnitudes | `StoryWorld` / `Entity` | ✅ seed model |
| Semantic frames for character setup, find/lost/search/ask/help/give/broken/fix/play/fear/rescue/friendship/lesson/reaction/transform | `Parser.direct_call` + `gen7packs.actions` | ✅ first slice |
| First renderer pack for desire/find/search/loss/ask/help/play/friendship/lesson/emotion/encounter/problem/transform/visit/object-state frames | `gen7packs.renderers` | ✅ first extraction |
| Lowercase object/state normalization (`lost(toy)`, `broken(toy)`, `hook(stick,string)`) | `LowerExpr` lowering | ✅ partial |
| 55 representative pinned stories from `data00` + `data01` | `gen7_story_tests.py`, `gen7_story_tests/` | ✅ snapshots pass |

Known gaps from the first 20 pins:

- [~] Scale gen7 sampling as part of every quality iteration. `gen7_story_tests.py`
      now has `--sample N --seed S --scan M`, which prints deterministic
      unpinned gen7 candidates with summary, generated text, and original text.
      The first sampled batch promoted 5 additional pins (`data00:14971`,
      `data00:18138`, `data00:18146`, `data00:9315`, `data01:3375`), bringing
      the suite to 55. Continue adding 5-10 reviewed pins per quality pass so
      regressions and new failure modes stay visible.
- [~] Split gen7 out of the giant-if prototype. The frame-name ontology now lives
      in `gen7packs.actions`, and a first high-frequency renderer batch lives in
      `gen7packs.renderers`. `gen7.py` still owns too much role normalization and
      many residual render branches; next migrations should move direct-call
      special cases into `direct_handler` packs and split world constraints/effects
      by frame kind while keeping the 49 snapshots green.
- [~] Continue pack-local quality fixes from rough samples. Untyped common names
      now infer likely child/person types (`Lily(Character, Neat + Kind)` renders
      as a girl rather than a literal "lily"), play locations use scene
      prepositions ("in the woods", "at the park", "on the sand"), action-like
      desires such as `Longing(jump(pit))` render as verbs, scoped warnings attach
      to the parent actor, and renderer-pack handlers for `Return`/`Praise` avoid
      "returned the play" / "praised someone" style fallbacks. Remaining work:
      owner transfer for chewed/lost toys, explicit rescue-agent extraction, and
      broader action ontology for `Build`/`Use`/`Show`/`Celebration`-style beats.
- [~] Broaden the first gen7 action ontology slice. `Pull(rope, Bear, Tim)` now
      lowers to a rescue child frame so parent `Rescue(Tim, ...)` can render
      "Bear rescued Tim"; `Build`/`Use`/`Show`/`CalendarAdd`/`Anticipation`/
      `Celebration` now have first-pass frame/rendering support; executable
      suggestion wrappers are suppressed when their child action already renders.
      This improves pinned fort, calendar, show-and-tell, rescue, and retrieve
      stories while keeping snapshots deterministic. Remaining work: move more
      direct-call special cases out of `gen7.py`, model inventory/ownership for
      damaged toys, and make group builders/celebrations less template-like.
- [~] Add first damaged-object ownership semantics. Routine play now embeds
      simple owned toy objects, `Incident(Dog, chew(toy))` survives as a `chew`
      frame, `chew` marks the object damaged without transferring ownership, and
      later `Loss(toy)` keeps the owner as the emotional subject. The pilot/toy
      sample is now pinned (`data01:73907`) and renders "Dog chewed her toy.
      Lily lost her toy..." instead of making the dog own the toy. Remaining
      work: generalize inventory beyond play/toy traits and render damaged/lost
      state with richer recovery/repair consequences.
- [~] Clean up vague structural renderer fallbacks. Empty `Routine(...)` wrappers
      now drop instead of rendering "had a familiar routine", location-only
      routines avoid duplicating later concrete scene actions, routine participant
      groups propagate into child play frames, vague `Outcome(... Friendship ...)`
      wrappers are suppressed, and stateful outcomes such as the seed story render
      a real consequence ("stayed small and felt sad"). Remaining work: replace
      the long tail of generic lesson phrasings with state-aware morals and move
      these renderer overrides into smaller domain packs as the ontology grows.
- [~] Replace common placeholder morals with actionable lesson text. The gen7
      renderer pack now maps recurring lesson memeplexes such as `Careful`,
      `Cooperation`, `NoStrangerTalk`, `UnknownNotScary`, `AskingForHelp`,
      `Responsibility + Kindness`, `Help + Friendship + Joy`, `GoodFeel`, and
      `Change` to concrete
      morals ("learned to be careful", "learned that working together helped")
      instead of the generic "learned an important lesson about X" fallback.
      Remaining work: make these topic rules data-driven packs and let relation
      / meme magnitudes choose the moral when multiple lessons are plausible.
- [~] Improve simple request/recipient role flow. `Ask(..., want=...)` now keeps
      the requested object as the goal, one-character `Give`/`Teach` calls infer
      the prior protagonist as recipient/student, and the pinned breakfast story
      renders "asked Mommy for the cereal" / "gave Lily a bowl of cereal" instead
      of help/someone fallbacks. Remaining work: model teaching content/tools
      explicitly (for example `raingauge`) and broaden breakfast/inventory
      semantics beyond the first cereal+bowl case.
- [~] Preserve named nonhuman carrier identity in discourse. Repeated animal,
      plant, and object-carrier actors now keep their story name instead of
      collapsing long action chains to ambiguous "It ..." subjects; this also
      exposes true actor transitions such as Lily the cat rewarding Max. `Quest`
      now preserves `objective=` as the desire goal, so a food quest renders as
      wanting food instead of "something special". Remaining work: add a richer
      reference planner so named nonhumans can alternate names, pronouns, and
      role phrases without losing clarity.
- [~] Expand helper/advice action semantics. `method=` is now executable phase
      data, `Cut(...)` lowers into a reusable action frame, `Help(...,
      method=Ask(...) + Cut(bush))` renders the concrete action ("helped cut the
      bush") instead of "helped by asking for help", and advice about `AskHelp`
      renders as "advised asking for help". Remaining work: represent advice as
      an explicit speaker/listener/command frame so refusals can say what was
      refused rather than generic "said no".
- [~] Suppress empty structural desires and recover simple visit hosts. `Quest`
      no longer invents "wanted something special" when the AST has no explicit
      goal, single-character visits now infer the first declared protagonist as
      host (`Sam visited Tim`), and parent `Bake(...)` wrappers are suppressed
      when a concrete child bake already renders the baked object. Remaining
      work: infer positive goals from problem/process traces instead of merely
      dropping empty desires, and add richer host/location inference for visits.
- [~] Render abstract concepts through their physical carriers. Desire for
      `magic` now reads as wanting to learn magic, `Reveal(ShapeShift)` binds to
      the character carrying that trait ("Bunny changed shape"),
      and encounter process frames now keep their partner through bond,
      separation, and reunion beats. Remaining work: generalize this into an
      embedded-concept rendering table so more traits/actions choose carrier
      verbs instead of noun phrases.
- [~] Improve phase ordering inside structural calls. `Rescue(...)`, `Deal(...)`,
      `Idea(...)`, and `Race(...)` now reorder parent/child frames more
      coherently; `Cautionary(...)` now defers generic lessons until after the
      event trace and skips them when an explicit lesson exists. Remaining work
      is a general phase planner instead of per-parent ordering.
- [~] Add richer exchange/transaction semantics for `Deal`, `Transform`, `Give`,
      and `Receive`. Event-time ownership snapshots now prevent final-state
      ownership from corrupting earlier prose, and deals render promises before
      later actual transforms. Remaining work: explicit inventory/transaction
      intent so chains like `penny -> toy` do not need bespoke handling.
- [~] Add action frames for common concept-only process values (`Run`, `Victory`,
      `Persistence`, `Recall`, `Competition`). The first mapping now gives race
      and rescue stories visible process beats; newer mappings cover
      `Bond`/`Separation`/`AskHelp`/`Success`/`Safe`/`Harmony` style process
      concepts. Expand this into a typed action ontology.
- [~] Improve routine/activity lowering for `screen(tablet)`, `Bake(...)`,
      `Collaboration(...)`, and `Satisfaction(...)`. Collaboration/satisfaction
      now render as world events; screen-heavy routines and farm chores have
      first-pass world text; richer bake/party flows are still thin.
- [~] Improve scoped focus/ownership. Parent phases now override stale actor
      focus for implicit child calls, event-time ownership can still render
      animal-owned objects as "its toy", and repeated exact sentences /
      repeated emotion labels are suppressed. `Find(Character)` now binds the
      found character as the target under a parent actor, conflict blockers own
      their motive frames, and nested physical labels like `bottom(pond)` keep
      their object content. Single-character child actions like `Hold(Tom)`,
      `Drop(Tom)`, and `Teach(Sam, ...)` now bind the parent actor as the doer
      and the child character as the patient. Participant lists now drive direct
      actions like group play, and generic child/person pronouns use common name
      cues when the type is otherwise too broad. Remaining work: track whether
      an actor was explicit in the AST instead of relying on scoped locks.
- [~] Stabilize local actor focus across subject annotations. Simple unknown
      subject calls like `Bossy(Lily)` now update the current actor for later
      bare actions, while kwarg-heavy calls such as `Caution(Mom, avoid=...)`
      no longer steal the following lesson from the protagonist. Repeated loss
      beats collapse by object so `Loss(kite)` does not render twice as
      "lost her lost kite". Direct meta calls now rescope unbound child phase
      frames to the parent actor too, so `Discovery(Lily, state=Routine(...))`
      and `Rescue(Tim, state=Routine(...))` no longer assign the routine to the
      last declared character.
- [~] Treat helper child-actions as actions, not objects. `Help(Sam,
      Remove(Veil))` now renders as helping take off the veil, and lower action
      objects such as `Help(push(gate))` render as helping push the gate instead
      of "helped the push".
- [~] Preserve physical scene roles before rendering. Location-like kwargs now
      lower to physical scene objects for direct calls such as `Visit(...,
      location=castle)`, companions stay attached to visit frames, object
      encounters render as seeing/noticing physical objects, and mixed
      character/object encounters preserve both (`met Tommy and saw the bag`).
      Prepositional lower objects such as `under(bed)` now render as physical
      locations rather than nounified objects (`found the piece under the bed`,
      `visited the park and spent time under the tree`).
- [~] Render action-like goals as actions. Requests such as `Request(Lily,
      to=Daddy, ask=Bring(island, closer))` now render as asking Daddy to bring
      the island closer instead of asking for "the bring"; body-part tool
      arguments such as `Pick(Tim, ball, hand)` no longer leak into prose.
      Desire frames can also read child actions, so `Desire(Help(cake))` becomes
      wanting to help with the cake rather than wanting "the help".
- [~] Preserve person-to-person visit roles. `Visit(Friend, Lily)` now renders
      as Friend visiting Lily rather than "Friend and Lily visited Lily";
      group-visit wording is still used when the object is a real place.
- [~] Broaden direct semantic kernels. `Reward`, `Approve`, `Perform`, `Visit`,
      `Hide`, `Warning`, `Intervention`, `Praise`, `Heal`, `Report`, and
      `Investigation` now have first-pass frames/rendering; remaining work is
      role typing so objects like `owner` / `BoxUnderBed` become proper
      participants/locations instead of noun phrases.
- [~] Normalize explicit lessons without duplicating child events. `lesson=Careful`
      now becomes a real lesson frame, repeated lesson topics are collapsed, and
      composed lesson phases such as `Avoidance(...) + Memory(...)` keep their
      concrete child frames instead of re-wrapping them as extra morals.
- [ ] Add a manual `QUALITY.md` grade for the 55 gen7 pins and compare them
      against gen6 output; the harness pins behavior but does not judge it.

### Still open for `gen6.py`

- **NLG depth**: port more of `gen5.py`'s `NLGUtils`/templates (verb inflection,
  article handling, template variety) — `gen6` currently uses fixed phrasings.
- **Transitions**: `_transition` is plumbed through but not yet driven by phase;
  add `when_src`/`effect_src` guards (below) to emit phase-aware connectors.
- **Rewrite expressiveness**: kwargs/rest wildcards and `when_src`/`effect_src`
  guards (the declarative engine currently matches strictly and has no guards).
- **Coverage/tests**: add a coverage + pinned-story harness pointed at `gen6`
  (mirroring `coverage.py` + `story_tests/`), and grow the ported kernel set.

---

## gen6 ← gen5 Feature Parity (Migration Checklist)

Goal: bring `gen6.py` to functional parity with `gen5.py` so the tooling can be
ported and `gen5.py` retired. **The kernel *format* is already unified** — both
engines `ast.parse` the same `kernel` field from `TinyStories_kernels/*.jsonl`,
so **no re-extraction is needed**. The gaps are robustness, AST coverage, NLG,
and kernel-library size.

### Compatibility snapshot (data00, 3,000-story sample)

| Metric | gen6 initial | **gen6 now** | gen5 | Notes |
|--------|-------------|--------------|------|-------|
| Parse OK (`ast.parse`) | 83.5% | 83.5% | ~80.8% | Same format; remaining ~16% is non-Python the LLM emitted |
| Execute end-to-end (no exception) | 0.2% | **99.9%** | 96.5% | Fallback never raises → higher than gen5 |
| Kernel-name coverage (usages) | 36.9% | **93.0%** | 85.0% | 1161 kernel names / 1195 variants; data01-driven coverage push also lifted data00 past 93% |
| Stories ≥90% kernel-covered | — | 40,631 | 26,982 | long tail remains, but gen6 now exceeds the old gen5 coverage snapshot |

The robustness headline is resolved: **0.2% → 99.9% end-to-end execution**. The
remaining gap to gen5 is purely **kernel-library size** (port more kernels).

### A. Robustness / execution (highest priority) — ✅ DONE

- [x] **Fallback for unknown kernels** — `gen6.fallback_text`: CamelCase →
      readable past-tense sentence; folds in nested Traces from args/kwargs.
- [x] **No-variant fallback** — `Registry._select_variant` returns `None`;
      `Registry.call` routes to `fallback_text` instead of raising.
- [x] **Per-kernel try/except** in `Registry.call` so a failing kernel degrades
      to fallback text rather than killing generation.
- [x] **Arity tolerance** — binder now supports optional positional params and
      skipping; `Actor` params fall back to the protagonist, so shapes like
      `Find(newPlace)` / `Play(smallball)` bind or degrade cleanly.
- [x] **Variable-arity characters (`*args`)** — the binder now accepts
      `VAR_POSITIONAL` params (optionally type-filtered, e.g. `*chars: Character`),
      building a real positional call. Handles dataset shapes like
      `Visit(zoo, Timmy, Mom, Gorilla)` / `Apology(Anna, Ben, Lily)`. (Found via
      the AGENTS.md workflow dry-run; see "Findings" below.)
- [x] **Fallback keeps trailing characters** — `fallback_text` now lists extra
      characters as targets, so `Visit(Lily, Mom, Friend)` →
      "Lily visited Mom and Friend." instead of dropping Mom/Friend.

### B. AST / operator coverage — ✅ (weights deferred)

- [x] **`/` attention-dilution operator** — `X / n` with large `n` suppresses `X`.
- [x] **Lists** `[a, b, c]` (`ast.List` / `ast.Tuple`).
- [x] **Subscript/indexing** (`ast.Subscript`) + unary minus.
- [ ] **Fragment weights** — full weight model + threshold filtering at render
      (gen6 currently only does binary suppress via `/`). Deferred.

### C. Meta / structural kernels (kwarg-driven) — ✅ first batch

- [x] First batch of multi-phase meta kernels in `gen6k01.py`: **Quest, Journey,
      Cautionary, Conflict, Transformation, Resolution, Response, Encounter,
      Accident, Routine, Friendship (phased)** (kwargs `state=`, `catalyst=`,
      `process=`, `insight=`, `outcome=`, `transformation=`, …).
- [x] **Focus pre-binding** — `Executor.eval` sets `world.actor` from the first
      character arg before evaluating the rest, so nested kwargs bind to the
      right actor.

### D. NLG / surface text — ✅ (TemplateEngine deferred)

- [x] **`NLGUtils`** ported: `past_tense` (irregular table + rules), `article`
      (a/an phonetic exceptions), `pluralize` (irregulars), `join_list` (Oxford).
      Fixed consonant-doubling so multi-syllable verbs don't double
      (`visit`→`visited`, not `visitted`); added common offenders to the
      irregular table. (Found via the workflow dry-run.)
- [x] **Concept-phrase helpers**: `to_phrase`, `state_to_phrase`,
      `action_to_phrase`, `event_to_phrase`, `_camel_words`.
- [ ] **TemplateEngine**: 5+ phrasing variations per kernel, gender-filtered +
      first-vs-subsequent intros. gen6 uses fixed phrasings. Deferred.
- [ ] **Character type inference**: richer `common_types`, trait-vs-type
      disambiguation. Partial (auto-"little" for children; he/she/they tables).

### E. Kernel library size & state model

- [~] **Port high-frequency kernels** — `gen6k01.py` (first batch), `gen6k02.py`
      (`Visit`), and `gen6k03.py` (~68 kernels from the top-70 missing list:
      Build, Open, Draw, Catch, Take, Make, Use, Gather, Offer, Call, Invite,
      Praise, Talk, Learn, Ride, Push, Hide, Explore, Chase, Reveal, Meet, Repair,
      Fix, Wish, Dream, Care, Reward, Aid, Trust, Question, Observation, Refusal,
      Smile, Listen, Rest, Sleep, Laughter, Celebrate/Celebration, Escape, Growth,
      Arrival, Happiness, Excitement, Relief, Kindness, Pain, Anticipation,
      Acceptance, Love, Break, Fall, Catalyst, Obstacle, Threat, Sight, Failure,
      Problem, Habit, Emotion, Guidance, Transform, Bond, Advice, Adventure,
      Process/Action, Cooperation). **154 names / 165 variants → 62.5% coverage.**
- [x] **gen6k04.py** — next ~70 highest-frequency missing kernels, sampled from
      the dataset then implemented (reusing the gen6k03 `transitive`/`intransitive`/
      `emotion` factories + a batch of bespoke variants): Careful, Travel,
      Invitation, Outcome, Wait, Dialogue, PlayTogether, Need, Retrieve, Game,
      Hit, Wear, Create, Hurt, Intervention, Confidence, Reunion, Noise, Memory,
      Result, Explain, Accept, Enter, Remember, Touch, Assist, Safety, Carry,
      Collaboration, Support, Seek, Compassion, Forget, Dance, Buy, Read, Place,
      Permission, Release, Continue, Healing, Value, Trip, Forgiveness, Pull,
      Collect, Bake, Cut, Magic, Practice, Knock, Sit, Explanation, Sing, Taste,
      Denial, Hold, Refuse, Learning, Pretend, Change, Not, Reassure, Recovery,
      Appreciation, Follow, Mix, Protect, Consequence, Stuck. Object-first calls
      (`Travel(zoo)`, `Wear(dress)`) fall back to `ctx.actor`; phase kwargs route
      to `meta_story`; `Outcome`/`Result`/`Consequence` wrap child Traces.
      **224 names / 236 variants → 70.9% coverage; 99.9% end-to-end execution.**
- [x] **gen6k05.py** — next ~90 highest-frequency missing kernels, sampled then
      implemented (reusing the gen6k03 factories + bespoke variants): Reach, Grab,
      Bite, Avoid, Feed, Purchase, Capture, Paint, Kick, Approach, Drive, Check,
      Tell, Put, Lift, Count, Move, Add, Dig, Fill, Remove, Scare, Receive,
      Answer, Choose, Stop, Reject, Grant, Write, Hear, Enjoy, Heal, Respect,
      Leave, Thanks, Bonding, Reassurance, Caution, Theft, Recall, Claim,
      Understanding, Inquiry (transitive); Grow, Agree, Swim, Slip (intransitive);
      Warm, Calm, Contentment, Hunger, Guilt, Grief, Upset, Safe, Victory
      (emotion); Broken (event); plus bespoke Go, Sharing/Shared, Exploration,
      Creation, Home, Illness, Choice, Task, Reaction, Knowledge, Continuation,
      Goal, Danger, Crisis, Disruption, Temptation, Disobedience, Missing, New,
      Mess, Attached/Attachment, Death, Injury, Flight, Farewell, Picnic,
      Unexpected, Cooperate. Object-first calls fall back to `ctx.actor`; phase
      kwargs route to `meta_story`; child-Trace args (Cooperate/Reaction/Task/
      Continuation/Unexpected/Sharing) render as their own sentences.
      **311 names / 323 variants → 77.4% coverage; 99.9% end-to-end execution.**
      Continue porting the long tail toward gen5's 85%. Next by usage: Care
      variants, Reward, Sight refinements, plus richer kwargs handling.
- [x] **gen6k07.py** — coverage push toward the explicit 90% target. Sampled the
      highest-frequency missing kernels in batches (first with `sample.py`, then
      compact AST call sampling over `data00`) and added a generic but
      meta-aware pack for everyday actions, emotions, states, structural wrappers,
      and story primitives. Representative names: If, Water, Meal, Persistence,
      ParkVisit, Ignore, Greeting, Competition, Unlock, Agreement, Feel, Steal,
      Warn, Cheer, Win; plus the long-tail batches from Neglect through
      JoyfulDay, Examine through Quarrel, and Lose through Misunderstanding.
      The pass is intentionally coverage-oriented: it greatly reduces generic
      fallback usage, updates meme magnitudes where obvious, and routes phase
      kwargs to `meta_story`, but some smoke-test prose remains rough and should
      be followed by a quality pass. **Measured:** `772` names / `802` variants,
      **90.1% coverage**, **29,706** high-coverage stories, **99.9%**
      end-to-end execution OK.
- [x] **gen6k08.py** — coverage push toward the explicit 92% target. Sampled the
      next missing tranche (`Flood`, `Lie`, `HelpRequest`, `Avoidance`, plus the
      previously sampled long-tail batch) and added tolerant state/action/meta
      wrappers that preserve phase kwargs through `meta_story` and update obvious
      meme magnitudes. Includes specific wording for common problem/event shapes
      such as floods, lies, and requests for help, plus small punctuation cleanup
      for meta wrappers. This is still coverage-oriented: it reduces fallback
      volume, but the next quality pass should inspect the added generic wrappers
      for overly bland prose. **Measured:** `1044` names / `1078` variants,
      **92.5% coverage**, **35,355** high-coverage stories, **99.9%**
      end-to-end execution OK.
- [x] **gen6k09.py / data01 pass** — coverage push for `data01` specifically.
      Baseline was **90.5%** on `TinyStories_kernels/data01.kernels.jsonl`; after
      sampling the highest-frequency missing data01 kernels (`Show`, `Lost`,
      `Harmony`, `Roll`, `Empathy`, `Party`, `Playground`, etc.) and adding a
      focused state/action/meta pack, data01 reached **92.9% coverage** with
      **40,213** high-coverage stories and **100.0%** execution OK. The same pack
      also lifts the default data00 snapshot to **93.0% coverage**, **40,631**
      high-coverage stories, **99.9%** execution OK. Quality follow-up included
      routing rich `Lesson(..., catalyst=..., process=..., outcome=...)` calls
      through `meta_story` in `gen6k06.py` and preventing `Discovery(object=Trace)`
      from splicing child sentences into noun slots in `gen6k01.py`. Remaining
      data01 missing kernels are now low-frequency (top missing usage ~54), so
      next gains should be selected by story quality defects rather than raw
      coverage alone.
- [x] **gen6k03 design note**: real calls capitalize objects (`Break(Vase)`,
      `Build(Stack, block)`), so capitalized undefined names arrive as concept
      *strings*, not `Physical` entities. `gen6k03` kernels take untyped `*args`
      and branch on `isinstance(x, Entity) and x.kind == "character"`; coherence
      still works because `ctx.say()` + the AST pass key off character-name args,
      not param types.
- [x] **Workflow gotcha**: running a pack standalone (`python gen6kXX.py`) only
      loads `gen6` + that pack, so sibling kernels (e.g. `Routine`/`Curiosity`
      from gen6k01) fall back to concept strings. Pack `__main__` blocks should
      `import gen6registry` first so the demo reflects the real (full) registry.
- [ ] **Decide emotional-state model**: gen5 uses 0–100 with baselines
      (Joy/Love start at 50); gen6 memes start at 0 and grow. Pick one and document.
- [ ] **Port character packs** — `legacy/char5k01.py` defines ~70 named-character
      defaults so the bare-name shorthand (`Lily()`, `Mom()`, `Spot()`) introduces
      a character with a default type + trait. gen6 has the loader hook
      (`gen6registry` auto-loads `char6kXX.py`) but **no `char6k01.py` yet**, so
      bare `Lily()` currently hits the generic fallback. Note: explicit
      `Lily(Character, girl, Curious)` already works natively (`_character_decl`),
      and character names are excluded from coverage — so this is a *readability*
      win, not a coverage win. **When porting, factor the intro sentence
      ("Once upon a time, there was a …") into one shared gen6 helper** so the
      pack and `_character_decl` stay in sync (currently the text is built inline
      in the executor). Authoring pattern documented in `AGENTS.md` → "Character
      Packs".

### F. API surface — ✅

- [x] `generate_story()` alias exposed via `gen6registry` (also `generate()` in `gen6`).

### Findings from the AGENTS.md workflow dry-run (Visit)

Ran the documented gen6 workflow end-to-end on `Visit` (3,368 usages). The
workflow itself is sound; the dry-run surfaced and fixed three engine issues:

- [x] **`*args` not supported** by the binder → fixed (section A). The dataset
      passes variable-length character lists constantly.
- [x] **`past_tense` doubling bug** (`visitted`, `lessonned`) → fixed (section D).
- [x] **Fallback dropped trailing characters** → fixed (section A).
- [x] **`AGENTS.md`** updated: "sample-first" is now a hard rule, and the gen6
      template documents the `*args` variable-arity pattern.
- [ ] **Open quality nit**: 3-character all-character calls like
      `Visit(Lily, Mom, Friend)` are ambiguous (who visits whom) and currently
      go through the fallback. Acceptable; revisit if it shows up often.

### Story-quality evaluation harness (`QUALITY.md` + `quality.py`)

Coverage/execution say nothing about whether a story *reads* well, so added an
**agent-as-judge** quality eval (synthesis-time; no runtime LLM). `QUALITY.md`
defines the rubric (6 dims × 1-5, `usable` bool, controlled `defects` tags) and
procedure; `quality.py --sample` writes a deterministic gradeable JSONL worksheet
of (original, kernel, generated) triples, `--report` aggregates means + usable
rate + quality-by-coverage-tier + a defect-frequency table. Sharded JSONL → runs
across many parallel agents.

**Baseline (24 stories, `data00`, seed 42, graded once):** overall **2.17/5**,
**0/24 usable**; by coverage tier full **2.67** > high **2.38** > partial
**1.92**. Top defects: `literal_concept` (19), `clause_in_noun_slot` (9),
`missing_kernel_fallback` (7), `verbed_noun` (6). Takeaways: (1) the 74% usage /
99.9% execution numbers massively overstate readiness — most stories are only
*partially* covered and degrade; (2) even fully-covered stories average 2.67
(listy, "There was X" concept dumps), so the **generator** needs work, not just
coverage; (3) the defect table is the prioritized backlog for the next passes:
- [ ] **`literal_concept` (#1)**: bare concepts / unimplemented names rendered as
      "There was X." Improve `_combine` / fallback to drop or better-template
      lone concepts; implement the high-frequency abstract-noun kernels.
- [x] **`clause_in_noun_slot` (#2)** — DONE (generator defect pass). Added
      clause-reduction helpers to `gen6.py` (`base_phrase`, `infinitive_phrase`,
      `gerund_phrase`, `clause_inline`, `_present_base`/`_gerund`, copula
      exclusion) and wired them: `Want`/`Desire` → "wanted to climb the tree"
      (un-reducible clauses fall back to the generic wish), `Realize`/`Insight`
      → "realized that help was on the way", `Lesson` → "a lesson about warning
      everyone" with multi-clause traces emitted as their own sentences, and
      `Attempt` → "tried to flap" (was "tried to flapped"). Also added
      plural-agreement in `_combine` ("There were dolls"). Defect count on the
      seed-42 worksheet dropped **9 → 4**; overall **2.17 → 2.29**, grammar
      2.54 → 2.71, coherence 2.58 → 2.71, usable 0% → 4%. After-run committed at
      `quality_runs/run_after_pass.jsonl`.
- [ ] **`literal_concept` (#1, now the top defect ~20)**: bare concepts /
      unimplemented names still render as "There was X." Next pass: smarter
      `_combine`/fallback (article for countable singulars, drop empty filler) +
      implement the high-frequency abstract-noun/onomatopoeia kernels.
- [ ] **`verbed_noun` remainder (~6)**: `Altruism`/`Response`/`Remind`/`Belong`/
      `Brave`-as-`braveried` etc. still hit fallback — extend the gen6k06
      tolerant pass / add the kernels.
- [ ] Re-run the **same seed** after each pass and diff the report (must not
      regress); baseline at `quality_runs/run_baseline.jsonl`.

### World-model dev pass: object memory + relationship state (`gen6.py`)

Made the engine *read* accumulated world state that was previously only written,
so prose reflects what already happened (AGENTS.md "Prefer the world model").

- [x] **Object memory → state-aware references.** New `World.thing_phrase(obj)`
      renders an object from accumulated state: its **owner** becomes a
      possessive pronoun and its **status** (`lost`/`missing`/`broken`, already
      set by `Loss`/`Vanish`) becomes an adjective. New `World.set_owner` records
      possession. The core world-model kernels now use them, so a Loss→Search→
      Find chain reads as a coherent arc:
      *"Lily lost **her ball** and felt sad. She looked everywhere for **her lost
      ball**. She finally found **her ball again**."* (was: "lost the ball … the
      ball … found the ball"). Ownership flows forward (`Find`→`Give`:
      "found the key. She gave **her key** to Mom"). Fresh discoveries stay
      "the treasure" (render-before-own), and `Find`/`FindAt` append "again" when
      reclaiming a lost/missing item. Wired into `Loss`, `Search`, `Find`,
      `FindAt`, `Return`, `Give`, `See`.
- [x] **Symmetric relationships.** `Friendship` now records the link/Love on
      *both* characters (mutual), and being thanked (`Gratitude`) gives the
      receiver a Joy bump — so relationship-aware readers see the bond from
      either side.
- [x] **Richer `HappyEnd`.** Reads more of the arc: reunited + befriended →
      "together again, the best of friends"; befriended → best friends;
      overcame fear (Brave while Fearful) → "braver than ever"; net-sad →
      "though it had been hard…".

Validated on 669 real `Loss`/`Find`/`Search`/`Return` stories: state-aware
possessives/adjectives fire naturally ("her lost eraser", "their lost ball")
with **0** article artifacts; coverage/execution unchanged (77.4% / 99.9%);
canonical no-context shapes still render "the ball".

### Quality pass #2: tolerant variants for strict builtins (`gen6k06.py`)

Generated ~2,000 fully-covered stories, tallied the worst recurring surface
patterns, and traced each to its root cause: the strict single-signature
builtins in `gen6.py` (`Joy(char)`, `Loss(owner, obj)`, `Warning(a, b)`,
`Help(a, b)`, `Friendship(a, b)`, `Routine(char)`, …) failed to bind on the
messy real shapes and fell through to `fallback_text`, which **verbed the kernel
name** ("routined", "warninged", "joyed", "lossed", "lessoned", "friendshiped")
or emitted the generic "Something help happened" line.

Fix (idiomatic gen6 — multiple typed variants, keep `gen6.py` lean): added a
**tolerant `*args`/`**kw` variant** for each high-frequency offender in a new
quality-pass pack `gen6k06.py`. The dispatcher still prefers the precise typed
builtin when it fits (it binds more args / registers earlier), so canonical
calls are byte-for-byte unchanged; the tolerant variants only catch what used to
degrade. Names covered: Joy, Loss, Warning, Lesson, Friendship, Help, Hug,
Share, Give, Search, Return, Brave, Conflict, Routine.

Measured over ~2,000 fully-covered stories (before → after):
`routined` 246→0, `friendshiped` 70→0, `joyed` 68→0, `lessoned` 50→0,
`lossed` 37→0, `warninged` 37→0; "Something {help/share/search/brave/return/hug}
happened" ~150→~0. Coverage/execution unchanged (77.4% / 99.9%); the top `-ed`
token list is now all genuine verbs.

Also in this pass:
- [x] **Engine `_looks_nounish`** broadened with a curated abstract-noun set
      (`joy`, `grief`, `pride`, `relief`, …; common noun/verb words like `help`,
      `play`, `care` deliberately excluded) so *unknown* abstract kernels degrade
      to "X felt <noun>" instead of being past-tensed.
- [x] **`gen6k03.Obstacle`**: nested action Traces (`Obstacle(ball, stuck(tree))`)
      are now emitted as their own sentence instead of being spliced as a clause
      into "{} stood in the way" ("But the ball and There was the tree stood…"
      → "But the ball stood in the way. There was the tree.").

### Quality pass #3: embed-or-zero concept pass + sampled aliases

Moved gen6 a step closer to the `story.py` memeplex model: bare concepts in a
narrative `+` chain now bind to the current physical carrier (`ctx.actor` /
`ctx.current_object`) as meme magnitudes, and only concepts with a readable
physical manifestation are narrated. This removes accidental platonic events
like "There was clap" / "There was bravery"; unrenderable concepts still affect
state but have zero surface weight.

Engine / shared infrastructure:
- [x] **Embed-or-zero in `_combine` + fallback.** `_combine(world, left, right)`
      now has access to world state, so non-narration concepts can be embedded
      into the current carrier or dropped instead of emitted as "There was X."
      Concept-only fallback uses the same path.
- [x] **State-vs-action concept guard.** `_looks_like_state` keeps "felt X" for
      abstract states (`indifference`, `bravery`, `altruism`, `satisfaction`,
      suffix nouns) but prevents action-like concepts (`HelpOthers`) from
      surfacing as "felt help others."
- [x] **Neutral-pronoun agreement repair.** Final rendering rewrites common
      `they was/is/has` artifacts to `they were/are/have`, fixing coherence-pass
      rewrites such as "They were satisfied with the melon."
- [x] **`Moral` clause reduction.** `Moral(Altruism)` now reduces a Trace topic
      to a gerund phrase ("showing kindness by helping others") instead of
      splicing a full clause into a noun slot.

Sampled kernels added to `gen6k06.py`:
- [x] `Clap`, `HappyEnding`, `Indifference`, `Satisfaction`, `Reminder`,
      `Altruism`, `Bravery` — chosen after sampling real dataset usage with
      `sample.py -k ... --show-source`. They update memes and render from
      accumulated world state where possible.

Spot checks:
- `data00:1032`: `Listen(radio) + Laugh + Clap` now reads "Sue listened
      carefully. Sue laughed and laughed. Sue clapped happily." instead of
      leaking "There was clap."
- `data00:25989`: `Bravery(Jazz, Fin)` and `HappyEnding` are implemented; the
      ending reads "they were very brave" / "they were braver than ever before"
      instead of `braveried` / `felt happy ending`.
- `data00:1474`: `Altruism(Lily, ...)` renders a multi-phase helping story, and
      missing `HelpOthers` embeds silently instead of "There was helpothers" or
      "felt help others."

Measured:
- `check_duplicates.py`: clean (318 kernel names / 344 variants).
- `coverage.py --brief --execute 3000`: **77.6%** coverage, **12,034**
      high-coverage stories, **99.9%** execution OK (was 77.4% / 11,794 before
      this pass).

### Quality pass #4: focus prebinding + recurring ending kernels

Ran the same seed-42 24-story worksheet and patched the highest-signal recurring
surface defects still visible after pass #3: verbed ending kernels
(`dailied play`, `goodbyed`, `belonginged`, `responsed`), missing gratitude
fallback (`Something thank happened`), bad compound-action desires, and wrong
actor focus in structural calls with `protagonists=` / `participants=`.

Engine / shared infrastructure:
- [x] **Character declaration type splitting.** `Character, child + Brave +
      Playful` now declares a `child` with `Brave`/`Playful` traits instead of a
      generic `person`; `Character, Happy + BeachLoving` still becomes a person
      with traits when no known type is present.
- [x] **Keyword focus prebinding.** Calls with structural focus kwargs
      (`actor`, `hero`, `protagonists`, `participants`, …) now prebind
      `ctx.actor` before kwargs execute, so nested phase kernels no longer run
      under the last declared character by accident. The same logic now handles
      first positional character compositions like `Lily + Max`.
- [x] **List infinitive reduction.** `Longing([Climb(tree), Win])` now renders
      "wanted to climb the tree and win" instead of "wanted Lily climbed the
      tree and win."

Sampled kernels / tolerant variants:
- [x] `DailyPlay` / `PlayAllDay`: "Sue and Tim played with the radio every day"
      instead of `dailied play`.
- [x] `Goodbye` / `Farewell`: "Tim said goodbye" instead of `goodbyed`.
- [x] `Belonging`: "Tim felt at home with the armchair" instead of
      `belonginged`.
- [x] `Thank`: bare or one-arg gratitude now uses the current actor ("Man gave
      thanks") instead of `Something thank happened`.
- [x] `Response`: positional action traces are emitted as response sentences
      instead of falling through to `responsed`.
- [x] `Run`: object-first motion (`Run(inside)`) now reads "ran inside."
- [x] `Turn`: common turn-taking/object-turn shapes now render ("Tim and Sue
      took turns sitting down in the armchair", "Tom turned the ball").
- [x] `Visit`: one-character visits no longer bind the same character as both
      visitor and target ("Sue went to visit Sue" → "Sue went to visit").

Seed-42 worksheet heuristic counts (before → after this pass):
`dailied|goodbyed|belonginged|responsed|...` **4→0**,
`Something X happened` **2→1**, bad `wanted Name verbed` clause **1→0**,
duplicate compound-name artifact **1→0**. Literal `There was ...` count stayed
flat (**15→15**), so the next pass should keep attacking literal concept/object
fallbacks and missing structural kernels.

Measured:
- `check_duplicates.py`: clean (323 kernel names / 353 variants).
- `coverage.py --brief --execute 3000`: **77.8%** coverage, **12,181**
      high-coverage stories, **99.9%** execution OK.

### Quality pass #5: target-like focus + state/challenge/fetch kernels

Continued the TODO quality pass from the next highest-frequency missing kernels,
following the AGENTS sample-first workflow on `State`, `Challenge`, `Fetch`,
`Join`, and `Reflection`. The fixes keep moving toward the memeplex model:
states and reflections embed into the current carrier as meme magnitudes, while
challenge/fetch/join update carrier state instead of falling through to generic
events.

Engine / focus model:
- [x] **Target-like one-arg focus guard.** The executor still prebinds normal
      actor calls like `Walk(Sally)`, but no longer steals focus for target-like
      one-arg calls (`Help(Owner)`, `Visit(Friend)`, `Join(Tom)`, `Thank(Friend)`,
      `Goodbye(Friend)`, `Farewell(Friend)`). This fixes phase-context stories
      where `Journey(Max, state=Routine(job=Help(Owner)), catalyst=Challenge)`
      accidentally moved the whole arc onto `Owner`, and where `Visit(Friend)`
      inside Lily's journey made Friend the protagonist.
- [x] **One-arg `Visit` target shape.** `Visit(Friend)` now uses the current
      protagonist as the visitor when one is already active, while top-level
      `Visit(Lily)` still reads as Lily going to visit.

Sampled kernels / tolerant variants:
- [x] `State`: `State(Jack, Sad+Tired)` and `State(animals, mood=sad)` now render
      states instead of `stated`; state words are normalized so lower-case state
      concepts do not surface as physical objects (`the sad`).
- [x] `Challenge`: bare and shaped challenges now render as a real obstacle
      (`Max faced a challenge`) and bump `Challenge`/`Brave`.
- [x] `Fetch`: object-first and item-kwarg forms (`Fetch(Sally, item=water)`,
      `Fetch(water, source=river)`) now narrate useful action instead of
      `Something fetch happened`.
- [x] `Join`: common group/object forms now render (`Sally joined dance party`)
      while bare `Join` remains phrase-like enough for invitation/condition
      contexts.
- [x] `Reflection`: reflection beats now read from the current protagonist and
      add `Wisdom`/`Reflection`.
- [x] `Help(action=...)`: preserves nested action traces such as fetch/wrap
      instead of collapsing to a one-line "helped out."

Spot checks:
- `data00:613`: `Visit(Friend)` and `Reflection(Gratitude)` now stay with Lily:
      "Lily went to visit Friend ... Lily thought carefully..."
- `data00:4150`: `Challenge` now stays with Max instead of Owner.
- `data00:4136`: `State(animals, mood=sad)` now reads "The animals were sad."
      and `Fetch` is implemented.

Measured:
- `check_duplicates.py`: clean (328 kernel names / 358 variants).
- `coverage.py --brief --execute 3000`: **78.1%** coverage, **12,484**
      high-coverage stories, **99.9%** execution OK.
- Seed-42 worksheet regenerated at `/private/tmp/storyweavers_todo_pass5.jsonl`;
      quick heuristics show prior wrong-target focus hits **3→0** and generic
      `Something X happened` hits **1→0** on the 24-record worksheet. Remaining
      visible defects include missing structural kernels (`Condition`, `Effect`,
      `Resume`) and clause/list junk from `Reaction(...)`.

### Quality pass #6: coverage-pack focus, carrier types, and fallback cleanup

After `gen6k07.py` pushed coverage past 90%, audited a deterministic covered
worksheet plus 1,000 sampled fully-covered stories. The pass targeted recurring
surface defects introduced or exposed by the broad coverage pack:

- [x] **Keyword-focus repair in `gen6k07.py`.** The generic action/state/meta
      factories now honor explicit focus kwargs (`initiator`, `asker`, `speaker`,
      `participants`, `helper`, etc.) instead of falling back to the last
      declared character. Example: `Trade(initiator=Timmy, request=car)` now
      renders from Timmy, not the previously declared friend.
- [x] **Narration Trace cleanup in target slots.** Coverage-pack `_concepts`
      no longer splices child sentences into noun phrases, avoiding artifacts
      like "the church and the floor" when a child action should stand alone.
- [x] **Dangling-preposition cleanup.** Generic state templates now drop empty
      optional tails (`with .`, `about .`, `for .`, `to .`). In the 1,000-story
      sample these counted **>0 → 0** for the tracked patterns.
- [x] **Sampled tolerant kernels:** `Clean`, `Start`, `Trash`, `Wind`, `Wave`,
      and tolerant `Proud`/`Pride`. These remove common `Something start/wind/
      wave happened`, `Mom prided Lily`, and trash/cleanup flattening.
- [x] **Moral grammar.** `Moral(HelpOthers)` now reads "to help others" instead
      of "to helped others."
- [x] **More physical carrier types.** Added sampled character types such as
      `bunny`, `cow`, `butterfly`, `dolphin`, `octopus`, `whale`, `group`,
      `leader`, `youth`, and `fisherman`, reducing intros like
      "cow proud person" and keeping the physical level visible.

Measured:
- `check_duplicates.py`: clean (`776` kernel names / `809` variants).
- `coverage.py --brief --execute 3000`: **90.1%** coverage, **30,032**
      high-coverage stories, **99.9%** execution OK.
- 1,000 fully-covered sample heuristic scan: `with/about/for/to .`, `prided`,
      `winded`, and `waveed` all **0**. Remaining visible defects include long-tail
      fallbacks (`Something observe happened`, `Something ice day happened`),
      rough structural prose (`was as good as new` from generic restoration), and
      deeper clause/subject issues (`played Dog and the ball`, `came across Dog`).

### Quality pass #7: richer structural phases and participant-aware play

Continued from the quality-gap list after the 90% coverage pass. Generated a
fresh deterministic covered worksheet (`/private/tmp/storyweavers_quality_pass7.jsonl`,
60 stories, seed 43) and targeted recurring problems where rich ASTs collapsed
to one-line summaries.

- [x] **Broader `meta_story` phase aliases.** The shared phase renderer now
      recognizes real dataset keys such as `event`, `warning`, `condition`,
      `help`, `find`, `rest`, `solution`, `exclusion`, `loss`, `twist`,
      `reaction`, `reward`, `continuation`, and `climax`. Goals now use
      `infinitive_phrase` so action goals read better.
- [x] **Structural kernels keep more content.** `Cautionary` and `Rescue` now
      route rich kwarg calls through `meta_story`, so calls like
      `Cautionary(... warning=..., loss=..., help=..., transformation=...)` and
      `Rescue(... trigger=..., conflict=..., solution=..., result=...)` no
      longer collapse to only "learned a lesson" / "saved the day."
- [x] **Participant-aware structures.** `Cooperation(participants=[...])` now
      uses the participant list as the subject and renders the phase body.
      `Play` gained a tolerant participant/composite-subject variant, fixing
      fragments like a story ending in just "Tim and Pigeon"; game traces such
      as `Play(HideSeek, participants=[Cat, Dog])` become group play.
- [x] **Small grammar repairs.** `Warning(Mom, Careful)` now warns everyone to
      be careful instead of treating "Mom was very careful" as the listener;
      `Attempt(Tim, fly)` reads "tried to fly"; `Success(fly)` reads "It worked
      at last"; `Return(home)` avoids "returned the home to Lily" when the actor
      is returning home.
- [x] **Event catalysts read less fallback-y.** Bare event concepts in catalyst
      slots now render as appearances ("the sunset appeared", "the unicorn
      appeared") instead of "something sunset/unicorn happened."

Measured:
- `check_duplicates.py`: clean (`776` kernel names / `810` variants).
- `coverage.py --brief --execute 3000`: **90.1%** coverage, **30,032**
      high-coverage stories, **99.9%** execution OK.
- 1,000 fully-covered sample heuristic scan: warning-careful and
      `played with hide and seek` patterns are **0**; dangling prepositions remain
      **0** from pass #6. Remaining visible defects include `There was the X and
      the Y` object-list prose, long-tail fallbacks (`Something observe
      happened`), strict-return edge cases, and physical phrases that should be
      action clauses (`try to tie shoes` still sometimes appears as
      `try to the tie shoes`).

### Quality pass #8: world-model/coherence cleanup after 93% coverage

Reviewed three deterministic batches of fully-covered stories (`data00` seeds
101/202 and `data01` seed 303) and fixed recurring generator defects rather than
adding broad coverage-only kernels.

- [x] **Trace targets stay out of noun slots.** `gen6k03` generic transitive
      kernels and `Problem` now split child `Trace` sentences from object
      phrases; bespoke `Disruption`, `Travel`, and `Satisfaction` got the same
      treatment. This fixes patterns like "problem with There was...", "made
      There was...", "traveled to X was...", and "Wind blew disrupted".
- [x] **Physical carrier phrasing.** Added a small `physical_phrase` path in
      `gen6.py` for bare physical/location/body-part nouns (`inside`, `home`,
      `eyes`, etc.), and added kernel-level idioms for `Cover(eyes)` and
      `Enter(inside)`.
- [x] **Possessive coherence.** The central `coherent()` pass now converts
      repeated possessive subjects with the correct possessive pronoun
      (`Buzz's goal` -> `Their goal`) instead of subject-pronoun junk
      (`They's goal`).
- [x] **Lowercase concept wrappers.** Added lowercase `balance`, `balanced`, and
      `lesson` helpers so moral/insight expressions such as
      `lesson(balance(activity))` reduce into readable clauses.
- [x] **Tolerant child-action ideas and reflections.** `Idea(Tim,
      Transform(...) + Fix(...))` now preserves the child actions after "had a
      clever idea"; `Reflection(...)` reduces state traces to phrases instead of
      embedding full sentences in "thought about ...".
- [x] **Reaction cleanup.** `Reaction(..., emotion=..., action=...)` now emits
      child emotion/action sentences or reduced emotion/action text instead of
      "reacted with angry".

Measured:
- `check_duplicates.py`: clean (`1164` kernel names / `1199` variants).
- `coverage.py --brief --execute 3000`: **93.0%** coverage, **40,631**
      high-coverage stories, **99.9%** execution OK.
- `coverage.py --brief --execute 3000 -d TinyStories_kernels/data01.kernels.jsonl`:
      **92.9%** coverage, **40,213** high-coverage stories, **100.0%** execution
      OK.
- Remaining visible defects in the reviewed batches: some wrong-subject choices
      inside deeply nested child traces (`Dad` reaction children can still drift
      to `They`), object-construction fragments from lowercase physical builders
      (`hook(stick, string)`), and broader story completeness gaps from missing
      named characters/types.

### Quality pass: meta-kernel coherence + rewrites/world model

Sampled fully-covered stories (≥5 kernels, all implemented) and fixed the
recurring quality bugs. Coverage/execution unchanged (62.5% / 99.9%) but
narrative quality is markedly higher (e.g. `data00:15817` went from a single
"Lily offered some guidance." to a full multi-phase story).

Engine / shared infrastructure (`gen6.py`):
- [x] **Centralised meta-phase rendering** (`render_state/action/event/outcome/
      clause`, `child_sentences`, `meta_story`, `is_meta_call`). Phase children
      that are narration Traces are now emitted as their *own* sentences instead
      of being string-spliced into "X was {…}" — kills the double-subject bug
      ("Leopard was Leopard really wanted…") and dropped fragments.
- [x] **World-model pronoun pass** (`coherent`): consecutive hero sentences
      collapse the repeated name to a pronoun ("Sam shared… He played…"),
      honouring the AST coherence `_use_pronoun` flag for the first mention.
- [x] **`_combine` fixes**: bare concepts in `+` chains become their own
      sentence ("There was indifference.") and concept-composition Traces are
      tagged `Concept` so they're never mistaken for narration ("…the flowers
      Frog realized…" bug).
- [x] **Bare-name kernels execute in arg/kwarg position** (`catalyst=Threat`
      now narrates instead of degrading to the literal "threat").
- [x] **Binder tolerates stray kwargs** (drop with `_DROP_KWARG_PENALTY`
      instead of failing) → fixed fallback verbing like "Tom gratituded" for
      `Gratitude(Tom, for=…)`.
- [x] **Nounish fallback**: abstract names (`Warmth`, `FamilySupport`,
      `Confidence`) render as "X felt warmth" not "X warmthed".
- [x] **camelCase object names** split ("the newPlace" → "the new place").
- [x] **Removed duplicate `_traits`** (the second def shadowed the richer first,
      breaking `Hat(leather)` → "leather hat" trait rendering).
- [x] **Adjacent duplicate sentences collapsed** in `narrate` (stutter from two
      kernels rendering the same line).

Kernel improvements:
- [x] Dual-use kernels are now meta-aware: gen6k03 factories + `Guidance`,
      `Adventure`, `Process`/`Action`, `Cooperation` route phase-kwarg calls to
      `meta_story`; gen6k01 `Quest/Journey`, `Cautionary`, `Conflict`,
      `Resolution`, `Friendship`, `Accident` use the shared helpers.
- [x] `Play/See/Find/Search/Surprise` take an `Actor` (protagonist fallback) so
      object-first calls inside process chains read well; `Surprise(char, obj)`
      and bare `Play(char)` variants added.

Rewrites / world model (answering "can we improve with rewrites/world model?"):
- [x] **World model already subsumes some rewrites**: `Fear(C,dog)+Brave(C)`
      yields "Even though X was afraid, X was brave" purely from accumulated
      `Fear`; the `coherent` pronoun pass is world-model-driven.
- [x] **World-model-aware ending**: `HappyEnd`/`HappilyEverAfter` reads
      accumulated Joy/Love vs Sadness/Fear and Friendship links to pick among
      "best of friends" / "turned out all right" / "lived happily".
- [x] **New DEFAULT_RULES**: witch→Mysterious enrichment; `Loss+Sadness`→bind
      sadness to the loser (alongside existing strict-mother and Warning+Anger).

Known remaining limitations (long tail; documented, not yet fixed):
- [ ] **Trace in a noun slot**: simple kernels that interpolate `to_phrase(x)`
      where `x` is an action Trace embed a full clause ("wanted Nemo explored the
      coral", "about Bird was very kind"). Needs past→infinitive/gerund
      reduction; affects Desire/Want, Moral, Reward, Insight/Realize, Attempt.
- [ ] **Unimplemented kernels in `+` chains** still fall back ("There was
      picnic.", "There was happy ever after."); shrinks as the library grows.
- [ ] **Stale pinned tests**: `story_tests/data00_{14193,3216,83}.txt` were
      pinned during gen5 development (gen5-style prose) and fail under gen6.
      Re-pin once gen6 quality on those specific stories is deemed good.

---

## Tooling & Docs Migration to gen6 (then retire gen5)

### Code / tooling

- [x] **`gen6registry.py`** — auto-discovers and loads `gen6kXX.py` / `char6kXX.py`
      packs into the shared `REGISTRY`; exposes `generate_story`,
      `get_kernel_count`, `get_variant_count`, `list_kernels`, `list_loaded_packs`.
- [x] **`coverage.py`** — runs on gen6 only (the `--engine gen5` branch was
      removed when gen5 moved to `legacy/`); `--execute N` end-to-end success
      metric. gen6 `REGISTRY.kernels` (name → `list[Variant]`) works with the
      existing membership checks; `__contains__` added to the Registry.
- [x] **`sample.py`** — imports gen6 only (gen5 engine switch removed);
      `--show-source` handles multi-variant kernels; suggestion template uses the
      gen6 typed style.
- [x] **`check_duplicates.py`** — rewritten for gen6 semantics: flags a duplicate
      only when two variants of the same name share an *identical parameter-type
      signature* (intended multi-variant kernels are fine). Runs clean
      (154 names / 166 variants).
- [ ] **`story_tests.py` / `story_tests/`** — repoint the pinned-story harness at
      gen6 and regenerate golden files (gen6 output differs).

### Docs / agent guidance

- [x] **`AGENTS.md`** — gen6 is now the only documented engine: typed-variant
      authoring, `Actor` doer, `@REGISTRY.addition`, `ctx.say`, the sample-first
      rule, the `*args` variable-arity pattern, a **Character Packs** section
      (`char6kXX.py`), the World-Model & Rewrites quality pass, pinning, coverage,
      and philosophy. The legacy gen5 half was removed (kept only as a `legacy/`
      pointer).
- [x] **`README.md`** — gen6 is the primary engine throughout (pipeline diagram,
      architecture, data structures, helper/Usage examples); gen5 rows replaced
      by a `legacy/` entry; `--engine gen5` references removed.

### Decommission gen5 — ✅ DONE

- [x] gen5 family moved to `legacy/`: `gen5.py`, `gen5kXX.py`, `gen5registry.py`,
      `char5k01.py`, `remove_duplicates.py`, and the older `gen*.py` / `gen.py`.
      (`wrld5.py` / `rewr5.py` remain at top level as standalone prototypes.)
- [x] Tooling de-gen5'd: `coverage.py`, `sample.py`, `check_duplicates.py` import
      gen6 only; README/AGENTS no longer reference gen5 as an engine option.
- [ ] **Follow-up:** kernel-name coverage is still below gen5's old ~85% (gen6 is
      at 62.5%) — keep porting the long tail (section E) so nothing is lost by the
      retirement.

---

## Current Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Kernel String  │────▶│  KernelExecutor  │────▶│  StoryFragment  │
│  (Python AST)   │     │   _eval_node()   │     │  text + weight  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                         │
                    ┌──────────┼──────────┐              │
                    ▼          ▼          ▼              ▼
              ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐
              │ REGISTRY │ │ Context │ │ Template │ │ render()│
              │ kernels  │ │ chars   │ │ Engine   │ │ → text  │
              └──────────┘ └─────────┘ └──────────┘ └─────────┘
```

### Architectural Strengths (What's Working)

1. **Clean AST-based execution**: Kernels are valid Python, parsed once, executed compositionally
2. **Centralized state**: `StoryContext` holds all mutable state (characters, focus, objects)
3. **Separation of concerns**: Kernels produce `StoryFragment`, templates handle surface text
4. **Character emotions**: Already tracked (`Joy`, `Fear`, `Love`, `Anger`, `Sadness`)
5. **Extensible registry**: New kernels added via `@REGISTRY.kernel()` decorator

### Architectural Gaps (What's Missing)

| Gap | Current State | IF Systems Have |
|-----|---------------|-----------------|
| **Story Phase** | None | Ink weaves, Twine passages |
| **Location** | `current_object` only | Inform 7 rooms, TADS scope |
| **Transitions** | Hardcoded "But then," | Ink glue, smart connectors |
| **Pronoun tracking** | Names repeated | Inform 7 auto-pronouns |
| **Scene structure** | Single paragraph | Twine passages, breaks |
| **Template variety** | 1-2 per kernel | Should be 5+ |
| **Emotion → text** | Emotions tracked but unused | ChoiceScript state-modified text |

### Fundamental Problem: Direct Interpretation

The current architecture directly interprets the AST, which means each kernel must independently handle:
- Pronoun decisions (can't see other references)
- Transition insertion (can't see story structure)
- Prerequisite checking (can't see what came before)
- Coherence (logic scattered across 800+ kernels)

---

## Declarative Rewrite Rules (AST → AST in Kernel Syntax)

**Key insight**: Instead of writing Python code for AST transforms, define rewrite rules using the same kernel syntax. The engine matches patterns and applies replacements.

### Rule Definition Syntax

```python
# Rewrite rules expressed AS kernels
REWRITE_RULES = [
    # Rule: Brave after Fear → inject _after context
    Rewrite(
        pattern_src = "Fear(__C, __OBJ) + Brave(__C)",
        output_src  = "Fear(__C, __OBJ) + Brave(__C, _after='fear')",
    ),
    
    # Rule: Same character twice → use pronoun (concrete example)
    Rewrite(
        pattern_src = "Brave(__C) + Happy(__C)",
        output_src  = "Brave(__C) + Happy(__C, _use_pronoun=True)",
    ),
    
    # Rule: Transition on phase change
    Rewrite(
        pattern_src = "Fear(__C, __OBJ)",
        output_src  = "Fear(__C, __OBJ, _transition='But one day, ')",
        when_src    = "PhaseIs('setup')",
        effect_src  = "SetPhase('rising')",
    ),
    
    # Rule: Resolution after Conflict → add connector
    Rewrite(
        pattern_src = "Story(conflict=__C, resolution=__R)",
        output_src  = "Story(conflict=__C, resolution=Sequence(_transition='In the end, ') + __R)",
    ),
]
```

### How It Works

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│ Kernel AST  │───▶│ Rule Matcher│───▶│ Transformed │───▶│ Execute  │
│ (raw input) │    │ (patterns)  │    │    AST      │    │  → Text  │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────┘
                         │
                   ┌─────┴─────┐
                   │ REWRITE   │
                   │ RULES     │
                   │ (kernels) │
                   └───────────┘
```

### Pattern Variables

| Variable | Matches | Example |
|----------|---------|---------|
| `__C` | Any subtree (metavariable) | `Tim`, `Lily`, `Kids(...)` |
| `__OBJ` | Any subtree | `dog`, `ball`, `Fear(monster)` |
| `__X` | Any subtree (metavariable) | any consistent binding |

**Note:** `rewr5.py` currently treats all `__` metavariables as *bindings* (no special wildcard, no “kernel-name metavariable”, no kwargs-rest capture yet).

### Example: Pronoun Resolution Rule

```python
# Input story:
Story(
    protagonist=Tim(Character, Curious),
    conflict=Fear(Tim, dog),
    resolution=Brave(Tim)
)

# Example rule (prototype-friendly, concrete kernels):
#   Brave(__C) + Happy(__C) → Brave(__C) + Happy(__C, _use_pronoun=True)

# Output (after all rules):
Story(
    protagonist=Tim(Character, Curious),
    conflict=Fear(Tim, dog, _transition='But one day, '),
    resolution=Brave(Tim, _use_pronoun=True, _after='fear')
)
```

### Implementation

```python
import ast
from dataclasses import dataclass

@dataclass
class RewriteRule:
    pattern: str      # Kernel pattern string
    output: str       # Replacement pattern string
    when: str = ""    # Optional condition (Python expression)
    effect: str = ""  # Optional side effect (Python statement)

class PatternMatcher:
    """Match AST patterns and extract bindings."""
    
    def match(self, pattern_ast: ast.AST, target_ast: ast.AST) -> dict | None:
        """Try to match pattern against target, return bindings or None."""
        bindings = {}
        
        match (pattern_ast, target_ast):
            # Variable binding: $name matches any Name
            case (ast.Name(id=var), ast.Name(id=value)) if var.startswith('$'):
                bindings[var] = value
                return bindings
            
            # Kernel call: Kernel($args) matches Call with same func
            case (ast.Call(func=ast.Name(id=p_name), args=p_args, keywords=p_kw),
                  ast.Call(func=ast.Name(id=t_name), args=t_args, keywords=t_kw)):
                
                # Pattern variable for kernel name
                if p_name.startswith('$'):
                    bindings[p_name] = t_name
                elif p_name != t_name:
                    return None  # Names don't match
                
                # Match args
                if len(p_args) != len(t_args):
                    return None
                for p_arg, t_arg in zip(p_args, t_args):
                    sub = self.match(p_arg, t_arg)
                    if sub is None:
                        return None
                    bindings.update(sub)
                
                # Handle **kwargs capture
                for kw in p_kw:
                    if kw.arg and kw.arg.startswith('**'):
                        # Capture all target kwargs
                        bindings[kw.arg] = t_kw
                
                return bindings
            
            # Composition: A + B matches BinOp
            case (ast.BinOp(op=ast.Add(), left=p_left, right=p_right),
                  ast.BinOp(op=ast.Add(), left=t_left, right=t_right)):
                left_bindings = self.match(p_left, t_left)
                right_bindings = self.match(p_right, t_right)
                if left_bindings is None or right_bindings is None:
                    return None
                bindings.update(left_bindings)
                bindings.update(right_bindings)
                return bindings
            
            case _:
                return None
    
    def substitute(self, template_ast: ast.AST, bindings: dict) -> ast.AST:
        """Substitute bindings into template AST."""
        match template_ast:
            case ast.Name(id=var) if var.startswith('$') and var in bindings:
                return ast.Name(id=bindings[var], ctx=ast.Load())
            
            case ast.Call(func=func, args=args, keywords=kws):
                new_func = self.substitute(func, bindings)
                new_args = [self.substitute(a, bindings) for a in args]
                new_kws = []
                for kw in kws:
                    if kw.arg and kw.arg.startswith('**') and kw.arg in bindings:
                        # Expand captured kwargs
                        new_kws.extend(bindings[kw.arg])
                    else:
                        new_kws.append(ast.keyword(
                            arg=kw.arg,
                            value=self.substitute(kw.value, bindings)
                        ))
                return ast.Call(func=new_func, args=new_args, keywords=new_kws)
            
            case ast.BinOp(op=op, left=left, right=right):
                return ast.BinOp(
                    op=op,
                    left=self.substitute(left, bindings),
                    right=self.substitute(right, bindings)
                )
            
            case _:
                return template_ast


class RuleEngine:
    """Apply rewrite rules to story AST."""
    
    def __init__(self, rules: list[RewriteRule]):
        self.rules = rules
        self.matcher = PatternMatcher()
        self.state = {'phase': 'setup', 'last_subject': None}
    
    def apply_rules(self, source: str) -> str:
        """Apply all rules until fixed point."""
        tree = ast.parse(source, mode='eval')
        
        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                pattern = ast.parse(rule.pattern, mode='eval').body
                new_tree, did_change = self._apply_rule(tree, pattern, rule)
                if did_change:
                    tree = new_tree
                    changed = True
        
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    
    def _apply_rule(self, tree, pattern, rule) -> tuple[ast.AST, bool]:
        """Apply single rule to tree, return (new_tree, changed)."""
        # ... recursive application logic
        pass
```

### Why This Is Powerful

1. **Rules in domain language** - Same syntax as stories, no Python needed
2. **Composable** - Rules can be combined, ordered, grouped
3. **Inspectable** - Can print rules, reason about them
4. **Agent-generatable** - Agent can write rules, not just kernel code
5. **Optimizable** - Can compile rules to efficient matcher

### Rule Categories

```python
# Pronoun rules
PRONOUN_RULES = [
    Rewrite(
        # Prototype-friendly, concrete example:
        #   Brave(__C) + Happy(__C) → Brave(__C) + Happy(__C, _use_pronoun=True)
        pattern_src = "Brave(__C) + Happy(__C)",
        output_src  = "Brave(__C) + Happy(__C, _use_pronoun=True)",
    ),
]

# Transition rules  
TRANSITION_RULES = [
    Rewrite(
        pattern_src = "Fear(__C, __OBJ)",
        output_src  = "Fear(__C, __OBJ, _transition='But one day, ')",
        when_src    = "PhaseIs('setup')",
        effect_src  = "SetPhase('rising')",
    ),
    Rewrite(
        pattern_src = "Happy(__C)",
        output_src  = "Happy(__C, _transition='In the end, ')",
        when_src    = "PhaseIs('climax')",
        effect_src  = "SetPhase('resolution')",
    ),
]

# Prerequisite rules
PREREQ_RULES = [
    Rewrite(
        pattern_src = "Fear(__C, __OBJ) + Brave(__C)",
        output_src  = "Fear(__C, __OBJ) + Brave(__C, _after='fear')",
    ),
    Rewrite(
        # (future) additional examples can go here once kwargs matching is more flexible
        pattern_src = "Conflict(__C1, __C2) + Forgiveness(__C1, to=__C2)",
        output_src  = "Conflict(__C1, __C2) + Forgiveness(__C1, to=__C2, _after='conflict')",
    ),
]

# All rules
ALL_RULES = PRONOUN_RULES + TRANSITION_RULES + PREREQ_RULES
```

### Testing Rules

```bash
# Test a specific rule (prototype: rewr5.py)
python - <<'PY'
from rewr5 import Rewrite, rewrite_source

rules = [
    Rewrite(
        pattern_src="Fear(__C, __OBJ) + Brave(__C)",
        output_src="Fear(__C, __OBJ) + Brave(__C, _after='fear', _use_pronoun=True)",
    )
]

src = "Fear(Tim, dog) + Brave(Tim)"
print(rewrite_source(src, rules))
PY
# Output: Fear(Tim, dog) + Brave(Tim, _after='fear', _use_pronoun=True)
```

### Comparison

| Approach | Pros | Cons |
|----------|------|------|
| **Python AST Transformer** | Full power, debuggable | Verbose, requires Python knowledge |
| **Declarative Rules** | Concise, domain language | Less flexible, new syntax to learn |
| **Both** | Best of both worlds | More complexity |

**Recommendation**: Start with declarative rules for common patterns (pronouns, transitions, prerequisites). Fall back to Python transformer for complex cases.

---

## Simplified Approach: AST → AST Transforms (Python)

This section is now **superseded** by the declarative rewrite prototype in `rewr5.py`.

**Implemented (done):**
- Declarative `Rewrite(pattern_src=..., output_src=...)` rules in `rewr5.py`
- Metavariables with `__` prefix (e.g. `__C`, `__OBJ`)
- `+` chain flattening so rules can match inside `A + B + C` sequences
- Minimal guard/effect DSL: `PhaseIs(...)`, `SetPhase(...)`

**Remaining TODOs (not done yet):**
- More flexible keyword matching/capture (e.g. kwargs “rest” capture)
- Better matching policies (priorities, non-overlap, multi-match per pass)
- Wire rewrite pass into story generation (`gen5registry.generate_story`) behind a flag

### Kernels Use Injected Kwargs

Kernels check for the injected `_` prefixed kwargs using match/case for clean handling:

```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    char = _get_character(args, ctx)
    
    # Extract injected hints with defaults
    use_pronoun = kwargs.get('_use_pronoun', False)
    transition = kwargs.get('_transition', '')
    after = kwargs.get('_after', '')  # e.g., 'fear' from Fear kernel
    
    # Choose subject reference
    subject = char.he if use_pronoun else char.name
    
    # Build text based on context using match/case
    match (after, use_pronoun):
        case (str(emotion), True) if emotion:
            # After emotion + pronoun: "Despite his fear, he was brave"
            text = f"Despite {char.pronoun_his} {emotion}, {subject} was brave."
        case (str(emotion), False) if emotion:
            # After emotion + name: "Despite his fear, Tim was brave"  
            text = f"Despite {char.pronoun_his} {emotion}, {subject} was brave."
        case (_, True):
            # Just pronoun: "He was brave"
            text = f"{subject.capitalize()} was brave."
        case _:
            # Default: "Tim was brave"
            text = f"{subject} was brave."
    
    # Prepend transition if present
    if transition:
        text = f"{transition}{text[0].lower()}{text[1:]}" if not text[0].isupper() else f"{transition}{text}"
    
    return StoryFragment(text)


# Even cleaner: helper for common pattern
def apply_hints(char: Character, kwargs: dict) -> tuple[str, str, str]:
    """Extract common AST-injected hints."""
    use_pronoun = kwargs.get('_use_pronoun', False)
    subject = char.he if use_pronoun else char.name
    transition = kwargs.get('_transition', '')
    after = kwargs.get('_after', '')
    return subject, transition, after


@REGISTRY.kernel("Happy")
def kernel_happy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    char = _get_character(args, ctx)
    subject, transition, after = apply_hints(char, kwargs)
    
    match after:
        case 'fear' | 'scared':
            text = f"{subject} felt relieved and happy."
        case 'sad' | 'loss':
            text = f"{subject} finally felt happy again."
        case _:
            text = f"{subject} was very happy."
    
    return StoryFragment(f"{transition}{text}" if transition else text)
```

### Example Transform

**Input:**
```python
Story(
    protagonist=Tim(Character, Curious),
    conflict=Fear(Tim, dog),
    resolution=Brave(Tim)
)
```

**After rewrite rules applied (prototype: `rewr5.py`):**
```python
Story(
    protagonist=Tim(Character, Curious),
    conflict=Fear(Tim, dog, _transition='But one day, '),
    resolution=Brave(Tim, _use_pronoun=True, _transition='Then, ', _after='fear')
)
```

**Generated text:**
```
Tim was curious. But one day, Tim was scared of the dog. Then, despite his fear, he was brave.
```

vs. current output:
```
Tim was curious. Tim was scared of the dog. Tim was brave.
```

### Advantages Over Full IR

| Aspect | AST → AST | Full IR |
|--------|-----------|---------|
| **Implementation** | ~100 lines | ~500+ lines |
| **Testing** | Can print transformed AST | Need IR pretty-printer |
| **Compatibility** | Works with existing executor | Needs new executor |
| **Incremental** | Add one pass at a time | All-or-nothing |
| **Debugging** | `ast.unparse()` to see result | Custom tooling needed |

### Limitations

- Less structured than full IR (still just AST nodes)
- Passes can't easily share state (need to re-walk)
- Complex multi-kernel patterns harder to express
- No typed schema for annotations

### When to Graduate to Full IR

Upgrade to full IR when:
1. AST transforms get too complex (>5 passes)
2. Need rich inter-kernel relationships
3. Want to serialize/cache the IR
4. Need constraint validation before execution

### Implementation Path

1. **Create a rewrite ruleset** (`list[Rewrite]`) in “kernel algebra” syntax (use `__C`, `__OBJ` metavariables)
2. **Apply rewrites pre-execution** (call `rewrite_source(...)` before evaluation)
3. **Add core rules**: pronouns, transitions, prerequisites (start small, iterate)
4. **Update key kernels** (optional): consume injected `_` kwargs for better text
5. **Test with `sample.py`** and compare before/after

---

## MLIR-Style Compiler Pipeline (Full IR Approach)

Instead of direct interpretation, adopt a **compiler pipeline** with intermediate representation (IR) and optimization passes:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│ Kernel AST  │───▶│   StoryIR   │───▶│ Optimization│───▶│  Annotated  │───▶│  Execute │
│ (raw input) │    │ (structured)│    │   Passes    │    │     IR      │    │  → Text  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └──────────┘
                          │                  │
                   ┌──────┴──────┐    ┌──────┴──────┐
                   │ Flatten     │    │ Pronouns    │
                   │ Scope chars │    │ Transitions │
                   │ Track locs  │    │ Prerequisites│
                   └─────────────┘    │ Coherence   │
                                      └─────────────┘
```

### Why This Is Better

| Concern | Current (Interpreter) | Proposed (Compiler) |
|---------|----------------------|---------------------|
| **Pronouns** | Each kernel checks `ctx.fragments[-1]` | Pronoun pass sees ALL refs, decides globally |
| **Transitions** | Kernels hardcode "But then" | Transition pass sees structure, inserts smartly |
| **Prerequisites** | Nothing enforces Fear→Brave | Prerequisite pass annotates `Brave(despite=Fear)` |
| **Coherence** | Logic in 800 kernels | Centralized in optimization passes |

### Proposed IR: StoryIR

```python
@dataclass
class StoryIR:
    """Intermediate representation of a story, before text generation."""
    
    # Extracted from AST parsing
    characters: Dict[str, CharacterIR]    # All characters with traits, emotions
    scenes: List[SceneIR]                  # Story broken into scenes/beats
    locations: List[str]                   # Settings mentioned
    
    # Added by optimization passes
    pronoun_map: Dict[int, str]           # sentence_idx → "he"/"she"/"they"/name
    transitions: Dict[int, str]            # scene_idx → "But then,"
    prerequisites_satisfied: bool          # Constraint check passed
    
@dataclass
class SceneIR:
    """A scene/beat in the story."""
    phase: str                            # setup, rising, climax, falling, resolution
    kernels: List[KernelIR]               # Kernels in this scene
    location: Optional[str]
    mood: str = "neutral"
    
@dataclass
class KernelIR:
    """A single kernel call, annotated."""
    name: str                             # "Brave", "Fear", etc.
    args: List[Any]                       # Positional args
    kwargs: Dict[str, Any]                # Keyword args
    
    # Added by passes
    subject_ref: str = ""                 # "Tim" or "he" or "the boy"
    emotion_modifier: str = ""            # "nervously", "despite fear"
    transition_before: str = ""           # "But then, "
    prerequisite_context: List[str] = field(default_factory=list)  # ["Fear"] for Brave
```

### Optimization Passes (Python 3.10+ with match/case)

#### Pass 1: Lower AST → StoryIR

```python
import ast
from dataclasses import dataclass, field

# Location and emotion kernel sets for classification
LOCATION_KERNELS = {'Park', 'Beach', 'Forest', 'Home', 'School', 'Garden', 'Kitchen'}
EMOTION_KERNELS = {'Fear', 'Joy', 'Sadness', 'Anger', 'Happy', 'Scared', 'Brave'}
META_PATTERNS = {'Story', 'Journey', 'Cautionary', 'Quest', 'Adventure'}


def lower_to_ir(ast_node: ast.AST) -> StoryIR:
    """Convert raw Python AST to structured StoryIR using match/case."""
    ir = StoryIR(characters={}, scenes=[], locations=[])
    current_scene = SceneIR(phase="setup", kernels=[], location=None)
    
    def walk(node: ast.AST) -> None:
        nonlocal current_scene
        
        match node:
            # Character definition: Tim(Character, Curious, ...)
            case ast.Call(func=ast.Name(id=char_name), args=[ast.Name(id='Character'), *traits]):
                trait_names = [t.id for t in traits if isinstance(t, ast.Name)]
                ir.characters[char_name] = CharacterIR(name=char_name, traits=trait_names)
            
            # Location kernel: Park(), Beach(), etc.
            case ast.Call(func=ast.Name(id=loc)) if loc in LOCATION_KERNELS:
                ir.locations.append(loc.lower())
                current_scene.location = loc.lower()
            
            # Meta-pattern with kwargs: Story(protagonist=..., conflict=..., resolution=...)
            case ast.Call(func=ast.Name(id=meta), keywords=kwargs) if meta in META_PATTERNS:
                for kw in kwargs:
                    match kw.arg:
                        case 'protagonist' | 'setup':
                            current_scene = SceneIR(phase="setup", kernels=[], location=None)
                            walk(kw.value)
                            ir.scenes.append(current_scene)
                        case 'conflict' | 'catalyst':
                            current_scene = SceneIR(phase="rising", kernels=[], location=None)
                            walk(kw.value)
                            ir.scenes.append(current_scene)
                        case 'climax':
                            current_scene = SceneIR(phase="climax", kernels=[], location=None)
                            walk(kw.value)
                            ir.scenes.append(current_scene)
                        case 'resolution' | 'transformation':
                            current_scene = SceneIR(phase="resolution", kernels=[], location=None)
                            walk(kw.value)
                            ir.scenes.append(current_scene)
                        case _:
                            walk(kw.value)
            
            # Regular kernel call: Fear(Tim, dog), Brave(Tim), etc.
            case ast.Call(func=ast.Name(id=kernel_name), args=args, keywords=kwargs):
                kernel_ir = KernelIR(
                    name=kernel_name,
                    args=[extract_arg(a) for a in args],
                    kwargs={k.arg: extract_arg(k.value) for k in kwargs if k.arg}
                )
                current_scene.kernels.append(kernel_ir)
            
            # Composition: left + right
            case ast.BinOp(op=ast.Add(), left=left, right=right):
                walk(left)
                walk(right)
            
            # Recurse into other nodes
            case ast.Expression(body=body):
                walk(body)
            
            case _:
                for child in ast.iter_child_nodes(node):
                    walk(child)
    
    walk(ast_node)
    
    # Add any remaining scene
    if current_scene.kernels and current_scene not in ir.scenes:
        ir.scenes.append(current_scene)
    
    return ir


def extract_arg(node: ast.AST) -> str | None:
    """Extract argument value from AST node."""
    match node:
        case ast.Name(id=name):
            return name
        case ast.Constant(value=val):
            return val
        case _:
            return None
```

#### Pass 2: Prerequisite Check & Annotation

```python
PREREQUISITES = {
    'Brave': ['Fear', 'Danger', 'Scared'],
    'Rescue': ['Danger', 'Accident', 'Fall', 'Trapped'],
    'Forgiveness': ['Conflict', 'Apology', 'Anger'],
    'Celebration': ['Victory', 'Achievement'],
    'Relief': ['Fear', 'Danger', 'Worry'],
    'Happy': ['Sad', 'Loss', 'Fear'],
}

def prerequisite_pass(ir: StoryIR) -> StoryIR:
    """Check prerequisites, annotate kernels with context using match/case."""
    seen_kernels: set[str] = set()
    
    for scene in ir.scenes:
        for kernel in scene.kernels:
            # Check if this kernel has prerequisites
            match kernel.name:
                case name if name in PREREQUISITES:
                    prereqs = PREREQUISITES[name]
                    matched = [p for p in prereqs if p in seen_kernels]
                    if matched:
                        kernel.prerequisite_context = matched
                        # Generate appropriate modifier based on context
                        match (name, matched[0]):
                            case ('Brave', 'Fear' | 'Scared'):
                                kernel.emotion_modifier = "despite the fear"
                            case ('Brave', 'Danger'):
                                kernel.emotion_modifier = "facing the danger"
                            case ('Happy', 'Sad' | 'Loss'):
                                kernel.emotion_modifier = "finally"
                            case ('Relief', _):
                                kernel.emotion_modifier = "with relief"
                            case _:
                                kernel.emotion_modifier = f"after the {matched[0].lower()}"
            
            seen_kernels.add(kernel.name)
    
    return ir
```

#### Pass 3: Pronoun Resolution

```python
def pronoun_pass(ir: StoryIR) -> StoryIR:
    """Globally resolve when to use names vs pronouns using match/case."""
    last_subject: str | None = None
    sentences_since_name: int = 0
    
    for scene in ir.scenes:
        for kernel in scene.kernels:
            # Get first arg if it's a character reference
            first_arg = kernel.args[0] if kernel.args else None
            
            match first_arg:
                # Character name that was just mentioned → use pronoun
                case str(char_name) if char_name == last_subject and sentences_since_name < 2:
                    char_ir = ir.characters.get(char_name)
                    kernel.subject_ref = char_ir.pronoun if char_ir else "they"
                    sentences_since_name += 1
                
                # Character name, different or needs refresh → use name
                case str(char_name) if char_name in ir.characters:
                    kernel.subject_ref = char_name
                    last_subject = char_name
                    sentences_since_name = 1
                
                # Not a character reference
                case _:
                    pass
        
        # Reset pronoun tracking at scene boundary for clarity
        last_subject = None
        sentences_since_name = 0
    
    return ir
```

#### Pass 4: Transition Insertion

```python
import random

PHASE_TRANSITIONS = {
    ('setup', 'rising'): ["One day, ", "But then, ", "Suddenly, ", "It happened that "],
    ('rising', 'climax'): ["The moment came. ", "It was then that ", "Just then, "],
    ('climax', 'resolution'): ["After that, ", "Finally, ", "In the end, ", "And so, "],
}

def transition_pass(ir: StoryIR) -> StoryIR:
    """Insert transitions between scenes/phases using match/case."""
    prev_phase: str | None = None
    
    for scene in ir.scenes:
        match (prev_phase, scene.phase):
            # Phase change with known transition
            case (str(old), str(new)) if old != new and (old, new) in PHASE_TRANSITIONS:
                if scene.kernels:
                    scene.kernels[0].transition_before = random.choice(
                        PHASE_TRANSITIONS[(old, new)]
                    )
            
            # Same phase or no transition defined
            case _:
                pass
        
        prev_phase = scene.phase
    
    return ir
```

### Execution After Passes

After all passes, kernels have rich annotations:

```python
# Before passes:
KernelIR(name="Brave", args=["Tim"])

# After passes:
KernelIR(
    name="Brave", 
    args=["Tim"],
    subject_ref="he",                    # Pronoun pass decided
    emotion_modifier="despite the fear", # Prerequisite pass added
    transition_before="Then, ",          # Transition pass added
    prerequisite_context=["Fear"]        # Knows what came before
)
```

Kernel execution becomes simpler with match/case:

```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx: StoryContext, kernel_ir: KernelIR) -> StoryFragment:
    """Generate 'brave' text using pre-computed IR annotations."""
    
    # All context already computed by passes!
    subject = kernel_ir.subject_ref or kernel_ir.args[0]
    
    # Use match/case for clean text generation
    match (kernel_ir.emotion_modifier, kernel_ir.transition_before):
        case (str(modifier), str(trans)) if modifier and trans:
            # Full context: "Then, despite the fear, he was brave."
            text = f"{trans}{modifier}, {subject} was brave."
        
        case (str(modifier), _) if modifier:
            # Just modifier: "Despite the fear, he was brave."
            text = f"{modifier.capitalize()}, {subject} was brave."
        
        case (_, str(trans)) if trans:
            # Just transition: "Then, he was brave."
            text = f"{trans}{subject.capitalize()} was brave."
        
        case _:
            # Plain: "He was brave."
            text = f"{subject.capitalize()} was brave."
    
    return StoryFragment(text)
```

### World Model Constraints

The IR can also enforce world-model constraints (Inform 7 style) using match/case:

```python
def constraint_pass(ir: StoryIR) -> StoryIR:
    """Validate world model constraints using match/case."""
    seen_kernels: set[str] = set()
    
    for scene in ir.scenes:
        for kernel in scene.kernels:
            match kernel.name:
                # Rescue requires danger context
                case 'Rescue' if not any(k in seen_kernels for k in ('Danger', 'Fall', 'Accident', 'Trapped')):
                    kernel.constraint_violation = "rescue_without_danger"
                    # Option: inject implicit danger
                    kernel.implicit_prereq = "Danger"
                
                # Fly requires flying creature
                case 'Fly' if kernel.args:
                    char_name = kernel.args[0]
                    char_ir = ir.characters.get(char_name)
                    if char_ir and 'flying' not in char_ir.traits:
                        # Make it metaphorical instead of literal
                        kernel.metaphorical = True
                        kernel.emotion_modifier = "felt like"
                
                # Forgiveness requires prior conflict
                case 'Forgiveness' if not any(k in seen_kernels for k in ('Conflict', 'Anger', 'Fight')):
                    kernel.constraint_violation = "forgiveness_without_conflict"
                
                case _:
                    pass
            
            seen_kernels.add(kernel.name)
    
    return ir


# The constraint-aware kernel uses the annotations:
@REGISTRY.kernel("Fly")
def kernel_fly(ctx: StoryContext, kernel_ir: KernelIR) -> StoryFragment:
    subject = kernel_ir.subject_ref or kernel_ir.args[0]
    
    match kernel_ir:
        case KernelIR(metaphorical=True):
            return StoryFragment(f"{subject} felt like flying.")
        case _:
            return StoryFragment(f"{subject} flew through the air.")
```

### Implementation Path

| Phase | Work | Impact |
|-------|------|--------|
| **1. Define StoryIR** | Dataclasses for IR | Foundation |
| **2. AST → IR lowering** | Parse existing AST into IR | No output change yet |
| **3. Pronoun pass** | First optimization | Immediate quality boost |
| **4. Transition pass** | Phase-aware connectors | Better flow |
| **5. Prerequisite pass** | Context annotations | Coherence |
| **6. Update kernels** | Use IR annotations | Simpler kernel code |

### Benefits

1. **Kernels become simpler** - just semantic → text, no context checking
2. **Coherence is centralized** - optimization passes, not 800 kernels
3. **Easy to add new passes** - pronoun improvements, style transforms
4. **Testable in isolation** - can unit test each pass
5. **Inspection** - can print IR to debug why output is wrong

### Analogy

| LLVM/MLIR | Storyweavers |
|-----------|--------------|
| Source code | Kernel AST |
| LLVM IR | StoryIR |
| Optimization passes | Pronoun, Transition, Prerequisite passes |
| Target codegen | Text generation via kernels |

---

## Architecture Improvement Roadmap

### Phase 1: StoryContext Enhancements (Foundation)

Add new fields to `StoryContext` (gen5.py line 151):

```python
@dataclass
class StoryContext:
    # Existing fields...
    characters: Dict[str, Character] = field(default_factory=dict)
    fragments: List[StoryFragment] = field(default_factory=list)
    current_focus: Optional[Character] = None
    current_object: Optional[str] = None
    
    # NEW: Phase 1 additions
    story_phase: str = "setup"                    # Priority 1
    previous_phase: str = ""                      # For transition detection
    current_location: str = ""                    # Priority 4
    location_established: bool = False
    
    # NEW: Phase 2 additions  
    last_subject: Optional[Character] = None      # Priority 5
    sentences_since_name: int = 0
    executed_kernels: Set[str] = field(default_factory=set)  # Priority 9
    
    # NEW: Phase 3 additions
    current_scene: str = ""                       # Priority 10
    scene_mood: str = "neutral"
```

### Phase 2: StoryFragment Enhancements

Add metadata to `StoryFragment` (gen5.py line 127):

```python
@dataclass 
class StoryFragment:
    text: str
    weight: float = 1.0
    kernel_name: str = ""
    
    # NEW: Text control
    glue_before: bool = False    # Priority 6: join without space
    glue_after: bool = False
    transition_type: str = "neutral"  # "cause", "contrast", "sequence", "conclusion"
    
    # NEW: Rendering hints
    starts_paragraph: bool = False    # Priority 10: scene breaks
    emotion_context: str = ""         # Priority 3: "fearful", "joyful"
```

### Phase 3: TemplateEngine Enhancements

Add phase-aware and emotion-aware templates (gen5.py line 400):

```python
class TemplateEngine:
    def __init__(self):
        self.templates: Dict[str, List[str]] = defaultdict(list)
        
        # NEW: Transition templates by phase change
        self.transitions: Dict[str, List[str]] = {
            "setup_to_rising": ["One day, ", "But then, ", "Suddenly, "],
            "rising_to_climax": ["The moment came. ", "It was then that "],
            "climax_to_resolution": ["After that, ", "Finally, ", "And so, "],
        }
        
        # NEW: Emotion-modified template categories
        # Instead of just 'joy', have 'joy_fear_high', 'joy_neutral', etc.
```

### Phase 4: KernelExecutor Enhancements

Add tracking and smart composition (gen5.py line 1991):

```python
class KernelExecutor:
    def __init__(self, registry):
        self.registry = registry
        self.ctx = StoryContext()
        
        # NEW: Tracking
        self._executed_kernels: List[str] = []
        self._phase_just_changed: bool = False
    
    def _compose(self, left, right):
        # NEW: Smart joining based on fragment types
        # Instead of always "and", use "while", "then", "but" contextually
```

### Phase 5: Helper Function Additions

Add to gen5.py after line 1793:

```python
def _emotion_adverb(char: Character) -> str:
    """Get adverb based on dominant emotion."""
    if char.Fear > 60: return "nervously"
    if char.Joy > 70: return "happily"
    if char.Sadness > 60: return "sadly"
    if char.Anger > 60: return "angrily"
    return ""

def _get_transition(old_phase: str, new_phase: str) -> str:
    """Get transition phrase for phase change."""
    key = f"{old_phase}_to_{new_phase}"
    transitions = REGISTRY.templates.transitions.get(key, [])
    return random.choice(transitions) if transitions else ""

def _smart_join(left: str, right: str, transition_type: str = "neutral") -> str:
    """Join two text fragments with appropriate connector."""
    connectors = {
        "cause": ["so ", "because of this, ", "as a result, "],
        "contrast": ["but ", "however, ", "yet "],
        "sequence": ["then ", "and then ", "next, "],
        "conclusion": ["finally, ", "in the end, ", "and so "],
        "neutral": [" ", " and ", ". "],
    }
    connector = random.choice(connectors.get(transition_type, connectors["neutral"]))
    return f"{left.rstrip('. ')}{connector}{right}"
```

---

## Feasibility Assessment

| Component | Effort | Risk | Dependencies |
|-----------|--------|------|--------------|
| `StoryContext` fields | Trivial | None | None |
| `StoryFragment` fields | Low | None | Update `_compose()` |
| `TemplateEngine` transitions | Low | None | Phase tracking |
| `KernelExecutor` tracking | Medium | Test carefully | None |
| Helper functions | Low | None | None |
| Update 800+ kernels | High (grunt work) | Low | All above |

### Recommended Implementation Order

1. **Add `StoryContext` fields** (10 min) - No breaking changes
2. **Add `_emotion_adverb()` helper** (5 min) - Immediately usable
3. **Update meta-patterns to set phase** (30 min) - `Journey`, `Cautionary`, `Quest`
4. **Add transition templates** (20 min) - Auto-insert on phase change
5. **Improve `_compose()`** (30 min) - Smarter joining logic
6. **Add template variety** (ongoing) - 5+ templates per kernel

---

## Priority 1: Story Phase Tracking
**Status:** Not started  
**Effort:** Low  
**Impact:** High  

Add phase awareness to `StoryContext` so templates and kernels know where we are in the narrative arc.

```python
@dataclass
class StoryContext:
    story_phase: str = "setup"  # setup, rising_action, climax, falling_action, resolution
    
    def advance_phase(self, new_phase: str):
        self.story_phase = new_phase
```

**Implementation notes:**
- Meta-patterns (`Journey`, `Cautionary`, `Quest`) should advance phases as they process kwargs
- Phase transitions: setup → rising_action (catalyst) → climax (conflict) → falling_action (resolution) → resolution (transformation)
- Templates can be phase-aware: "Once upon a time..." in setup vs "Finally..." in resolution

**Inspired by:** Ink's weave structure for managing narrative flow

---

## Priority 2: Transition Templates
**Status:** Not started  
**Effort:** Medium  
**Impact:** High  

Add transition phrases between story phases to fix choppy narrative flow.

```python
class TemplateEngine:
    def __init__(self):
        self.transitions = {
            "setup_to_rising": [
                "One day, ",
                "But then, ",
                "Suddenly, ",
                "It happened that ",
            ],
            "rising_to_climax": [
                "The moment had come. ",
                "It was then that ",
                "Just when things seemed okay, ",
            ],
            "climax_to_resolution": [
                "After that, ",
                "In the end, ",
                "Finally, ",
                "And so, ",
            ]
        }
```

**Implementation notes:**
- `StoryContext.emit()` could auto-insert transitions when phase changes
- Transition selection should be random for variety
- Could also have fragment-level transitions (cause, contrast, sequence, conclusion)

**Inspired by:** Twine's passage links and natural flow between story segments

---

## Priority 3: Emotion-Modified Templates
**Status:** Not started  
**Effort:** Low  
**Impact:** Medium  

Leverage existing character emotion state (Joy, Fear, Love, Anger, Sadness) to modify generated text.

```python
# In TemplateEngine
self.templates['action_joy_high'] = [
    "{name} happily {action}.",
    "{name} {action}, beaming with joy.",
]
self.templates['action_fear_high'] = [
    "{name} nervously {action}.",
    "{name} {action}, trembling slightly.",
]

# Usage in kernels:
def kernel_action(ctx, char, **kwargs):
    if char.Fear > 60:
        return ctx.templates.generate('action_fear_high', name=char.name, action="did it")
    elif char.Joy > 70:
        return ctx.templates.generate('action_joy_high', name=char.name, action="did it")
    return StoryFragment(f"{char.name} did it.")
```

**Implementation notes:**
- Define emotion thresholds (e.g., >60 = "high")
- Apply to common action kernels first (Run, Walk, See, Find)
- Could add adverb injection as simpler alternative: `"{name} {adverb} {action}."`

**Inspired by:** ChoiceScript's state-modified text output

---

## Priority 4: Location/Setting Persistence
**Status:** Not started  
**Effort:** Low  
**Impact:** Medium  

Track current location so action kernels can reference it naturally.

```python
@dataclass
class StoryContext:
    current_location: str = ""
    location_established: bool = False

# In location kernels:
@REGISTRY.kernel("Park")
def kernel_park(ctx, *args, **kwargs):
    ctx.current_location = "the park"
    ctx.location_established = True
    return StoryFragment("at the park", kernel_name="Park")

# In action kernels:
@REGISTRY.kernel("Play")
def kernel_play(ctx, *args, **kwargs):
    location_suffix = f" in {ctx.current_location}" if ctx.location_established else ""
    return StoryFragment(f"{char.name} played happily{location_suffix}.")
```

**Implementation notes:**
- Location should persist until explicitly changed
- Meta-patterns with `setting=` kwarg should set location
- Consider location-appropriate action variations (play in park vs play at home)

**Inspired by:** Inform 7's world model with automatic scope

---

## Priority 5: Pronoun Resolution
**Status:** Not started  
**Effort:** Medium  
**Impact:** Medium  

Reduce repetitive character name usage by tracking mentions and using pronouns.

```python
@dataclass
class StoryContext:
    last_subject: Character | None = None
    last_object: str | None = None
    mention_counts: dict[str, int] = field(default_factory=dict)
    sentences_since_name: int = 0
    
    def subject_reference(self, char: Character) -> str:
        """Get appropriate reference (name or pronoun) using match/case."""
        self.sentences_since_name += 1
        count = self.mention_counts.get(char.name, 0)
        
        match (self.last_subject, self.sentences_since_name, count):
            # First mention ever → use name
            case (_, _, 0):
                ref = char.name
                
            # Different character → use name
            case (last, _, _) if last != char:
                ref = char.name
                
            # Same character but too long since name → use name
            case (_, n, _) if n > 2:
                ref = char.name
                
            # Same character, recently mentioned → use pronoun
            case _:
                return char.he  # "he", "she", "they"
        
        # Update tracking when using name
        self.mention_counts[char.name] = count + 1
        self.last_subject = char
        self.sentences_since_name = 0
        return ref
    
    def object_reference(self, obj: str) -> str:
        """Get reference for objects (it/them or the object name)."""
        match (self.last_object, obj):
            case (last, current) if last == current:
                return "it"
            case _:
                self.last_object = obj
                return f"the {obj}"
```

**Implementation notes:**
- Need to be careful with multiple characters in same scene
- Reset pronoun tracking at scene/phase changes
- Consider object pronouns too (him/her/them, it)

**Inspired by:** Inform 7's automatic pronoun resolution

---

## Priority 6: Ink-style Glue & Text Control
**Status:** Not started  
**Effort:** Low  
**Impact:** Medium  

Ink uses "glue" (`<>`) to control how text fragments join. Currently fragments join with simple spaces, leading to awkward output like "Frog hop. Bird provided guidance."

```python
class StoryFragment:
    text: str
    weight: float = 1.0
    kernel_name: str = ""
    glue_before: bool = False   # NEW: join without space to previous
    glue_after: bool = False    # NEW: join without space to next
    suppress: bool = False      # NEW: generate but don't emit (side effects only)

# Usage in composition:
def _compose(self, left, right):
    if right.glue_before or left.glue_after:
        return StoryFragment(f"{left.text}{right.text}")  # No space
    # ... existing logic
```

**Current problem** (from `Journey` kernel):
- `process=hop + Guidance(Bird)` → "Frog hop. Bird provided guidance." 
- Should be: "Frog hopped along as Bird guided the way."

**Implementation notes:**
- Verbs used as concepts (`hop`) should auto-conjugate based on context
- Compound actions (`hop + Guidance`) need smarter joining: "X did A while Y did B"
- Add `StoryFragment.as_verb()` helper for present/past tense conversion

**Inspired by:** Ink's glue system (`<>`) for text control

---

## Priority 7: Conditional Text Variations (Ink Alternatives)
**Status:** Not started  
**Effort:** Medium  
**Impact:** Medium  

Ink supports inline alternatives: `{~once|twice|many times}` and conditionals `{flag: text if true}`. This could make kernels more dynamic without hardcoding.

```python
# New template syntax with alternatives
self.templates['discovery'] = [
    "{name} found {article} {object}.",
    "{name} discovered {article} {object}!",
    "{name} came across {article} {object}.",  
    "There, in front of {name}, was {article} {object}.",
]

# Conditional based on story state
self.templates['discovery_feared'] = [
    "{name} nervously approached the {object}.",
    "With trembling hands, {name} picked up the {object}.",
]

# In kernel:
def kernel_find(ctx, char, obj):
    if char.Fear > 50:
        return ctx.templates.generate('discovery_feared', name=char.name, object=obj)
    return ctx.templates.generate('discovery', name=char.name, object=obj)
```

**Current problem** (from `Basket`, `Escape` kernels):
- These kernels have smart pattern detection (methods vs threats)
- But text output is still single-template: `"{char.name} escaped from the {thing}!"`
- Missing: variations based on *how* they escaped, *how scared* they were

**Implementation notes:**
- Template selection could weight by emotion state
- Add "once only" templates for first-time events
- Consider cycling through templates to avoid repetition in longer stories

**Inspired by:** Ink's alternatives `{~a|b|c}` and sequences `{stopping: a|b|c}`

---

## Priority 8: ChoiceScript-style Fairmath for Emotions
**Status:** Not started  
**Effort:** Low  
**Impact:** Low  

ChoiceScript uses "fairmath" - bounded changes that are proportional to distance from limits. Currently emotions can overflow (Joy > 100) or underflow (Joy < 0).

```python
class Character:
    def _fairmath_adjust(self, current: float, delta: float) -> float:
        """Bounded adjustment - harder to reach extremes."""
        if delta > 0:
            # Positive change: percentage of remaining headroom
            return current + (100 - current) * (delta / 100)
        else:
            # Negative change: percentage of current value
            return current + current * (delta / 100)
    
    def adjust_joy(self, delta: float):
        self.Joy = max(0, min(100, self._fairmath_adjust(self.Joy, delta)))
```

**Current problem** (from `Happy`, `Contentment`, `Journey` kernels):
- Multiple joy boosts can stack: `char.Joy += 15` in Happy, `+8` in Contentment, `+15` in Journey insight
- A character going through a full Journey pattern ends up with Joy > 100
- No diminishing returns - 5th "happy" event feels same as 1st

**Implementation notes:**
- Keep simple `+=` syntax but clamp internally
- Consider opposing pairs: Joy vs Sadness should balance
- High emotion should decay slightly each phase (regression to mean)

**Inspired by:** ChoiceScript's fairmath system for balanced stat progression

---

## Priority 9: Inform 7-style Implicit Actions
**Status:** Not started  
**Effort:** Medium  
**Impact:** Medium  

Inform 7 automatically inserts implicit actions (opening a closed door before entering). This could help with narrative coherence.

```python
# Define action prerequisites
ACTION_PREREQUISITES = {
    'Escape': ['Fear', 'Danger', 'Trapped'],  # Should have fear/danger context
    'Rescue': ['Fear', 'Danger', 'Accident'],  # Someone must be in danger
    'Forgiveness': ['Conflict', 'Apology'],    # Must have conflict first
    'Celebration': ['Victory', 'Achievement', 'Resolution'],  # Must have won
}

# In executor, check prerequisites and inject if missing:
def _eval_call(self, node):
    # ... existing logic ...
    
    kernel_name = node.func.id
    if kernel_name in ACTION_PREREQUISITES:
        prereqs = ACTION_PREREQUISITES[kernel_name]
        if not any(p in self._executed_kernels for p in prereqs):
            # Auto-inject a minimal prerequisite
            self._inject_prerequisite(kernel_name, prereqs[0])
```

**Current problem** (from `Escape`, `Belonging` kernels):
- `Escape` is smart about methods vs threats, but doesn't ensure danger was established
- `Belonging` has catalyst/process/outcome but they're optional
- Story can have `Rescue(Mom, Lily)` without any `Danger` or `Fear` being established

**Implementation notes:**
- Track which kernels have been executed in context
- Soft prerequisites (warn but continue) vs hard (inject if missing)
- Could also suggest missing kernels in `sample.py` output

**Inspired by:** Inform 7's implicit action system and "before" rules

---

## Priority 10: Twine-style Passage/Scene Structure
**Status:** Not started  
**Effort:** Medium  
**Impact:** High  

Twine organizes stories into passages with links. This maps well to story "beats" or scenes that should have paragraph breaks and distinct moods.

```python
@dataclass
class StoryContext:
    current_scene: str = ""
    scene_fragments: List[StoryFragment] = field(default_factory=list)
    all_scenes: List[Tuple[str, List[StoryFragment]]] = field(default_factory=list)
    
    def start_scene(self, name: str, mood: str = "neutral"):
        """Begin a new scene/passage."""
        if self.scene_fragments:
            self.all_scenes.append((self.current_scene, self.scene_fragments))
        self.current_scene = name
        self.scene_fragments = []
        self.scene_mood = mood
    
    def render(self) -> str:
        """Render with paragraph breaks between scenes."""
        paragraphs = []
        for scene_name, frags in self.all_scenes:
            para = ' '.join(f.text for f in frags if f.weight > 0.3)
            paragraphs.append(para)
        # Add current scene
        if self.scene_fragments:
            paragraphs.append(' '.join(f.text for f in self.scene_fragments if f.weight > 0.3))
        return '\n\n'.join(paragraphs)
```

**Current problem:**
- All output is one continuous paragraph
- Original stories have natural paragraph breaks
- No way to mark "this is a new beat" in the narrative

**Implementation notes:**
- Meta-patterns (`Journey`, `Cautionary`) could auto-create scenes for each phase
- Scene transitions get different connectors: "Meanwhile...", "Later that day..."
- Scene mood affects template selection within that scene

**Inspired by:** Twine's passage structure and Bitsy's room-based organization

---

## Future Ideas (Lower Priority)

### Bitsy-style Minimal Evocative Output
Bitsy creates atmosphere with minimal text. Consider a "compact" mode:

```python
# Verbose (current):
"Once upon a time, there was a little boy named Tim. Tim was very curious. 
Tim found a ball. Tim was happy."

# Compact/evocative:
"Tim, curious. A ball, found. Joy."
```

Useful for: summaries, poetry mode, or dense narrative kernels.

### Kernel Preconditions & Effects Metadata
Tag kernels with preconditions and automatic state effects:

```python
@REGISTRY.kernel("Rescue", 
    requires={"target": {"Fear": ">30"}},
    effects={"target": {"Fear": -30, "Joy": +20}},
    transitions_from=["Danger", "Fall", "Accident"])
def kernel_rescue(ctx, *args, **kwargs):
    pass
```

### Fragment Transition Types
Add semantic transition hints to fragments:

```python
class StoryFragment:
    transition_type: str = "neutral"  # "cause", "contrast", "sequence", "conclusion"
```

### Scene/Beat Boundaries
Explicit scene markers for paragraph breaks and tonal shifts:

```python
ctx.start_scene("confrontation")
# ... generate conflict ...
ctx.end_scene()
ctx.start_scene("resolution")
```

### Dialogue Generation
Quoted speech for character interactions:

```python
@REGISTRY.kernel("Say")
def kernel_say(ctx, speaker, content, to=None):
    return StoryFragment(f'"{content}," said {speaker.name}.')
```

### TADS-style Action Verification
TADS verifies actions before execution. Could add narrative plausibility checks:

```python
@REGISTRY.kernel("Fly")
def kernel_fly(ctx, char, **kwargs):
    # Verify: can this character fly?
    if char.char_type not in ('bird', 'butterfly', 'fairy', 'dragon'):
        # Make it metaphorical or add context
        return StoryFragment(f"{char.name} felt like flying.")
    return StoryFragment(f"{char.name} flew through the air.")
```

### Ink-style Tunnels (Subroutine Calls)
Ink's tunnels let you call a sub-story and return. Could work for recurring patterns:

```python
# Define a reusable sub-pattern
@REGISTRY.tunnel("comfort_sequence")
def tunnel_comfort(ctx, comforter, comforted):
    """Reusable comfort pattern: approach → hug → reassure."""
    return [
        kernel_approach(ctx, comforter, comforted),
        kernel_hug(ctx, comforter, comforted),
        kernel_reassure(ctx, comforter, comforted),
    ]

# Use in kernels:
@REGISTRY.kernel("Comfort")
def kernel_comfort(ctx, *args):
    # Can either do simple version or call tunnel
    if ctx.detail_level > 2:
        return ctx.call_tunnel("comfort_sequence", *args)
    return StoryFragment(f"{args[0].name} comforted {args[1].name}.")
```

---

## Observations from Current Kernel Implementations

### What's Working Well

1. **Pattern detection in `Escape`**: Distinguishes methods (basket, window) from threats (cage, trap)
2. **Context tracking in `Basket`**: Sets `ctx.current_object` for later reference
3. **Structured patterns in `Belonging`**: catalyst/process/outcome mirrors IF story structure
4. **Character group factories in `Kids`**: `_make_character_kernel` reduces boilerplate

### What's Missing

1. **Verb conjugation**: `hop` as a process becomes "Frog hop" not "Frog hopped"
2. **Compound action joining**: `A + B` becomes "A. B." not "A while B" or "A and then B"
3. **Emotion-aware output**: High Fear doesn't affect how `Escape` is narrated
4. **Scene breaks**: No paragraph structure in output
5. **Prerequisite tracking**: Can `Rescue` without `Danger`, `Forgive` without `Conflict`
6. **Template variety**: Most kernels have 1-2 templates, should have 5+ for naturalness

---

## References

- **Ink**: https://www.inklestudios.com/ink/ - Weaves & threading for narrative flow
- **ChoiceScript**: https://www.choiceofgames.com/make-your-own-games/choicescript-intro/ - State-modified text
- **Inform 7**: http://inform7.com/ - World model, pronoun resolution, natural language
- **Twine**: https://twinery.org/ - Passage flow and transitions
- **TADS**: https://www.tads.org/ - Action preconditions and effects

---

## Implementation Order

### Phase 1: Core Narrative Flow (High Impact)
1. [ ] Story Phase Tracking (Priority 1) - Foundation for other improvements
2. [ ] Transition Templates (Priority 2) - Fix choppy narrative flow
3. [ ] Twine-style Scene Structure (Priority 10) - Paragraph breaks, mood tracking

### Phase 2: Text Quality (Medium Impact)
4. [ ] Ink-style Glue & Text Control (Priority 6) - Better fragment joining
5. [ ] Conditional Text Variations (Priority 7) - Template variety
6. [ ] Emotion-Modified Templates (Priority 3) - Use existing emotion state

### Phase 3: World Coherence (Polish)
7. [ ] Location Persistence (Priority 4) - Setting context
8. [ ] Pronoun Resolution (Priority 5) - Natural prose
9. [ ] Implicit Actions (Priority 9) - Narrative prerequisites

### Phase 4: Refinements
10. [ ] Fairmath Emotions (Priority 8) - Bounded stat changes

### Testing Each Change

```bash
# Before making changes, capture baseline
python sample.py -k Journey -n 5 --seed 42 -o > baseline_journey.txt

# After changes, compare
python sample.py -k Journey -n 5 --seed 42 -o > new_journey.txt
diff baseline_journey.txt new_journey.txt

# Pin good stories as tests
python story_tests.py --pin data00:41 --description "Journey with improved flow"
```

### Quick Wins (Can Do Now)

These require only kernel changes, no engine changes:

1. **Add template variety** - Each kernel should have 5+ templates
2. **Improve verb handling** - `_action_to_phrase()` should conjugate properly
3. **Better compound joining** - `_compose()` should use "and", "while", "then"
4. **Add emotion adverbs** - Helper function to get adverb from emotion state

```python
def _emotion_adverb(char: Character) -> str:
    """Get adverb based on dominant emotion using match/case."""
    # Find the dominant emotion
    emotions = [
        ('Fear', char.Fear),
        ('Joy', char.Joy),
        ('Sadness', char.Sadness),
        ('Anger', char.Anger),
    ]
    dominant, level = max(emotions, key=lambda x: x[1])
    
    match (dominant, level):
        case ('Fear', n) if n > 60:
            return "nervously"
        case ('Joy', n) if n > 70:
            return "happily"
        case ('Sadness', n) if n > 60:
            return "sadly"
        case ('Anger', n) if n > 60:
            return "angrily"
        case _:
            return ""  # neutral
```

---

## Context Helpers for Autonomous Kernel Optimization

**Key insight**: The language model gets compiled into kernel if-statements. At 10k kernels with sophisticated conditionals, coherence emerges from pattern-matching in kernel code, not engine smarts.

### The Agent Optimization Loop

```
1. python sample.py -k Brave -n 10 --show-source
2. See: "Tim was scared. Tim was brave." (incoherent)
3. Add if-statement to kernel_brave checking for recent Fear
4. Retest: "Tim was scared. Despite his fear, Tim was brave." (coherent)
5. Repeat
```

### StoryContext Helper Properties

Add computed properties to `StoryContext` that make pattern-matching easy for kernels:

```python
@dataclass
class StoryContext:
    # ... existing fields ...
    
    @property
    def recent_kernels(self) -> list[str]:
        """Last 5 kernel names for quick pattern matching."""
        return [f.kernel_name for f in self.fragments[-5:] if f.kernel_name]
    
    @property
    def recent_emotions(self) -> set[str]:
        """Emotion kernels from recent fragments."""
        emotion_kernels = {'Fear', 'Joy', 'Sadness', 'Anger', 'Love', 'Happy', 'Scared', 'Brave'}
        return {k for k in self.recent_kernels if k in emotion_kernels}
    
    @property  
    def mentioned_names(self) -> set[str]:
        """Character names mentioned in last fragment."""
        if not self.fragments:
            return set()
        return {c.name for c in self.characters.values() 
                if c.name in self.fragments[-1].text}
    
    @property
    def last_action(self) -> str | None:
        """Most recent action kernel name."""
        action_kernels = {'Run', 'Walk', 'Find', 'See', 'Eat', 'Play', 'Jump', 'Climb'}
        for f in reversed(self.fragments[-5:]):
            if f.kernel_name in action_kernels:
                return f.kernel_name
        return None
```

### Pattern-Matching Helpers (using match/case)

Common patterns extracted as helper functions with match/case:

```python
def analyze_context(ctx: StoryContext, char: Character) -> dict[str, any]:
    """Analyze context for a character, return hints for text generation."""
    recent = ctx.recent_kernels
    
    hints = {
        'use_pronoun': False,
        'after_emotion': None,
        'same_focus': False,
    }
    
    # Check pronoun usage
    match ctx.last_subject:
        case c if c and c.name == char.name:
            hints['use_pronoun'] = True
    
    # Check for preceding emotion
    match recent:
        case [*_, 'Fear' | 'Scared'] | ['Fear' | 'Scared', *_]:
            hints['after_emotion'] = 'fear'
        case [*_, 'Joy' | 'Happy'] | ['Joy' | 'Happy', *_]:
            hints['after_emotion'] = 'joy'
        case [*_, 'Sadness' | 'Sad'] | ['Sadness' | 'Sad', *_]:
            hints['after_emotion'] = 'sadness'
        case [*_, 'Anger' | 'Angry'] | ['Anger' | 'Angry', *_]:
            hints['after_emotion'] = 'anger'
    
    # Check focus
    match ctx.current_focus:
        case c if c and c.name == char.name:
            hints['same_focus'] = True
    
    return hints


def get_subject_ref(char: Character, hints: dict) -> str:
    """Get the right subject reference based on hints."""
    match hints:
        case {'use_pronoun': True}:
            return char.he
        case _:
            return char.name
```

### Example: Context-Aware Kernel (with match/case)

Before (incoherent):
```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx, *args, **kwargs):
    char = _get_character(args, ctx)
    return StoryFragment(f"{char.name} was brave.")
```

After (coherent, using match/case):
```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    char = _get_character(args, ctx)
    hints = analyze_context(ctx, char)
    subject = get_subject_ref(char, hints)
    
    # Use match/case for clean branching
    match hints:
        case {'after_emotion': 'fear'}:
            text = f"Despite {char.pronoun_his} fear, {subject} was brave."
        
        case {'after_emotion': 'anger'}:
            text = f"Channeling {char.pronoun_his} anger, {subject} stood brave."
        
        case {'same_focus': True, 'use_pronoun': True}:
            text = f"{subject.capitalize()} was very brave."
        
        case _:
            text = f"{subject} was brave."
    
    return StoryFragment(text)
```

### Scaling to 10k Kernels

| Kernel Count | What Gets Encoded in match/case |
|--------------|-------------------------------------|
| 800 | Basic patterns: `case {'to': recipient}` → "apologized to X" |
| 2k | Context awareness: `case {'after_emotion': 'fear'}` → "despite fear" |
| 5k | Narrative arcs: `case {'prereq': 'Conflict'}` → "resolution references conflict" |
| 10k | Style variations: `case {'sentence_length': 'long'}` → use short next |

### Implementation Priority

1. **Add `recent_kernels` property** - Trivial, immediately useful
2. **Add `analyze_context()` helper** - Returns dict for match/case
3. **Update 10 key emotion kernels** - Brave, Happy, Sad, Scared to use match/case
4. **Document patterns in kernel docstrings** - Help agent know what to match
5. **Add `--incoherent` flag to sample.py** - Find stories where patterns break

### Why This Works

Infocom's coherence came from hand-written responses. Storyweavers' coherence comes from:

1. **LLM extracts patterns** at dataset creation time
2. **Agent encodes patterns** into match/case during kernel development
3. **Runtime executes code** - no LLM needed

The more sophisticated the match/case patterns, the more coherent the output. The agent's job is to:
- Sample stories
- Identify incoherent sequences  
- Add match/case branches to handle them
- Test and iterate

**The kernels ARE the language model, just compiled into match/case patterns.**
