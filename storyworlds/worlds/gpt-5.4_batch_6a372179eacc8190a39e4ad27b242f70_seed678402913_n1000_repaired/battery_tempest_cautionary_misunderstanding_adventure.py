#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py
===================================================================================

A standalone storyworld about two children turning a stormy afternoon into an
adventure. During a loud tempest, their pretend expedition needs light. One
child finds a loose battery and misunderstands what it is safe for: either a
tiny "treasure coin" to carry in the mouth, or a "storm key" to wake with metal.
A cautious child warns them, and a grown-up helps them switch to a safe plan.

This world is intentionally small and constraint-checked:

* Only battery/mistake pairs with a believable hazard are allowed.
* The misunderstanding drives the danger beat.
* The ending changes because the loose battery is put away and safe light takes
  its place.
* The ASP twin mirrors both the validity gate and the simple outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py
    python storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py --battery button_cell --mistake coin
    python storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py --battery aa --mistake coin
    python storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py --all
    python storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/battery_tempest_cautionary_misunderstanding_adventure.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    team_word: str
    goal: str
    dark_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BatteryKind:
    id: str
    label: str
    phrase: str
    small: bool = False
    exposed_both: bool = False
    powers: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str
    nickname: str
    speech: str
    mode: str
    warning: str
    lesson: str
    requires_small: bool = False
    requires_exposed: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    phrase: str
    glow: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_mouth_fear(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("instigator")
    if not kid or kid.meters["mouth_risk"] < THRESHOLD:
        return out
    sig = ("mouth_fear", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["fear"] += 1
    if "room" in world.entities:
        world.get("room").meters["danger"] += 1
    out.append("__mouth__")
    return out


def _r_heat_fear(world: World) -> list[str]:
    out: list[str] = []
    battery = world.entities.get("battery")
    if not battery or battery.meters["hot"] < THRESHOLD:
        return out
    sig = ("heat_fear", battery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    if "room" in world.entities:
        world.get("room").meters["danger"] += 1
    out.append("__heat__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="mouth_fear", tag="safety", apply=_r_mouth_fear),
    Rule(name="heat_fear", tag="safety", apply=_r_heat_fear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def battery_matches(battery: BatteryKind, mistake: Mistake) -> bool:
    if mistake.requires_small and not battery.small:
        return False
    if mistake.requires_exposed and not battery.exposed_both:
        return False
    return True


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def predict_incident(world: World, mistake: Mistake) -> dict:
    sim = world.copy()
    do_mistake(sim, mistake, narrate=False)
    battery = sim.get("battery")
    kid = sim.get("instigator")
    return {
        "mouth_risk": kid.meters["mouth_risk"],
        "hot": battery.meters["hot"],
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"Rain battered the windows, and the wind made the house sound like a ship in a tempest. "
        f"{a.id} and {b.id} turned the living room into {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"Quick," said {a.id}, "we have to reach {theme.goal} before the storm gets us."'
    )
    world.say(
        f"{b.id} looked toward {theme.dark_spot}, where the blankets made a deep little cave."
    )
    world.say(
        f"{parent.label_word.capitalize()} was nearby, folding laundry and listening to the rain."
    )


def device_fails(world: World, a: Entity, battery: BatteryKind, theme: Theme) -> None:
    world.say(
        f"They clicked their toy beacon, but only a weak blink came out. Its battery was all used up, "
        f"and {theme.dark_spot} suddenly felt much darker."
    )
    a.memes["desire"] += 1


def temptation(world: World, a: Entity, battery: BatteryKind, mistake: Mistake) -> None:
    world.say(
        f'Then {a.id} spotted {battery.phrase} on the side table. "{mistake.speech}" '
        f"{a.pronoun()} said. \"It can help our adventure.\""
    )
    a.memes["bravado"] += 1
    world.get("battery").meters["loose"] += 1


def warning(world: World, b: Entity, a: Entity, battery: BatteryKind, mistake: Mistake) -> None:
    pred = predict_incident(world, mistake)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    extra = ""
    if mistake.mode == "mouth":
        extra = " It was too small to belong anywhere near a mouth."
    elif mistake.mode == "short":
        extra = " Metal touching both ends could make it heat up fast."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. {mistake.warning}"{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, battery: BatteryKind) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at the little battery, then at {b.id}. The storm still boomed outside, "
        f"but the brave idea suddenly felt much smaller."
    )
    world.say(
        f'"You are right," {a.pronoun()} whispered. {a.id} set the battery down on a high shelf and stepped away from it.'
    )


def defy(world: World, a: Entity, mistake: Mistake) -> None:
    a.memes["defiance"] += 1
    if mistake.mode == "mouth":
        world.say(
            f'"I only want to carry it for one second," {a.id} said, and lifted the battery toward {a.pronoun("possessive")} lips.'
        )
    else:
        world.say(
            f'"I just want to wake it up," {a.id} said, reaching for a metal key from the table.'
        )


def do_mistake(world: World, mistake: Mistake, narrate: bool = True) -> None:
    battery = world.get("battery")
    kid = world.get("instigator")
    if mistake.mode == "mouth":
        kid.meters["mouth_risk"] += 1
        battery.meters["near_mouth"] += 1
    else:
        battery.meters["hot"] += 1
        battery.meters["spark"] += 1
    propagate(world, narrate=narrate)


def interrupt(world: World, parent: Entity, a: Entity, battery: BatteryKind, mistake: Mistake) -> None:
    world.say(
        f"Before the dangerous idea could become a dangerous action, {parent.label_word} crossed the room in two quick steps."
    )
    world.say(
        f'{parent.label_word.capitalize()} gently closed {a.id}\'s hand and took the loose battery away. '
        f'"Loose batteries are for grown-ups to handle," {parent.pronoun()} said.'
    )
    a.memes["fear"] += 1
    a.memes["relief"] += 1
    world.get("battery").meters["stored"] += 1


def incident(world: World, parent: Entity, a: Entity, battery: BatteryKind, mistake: Mistake) -> None:
    do_mistake(world, mistake, narrate=False)
    if mistake.mode == "mouth":
        world.say(
            f"The cold edge touched {a.id}'s lips, and {a.pronoun()} froze at once. It felt wrong right away."
        )
    else:
        world.say(
            "The key tapped the battery, and a tiny angry spark snapped. The battery grew warm so quickly that both children jumped."
        )
    world.say(f'"{parent.label_word.upper()}!"')
    world.say(
        f"{parent.label_word.capitalize()} hurried over, took the battery away, and set it high above little hands."
    )
    world.get("battery").meters["stored"] += 1
    a.memes["relief"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 0.0


def lesson(world: World, parent: Entity, a: Entity, b: Entity, battery: BatteryKind, mistake: Mistake) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "{mistake.lesson} '
        f'If you find a loose battery, you do not touch it with your mouth, and you do not test it with metal. '
        f'You call a grown-up," {parent.pronoun()} said.'
    )
    world.say(
        f"{a.id} nodded hard. {b.id} leaned close, and the storm no longer sounded exciting. It only sounded loud."
    )


def safe_plan(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, tool: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.para()
    world.say(
        f"After the scary moment had been talked through, {parent.label_word} opened a drawer and brought out {tool.phrase}."
    )
    world.say(
        f"It {tool.glow}, and its battery door was shut tight where little fingers could not open it."
    )
    world.say(
        f'"Now your adventure can go on the safe way," {parent.pronoun()} said.'
    )
    world.say(
        f"{a.id} held the light low. {b.id} crawled into {theme.dark_spot}. At the back of their fort, the blankets shone gold instead of scary gray."
    )
    world.say(
        f"Outside, the tempest still drummed on the windows, but inside the two {theme.team_word} explorers were calm, bright, and careful."
    )


def tell(
    theme: Theme,
    battery_cfg: BatteryKind,
    mistake: Mistake,
    safe_tool: SafeTool,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    battery = world.add(Entity(
        id="battery",
        type="battery",
        label=battery_cfg.label,
        phrase=battery_cfg.phrase,
        tags=set(battery_cfg.tags),
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, theme, parent)
    device_fails(world, a, battery_cfg, theme)

    world.para()
    temptation(world, a, battery_cfg, mistake)
    warning(world, b, a, battery_cfg, mistake)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, battery_cfg)
        outcome = "averted"
    else:
        defy(world, a, mistake)
        world.para()
        if delay == 0:
            interrupt(world, parent, a, battery_cfg, mistake)
            outcome = "interrupted"
        else:
            incident(world, parent, a, battery_cfg, mistake)
            outcome = "incident"
        lesson(world, parent, a, b, battery_cfg, mistake)

    safe_plan(world, parent, a, b, theme, safe_tool)

    world.facts.update(
        theme=theme,
        battery_cfg=battery_cfg,
        mistake=mistake,
        safe_tool=safe_tool,
        instigator=a,
        cautioner=b,
        parent=parent,
        battery=battery,
        relation=relation,
        delay=delay,
        outcome=outcome,
        names={"instigator": instigator, "cautioner": cautioner},
        incident_happened=outcome == "incident",
        interrupted=outcome == "interrupted",
        averted=outcome == "averted",
        predicted_danger=world.facts.get("predicted_danger", 0),
    )
    return world


THEMES = {
    "lighthouse": Theme(
        id="lighthouse",
        scene="a storm-beaten lighthouse",
        rig="A chair became the watchtower, the sofa became a cliff, and a pile of cushions became the crashing sea.",
        team_word="lighthouse",
        goal="the top lamp room",
        dark_spot="the blanket fort under the table",
        tags={"storm", "adventure"},
    ),
    "ship": Theme(
        id="ship",
        scene="a brave rescue ship",
        rig="The sofa became the deck, a broom became the mast, and a blue blanket became the tossing ocean.",
        team_word="ship",
        goal="the captain's cabin",
        dark_spot="the blanket cave behind the sofa",
        tags={"storm", "adventure"},
    ),
    "cave": Theme(
        id="cave",
        scene="a windy treasure cave",
        rig="Two chairs became a rocky gate, a blanket became the cave roof, and a shoe box held their maps.",
        team_word="cave",
        goal="the hidden treasure room",
        dark_spot="the dark little tunnel under the blanket roof",
        tags={"storm", "adventure"},
    ),
}

BATTERIES = {
    "button_cell": BatteryKind(
        id="button_cell",
        label="button battery",
        phrase="a shiny button battery",
        small=True,
        exposed_both=False,
        powers="small toys",
        tags={"battery", "button_battery"},
    ),
    "aa": BatteryKind(
        id="aa",
        label="AA battery",
        phrase="a loose AA battery",
        small=False,
        exposed_both=False,
        powers="flashlights and toys",
        tags={"battery"},
    ),
    "ninevolt": BatteryKind(
        id="ninevolt",
        label="9-volt battery",
        phrase="a square 9-volt battery",
        small=False,
        exposed_both=True,
        powers="alarms and small gadgets",
        tags={"battery", "spark"},
    ),
}

MISTAKES = {
    "coin": Mistake(
        id="coin",
        nickname="treasure coin",
        speech="Look, a silver coin for the lighthouse",
        mode="mouth",
        warning="That is not a coin. It is a battery, and batteries never go in your mouth.",
        lesson="A battery is not treasure and not a snack.",
        requires_small=True,
        tags={"mouth_risk", "battery"},
    ),
    "candy": Mistake(
        id="candy",
        nickname="storm candy",
        speech="It looks like shiny candy for explorers",
        mode="mouth",
        warning="That is not candy. It is a battery, and swallowing one can hurt you badly.",
        lesson="Batteries are never candy, even when they look shiny.",
        requires_small=True,
        tags={"mouth_risk", "battery"},
    ),
    "storm_key": Mistake(
        id="storm_key",
        nickname="storm key",
        speech="Maybe a metal key can wake it up like lightning",
        mode="short",
        warning="That can make a battery spark or get hot.",
        lesson="A battery is not a toy to test with metal.",
        requires_exposed=True,
        tags={"spark", "battery"},
    ),
}

SAFE_TOOLS = {
    "lantern": SafeTool(
        id="lantern",
        phrase="a little camping lantern",
        glow="glowed warm and steady",
        tags={"lantern", "safe_light"},
    ),
    "flashlight": SafeTool(
        id="flashlight",
        phrase="a flashlight",
        glow="clicked on bright as a star",
        tags={"flashlight", "safe_light"},
    ),
    "headlamp": SafeTool(
        id="headlamp",
        phrase="a head-lamp",
        glow="threw a clean circle of light over the whole fort",
        tags={"headlamp", "safe_light"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "sensible", "thoughtful", "curious", "bold"]


@dataclass
class StoryParams:
    theme: str
    battery: str
    mistake: str
    safe_tool: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="lighthouse",
        battery="button_cell",
        mistake="coin",
        safe_tool="lantern",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        delay=1,
    ),
    StoryParams(
        theme="ship",
        battery="button_cell",
        mistake="candy",
        safe_tool="flashlight",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="curious",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
        delay=0,
    ),
    StoryParams(
        theme="cave",
        battery="ninevolt",
        mistake="storm_key",
        safe_tool="headlamp",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        delay=1,
    ),
]


KNOWLEDGE = {
    "battery": [
        (
            "What is a battery?",
            "A battery stores energy and gives power to things like lights and toys. It is useful, but loose batteries should be handled by grown-ups."
        ),
    ],
    "button_battery": [
        (
            "Why are button batteries dangerous for children?",
            "Button batteries are tiny and shiny, so children can mistake them for coins or candy. If one is swallowed, it can hurt the body very badly, so a grown-up should be told right away."
        ),
    ],
    "spark": [
        (
            "Why should metal not touch both ends of a battery?",
            "Metal can let the battery's energy rush out too fast. That can make the battery grow hot or spark."
        ),
    ],
    "storm": [
        (
            "What is a tempest?",
            "A tempest is a strong, noisy storm with wild wind and heavy weather. It is another word for a fierce storm."
        ),
    ],
    "flashlight": [
        (
            "Why is a flashlight a safer way to make light?",
            "A flashlight is made to give light safely. You press a switch instead of touching a loose battery."
        ),
    ],
    "lantern": [
        (
            "What does a camping lantern do?",
            "A camping lantern makes a soft steady light for dark places. It lets people see without using loose parts the wrong way."
        ),
    ],
    "headlamp": [
        (
            "What is a head-lamp?",
            "A head-lamp is a small light you wear on your head. It keeps your hands free while giving safe light."
        ),
    ],
}
KNOWLEDGE_ORDER = ["battery", "button_battery", "spark", "storm", "flashlight", "lantern", "headlamp"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for bid, battery in BATTERIES.items():
            for mid, mistake in MISTAKES.items():
                if battery_matches(battery, mistake):
                    combos.append((theme, bid, mid))
    return combos


def explain_rejection(battery: BatteryKind, mistake: Mistake) -> str:
    if mistake.requires_small and not battery.small:
        return (
            f"(No story: {battery.label} is not the kind a child would mistake for {mistake.nickname}. "
            f"That misunderstanding only makes sense with a tiny battery.)"
        )
    if mistake.requires_exposed and not battery.exposed_both:
        return (
            f"(No story: {mistake.nickname} needs a battery with both terminals close together, "
            f"so touching metal could make it heat or spark. {battery.label.capitalize()} does not fit that danger.)"
        )
    return "(No story: this battery and misunderstanding do not create a clear cautionary hazard.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "interrupted" if params.delay == 0 else "incident"


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    battery = f["battery_cfg"]
    mistake = f["mistake"]
    outcome = f["outcome"]
    prompts = [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "battery" and "tempest".',
        f"Tell a cautionary indoor adventure where {a.label} and {b.label} play through a storm, a loose {battery.label} is misunderstood, and a grown-up teaches the safe rule.",
    ]
    if outcome == "averted":
        prompts.append(
            f"Write a near-miss story where an older child stops a misunderstanding about a {battery.label} before anything happens, and the adventure continues with safe light."
        )
    elif outcome == "interrupted":
        prompts.append(
            f"Write a gentle cautionary story where a child starts to use a {battery.label} the wrong way because of a misunderstanding, but a grown-up interrupts in time."
        )
    else:
        prompts.append(
            f"Write a cautionary story where a misunderstanding about a {battery.label} leads to one scary moment before the grown-up steps in, and end with calm safe light."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    battery = f["battery_cfg"]
    mistake = f["mistake"]
    tool = f["safe_tool"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, playing an adventure during a tempest. {a.label}'s {parent.label_word} is the grown-up who helps them choose the safe way."
        ),
        (
            "What was the problem in the story?",
            f"Their pretend adventure went dark when the toy light had no power, and {a.label} found a loose {battery.label}. Because of a misunderstanding, {a.pronoun('subject')} thought the battery could help in a way that was not safe."
        ),
        (
            f"Why did {b.label} warn {a.label}?",
            f"{b.label} understood that the loose {battery.label} was dangerous to use that way. The warning came from the real risk behind the misunderstanding, not from trying to spoil the game."
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                f"What changed after {b.label} spoke?",
                f"{a.label} listened and put the battery down instead of using it. That stopped the danger before it began, so the adventure could continue safely."
            )
        )
    elif f["outcome"] == "interrupted":
        out.append(
            (
                f"How did {parent.label_word} help?",
                f"{parent.label_word.capitalize()} crossed the room quickly, took the loose battery away, and explained that only grown-ups should handle it. The danger ended before the battery touched {a.label} or metal the wrong way."
            )
        )
    else:
        if mistake.mode == "mouth":
            detail = f"The battery touched {a.label}'s lips for a moment, which made the danger feel real right away."
        else:
            detail = "The battery sparked and grew warm when metal touched it the wrong way."
        out.append(
            (
                "What was the scary moment?",
                f"{detail} Then {parent.label_word} stepped in, took it away, and put it high out of reach. That quick help turned the mistake into a lesson instead of a bigger accident."
            )
        )
    out.append(
        (
            "How did the story end?",
            f"It ended with {tool.phrase} lighting the fort safely while the tempest still rumbled outside. The last picture shows the children calm and careful, because they now knew that a loose battery is not part of the game."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["battery_cfg"].tags) | set(f["mistake"].tags) | set(f["theme"].tags) | set(f["safe_tool"].tags)
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
hazard(B, M) :- battery(B), mistake(M), needs_small(M), small(B).
hazard(B, M) :- battery(B), mistake(M), needs_exposed(M), exposed_both(B).
valid(T, B, M) :- theme(T), hazard(B, M).

% --- outcome model ----------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
authority(C + 4) :- init_caution(C), older_sibling.
averted :- authority(A), bravery_init(B), A > B.

outcome(averted) :- averted.
outcome(interrupted) :- not averted, delay(0).
outcome(incident) :- not averted, delay(1).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for bid, battery in BATTERIES.items():
        lines.append(asp.fact("battery", bid))
        if battery.small:
            lines.append(asp.fact("small", bid))
        if battery.exposed_both:
            lines.append(asp.fact("exposed_both", bid))
    for mid, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mid))
        if mistake.requires_small:
            lines.append(asp.fact("needs_small", mid))
        if mistake.requires_exposed:
            lines.append(asp.fact("needs_exposed", mid))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        saved = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = saved
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a storm adventure, a loose battery, and a misunderstanding. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--battery", choices=BATTERIES)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--safe-tool", dest="safe_tool", choices=SAFE_TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = adult interrupts in time, 1 = one scary moment happens first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.battery and args.mistake:
        battery = BATTERIES[args.battery]
        mistake = MISTAKES[args.mistake]
        if not battery_matches(battery, mistake):
            raise StoryError(explain_rejection(battery, mistake))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.battery is None or combo[1] == args.battery)
        and (args.mistake is None or combo[2] == args.mistake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, battery, mistake = rng.choice(sorted(combos))
    safe_tool = args.safe_tool or rng.choice(sorted(SAFE_TOOLS))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        theme=theme,
        battery=battery,
        mistake=mistake,
        safe_tool=safe_tool,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.battery not in BATTERIES:
        raise StoryError(f"(Invalid battery: {params.battery})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Invalid mistake: {params.mistake})")
    if params.safe_tool not in SAFE_TOOLS:
        raise StoryError(f"(Invalid safe tool: {params.safe_tool})")

    battery = BATTERIES[params.battery]
    mistake = MISTAKES[params.mistake]
    if not battery_matches(battery, mistake):
        raise StoryError(explain_rejection(battery, mistake))
    if params.delay not in {0, 1}:
        raise StoryError("(Delay must be 0 or 1.)")

    world = tell(
        THEMES[params.theme],
        battery,
        mistake,
        SAFE_TOOLS[params.safe_tool],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        delay=params.delay,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, battery, mistake) combos:\n")
        for theme, battery, mistake in combos:
            print(f"  {theme:10} {battery:11} {mistake}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.battery} + {p.mistake} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
