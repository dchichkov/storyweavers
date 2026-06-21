#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sacred_pewter_conflict_bravery_tall_tale.py
======================================================================

A standalone story world for a child-facing tall tale about a brave youngster,
a sacred bell, and a windstorm that threatens the town's tiny hill chapel.

This world models a simple, state-driven premise:

- A town keeps a sacred pewter bell in a little chapel on the hill.
- A wild storm or danger threatens the bell and the people below.
- One brave child faces conflict with a fearful or doubtful grown-up and climbs
  the hill anyway.
- The child uses sensible gear and a grounded method to steady, protect, or ring
  the bell.
- The ending image proves what changed: the danger passes, the town gathers, and
  the sacred pewter bell means something deeper because of the child's bravery.

The prose leans gently toward tall-tale style: big images, playful exaggeration,
and a legendary ending, while still staying physically coherent enough for a
simulation and ASP parity checks.

Run it
------
    python storyworlds/worlds/gpt-5.4/sacred_pewter_conflict_bravery_tall_tale.py
    python storyworlds/worlds/gpt-5.4/sacred_pewter_conflict_bravery_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/sacred_pewter_conflict_bravery_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/sacred_pewter_conflict_bravery_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/sacred_pewter_conflict_bravery_tall_tale.py --verify
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
BRAVERY_INIT = 5.0
FEARFUL_MIN = 5
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
    movable: bool = False
    fragile: bool = False
    sheltering: bool = False
    sounding: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    hill: str
    town_noun: str
    sky: str
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
class Threat:
    id: str
    label: str
    verb: str
    image: str
    force: int
    end_sign: str
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
class Bell:
    id: str
    label: str
    phrase: str
    metal: str
    sacred: bool
    weight: int
    sound: str
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
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    grip: int = 0
    power: int = 0
    brave_bonus: int = 0
    sense: int = 2
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
    need_grip: int
    need_power: int
    works_for: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    fail_text: str = ""
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_shudder(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    bell = world.get("bell")
    chapel = world.get("chapel")
    if threat.meters["striking"] >= THRESHOLD and bell.meters["secured"] < THRESHOLD:
        sig = ("shudder",)
        if sig not in world.fired:
            world.fired.add(sig)
            bell.meters["risk"] += 1
            chapel.meters["danger"] += 1
            out.append("__risk__")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    bell = world.get("bell")
    town = world.get("town")
    child = world.get("child")
    if bell.meters["ringing"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            town.meters["warned"] += 1
            child.memes["hope"] += 1
            out.append("__ring__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    town = world.get("town")
    child = world.get("child")
    helper = world.get("helper")
    if threat.meters["calmed"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            town.meters["safe"] += 1
            child.memes["relief"] += 1
            helper.memes["relief"] += 1
            out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule(name="shudder", tag="physical", apply=_r_shudder),
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def method_fits(threat: Threat, method: Method) -> bool:
    return threat.id in method.works_for


def sensible_gear() -> list[Gear]:
    return [g for g in GEARS.values() if g.sense >= SENSE_MIN]


def bravery_score(child: Entity, gear: Gear, method: Method, helper: Entity) -> int:
    score = int(child.memes["bravery"])
    score += gear.brave_bonus
    if helper.memes["doubt"] >= THRESHOLD:
        score -= 1
    if "steady" in helper.traits or "kind" in helper.traits:
        score += 1
    if method.id == "ring_warning":
        score += 1
    return score


def needed_bravery(threat: Threat) -> int:
    return threat.force + 2


def action_power(gear: Gear, method: Method) -> int:
    return gear.power + method.need_power


def action_grip(gear: Gear, method: Method) -> int:
    return gear.grip - method.need_grip


def can_face(threat: Threat, bell: Bell, gear: Gear, method: Method, child: Entity, helper: Entity) -> bool:
    if gear.sense < SENSE_MIN:
        return False
    if not method_fits(threat, method):
        return False
    if action_grip(gear, method) < 0:
        return False
    return bravery_score(child, gear, method, helper) >= needed_bravery(threat) and action_power(gear, method) >= threat.force


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    dummy_child = Entity(id="child", kind="character", type="girl", role="child")
    dummy_child.memes["bravery"] = BRAVERY_INIT
    dummy_helper = Entity(id="helper", kind="character", type="father", role="helper", traits=["kind"])
    dummy_helper.memes["doubt"] = 0
    bell = BELLS["chapel_bell"]
    for setting_id in SETTINGS:
        for threat_id, threat in THREATS.items():
            for gear_id, gear in GEARS.items():
                for method_id, method in METHODS.items():
                    if can_face(threat, bell, gear, method, dummy_child, dummy_helper):
                        combos.append((setting_id, threat_id, gear_id, method_id))
    return combos


def predict_outcome(setting: Setting, threat: Threat, bell: Bell, gear: Gear, method: Method, child: Entity, helper: Entity) -> dict:
    outcome = can_face(threat, bell, gear, method, child, helper)
    return {
        "success": outcome,
        "risk": threat.force,
        "need": needed_bravery(threat),
    }


def begin_tale(world: World, child: Entity, helper: Entity, bell: Bell) -> None:
    town = world.setting.town_noun
    world.say(
        f"In {world.setting.place}, folks liked to say the wind could comb a horse's mane from half a mile away. "
        f"At the top of {world.setting.hill} stood a little chapel, and in that chapel hung {bell.phrase}, "
        f"a sacred {bell.metal} bell the town loved as dearly as bread on winter mornings."
    )
    world.say(
        f"{child.id} was the sort of {child.type} who walked straight at hard things, while {helper.label_word} "
        f"was the sort who counted every worry twice before breakfast."
    )
    world.say(
        f"People said that when the bell sang, even the geese in the marsh stood still to listen. "
        f"That was a tall saying, but in {town}, nobody bothered to argue with it."
    )


def storm_rises(world: World, child: Entity, helper: Entity, threat: Threat, bell: Bell) -> None:
    helper.memes["doubt"] += 1
    threat_ent = world.get("threat")
    threat_ent.meters["striking"] = 1
    propagate(world, narrate=False)
    world.say(
        f"One afternoon, the {threat.label} came {threat.verb} over the fields, and {threat.image}. "
        f"The chapel windows rattled. The sacred pewter bell shivered on its beam as if it knew trouble by name."
    )
    world.say(
        f'"Stay below," said {helper.label_word} {helper.id}. "{world.setting.hill.capitalize()} is no place for little feet today."'
    )


def child_decides(world: World, child: Entity, helper: Entity, threat: Threat, method: Method) -> None:
    child.memes["conflict"] += 1
    child.memes["resolve"] += 1
    world.say(
        f'But {child.id} looked up at the hill and answered, "If the bell goes quiet, the town goes unwarned." '
        f"It was the kind of answer that makes a room feel smaller and a heart feel bigger."
    )
    if method.id == "ring_warning":
        world.say(
            f"{child.id} did not boast. {child.pronoun().capitalize()} only set {child.pronoun('possessive')} jaw and started for the path, "
            f"planning to ring the bell so loud the whole valley would hear."
        )
    else:
        world.say(
            f"{child.id} did not stomp or fuss. {child.pronoun().capitalize()} simply started for the path, "
            f"meaning to save the bell before the storm could tear it loose."
        )


def helper_objects(world: World, child: Entity, helper: Entity, gear: Gear) -> None:
    world.say(
        f"{helper.id} caught {child.pronoun('possessive')} sleeve. "
        f'"Bravery is not the same as foolishness," {helper.pronoun()} said. '
        f'"If you climb, you climb with {gear.phrase}."'
    )


def gear_up(world: World, child: Entity, gear: Gear) -> None:
    child.meters["equipped"] += 1
    child.attrs["gear"] = gear.id
    world.say(
        f"So {child.id} pulled on {gear.phrase}. In the tall-talk of that town, "
        f"{gear.label} fit so snugly they could have held onto a rainbow, though really they just made the climb safer."
    )


def climb(world: World, child: Entity, threat: Threat) -> None:
    child.meters["on_hill"] += 1
    child.memes["fear"] += 1
    world.say(
        f"Up {world.setting.hill} {child.pronoun()} went while the {threat.label} shoved at the grass in long gray hands. "
        f"Every step felt as heavy as a bucket of nails, and every step still went forward."
    )


def do_method(world: World, child: Entity, threat: Threat, bell: Bell, method: Method, gear: Gear, helper: Entity) -> bool:
    success = can_face(threat, bell, gear, method, child, helper)
    bell_ent = world.get("bell")
    threat_ent = world.get("threat")
    if success:
        bell_ent.meters["secured"] += 1
        if method.id == "ring_warning":
            bell_ent.meters["ringing"] += 1
        threat_ent.meters["calmed"] += 1
        propagate(world, narrate=False)
        world.say(method.text.format(child=child.id, sound=bell.sound, label=bell.label))
    else:
        bell_ent.meters["risk"] += 1
        bell_ent.meters["tilting"] += 1
        propagate(world, narrate=False)
        world.say(method.fail_text.format(child=child.id, label=bell.label))
    return success


def success_ending(world: World, child: Entity, helper: Entity, threat: Threat, bell: Bell, method: Method) -> None:
    town = world.get("town")
    child.memes["lesson"] += 1
    helper.memes["pride"] += 1
    if town.meters["warned"] >= THRESHOLD:
        world.say(
            f"Then the bell gave out {bell.sound}, and the sound ran downhill faster than the rain. "
            f"Doors opened, lanterns bobbed, and the town moved together instead of panicking apart."
        )
    world.say(
        f"When the {threat.label} finally lost its temper and wandered off, {helper.id} met {child.id} at the bottom of the path and hugged "
        f"{child.pronoun('object')} hard enough to rattle the buttons."
    )
    world.say(
        f'From that day on, whenever neighbors spoke of the sacred pewter bell, they also spoke of {child.id}. '
        f"They said {child.pronoun()} had a heart tall enough to stand beside the steeple, and for once the tall tale was not much taller than the truth."
    )


def failure_ending(world: World, child: Entity, helper: Entity, threat: Threat, bell: Bell) -> None:
    child.memes["lesson"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"{bell.label.capitalize()} slipped crooked and struck the chapel wall with a sorrowful clang. "
        f"{child.id} scrambled down safely, but the town heard the danger too late and spent the night hauling shutters shut in the dark."
    )
    world.say(
        f"{helper.id} wrapped a blanket around {child.id} and whispered that trying to help had been brave, but brave plans still need the right tools. "
        f"The next spring, the town hung the bell again with stronger beams and wiser ropes."
    )


def tell(setting: Setting, threat: Threat, bell: Bell, gear: Gear, method: Method,
         child_name: str = "Mara", child_type: str = "girl",
         helper_name: str = "Jon", helper_type: str = "father",
         helper_trait: str = "kind") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=["brave", "small"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=[helper_trait, "steady"]))
    world.add(Entity(id="chapel", type="chapel", label="the chapel", sheltering=True))
    world.add(Entity(id="town", type="town", label=setting.town_noun))
    world.add(Entity(id="bell", type="bell", label=bell.label, movable=True, fragile=True, sounding=True))
    world.add(Entity(id="threat", type="threat", label=threat.label))

    child.memes["bravery"] = BRAVERY_INIT
    child.memes["fear"] = 0.0
    child.memes["resolve"] = 0.0
    child.memes["conflict"] = 0.0
    helper.memes["doubt"] = 0.0
    helper.memes["relief"] = 0.0
    world.get("bell").meters["secured"] = 0.0
    world.get("bell").meters["risk"] = 0.0
    world.get("bell").meters["ringing"] = 0.0
    world.get("chapel").meters["danger"] = 0.0
    world.get("town").meters["warned"] = 0.0
    world.get("town").meters["safe"] = 0.0
    world.get("threat").meters["striking"] = 0.0
    world.get("threat").meters["calmed"] = 0.0
    world.facts["predicted"] = predict_outcome(setting, threat, bell, gear, method, child, helper)

    begin_tale(world, child, helper, bell)
    world.para()
    storm_rises(world, child, helper, threat, bell)
    child_decides(world, child, helper, threat, method)
    helper_objects(world, child, helper, gear)
    gear_up(world, child, gear)
    world.para()
    climb(world, child, threat)
    success = do_method(world, child, threat, bell, method, gear, helper)
    world.para()
    if success:
        success_ending(world, child, helper, threat, bell, method)
        outcome = "saved"
    else:
        failure_ending(world, child, helper, threat, bell)
        outcome = "lost"

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        threat_cfg=threat,
        bell_cfg=bell,
        gear_cfg=gear,
        method_cfg=method,
        outcome=outcome,
        conflict=child.memes["conflict"] >= THRESHOLD,
        bravery=bravery_score(child, gear, method, helper),
        need=needed_bravery(threat),
        town_warned=world.get("town").meters["warned"] >= THRESHOLD,
        bell_saved=world.get("bell").meters["secured"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "hollow": Setting(
        id="hollow",
        place="Juniper Hollow",
        hill="Chapel Hill",
        town_noun="the town below",
        sky="a sky with room for weather",
        tags={"hill", "chapel"},
    ),
    "prairie": Setting(
        id="prairie",
        place="Silver Prairie",
        hill="Lantern Hill",
        town_noun="the little prairie town",
        sky="a sky broad as a tablecloth",
        tags={"prairie", "chapel"},
    ),
    "riverbend": Setting(
        id="riverbend",
        place="Willow Riverbend",
        hill="Old Bell Rise",
        town_noun="the river town",
        sky="a sky stretched wide over the reeds",
        tags={"river", "chapel"},
    ),
}

THREATS = {
    "windstorm": Threat(
        id="windstorm",
        label="windstorm",
        verb="charging",
        image="it bent the reeds flat and made the weathercock spin like a toy top",
        force=2,
        end_sign="the wind went grumbling east",
        tags={"wind", "storm"},
    ),
    "ice_rain": Threat(
        id="ice_rain",
        label="ice rain",
        verb="hissing",
        image="it stitched silver lines through the air and glazed every rail with slick shine",
        force=3,
        end_sign="the last cold drops slipped from the eaves",
        tags={"rain", "ice"},
    ),
    "dust_gale": Threat(
        id="dust_gale",
        label="dust gale",
        verb="rolling",
        image="it made the whole road look like it was trying to gallop away",
        force=2,
        end_sign="the dust settled back into the wheel ruts",
        tags={"dust", "wind"},
    ),
}

BELLS = {
    "chapel_bell": Bell(
        id="chapel_bell",
        label="the bell",
        phrase="a sacred pewter bell no bigger than a wash pot and no less important than sunrise",
        metal="pewter",
        sacred=True,
        weight=2,
        sound="three brave peals that bounced from barn roof to barn roof",
        tags={"sacred", "pewter", "bell"},
    ),
}

GEARS = {
    "rope_gloves": Gear(
        id="rope_gloves",
        label="rope gloves",
        phrase="thick rope gloves and a leather belt",
        protects={"wind", "dust"},
        grip=2,
        power=1,
        brave_bonus=1,
        sense=3,
        tags={"gloves", "rope"},
    ),
    "spike_boots": Gear(
        id="spike_boots",
        label="spike boots",
        phrase="spike boots and a short safety rope",
        protects={"ice", "wind"},
        grip=3,
        power=1,
        brave_bonus=1,
        sense=3,
        tags={"boots", "rope"},
    ),
    "shawl": Gear(
        id="shawl",
        label="grand shawl",
        phrase="a wool shawl wrapped twice around the shoulders",
        protects={"cold"},
        grip=0,
        power=0,
        brave_bonus=0,
        sense=1,
        tags={"shawl"},
    ),
    "ladder_belt": Gear(
        id="ladder_belt",
        label="ladder belt",
        phrase="a ladder belt with iron hooks and grippy gloves",
        protects={"wind", "ice", "dust"},
        grip=3,
        power=2,
        brave_bonus=1,
        sense=3,
        tags={"belt", "hooks"},
    ),
}

METHODS = {
    "ring_warning": Method(
        id="ring_warning",
        label="ring the bell",
        need_grip=1,
        need_power=1,
        works_for={"windstorm", "ice_rain", "dust_gale"},
        text="{child} braced both feet, grabbed the rope, and rang {label} until it sent {sound} across the roofs. With the town warned and the beam steadied, the worst of the danger broke apart.",
        qa_text="rang the bell to warn everyone and steadied it at the same time",
        fail_text="{child} tugged for all {child} was worth, but the rope whipped wild and {label} lurched harder instead of steadier.",
        tags={"bell", "warning"},
    ),
    "lash_beam": Method(
        id="lash_beam",
        label="lash the beam",
        need_grip=2,
        need_power=1,
        works_for={"windstorm", "dust_gale"},
        text="{child} crawled along the beam, looped the safety line twice, and lashed {label} tight. After that, the storm could only grumble and shove while the bell held fast.",
        qa_text="lashed the bell beam tight with a safety line",
        fail_text="{child} tried to lash the beam, but the line slipped and {label} kept bucking in the gusts.",
        tags={"rope", "beam"},
    ),
    "wedge_clapper": Method(
        id="wedge_clapper",
        label="wedge the clapper",
        need_grip=2,
        need_power=1,
        works_for={"ice_rain"},
        text="{child} climbed close, wedged the clapper safe, and braced the bell so the ice could not jerk it loose. Little by little, the frozen rattling gave up.",
        qa_text="wedged the clapper and braced the bell against the ice",
        fail_text="{child} reached for the clapper, but the slick ice turned the job into a losing wrestle.",
        tags={"ice", "clapper"},
    ),
}

GIRL_NAMES = ["Mara", "Ruth", "Nell", "Elsie", "Willa", "June", "Ada", "Pearl"]
BOY_NAMES = ["Eli", "Jude", "Cal", "Silas", "Ben", "Owen", "Toby", "Ash"]
HELPER_NAMES = ["Jon", "Mabel", "Rosa", "Eben", "Clara", "Paul", "Mae", "Ira"]
HELPER_TRAITS = ["kind", "steady", "careful", "weatherwise"]


@dataclass
class StoryParams:
    setting: str
    threat: str
    bell: str
    gear: str
    method: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    helper_trait: str
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
    "sacred": [
        (
            "What does sacred mean?",
            "Sacred means something is deeply special and treated with great care and respect. People often use the word for a place or object that matters to a whole community."
        )
    ],
    "pewter": [
        (
            "What is pewter?",
            "Pewter is a soft gray metal. People have used it to make cups, plates, and other objects for a very long time."
        )
    ],
    "bell": [
        (
            "Why do towns ring bells in emergencies?",
            "A loud bell can reach many people at once. It warns everyone quickly, even before they can see the danger for themselves."
        )
    ],
    "wind": [
        (
            "Why is a strong wind dangerous on a hill?",
            "A strong wind can push people off balance and shake loose things that are hanging up high. Hills and open places often feel wind more strongly because there is less to block it."
        )
    ],
    "ice": [
        (
            "Why is ice rain slippery?",
            "Ice rain freezes on cold surfaces and makes them smooth and slick. That makes walking and climbing much harder."
        )
    ],
    "rope": [
        (
            "Why can rope help in a storm?",
            "A good rope helps hold things steady and gives people something firm to grip. That matters when the weather is pushing and pulling."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared. It does not mean ignoring danger; it means facing danger wisely."
        )
    ],
}

KNOWLEDGE_ORDER = ["sacred", "pewter", "bell", "wind", "ice", "rope", "bravery"]


def pair_role(helper: Entity) -> str:
    return f"{helper.label_word} {helper.id}" if helper.id else helper.label_word


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    threat = f["threat_cfg"]
    bell = f["bell_cfg"]
    method = f["method_cfg"]
    return [
        f'Write a short tall tale for a young child about bravery and conflict in a small town, and include the words "sacred" and "pewter".',
        f"Tell a child-friendly story where {child.id} climbs a hill during a {threat.label} to save a sacred pewter bell and uses {method.label}.",
        f"Write a gentle legend-like story in tall-tale style where a child argues with a worried grown-up, chooses brave action, and protects something sacred for the whole town.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    threat = f["threat_cfg"]
    bell = f["bell_cfg"]
    gear = f["gear_cfg"]
    method = f["method_cfg"]
    pred = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a brave child in {world.setting.place}, and {helper.id}, the worried {helper.label_word} who tried to keep {child.pronoun('object')} safe."
        ),
        (
            "What was special about the bell?",
            f"The bell was sacred to the town, and it was made of pewter. People treated it as a sign that the whole town belonged together."
        ),
        (
            f"Why was there conflict between {child.id} and {helper.id}?",
            f"There was conflict because {helper.id} wanted {child.id} to stay below the hill, but {child.id} believed the town needed help right away. The storm made the choice feel urgent and dangerous."
        ),
        (
            f"Why did {child.id} climb the hill?",
            f"{child.id} climbed because the {threat.label} was threatening the chapel bell and the town below. {child.pronoun().capitalize()} believed someone had to act before the danger grew worse."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                f"How did {child.id} save the bell?",
                f"{child.id} used {gear.label} and {method.qa_text}. Those tools and actions gave {child.pronoun('object')} enough grip and strength to beat the storm."
            )
        )
        if f["town_warned"]:
            qa.append(
                (
                    "How did the bell help the town?",
                    f"The ringing warned everyone quickly, so people could move together instead of being surprised. The bell turned one child's brave climb into help for the whole town."
                )
            )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the danger passing and the town remembering {child.id}'s bravery beside the sacred pewter bell. The ending shows that the bell became even more meaningful after it was saved."
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id}'s plan work?",
                f"No, the plan did not fully work that day. {child.id} was brave, but the storm was too strong for those tools and methods."
            )
        )
        qa.append(
            (
                "What did everyone learn?",
                f"They learned that bravery matters, but brave hearts still need the right gear. The town rebuilt more wisely after seeing how hard the storm struck."
            )
        )
    qa.append(
        (
            f"Was {child.id} brave even though the hill was scary?",
            f"Yes. {child.id} felt fear, but kept going because helping the town mattered more. The story treats bravery as wise action, not as pretending nothing is frightening."
        )
    )
    if pred["success"]:
        qa.append(
            (
                f"How hard was the danger compared with {child.id}'s bravery?",
                f"The danger needed a bravery score of at least {pred['need']}, and {child.id} reached that with the right gear and method. That is why the rescue worked instead of turning into a worse accident."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sacred", "pewter", "bell", "bravery"}
    threat = world.facts["threat_cfg"]
    gear = world.facts["gear_cfg"]
    method = world.facts["method_cfg"]
    if "wind" in threat.tags or "dust" in threat.tags:
        tags.add("wind")
    if "ice" in threat.tags:
        tags.add("ice")
    if "rope" in gear.tags or "rope" in method.tags:
        tags.add("rope")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="hollow",
        threat="windstorm",
        bell="chapel_bell",
        gear="rope_gloves",
        method="ring_warning",
        child_name="Mara",
        child_type="girl",
        helper_name="Jon",
        helper_type="father",
        helper_trait="kind",
    ),
    StoryParams(
        setting="prairie",
        threat="dust_gale",
        bell="chapel_bell",
        gear="ladder_belt",
        method="lash_beam",
        child_name="Eli",
        child_type="boy",
        helper_name="Mae",
        helper_type="aunt",
        helper_trait="steady",
    ),
    StoryParams(
        setting="riverbend",
        threat="ice_rain",
        bell="chapel_bell",
        gear="spike_boots",
        method="wedge_clapper",
        child_name="June",
        child_type="girl",
        helper_name="Ira",
        helper_type="uncle",
        helper_trait="weatherwise",
    ),
    StoryParams(
        setting="prairie",
        threat="windstorm",
        bell="chapel_bell",
        gear="ladder_belt",
        method="ring_warning",
        child_name="Cal",
        child_type="boy",
        helper_name="Rosa",
        helper_type="mother",
        helper_trait="careful",
    ),
]


def explain_combo(threat: Threat, gear: Gear, method: Method) -> str:
    if gear.sense < SENSE_MIN:
        return (
            f"(No story: {gear.label} is a weak or foolish choice for climbing into a {threat.label}. "
            f"Pick steadier gear like rope gloves, spike boots, or the ladder belt.)"
        )
    if not method_fits(threat, method):
        return (
            f"(No story: {method.label} does not honestly solve the problem caused by {threat.label}. "
            f"Choose a method that fits this kind of danger.)"
        )
    if action_grip(gear, method) < 0:
        return (
            f"(No story: {gear.label} does not give enough grip to {method.label} during a {threat.label}. "
            f"The child would likely slip before helping.)"
        )
    dummy_child = Entity(id="child", kind="character", type="girl")
    dummy_child.memes["bravery"] = BRAVERY_INIT
    dummy_helper = Entity(id="helper", kind="character", type="father", traits=["kind"])
    dummy_helper.memes["doubt"] = 0
    if not can_face(threat, BELLS["chapel_bell"], gear, method, dummy_child, dummy_helper):
        return (
            f"(No story: this plan is too weak for the {threat.label}. A tall tale may sound big, "
            f"but the world still needs a believable way for bravery to succeed.)"
        )
    return "(No story: this combination does not fit the world.)"


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
method_fits(T, M) :- works_for(M, T).
sensible_gear(G) :- gear(G), sense(G, S), sense_min(Min), S >= Min.
enough_grip(G, M) :- grip(G, GG), need_grip(M, MG), GG >= MG.
enough_power(T, G, M) :- force(T, FT), power(G, GP), need_power(M, MP), GP + MP >= FT.

% Helper is calm in the gate model; bravery comes from the child plus the gear
% and a small bonus for warning everyone by ringing the bell.
bravery_score(T, G, M, B) :-
    bravery_init(B0), brave_bonus(G, GB), method_bonus(M, MB), B = B0 + GB + MB.
needed(T, N) :- force(T, F), N = F + 2.

valid_combo(S, T, G, M) :-
    setting(S), threat(T), gear(G), method(M),
    sensible_gear(G), method_fits(T, M),
    enough_grip(G, M), enough_power(T, G, M),
    bravery_score(T, G, M, B), needed(T, N), B >= N.

% --- scenario outcome ------------------------------------------------------
outcome(saved) :- chosen_setting(S), chosen_threat(T), chosen_gear(G), chosen_method(M),
                  valid_combo(S, T, G, M).
outcome(lost) :- chosen_setting(_), chosen_threat(_), chosen_gear(_), chosen_method(_),
                 not outcome(saved).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("force", tid, t.force))
    for bid, bell in BELLS.items():
        lines.append(asp.fact("bell", bid))
        if bell.sacred:
            lines.append(asp.fact("sacred", bid))
        lines.append(asp.fact("weight", bid, bell.weight))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("sense", gid, g.sense))
        lines.append(asp.fact("grip", gid, g.grip))
        lines.append(asp.fact("power", gid, g.power))
        lines.append(asp.fact("brave_bonus", gid, g.brave_bonus))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("need_grip", mid, m.need_grip))
        lines.append(asp.fact("need_power", mid, m.need_power))
        lines.append(asp.fact("method_bonus", mid, 1 if mid == "ring_warning" else 0))
        for t in sorted(m.works_for):
            lines.append(asp.fact("works_for", mid, t))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_threat", params.threat),
        asp.fact("chosen_gear", params.gear),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def outcome_of(params: StoryParams) -> str:
    child = Entity(id="child", kind="character", type=params.child_type, role="child")
    helper = Entity(id="helper", kind="character", type=params.helper_type, role="helper", traits=[params.helper_trait, "steady"])
    child.memes["bravery"] = BRAVERY_INIT
    helper.memes["doubt"] = 0
    ok = can_face(
        THREATS[params.threat],
        BELLS[params.bell],
        GEARS[params.gear],
        METHODS[params.method],
        child,
        helper,
    )
    return "saved" if ok else "lost"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - python_set))
    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")
    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a child, a sacred pewter bell, a storm, and a brave climb."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--bell", choices=BELLS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    bell = args.bell or "chapel_bell"
    if bell not in BELLS:
        raise StoryError(f"(No story: unknown bell '{bell}'.)")
    if args.threat and args.gear and args.method:
        threat = THREATS[args.threat]
        gear = GEARS[args.gear]
        method = METHODS[args.method]
        if not can_face(threat, BELLS[bell], gear, method,
                        Entity(id="child", kind="character", type="girl", meters=defaultdict(float), memes=defaultdict(float, {"bravery": BRAVERY_INIT})),
                        Entity(id="helper", kind="character", type="father", traits=["kind"], meters=defaultdict(float), memes=defaultdict(float, {"doubt": 0}))):
            raise StoryError(explain_combo(threat, gear, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.threat is None or c[1] == args.threat)
        and (args.gear is None or c[2] == args.gear)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, threat_id, gear_id, method_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    child_name = _pick_name(rng, child_type)
    helper_name = rng.choice(HELPER_NAMES)
    helper_trait = rng.choice(HELPER_TRAITS)
    return StoryParams(
        setting=setting_id,
        threat=threat_id,
        bell=bell,
        gear=gear_id,
        method=method_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        threat = THREATS[params.threat]
        bell = BELLS[params.bell]
        gear = GEARS[params.gear]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err!s}.)") from None
    child = Entity(id="child", kind="character", type=params.child_type, role="child")
    helper = Entity(id="helper", kind="character", type=params.helper_type, role="helper", traits=[params.helper_trait, "steady"])
    child.memes["bravery"] = BRAVERY_INIT
    helper.memes["doubt"] = 0
    if not can_face(threat, bell, gear, method, child, helper):
        raise StoryError(explain_combo(threat, gear, method))
    world = tell(
        setting=setting,
        threat=threat,
        bell=bell,
        gear=gear,
        method=method,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_trait=params.helper_trait,
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
        print(asp_program("", "#show valid_combo/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, threat, gear, method) combos:\n")
        for setting_id, threat_id, gear_id, method_id in combos:
            print(f"  {setting_id:10} {threat_id:10} {gear_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.threat} at {p.setting} ({p.gear}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
