#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/efficiency_awning_icy_sidewalk_happy_ending_cautionary.py

A standalone storyworld about two children on an icy sidewalk who are tempted by
a quick, "efficient" shortcut under an awning. The world enforces a simple
common-sense rule: a speed-first move on slick ice can cause a fall, and only
reasonable responses count as valid fixes.

The tone stays close to a cautionary pretend-play tale: a playful setup, a
tempting bad idea, a grounded warning, a state-driven turn, and then either a
safe bright ending or a sober cautionary one.
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible"}


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
    icy: bool = False
    supports_walking: bool = True
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
    titles: tuple[str, str]
    mission: str
    role_plural: str
    send_off: str


@dataclass
class Shortcut:
    id: str
    idea: str
    motion: str
    boast: str
    speed: int
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    awning: str
    source: str
    slickness: int
    icy: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_danger(world: World) -> list[str]:
    patch = world.get("patch")
    if patch.meters["slid_on"] < THRESHOLD:
        return []
    sig = ("danger", patch.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sidewalk").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__slip__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(shortcut: Shortcut, hazard: Hazard) -> bool:
    return shortcut.risk > 0 and hazard.icy and hazard.slickness > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def slip_severity(shortcut: Shortcut, hazard: Hazard, delay: int) -> int:
    return shortcut.risk + hazard.slickness + delay


def is_contained(response: Response, shortcut: Shortcut, hazard: Hazard, delay: int) -> bool:
    return response.power >= slip_severity(shortcut, hazard, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLDNESS_INIT


def predict_slip(world: World) -> dict:
    sim = world.copy()
    patch = sim.get("patch")
    patch.meters["slid_on"] += 1
    sim.get("instigator").meters["off_balance"] += 1
    propagate(sim, narrate=False)
    severity = slip_severity(
        SHORTCUTS[sim.facts["shortcut"].id],
        HAZARDS[sim.facts["hazard"].id],
        sim.facts["delay"],
    )
    return {
        "danger": sim.get("sidewalk").meters["danger"],
        "would_slip": sim.get("instigator").meters["off_balance"] >= THRESHOLD,
        "severity": severity,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, hazard: Hazard) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    captain, mate = theme.titles
    world.say(
        f"On a bright winter afternoon, {a.id} and {b.id} turned the icy sidewalk into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f"The {hazard.awning} hung over one part of the walk, and meltwater from it had frozen into "
        f"{hazard.source}."
    )
    world.say(
        f'"{captain} {a.id} and {mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s finish {theme.mission}!"'
    )


def mission_need(world: World, b: Entity, theme: Theme, hazard: Hazard) -> None:
    world.say(
        f"They had to pass {hazard.the} to reach the corner, where the game said the treasure waited."
    )
    world.say(
        f'{b.id} looked at the shine on the ground. "{hazard.The} looks slippery," '
        f'{b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, shortcut: Shortcut, hazard: Hazard) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed at {hazard.the}. "I know a faster way," {a.pronoun()} said. '
        f'"We can {shortcut.idea}. It will be pure efficiency!"'
    )
    world.say(shortcut.boast)


def warn(world: World, b: Entity, a: Entity, hazard: Hazard, parent: Entity) -> None:
    pred = predict_slip(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_severity"] = pred["severity"]
    b.memes["caution"] += 1
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} shook {b.pronoun('possessive')} head, already sure the shiny ice would throw someone down."
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, no. Ice like that forms when drips fall from '
        f'the {hazard.awning}. Fast feet slip on it, and {parent.label_word} said shiny winter ice can fool you."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, theme: Theme, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    sib = "brother" if b.type == "boy" else "sister"
    world.say(
        f'"Maybe fast is not best," {a.id} admitted. Because {b.id} was {a.pronoun("possessive")} big {sib}, '
        f'{a.id} listened and stepped back from the ice.'
    )
    world.say(
        f"Instead, they called to {parent.label_word.capitalize()} and took the longer snowy edge where boots could grip."
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Don\'t worry," {a.id} said. "I know how." And because {a.id} was {b.pronoun("possessive")} {rel}, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Don\'t worry," {a.id} said, and darted toward the shining strip.')


def slip(world: World, a: Entity, b: Entity, shortcut: Shortcut, hazard: Hazard) -> None:
    patch = world.get("patch")
    patch.meters["slid_on"] += 1
    a.meters["off_balance"] += 1
    a.meters["cold"] += 1
    world.get("bag").meters["dropped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} tried to {shortcut.motion} across {hazard.the}. For one blink it looked clever. "
        f"Then one boot skated away, both arms flew up, and down {a.pronoun()} went."
    )
    world.say(
        f"The paper bag bumped the ice, a bun rolled free, and the game stopped feeling like a game."
    )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, a: Entity, theme: Theme) -> None:
    world.get("patch").meters["slid_on"] = 0.0
    world.get("sidewalk").meters["danger"] = 0.0
    a.meters["off_balance"] = 0.0
    a.memes["fear"] = 0.0
    world.say(f"{parent.label_word.capitalize()} came quickly and {response.text}.")
    world.say(
        f"Soon the slick strip looked dull instead of glassy, and the little {theme.role_plural} could stand steady again."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside them and brushed the ice from their coats. "
        f'"I am glad you called me," {parent.pronoun()} said softly. "Efficiency is not the same as rushing. '
        f'The fastest trip is the one where everybody gets there safely."'
    )
    world.say(f'"We know," whispered {a.id} and {b.id}.')


def safe_end(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} showed them how to look for the rough, snowy side of a winter path instead of the shiny side."
    )
    world.say(
        f"{a.id} squeezed {b.id}'s mitten, and together they took slow captain steps past the awning."
    )
    world.say(
        f"This time the {theme.role_plural} {theme.send_off} -- not faster, but wiser, warm, and safe."
    )


def rescue_fail(world: World, parent: Entity, response: Response, a: Entity, hazard: Hazard) -> None:
    world.get("sidewalk").meters["danger"] += 1
    a.meters["bruise"] += 1
    a.meters["cold"] += 1
    world.say(f"{parent.label_word.capitalize()} hurried over and {response.fail}.")
    world.say(
        f"But {hazard.the} was still slick, and everyone had to pick careful, tiny steps around it while {a.id} fought back tears."
    )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} held them close under the awning until the shaking stopped. "
        f'"You are safe, and that matters most," {parent.pronoun()} whispered.'
    )
    world.say(
        "The warm buns were squashed, one knee throbbed, and the walk home felt much longer than any careful detour would have."
    )
    world.say(
        "After that, whenever a winter shortcut looked too shiny, they chose the slower edge and remembered that rushing can waste the very time it tries to save."
    )


def tell(
    theme: Theme,
    shortcut: Shortcut,
    hazard: Hazard,
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="sidewalk", type="sidewalk", label="the icy sidewalk"))
    patch = world.add(Entity(
        id="patch",
        type="ice_patch",
        label=hazard.label,
        phrase=hazard.the,
        icy=hazard.icy,
        tags=set(hazard.tags),
    ))
    bag = world.add(Entity(id="bag", type="bag", label="paper bag", phrase="a paper bag of warm buns"))

    a.memes["bravery"] = BOLDNESS_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    world.facts["theme"] = theme
    world.facts["shortcut"] = shortcut
    world.facts["hazard"] = hazard
    world.facts["response"] = response
    world.facts["delay"] = delay

    play_setup(world, a, b, theme, hazard)
    mission_need(world, b, theme, hazard)

    world.para()
    tempt(world, a, shortcut, hazard)
    warn(world, b, a, hazard, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, theme, parent)
        world.para()
        safe_end(world, parent, a, b, theme)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        defy(world, a, b, shortcut)
        world.para()
        slip(world, a, b, shortcut, hazard)
        alarm(world, b, a, parent)
        severity = slip_severity(shortcut, hazard, delay)
        contained = is_contained(response, shortcut, hazard, delay)
        world.para()
        if contained:
            rescue(world, parent, response, a, theme)
            lesson(world, parent, a, b)
            world.para()
            safe_end(world, parent, a, b, theme)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, a, hazard)
            grim_lesson(world, parent, a, b)
            outcome = "hard_fall"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        patch=patch,
        bag=bag,
        relation=relation,
        outcome=outcome,
        severity=severity,
        rescued=contained,
        slipped=bag.meters["dropped"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "captains": Theme(
        id="captains",
        scene="a frozen harbor full of silver water",
        rig="The snowbanks were sea walls, their boot prints were little docks, and the paper bag of warm buns was precious cargo from the bakery ship.",
        titles=("Captain", "Lookout"),
        mission="the harbor run before the buns got cold",
        role_plural="captains",
        send_off="made their careful crossing",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a glittering ice kingdom",
        rig="The snowbanks were mountains, the curb was a cliff, and the paper bag of warm buns was a supply sack for the long trek.",
        titles=("Leader", "Scout"),
        mission="the mountain trail before the snow giants woke",
        role_plural="explorers",
        send_off="went on with their expedition",
    ),
    "messengers": Theme(
        id="messengers",
        scene="a winter city of secret routes",
        rig="The mailbox was a red tower, the streetlamp was a beacon, and the paper bag of warm buns was an important delivery bundle.",
        titles=("Chief", "Runner"),
        mission="their delivery route to the safe gate",
        role_plural="messengers",
        send_off="finished their mission",
    ),
}

SHORTCUTS = {
    "dash": Shortcut(
        id="dash",
        idea="dash straight under the awning instead of taking the rough snowy edge",
        motion="dash",
        boast="For one breath, the shortcut sounded smart simply because it was short.",
        speed=3,
        risk=2,
        tags={"ice", "efficiency"},
    ),
    "slide": Shortcut(
        id="slide",
        idea="slide across the smooth part like skaters",
        motion="slide",
        boast="The quick idea glittered in the air the way bad winter ideas sometimes do.",
        speed=4,
        risk=3,
        tags={"ice", "slide", "efficiency"},
    ),
    "hop": Shortcut(
        id="hop",
        idea="hop from one shiny spot to the next and save time",
        motion="hop",
        boast="It sounded almost playful, which made the risk easy to miss.",
        speed=2,
        risk=2,
        tags={"ice", "efficiency"},
    ),
}

HAZARDS = {
    "bakery_awning": Hazard(
        id="bakery_awning",
        label="bakery ice strip",
        the="the icy strip under the bakery awning",
        awning="bakery awning",
        source="a long, glassy strip where drips had frozen",
        slickness=3,
        icy=True,
        tags={"awning", "ice", "sidewalk", "bakery"},
    ),
    "library_awning": Hazard(
        id="library_awning",
        label="library ice patch",
        the="the icy patch under the library awning",
        awning="library awning",
        source="a hard patch of ice made by slow drips from the roof edge",
        slickness=2,
        icy=True,
        tags={"awning", "ice", "sidewalk"},
    ),
    "market_awning": Hazard(
        id="market_awning",
        label="market ice ribbon",
        the="the narrow ice ribbon under the market awning",
        awning="market awning",
        source="a clear ribbon of ice where slush had frozen again",
        slickness=2,
        icy=True,
        tags={"awning", "ice", "sidewalk"},
    ),
    "dry_stones": Hazard(
        id="dry_stones",
        label="dry stone strip",
        the="the dry stone strip by the wall",
        awning="stone overhang",
        source="a rough dry strip with no frozen drips at all",
        slickness=0,
        icy=False,
        tags={"sidewalk"},
    ),
}

RESPONSES = {
    "salt_and_hand": Response(
        id="salt_and_hand",
        sense=3,
        power=5,
        text="shook out a scoop of salt, scraped the worst shine with a boot, and held out a steady hand",
        fail="sprinkled a little salt and reached for a hand, but the ice was already too wide and slick to fix quickly",
        qa_text="spread salt on the ice and gave the children a steady hand",
        tags={"salt", "ice"},
    ),
    "detour_and_hold": Response(
        id="detour_and_hold",
        sense=3,
        power=4,
        text="guided them around the icy strip and kept one warm hand wrapped around each mitten",
        fail="tried to guide them around it, but there was too little room and the slick edge still caught their boots",
        qa_text="led them around the icy strip while holding their hands",
        tags={"detour", "ice"},
    ),
    "sand_then_walk": Response(
        id="sand_then_walk",
        sense=2,
        power=3,
        text="sprinkled gritty sand over the patch and tested each step before letting them pass",
        fail="threw down a little sand, but the smooth ice underneath stayed too slippery",
        qa_text="covered the patch with sand so their boots could grip",
        tags={"sand", "ice"},
    ),
    "hurry_them": Response(
        id="hurry_them",
        sense=1,
        power=1,
        text="told them to run across before the cold got worse",
        fail="urged them to hurry across, which only made the slippery patch feel worse",
        qa_text="told them to hurry across",
        tags={"ice"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "cautious", "sensible", "thoughtful", "steady"]


@dataclass
class StoryParams:
    theme: str
    shortcut: str
    hazard: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="captains",
        shortcut="slide",
        hazard="bakery_awning",
        response="salt_and_hand",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="explorers",
        shortcut="dash",
        hazard="library_awning",
        response="detour_and_hold",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="messengers",
        shortcut="slide",
        hazard="market_awning",
        response="sand_then_walk",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        theme="captains",
        shortcut="dash",
        hazard="bakery_awning",
        response="salt_and_hand",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Tom",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=3,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for shortcut_id, shortcut in SHORTCUTS.items():
            for hazard_id, hazard in HAZARDS.items():
                if hazard_at_risk(shortcut, hazard):
                    combos.append((theme_id, shortcut_id, hazard_id))
    return combos


KNOWLEDGE = {
    "awning": [
        (
            "What is an awning?",
            "An awning is a little roof that sticks out over a door or window. It can drip water that later freezes in winter."
        )
    ],
    "ice": [
        (
            "Why is shiny sidewalk ice slippery?",
            "Smooth ice gives your boots very little grip, so your feet can slide away. That is why winter walkers take slow steps on it."
        )
    ],
    "salt": [
        (
            "Why do people put salt on icy sidewalks?",
            "Salt helps melt ice and makes the surface less slick. Grown-ups use it to make walking safer."
        )
    ],
    "sand": [
        (
            "Why would someone throw sand on ice?",
            "Sand does not melt ice much, but it makes a rougher surface for boots to grip. That can help people walk more safely."
        )
    ],
    "detour": [
        (
            "Why is a detour sometimes faster in winter?",
            "A safe longer path can be faster than a dangerous short one if the short path makes you slip or stop. In winter, careful steps save time."
        )
    ],
    "efficiency": [
        (
            "What does efficiency mean?",
            "Efficiency means doing something in a way that works well without wasting time or effort. But in a winter story, safe efficiency means choosing the method that gets everyone there without a fall."
        )
    ],
}
KNOWLEDGE_ORDER = ["awning", "ice", "salt", "sand", "detour", "efficiency"]


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
    shortcut = f["shortcut"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a winter safety story for a 3-to-5-year-old where two children playing {theme.role_plural} face an icy sidewalk and the word "awning" appears.',
            f"Tell a near-miss story where {a.id} wants to use a quick shortcut for efficiency under {hazard.awning}, but {b.id} talks {a.pronoun('object')} out of it before anyone falls.",
            'Write a gentle cautionary story that includes the word "efficiency" and ends happily because the children choose careful steps over a winter shortcut.',
        ]
    if outcome == "hard_fall":
        return [
            f'Write a cautionary winter story with the words "efficiency" and "awning" where children on an icy sidewalk choose a bad shortcut.',
            f"Tell a story where {a.id} ignores {b.id}'s warning and slips on ice under {hazard.awning}, learning that a rushed shortcut can waste time instead of saving it.",
            "Write a child-facing story with a sober ending: nobody is lost, but a fall on winter ice makes the lesson unforgettable.",
        ]
    return [
        f'Write a winter safety story for a 3-to-5-year-old that includes the words "efficiency" and "awning" and takes place on an icy sidewalk.',
        f"Tell a playful cautionary story where {a.id} wants a fast shortcut under {hazard.awning}, but after a slip a calm grown-up helps and the ending turns safe and bright.",
        f"Write a simple story about two children playing {theme.role_plural} who learn that safe steps are better than rushed steps on ice.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    shortcut = f["shortcut"]
    hazard = f["hazard"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be {theme.role_plural} on an icy sidewalk. {a.id}'s {pw} also had to help when the shortcut idea turned risky."
        ),
        (
            "What was the dangerous place in the story?",
            f"The dangerous place was {hazard.the}. It was slippery because winter drips from the {hazard.awning} had frozen there."
        ),
        (
            f"Why did {a.id} think the shortcut was a good idea?",
            f"{a.id} thought the shortcut would save time and called it efficiency. The idea felt smart because it was short, even though the ice made it unsafe."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because shiny ice under the awning looked slick and dangerous. {b.pronoun().capitalize()} understood that fast feet can slide when winter drips freeze on the sidewalk."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} listened and stepped back from the ice, so nobody fell. They chose the rough snowy edge instead, which solved the problem before it started."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the children walking carefully past the awning and finishing their game safely. The ending proves they changed because they now looked for the grippy side of the path instead of the shiny side."
            )
        )
    elif f["outcome"] == "contained":
        body = response.qa_text
        qa.append(
            (
                f"How did {a.id}'s {pw} help after the slip?",
                f"{pw.capitalize()} {body}. That calm help changed the icy shortcut from a danger into a safer crossing."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                "They learned that efficiency is not the same as rushing. A safe method may look slower at first, but it gets everyone there without a fall."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children taking slow captain steps past the awning and going on safely. The final image shows that they were still playful, but now they were wiser too."
            )
        )
    else:
        qa.append(
            (
                "What went wrong in the cautionary ending?",
                f"The ice stayed too slick, so the help did not fully solve the problem right away. One knee hurt, the warm buns were squashed, and the walk home became slower and sadder than the shortcut was meant to be."
            )
        )
        qa.append(
            (
                "What did the children learn from the hard fall?",
                "They learned that rushing on winter ice can waste the very time it tries to save. After that, they chose slower, safer paths whenever a shortcut looked too shiny."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"awning", "ice", "efficiency"}
    for tag in f["response"].tags:
        if tag in {"salt", "sand", "detour"}:
            tags.add(tag)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("icy", ent.icy), ("supports_walking", ent.supports_walking)) if on and name != "supports_walking"]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(shortcut: Shortcut, hazard: Hazard) -> str:
    if not hazard.icy:
        return (
            f"(No story: {hazard.the} is not icy, so {shortcut.idea} would not create the winter slip this world depends on. "
            f"Pick a real ice hazard, especially one formed under an awning.)"
        )
    if shortcut.risk <= 0:
        return "(No story: this shortcut is not risky enough to drive the cautionary turn.)"
    return "(No story: this combination has no believable slip risk.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    shortcut = SHORTCUTS[params.shortcut]
    hazard = HAZARDS[params.hazard]
    return "contained" if is_contained(response, shortcut, hazard, params.delay) else "hard_fall"


ASP_RULES = r"""
hazard(S, H) :- shortcut(S), hazard_place(H), risky(S), icy(H).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, S, H) :- theme(T), shortcut(S), hazard_place(H), hazard(S, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(BI), A > BI.

severity(Ri + Sl + D) :- chosen_shortcut(S), risk(S, Ri), chosen_hazard(H), slickness(H, Sl), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(hard_fall) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("risk", sid, shortcut.risk))
        if shortcut.risk > 0:
            lines.append(asp.fact("risky", sid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard_place", hid))
        lines.append(asp.fact("slickness", hid, hazard.slickness))
        if hazard.icy:
            lines.append(asp.fact("icy", hid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_shortcut", params.shortcut),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: icy sidewalk, awning drips, a tempting shortcut, and a safer way."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help takes to settle the icy problem")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and not HAZARDS[args.hazard].icy:
        shortcut = SHORTCUTS[args.shortcut] if args.shortcut else next(iter(SHORTCUTS.values()))
        raise StoryError(explain_rejection(shortcut, HAZARDS[args.hazard]))
    if args.shortcut and args.hazard:
        shortcut = SHORTCUTS[args.shortcut]
        hazard = HAZARDS[args.hazard]
        if not hazard_at_risk(shortcut, hazard):
            raise StoryError(explain_rejection(shortcut, hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, shortcut_id, hazard_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme_id,
        shortcut=shortcut_id,
        hazard=hazard_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    shortcut = SHORTCUTS[params.shortcut]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    if not hazard_at_risk(shortcut, hazard):
        raise StoryError(explain_rejection(shortcut, hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        THEMES[params.theme],
        shortcut,
        hazard,
        response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, shortcut, hazard) combos:\n")
        for theme_id, shortcut_id, hazard_id in combos:
            print(f"  {theme_id:10} {shortcut_id:8} {hazard_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.shortcut} at {p.hazard} ({p.theme}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
