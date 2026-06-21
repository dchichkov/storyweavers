#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wick_mocha_rhyme_cautionary_inner_monologue_space.py
===============================================================================

A standalone storyworld for a tiny "space adventure in a bedroom fort" domain.

A child and a sibling or friend turn blankets and boxes into a spaceship. The
cockpit grows dark, and the bold child is tempted to light a real candle wick to
make the ship feel "space-real." The world model decides whether the other child
can talk them out of it, whether a small fire starts, and whether a grown-up can
stop it in time. The prose includes a few gentle rhyming lines and moments of
inner monologue, but the plot is driven by simulated state rather than a fixed
template.

Run it
------
    python storyworlds/worlds/gpt-5.4/wick_mocha_rhyme_cautionary_inner_monologue_space.py
    python storyworlds/worlds/gpt-5.4/wick_mocha_rhyme_cautionary_inner_monologue_space.py --all
    python storyworlds/worlds/gpt-5.4/wick_mocha_rhyme_cautionary_inner_monologue_space.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/wick_mocha_rhyme_cautionary_inner_monologue_space.py --qa
    python storyworlds/worlds/gpt-5.4/wick_mocha_rhyme_cautionary_inner_monologue_space.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    flammable: bool = False
    makes_flame: bool = False
    gives_light: bool = False
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
class Mission:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    dark_spot: str
    place_word: str
    sendoff: str


@dataclass
class ForbiddenLight:
    id: str
    label: str
    phrase: str
    where: str
    wick_line: str
    scent: str
    cry: str
    strike: str
    not_toy: str
    plural: bool = False
    makes_flame: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    near: str
    dress: str
    spread: int = 2
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [
    Rule(name="spread", tag="physical", apply=_r_spread),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(forbidden: ForbiddenLight, target: Target) -> bool:
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {
        "ignites": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def setup_scene(world: World, a: Entity, b: Entity, mission: Mission) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After supper, {a.id} and {b.id} turned the bedroom into {mission.scene}. "
        f"{mission.rig}"
    )
    world.say(
        f'"{mission.title_a} {a.id} and {mission.title_b} {b.id}!" {a.id} cried. '
        f'"Set a course for {mission.goal}!"'
    )
    world.say(
        'They whispered a launch rhyme: "Zoom through the room, past shadow and gloom."'
    )


def mention_mocha(world: World) -> None:
    world.say(
        "On the desk nearby sat a mug of mocha, sending up a sweet, sleepy smell while the stars on the curtains winked."
    )


def dark_need(world: World, b: Entity, mission: Mission, target: Target) -> None:
    world.say(
        f"But the {mission.place_word} -- {mission.dark_spot}, {target.dress} -- looked black as the far side of the moon."
    )
    world.say(f'"We need a beacon," {b.id} said softly.')
    world.say(
        f'In {b.id}\'s head came a quick brave song: "Dark is deep, but promises keep."'
    )


def tempt(world: World, a: Entity, forbidden: ForbiddenLight) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} looked toward {forbidden.where}. "I know," {a.pronoun()} said. '
        f'"{forbidden.cry} We could light {forbidden.phrase}."'
    )
    world.say(
        f'In {a.id}\'s head, a daring thought zipped by: Maybe one tiny wick could make the ship feel real.'
    )


def warn(world: World, b: Entity, a: Entity, forbidden: ForbiddenLight, target: Target, parent: Entity) -> None:
    pred = predict_fire(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} hugged the control box to {b.pronoun('possessive')} chest and did not smile at all."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. {parent.label_word.capitalize()} said real flames are for grown-ups. '
        f'{forbidden.wick_line}, and {target.the} could catch."{extra}'
    )
    world.say(
        f'In {b.id}\'s head came the warning clear as a radio ping: If the flame wakes, the game could break.'
    )


def defy(world: World, a: Entity, b: Entity, forbidden: ForbiddenLight) -> None:
    a.memes["defiance"] += 1
    if a.attrs.get("relation") == "siblings" and a.age > b.age:
        world.say(
            f'"It will only be for a blink," {a.id} said. Because {a.id} was the older one, {b.id} hesitated and did not stop {a.pronoun("object")}.'
        )
    else:
        world.say(f'"It will only be for a blink," {a.id} said, and reached for it anyway.')


def back_down(world: World, a: Entity, b: Entity, forbidden: ForbiddenLight, parent: Entity, mission: Mission) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} stared at the dark fort and thought, In space, smart is part of brave. Then {a.pronoun()} let {forbidden.phrase} alone.'
    )
    world.say(
        f'"You are right," {a.id} admitted. "A mission is no good if it burns the ship."'
    )
    world.say(
        f'Together they called to {parent.label_word.capitalize()} and said the {mission.place_word} needed safe light instead.'
    )
    world.say(
        'They made up a softer rhyme: "Glow, not flame; play the game."'
    )


def ignite(world: World, target_ent: Entity, forbidden: ForbiddenLight, target: Target) -> None:
    _do_forbidden(world, target_ent)
    world.say(
        f"{forbidden.strike} The little flame kissed the wick. For one second the light looked golden and spacey, and the air smelled of {forbidden.scent}. Then the flame leaned toward {target.near}, and a bright bite of orange began to crawl."
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"{a.id}! {target.The} is on fire!" {b.id} shouted.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target, mission: Mission) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {response.text.replace('{target}', target.label)}."
    )
    world.say(
        f"Soon the orange snap was gone. Only a smoky curl, a singed edge, and two quiet astronauts were left in the fort."
    )
    world.say(
        'The room seemed to sigh: "No more spark in the dark."'
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: ForbiddenLight) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f'{parent.label_word.capitalize()} knelt beside the fort. "I am glad you called me fast," {parent.pronoun()} said. '
        f'"But remember this: {forbidden.not_toy}. A tiny flame can run bigger than a little game."'
    )
    world.say(
        f'In {a.id}\'s head came a heavy, honest thought: I wanted the ship to shine, and nearly made it dangerous instead.'
    )
    world.say(f'"We understand," {a.id} and {b.id} said together.')


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, mission: Mission, l1: SafeLight, l2: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next evening, {parent.label_word.capitalize()} brought {l1.phrase} and {l2.phrase}."
    )
    world.say(
        f'"A real crew uses safe tools," {parent.pronoun()} said with a smile.'
    )
    world.say(
        f'{b.id} clicked on the {l1.label}, and {a.id} lifted the {l2.label}. {l1.glow}, while {l2.glow}.'
    )
    world.say(
        'They sang, "Bright and right, starry night," and the fort became a spaceship again.'
    )
    world.say(
        f"This time they {mission.sendoff}, and the new glow proved what had changed: they wanted wonder, but they chose safety first."
    )


def rescue_fail(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    target_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {response.fail.replace('{target}', target.label)}."
    )
    world.say(
        f"But the fire skipped from {target.the} to the fort wall and then to the rug, hot and hungry."
    )


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity, mission: Mission) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} swept the children out into the hall before the smoke could grow thicker."
    )
    world.say(
        "They watched from the doorway as grown-ups stamped out the last angry sparks and opened the windows wide."
    )
    world.say(
        f"The cardboard cockpit was ruined. Their little {mission.place_word} was only a wet, gray heap now."
    )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: ForbiddenLight) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} hugged them tight and said, "You are safe, and that matters most."'
    )
    world.say(
        f"{a.id} thought, I wanted adventure, not ashes. {forbidden.not_toy[0].upper()}{forbidden.not_toy[1:]}, and that truth stayed with both children."
    )
    world.say(
        'After that, whenever a mission needed light, they used the rule they could still recite: "Glow, not flame; play the game."'
    )


def tell(
    mission: Mission,
    forbidden: ForbiddenLight,
    target: Target,
    lights: tuple[SafeLight, SafeLight],
    response: Response,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    cautioner: str = "Milo",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"relation": relation, "trust": trust},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(Entity(id="room", type="room", label="the room"))
    tool = world.add(
        Entity(
            id="tool",
            type="tool",
            label=forbidden.label,
            phrase=forbidden.phrase,
            makes_flame=True,
        )
    )
    tgt = world.add(
        Entity(
            id="target",
            type="target",
            label=target.label,
            phrase=target.the,
            flammable=target.flammable,
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    setup_scene(world, a, b, mission)
    mention_mocha(world)
    dark_need(world, b, mission, target)

    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, target, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, forbidden, parent, mission)
        world.para()
        safe_gift(world, parent, a, b, mission, lights[0], lights[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b, forbidden)
        world.para()
        ignite(world, tgt, forbidden, target)
        alarm(world, b, a, target, parent)
        severity = fire_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue(world, parent, response, tgt, target, mission)
            lesson(world, parent, a, b, forbidden)
            world.para()
            safe_gift(world, parent, a, b, mission, lights[0], lights[1])
        else:
            rescue_fail(world, parent, response, tgt, target)
            escape_and_loss(world, parent, a, b, mission)
            grim_lesson(world, parent, a, b, forbidden)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        mission=mission,
        forbidden=forbidden,
        target_cfg=target,
        target=tgt,
        tool=tool,
        lights=lights,
        response=response,
        ignited=tgt.meters["scorched"] >= THRESHOLD,
        outcome=outcome,
        rescued=contained,
        severity=severity,
        delay=delay,
        relation=relation,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "moon": Mission(
        id="moon",
        scene="a silver moon ship",
        rig="A blanket over two chairs became the hull, a laundry basket became the engine pod, and a shoebox full of crayons became the star controls.",
        title_a="Captain",
        title_b="Navigator",
        goal="the Moon Crater Sea",
        dark_spot="under the blanket roof",
        place_word="cockpit",
        sendoff="flew toward the Moon Crater Sea",
    ),
    "mars": Mission(
        id="mars",
        scene="a red-dust rover",
        rig="A cardboard box became the rover, pillows became crater rocks, and a string of socks became a line of floating comets.",
        title_a="Captain",
        title_b="Scout",
        goal="the red hills of Mars",
        dark_spot="inside the box rover",
        place_word="cabin",
        sendoff="rumbled across the red hills of Mars",
    ),
    "comet": Mission(
        id="comet",
        scene="a comet chaser",
        rig="A blanket fort became the ship, a broom became an antenna, and paper circles on the floor became icy comets to dodge.",
        title_a="Commander",
        title_b="Pilot",
        goal="the shining comet tail",
        dark_spot="inside the blanket fort",
        place_word="bridge",
        sendoff="sailed past the shining comet tail",
    ),
}

FORBIDDEN = {
    "mocha_candle": ForbiddenLight(
        id="mocha_candle",
        label="mocha candle",
        phrase="the mocha candle",
        where="the shelf by the desk",
        wick_line="Its wick is real, even if it smells sweet like mocha",
        scent="mocha",
        cry="That mocha candle!",
        strike="Ffft!",
        not_toy="candle wicks are not for children to light",
        plural=False,
        tags={"candle", "wick", "mocha", "fire", "call_adult"},
    ),
    "star_candle": ForbiddenLight(
        id="star_candle",
        label="star candle",
        phrase="the star candle",
        where="the shelf by the desk",
        wick_line="Its wick is real, even if the jar has stars on it",
        scent="mocha from the mug on the desk",
        cry="That star candle!",
        strike="Ffft!",
        not_toy="candle wicks are not for children to light",
        plural=False,
        tags={"candle", "wick", "mocha", "fire", "call_adult"},
    ),
    "lantern_candle": ForbiddenLight(
        id="lantern_candle",
        label="camp candle",
        phrase="the camp candle",
        where="the dresser",
        wick_line="Its wick still makes a real flame",
        scent="mocha from the nearby mug",
        cry="That camp candle!",
        strike="Ffft!",
        not_toy="candle wicks are not for children to light",
        plural=False,
        tags={"candle", "wick", "mocha", "fire", "call_adult"},
    ),
}

TARGETS = {
    "chart": Target(
        id="chart",
        label="paper star chart",
        the="the paper star chart",
        near="the edge of the paper star chart",
        dress="lined with a paper star chart",
        spread=2,
        flammable=True,
        tags={"paper", "chart", "flammable"},
    ),
    "blanket": Target(
        id="blanket",
        label="blanket wall",
        the="the blanket wall",
        near="the hanging blanket wall",
        dress="walled with an old blanket",
        spread=3,
        flammable=True,
        tags={"blanket", "flammable"},
    ),
    "cardboard": Target(
        id="cardboard",
        label="cardboard control panel",
        the="the cardboard control panel",
        near="the cardboard control panel",
        dress="trimmed with a cardboard control panel",
        spread=2,
        flammable=True,
        tags={"cardboard", "flammable"},
    ),
    "metal": Target(
        id="metal",
        label="metal toy chest",
        the="the metal toy chest",
        near="the metal toy chest",
        dress="backed by a cool metal toy chest",
        spread=0,
        flammable=False,
        tags={"metal"},
    ),
}

SAFE_LIGHTS = {
    "flashlight": SafeLight(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="It made a clean white beam",
        tags={"flashlight", "safe_light"},
    ),
    "starlamp": SafeLight(
        id="starlamp",
        label="star lamp",
        phrase="a little star lamp",
        glow="the star lamp spilled blue dots over the blanket roof",
        tags={"starlamp", "safe_light"},
    ),
    "helmetlamp": SafeLight(
        id="helmetlamp",
        label="helmet lamp",
        phrase="a clip-on helmet lamp",
        glow="the helmet lamp shone right where they looked",
        tags={"helmetlamp", "safe_light"},
    ),
}

RESPONSES = {
    "damp_cloth": Response(
        id="damp_cloth",
        sense=3,
        power=3,
        text="pressed a damp cloth over the {target} and smothered the flame at once",
        fail="pressed a damp cloth over the {target}, but the fire had already skipped beyond that first spot",
        qa_text="pressed a damp cloth over it and smothered the flame",
        tags={"smother", "fire"},
    ),
    "extinguisher": Response(
        id="extinguisher",
        sense=3,
        power=4,
        text="grabbed the small home extinguisher from the hall and sprayed the flames until they were gone",
        fail="sprayed the extinguisher at the {target}, but the fire had already spread too far through the fort",
        qa_text="used the home extinguisher to put the flames out",
        tags={"extinguisher", "fire"},
    ),
    "cup_splash": Response(
        id="cup_splash",
        sense=1,
        power=1,
        text="splashed a little water from a cup onto the {target}",
        fail="splashed a little water from a cup at the {target}, but it was not enough",
        qa_text="splashed a little water from a cup at it",
        tags={"water", "fire"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Tess", "Ivy", "Zara", "Nia", "Skye"]
BOY_NAMES = ["Milo", "Orion", "Finn", "Jude", "Theo", "Leo", "Arlo", "Kai"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "clever"]


@dataclass
class StoryParams:
    mission: str
    forbidden: str
    target: str
    light1: str
    light2: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for forbidden_id, forbidden in FORBIDDEN.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(forbidden, target):
                    combos.append((mission_id, forbidden_id, target_id))
    return combos


KNOWLEDGE = {
    "wick": [
        (
            "What is a wick?",
            "A wick is the little string inside a candle that catches the flame and helps the candle burn. If you light the wick, you get a real fire.",
        )
    ],
    "mocha": [
        (
            "What is mocha?",
            "Mocha is a chocolate-and-coffee flavor or smell. It can smell cozy, but a sweet smell does not make a candle safe for children.",
        )
    ],
    "candle": [
        (
            "Why can a candle be dangerous?",
            "A candle has a real flame. If that flame touches paper, cloth, or cardboard, it can start a fire quickly.",
        )
    ],
    "fire": [
        (
            "Why is a small flame still dangerous?",
            "Even a small flame is hot enough to start a fire. Fires can spread faster than children can stop them.",
        )
    ],
    "paper": [
        (
            "Why does paper catch fire easily?",
            "Paper is thin and dry, so a flame can bite into it very fast. That is why candles should stay far away from paper.",
        )
    ],
    "blanket": [
        (
            "Why is a blanket unsafe near a flame?",
            "A blanket is cloth, and cloth can burn. A hanging blanket can also let flames climb upward fast.",
        )
    ],
    "cardboard": [
        (
            "Can cardboard burn?",
            "Yes. Cardboard is made from paper, so it can catch fire and spread it to other things nearby.",
        )
    ],
    "call_adult": [
        (
            "What should a child do if something catches fire?",
            "Move away and call a grown-up right away. Getting help fast is the safest and bravest choice.",
        )
    ],
    "smother": [
        (
            "What does it mean to smother a small fire?",
            "Smothering a fire means covering it so the flame cannot keep getting air. Grown-ups can do this with the right safe tools.",
        )
    ],
    "extinguisher": [
        (
            "What is a home fire extinguisher for?",
            "A fire extinguisher helps a grown-up put out a small fire fast. It is safety equipment, not a toy.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight safer than a candle?",
            "A flashlight makes light without any flame. That means it can brighten the dark without starting a fire.",
        )
    ],
    "starlamp": [
        (
            "What is a star lamp?",
            "A star lamp is a safe electric light that shines shapes or dots like stars. It gives the feeling of space without using fire.",
        )
    ],
    "helmetlamp": [
        (
            "Why is a helmet lamp handy on an adventure?",
            "A helmet lamp points light where you look and keeps your hands free. It is useful because it helps you see without any flame.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "wick",
    "mocha",
    "candle",
    "fire",
    "paper",
    "blanket",
    "cardboard",
    "call_adult",
    "smother",
    "extinguisher",
    "flashlight",
    "starlamp",
    "helmetlamp",
]


CURATED = [
    StoryParams(
        mission="moon",
        forbidden="mocha_candle",
        target="chart",
        light1="flashlight",
        light2="starlamp",
        response="damp_cloth",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Milo",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        mission="mars",
        forbidden="star_candle",
        target="cardboard",
        light1="helmetlamp",
        light2="flashlight",
        response="extinguisher",
        instigator="Orion",
        instigator_gender="boy",
        cautioner="Luna",
        cautioner_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        mission="comet",
        forbidden="lantern_candle",
        target="blanket",
        light1="starlamp",
        light2="helmetlamp",
        response="damp_cloth",
        instigator="Kai",
        instigator_gender="boy",
        cautioner="Nia",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        mission="moon",
        forbidden="mocha_candle",
        target="blanket",
        light1="flashlight",
        light2="helmetlamp",
        response="extinguisher",
        instigator="Arlo",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
]


def explain_rejection(forbidden: ForbiddenLight, target: Target) -> str:
    if not target.flammable:
        return (
            f"(No story: {forbidden.label} makes a real flame, but {target.the} will not catch fire. "
            f"Pick paper, cloth, or cardboard for a real cautionary problem.)"
        )
    return "(No story: this combination does not make a believable fire hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too weak or too low-sense for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    mission = f["mission"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    l1, l2 = f["lights"]
    outcome = f["outcome"]
    base = (
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "wick" and "mocha", '
        f'uses a little inner monologue and gentle rhyme, and involves children in a pretend spaceship.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a cautionary but gentle story where {a.id} wants to light {forbidden.label}, but {b.id} warns about the wick and stops the danger before anything burns.",
            f"Write a space-fort story where the dark cockpit needs light, a child thinks about using a candle, and the ending proves that safe light is braver than risky light with {l1.label} and {l2.label}.",
        ]
    if outcome == "burned":
        return [
            base,
            f"Tell a cautionary space-adventure where {a.id} lights {forbidden.label} near {target.the}, the fire spreads through the fort, and everyone escapes safely but learns a serious lesson.",
            f"Write a rhyming, reflective story where a child's inner monologue says the idea feels clever, but the flame near {target.the} ruins the mission.",
        ]
    return [
        base,
        f"Tell a gentle cautionary story where {a.id} lights {forbidden.label} near {target.the}, a grown-up puts the fire out quickly, and the children later use safe lights instead.",
        f"Write a pretend-space story with rhyme and inner monologue where a child learns that a real wick does not belong in a cardboard spaceship.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    mission = f["mission"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    response = f["response"]
    l1, l2 = f["lights"]
    pair = pair_noun(a, b, f.get("relation", "friends"))
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who turned a room into a spaceship. Their {pw} also mattered because the grown-up helped keep everyone safe.",
        ),
        (
            "Why did the children want more light?",
            f"They were pretending to fly through space, but the {mission.place_word} had grown dark. That darkness made a risky idea seem exciting for a moment.",
        ),
        (
            f"What risky thing did {a.id} want to do?",
            f"{a.id} wanted to light {forbidden.phrase}. The danger was that its wick made a real flame, not pretend spaceship light.",
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} knew the flame could touch {target.the} and start a fire. The warning came before anything happened because {b.id} could see the risk in the dark fort.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{a.id} had an inner thought that being smart was part of being brave. Because {b.id} was the older sibling and spoke firmly, the mission mattered less than safety.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with no fire at all. The children used {l1.phrase} and {l2.phrase}, so the spaceship still felt magical without any flame.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when the wick was lit?",
                f"{target.The} caught fire and scared both children. The trouble started because a real flame touched something flammable in their pretend spaceship.",
            )
        )
        qa.append(
            (
                f"How did the grown-up stop the fire?",
                f"{pw.capitalize()} {response.qa_text.replace('{target}', target.label)}. The quick response worked because the fire was still small enough to contain.",
            )
        )
        qa.append(
            (
                f"What did {a.id} learn?",
                f"{a.id} learned that wanting a mission to feel real was not a good reason to use a real flame. Later, the safe lights proved the adventure could continue in a better way.",
            )
        )
    else:
        qa.append(
            (
                f"Could {pw} stop the fire right away?",
                f"No. {pw.capitalize()} tried, but the flames spread through the fort too quickly. The children got out safely, yet the pretend spaceship was lost because the fire had grown too strong.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with everyone safe but sad, because the fort was ruined. The children remembered afterward that wick flames do not belong in play spaces.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["forbidden"].tags) | set(world.facts["target_cfg"].tags)
    outcome = world.facts["outcome"]
    if outcome == "contained":
        tags |= set(world.facts["response"].tags)
        for light in world.facts["lights"]:
            tags |= set(light.tags)
    elif outcome == "burned":
        tags |= set(world.facts["response"].tags)
    else:
        for light in world.facts["lights"]:
            tags |= set(light.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("flammable", ent.flammable), ("makes_flame", ent.makes_flame), ("gives_light", ent.gives_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F, T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Mi, F, T) :- mission(Mi), forbidden(F), target(T), hazard(F, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for forbidden_id, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", forbidden_id))
        if forbidden.makes_flame:
            lines.append(asp.fact("makes_flame", forbidden_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
        if target.flammable:
            lines.append(asp.fact("flammable", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(item for (item,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-fort cautionary storyworld with rhyme, inner monologue, and safe-light lessons."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].flammable:
        forbidden = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        raise StoryError(explain_rejection(forbidden, TARGETS[args.target]))
    if args.forbidden and args.target:
        forbidden = FORBIDDEN[args.forbidden]
        target = TARGETS[args.target]
        if not hazard_at_risk(forbidden, target):
            raise StoryError(explain_rejection(forbidden, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, forbidden_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        mission=mission_id,
        forbidden=forbidden_id,
        target=target_id,
        light1=light1,
        light2=light2,
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
    try:
        mission = MISSIONS[params.mission]
        forbidden = FORBIDDEN[params.forbidden]
        target = TARGETS[params.target]
        light1 = SAFE_LIGHTS[params.light1]
        light2 = SAFE_LIGHTS[params.light2]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"Invalid parameter value: {err}") from err

    if not hazard_at_risk(forbidden, target):
        raise StoryError(explain_rejection(forbidden, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        mission=mission,
        forbidden=forbidden,
        target=target,
        lights=(light1, light2),
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, forbidden, target) combos:\n")
        for mission_id, forbidden_id, target_id in combos:
            print(f"  {mission_id:8} {forbidden_id:14} {target_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.forbidden} near {p.target} ({p.mission}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
