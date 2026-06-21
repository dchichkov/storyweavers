#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meek_avenue_wheat_cautionary_suspense_nursery_rhyme.py

A small storyworld about a meek child on an avenue, a tempting thing on the far
side, and the dangerous wish to dart into the road before it is safe. The prose
leans toward nursery rhyme: light repetition, concrete sounds, and a clear
lesson.

Run it
------
python storyworlds/worlds/gpt-5.4/meek_avenue_wheat_cautionary_suspense_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/meek_avenue_wheat_cautionary_suspense_nursery_rhyme.py --avenue clover --lure wheat_bun
python storyworlds/worlds/gpt-5.4/meek_avenue_wheat_cautionary_suspense_nursery_rhyme.py --method tiptoe_alone
python storyworlds/worlds/gpt-5.4/meek_avenue_wheat_cautionary_suspense_nursery_rhyme.py --all --qa
python storyworlds/worlds/gpt-5.4/meek_avenue_wheat_cautionary_suspense_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Avenue:
    id: str
    label: str
    bustle: int
    sound: str
    crossing: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    phrase: str
    motion: str
    peril: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    power: int
    lead: str
    cross: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_danger(world: World) -> list[str]:
    child = world.get("child")
    avenue = world.get("avenue")
    if child.meters["in_road"] < THRESHOLD:
        return []
    sig = ("danger", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    avenue.meters["danger"] += 1
    return ["__danger__"]


def _r_rescue(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["pulled_back"] < THRESHOLD:
        return []
    sig = ("relief", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["in_road"] = 0.0
    child.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(avenue: Avenue, lure: Lure) -> bool:
    return avenue.bustle >= 1 and bool(lure.peril)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def crossing_severity(avenue: Avenue, delay: int) -> int:
    return avenue.bustle + delay


def is_safe(method: Method, avenue: Avenue, delay: int) -> bool:
    return method.power >= crossing_severity(avenue, delay)


def predict_risk(world: World, avenue: Avenue) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["in_road"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("avenue").meters["danger"],
        "fear": sim.get("child").memes["fear"],
        "sound": avenue.sound,
    }


def open_scene(world: World, child: Entity, parent: Entity, avenue: Avenue) -> None:
    child.memes["calm"] += 1
    world.say(
        f"Along {avenue.label}, where wheels went {avenue.sound}, walked {child.id}, "
        f"a meek little {child.type}, beside {child.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f"The baker's door stood open, and the air smelled warm with wheat. "
        f"{child.id} kept a careful pace, tap-tap by the stones."
    )


def spot_lure(world: World, child: Entity, lure: Lure) -> None:
    child.memes["want"] += 1
    world.say(
        f"Then {lure.phrase} {lure.motion} across the avenue. "
        f'"Oh!" said {child.id}. "There it goes, there it goes!"'
    )


def warn(world: World, child: Entity, parent: Entity, avenue: Avenue, lure: Lure) -> None:
    pred = predict_risk(world, avenue)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["caution"] += 1
    world.say(
        f'{parent.label_word.capitalize()} squeezed {child.pronoun("possessive")} hand. '
        f'"Not yet, my dear. {avenue.label} is wide, and {pred["sound"]} means carts are near. '
        f'If you hurry after {lure.label}, the road may hurry too."'
    )


def edge_forward(world: World, child: Entity) -> None:
    child.meters["at_curb"] += 1
    child.memes["tempted"] += 1
    world.say(
        f"But want went quick and caution went meek. {child.id} put one shoe to the curb, "
        f"then one toe past it."
    )


def near_miss(world: World, child: Entity, parent: Entity, avenue: Avenue) -> None:
    child.meters["in_road"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Clip-clop, rumble-bump! A cart swept by on {avenue.label}, so close that the ribbon "
        f"on {child.id}'s sleeve fluttered."
    )
    child.meters["pulled_back"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} caught {child.pronoun('object')} gently and drew "
        f"{child.pronoun('object')} back to the stones. {child.id}'s heart went thump-thump-thump."
    )


def steady(world: World, child: Entity, parent: Entity) -> None:
    child.memes["shame"] += 1
    child.memes["fear"] += 1
    world.say(
        f'"Little feet must wait for little eyes to look," said {parent.label_word}. '
        f'{child.id} nodded, small and still.'
    )


def cross(world: World, child: Entity, parent: Entity, avenue: Avenue, lure: Lure,
          method: Method) -> None:
    child.memes["trust"] += 1
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} {method.lead}. Together they {method.cross} over '
        f"{avenue.crossing}."
    )
    world.say(
        f"Soon {lure.phrase} was safe in {child.id}'s hands again. {lure.ending}"
    )


def ending(world: World, child: Entity, parent: Entity, avenue: Avenue) -> None:
    child.memes["joy"] += 1
    world.say(
        f"So down {avenue.label} they went, slow feet and bright eyes. {avenue.ending}"
    )
    world.say(
        f"And {child.id} learned this little beat: on a busy road, be meek in feet."
    )


def tell(avenue: Avenue, lure: Lure, method: Method, *, child_name: str = "Mina",
         child_gender: str = "girl", parent_type: str = "mother",
         trait: str = "gentle", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["meek", trait],
        attrs={"display_name": child_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    avenue_ent = world.add(Entity(
        id="avenue",
        kind="thing",
        type="road",
        label=avenue.label,
    ))
    lure_ent = world.add(Entity(
        id="lure",
        kind="thing",
        type="lure",
        label=lure.label,
        phrase=lure.phrase,
    ))

    open_scene(world, child, parent, avenue)
    spot_lure(world, child, lure)

    world.para()
    warn(world, child, parent, avenue, lure)
    edge_forward(world, child)

    outcome = "safe" if is_safe(method, avenue, delay) else "near_miss"
    if outcome == "near_miss":
        near_miss(world, child, parent, avenue)
        steady(world, child, parent)

    world.para()
    cross(world, child, parent, avenue, lure, method)
    ending(world, child, parent, avenue)

    world.facts.update(
        child=child,
        parent=parent,
        avenue=avenue,
        lure=lure,
        method=method,
        delay=delay,
        outcome=outcome,
        child_name=child_name,
        risk=crossing_severity(avenue, delay),
        lure_entity=lure_ent,
        avenue_entity=avenue_ent,
    )
    return world


AVENUES = {
    "clover": Avenue(
        id="clover",
        label="Clover Avenue",
        bustle=1,
        sound="clip-clop",
        crossing="the painted stripes",
        ending="The baker waved, and even the windows seemed to wink.",
        tags={"avenue", "crosswalk"},
    ),
    "market": Avenue(
        id="market",
        label="Market Avenue",
        bustle=2,
        sound="rumble-bump",
        crossing="the painted stripes beneath the lantern",
        ending="The wheat sacks by the shop stood still as sleepy sheep.",
        tags={"avenue", "traffic", "crosswalk"},
    ),
    "mill": Avenue(
        id="mill",
        label="Mill Avenue",
        bustle=3,
        sound="clatter-clang",
        crossing="the crossing where the guard raises a red hand",
        ending="Far off, the mill wheel turned, but the curb stayed calm behind them.",
        tags={"avenue", "traffic", "guard"},
    ),
}

LURES = {
    "wheat_bun": Lure(
        id="wheat_bun",
        label="the wheat bun",
        phrase="a round wheat bun",
        motion="rolled from a paper bag and spun",
        peril="bun in the road",
        ending="The bun was a bit dusty, but the lesson was bright and clean.",
        tags={"wheat", "food"},
    ),
    "straw_hat": Lure(
        id="straw_hat",
        label="the straw hat",
        phrase="a straw hat tied with yellow ribbon",
        motion="skipped in the wind like a little boat",
        peril="hat in the road",
        ending="The hat sat straight again, and its ribbon stopped trembling.",
        tags={"wheat", "hat"},
    ),
    "duckling": Lure(
        id="duckling",
        label="the duckling",
        phrase="a small duckling peeping for crumbs of wheat",
        motion="pittered after the smell of bread",
        peril="duckling in the road",
        ending="The duckling was carried back to the baker's step, peep-peep and safe.",
        tags={"duckling", "wheat"},
    ),
}

METHODS = {
    "hold_hand": Method(
        id="hold_hand",
        label="hold a grown-up hand",
        sense=3,
        power=2,
        lead="took one firm grown-up hand in one small hand and one deep breath in one small chest",
        cross="looked left, looked right, listened, and walked",
        qa_text="held a grown-up hand, looked both ways, and crossed together",
        tags={"crosswalk", "safety"},
    ),
    "crossing_guard": Method(
        id="crossing_guard",
        label="wait for the crossing guard",
        sense=3,
        power=4,
        lead="waited for the crossing guard's red hand and the quiet that comes after wheels",
        cross="walked step by step",
        qa_text="waited for the crossing guard to stop traffic and then crossed together",
        tags={"guard", "safety"},
    ),
    "tiptoe_alone": Method(
        id="tiptoe_alone",
        label="tiptoe alone",
        sense=1,
        power=1,
        lead="tried to be quieter than the wheels",
        cross="tiptoed quickly",
        qa_text="tiptoed alone into the road",
        tags={"unsafe"},
    ),
}


@dataclass
class StoryParams:
    avenue: str
    lure: str
    method: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "avenue": [(
        "What is an avenue?",
        "An avenue is a road in a town or city. People walk beside it, and carts or cars travel on it."
    )],
    "crosswalk": [(
        "What is a crosswalk for?",
        "A crosswalk is a marked place to cross the road more safely. It helps drivers see where people may walk."
    )],
    "traffic": [(
        "Why is traffic dangerous?",
        "Traffic moves fast and heavy, so feet cannot argue with wheels. That is why people stop, look, and wait before crossing."
    )],
    "guard": [(
        "What does a crossing guard do?",
        "A crossing guard helps people cross the road at the right time. The guard watches the traffic and tells everyone when it is safe."
    )],
    "wheat": [(
        "What is wheat?",
        "Wheat is a grain that people grind into flour. Bakers use that flour to make bread and buns."
    )],
    "duckling": [(
        "What is a duckling?",
        "A duckling is a baby duck. It is small and soft, and it needs careful help near roads."
    )],
    "food": [(
        "Should you run into a road to grab food?",
        "No. Food can be replaced, but a road can be dangerous in a blink. It is better to wait for help and cross safely."
    )],
    "hat": [(
        "Should you chase a hat into the road?",
        "No. A hat is not worth stepping into traffic for. A grown-up can help you wait and cross safely if it can be reached."
    )],
    "safety": [(
        "What should little feet do near a road?",
        "Little feet should stop at the curb, while little eyes look and ears listen. Crossing safely means going together at the right time."
    )],
}
KNOWLEDGE_ORDER = ["avenue", "crosswalk", "traffic", "guard", "wheat", "duckling", "food", "hat", "safety"]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Elsie", "Poppy", "Wren"]
BOY_NAMES = ["Tobin", "Milo", "Ned", "Otis", "Bram", "Hugo"]
TRAITS = ["gentle", "timid", "soft-spoken", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for avenue_id, avenue in AVENUES.items():
        for lure_id, lure in LURES.items():
            if hazard_at_risk(avenue, lure):
                combos.append((avenue_id, lure_id))
    return combos


def pair_noun(parent: Entity) -> str:
    return parent.label_word


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    avenue = f["avenue"]
    lure = f["lure"]
    outcome = f["outcome"]
    name = f["child_name"]
    base = (
        f'Write a nursery-rhyme-style cautionary story for a 3-to-5-year-old that includes '
        f'the words "meek", "avenue", and "wheat". Use {avenue.label} and {lure.label}.'
    )
    if outcome == "near_miss":
        return [
            base,
            f"Tell a suspenseful rhyme where {name}, a meek little {child.type}, almost steps into "
            f"{avenue.label} after {lure.label}, then learns to wait and cross safely.",
            f"Write a gentle cautionary story in bouncing, rhythmic prose where a child is tempted "
            f"to dash after {lure.label}, a grown-up pulls them back, and the ending shows what changed.",
        ]
    return [
        base,
        f"Tell a nursery-rhyme story where {name} wants to hurry after {lure.label}, but a grown-up "
        f"teaches safe crossing on {avenue.label}.",
        f"Write a child-facing cautionary poem-story with a warm ending: the danger is near, the lesson "
        f"is clear, and the child crosses the avenue the safe way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    avenue = f["avenue"]
    lure = f["lure"]
    method = f["method"]
    outcome = f["outcome"]
    name = f["child_name"]
    pw = pair_noun(parent)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a meek little {child.type}, and {name}'s {pw}. They are walking together beside {avenue.label}."
        ),
        (
            f"What tempted {name} to hurry?",
            f"{lure.phrase.capitalize()} {lure.motion} across the avenue, and {name} wanted to go after it at once. The sudden movement made the wish to hurry feel stronger than the wish to wait."
        ),
        (
            f"Why did {name}'s {pw} say not to rush?",
            f"{pw.capitalize()} knew the avenue was busy and that wheels could come quickly. That is why {pw} warned that the road might hurry too if {name} hurried after {lure.label}."
        ),
    ]
    if outcome == "near_miss":
        qa.append((
            f"What scary thing happened before they crossed safely?",
            f"{name} stepped too far from the curb, and a cart swept by very close. {pw.capitalize()} pulled {name} back at once, which is why the story feels suspenseful before it turns safe again."
        ))
    qa.append((
        f"How did they finally get {lure.label} safely?",
        f"They {method.qa_text}. The safe method worked because it matched how busy {avenue.label} was."
    ))
    qa.append((
        "What lesson did the child learn at the end?",
        f"{name} learned not to dart into a road, even for something small and wanted. The ending proves the change because {name} goes on with slow feet and bright eyes instead of rushing."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["avenue"].tags) | set(world.facts["lure"].tags) | set(world.facts["method"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        avenue="clover",
        lure="wheat_bun",
        method="hold_hand",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        avenue="market",
        lure="duckling",
        method="hold_hand",
        child_name="Milo",
        child_gender="boy",
        parent="father",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        avenue="mill",
        lure="straw_hat",
        method="crossing_guard",
        child_name="Elsie",
        child_gender="girl",
        parent="mother",
        trait="timid",
        delay=0,
    ),
    StoryParams(
        avenue="mill",
        lure="wheat_bun",
        method="hold_hand",
        child_name="Ned",
        child_gender="boy",
        parent="father",
        trait="soft-spoken",
        delay=1,
    ),
]


def explain_rejection(avenue: Avenue, lure: Lure) -> str:
    if not hazard_at_risk(avenue, lure):
        return (
            f"(No story: {lure.label} does not create a real road-crossing hazard on {avenue.label}. "
            f"This world only tells stories where a tempting thing on the far side could lure a child toward traffic.)"
        )
    return "(No story: this combination has no cautionary road hazard.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    avenue = AVENUES[params.avenue]
    method = METHODS[params.method]
    return "safe" if is_safe(method, avenue, params.delay) else "near_miss"


ASP_RULES = r"""
hazard(A, L) :- avenue(A), lure(L), bustle(A, B), B >= 1, tempting(L).
valid(A, L) :- hazard(A, L).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

severity(B + D) :- chosen_avenue(A), bustle(A, B), delay(D).
safe_outcome :- chosen_method(M), power(M, P), severity(V), P >= V.
outcome(safe) :- safe_outcome.
outcome(near_miss) :- not safe_outcome.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for avenue_id, avenue in AVENUES.items():
        lines.append(asp.fact("avenue", avenue_id))
        lines.append(asp.fact("bustle", avenue_id, avenue.bustle))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
        lines.append(asp.fact("tempting", lure_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_avenue", params.avenue),
        asp.fact("chosen_method", params.method),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_methods = set(asp_sensible())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_methods)} python={sorted(python_methods)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False, header="smoke")
        finally:
            sys.stdout = old
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme cautionary storyworld about a meek child, an avenue, and a tempting wheat-side trouble."
    )
    ap.add_argument("--avenue", choices=AVENUES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra hesitation before the safe crossing")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.avenue and args.lure:
        avenue = AVENUES[args.avenue]
        lure = LURES[args.lure]
        if not hazard_at_risk(avenue, lure):
            raise StoryError(explain_rejection(avenue, lure))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.avenue is None or combo[0] == args.avenue)
        and (args.lure is None or combo[1] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    avenue_id, lure_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        avenue=avenue_id,
        lure=lure_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        avenue = AVENUES[params.avenue]
        lure = LURES[params.lure]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not hazard_at_risk(avenue, lure):
        raise StoryError(explain_rejection(avenue, lure))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(method.id))

    world = tell(
        avenue=avenue,
        lure=lure,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
    )
    child = world.get("child")
    child_name = params.child_name
    # Replace internal entity ids in the rendered story with display names.
    story = world.render().replace("child", child_name).replace("parent", world.get("parent").label_word)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (avenue, lure) combos:\n")
        for avenue_id, lure_id in combos:
            print(f"  {avenue_id:8} {lure_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.lure} on {p.avenue} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
