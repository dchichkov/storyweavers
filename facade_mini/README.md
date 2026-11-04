# The Last Place Setting

An original interactive domestic drama inspired by the beat-driven architecture
of Façade. You are the only guest at Mara and Eli's anniversary dinner. A folded
letter and a receipt carry decisions neither has told the other about. You can
listen, probe, take sides, speak privately, keep or break a confidence, negotiate
practical commitments, or leave.

This is the expanded second delivery. The first small prototype is preserved in
[versions/v1/](versions/v1/README.md); development samples and failed checks are
retained in [reviews/](reviews/round2/REVIEW.md).

## Play in your browser

From the repository root:

```bash
python3 facade_mini/serve.py --open
```

Or, after copying this directory anywhere:

```bash
cd facade_mini
python3 serve.py --open
```

The server listens only on your own computer, normally at
[127.0.0.1:8765](http://127.0.0.1:8765). Choose another `--port` if that port is busy;
`--port 0` chooses a free one and prints its address. Ctrl-C stops the server.
Nothing is sent to an external service. Python 3.9+ is the only dependency.

The browser offers contextual choices, a reading view, private-room indicators,
and save/resume. Your choices have no real-time deadline: each advances the
fictional evening. An ordinary full playthrough takes about 16–30 choices, with a
48-move bound. Leaving or being asked to leave can end it sooner. “Behind the
scenes” exposes the world and director for inspection and contains spoilers.

Save an evening before stopping the server. Browser sessions live in memory;
refresh preserves them while the server is running. Exported JSON is a verified
replay record that can be loaded to continue a partial evening. Different browser
cookie sessions have separate games. The local server retains up to 32 sessions.

## Terminal and demonstrations

```bash
python3 play.py
python3 play.py --demo private
python3 play.py --demo initiative
python3 play.py --demo practical
python3 play.py --demo betrayal
python3 play.py --demo separate
```

Inside the terminal, `help` lists explicit moves. Enter a command or its number;
`listen` lets the hosts continue. `look`, `state`, and `why` inspect the simulation
without advancing it. This is an explicit-action interface, not an unrestricted
natural-language parser.

The eleven saved [example transcripts](examples/private.txt) include:

| Approach | What changes |
| --- | --- |
| [Direct mediation](examples/repair.txt) | Build enough trust for each host to own a choice, then ask for a conversation tomorrow. |
| [Character initiative](examples/initiative.txt) | Give each person room and step back; the hosts disclose, take responsibility, and propose a next step themselves. No `reflect` or `mediate` commands. |
| [Private confidences](examples/private.txt) | Hear each person alone, promise privacy, and support their own public disclosure. |
| [Practical negotiation](examples/practical.txt) | Learn the refund terms and travel schedule; get two observable commitments without demanding emotional reconciliation. No empathy or reflection commands. |
| [Betrayal](examples/betrayal.txt) | Announce a private confidence. The breach interrupts the current topic and changes the remaining arc, even after an apology. |
| [Separation](examples/separate.txt) | Help the hosts discuss separate futures after acknowledging their choices. |
| [Earlier blame](examples/distrust.txt) | Change just two early empathetic moves to blame; the same later intervention fails and a different arc follows. |

The other examples are silence, a night apart, ejection, and voluntary departure.
There are **eight ending categories**. Repair is a first step toward another
conversation, not a declaration that the relationship is cured.

## What was expanded

The loaded library has **27 sequenced beats, 80 goals, 183 performance slots,
11 public topics with 30 tiers, eight private content units, and 15 social
exchange bindings**. It includes roughly **6,000 words across unique loaded
content lines**, excluding dynamic interaction scaffolding. Inventory definitions
and exact counts are in [audit.json](audit.json).

These beats are short text scenes. They are **not comparable units of production
work to Façade's beats**. The reference paper reports about three person-years of
content authoring beyond the architecture, including dialogue and performance
specification. This prototype has no animation, voice performance, ABL runtime,
or continuous free-text interpretation. [Mateas & Stern, 2005](https://ojs.aaai.org/index.php/AIIDE/article/view/18722)

The social layer is only a small sketch in the direction suggested by Comme il
Faut: reusable exchanges, influence rules, context, and social memory. It is not a
reproduction of CiF's full rulebase or a validated model of human relationships.

## How it works

- **Physical carriers:** characters carry anger, fear, trust, knowledge, insights,
  offenses, forgiveness, and commitments; props carry owner, location, and state.
- **Audience boundaries:** only the guest and one host enter the kitchen. Public
  goals pause. Private disclosures update the guest's knowledge, not the absent
  partner's. The trace records who was present for every performance.
- **Social memory:** an apology addresses the current offense, not a generic
  once-per-evening flag. A new offense allows a new apology; repeating an apology
  for the same incident cannot accumulate trust. A breached confidence persists.
- **Character initiative:** when trust, emotional state, being heard, and an open
  conversational floor permit it, hosts can disclose and take responsibility
  without a direct instruction. Their joint proposal changes the arc.
- **Drama management:** eligible unused scenes are ranked by priority, the topic
  the guest raised, an authored tension estimate, and current emotional state.
  The arc has arrival, topics, crisis, aftermath, and closing phases. A late
  confidence breach can interrupt even the closing phase.
- **Performance:** conditional authored exchanges apply explicit effects. A joint
  exchange is atomic; interruptions happen between goals, with authored re-entry.
  Audience knowledge selects reminder variants instead of repeated revelations.
- **Consequences:** aftermath scenes enact changes—writing terms, marking dates,
  accepting help, preparing an overnight stay—before a grounded final image.

This moves toward the carrier-based model in the repository's `story.py`:
embedded state drives compatible performances; the engine never infers its state
from rendered prose. It remains a separate experiment, not a gen6/gen7 change.
Characters, concepts, and beats do not yet share the complete memeplex algebra.
There are no runtime LLMs, network calls, or Storyweavers dependencies.

## Inspect, author, and verify

| File | Responsibility |
| --- | --- |
| [content.py](content.py) | Original base scenes and exchange definitions |
| [content_ext.py](content_ext.py) | Added scenes, histories, aftermaths, topics, ending conditions, memory variants |
| [interactions.py](interactions.py) | Private performances, promises, betrayal, voluntary character actions |
| [engine.py](engine.py) | State, effect execution, selection, suspension, memory, replay |
| [play.py](play.py) | Terminal and deterministic policies |
| [serve.py](serve.py), [player.html](player.html) | Local browser player |
| [test_drama.py](test_drama.py), [test_expanded.py](test_expanded.py) | Mechanical and causal regressions, plus HTTP integration |
| [audit.py](audit.py) | Inventory, seeded traversal, knowledge/replay checks |

A `Beat` contains ordered `Goal` objects. Each goal chooses the first compatible
`Performance`; the final variant is a fallback. Effects are `set` or bounded `add`
on registered state paths. Conditions are `(path, operator, value)` conjunctions.
Add props and facts to the initial world before referencing them. Add a topic to
the mix-in library to expose a command automatically. Follow the authoring
checklist in [AUTHORING.md](AUTHORING.md).

From inside this directory:

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
python3 audit.py --samples 500 --policy broad
python3 audit.py --samples 500 --policy curious
python3 play.py --demo private --trace /tmp/evening.json
python3 play.py --replay /tmp/evening.json
python3 play.py --resume /tmp/evening.json
```

`--replay` verifies the entire saved record. `--resume` verifies it and continues
if unfinished. Changed code/content can invalidate an old record; v1 records must
be played with `versions/v1/play.py`. `audit.py --write` regenerates examples and
selected complete traces. The browser can export and load the same records.

The HTTP tests require permission to bind a loopback port. All tests run on a
normal local Python installation; an execution sandbox may require that specific
permission. There are no package installs.

## Evidence and limits

Read [REVIEW.md](REVIEW.md) for the measured results and the two reading/repair
rounds. The original failed 500-session curious audit is preserved; the final
recheck and reserved-seed checks are separate artifacts. Path counts, exact text
counts, and green tests are not counts of good stories.

This is a more substantial authored experiment than the first pass. It still
has one premise, explicit action menus, compact social rules, and some repetitive
reactions. There is no independent human quality study and no measured authoring
cost reduction. [TODO.md](TODO.md) identifies the next controlled experiment.
