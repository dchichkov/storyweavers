# Storyscenes v2: causal scenes, conditional prose

Write warm, lively stories for ages 5–8. Cleverness can be playful. Characters
want a party, a discovery, a daring performance, a friend, a ridiculous prize.
They are not inspectors teaching each other project management. Let a choice
change something; let the last image carry the meaning without explaining it.

The engine composes scenes over a persistent world. Shared characters and props
carry desires, beliefs and meme magnitudes. No runtime LLM. No prewritten linear
route selected by a branch number. Keep the world small enough to understand.

## Theater design

Use 2–4 characters with distinct wants, one shared setting, and a few props.
Design THREE genuinely different problems that can arise from initial physical
or social conditions. At least one should involve mistaken belief or conflicting
wants, not broken equipment or weather. Examples within a puppet theater:
someone wants the wrong part; a supposed audience turns out to be a rehearsal;
a child invents a performance for a guest who experiences it differently.
Do not use these examples unless they suit this theater. Find your own.

Let these produce different consequences and endings, not three routes to the
same delivered parcel. Seed changes should alter what is wanted, understood,
traded, made or performed. Use 3–5 interacting kernel families. Reuse at least
two scenes across materially different paths. An inciting action must establish
its problem before responses to it; bind that to a physical promise, invitation,
observed problem, or an actor's knowledge. Do not add abstract stage counters.

## Executable simulation

Return Python defining `build(seed) -> WorldSpec`. Allowed imports: random,
runtime, math, itertools, collections. All state values are scalar. All state
keys start with the ID of an existing physical entity. Declare every slot first.

```python
import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer

def build(seed):
    rng = random.Random(seed)
    entities = {'ada': {'name':'Ada','kind':'child'},
                'box': {'name':'wooden box','kind':'prop'}}
    initial = {'ada.memes.Curiosity': 2, 'ada.knows.box.open': None,
               'box.open': False, 'box.owner': 'ada'}
    scenes = (
        observe('look', 'ada', 'box.open',
                requires=(C('ada.memes.Curiosity','ge',1),),
                summary='Ada inspected the box'),
        scene('open', 'Solve', ('ada',),
              when=(C('ada.knows.box.open','eq',False),),
              set_values={'box.open':True},
              summary='Ada lifted the lid'),
    )
    return WorldSpec('Example only', entities, initial, scenes,
                     goal=(C('box.open','eq',True),),
                     rules=(), labels={'box.open':'the box lid'}, prune=True,
                     premise_keys=('box.owner',), outcome_keys=('box.open',))
```

`scene(id,kernel,actors, *, when=(), set_values=None, increments=None,
copies=None, summary='', weight=1.0, max_uses=1, pivotal=False)` creates an
immutable candidate. `set_values` maps keys to constants, `increments` maps
keys to numerical additions, `copies` maps destination keys to source keys.
Copies read PRE-state. Every effect is atomic; duplicate destination keys fail.
Use this keyword API, not positional Effect constructors.

`C(key,op,constant)` supports eq/ne/lt/le/gt/ge/in/not_in. Conditions are ANDed;
a condition value is never another state reference. `Rule(name,must,when=())`
means all must conditions hold whenever all when conditions hold. Use tuples
of Conditions, even for a single condition. Empty when means always.

`observe(id,actor,fact,requires=(),summary='')` copies fact into the declared
`actor.knows.<fact>` slot. `tell(id,speaker,listener,fact,...)` copies the
speaker's non-None belief to the listener. `transfer(id,actor,recipient,prop,...)`
requires prop.owner == actor and updates the single owner slot. Use at least one
of these shared kernels. Guard access, location, knowledge, and motives as needed.
No mind reading. Beliefs do not automatically change when the world changes.

Use 12–22 candidates and aim for 5–10 selected events. The shared planner drops
actions that contribute neither to the final outcome nor to a pivotal character
turn. Set `pivotal=True` only for 1–2 important character moments whose changed
state matters even if it is not a goal prerequisite. Prefer real dependencies.
Never mark every preparation action pivotal. Supply `prune=True`.

`premise_keys` names 2–4 actual initial properties that distinguish the problems.
`outcome_keys` names 1–3 actual final properties that distinguish consequences.
They must be declared state keys. Track concrete accomplishments, ownership,
agreements and locations. A promise to do something is not its completion.
One goal may accept several distinct outcomes (e.g. actor.content == True),
but the outcomes themselves must be physical/social facts with different meaning.

## Prose catalog

The final generator is compiled from a JSON catalog by a shared renderer. Write
complete grammatical text variants; the engine handles conditions, placeholders,
event order, grouping, RNG selection and fact references. Do not write Python
rendering logic. No hand-built enum interpolation.

Catalog fields:
- `openings`: variants establishing the actual initial desire and problem.
- `scenes`: objects with `scene` (exact simulation ID), `role` (`beat` or
  `bridge`), and `variants`. Supply EVERY candidate, including unseen preview paths.
- `endings`: variants guarded by the actual final outcome. A final image, not
  another summary of the full story. Do not claim unused props were used.
- `lexicon`: objects `{key, value, text}` defining a complete grammatical phrase
  for each dynamic state value mentioned through a phrase placeholder.

Each variant: `{text, when}`. Each condition in `when` has `key`, `op` (eq/ne/ge/le),
`value` (scalar), `at` (initial/before/after). For scenes, after means THIS event's
post-state. Before means its pre-state. For endings, after means final state.
The most specific matching variants are eligible; the prose RNG selects among
them. No matching variant is an error. Two unguarded variants can vary voice,
but assertions about a variable fact MUST be conditional or use a phrase slot.

Placeholders:
- `{name:ada}` substitutes the existing entity's display name.
- `{phrase:box.mark}` substitutes an explicit lexicon phrase for its current value.
No other braces or Python expressions. There is no raw-value fallback.
Examples: for request == 'return', map to 'wanted her button back'; for
condition == 'sound', map to 'was smooth and unbroken'. Do not write 'to be return'.

`bridge` cards should take 10–25 words and connect routine actions naturally.
Adjacent bridges are joined. `beat` cards should take 35–70 words, often with
an exchange of dialogue. A discovery must say WHAT was discovered. A character
who has not discovered a fact cannot speak as if they know it. Do not narrate
an event twice by adding its debug summary after the scene prose.

Aim for 220–400 words in a complete sample, not 600 words of repeated preparation.
Provide at least two voice variants for openings and two for each major ending.
Use silly specifics, surprise, affection, and distinctive voices, without adding
new physical events. Avoid stock explanations about evidence, responsibility,
accounting, carefulness, or proving that a constraint was satisfied. No moral
paragraph. The reader should notice the change in the final image.

Never leave alternatives in the text ('held—or did not hold', 'she said, or').
Do not narrate correct equipment as broken; do not repair it twice. Do not carry
a functioning machine's part away merely because it makes a nice ending image.

## Cheap authoring protocol (v3)

All authoring and routine repairs use Luna. Plan compactly: keep the whole plan
under 650 words and the mechanics under 200 lines. Repairs return exact source
edits or individual JSON catalog edits. Never depend on a more capable model
replacing the world later. Keep a small, inspectable set of real constraints.

The shared observe/tell/transfer kernels accept `when` as well as `requires`,
and `pivotal`/`weight`, consistently with scene(). A shared kernel must matter:
observed or told knowledge must enable a later action; gratuitous observations
will be pruned. Names of facts include their carrier: observing box.open declares
ada.knows.box.open, not ada.knows.open. A shared observation can occur before
several different decisions. No unsupported first-name variables.

Characters may speak about their own wants without inspecting themselves.
A performer actually performs before an ending can describe the performance;
a promised invitation is not a delivered invitation. Narrative prose can add
voice and harmless sensory detail, but must not invent an action to make a thin
simulation seem richer. Condition cards on variable wants, knowledge and results.
