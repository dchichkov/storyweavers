#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py
========================================================

A standalone story world about two children on a small adventure who find a
cruel rumor scratched on a sign, argue about whether to trust a strange helper,
and learn that brave adventures also need fairness.

The required seed word appears as graffiti inside the story, always framed as a
hurtful word someone should not use.

Run it
------
    python storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py
    python storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py --place island --obstacle ravine --helper keeper
    python storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py --helper gardener --obstacle tunnel
    python storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py --all
    python storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pervert_conflict_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    scene: str
    goal: str
    goal_object: str
    route: str
    affordances: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    block_text: str
    need: str
    crossing: str
    risk_text: str
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
class Helper:
    id: str
    label: str
    title: str
    station: str
    tool: str
    solves: set[str] = field(default_factory=set)
    warm: int = 1
    aid_text: str = ""
    kindness_text: str = ""
    truth_text: str = ""
    apology_reply: str = ""
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
class RumorMark:
    id: str
    surface: str
    look: str
    fear: int
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
class DoubterTrait:
    id: str
    base_trust: int
    line: str
    recovery_line: str
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
class StoryParams:
    place: str
    obstacle: str
    helper: str
    rumor: str
    lead: str
    lead_gender: str
    doubter: str
    doubter_gender: str
    doubter_trait: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "insult_repeated": False,
            "asked_for_help": False,
            "goal_reached": False,
            "outcome": "",
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "doubter"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_blocked(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["blocking"] < THRESHOLD or obstacle.meters["cleared"] >= THRESHOLD:
        return []
    sig = ("blocked", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["frustration"] += 1
        kid.memes["worry"] += 1
    world.get("quest").meters["delay"] += 1
    return []


def _r_cross(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["cleared"] < THRESHOLD:
        return []
    sig = ("cross", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    quest = world.get("quest")
    quest.meters["progress"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
    return []


def _r_kindness(world: World) -> list[str]:
    helper = world.get("helper")
    if helper.meters["helped"] < THRESHOLD:
        return []
    sig = ("kindness", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["trust"] += 1
    if world.facts.get("insult_repeated"):
        world.get("doubter").memes["shame"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked", tag="physical", apply=_r_blocked),
    Rule(name="cross", tag="physical", apply=_r_cross),
    Rule(name="kindness", tag="social", apply=_r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def helper_fits(obstacle: Obstacle, helper: Helper) -> bool:
    return obstacle.need in helper.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affordances):
            obstacle = OBSTACLES[obstacle_id]
            for helper_id, helper in HELPERS.items():
                if helper_fits(obstacle, helper):
                    combos.append((place_id, obstacle_id, helper_id))
    return combos


def trust_score(trait: DoubterTrait, helper: Helper) -> int:
    return trait.base_trust + helper.warm


def would_ask_for_help(trait: DoubterTrait, helper: Helper, rumor: RumorMark) -> bool:
    return trust_score(trait, helper) >= rumor.fear


def introduce(world: World, lead: Entity, doubter: Entity, place: Place) -> None:
    lead.memes["excitement"] += 1
    doubter.memes["excitement"] += 1
    world.say(
        f"By late afternoon, {lead.id} and {doubter.id} were on their Adventure Club mission in {place.scene}. "
        f"They had promised themselves they would reach {place.goal} before the light turned honey-gold."
    )
    world.say(
        f"In {lead.id}'s pocket was a folded map, and on it a red star circled {place.goal_object}. "
        f"The whole route felt brave and secret and full of wind."
    )


def reach_obstacle(world: World, lead: Entity, doubter: Entity, obstacle: Obstacle) -> None:
    world.get("obstacle").meters["blocking"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But halfway there, the path was stopped by {obstacle.block_text}. "
        f"{obstacle.risk_text}"
    )
    world.say(
        f'{lead.id} tightened {lead.pronoun("possessive")} hand around the map. "We still have to get through," '
        f'{lead.pronoun()} said.'
    )


def find_sign(world: World, doubter: Entity, helper: Helper, rumor: RumorMark) -> None:
    doubter.memes["alarm"] += 1
    world.say(
        f"Next to the path stood a board that pointed toward {helper.station}. "
        f"Someone had scratched the ugly word 'pervert' across the {rumor.surface}, {rumor.look}."
    )
    world.say(
        f"{doubter.id} stopped so fast that gravel clicked under {doubter.pronoun('possessive')} shoes. "
        f'{trait_line(world)}'
    )


def trait_line(world: World) -> str:
    doubter = world.get("doubter")
    trait = DOUBTER_TRAITS[world.facts["doubter_trait"].id]
    return f'"{trait.line}" {doubter.pronoun()} whispered.'


def argue(world: World, lead: Entity, doubter: Entity, helper: Helper) -> None:
    lead.memes["courage"] += 1
    doubter.memes["conflict"] += 1
    lead.memes["conflict"] += 1
    world.say(
        f'"That is just a nasty word," {lead.id} said. "It does not prove anything about {helper.title}."'
    )
    world.say(
        f'"But what if it is true?" {doubter.id} asked. The adventure suddenly felt less like a game and more like a choice.'
    )


def ask_for_help(world: World, lead: Entity, doubter: Entity, helper: Helper, obstacle: Obstacle) -> None:
    world.facts["asked_for_help"] = True
    helper_ent = world.get("helper")
    helper_ent.meters["helped"] += 1
    world.get("obstacle").meters["cleared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So they walked together to {helper.station}, slowly but without turning back. "
        f"{helper.title} looked up, saw their worried faces, and listened all the way through before speaking."
    )
    world.say(
        f'"That word was a cruel lie," {helper.title} said softly. "{helper.truth_text}"'
    )
    world.say(
        helper.aid_text.format(
            lead=lead.id,
            doubter=doubter.id,
            crossing=obstacle.crossing,
            tool=helper.tool,
        )
    )
    world.say(
        helper.kindness_text.format(
            lead=lead.id,
            doubter=doubter.id,
            goal=world.place.goal,
        )
    )


def cross_and_finish(world: World, lead: Entity, doubter: Entity, place: Place, helper: Helper) -> None:
    world.get("quest").meters["finished"] += 1
    world.facts["goal_reached"] = True
    world.facts["outcome"] = "trusted"
    world.say(
        f"Soon the children were past the worst part of the trail, hurrying along {place.route} until {place.goal} rose in front of them."
    )
    world.say(
        f"They reached {place.goal_object} just in time, and the small sound they made there carried out over the evening like a bright answer."
    )
    if world.facts.get("insult_repeated"):
        world.say(
            f'{doubter.id} looked back toward {helper.station}. "I should not have let that mean word steer me," '
            f'{doubter.pronoun()} said.'
        )
        world.say(
            f'{helper.apology_reply} Then the adventure felt truly finished.'
        )
    else:
        world.say(
            f"When they waved back at {helper.title}, the whole path seemed kinder than it had at the start."
        )


def refuse_help(world: World, lead: Entity, doubter: Entity, helper: Helper, place: Place) -> None:
    world.facts["asked_for_help"] = False
    world.facts["goal_reached"] = False
    world.facts["outcome"] = "missed"
    world.get("quest").meters["delay"] += 1
    lead.memes["disappointment"] += 1
    doubter.memes["disappointment"] += 1
    world.say(
        f"In the end, they did not go to {helper.station}. They tried to hunt for another way, but every side path bent into nettles, wet stones, or empty time."
    )
    world.say(
        f"By the time they came back to the main trail, the sky was already dimming and {place.goal} was too far away to reach before dark."
    )
    world.say(
        f"As they turned around, they saw {helper.title} helping a tiny child lift a dropped pail and speaking with patient, careful kindness. "
        f"At once the scratched word on the sign looked even uglier than before."
    )
    world.say(
        f'{DOUBTER_TRAITS[world.facts["doubter_trait"].id].recovery_line} {doubter.id} said. '
        f'{lead.id} nodded, and together they rubbed dirt over the cruel graffiti so no one else would have to see it first.'
    )


def build_world(place: Place, obstacle: Obstacle, helper: Helper, rumor: RumorMark,
                lead_name: str, lead_gender: str, doubter_name: str, doubter_gender: str,
                doubter_trait: DoubterTrait) -> World:
    world = World(place)
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        traits=["bold", "curious"],
        attrs={"club": "Adventure Club"},
        tags={"child"},
    ))
    doubter = world.add(Entity(
        id=doubter_name,
        kind="character",
        type=doubter_gender,
        role="doubter",
        traits=[doubter_trait.id],
        attrs={"club": "Adventure Club"},
        tags={"child"},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        role="helper",
        label=helper.label,
        traits=["steady", "kind"],
        attrs={"station": helper.station, "tool": helper.tool},
        tags=set(helper.tags),
    ))
    world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        attrs={"need": obstacle.need},
        tags=set(obstacle.tags),
    ))
    world.add(Entity(
        id="quest",
        kind="thing",
        type="quest",
        label=place.goal_object,
        attrs={"goal": place.goal},
        tags=set(place.tags),
    ))
    world.facts.update(
        place=place,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        rumor=rumor,
        lead=lead,
        doubter=doubter,
        doubter_trait=doubter_trait,
        helper=helper_ent,
    )
    return world


def tell(place: Place, obstacle: Obstacle, helper: Helper, rumor: RumorMark,
         lead_name: str = "Mina", lead_gender: str = "girl",
         doubter_name: str = "Toby", doubter_gender: str = "boy",
         doubter_trait: DoubterTrait = None) -> World:
    if doubter_trait is None:
        doubter_trait = DOUBTER_TRAITS["fair"]
    world = build_world(place, obstacle, helper, rumor, lead_name, lead_gender,
                        doubter_name, doubter_gender, doubter_trait)
    lead = world.get(lead_name)
    doubter = world.get(doubter_name)
    world.facts["doubter_trait"] = doubter_trait

    introduce(world, lead, doubter, place)
    world.para()
    reach_obstacle(world, lead, doubter, obstacle)
    find_sign(world, doubter, helper, rumor)

    if rumor.fear >= 3:
        world.facts["insult_repeated"] = True
        doubter.memes["fear"] += 1
        world.say(
            f'{doubter.id} swallowed. "What if the sign means we should stay away from {helper.title}?" '
            f'{doubter.pronoun()} asked.'
        )

    argue(world, lead, doubter, helper)
    world.para()

    if would_ask_for_help(doubter_trait, helper, rumor):
        ask_for_help(world, lead, doubter, helper, obstacle)
        cross_and_finish(world, lead, doubter, place, helper)
    else:
        refuse_help(world, lead, doubter, helper, place)

    return world


PLACES = {
    "island": Place(
        id="island",
        scene="the windy path around Gull Island",
        goal="the old bell tower",
        goal_object="the sunset bell",
        route="the narrow grass path above the sea",
        affordances={"ravine", "tunnel"},
        tags={"island", "beacon"},
    ),
    "forest": Place(
        id="forest",
        scene="the ferny trail through Lantern Wood",
        goal="the lookout stump",
        goal_object="the brass signal flag",
        route="the rooty trail under the pines",
        affordances={"bramble", "ravine"},
        tags={"forest", "trail"},
    ),
    "cove": Place(
        id="cove",
        scene="the shell-bright cliffs above Moonshell Cove",
        goal="the cave mouth with the echo stone",
        goal_object="the echo stone",
        route="the chalky path above the water",
        affordances={"tunnel", "bramble"},
        tags={"cove", "cave"},
    ),
}

OBSTACLES = {
    "ravine": Obstacle(
        id="ravine",
        label="ravine",
        block_text="a narrow ravine with a broken plank bridge",
        need="rope",
        crossing="a safe rope line and a knot to hold onto",
        risk_text="There was room for only the wind to cross it safely.",
        tags={"ravine", "rope"},
    ),
    "bramble": Obstacle(
        id="bramble",
        label="bramble wall",
        block_text="a wall of brambles thick as a sleepy bear",
        need="cut",
        crossing="a small doorway clipped through the thorns",
        risk_text="The thorns hooked at sleeves and map corners whenever the breeze shook them.",
        tags={"bramble", "shears"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="tunnel",
        block_text="a low sea tunnel black enough to hide its own ceiling",
        need="light",
        crossing="a pool-safe lantern path through the dark",
        risk_text="A wrong step in there would mean cold water and bruised knees.",
        tags={"tunnel", "lantern"},
    ),
}

HELPERS = {
    "keeper": Helper(
        id="keeper",
        label="lighthouse keeper",
        title="the lighthouse keeper",
        station="the keeper's shed",
        tool="a coil of rope",
        solves={"rope"},
        warm=2,
        aid_text="{helper} took {tool}, crossed first, tied a sure line, and called each step to {lead} and {doubter} until the ravine no longer looked like a mouth.",
        kindness_text='Before they left, {helper} tucked a biscuit into each child\'s pocket "for the last bit of courage" and pointed the way to {goal}.',
        truth_text="I mend lamps, mend ropes, and sometimes mend signs after people do foolish things in the dark.",
        apology_reply='"I am glad you came anyway," the lighthouse keeper called. "The bell sounds better when children are brave enough to be fair."',
        tags={"rope", "beacon"},
    ),
    "gardener": Helper(
        id="gardener",
        label="cliff gardener",
        title="the cliff gardener",
        station="the little glass shed",
        tool="long silver shears",
        solves={"cut"},
        warm=1,
        aid_text="{helper} lifted {tool} with careful hands and clipped {crossing}. Soon even the thorns seemed to know better than to grab at {lead} and {doubter}.",
        kindness_text="{helper} tied the cut branches into a neat bundle, so the trail would be safer for the next walkers too.",
        truth_text="I grow herbs and rescue paths. A mean scratch on a board does not change what my hands are for.",
        apology_reply='"Kind feet can make a new path," the cliff gardener said, smiling as the children hurried on.',
        tags={"shears", "garden"},
    ),
    "maker": Helper(
        id="maker",
        label="lantern maker",
        title="the lantern maker",
        station="the lamp workshop by the rocks",
        tool="a blue-glass lantern",
        solves={"light"},
        warm=2,
        aid_text="{helper} lit {tool}, walked ahead, and showed {lead} and {doubter} where the stone stayed dry and where the ceiling dipped low.",
        kindness_text='At the far side, {helper} hung the lantern high for a moment so the cave walls glittered like hidden treasure before sending the children on to {goal}.',
        truth_text="I make light for dark places. Whoever scratched that word wanted to spread fear instead.",
        apology_reply='"Next time, trust the light more than the scratch marks," the lantern maker said.',
        tags={"lantern", "cave"},
    ),
}

RUMORS = {
    "chalk": RumorMark(
        id="chalk",
        surface="paint-flaked board",
        look="in crumbly white chalk that rain had already begun to smear",
        fear=2,
        tags={"graffiti", "rumor"},
    ),
    "charcoal": RumorMark(
        id="charcoal",
        surface="weather-gray signpost",
        look="in greasy black charcoal, ugly and quick",
        fear=3,
        tags={"graffiti", "rumor"},
    ),
    "carved": RumorMark(
        id="carved",
        surface="old cedar arrow-sign",
        look="cut deep enough to make the wood splinter around it",
        fear=4,
        tags={"graffiti", "rumor"},
    ),
}

DOUBTER_TRAITS = {
    "fair": DoubterTrait(
        id="fair",
        base_trust=2,
        line="That word is awful ... but what if someone wrote it for a reason?",
        recovery_line='"We let a cruel rumor boss us around. Next time I want to ask a real person, not a scratched sign,"',
        tags={"fairness", "rumor"},
    ),
    "cautious": DoubterTrait(
        id="cautious",
        base_trust=1,
        line="I do not like this at all. Maybe the safest thing is to stay away.",
        recovery_line='"Being careful is good, but I still should not have believed a mean sign without learning the truth,"',
        tags={"caution", "rumor"},
    ),
    "jumpy": DoubterTrait(
        id="jumpy",
        base_trust=0,
        line="I wish I had never seen that word. It makes my stomach feel wobbly.",
        recovery_line='"I was scared, and I let fear do the thinking for me,"',
        tags={"fear", "rumor"},
    ),
    "steady": DoubterTrait(
        id="steady",
        base_trust=3,
        line="It is nasty, but nasty writing is still only writing until we know more.",
        recovery_line='"I almost forgot that fair adventures need fair hearts too,"',
        tags={"fairness", "courage"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "June", "Ivy", "Ruby", "Tess"]
BOY_NAMES = ["Toby", "Finn", "Owen", "Leo", "Max", "Eli", "Jude", "Ben"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    outcome = world.facts["outcome"]
    lead = world.facts["lead"]
    doubter = world.facts["doubter"]
    if outcome == "trusted":
        return [
            f'Write a short adventure story for a 3-to-5-year-old where two children find the rude word "pervert" scratched on a sign, feel unsure, and still choose fairness over rumor.',
            f"Tell an adventure about {lead.id} and {doubter.id} trying to reach {place.goal}, getting stopped by a {obstacle.label}, and learning that {helper.label} is kind.",
            "Write a gentle conflict story where children face a mean rumor, ask for the truth, and end with a brave, bright success.",
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old where two children find the rude word "pervert" scratched on a sign and let the rumor spoil part of their quest.',
        f"Tell an adventure about {lead.id} and {doubter.id} trying to reach {place.goal}, arguing over whether to trust {helper.label}, and learning too late that the rumor was cruel.",
        "Write a story with conflict, a missed chance, and an ending where children decide to be fairer next time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    rumor = world.facts["rumor"]
    lead = world.facts["lead"]
    doubter = world.facts["doubter"]
    trait = world.facts["doubter_trait"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {doubter.id}, two children on an Adventure Club mission. They were trying to reach {place.goal} before evening.",
        ),
        (
            "What stopped them on the trail?",
            f"They were blocked by {obstacle.block_text}. That danger mattered because they could not finish the adventure without crossing safely.",
        ),
        (
            "Why did the children start arguing?",
            f"They found the ugly word 'pervert' scratched on a sign pointing toward {helper.station}. The writing made {doubter.id} afraid to trust {helper.title}, while {lead.id} said a nasty word was not proof.",
        ),
    ]

    if world.facts["outcome"] == "trusted":
        qa.extend([
            (
                f"Why did they decide to go to {helper.title} anyway?",
                f"They chose to ask a real person instead of obeying a cruel rumor. That was brave because the sign had frightened them, but they still wanted the truth.",
            ),
            (
                f"How did {helper.title} help them?",
                f"{helper.title} used {helper.tool} to make {obstacle.crossing}. The help changed the world of the story because the blocked path became passable again.",
            ),
            (
                "What changed by the end?",
                f"The children reached {place.goal_object} and understood that ugly graffiti can lie. The ending proves they grew because the adventure finishes with trust, apology, and a kinder view of the trail.",
            ),
        ])
    else:
        qa.extend([
            (
                f"Why did they miss {place.goal}?",
                f"They lost time because they were too frightened to ask {helper.title} for help. The rumor on the sign pushed their choice, and the long detour used up the light.",
            ),
            (
                "How did they learn the sign was wrong?",
                f"They later saw {helper.title} acting with patient kindness toward a small child. That sight gave them real evidence, and it made the scratched word seem even crueler.",
            ),
            (
                "What did they do at the end?",
                f"They covered the nasty graffiti so it would not greet the next walker. That ending shows a change because they could not fix the missed adventure, but they could stop the rumor from spreading further.",
            ),
        ])

    if world.facts.get("insult_repeated"):
        qa.append(
            (
                f"How did {doubter.id} feel after the truth became clearer?",
                f"{doubter.id} felt ashamed as well as relieved. The shame came from letting a mean word guide the adventure before learning what was true.",
            )
        )
    else:
        qa.append(
            (
                f"How did {doubter.id}'s personality matter?",
                f"{trait.id.capitalize()} thinking helped {doubter.id} stay open to the truth. That mattered because a fair-minded pause kept the rumor from winning.",
            )
        )
    return qa


KNOWLEDGE = {
    "graffiti": [
        (
            "What is graffiti?",
            "Graffiti is writing or drawing left on a wall or sign. Sometimes it is playful, but hurtful graffiti can make places feel unkind."
        )
    ],
    "rumor": [
        (
            "What is a rumor?",
            "A rumor is a story people repeat before they know whether it is true. Rumors can hurt people when they spread fear instead of facts."
        )
    ],
    "fairness": [
        (
            "Why is it important not to call someone a mean name just because you saw it written down?",
            "Writing can be wrong, just like speaking can be wrong. Fairness means learning the truth before you judge a person."
        )
    ],
    "rope": [
        (
            "What is a rope line good for on a trail?",
            "A rope line gives your hands something steady to hold. It helps people cross tricky places more safely."
        )
    ],
    "shears": [
        (
            "What are garden shears?",
            "Garden shears are strong scissors for plants and branches. Grown-ups use them to trim thorny or tangled places."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in a tunnel?",
            "A lantern brings light into a dark place so you can see where to step. Good light turns guessing into careful seeing."
        )
    ],
    "beacon": [
        (
            "What does a bell tower or signal place do in an adventure?",
            "It gives travelers a clear goal and sometimes a way to send a sound or signal. Reaching it feels like finishing a brave journey."
        )
    ],
    "cave": [
        (
            "Why can a cave or tunnel feel scary?",
            "Dark spaces hide what is ahead, so your body gets ready for danger. Light and a trusted guide can make them feel safer."
        )
    ],
}

KNOWLEDGE_ORDER = ["graffiti", "rumor", "fairness", "rope", "shears", "lantern", "beacon", "cave"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"graffiti", "rumor", "fairness"}
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    tags |= set(world.facts["place"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="island",
        obstacle="ravine",
        helper="keeper",
        rumor="chalk",
        lead="Mina",
        lead_gender="girl",
        doubter="Toby",
        doubter_gender="boy",
        doubter_trait="steady",
    ),
    StoryParams(
        place="forest",
        obstacle="bramble",
        helper="gardener",
        rumor="carved",
        lead="Nora",
        lead_gender="girl",
        doubter="Finn",
        doubter_gender="boy",
        doubter_trait="jumpy",
    ),
    StoryParams(
        place="cove",
        obstacle="tunnel",
        helper="maker",
        rumor="charcoal",
        lead="Ava",
        lead_gender="girl",
        doubter="Leo",
        doubter_gender="boy",
        doubter_trait="fair",
    ),
    StoryParams(
        place="forest",
        obstacle="ravine",
        helper="keeper",
        rumor="carved",
        lead="Ben",
        lead_gender="boy",
        doubter="Ruby",
        doubter_gender="girl",
        doubter_trait="cautious",
    ),
    StoryParams(
        place="cove",
        obstacle="bramble",
        helper="gardener",
        rumor="chalk",
        lead="Ivy",
        lead_gender="girl",
        doubter="Max",
        doubter_gender="boy",
        doubter_trait="steady",
    ),
]


def explain_rejection(place: Place, obstacle: Obstacle, helper: Helper) -> str:
    if obstacle.id not in place.affordances:
        return (
            f"(No story: {place.scene} does not include a plausible {obstacle.label} on this route. "
            f"Pick an obstacle the place actually affords.)"
        )
    return (
        f"(No story: {helper.label} cannot reasonably solve a {obstacle.label}. "
        f"The helper's tool must match the problem on the trail.)"
    )


ASP_RULES = r"""
fits(O,H) :- obstacle(O), helper(H), needs(O,N), solves(H,N).
valid(P,O,H) :- place(P), affords(P,O), fits(O,H).

trust_score(Total) :- chosen_trait(T), base_trust(T,B), chosen_helper(H), warm(H,W), Total = B + W.
ask_for_help :- chosen_rumor(R), rumor_fear(R,F), trust_score(S), S >= F.

outcome(trusted) :- ask_for_help.
outcome(missed)  :- not ask_for_help.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("warm", helper_id, helper.warm))
        for solve in sorted(helper.solves):
            lines.append(asp.fact("solves", helper_id, solve))
    for rumor_id, rumor in RUMORS.items():
        lines.append(asp.fact("rumor", rumor_id))
        lines.append(asp.fact("rumor_fear", rumor_id, rumor.fear))
    for trait_id, trait in DOUBTER_TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("base_trust", trait_id, trait.base_trust))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_rumor", params.rumor),
        asp.fact("chosen_trait", params.doubter_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "trusted" if would_ask_for_help(DOUBTER_TRAITS[params.doubter_trait], HELPERS[params.helper], RUMORS[params.rumor]) else "missed"


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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: children meet a rumor, a trail problem, and a choice about fairness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--doubter-trait", choices=DOUBTER_TRAITS)
    ap.add_argument("--lead")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--doubter")
    ap.add_argument("--doubter-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, obstacle, helper) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.helper:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if args.obstacle not in place.affordances or not helper_fits(obstacle, helper):
            raise StoryError(explain_rejection(place, obstacle, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    rumor_id = args.rumor or rng.choice(sorted(RUMORS))
    trait_id = args.doubter_trait or rng.choice(sorted(DOUBTER_TRAITS))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    doubter_gender = args.doubter_gender or rng.choice(["girl", "boy"])
    lead = args.lead or _pick_name(rng, lead_gender)
    doubter = args.doubter or _pick_name(rng, doubter_gender, avoid=lead)

    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        helper=helper_id,
        rumor=rumor_id,
        lead=lead,
        lead_gender=lead_gender,
        doubter=doubter,
        doubter_gender=doubter_gender,
        doubter_trait=trait_id,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        obstacle = OBSTACLES[params.obstacle]
        helper = HELPERS[params.helper]
        rumor = RUMORS[params.rumor]
        trait = DOUBTER_TRAITS[params.doubter_trait]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if (params.place, params.obstacle, params.helper) not in set(valid_combos()):
        raise StoryError(explain_rejection(place, obstacle, helper))

    world = tell(
        place=place,
        obstacle=obstacle,
        helper=helper,
        rumor=rumor,
        lead_name=params.lead,
        lead_gender=params.lead_gender,
        doubter_name=params.doubter,
        doubter_gender=params.doubter_gender,
        doubter_trait=trait,
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
        print(f"{len(combos)} compatible (place, obstacle, helper) combos:\n")
        for place, obstacle, helper in combos:
            print(f"  {place:8} {obstacle:8} {helper}")
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
            header = f"### {p.lead} & {p.doubter}: {p.place} / {p.obstacle} / {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
