#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/physics_pier_rhyme_lesson_learned_nursery_rhyme.py
=============================================================================

A standalone story world about a child on a pier learning a small, concrete
piece of physics: when a load is too heavy or uneven for a little carrier, it
wobbles and can tip. The safe fix is to balance the load, slow down, or make
two trips instead of one.

The stories are written in a gentle nursery-rhyme style with repeated rhyme
echoes, but the prose is driven by simulated state rather than slot-swapped
templates. The world tracks simple physical meters (weight, wobble, spill,
distance, safety) and emotional memes (pride, worry, relief, patience, joy).

Run it
------
    python storyworlds/worlds/gpt-5.4/physics_pier_rhyme_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/physics_pier_rhyme_lesson_learned_nursery_rhyme.py --cargo shells --carrier wagon
    python storyworlds/worlds/gpt-5.4/physics_pier_rhyme_lesson_learned_nursery_rhyme.py --cargo fish_bucket --carrier basket
    python storyworlds/worlds/gpt-5.4/physics_pier_rhyme_lesson_learned_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/physics_pier_rhyme_lesson_learned_nursery_rhyme.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    pieces: int
    material: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    stable_bonus: int
    roll_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    mode: str
    stability_gain: int
    capacity_gain: int
    text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    load = world.get("load")
    carrier = world.get("carrier")
    if load.meters["weight"] <= carrier.meters["capacity"]:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.meters["wobble"] += 1
    carrier.meters["risk"] += 1
    world.get("pier").meters["danger"] += 1
    world.get("child").memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_tip(world: World) -> list[str]:
    out: list[str] = []
    load = world.get("load")
    carrier = world.get("carrier")
    child = world.get("child")
    if carrier.meters["wobble"] < THRESHOLD:
        return out
    if child.memes["hurry"] < THRESHOLD:
        return out
    excess = load.meters["weight"] - carrier.meters["capacity"]
    if excess < 2 and carrier.meters["stability"] >= 1:
        return out
    sig = ("tip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    load.meters["spilled"] += 1
    carrier.meters["tilted"] += 1
    world.get("pier").meters["danger"] += 1
    child.memes["fear"] += 1
    out.append("__tip__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="tip", tag="physical", apply=_r_tip),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__wobble__":
                world.say("The little load gave a wobble and a sway, as if the boards themselves had something to say.")
            elif bit == "__tip__":
                world.say("Then over it leaned with a clitter-clatter sound, and part of the load came tumbling to the ground.")
    return produced


def load_is_risky(cargo: Cargo, carrier: Carrier) -> bool:
    return cargo.weight > carrier.capacity


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for cargo_id, cargo in CARGOS.items():
        for carrier_id, carrier in CARRIERS.items():
            if load_is_risky(cargo, carrier):
                combos.append((cargo_id, carrier_id))
    return combos


def fix_solves(cargo: Cargo, carrier: Carrier, fix: Fix) -> bool:
    if fix.mode == "two_trips":
        return True
    if fix.mode == "rebalance":
        return cargo.weight <= carrier.capacity + fix.capacity_gain and carrier.stable_bonus + fix.stability_gain >= 1
    if fix.mode == "bigger_carrier":
        return cargo.weight <= carrier.capacity + fix.capacity_gain
    return False


def best_fix_for(cargo: Cargo, carrier: Carrier) -> list[str]:
    good = [fix.id for fix in sensible_fixes() if fix_solves(cargo, carrier, fix)]
    return sorted(good)


def explain_rejection(cargo: Cargo, carrier: Carrier) -> str:
    return (
        f"(No story: {carrier.phrase} can safely hold {carrier.capacity} weight-units, "
        f"but {cargo.phrase} weighs only {cargo.weight}. If nothing is too heavy, there is no wobble, "
        f"no turn, and no physics lesson to learn.)"
    )


def explain_fix_rejection(cargo: Cargo, carrier: Carrier, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). The storyworld prefers safer fixes like "
            f"{' / '.join(best_fix_for(cargo, carrier) or ['make_two_trips'])}.)"
        )
    return (
        f"(No story: fix '{fix.id}' would not make {cargo.label} safe in the {carrier.label}. "
        f"Try one of: {', '.join(best_fix_for(cargo, carrier) or ['make_two_trips'])}.)"
    )


def predict_trip(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["hurry"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("carrier").meters["wobble"] >= THRESHOLD,
        "tip": sim.get("load").meters["spilled"] >= THRESHOLD,
        "danger": sim.get("pier").meters["danger"],
    }


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def introduce(world: World, child: Entity, helper: Entity, cargo: Cargo, carrier: Carrier) -> None:
    world.say(
        f"On the pier at morning light, {child.id} skipped left and right. "
        f"{helper.id} stood near with a smile so clear, while gulls called bright above the pier."
    )
    world.say(
        f"{child.id} had {cargo.phrase} and {carrier.phrase}. "
        f'"I can move it all at once," {child.pronoun()} sang, "and I will be there in a trice!"'
    )


def need(world: World, cargo: Cargo) -> None:
    world.say(
        f"The bait shop waited at the far end of the planks, and the sea made soft slap-slap thanks. "
        f"The job was plain: carry {cargo.label} along, and make the morning a little work-song."
    )


def boast(world: World, child: Entity, carrier: Carrier) -> None:
    child.memes["pride"] += 1
    child.memes["hurry"] += 1
    world.say(
        f'{child.id} gave the {carrier.label} a tug and a grin. '
        f'"Quick and slick, fast as can be — that is the way for me!"'
    )


def warn(world: World, child: Entity, helper: Entity, cargo: Cargo, carrier: Carrier) -> None:
    pred = predict_trip(world)
    world.facts["predicted_tip"] = pred["tip"]
    world.facts["predicted_wobble"] = pred["wobble"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} watched the load and softly said, '
        f'"Slow your feet and use your head. '
        f'Here is a bit of physics for the day: when weight sits wrong, small wheels sway."'
    )
    if pred["tip"]:
        world.say(
            f'"If all that weight goes in one sweep, the {carrier.label} may tip and spill in a heap."'
        )
    else:
        world.say(
            f'"Even before a tumble, I can see a wobble. On these pier boards, a wobble is trouble."'
        )


def start_trip(world: World, child: Entity, cargo: Cargo, carrier: Carrier) -> None:
    load = world.get("load")
    carry = world.get("carrier")
    load.meters["weight"] = float(cargo.weight)
    carry.meters["capacity"] = float(carrier.capacity)
    carry.meters["stability"] = float(carrier.stable_bonus)
    world.say(
        f"Still {child.id} pulled with a patter and clack. The {carrier.label} rolled over each board crack."
    )
    propagate(world, narrate=True)


def fix_applied(world: World, child: Entity, helper: Entity, cargo: Cargo, carrier: Carrier, fix: Fix) -> None:
    child.memes["patience"] += 1
    child.memes["pride"] = 0.0
    helper.memes["care"] += 1
    if fix.mode == "two_trips":
        world.get("load").meters["weight"] = float(max(1, cargo.weight // 2 + cargo.weight % 2))
        world.get("carrier").meters["capacity"] = float(carrier.capacity)
        world.get("carrier").meters["stability"] = float(carrier.stable_bonus)
        world.say(
            f'{helper.id} knelt by the planks and said, "{fix.text}" '
            f'Together they split the load into two neat rows, small enough for the {carrier.label} to go.'
        )
    elif fix.mode == "rebalance":
        world.get("carrier").meters["capacity"] = float(carrier.capacity + fix.capacity_gain)
        world.get("carrier").meters["stability"] = float(carrier.stable_bonus + fix.stability_gain)
        world.say(
            f'{helper.id} said, "{fix.text}" '
            f'{helper.pronoun().capitalize()} tucked the heavy things low and in the middle, where the load would ride less like a fiddle.'
        )
    elif fix.mode == "bigger_carrier":
        world.get("carrier").meters["capacity"] = float(carrier.capacity + fix.capacity_gain)
        world.get("carrier").meters["stability"] = float(carrier.stable_bonus + fix.stability_gain)
        world.say(
            f'{helper.id} said, "{fix.text}" '
            f'Soon a sturdier cart stood ready by the rail, wide in the wheels and steady in the trail.'
        )
    world.get("carrier").meters["wobble"] = 0.0
    world.get("carrier").meters["tilted"] = 0.0
    world.get("load").meters["spilled"] = 0.0
    world.get("pier").meters["danger"] = 0.0
    world.get("child").memes["hurry"] = 0.0
    world.get("child").memes["fear"] = 0.0
    world.get("child").memes["relief"] += 1


def safe_trip(world: World, child: Entity, helper: Entity, cargo: Cargo, carrier: Carrier, fix: Fix) -> None:
    world.get("child").memes["joy"] += 1
    world.get("child").memes["lesson"] += 1
    world.get("child").meters["distance"] += 1
    world.say(
        f"Then off they went with step by step, not fast and rash but calm and kept. "
        f"The {carrier.label} gave {carrier.roll_word}, soft and slow, and all the load stayed snug below."
    )
    world.say(
        f'At the end of the pier, {child.id} laughed, "{cargo.label.capitalize()} arrived, and so did I!" '
        f'{helper.id} tapped the handle and said, "That is the lesson to keep nearby."'
    )
    world.say(
        "Little loads may dance and slide; balance helps them safely ride. "
        "That was the physics lesson learned on the shining pier where the gulls returned."
    )


def aftermath_spill(world: World, child: Entity, helper: Entity, cargo: Cargo) -> None:
    child.memes["fear"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{cargo.pieces} little pieces did not all stay still. Some skittered near the rail with a clink and spill."
    )
    world.say(
        f"{helper.id} caught the handle before worse could start, and held {child.id} close with a careful heart."
    )


def tell(
    cargo: Cargo,
    carrier: Carrier,
    fix: Fix,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_name: str = "Dad",
    helper_type: str = "father",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    pier = world.add(Entity(id="pier", type="pier", label="pier", phrase="the wooden pier", tags={"pier"}))
    load = world.add(Entity(id="load", type="cargo", label=cargo.label, phrase=cargo.phrase, tags=set(cargo.tags)))
    carrier_ent = world.add(Entity(id="carrier", type="carrier", label=carrier.label, phrase=carrier.phrase, tags=set(carrier.tags)))

    introduce(world, child, helper, cargo, carrier)
    need(world, cargo)

    world.para()
    boast(world, child, carrier)
    warn(world, child, helper, cargo, carrier)
    start_trip(world, child, cargo, carrier)

    if load.meters["spilled"] >= THRESHOLD:
        aftermath_spill(world, child, helper, cargo)

    world.para()
    fix_applied(world, child, helper, cargo, carrier, fix)
    safe_trip(world, child, helper, cargo, carrier, fix)

    world.facts.update(
        child=child,
        helper=helper,
        cargo_cfg=cargo,
        carrier_cfg=carrier,
        fix=fix,
        pier=pier,
        load=load,
        carrier=carrier_ent,
        spilled_before_fix=True,
        lesson=child.memes["lesson"] >= THRESHOLD,
        predicted_tip=world.facts.get("predicted_tip", False),
        predicted_wobble=world.facts.get("predicted_wobble", False),
    )
    return world


CARGOS = {
    "shells": Cargo(
        id="shells",
        label="shells",
        phrase="a pail of shiny shells",
        weight=3,
        pieces=12,
        material="shell",
        plural=True,
        tags={"shells", "weight"},
    ),
    "rope": Cargo(
        id="rope",
        label="rope coils",
        phrase="two heavy rope coils",
        weight=4,
        pieces=2,
        material="rope",
        plural=True,
        tags={"rope", "weight"},
    ),
    "fish_bucket": Cargo(
        id="fish_bucket",
        label="the fish bucket",
        phrase="a sloshy fish bucket",
        weight=5,
        pieces=1,
        material="water",
        plural=False,
        tags={"fish", "water", "weight"},
    ),
}

CARRIERS = {
    "wagon": Carrier(
        id="wagon",
        label="wagon",
        phrase="a red little wagon",
        capacity=2,
        stable_bonus=0,
        roll_word="a rumble-bump along the boards",
        tags={"wagon"},
    ),
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a wicker carry basket",
        capacity=1,
        stable_bonus=0,
        roll_word="almost no song at all, because it had no wheels",
        tags={"basket"},
    ),
    "handcart": Carrier(
        id="handcart",
        label="handcart",
        phrase="a narrow handcart",
        capacity=3,
        stable_bonus=1,
        roll_word="a neat clack-click over the boards",
        tags={"handcart"},
    ),
}

FIXES = {
    "make_two_trips": Fix(
        id="make_two_trips",
        label="make two trips",
        sense=3,
        mode="two_trips",
        stability_gain=0,
        capacity_gain=0,
        text="One trip for some, then one trip for the rest. Small and steady is often best.",
        qa_text="They split the heavy load into two smaller trips.",
        tags={"counting", "patience"},
    ),
    "rebalance_low": Fix(
        id="rebalance_low",
        label="rebalance low",
        sense=3,
        mode="rebalance",
        stability_gain=1,
        capacity_gain=1,
        text="Let us place the heaviest part low and near the middle. Balanced loads wobble less.",
        qa_text="They put the heaviest part low and in the middle so the load stayed balanced.",
        tags={"balance", "physics"},
    ),
    "bigger_cart": Fix(
        id="bigger_cart",
        label="bigger cart",
        sense=2,
        mode="bigger_carrier",
        stability_gain=1,
        capacity_gain=2,
        text="This little carrier is too small. We need a wider one for such a heavy haul.",
        qa_text="They switched to a wider, stronger carrier that could hold the weight safely.",
        tags={"force", "physics"},
    ),
    "run_faster": Fix(
        id="run_faster",
        label="run faster",
        sense=1,
        mode="rebalance",
        stability_gain=0,
        capacity_gain=0,
        text="Go faster before it falls.",
        qa_text="They tried to go faster.",
        tags={"bad_idea"},
    ),
}


@dataclass
class StoryParams:
    cargo: str
    carrier: str
    fix: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lula", "Nora", "Tess", "Poppy", "May"]
BOY_NAMES = ["Ollie", "Finn", "Toby", "Ned", "Leo", "Ben"]
HELPER_NAMES = {
    "mother": ["Mom", "Mama"],
    "father": ["Dad", "Papa"],
}
CHILD_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father"]

CURATED = [
    StoryParams(
        cargo="shells",
        carrier="wagon",
        fix="make_two_trips",
        child_name="Mina",
        child_type="girl",
        helper_name="Dad",
        helper_type="father",
    ),
    StoryParams(
        cargo="rope",
        carrier="wagon",
        fix="bigger_cart",
        child_name="Ollie",
        child_type="boy",
        helper_name="Mom",
        helper_type="mother",
    ),
    StoryParams(
        cargo="fish_bucket",
        carrier="handcart",
        fix="rebalance_low",
        child_name="Nora",
        child_type="girl",
        helper_name="Dad",
        helper_type="father",
    ),
]


KNOWLEDGE = {
    "pier": [
        (
            "What is a pier?",
            "A pier is a long platform built out over the water. People walk on it to fish, look at boats, or carry things near the sea.",
        )
    ],
    "physics": [
        (
            "What does physics mean in a simple way?",
            "Physics is the study of how things move, push, pull, fall, and balance. In a child's story, it can mean noticing that heavy things wobble or tip if they are carried the wrong way.",
        )
    ],
    "balance": [
        (
            "Why does balance matter when you carry something?",
            "Balance matters because a load that is even and low is less likely to wobble or tip. When the weight sits crooked, it pulls harder on one side.",
        )
    ],
    "weight": [
        (
            "What can happen if a load is too heavy for a small carrier?",
            "It may wobble, tip, or spill. A small carrier can only hold so much weight before it becomes hard to control.",
        )
    ],
    "wagon": [
        (
            "What is a wagon?",
            "A wagon is a small cart with wheels that can carry things when someone pulls it. If it is overloaded, it can be hard to keep steady.",
        )
    ],
    "handcart": [
        (
            "What is a handcart?",
            "A handcart is a small cart used to move things. A stronger handcart can carry more weight than a tiny toy wagon.",
        )
    ],
    "counting": [
        (
            "Why can making two trips be safer than making one?",
            "Two smaller trips can be safer because each trip is lighter and easier to control. Going slowly with less weight helps stop spills.",
        )
    ],
    "force": [
        (
            "Why does a wider, stronger carrier help?",
            "A stronger carrier can handle more weight without wobbling as much. Wider wheels or a sturdier frame make the load steadier.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pier", "physics", "balance", "weight", "wagon", "handcart", "counting", "force"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cargo = f["cargo_cfg"]
    carrier = f["carrier_cfg"]
    fix = f["fix"]
    return [
        f'Write a nursery-rhyme style story set on a pier that includes the word "physics" and teaches a small lesson about balance.',
        f"Tell a gentle rhyming story where {child.id} tries to move {cargo.label} in a {carrier.label}, something wobbles, and a grown-up helps with a safer plan.",
        f"Write a short child-facing rhyme in which a heavy load becomes a little physics lesson, and the fix is to {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    carrier = f["carrier_cfg"]
    fix = f["fix"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} on a pier and {helper.id}, {child.pronoun('possessive')} {helper_word}, helping nearby. They are moving {cargo.label} together by the sea.",
        ),
        (
            f"What problem started when {child.id} tried to use the {carrier.label}?",
            f"The load was too heavy for the {carrier.label}, so it began to wobble and tip. That happened because the weight was more than the little carrier could handle safely.",
        ),
        (
            'Why did the grown-up say the word "physics"?',
            "The grown-up used the word to explain that weight, balance, and motion follow real rules. The lesson was that a heavy or uneven load will sway more on a small carrier, especially on pier boards.",
        ),
    ]
    if f.get("spilled_before_fix"):
        qa.append(
            (
                "Did anything spill before the safe fix?",
                f"Yes. Part of the load spilled when the carrier tipped. That small spill showed why hurrying with too much weight was risky.",
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"{fix.qa_text} After that, the trip was slower and steadier, so the load reached the end of the pier safely.",
        )
    )
    qa.append(
        (
            "What lesson did the child learn at the end?",
            "The child learned that quick is not always wise, and balance matters when something is heavy. A calm plan made the work safer than a proud, hurried one.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"pier", "physics", "weight"}
    tags |= set(f["fix"].tags)
    tags |= set(f["carrier_cfg"].tags)
    if f["fix"].id == "rebalance_low":
        tags.add("balance")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(C, Car) :- cargo(C), carrier(Car), weight(C, W), capacity(Car, Cap), W > Cap.

sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

solves(C, Car, F) :- risky(C, Car), mode(F, two_trips).
solves(C, Car, F) :- risky(C, Car), mode(F, rebalance),
                     weight(C, W), capacity(Car, Cap), cap_gain(F, G),
                     stable_bonus(Car, B), stability_gain(F, SG),
                     W <= Cap + G, B + SG >= 1.
solves(C, Car, F) :- risky(C, Car), mode(F, bigger_carrier),
                     weight(C, W), capacity(Car, Cap), cap_gain(F, G),
                     W <= Cap + G.

valid(C, Car) :- risky(C, Car).

chosen_valid_fix :- chosen_cargo(C), chosen_carrier(Car), chosen_fix(F), sensible_fix(F), solves(C, Car, F).
story_ok :- chosen_cargo(C), chosen_carrier(Car), risky(C, Car), chosen_valid_fix.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("weight", cid, cargo.weight))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("capacity", cid, carrier.capacity))
        lines.append(asp.fact("stable_bonus", cid, carrier.stable_bonus))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("cap_gain", fid, fix.capacity_gain))
        lines.append(asp.fact("stability_gain", fid, fix.stability_gain))
        lines.append(asp.fact("mode", fid, fix.mode))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible_fix"))


def asp_story_ok(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_carrier", params.carrier),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show story_ok/0."))
    return bool(asp.atoms(model, "story_ok"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world on a pier: a child learns a small physics lesson about heavy loads, balance, and moving safely."
    )
    ap.add_argument("--cargo", choices=sorted(CARGOS))
    ap.add_argument("--carrier", choices=sorted(CARRIERS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible cargo/carrier combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.carrier:
        cargo = CARGOS[args.cargo]
        carrier = CARRIERS[args.carrier]
        if not load_is_risky(cargo, carrier):
            raise StoryError(explain_rejection(cargo, carrier))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.carrier is None or combo[1] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, carrier_id = rng.choice(sorted(combos))
    cargo = CARGOS[cargo_id]
    carrier = CARRIERS[carrier_id]

    if args.fix:
        fix = FIXES[args.fix]
        if not fix_solves(cargo, carrier, fix) or fix.sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(cargo, carrier, fix))
        fix_id = args.fix
    else:
        fix_choices = [fix.id for fix in sensible_fixes() if fix_solves(cargo, carrier, fix)]
        if not fix_choices:
            raise StoryError("(No sensible fix solves the chosen cargo/carrier problem.)")
        fix_id = rng.choice(sorted(fix_choices))

    child_type = args.child_type or rng.choice(CHILD_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES[helper_type])

    return StoryParams(
        cargo=cargo_id,
        carrier=carrier_id,
        fix=fix_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    cargo = CARGOS[params.cargo]
    carrier = CARRIERS[params.carrier]
    fix = FIXES[params.fix]

    if not load_is_risky(cargo, carrier):
        raise StoryError(explain_rejection(cargo, carrier))
    if fix.sense < SENSE_MIN or not fix_solves(cargo, carrier, fix):
        raise StoryError(explain_fix_rejection(cargo, carrier, fix))

    world = tell(
        cargo=cargo,
        carrier=carrier,
        fix=fix,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sens = {fix.id for fix in sensible_fixes()}
    asp_sens = set(asp_sensible_fixes())
    if py_sens == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: python={sorted(py_sens)} clingo={sorted(asp_sens)}")

    scenarios: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    bad = 0
    for params in scenarios:
        py_ok = FIXES[params.fix].sense >= SENSE_MIN and fix_solves(CARGOS[params.cargo], CARRIERS[params.carrier], FIXES[params.fix])
        asp_ok = asp_story_ok(params)
        if py_ok != asp_ok:
            bad += 1
    if bad == 0:
        print(f"OK: ASP story_ok parity matches Python on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} story_ok checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        fixes = asp_sensible_fixes()
        print(f"sensible fixes: {', '.join(fixes)}\n")
        print(f"{len(combos)} compatible (cargo, carrier) combos:\n")
        for cargo, carrier in combos:
            print(f"  {cargo:12} {carrier}")
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
            header = f"### {p.child_name}: {p.cargo} in {p.carrier} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
