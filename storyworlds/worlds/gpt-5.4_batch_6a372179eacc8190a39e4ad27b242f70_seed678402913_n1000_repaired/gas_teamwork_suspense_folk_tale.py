#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py
=============================================================

A standalone storyworld about children in a small village who notice the smell
of gas, work together under pressure, and help a grandparent make the cottage
safe. The stories aim for a gentle folk-tale feel: a clear village setting, a
gathering danger, a wise rule, and an ending image that proves what changed.

The world model is intentionally small and concrete:

- a home has a gas source, an odor, and rising danger
- children notice clues and choose a sensible action
- teamwork matters: one child opens a way out, one calls for help, and the elder
  closes the valve from outside or a helper repairs it
- unsafe choices are known but refused by the reasonableness gate

Run it
------
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py --house cottage --source stove
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py --action light_lantern
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4/gas_teamwork_suspense_folk_tale.py --qa --json
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
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type or self.label)


@dataclass
class House:
    id: str
    label: str
    phrase: str
    door: str
    window: str
    yard: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GasSource:
    id: str
    label: str
    phrase: str
    valve_place: str
    repairer: str
    smell_words: str
    leak_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeAction:
    id: str
    label: str
    sense: int
    steps: tuple[str, ...]
    teamwork: bool
    needs_helper: bool
    closes_from_outside: bool
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class UnsafeAction:
    id: str
    label: str
    sense: int
    why_bad: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_gas_spreads(world: World) -> list[str]:
    out: list[str] = []
    house = world.get("house")
    leak = world.get("leak")
    if leak.meters["open"] < THRESHOLD:
        return out
    sig = ("gas_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    house.meters["gas"] += 1
    house.meters["danger"] += 1
    for eid in ("hero1", "hero2", "elder"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__gas__")
    return out


def _r_smell_noticed(world: World) -> list[str]:
    out: list[str] = []
    house = world.get("house")
    if house.meters["gas"] < THRESHOLD:
        return out
    for eid in ("hero1", "hero2"):
        ent = world.get(eid)
        sig = ("notice", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["alert"] += 1
        out.append("__notice__")
    return out


CAUSAL_RULES = [
    Rule(name="gas_spreads", tag="physical", apply=_r_gas_spreads),
    Rule(name="smell_noticed", tag="social", apply=_r_smell_noticed),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(source: GasSource) -> bool:
    return True


def sensible_actions() -> list[SafeAction]:
    return [a for a in SAFE_ACTIONS.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hid in HOUSES:
        for sid, source in GAS_SOURCES.items():
            for aid, action in SAFE_ACTIONS.items():
                if hazard_at_risk(source) and action.sense >= SENSE_MIN:
                    combos.append((hid, sid, aid))
    return combos


def explain_action_rejection(action_id: str) -> str:
    action = UNSAFE_ACTIONS[action_id]
    better = ", ".join(sorted(SAFE_ACTIONS))
    return (
        f"(Refusing action '{action_id}': {action.why_bad} "
        f"Choose a safer teamwork action such as {better}.)"
    )


def predict_after_leak(world: World) -> dict:
    sim = world.copy()
    sim.get("leak").meters["open"] += 1
    propagate(sim, narrate=False)
    return {
        "gas": sim.get("house").meters["gas"],
        "danger": sim.get("house").meters["danger"],
        "noticed": sim.get("hero1").memes["alert"] >= THRESHOLD,
    }


def begin_evening(world: World, h1: Entity, h2: Entity, elder: Entity, house: House) -> None:
    for ent in (h1, h2, elder):
        ent.memes["peace"] += 1
    world.say(
        f"In a valley of mills and willow trees stood {house.phrase}. "
        f"There lived {h1.id}, {h2.id}, and their {elder.label_word}, who kept a warm table and a tidy hearth."
    )
    world.say(
        f"At dusk the wind went softly around {house.door}, and the children sat listening as if the old house were telling its own quiet tale."
    )


def leak_begins(world: World, source: GasSource, house: House) -> None:
    world.get("leak").meters["open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a new smell crept through the room from {source.leak_place} near the {source.label}: {source.smell_words}. "
        f"It was the smell of gas, and it did not belong in a safe home."
    )
    world.say(
        f"The sound was so small it was almost nothing at all, yet the danger in {house.label} had begun to grow."
    )


def notice(world: World, h1: Entity, h2: Entity) -> None:
    h1.memes["care"] += 1
    h2.memes["care"] += 1
    world.say(
        f'{h1.id} lifted {h1.pronoun("possessive")} head first. "{h1.id if h1.id == h2.id else ""}'
    )
    world.paragraphs[-1].pop()
    world.say(
        f'"Do you smell that?" {h1.id} whispered. {h2.id} sniffed the air too, and all at once both children sat very still.'
    )


def elder_wisdom(world: World, elder: Entity, source: GasSource) -> None:
    pred = predict_after_leak(world)
    world.facts["predicted_danger"] = pred["danger"]
    elder.memes["wisdom"] += 1
    world.say(
        f'Their {elder.label_word} did not strike a match or touch a switch. "{source.label.capitalize()} gas can bite faster than a fox," '
        f'{elder.pronoun()} said. "We must use our heads and our hands together."'
    )


def teamwork_plan(world: World, h1: Entity, h2: Entity, elder: Entity, action: SafeAction, house: House) -> None:
    for ent in (h1, h2, elder):
        ent.memes["resolve"] += 1
    if action.id == "open_and_call":
        world.say(
            f"{h1.id} eased {house.window} wide. {h2.id} held {elder.label_word}'s hand and led {elder.pronoun('object')} through {house.door} into {house.yard}."
        )
        world.say(
            f"Outside, {h2.id} ran to the neighbor's gate and called for help, while {h1.id} stayed by the open air so no one would wander back inside."
        )
    elif action.id == "open_and_close":
        world.say(
            f"{h1.id} pulled {house.window} open, and {h2.id} guided their {elder.label_word} out through {house.door}."
        )
        world.say(
            f"Together they circled the wall to {source_valve_sentence(source=world.facts['source_cfg'])}, where the elder could reach the shutoff from outside."
        )
    elif action.id == "call_repairer":
        world.say(
            f"{h1.id} opened {house.window} to let the air move, while {h2.id} hurried everyone through {house.door} into {house.yard}."
        )
        world.say(
            f"There, with steady hands, the children helped their {elder.label_word} send for {world.facts['source_cfg'].repairer}, and they waited together under the night sky."
        )


def source_valve_sentence(source: GasSource) -> str:
    return f"the outside valve by {source.valve_place}"


def resolve_safe(world: World, h1: Entity, h2: Entity, elder: Entity, action: SafeAction, source: GasSource, house: House) -> None:
    leak = world.get("leak")
    house_ent = world.get("house")
    if action.closes_from_outside:
        leak.meters["open"] = 0.0
        house_ent.meters["danger"] = 0.0
        house_ent.meters["gas"] = 0.0
        world.say(
            f"The elder turned the handle at {source.valve_place}, and the faint hiss gave up at last. For a few breaths they waited, listening harder than they had ever listened before."
        )
        world.say(
            f"When the sharp smell began to thin and drift away, all three of them knew the house had been given back its safety."
        )
    else:
        leak.meters["open"] = 0.0
        house_ent.meters["danger"] = 0.0
        house_ent.meters["gas"] = 0.0
        world.say(
            f"Before long {source.repairer} arrived with a lamp kept safely far from the leak and with practiced, careful hands. Soon the bad line was tightened, the gas was stopped, and the rooms could breathe again."
        )
    for ent in (h1, h2, elder):
        ent.memes["relief"] += 1
        ent.memes["worry"] = 0.0
        ent.memes["trust"] += 1
    world.say(
        f"{action.ending_image} In the yard, the family stood close together, feeling how strong a small team can be when each person does the right part."
    )


def closing_moral(world: World, h1: Entity, h2: Entity, elder: Entity, house: House) -> None:
    world.say(
        f'After that night, {h1.id} and {h2.id} remembered the lesson whenever a strange smell wandered through the air: hurry to safety, open the way out, and call for wise help. '
        f"So {house.label} remained a place of bread, stories, and sleeping lantern-light, not a place of hidden danger."
    )


HOUSES = {
    "cottage": House(
        id="cottage",
        label="the cottage",
        phrase="a stone cottage with a blue door",
        door="the blue door",
        window="the kitchen window",
        yard="the herb yard",
        tags={"home", "village"},
    ),
    "hut": House(
        id="hut",
        label="the hut",
        phrase="a reed-roofed hut at the edge of the lane",
        door="the wooden door",
        window="the front shutter-window",
        yard="the little yard",
        tags={"home", "village"},
    ),
    "farmhouse": House(
        id="farmhouse",
        label="the farmhouse",
        phrase="an old farmhouse beside a plum tree",
        door="the back door",
        window="the pantry window",
        yard="the moonlit yard",
        tags={"home", "farm"},
    ),
}

GAS_SOURCES = {
    "stove": GasSource(
        id="stove",
        label="stove",
        phrase="the cooking stove",
        valve_place="the iron pipe outside the kitchen wall",
        repairer="the village gas man",
        smell_words="sharp and sour, like bad eggs hiding in warm soup",
        leak_place="the loose pipe",
        tags={"gas", "kitchen"},
    ),
    "heater": GasSource(
        id="heater",
        label="heater",
        phrase="the wall heater",
        valve_place="the brass knob by the back step",
        repairer="the town repair woman",
        smell_words="sharp and bitter, like a warning carried in cold metal",
        leak_place="the old heater line",
        tags={"gas", "winter"},
    ),
    "lamp_line": GasSource(
        id="lamp_line",
        label="gas lamp line",
        phrase="the old gas lamp line",
        valve_place="the shutoff by the rain barrel",
        repairer="the lantern keeper",
        smell_words="thin and mean, like a rotten whisper in the dark",
        leak_place="the cracked lamp pipe",
        tags={"gas", "lamp"},
    ),
}

SAFE_ACTIONS = {
    "open_and_call": SafeAction(
        id="open_and_call",
        label="open windows, leave, and call a helper",
        sense=3,
        steps=("open", "leave", "call"),
        teamwork=True,
        needs_helper=True,
        closes_from_outside=False,
        ending_image="Soon the windows breathed out the last of the sharp smell, and the stars above the roof looked clean again.",
        tags={"gas", "teamwork", "call_help"},
    ),
    "open_and_close": SafeAction(
        id="open_and_close",
        label="open a way out and close the valve from outside",
        sense=3,
        steps=("open", "leave", "shutoff"),
        teamwork=True,
        needs_helper=False,
        closes_from_outside=True,
        ending_image="The night wind moved through the open window, and the cottage seemed to sigh like a tired old animal finally at rest.",
        tags={"gas", "teamwork", "shutoff"},
    ),
    "call_repairer": SafeAction(
        id="call_repairer",
        label="leave quickly and send for the repairer",
        sense=2,
        steps=("leave", "call"),
        teamwork=True,
        needs_helper=True,
        closes_from_outside=False,
        ending_image="When the repair was done, even the moonlit yard felt easier to breathe in.",
        tags={"gas", "teamwork", "repair"},
    ),
}

UNSAFE_ACTIONS = {
    "light_lantern": UnsafeAction(
        id="light_lantern",
        label="light a lantern to look around",
        sense=0,
        why_bad="a flame near leaking gas could cause a terrible fire",
        tags={"flame", "gas"},
    ),
    "flip_switch": UnsafeAction(
        id="flip_switch",
        label="turn on a bright switch",
        sense=1,
        why_bad="switches should not be used around a gas leak because a spark could ignite the gas",
        tags={"spark", "gas"},
    ),
    "keep_cooking": UnsafeAction(
        id="keep_cooking",
        label="finish the soup first",
        sense=0,
        why_bad="staying inside and using the stove leaves everyone in danger",
        tags={"gas", "delay"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Lina", "Tessa", "Nora", "Elsa", "Pia", "Willa"]
BOY_NAMES = ["Ivo", "Milo", "Tomas", "Niko", "Sava", "Luka", "Oren", "Bram"]
ELDER_TYPES = ["grandmother", "grandfather"]
TRAITS = ["careful", "steady", "quick", "kind", "thoughtful", "brave"]


@dataclass
class StoryParams:
    house: str
    source: str
    action: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    elder: str
    elder_type: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        house="cottage",
        source="stove",
        action="open_and_close",
        child1="Anya",
        child1_gender="girl",
        child2="Milo",
        child2_gender="boy",
        elder="Baba",
        elder_type="grandmother",
        trait1="careful",
        trait2="steady",
    ),
    StoryParams(
        house="farmhouse",
        source="heater",
        action="open_and_call",
        child1="Tomas",
        child1_gender="boy",
        child2="Nora",
        child2_gender="girl",
        elder="Grandad",
        elder_type="grandfather",
        trait1="quick",
        trait2="kind",
    ),
    StoryParams(
        house="hut",
        source="lamp_line",
        action="call_repairer",
        child1="Lina",
        child1_gender="girl",
        child2="Ivo",
        child2_gender="boy",
        elder="Nan",
        elder_type="grandmother",
        trait1="thoughtful",
        trait2="brave",
    ),
]


def tell(
    house_cfg: House,
    source_cfg: GasSource,
    action_cfg: SafeAction,
    child1: str,
    child1_gender: str,
    child2: str,
    child2_gender: str,
    elder_name: str,
    elder_type: str,
    trait1: str,
    trait2: str,
) -> World:
    world = World()
    h1 = world.add(Entity(id="hero1", kind="character", type=child1_gender, label=child1, role="child", traits=[trait1]))
    h1.attrs["name"] = child1
    h2 = world.add(Entity(id="hero2", kind="character", type=child2_gender, label=child2, role="child", traits=[trait2]))
    h2.attrs["name"] = child2
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="elder", traits=["wise"]))
    house = world.add(Entity(id="house", kind="thing", type="house", label=house_cfg.label, phrase=house_cfg.phrase))
    leak = world.add(Entity(id="leak", kind="thing", type="gas_leak", label="leak"))
    world.facts["child1_name"] = child1
    world.facts["child2_name"] = child2
    world.facts["elder_name"] = elder_name
    world.facts["house_cfg"] = house_cfg
    world.facts["source_cfg"] = source_cfg
    world.facts["action_cfg"] = action_cfg

    begin_evening(world, h1, h2, elder, house_cfg)
    world.para()
    leak_begins(world, source_cfg, house_cfg)
    notice(world, h1, h2)
    elder_wisdom(world, elder, source_cfg)
    world.para()
    teamwork_plan(world, h1, h2, elder, action_cfg, house_cfg)
    world.para()
    resolve_safe(world, h1, h2, elder, action_cfg, source_cfg, house_cfg)
    closing_moral(world, h1, h2, elder, house_cfg)

    outcome = "safe"
    world.facts.update(
        hero1=h1,
        hero2=h2,
        elder=elder,
        house=house,
        leak=leak,
        source=source_cfg,
        action=action_cfg,
        outcome=outcome,
        teamwork=action_cfg.teamwork,
        gas_stopped=leak.meters["open"] < THRESHOLD,
        danger_cleared=house.meters["danger"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c1 = f["child1_name"]
    c2 = f["child2_name"]
    elder_name = f["elder_name"]
    source = f["source_cfg"]
    house = f["house_cfg"]
    return [
        'Write a folk-tale style story for a 3-to-5-year-old that includes the word "gas", uses teamwork, and builds gentle suspense.',
        f"Tell a village-night story where {c1} and {c2} smell gas in {house.label} and must work together with {elder_name} to make the home safe.",
        f"Write a simple suspense tale where children notice danger from a {source.label}, stay calm, and help in the right order until the house is safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1 = f["child1_name"]
    c2 = f["child2_name"]
    elder_name = f["elder_name"]
    elder = f["elder"]
    house = f["house_cfg"]
    source = f["source_cfg"]
    action = f["action_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {c1}, {c2}, and their {elder.label_word} {elder_name}. They live together in {house.label} and face one dangerous problem as a team.",
        ),
        (
            "What made the story feel scary?",
            f"A strange smell of gas crept into the house so quietly that the danger was hard to see. That made the children listen closely and move carefully before anything worse could happen.",
        ),
        (
            f"What danger did the family notice?",
            f"They noticed gas leaking near the {source.label}. The smell warned them that the house was no longer safe to stay in as if nothing were wrong.",
        ),
    ]
    if action.id == "open_and_call":
        qa.append(
            (
                "How did the children work together?",
                f"{c1} opened a way for air to move, and {c2} helped lead their {elder.label_word} outside and called for help. Their teamwork mattered because each child took one clear job and nobody wasted time.",
            )
        )
    elif action.id == "open_and_close":
        qa.append(
            (
                "How did the children work together?",
                f"One child opened a window and the other guided their {elder.label_word} outside, and then all three went to the outside valve together. They solved the problem by sharing the work in the safest order.",
            )
        )
    else:
        qa.append(
            (
                "How did the children work together?",
                f"One child opened the house and the other helped everyone reach the yard, and then they helped send for the repairer. They stayed together and followed the wise plan instead of panicking.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the gas stopped and the home safe again. The final image in the yard shows the family standing close together, calmer because they had acted wisely and together.",
        )
    )
    return qa


KNOWLEDGE = {
    "gas": [
        (
            "What is gas in a home like this?",
            "Gas is a fuel people may use for cooking or heat. It can be useful, but if it leaks into the air it becomes dangerous."
        )
    ],
    "smell": [
        (
            "Why is a gas smell important?",
            "A gas smell is a warning sign. It tells people something may be leaking and they should get safe help quickly."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another by sharing jobs and acting together. A hard problem can become easier when each person does a careful part."
        )
    ],
    "call_help": [
        (
            "Why should you call a grown-up or helper for a gas leak?",
            "A gas leak is not a child's job to fix alone. A trusted grown-up or repair worker knows how to make the place safe."
        )
    ],
    "shutoff": [
        (
            "What does shutting off the gas do?",
            "Shutting off the gas stops more fuel from escaping. That helps the danger stop growing."
        )
    ],
    "repair": [
        (
            "What does a repair worker do?",
            "A repair worker finds what is broken and fixes it the safe way. That is how a leak can be stopped properly."
        )
    ],
}
KNOWLEDGE_ORDER = ["gas", "smell", "teamwork", "call_help", "shutoff", "repair"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gas", "smell", "teamwork"}
    action = world.facts["action_cfg"]
    if "call_help" in action.tags:
        tags.add("call_help")
    if "shutoff" in action.tags:
        tags.add("shutoff")
    if "repair" in action.tags:
        tags.add("repair")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S) :- source(S).

sensible(A) :- action(A), sense(A, N), sense_min(M), N >= M.
valid(H, S, A) :- house(H), source(S), action(A), sensible(A), hazard(S).

outcome(A, safe) :- sensible(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HOUSES:
        lines.append(asp.fact("house", hid))
    for sid in GAS_SOURCES:
        lines.append(asp.fact("source", sid))
    for aid, action in SAFE_ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
    for aid, action in UNSAFE_ACTIONS.items():
        lines.append(asp.fact("unsafe_action", aid))
        lines.append(asp.fact("unsafe_sense", aid, action.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_actions() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(action_id: str) -> str:
    import asp
    model = asp.one_model(
        asp_program(
            "",
            "#show outcome/2.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    for a, out in atoms:
        if a == action_id:
            return out
    return "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a folk-tale gas scare solved by teamwork. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--house", choices=HOUSES)
    ap.add_argument("--source", choices=GAS_SOURCES)
    ap.add_argument("--action", choices=list(SAFE_ACTIONS) + list(UNSAFE_ACTIONS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action in UNSAFE_ACTIONS:
        raise StoryError(explain_action_rejection(args.action))

    combos = [
        combo for combo in valid_combos()
        if (args.house is None or combo[0] == args.house)
        and (args.source is None or combo[1] == args.source)
        and (args.action is None or combo[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    house, source, action = rng.choice(sorted(combos))
    g1 = rng.choice(["girl", "boy"])
    g2 = rng.choice(["girl", "boy"])
    c1 = _pick_name(rng, g1)
    c2 = _pick_name(rng, g2, avoid=c1)
    elder_type = rng.choice(ELDER_TYPES)
    elder_name = rng.choice(["Baba", "Nan", "Old Mira", "Grandad", "Dedo", "Nona"])
    return StoryParams(
        house=house,
        source=source,
        action=action,
        child1=c1,
        child1_gender=g1,
        child2=c2,
        child2_gender=g2,
        elder=elder_name,
        elder_type=elder_type,
        trait1=rng.choice(TRAITS),
        trait2=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.house not in HOUSES:
        raise StoryError(f"(Unknown house: {params.house})")
    if params.source not in GAS_SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.action not in SAFE_ACTIONS:
        if params.action in UNSAFE_ACTIONS:
            raise StoryError(explain_action_rejection(params.action))
        raise StoryError(f"(Unknown action: {params.action})")

    world = tell(
        house_cfg=HOUSES[params.house],
        source_cfg=GAS_SOURCES[params.source],
        action_cfg=SAFE_ACTIONS[params.action],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        elder_name=params.elder,
        elder_type=params.elder_type,
        trait1=params.trait1,
        trait2=params.trait2,
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
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {a.id for a in sensible_actions()}
    asp_sensible = set(asp_sensible_actions())
    if py_sensible == asp_sensible:
        print(f"OK: sensible actions match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible actions: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    for aid in sorted(SAFE_ACTIONS):
        if asp_outcome(aid) != "safe":
            rc = 1
            print(f"MISMATCH in outcome for {aid}: clingo={asp_outcome(aid)} python=safe")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show valid/3.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible actions: {', '.join(asp_sensible_actions())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (house, source, action) combos:\n")
        for house, source, action in combos:
            print(f"  {house:10} {source:10} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} and {p.child2}: {p.source} in {p.house} ({p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
