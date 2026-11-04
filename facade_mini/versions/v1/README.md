# The Last Place Setting

A playable, standalone miniature of a Façade-style interactive domestic drama.
You are the only guest at Mara and Eli's anniversary dinner. She has accepted a
residency away from home; he has spent their joint savings on a workshop. Neither
has told the other. The room contains physical evidence, and your interventions
can help them speak honestly, harden their positions, bring the evening to a
pause, or get you thrown out.

Original characters and dialogue. Python 3.9+ standard library only. Copy this
whole directory anywhere; it needs no Storyweavers imports, dataset, model,
network connection, or API key. Existing gen6/gen7 engines are untouched.

## Play

From the repository root:

```bash
python3 facade_mini/play.py
```

Or, from inside this directory:

```bash
python3 play.py
```

Type `help` to see moves; enter either their number or exact command. `listen`
lets the conversation continue. Try `ask letter`, `ask receipt`, `empathize mara`,
`support eli`, or `reflect mara`. Asking again may go deeper into a clue. The
interface accepts explicit discourse acts, not unrestricted natural language.
Unsupported text costs no turn and cannot accidentally be interpreted as support.

Most complete evenings take about 10–20 moves, with a 24-move deadline. `leave`
ends the evening immediately. `look` describes object state; `state` and `why`
are optional diagnostic views that expose the simulation, including spoilers.
End-of-input or Ctrl-C exits; `--trace` preserves a replayable, possibly partial
record, not an interactive save-game continuation.

## See the experiment without playing

```bash
python3 play.py --demo repair
python3 play.py --demo distrust
python3 play.py --demo space
python3 play.py --demo silent
python3 play.py --demo ejected
python3 play.py --demo leave
```

Read the saved [repair](examples/repair.txt), [distrust](examples/distrust.txt),
[night apart](examples/space.txt), and [silent](examples/silent.txt) transcripts.
The repair/distrust pair changes **only two early commands**: empathy becomes
blame. All subsequent scripted requests are identical, followed by listening.
The warm version earns responsibility-taking and a modest agreement to talk
tomorrow. In the cold version, the same requests meet distrust, the director
continues through the crisis, and the evening ends unresolved.

This demonstrates local reactions, topic steering, and a small amount of global
agency. Repair means a first step toward a conversation, not a magically cured
relationship. A night apart is an explicitly requested boundary, not a failure
score for the player.

## Architecture and historical scope

The reference is Mateas and Stern's 2005
[Structuring Content in the Façade Interactive Drama Architecture](https://ojs.aaai.org/index.php/AIIDE/article/view/18722).
It describes authored beats selected by a drama manager, coordinated dialogue
behaviors, and mix-ins that interrupt and rejoin ongoing exchanges. This prototype
adapts those structural ideas at a much smaller scale. It does not reproduce
Façade's ABL runtime, animation, voice acting, natural-language interpretation,
or real-time interruption inside spoken lines. Its units are not comparable in
size to the paper's beats or joint dialogue behaviors.

| Layer | Here |
| --- | --- |
| Physical and social world | Two hosts carry anger, fear, directed trust, accountability, and knowledge. Props carry owner, location, and state. |
| Beat library | Eight sequenced beats with 23 goals, ordered conditional performance variants, explicit effects, priority, weight, and estimated tension. |
| Director | Filters by phase, prerequisites, and unused beats; ranks by priority, topic relevance, and tension fit; seeded tie-breaking. |
| Coordinated performance | One atomic exchange of authored lines and effects per goal. Both hosts participate in the same performance. |
| Interruptions | Three clue topics, two tiers each. They pause the pending goal; a re-entry line restores context. A refusal does not consume a clue tier. |
| Social exchanges | Parameterized support, blame, empathy, and responsibility-taking; apology, mediation, and space. Weighted influence rules gate willingness. |
| Global consequences | Five terminal outcomes. Earned mediation or an accepted request for space can release an unfinished argument and change the remaining sequence. |
| Trace | Input, selected performance, before/after world state, eligible beat scores, and influence-rule contributions; deterministic replay. |

The social-exchange layer is a small design sketch in the direction suggested by
the user's mention of Comme il Faut, **not a reproduction or evaluation of that
system**. There is no general social-practice planner, cultural rulebase, or
autonomous multi-character goal search here. The drama director coordinates both
characters rather than running two independent agents.

The tension target is an author-specified phase arc (2, 4, 6, 3). Beat tension is
an author estimate, not a prediction obtained by simulating the future. Current
tension comes from the hosts' anger and fear. Mandatory phase boundaries still
constrain the possible plots; five topical beats can reorder but are not
arbitrary interchangeable stories.

### Alignment with the memeplex north star

Feelings have physical carriers: they live on Mara and Eli. Knowledge changes
when a character speaks or a paper is disclosed; public truths propagate to both
hosts and the guest. Trust and anger determine whether reflection is accepted.
The concluding image has matching prop and character effects in the trace.
There are no unembedded concept sentences or prose-based state inference.

This experiment deliberately stops short of the full model in `story.py`:
characters, concepts, and beats do not yet share one compositional algebra.
Dialogue remains authored, with selected alternatives driven by state. Keeping
it isolated makes that limitation explicit rather than quietly changing gen6.

## Authoring and inspection

- [content.py](content.py): scene, goals, variants, exchange rules, endings.
- [engine.py](engine.py): world effects, director, interruptions, input processing.
- [play.py](play.py): terminal interface and deterministic demonstration policies.
- [test_drama.py](test_drama.py): causal, interruption, knowledge, boundary, and replay checks.
- [audit.json](audit.json): generated inventory and traversal results.
- [REVIEW.md](REVIEW.md): reading notes, interpretation, and limitations.
- [TODO.md](TODO.md): next measurable experiments.

To add a topical beat, put a `Beat` in `BEATS`, give it phase `topics`, and write
its `Goal`/`Performance` sequence. The last variant must be a compatible fallback;
earlier variants carry `when` predicates. Effects use `set` or bounded `add` on
existing state paths. Register every new carrier or property in `INITIAL`.
The director discovers eligible beats from the content library automatically.
For a new interruptible clue, add ordered tiers under `MIXINS`; the command list
is generated from those entries. A topic matching a beat's `topic` gets a
selection bonus. This works without writing a separate branch for every path,
but coherent entry, exit, re-entry, and emotional variants still need authoring.

Conditions are `(path, operator, value)` tuples. Operators are `eq`, `ge`, `le`,
`gt`, and `lt`; a list of conditions is a conjunction. Ordered variants provide
alternatives. No code is evaluated from user input. A successful social exchange
has effects only once per evening; refusals and unnecessary apologies can be
retried when context changes. This intentionally coarse memory prevents point
farming but also limits genuine conversational repair after repeated harms.

## Verify and replay

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
python3 audit.py --samples 500
python3 play.py --demo repair --trace /tmp/dinner.json --inspect
python3 play.py --replay /tmp/dinner.json
python3 play.py --replay examples/repair.trace.json
```

`audit.py --samples 500 --write` regenerates the inventory, six readable example
transcripts, and one full replay record. The audit's predeclared policy selects
uniformly from supported moves plus eight extra `listen` entries, for seeds
0–499. Leaving is permitted; early exits count rather than being discarded.
Random runs test robustness, not a competent player's likely experience.

The inventory reports authored slots and unique lines separately: alternatives
and reused text do not become new stories. It excludes engine-level refusal,
resume, and command-echo scaffolding. The examples and trace are generated
artifacts, not additional hand-authored story content.

## What this says about authoring cost

This delivery shows a coding agent can produce a small executable content library,
its scheduling machinery, examples, and regression checks in one task. It has
**no measured human baseline, comparable production values, or controlled timing
study**. It therefore does not establish a cost multiplier relative to Façade,
nor does it show that 27 comparable beats would be cheap.

The remaining bottleneck is visible in the code: most dramatic meaning lives in
handwritten scene content and condition-specific alternatives. The next useful
experiment is a timed, fixed-quality extension of this library, with independent
readers checking the resulting conversations. See [TODO.md](TODO.md).
