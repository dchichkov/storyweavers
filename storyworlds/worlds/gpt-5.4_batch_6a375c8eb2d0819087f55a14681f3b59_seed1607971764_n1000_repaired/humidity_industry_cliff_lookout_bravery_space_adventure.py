#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py
=====================================================================================

A standalone story world about children at a cliff lookout who turn an evening
view into a space adventure. The sea air is heavy with humidity, the harbor's
industry lights glitter below like a robot city, and one child is tempted to
step past the safety chain for a better view. The world prefers sensible,
child-facing stories where bravery means warning, calling for help, and using a
safe lookout tool instead of risking the slippery edge.

Run it
------
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py --humidity foggy --spot outer_rock
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py --spot sign_base   # rejected
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py --response wave_arms  # rejected
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/humidity_industry_cliff_lookout_bravery_space_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    exposed: bool = False
    slippery: bool = False
    gives_view: bool = False
    rescue_reach: int = 0
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mission:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    sendoff: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Humidity:
    id: str
    line: str
    level: int
    beads: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Spot:
    id: str
    label: str
    the: str
    near: str
    distance: int
    exposed: bool
    overlook: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    glow: str
    view_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    reach: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_humidity_slick(world: World) -> list[str]:
    out: list[str] = []
    sea = world.get("sea_air")
    spot = world.get("spot")
    if sea.meters["humidity"] >= THRESHOLD and spot.exposed:
        sig = ("slick", spot.id)
        if sig not in world.fired:
            world.fired.add(sig)
            spot.slippery = True
            spot.meters["slippery"] += 1
            out.append("__slick__")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    spot = world.get("spot")
    if child.meters["beyond_chain"] >= THRESHOLD and spot.meters["slippery"] >= THRESHOLD:
        sig = ("wobble", child.id, spot.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["wobble"] += 1
            child.memes["fear"] += 1
            world.get("lookout").meters["danger"] += 1
            out.append("__wobble__")
    return out


def _r_slide(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    if child.meters["wobble"] >= THRESHOLD and world.facts["response_reach"] < world.facts["needed_reach"]:
        sig = ("slide", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["lower_shelf"] += 1
            child.memes["fear"] += 1
            world.get("lookout").meters["danger"] += 1
            out.append("__slide__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="humidity_slick", tag="physical", apply=_r_humidity_slick),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="slide", tag="physical", apply=_r_slide),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(humidity: Humidity, spot: Spot) -> bool:
    return humidity.level >= 1 and spot.exposed


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def needed_reach(spot: Spot, delay: int) -> int:
    return spot.distance + delay


def is_rescued(response: Response, spot: Spot, delay: int) -> bool:
    return response.reach >= needed_reach(spot, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("instigator").meters["beyond_chain"] += 1
    propagate(sim, narrate=False)
    child = sim.get("instigator")
    return {
        "slick": sim.get("spot").meters["slippery"] >= THRESHOLD,
        "wobble": child.meters["wobble"] >= THRESHOLD,
        "danger": sim.get("lookout").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, mission: Mission, humidity: Humidity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"At the cliff lookout, {a.id} and {b.id} turned the evening into {mission.scene}. "
        f"{mission.rig}"
    )
    world.say(
        f"The sea air carried so much humidity that tiny beads gathered on the rail, "
        f"and far below them the harbor industry glowed in neat rows of yellow lights."
    )
    world.say(
        f'"{mission.title_a} {a.id} and {mission.title_b} {b.id}!" {a.id} said. '
        f'"Let\'s find {mission.goal}!"'
    )
    world.say(humidity.line)


def need_better_view(world: World, b: Entity, mission: Mission, spot: Spot) -> None:
    world.say(
        f"But {spot.overlook} was the darkest, most exciting part of the whole lookout. "
        f"{b.id} leaned close and tried to peer through the damp air."
    )
    world.say(f'"We need a better view," {b.pronoun()} said. "The lights look like a city on another planet."')


def tempt(world: World, a: Entity, spot: Spot) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed at {spot.the}. "If I step onto {spot.near}, I can see everything," '
        f'{a.pronoun()} said. For one breath, the idea felt bold and brilliant.'
    )


def warn(world: World, b: Entity, a: Entity, humidity: Humidity, spot: Spot, parent: Entity) -> None:
    pred = predict_risk(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} could already imagine a shoe sliding on the wet stone."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "Don\'t go past the chain," {b.pronoun()} said. '
        f'"The humidity put {humidity.beads} on everything, and {spot.the} is slick."{extra}'
    )
    world.say(
        f'"Real bravery is knowing when to call {parent.label_word} and use the safe lookout," '
        f'{b.id} added.'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    instigator_older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older_sib:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"I can do it," {a.id} said, and because {a.id} was {b.id}\'s {rel}, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"I can do it," {a.id} said, and slipped past the chain before anyone could stop {a.pronoun("object")}.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} stared at the shining rocks, then back at {b.id}. Because {b.id} was '
        f'{a.pronoun("possessive")} older {rel}, the warning landed hard. '
        f'{a.id} stepped away from the chain and let out a shaky breath.'
    )
    world.say(
        f'Together they told {parent.label_word} that the wet edge had looked like part of the mission, '
        f'but it was not a safe place to stand.'
    )


def step_out(world: World, a: Entity, spot: Spot) -> None:
    a.meters["beyond_chain"] += 1
    propagate(world, narrate=False)
    if a.meters["wobble"] >= THRESHOLD:
        world.say(
            f'{a.id} edged onto {spot.near}. One shoe skidded on the damp stone, and {a.pronoun()} '
            f'windmilled both arms as the whole world suddenly felt too high.'
        )
    else:
        world.say(
            f'{a.id} edged onto {spot.near}. The stone looked shiny under the mist, and the drop below '
            f'felt much bigger than it had from behind the chain.'
        )


def alarm(world: World, b: Entity, a: Entity, parent: Entity, spot: Spot) -> None:
    if world.get("instigator").meters["lower_shelf"] >= THRESHOLD:
        world.say(f'"{a.id} slid down to the lower shelf!" {b.id} cried.')
    else:
        world.say(f'"{a.id}! Hold still by {spot.the}!" {b.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, a: Entity, spot: Spot) -> None:
    a.meters["beyond_chain"] = 0.0
    a.meters["wobble"] = 0.0
    a.meters["lower_shelf"] = 0.0
    world.get("lookout").meters["danger"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} came running and {response.text}. In one careful pull, '
        f'{a.id} was back behind the chain.'
    )
    world.say(
        f'{a.id} leaned against {parent.pronoun("possessive")} side, trembling but safe, while the '
        f'industry lights below went on blinking like patient little stars.'
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
    world.say("For a moment, nobody said anything except the wind.")
    world.say(
        f'Then {parent.label_word.capitalize()} crouched beside them. "Bravery is not stepping closer to danger," '
        f'{parent.pronoun()} said softly. "Bravery is listening, calling for help fast, and choosing the safe place to stand."'
    )
    world.say(f'"We know," whispered {a.id}. "{b.id} was right."')


def ranger_rescue(world: World, parent: Entity, response: Response, a: Entity) -> None:
    a.meters["wobble"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} {response.fail}. {a.id} had slid onto a lower stone shelf and was crying too hard to climb back.'
    )
    world.say(
        f'{parent.pronoun().capitalize()} called the cliff ranger station at once, and soon a ranger came down the safety steps with a clipped line and lifted {a.id} up again.'
    )


def after_bad_rescue(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    a.meters["lower_shelf"] = 0.0
    world.get("lookout").meters["danger"] = 0.0
    world.say(
        f'Wrapped in {parent.pronoun("possessive")} coat, {a.id} shook all over. Nobody was hurt badly, but the game was over and the lookout felt very quiet.'
    )
    world.say(
        'That night the children learned that cliffs do not care about brave speeches. They only become safe when people respect the barrier and ask trained grown-ups for help.'
    )


def safe_tool_end(world: World, parent: Entity, a: Entity, b: Entity, mission: Mission, tool1: SafeTool, tool2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    lead = "A little later" if world.facts["outcome"] == "stranded" else "After everyone had settled down"
    world.say(
        f'{lead}, {parent.label_word} showed them {tool1.phrase} and {tool2.phrase}. '
        f'{tool1.glow}, and {tool2.glow}.'
    )
    world.say(
        f'"Now you can finish the mission from the safe side of the chain," {parent.pronoun()} said.'
    )
    world.say(
        f'{b.id} used the {tool1.label}, and {a.id} tried the {tool2.label}. Soon {tool1.view_text}, '
        f'and the children could count the harbor lights without touching the edge.'
    )
    world.say(
        f'This time the explorers {mission.sendoff} -- not by climbing higher, but by being brave enough to stay safe.'
    )


def tell(
    mission: Mission,
    humidity: Humidity,
    spot: Spot,
    tools: tuple[SafeTool, SafeTool],
    response: Response,
    *,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lina",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "steady",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation, "trust": trust},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    lookout = world.add(Entity(id="lookout", type="place", label="cliff lookout"))
    sea_air = world.add(Entity(id="sea_air", type="weather", label="sea air"))
    sea_air.meters["humidity"] = float(humidity.level)
    spot_ent = world.add(Entity(
        id="spot",
        type="edge",
        label=spot.label,
        exposed=spot.exposed,
        attrs={"distance": spot.distance},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    world.facts["response_reach"] = response.reach
    world.facts["needed_reach"] = needed_reach(spot, delay)

    play_setup(world, a, b, mission, humidity)
    need_better_view(world, b, mission, spot)

    world.para()
    tempt(world, a, spot)
    warn(world, b, a, humidity, spot, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        outcome = "averted"
        safe_tool_end(world, parent, a, b, mission, tools[0], tools[1])
    else:
        defy(world, a, b)
        world.para()
        step_out(world, a, spot)
        if not is_rescued(response, spot, delay):
            propagate(world, narrate=False)
        alarm(world, b, a, parent, spot)
        world.para()
        if is_rescued(response, spot, delay):
            rescue(world, parent, response, a, spot)
            lesson(world, parent, a, b)
            world.para()
            outcome = "rescued"
            safe_tool_end(world, parent, a, b, mission, tools[0], tools[1])
        else:
            ranger_rescue(world, parent, response, a)
            after_bad_rescue(world, parent, a, b)
            world.para()
            outcome = "stranded"
            safe_tool_end(world, parent, a, b, mission, tools[0], tools[1])

    world.facts.update(
        mission=mission,
        humidity=humidity,
        spot_cfg=spot,
        response=response,
        tools=tools,
        instigator=a,
        cautioner=b,
        parent=parent,
        delay=delay,
        relation=relation,
        outcome=outcome,
        predicted_danger=world.facts.get("predicted_danger", 0),
        slipped=(not averted and a.meters["wobble"] >= 0.0),
        promised=(a.memes["lesson"] >= THRESHOLD),
    )
    return world


MISSIONS = {
    "orbit_watch": Mission(
        id="orbit_watch",
        scene="a tiny moon-base on the edge of the world",
        rig="The bench was mission control, the map board was their star chart, and the harbor below looked like a shining galaxy.",
        title_a="Captain",
        title_b="Scout",
        goal="the blinking robot city",
        sendoff="finished their orbit watch with noses pressed to the lenses",
    ),
    "comet_patrol": Mission(
        id="comet_patrol",
        scene="a comet patrol station above the sea",
        rig="The lookout sign became their launch computer, the pebble path became a docking lane, and the lights below looked like little engines warming up.",
        title_a="Commander",
        title_b="Pilot",
        goal="the silver shipping lane",
        sendoff="reported back to mission control with happy, steady voices",
    ),
    "star_port": Mission(
        id="star_port",
        scene="a secret star-port above the waves",
        rig="The fence was the station wall, the ticket post was a fuel pump, and the dark water below looked like space with ripples in it.",
        title_a="Ranger",
        title_b="Navigator",
        goal="the harbor constellation",
        sendoff="completed their star-port check from the safe platform",
    ),
}

HUMIDITIES = {
    "misty": Humidity(
        id="misty",
        line="A soft mist kept drifting in from the sea, so every metal bar felt cool and wet.",
        level=1,
        beads="tiny silver beads",
        tags={"humidity", "mist"},
    ),
    "foggy": Humidity(
        id="foggy",
        line="The humidity was thick enough to turn the air into a pale gray veil over the cliff.",
        level=2,
        beads="fat drops",
        tags={"humidity", "fog"},
    ),
    "sticky": Humidity(
        id="sticky",
        line="Even without a cloud, the humidity made the evening feel sticky and left a damp shine on the stones.",
        level=1,
        beads="a damp shine",
        tags={"humidity"},
    ),
}

SPOTS = {
    "outer_rock": Spot(
        id="outer_rock",
        label="outer rock",
        the="the outer rock",
        near="the outer rock beyond the chain",
        distance=2,
        exposed=True,
        overlook="the narrow ledge by the outer rock",
        tags={"cliff", "rock", "danger"},
    ),
    "marker_stone": Spot(
        id="marker_stone",
        label="marker stone",
        the="the marker stone",
        near="the marker stone just past the chain",
        distance=1,
        exposed=True,
        overlook="the marker stone near the edge",
        tags={"cliff", "stone", "danger"},
    ),
    "sign_base": Spot(
        id="sign_base",
        label="sign base",
        the="the sign base",
        near="the flat ground by the sign",
        distance=0,
        exposed=False,
        overlook="the flat place by the sign",
        tags={"sign"},
    ),
}

SAFE_TOOLS = {
    "viewscope": SafeTool(
        id="viewscope",
        label="public viewscope",
        phrase="the public viewscope",
        glow="Its round glass was dry under a hood",
        view_text="the far industry lights jumped close and bright in the eyepiece",
        tags={"viewscope", "lookout"},
    ),
    "star_chart": SafeTool(
        id="star_chart",
        label="laminated star chart",
        phrase="a laminated star chart",
        glow="The chart shone under the lookout lamp without getting soggy",
        view_text="the children matched the real lights to little silver dots on the chart",
        tags={"chart", "lookout"},
    ),
    "binoculars": SafeTool(
        id="binoculars",
        label="binoculars",
        phrase="a pair of binoculars",
        glow="The lenses clicked clear after a quick wipe",
        view_text="the ships and cranes below looked close enough to count",
        tags={"binoculars", "lookout"},
    ),
    "scope_card": SafeTool(
        id="scope_card",
        label="coin card for the telescope",
        phrase="a coin card for the lookout telescope",
        glow="It slid into the telescope slot with a cheerful click",
        view_text="the big telescope opened a sharp view through the haze",
        tags={"telescope", "lookout"},
    ),
}

RESPONSES = {
    "backpack_pull": Response(
        id="backpack_pull",
        sense=3,
        reach=2,
        text="caught the strap of the child's little backpack and drew the child back without stepping past the barrier",
        fail="snatched for the backpack strap, but the child had already slipped too low for that quick grab to work",
        qa_text="caught the backpack strap and pulled the child back behind the chain",
        tags={"rescue", "barrier"},
    ),
    "coat_pull": Response(
        id="coat_pull",
        sense=3,
        reach=1,
        text="lay flat, grabbed the back of the child's coat, and slid the child carefully behind the chain",
        fail="reached for the child's coat, but the child had slipped past arm's reach onto the lower shelf",
        qa_text="grabbed the coat and pulled the child back to the safe side",
        tags={"rescue", "coat"},
    ),
    "walking_stick": Response(
        id="walking_stick",
        sense=2,
        reach=2,
        text="braced a walking stick across the gap and told the child to hold on while the child was guided back to the platform",
        fail="stretched out a walking stick, but the child was too low and scared to grab it safely",
        qa_text="used a walking stick to guide the child back from the edge",
        tags={"rescue", "stick"},
    ),
    "wave_arms": Response(
        id="wave_arms",
        sense=1,
        reach=0,
        text="waved both arms and called for the child to hop back alone",
        fail="waved and called, but that did not reach the child at all",
        qa_text="waved and called from a distance",
        tags={"bad_response"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Zoe", "Ava", "Nora", "Lucy", "Maya", "Ella"]
BOY_NAMES = ["Max", "Leo", "Finn", "Sam", "Eli", "Theo", "Noah", "Ben"]
TRAITS = ["careful", "steady", "thoughtful", "sensible", "curious", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for mission_id in MISSIONS:
        for humidity_id, humidity in HUMIDITIES.items():
            for spot_id, spot in SPOTS.items():
                if hazard_at_risk(humidity, spot):
                    combos.append((mission_id, humidity_id, spot_id))
    return combos


@dataclass
class StoryParams:
    mission: str
    humidity: str
    spot: str
    tool1: str
    tool2: str
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
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "humidity": [
        (
            "What is humidity?",
            "Humidity is water floating in the air that you cannot always see. When there is a lot of it, the air can feel damp and surfaces can get wet."
        )
    ],
    "industry": [
        (
            "What does industry mean?",
            "Industry means places where people make, move, or build things, like factories, cranes, and busy harbor work. At night, industry areas can shine with many bright lights."
        )
    ],
    "cliff": [
        (
            "Why is a cliff edge dangerous?",
            "A cliff edge is dangerous because the ground can drop away suddenly. Wet stone can make slipping happen even faster."
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a cloud of tiny water drops floating close to the ground. It can make things look blurry and leave surfaces damp."
        )
    ],
    "fog": [
        (
            "What is fog?",
            "Fog is very thick mist that makes it hard to see far away. It can make a place feel quieter and closer all at once."
        )
    ],
    "barrier": [
        (
            "Why should children stay behind a safety barrier?",
            "A safety barrier marks the place where people are meant to stand. Staying behind it gives your feet stable ground and keeps you farther from danger."
        )
    ],
    "rescue": [
        (
            "What should you do if someone slips near an edge?",
            "Call a grown-up or trained helper right away and tell the person to hold still. Quick help is safer than rushing after them."
        )
    ],
    "lookout": [
        (
            "What is a lookout?",
            "A lookout is a safe place built so people can stand and see far away. It is made for looking, not for climbing past the edge."
        )
    ],
    "binoculars": [
        (
            "What do binoculars do?",
            "Binoculars make far things look closer. They help you see better without walking into a dangerous place."
        )
    ],
    "telescope": [
        (
            "What does a telescope help you do?",
            "A telescope helps you look at faraway things in a bigger, clearer way. It lets you stay in one safe spot while your eyes do the traveling."
        )
    ],
    "chart": [
        (
            "What is a star chart?",
            "A star chart is a picture guide that helps you match lights in the sky or far away with names and patterns. It helps people notice details carefully."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "humidity",
    "industry",
    "cliff",
    "mist",
    "fog",
    "barrier",
    "rescue",
    "lookout",
    "binoculars",
    "telescope",
    "chart",
]


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
    mission = f["mission"]
    humidity = f["humidity"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short space-adventure story for a 3-to-5-year-old at a cliff lookout that includes the words "humidity" and "industry".',
            f"Tell a gentle story where {a.label} wants to step onto {spot.the} for a better view, but {b.label} explains that the humidity made it slippery and the children choose a safe lookout tool instead.",
            f'Write a story where bravery means listening and staying behind the chain while the harbor industry lights below look like a city in space.',
        ]
    if outcome == "stranded":
        return [
            f'Write a cautionary space-adventure story for a 3-to-5-year-old set at a cliff lookout that includes the words "humidity" and "industry".',
            f"Tell a story where {a.label} slips past the safety chain in the damp air, gets stuck on a lower shelf, and a grown-up calls a ranger before the children finish the mission safely from the platform.",
            f'Write a child-facing story that teaches that bravery is asking for help quickly instead of climbing closer to danger.',
        ]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old at a cliff lookout that includes the words "humidity" and "industry".',
        f"Tell a gentle cautionary story where {a.label} ignores a warning about the wet rocks, but a grown-up rescues the child and later gives the children safe ways to keep watching the lights.",
        f'Write a story where harbor industry lights look like stars, and the ending shows that real bravery means staying in the safe lookout area.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    mission = f["mission"]
    humidity = f["humidity"]
    spot = f["spot_cfg"]
    response = f["response"]
    tools = f["tools"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, and their {pw} at the cliff lookout. They were pretending the lookout was {mission.scene}."
        ),
        (
            "What made the lookout feel like a space adventure?",
            f"The harbor industry lights below looked like a bright city in space, and the children turned the bench, signs, and lenses into mission tools. That pretend game made the cliff lookout feel like a launch station."
        ),
        (
            "Why did stepping past the chain become dangerous?",
            f"The humidity left wet beads on the rail and slick dampness on {spot.the}. That made the edge slippery, so a child could lose footing very quickly."
        ),
        (
            f"What did {b.label} say bravery meant?",
            f"{b.label} said bravery meant listening, calling a grown-up, and using the safe lookout instead of stepping closer to danger. That warning came before the big turn in the story."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Why did {a.label} change {a.pronoun('possessive')} mind?",
            f"{a.label} believed {b.label}'s warning and stepped away from the chain. Because {b.label} was older and spoke firmly, the danger finally felt real."
        ))
        qa.append((
            "How did the story end?",
            f"The children used {tools[0].phrase} and {tools[1].phrase} from the safe platform. They still finished the mission, but they did it without touching the edge."
        ))
    elif f["outcome"] == "rescued":
        body = response.qa_text
        qa.append((
            f"How did {a.label}'s {pw} help?",
            f"{pw.capitalize()} came fast and {body}. The quick rescue worked because the grown-up acted right away instead of shouting from far away."
        ))
        qa.append((
            f"How did {a.label} feel after the rescue?",
            f"{a.label} felt shaky and scared at first, then relieved. The blinking lights below looked different after that because the child understood how close the danger had been."
        ))
        qa.append((
            "What changed at the end?",
            f"The children stopped trying to get a better view by climbing. Instead, they used lookout tools from the safe side and learned a truer kind of bravery."
        ))
    else:
        qa.append((
            f"Why did a ranger need to help {a.label}?",
            f"The first rescue try could not reach far enough after {a.label} slipped onto a lower shelf. A trained ranger was needed because the child was below the platform and too scared to climb back alone."
        ))
        qa.append((
            "Was anyone badly hurt?",
            f"No, nobody was badly hurt, but everyone was frightened and the game stopped. The scary part is what taught them to respect the barrier."
        ))
        qa.append((
            "How did the story end?",
            f"After the ranger brought {a.label} back, the children finished the mission with lookout tools instead of risky climbing. The ending proves they changed because they stayed on the platform and used the safe view."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"industry", "cliff", "lookout"}
    tags |= set(f["humidity"].tags)
    tags |= set(f["response"].tags)
    for tool in f["tools"]:
        tags |= set(tool.tags)
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
        if e.exposed:
            bits.append("exposed=True")
        if e.slippery:
            bits.append("slippery=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:11} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="orbit_watch",
        humidity="foggy",
        spot="marker_stone",
        tool1="viewscope",
        tool2="star_chart",
        response="backpack_pull",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lina",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        mission="comet_patrol",
        humidity="misty",
        spot="outer_rock",
        tool1="binoculars",
        tool2="scope_card",
        response="walking_stick",
        instigator="Mira",
        instigator_gender="girl",
        cautioner="Noah",
        cautioner_gender="boy",
        parent="father",
        trait="clever",
        delay=0,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        mission="star_port",
        humidity="foggy",
        spot="outer_rock",
        tool1="viewscope",
        tool2="binoculars",
        response="coat_pull",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=1,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        mission="orbit_watch",
        humidity="sticky",
        spot="marker_stone",
        tool1="scope_card",
        tool2="star_chart",
        response="backpack_pull",
        instigator="Finn",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(humidity: Humidity, spot: Spot) -> str:
    if not spot.exposed:
        return (
            f"(No story: {spot.the} is inside the safe lookout area, so stepping there does not create a real edge danger. "
            f"Pick an exposed place like the marker stone or the outer rock.)"
        )
    if humidity.level < 1:
        return (
            f"(No story: this air would not make {spot.the} slick enough for the warning to be honest.)"
        )
    return "(No story: this combination does not create a plausible slippery-edge problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "rescued" if is_rescued(RESPONSES[params.response], SPOTS[params.spot], params.delay) else "stranded"


ASP_RULES = r"""
hazard(H, S) :- humidity(H), spot(S), level(H, L), L >= 1, exposed(S).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Mis, H, S) :- mission(Mis), hazard(H, S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

needed_reach(Dist + Delay) :- chosen_spot(S), distance(S, Dist), delay(Delay).
rescued :- chosen_response(R), reach(R, Reach), needed_reach(N), Reach >= N.

outcome(averted) :- averted.
outcome(rescued) :- not averted, rescued.
outcome(stranded) :- not averted, not rescued.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for hid, h in HUMIDITIES.items():
        lines.append(asp.fact("humidity", hid))
        lines.append(asp.fact("level", hid, h.level))
    for sid, s in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("distance", sid, s.distance))
        if s.exposed:
            lines.append(asp.fact("exposed", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("reach", rid, r.reach))
    for tid in SAFE_TOOLS:
        lines.append(asp.fact("tool", tid))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(resolve_params(parser.parse_args([]), random.Random(123)))
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        _ = generate(CURATED[0]).story
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cliff lookout space adventure where bravery means staying safe."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--humidity", choices=HUMIDITIES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--tool1", choices=SAFE_TOOLS)
    ap.add_argument("--tool2", choices=SAFE_TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how much head start the slip gets before the rescue can reach")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and not SPOTS[args.spot].exposed:
        humidity = HUMIDITIES[args.humidity] if args.humidity else next(iter(HUMIDITIES.values()))
        raise StoryError(explain_rejection(humidity, SPOTS[args.spot]))
    if args.humidity and args.spot:
        if not hazard_at_risk(HUMIDITIES[args.humidity], SPOTS[args.spot]):
            raise StoryError(explain_rejection(HUMIDITIES[args.humidity], SPOTS[args.spot]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.tool1 and args.tool2 and args.tool1 == args.tool2:
        raise StoryError("(No story: choose two different safe lookout tools.)")

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.humidity is None or c[1] == args.humidity)
        and (args.spot is None or c[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, humidity, spot = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    tool_keys = sorted(SAFE_TOOLS)
    if args.tool1 and args.tool2:
        tool1, tool2 = args.tool1, args.tool2
    elif args.tool1:
        others = [k for k in tool_keys if k != args.tool1]
        tool1, tool2 = args.tool1, rng.choice(others)
    elif args.tool2:
        others = [k for k in tool_keys if k != args.tool2]
        tool1, tool2 = rng.choice(others), args.tool2
    else:
        tool1, tool2 = rng.sample(tool_keys, 2)

    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        mission=mission,
        humidity=humidity,
        spot=spot,
        tool1=tool1,
        tool2=tool2,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
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
        humidity = HUMIDITIES[params.humidity]
        spot = SPOTS[params.spot]
        tool1 = SAFE_TOOLS[params.tool1]
        tool2 = SAFE_TOOLS[params.tool2]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if params.tool1 == params.tool2:
        raise StoryError("(No story: the two safe lookout tools must be different.)")
    if not hazard_at_risk(humidity, spot):
        raise StoryError(explain_rejection(humidity, spot))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        mission=mission,
        humidity=humidity,
        spot=spot,
        tools=(tool1, tool2),
        response=response,
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

    story = world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner)
    story = story.replace("parent", params.parent)
    story = story.replace("Max", params.instigator if params.instigator == "Max" else "Max")
    for internal, external in [("instigator", params.instigator), ("cautioner", params.cautioner)]:
        story = story.replace(f"{internal}.", f"{external}.")
    # Replace entity labels via targeted cleanup.
    story = story.replace("instigator", params.instigator).replace("cautioner", params.cautioner)
    story = story.replace("the child's", f"{params.instigator}'s")
    # Human-facing text should use names from labels; rebuild from labels in world objects.
    story = story.replace(world.facts["instigator"].label, params.instigator)
    story = story.replace(world.facts["cautioner"].label, params.cautioner)

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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, humidity, spot) combos:\n")
        for mission, humidity, spot in combos:
            print(f"  {mission:12} {humidity:7} {spot}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.humidity} at {p.spot} ({p.mission}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
