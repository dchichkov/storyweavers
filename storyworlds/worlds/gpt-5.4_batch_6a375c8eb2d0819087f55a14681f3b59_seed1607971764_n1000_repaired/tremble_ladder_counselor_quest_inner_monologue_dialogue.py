#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tremble_ladder_counselor_quest_inner_monologue_dialogue.py
======================================================================================

A standalone story world for a small Space Adventure domain: a young cadet has
a quest that can only be finished by climbing a ladder inside a futuristic
outpost, but fear makes their knees tremble. A calm station counselor helps the
cadet with simple steps -- breathing, looking at one rung at a time, and using
sensible safety gear -- until the quest is done.

The world model is classical and state-driven:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a Python reasonableness gate plus an inline ASP twin
- grounded story QA and world-knowledge QA generated from simulated state

Run it
------
    python storyworlds/worlds/gpt-5.4/tremble_ladder_counselor_quest_inner_monologue_dialogue.py
    python storyworlds/worlds/gpt-5.4/tremble_ladder_counselor_quest_inner_monologue_dialogue.py --place moon_tower --quest beacon
    python storyworlds/worlds/gpt-5.4/tremble_ladder_counselor_quest_inner_monologue_dialogue.py --gear jet_skates
    python storyworlds/worlds/gpt-5.4/tremble_ladder_counselor_quest_inner_monologue_dialogue.py --all --qa
    python storyworlds/worlds/gpt-5.4/tremble_ladder_counselor_quest_inner_monologue_dialogue.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "counselor_f"}
        male = {"boy", "man", "father", "counselor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.role == "counselor":
            return "counselor"
        return self.label or self.type
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
class Place:
    id: str
    label: str
    vista: str
    high_spot: str
    clue: str
    affords: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    title: str
    object_label: str
    object_phrase: str
    mission_line: str
    finish_line: str
    needs_height: bool = True
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
class LadderCfg:
    id: str
    label: str
    material: str
    wobble: int
    height: int
    safe_for: set[str] = field(default_factory=set)
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
class Gear:
    id: str
    label: str
    phrase: str
    grip_bonus: int
    calm_bonus: int
    sense: int
    text: str
    bad_reason: str
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
class Method:
    id: str
    label: str
    phrase: str
    calm_bonus: int
    focus_bonus: int
    sense: int
    coach_line: str
    inner_line: str
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


def _r_tremble(world: World) -> list[str]:
    out: list[str] = []
    cadet = world.get("cadet")
    ladder = world.get("ladder")
    if cadet.meters["on_ladder"] < THRESHOLD:
        return out
    if cadet.memes["fear"] + ladder.meters["wobble"] <= cadet.memes["calm"] + cadet.meters["steady"]:
        return out
    sig = ("tremble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cadet.meters["tremble"] += 1
    cadet.memes["doubt"] += 1
    out.append("__tremble__")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    cadet = world.get("cadet")
    ladder = world.get("ladder")
    quest_item = world.get("quest_item")
    if cadet.meters["on_ladder"] < THRESHOLD:
        return out
    power = cadet.meters["steady"] + cadet.memes["calm"] + cadet.memes["focus"]
    need = ladder.height + ladder.meters["wobble"]
    if power < need:
        return out
    sig = ("progress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cadet.meters["at_top"] += 1
    quest_item.meters["delivered"] += 1
    cadet.memes["pride"] += 1
    out.append("__success__")
    return out


def _r_retreat(world: World) -> list[str]:
    out: list[str] = []
    cadet = world.get("cadet")
    if cadet.meters["on_ladder"] < THRESHOLD:
        return out
    if cadet.meters["at_top"] >= THRESHOLD:
        return out
    if cadet.meters["tremble"] < THRESHOLD:
        return out
    if cadet.memes["fear"] < cadet.memes["calm"] + 2:
        return out
    sig = ("retreat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cadet.meters["back_down"] += 1
    out.append("__retreat__")
    return out


CAUSAL_RULES = [
    Rule(name="tremble", tag="body", apply=_r_tremble),
    Rule(name="progress", tag="quest", apply=_r_progress),
    Rule(name="retreat", tag="quest", apply=_r_retreat),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def sensible_gear() -> list[Gear]:
    return [g for g in GEAR.values() if g.sense >= SENSE_MIN]


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def compatible(place: Place, quest: Quest, ladder: LadderCfg, gear: Gear, method: Method) -> bool:
    if quest.id not in place.affords:
        return False
    if not quest.needs_height:
        return False
    if place.id not in ladder.safe_for:
        return False
    if gear.sense < SENSE_MIN or method.sense < SENSE_MIN:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            for ladder_id, ladder in LADDERS.items():
                for gear_id, gear in GEAR.items():
                    for method_id, method in METHODS.items():
                        if compatible(place, quest, ladder, gear, method):
                            combos.append((place_id, quest_id, ladder_id, gear_id, method_id))
    return combos


def fear_need(ladder: LadderCfg) -> int:
    return ladder.height + ladder.wobble


def support_power(gear: Gear, method: Method) -> int:
    return gear.grip_bonus + gear.calm_bonus + method.calm_bonus + method.focus_bonus


def outcome_of(params: "StoryParams") -> str:
    if params.place not in PLACES or params.quest not in QUESTS or params.ladder not in LADDERS:
        raise StoryError("(Invalid params: unknown place, quest, or ladder.)")
    if params.gear not in GEAR or params.method not in METHODS:
        raise StoryError("(Invalid params: unknown gear or method.)")
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    ladder = LADDERS[params.ladder]
    gear = GEAR[params.gear]
    method = METHODS[params.method]
    if not compatible(place, quest, ladder, gear, method):
        raise StoryError(explain_rejection(place, quest, ladder, gear, method))
    return "success" if support_power(gear, method) >= fear_need(ladder) else "pause"


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    cadet = sim.get("cadet")
    cadet.meters["on_ladder"] += 1
    propagate(sim, narrate=False)
    return {
        "tremble": cadet.meters["tremble"] >= THRESHOLD,
        "success": cadet.meters["at_top"] >= THRESHOLD,
        "retreat": cadet.meters["back_down"] >= THRESHOLD,
    }


def introduce(world: World, cadet: Entity, place: Place, quest: Quest) -> None:
    cadet.memes["wonder"] += 1
    world.say(
        f"In {place.label}, {cadet.id} had a quest. "
        f"{cadet.pronoun('possessive').capitalize()} mission was to {quest.mission_line}."
    )
    world.say(
        f"Outside the wide window, {place.vista}. The whole station felt like the start of a space adventure."
    )


def show_goal(world: World, cadet: Entity, quest: Quest, place: Place) -> None:
    item = world.get("quest_item")
    world.say(
        f"The {quest.object_label} had to reach {place.high_spot}, far above the floor. "
        f"{item.label.capitalize()} glimmered in {cadet.id}'s hands like a tiny star."
    )


def spot_ladder(world: World, cadet: Entity, ladder: LadderCfg, place: Place) -> None:
    cadet.memes["fear"] += float(ladder.height)
    world.say(
        f"Between {cadet.id} and the goal stood {ladder.label}, made of {ladder.material} and climbing toward {place.high_spot}."
    )
    world.say(
        f"{cadet.id} looked up, and {cadet.pronoun('possessive')} knees began to tremble."
    )
    world.say(
        f'"That ladder is tall," {cadet.id} whispered.'
    )


def inner_monologue(world: World, cadet: Entity, method: Method) -> None:
    world.say(
        f'Inside, {cadet.id} thought, "{method.inner_line}"'
    )


def counselor_arrives(world: World, counselor: Entity) -> None:
    counselor.memes["care"] += 1
    world.say(
        f"Just then, the station counselor came across the deck in soft silver shoes."
    )
    world.say(
        f'"I can see this is a big moment," the counselor said.'
    )


def warning(world: World, cadet: Entity) -> None:
    pred = predict_attempt(world)
    world.facts["predicted_tremble"] = pred["tremble"]
    world.facts["predicted_retreat"] = pred["retreat"]
    if pred["tremble"]:
        world.say(
            f'The counselor glanced from the ladder to {cadet.id}\'s tight hands. '
            f'"You do not have to rush," the counselor said.'
        )


def offer_help(world: World, counselor: Entity, gear: Gear, method: Method) -> None:
    world.say(
        f'"Let us make the climb smaller," the counselor said. "{method.coach_line}"'
    )
    world.say(
        f"Then the counselor {gear.text}."
    )


def accept_help(world: World, cadet: Entity, gear: Gear, method: Method) -> None:
    cadet.meters["steady"] += float(gear.grip_bonus)
    cadet.memes["calm"] += float(gear.calm_bonus + method.calm_bonus)
    cadet.memes["focus"] += float(method.focus_bonus)
    cadet.memes["trust"] += 1
    world.say(
        f'{cadet.id} nodded. "{gear.phrase} and {method.phrase}," {cadet.pronoun()} repeated, as if saying the plan could make it real.'
    )


def climb(world: World, cadet: Entity, ladder: LadderCfg) -> None:
    cadet.meters["on_ladder"] += 1
    world.say(
        f"{cadet.id} set one foot on the first rung of the ladder, then another."
    )
    markers = propagate(world, narrate=False)
    if "__tremble__" in markers:
        world.say(
            f"The metal gave a tiny hum, and {cadet.id}'s hands did tremble for a moment."
        )
    else:
        world.say(
            f"The ladder still felt tall, but {cadet.id}'s body stayed steadier than before."
        )


def coached_steps(world: World, cadet: Entity, method: Method) -> None:
    world.say(
        f'"{method.label.capitalize()}," the counselor called from below. "Only the next rung."'
    )
    world.say(
        f'Inside, {cadet.id} thought, "Only the next rung. Then one more."'
    )


def finish_or_pause(world: World, cadet: Entity, counselor: Entity, quest: Quest, place: Place) -> None:
    if cadet.meters["at_top"] >= THRESHOLD:
        cadet.memes["joy"] += 1
        world.say(
            f"Step by step, {cadet.id} reached {place.high_spot} and {quest.finish_line}."
        )
        world.say(
            f'"I did it!" {cadet.id} shouted.'
        )
        world.say(
            f'The counselor smiled up from the floor. "You did it by taking brave little steps."'
        )
    else:
        cadet.memes["relief"] += 1
        counselor.memes["care"] += 1
        world.say(
            f"{cadet.id} climbed a little way, then stopped and came back down carefully."
        )
        world.say(
            f'"Not today," {cadet.id} said, breathing hard.'
        )
        world.say(
            f'"That is all right," the counselor said. "A quest can wait for a better plan, and turning back safely is brave too."'
        )


def changed_ending(world: World, cadet: Entity, quest: Quest, place: Place) -> None:
    if cadet.meters["at_top"] >= THRESHOLD:
        world.say(
            f"After that, the high ladder in {place.label} no longer looked like a wall. It looked like a path."
        )
        world.say(
            f"The little {quest.object_label} shone at {place.high_spot}, and so did {cadet.id}'s face."
        )
    else:
        world.say(
            f"When {cadet.id} looked at the ladder again, it was still tall, but it was not a monster anymore."
        )
        world.say(
            f"The counselor had turned the scary climb into a practice path for another day."
        )


def tell(
    place: Place,
    quest: Quest,
    ladder: LadderCfg,
    gear: Gear,
    method: Method,
    *,
    cadet_name: str = "Nova",
    cadet_type: str = "girl",
    counselor_type: str = "counselor_m",
) -> World:
    world = World()
    cadet = world.add(Entity(id=cadet_name, kind="character", type=cadet_type, role="cadet", label=cadet_name))
    counselor = world.add(Entity(id="Counselor", kind="character", type=counselor_type, role="counselor", label="the counselor"))
    ladder_ent = world.add(Entity(id="ladder", type="ladder", label=ladder.label))
    quest_item = world.add(Entity(id="quest_item", type="quest_item", label=quest.object_phrase))
    world.add(Entity(id="place", type="place", label=place.label))

    ladder_ent.meters["wobble"] = float(ladder.wobble)
    cadet.memes["fear"] = float(ladder.height)
    cadet.memes["calm"] = 0.0
    cadet.memes["focus"] = 0.0
    cadet.meters["steady"] = 0.0
    cadet.meters["on_ladder"] = 0.0
    cadet.meters["at_top"] = 0.0
    cadet.meters["back_down"] = 0.0
    cadet.meters["tremble"] = 0.0
    quest_item.meters["delivered"] = 0.0

    world.facts.update(
        place=place,
        quest=quest,
        ladder_cfg=ladder,
        gear=gear,
        method=method,
        cadet=cadet,
        counselor=counselor,
        predicted_tremble=False,
        predicted_retreat=False,
    )

    introduce(world, cadet, place, quest)
    show_goal(world, cadet, quest, place)

    world.para()
    spot_ladder(world, cadet, ladder, place)
    inner_monologue(world, cadet, method)
    counselor_arrives(world, counselor)
    warning(world, cadet)
    offer_help(world, counselor, gear, method)
    accept_help(world, cadet, gear, method)

    world.para()
    climb(world, cadet, ladder)
    coached_steps(world, cadet, method)
    finish_or_pause(world, cadet, counselor, quest, place)

    world.para()
    changed_ending(world, cadet, quest, place)

    outcome = "success" if cadet.meters["at_top"] >= THRESHOLD else "pause"
    world.facts.update(
        outcome=outcome,
        finished=quest_item.meters["delivered"] >= THRESHOLD,
        trembled=cadet.meters["tremble"] >= THRESHOLD,
    )
    return world


PLACES = {
    "moon_tower": Place(
        id="moon_tower",
        label="the Moon Tower",
        vista="rings of small ships drifted above the gray moon",
        high_spot="the beacon shelf",
        clue="cold blue moonlight",
        affords={"beacon", "map", "seed"},
        tags={"space", "tower"},
    ),
    "comet_harbor": Place(
        id="comet_harbor",
        label="Comet Harbor",
        vista="glass docks glowed while comet dust sparkled beyond them",
        high_spot="the signal perch",
        clue="silver comet dust",
        affords={"beacon", "map"},
        tags={"space", "harbor"},
    ),
    "sun_garden": Place(
        id="sun_garden",
        label="the Sun Garden Dome",
        vista="warm lamps floated above rows of star-plants",
        high_spot="the upper growth rail",
        clue="golden leaf-light",
        affords={"seed"},
        tags={"space", "garden"},
    ),
}

QUESTS = {
    "beacon": Quest(
        id="beacon",
        title="Beacon Quest",
        object_label="signal crystal",
        object_phrase="the signal crystal",
        mission_line="carry the signal crystal to the high beacon so ships can see the station",
        finish_line="set the signal crystal into the beacon slot until the whole tower glowed",
        needs_height=True,
        tags={"beacon", "quest"},
    ),
    "map": Quest(
        id="map",
        title="Map Quest",
        object_label="star map chip",
        object_phrase="the star map chip",
        mission_line="bring the star map chip to the navigation nest before the scout shuttle launched",
        finish_line="slid the star map chip into the navigation nest and watched the route bloom in light",
        needs_height=True,
        tags={"map", "quest"},
    ),
    "seed": Quest(
        id="seed",
        title="Seed Quest",
        object_label="sun-seed vial",
        object_phrase="the sun-seed vial",
        mission_line="lift the sun-seed vial to the upper rail where the sleepy vines could drink light",
        finish_line="clipped the sun-seed vial to the upper rail and the vines opened like green stars",
        needs_height=True,
        tags={"garden", "quest"},
    ),
}

LADDERS = {
    "service_ladder": LadderCfg(
        id="service_ladder",
        label="the service ladder",
        material="silver rail-metal",
        wobble=1,
        height=3,
        safe_for={"moon_tower", "comet_harbor"},
        tags={"ladder", "metal"},
    ),
    "garden_ladder": LadderCfg(
        id="garden_ladder",
        label="the garden ladder",
        material="wide green composite",
        wobble=0,
        height=2,
        safe_for={"sun_garden"},
        tags={"ladder", "garden"},
    ),
    "rope_ladder": LadderCfg(
        id="rope_ladder",
        label="the rope ladder",
        material="flex-rope",
        wobble=2,
        height=3,
        safe_for={"comet_harbor"},
        tags={"ladder", "rope"},
    ),
}

GEAR = {
    "mag_boots": Gear(
        id="mag_boots",
        label="mag-boots",
        phrase="mag-boots first",
        grip_bonus=2,
        calm_bonus=0,
        sense=3,
        text="clicked a pair of mag-boots onto the cadet's shoes so each step would hold fast",
        bad_reason="mag-boots help feet stay on metal rungs",
        tags={"boots", "safety"},
    ),
    "safety_belt": Gear(
        id="safety_belt",
        label="safety belt",
        phrase="safety belt snug",
        grip_bonus=1,
        calm_bonus=1,
        sense=3,
        text="buckled on a safety belt and checked the clip twice",
        bad_reason="a safety belt gives backup if a climber feels shaky",
        tags={"belt", "safety"},
    ),
    "jet_skates": Gear(
        id="jet_skates",
        label="jet skates",
        phrase="jet skates on",
        grip_bonus=0,
        calm_bonus=0,
        sense=1,
        text="rolled out a pair of shiny jet skates",
        bad_reason="jet skates are flashy, but wheels and ladders do not belong together",
        tags={"wheels"},
    ),
}

METHODS = {
    "breathe_count": Method(
        id="breathe_count",
        label="breathe and count",
        phrase="breathe and count",
        calm_bonus=2,
        focus_bonus=1,
        sense=3,
        coach_line='Breathe in like you are filling a moon balloon, breathe out slowly, and count each rung.',
        inner_line="My heart is fast, but my breath can be slow. One rung. Then two.",
        tags={"breathing", "counselor"},
    ),
    "next_rung": Method(
        id="next_rung",
        label="eyes on the next rung",
        phrase="eyes on the next rung",
        calm_bonus=1,
        focus_bonus=2,
        sense=3,
        coach_line='Do not climb the whole ladder in your mind. Only look at the next rung and greet it.',
        inner_line="I do not have to climb the whole sky. I only need the next rung.",
        tags={"focus", "counselor"},
    ),
    "be_bold": Method(
        id="be_bold",
        label="just be bold",
        phrase="just be bold",
        calm_bonus=0,
        focus_bonus=0,
        sense=1,
        coach_line='Do not think about it. Just leap up fast.',
        inner_line="Maybe if I hurry, I will not notice being scared.",
        tags={"bad_advice"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ivy", "Zeta", "Astra", "Skye", "Nia"]
BOY_NAMES = ["Orion", "Leo", "Milo", "Finn", "Jett", "Arlo", "Tao", "Kai"]


@dataclass
class StoryParams:
    place: str
    quest: str
    ladder: str
    gear: str
    method: str
    cadet_name: str
    cadet_gender: str
    counselor_gender: str
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
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps you climb up or down to a high place. You use one rung at a time so your hands and feet stay steady."
        )
    ],
    "counselor": [
        (
            "What does a counselor do?",
            "A counselor helps people with big feelings and hard moments. They listen, stay calm, and teach safe ways to handle worry."
        )
    ],
    "breathing": [
        (
            "Why can slow breathing help when you feel scared?",
            "Slow breathing tells your body to calm down. When your body is calmer, it is easier to think about the next safe step."
        )
    ],
    "focus": [
        (
            "Why does looking at one step at a time help?",
            "A big job can feel less scary when you break it into small parts. One safe step is easier for your brain and body to do than thinking about the whole climb."
        )
    ],
    "boots": [
        (
            "What are mag-boots in a space story?",
            "Mag-boots are boots that hold onto metal surfaces. In a pretend space adventure, they help a climber feel steadier on metal rungs."
        )
    ],
    "belt": [
        (
            "What does a safety belt do?",
            "A safety belt clips a climber in for extra protection. It gives backup support if someone feels shaky."
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a bright signal light. It helps people find a place or see where to go."
        )
    ],
    "map": [
        (
            "What is a star map?",
            "A star map shows routes and places in space. Pilots use it to know where they are going."
        )
    ],
    "garden": [
        (
            "What is a space garden?",
            "A space garden is a place where plants are grown in a station or ship. People care for it with light, water, and lots of attention."
        )
    ],
}
KNOWLEDGE_ORDER = ["ladder", "counselor", "breathing", "focus", "boots", "belt", "beacon", "map", "garden"]


def generation_prompts(world: World) -> list[str]:
    cadet = world.facts["cadet"]
    place = world.facts["place"]
    quest = world.facts["quest"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old about a child with a quest in {place.label} who feels scared on a ladder. Include the words "tremble", "ladder", and "counselor".',
        f"Tell a gentle story where {cadet.id} has to {quest.mission_line}, but a station counselor helps {cadet.pronoun('object')} handle the scary climb with dialogue and inner thoughts.",
        'Write a simple quest story with dialogue and inner monologue, where a child takes brave little steps instead of rushing.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cadet = f["cadet"]
    quest = f["quest"]
    place = f["place"]
    gear = f["gear"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {cadet.id}, a young space cadet on a quest in {place.label}, and the station counselor who helps. The story follows the climb from fear to a safer plan."
        ),
        (
            "Why did the cadet feel scared?",
            f"{cadet.id} had to climb a ladder to reach {place.high_spot}, and the height made {cadet.pronoun('possessive')} knees tremble. The quest mattered, so the hard part could not simply be skipped."
        ),
        (
            "What did the counselor do to help?",
            f"The counselor slowed the moment down and gave {cadet.id} a real plan: {gear.phrase} and {method.phrase}. That helped {cadet.pronoun('object')} feel steadier in body and calmer in mind."
        ),
    ]
    if f["outcome"] == "success":
        qa.append(
            (
                "How did the cadet finish the quest?",
                f"{cadet.id} climbed one rung at a time until {cadet.pronoun()} reached {place.high_spot} and {quest.finish_line}. The small steps worked because the counselor's method turned a huge climb into manageable pieces."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"At first the ladder looked like a wall, but at the end it looked like a path. {cadet.id} was still the same child, yet now {cadet.pronoun()} knew a brave quest can be done in little steady steps."
            )
        )
    else:
        qa.append(
            (
                "Did the cadet fail?",
                f"No. {cadet.id} came down safely and learned what the climb would need next time. The counselor treated that careful choice as part of being brave, not as something shameful."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"The ladder was still tall, but it no longer felt like a monster. Because the counselor listened and planned with {cadet.id}, the scary thing became something {cadet.pronoun()} could practice another day."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ladder", "counselor"}
    tags |= set(world.facts["gear"].tags)
    tags |= set(world.facts["method"].tags)
    tags |= set(world.facts["quest"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_tower",
        quest="beacon",
        ladder="service_ladder",
        gear="mag_boots",
        method="breathe_count",
        cadet_name="Nova",
        cadet_gender="girl",
        counselor_gender="man",
    ),
    StoryParams(
        place="comet_harbor",
        quest="map",
        ladder="service_ladder",
        gear="safety_belt",
        method="next_rung",
        cadet_name="Orion",
        cadet_gender="boy",
        counselor_gender="woman",
    ),
    StoryParams(
        place="sun_garden",
        quest="seed",
        ladder="garden_ladder",
        gear="safety_belt",
        method="breathe_count",
        cadet_name="Luna",
        cadet_gender="girl",
        counselor_gender="woman",
    ),
    StoryParams(
        place="comet_harbor",
        quest="beacon",
        ladder="rope_ladder",
        gear="safety_belt",
        method="next_rung",
        cadet_name="Milo",
        cadet_gender="boy",
        counselor_gender="man",
    ),
]


def explain_rejection(place: Place, quest: Quest, ladder: LadderCfg, gear: Gear, method: Method) -> str:
    if quest.id not in place.affords:
        return (
            f"(No story: {quest.title} does not belong in {place.label}. "
            f"That place does not support that quest.)"
        )
    if place.id not in ladder.safe_for:
        return (
            f"(No story: {ladder.label} is not the right ladder for {place.label}. "
            f"Pick a ladder used in that location.)"
        )
    if gear.sense < SENSE_MIN:
        return (
            f"(Refusing gear '{gear.id}': {gear.bad_reason}. "
            f"A storyworld should prefer safer climbing help.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': this advice is too weak for a scary climb. "
            f"Choose a calmer, step-by-step method.)"
        )
    return "(No story: this combination is not a reasonable climbing plan.)"


ASP_RULES = r"""
valid(Place, Quest, Ladder, Gear, Method) :-
    affords(Place, Quest),
    needs_height(Quest),
    ladder_for(Ladder, Place),
    gear(Gear), sense_gear(Gear, GS), sense_min(M), GS >= M,
    method(Method), sense_method(Method, MS), MS >= M.

need(Ladder, H + W) :- height(Ladder, H), wobble(Ladder, W).
power(Gear, Method, GB + GC + MC + MF) :-
    grip_bonus(Gear, GB), calm_bonus_gear(Gear, GC),
    calm_bonus_method(Method, MC), focus_bonus(Method, MF).

outcome(success) :-
    chosen_ladder(L),
    chosen_gear(G),
    chosen_method(M),
    need(L, N),
    power(G, M, P),
    P >= N.

outcome(pause) :-
    chosen_ladder(L),
    chosen_gear(G),
    chosen_method(M),
    need(L, N),
    power(G, M, P),
    P < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for quest_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, quest_id))
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        if quest.needs_height:
            lines.append(asp.fact("needs_height", quest_id))
    for ladder_id, ladder in LADDERS.items():
        lines.append(asp.fact("ladder", ladder_id))
        lines.append(asp.fact("height", ladder_id, ladder.height))
        lines.append(asp.fact("wobble", ladder_id, ladder.wobble))
        for place_id in sorted(ladder.safe_for):
            lines.append(asp.fact("ladder_for", ladder_id, place_id))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("sense_gear", gear_id, gear.sense))
        lines.append(asp.fact("grip_bonus", gear_id, gear.grip_bonus))
        lines.append(asp.fact("calm_bonus_gear", gear_id, gear.calm_bonus))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense_method", method_id, method.sense))
        lines.append(asp.fact("calm_bonus_method", method_id, method.calm_bonus))
        lines.append(asp.fact("focus_bonus", method_id, method.focus_bonus))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_ladder", params.ladder),
            asp.fact("chosen_gear", params.gear),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos() matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

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
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space quest, a tall ladder, and a calm counselor."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ladder", choices=LADDERS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--cadet-name")
    ap.add_argument("--cadet-gender", choices=["girl", "boy"])
    ap.add_argument("--counselor-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and args.ladder and args.gear and args.method:
        place = PLACES[args.place]
        quest = QUESTS[args.quest]
        ladder = LADDERS[args.ladder]
        gear = GEAR[args.gear]
        method = METHODS[args.method]
        if not compatible(place, quest, ladder, gear, method):
            raise StoryError(explain_rejection(place, quest, ladder, gear, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.quest is None or combo[1] == args.quest)
        and (args.ladder is None or combo[2] == args.ladder)
        and (args.gear is None or combo[3] == args.gear)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, quest_id, ladder_id, gear_id, method_id = rng.choice(sorted(combos))
    cadet_gender = args.cadet_gender or rng.choice(["girl", "boy"])
    counselor_gender = args.counselor_gender or rng.choice(["woman", "man"])
    cadet_name = args.cadet_name or rng.choice(GIRL_NAMES if cadet_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place_id,
        quest=quest_id,
        ladder=ladder_id,
        gear=gear_id,
        method=method_id,
        cadet_name=cadet_name,
        cadet_gender=cadet_gender,
        counselor_gender=counselor_gender,
    )


def generate(params: StoryParams) -> StorySample:
    required = {
        "place": PLACES,
        "quest": QUESTS,
        "ladder": LADDERS,
        "gear": GEAR,
        "method": METHODS,
    }
    for field_name, registry in required.items():
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid params: unknown {field_name} '{value}'.)")
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    ladder = LADDERS[params.ladder]
    gear = GEAR[params.gear]
    method = METHODS[params.method]
    if not compatible(place, quest, ladder, gear, method):
        raise StoryError(explain_rejection(place, quest, ladder, gear, method))

    counselor_type = "counselor_f" if params.counselor_gender == "woman" else "counselor_m"
    world = tell(
        place,
        quest,
        ladder,
        gear,
        method,
        cadet_name=params.cadet_name,
        cadet_type=params.cadet_gender,
        counselor_type=counselor_type,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, ladder, gear, method) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
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
            header = (
                f"### {p.cadet_name}: {p.quest} at {p.place} "
                f"({p.ladder}, {p.gear}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
