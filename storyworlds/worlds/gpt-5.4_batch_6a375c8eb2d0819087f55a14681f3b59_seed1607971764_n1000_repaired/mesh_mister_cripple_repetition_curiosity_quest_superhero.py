#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mesh_mister_cripple_repetition_curiosity_quest_superhero.py
======================================================================================

A standalone storyworld for a small superhero quest. A child hero joins the
mentor Mister Mesh to recover a missing machine-part before the city helper it
belongs to fails. The world is built around three required story instruments:

- Repetition: Mister Mesh teaches a clue-chant and the hero repeats it.
- Curiosity: the hero's questions and clue-following drive the middle.
- Quest: the pair cross the neighborhood to recover the missing part.

The required seed words appear naturally in the domain:
- "mesh" in Mister Mesh and in a rescue tool
- "mister" in the mentor's superhero name
- "cripple" in the warning that a missing part can cripple a machine

The world is intentionally small and constraint-checked:
- each mission needs the right kind of missing part
- each hiding place needs a gadget that can reasonably retrieve that part
- explicit invalid choices raise StoryError with a readable reason

Run it
------
python storyworlds/worlds/gpt-5.4/mesh_mister_cripple_repetition_curiosity_quest_superhero.py
python storyworlds/worlds/gpt-5.4/mesh_mister_cripple_repetition_curiosity_quest_superhero.py --qa
python storyworlds/worlds/gpt-5.4/mesh_mister_cripple_repetition_curiosity_quest_superhero.py --all
python storyworlds/worlds/gpt-5.4/mesh_mister_cripple_repetition_curiosity_quest_superhero.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
    place: str
    machine: str
    need: str
    opening: str
    danger: str
    ending: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    family: str
    material: str
    shine: str
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
class HidingPlace:
    id: str
    label: str
    intro: str
    clue_line: str
    reach: str
    fail_text: str
    found_text: str
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
class Gadget:
    id: str
    label: str
    phrase: str
    works_for: set[str]
    materials: set[str]
    action_text: str
    qa_text: str
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


def _r_missing_trouble(world: World) -> list[str]:
    machine = world.get("machine")
    hero = world.get("hero")
    mentor = world.get("mentor")
    if machine.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_trouble", machine.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    machine.meters["trouble"] += 1
    hero.memes["curiosity"] += 1
    mentor.memes["urgency"] += 1
    return ["__missing__"]


def _r_bad_reach(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["stuck"] < THRESHOLD or hero.memes["grab_by_hand"] < THRESHOLD:
        return []
    sig = ("bad_reach", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.meters["risk"] += 1
    return ["__risk__"]


def _r_restored_relief(world: World) -> list[str]:
    machine = world.get("machine")
    hero = world.get("hero")
    mentor = world.get("mentor")
    if machine.meters["restored"] < THRESHOLD:
        return []
    sig = ("restored_relief", machine.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    machine.meters["trouble"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    mentor.memes["pride"] += 1
    return ["__restored__"]


CAUSAL_RULES = [
    Rule(name="missing_trouble", tag="physical", apply=_r_missing_trouble),
    Rule(name="bad_reach", tag="physical", apply=_r_bad_reach),
    Rule(name="restored_relief", tag="social", apply=_r_restored_relief),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


MISSIONS = {
    "beacon": Mission(
        id="beacon",
        place="the hill beacon",
        machine="beacon wheel",
        need="power",
        opening="The hill beacon blinked weakly over the little city.",
        danger="Without its heart-piece, the evening fog would creep in early.",
        ending="Soon the beacon spun gold over the roofs again.",
        tags={"beacon", "machine"},
    ),
    "bridge": Mission(
        id="bridge",
        place="the river bridge bell",
        machine="bridge bell",
        need="signal",
        opening="The bridge bell above the river gave only a tiny click instead of a proud ring.",
        danger="Boats and carts both listened for that bell, and silence made everyone hesitate.",
        ending="Soon the bridge bell rang clear and bright over the water.",
        tags={"bridge", "machine"},
    ),
    "garden": Mission(
        id="garden",
        place="the glass garden fan",
        machine="garden fan",
        need="wind",
        opening="Inside the glass garden, the big fan barely turned.",
        danger="Warm air pressed under the roof, and the tender vines drooped at once.",
        ending="Soon the garden fan whirled cool air through every leaf.",
        tags={"garden", "machine"},
    ),
}

ITEMS = {
    "sun_cell": LostItem(
        id="sun_cell",
        label="sun cell",
        phrase="the bright sun cell",
        family="power",
        material="metal",
        shine="glimmered like a trapped drop of morning",
        tags={"power", "metal"},
    ),
    "echo_key": LostItem(
        id="echo_key",
        label="echo key",
        phrase="the silver echo key",
        family="signal",
        material="metal",
        shine="winked whenever it caught a stripe of light",
        tags={"signal", "metal"},
    ),
    "breeze_vane": LostItem(
        id="breeze_vane",
        label="breeze vane",
        phrase="the little breeze vane",
        family="wind",
        material="cloth",
        shine="fluttered even when the air felt still",
        tags={"wind", "cloth"},
    ),
}

HIDING_PLACES = {
    "kite_tree": HidingPlace(
        id="kite_tree",
        label="the kite tree",
        intro="At the end of Hero Lane stood a tree full of old ribbons and one brave red kite.",
        clue_line="Up high, eyes to the sky.",
        reach="high",
        fail_text="The branch was too high for bare hands, and tugging at it from below only made the branch sway.",
        found_text="The lost part was tangled beside the kite tail high in the branches.",
        tags={"tree", "high"},
    ),
    "storm_grate": HidingPlace(
        id="storm_grate",
        label="the storm grate",
        intro="By the curb, rainwater whispered under a square iron grate.",
        clue_line="Down low, watch for the glow.",
        reach="narrow",
        fail_text="The bars were too narrow for fingers, and one wrong poke could push the part even farther in.",
        found_text="The lost part glittered just under the grate where the water could not quite carry it away.",
        tags={"grate", "low"},
    ),
    "statue_hand": HidingPlace(
        id="statue_hand",
        label="the statue hand",
        intro="In the tiny plaza, a stone hero stood with one hand stretched toward the clouds.",
        clue_line="Tall and still, search the hill.",
        reach="perch",
        fail_text="The stone hand was too high and too narrow to reach safely from the ground.",
        found_text="The lost part perched in the statue's open hand as if it had been left there on purpose.",
        tags={"statue", "high"},
    ),
}

GADGETS = {
    "zip_claw": Gadget(
        id="zip_claw",
        label="zip claw",
        phrase="a zip claw on a bright cord",
        works_for={"high", "perch"},
        materials={"metal", "cloth"},
        action_text="flicked the zip claw upward, caught the hidden part, and guided it down in a neat shining arc",
        qa_text="used the zip claw to reach the hidden part and bring it down safely",
        tags={"tool", "reach"},
    ),
    "magnet_line": Gadget(
        id="magnet_line",
        label="magnet line",
        phrase="a humming magnet line",
        works_for={"narrow", "perch"},
        materials={"metal"},
        action_text="lowered the magnet line with a careful wrist and drew the metal part back without dropping it",
        qa_text="used the magnet line to pull the metal part back",
        tags={"tool", "magnet"},
    ),
    "pocket_mesh": Gadget(
        id="pocket_mesh",
        label="pocket mesh",
        phrase="a fold-out pocket mesh",
        works_for={"narrow"},
        materials={"cloth"},
        action_text="slid the pocket mesh through the gap, scooped the hidden part gently, and lifted it free",
        qa_text="used the pocket mesh to scoop the hidden part out",
        tags={"tool", "mesh"},
    ),
}

GIRL_NAMES = ["Nia", "Ava", "Maya", "Lila", "Ruby", "Zoe", "Tess", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Finn", "Jude", "Eli", "Noah"]
TRAITS = ["curious", "brave", "quick", "careful", "hopeful", "steady"]


def compatible(mission: Mission, item: LostItem, hiding: HidingPlace, gadget: Gadget) -> bool:
    if mission.need != item.family:
        return False
    if hiding.reach not in gadget.works_for:
        return False
    if item.material not in gadget.materials:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mid, mission in MISSIONS.items():
        for iid, item in ITEMS.items():
            for hid, hiding in HIDING_PLACES.items():
                for gid, gadget in GADGETS.items():
                    if compatible(mission, item, hiding, gadget):
                        combos.append((mid, iid, hid, gid))
    return combos


def gadgets_for(item: LostItem, hiding: HidingPlace) -> list[str]:
    out = []
    for gid, gadget in GADGETS.items():
        if hiding.reach in gadget.works_for and item.material in gadget.materials:
            out.append(gid)
    return sorted(out)


def explain_rejection(mission: Mission, item: LostItem, hiding: HidingPlace, gadget: Gadget) -> str:
    if mission.need != item.family:
        return (
            f"(No story: {mission.machine} needs a {mission.need} part, but "
            f"{item.label} is a {item.family} part. The quest only works when the missing piece matches the machine.)"
        )
    if hiding.reach not in gadget.works_for:
        return (
            f"(No story: {gadget.label} cannot solve a {hiding.reach} retrieval problem at {hiding.label}. "
            f"Pick a gadget that can actually reach the hiding place.)"
        )
    if item.material not in gadget.materials:
        return (
            f"(No story: {gadget.label} does not work on a {item.material} item like {item.label}. "
            f"Pick a gadget that can hold the real object.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_snatch(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["grab_by_hand"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("hero").meters["risk"],
        "fear": sim.get("hero").memes["fear"],
    }


def mission_call(world: World, mission: Mission, item: LostItem) -> None:
    machine = world.get("machine")
    machine.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(mission.opening)
    world.say(
        f"Mister Mesh knelt beside the panel and found the empty place where {item.phrase} should have been."
    )
    world.say(
        f'"A missing part can cripple a machine if no one helps in time," he said. "{mission.danger}"'
    )


def hero_setup(world: World, hero: Entity, parent: Entity, mission: Mission) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved to notice the details other people missed."
    )
    world.say(
        f"That afternoon, {hero.pronoun().capitalize()} was visiting {mission.place} with {hero.pronoun('possessive')} {parent.label_word} when a shadow striped the path and a blue cape swooped down."
    )
    world.say(
        "It was Mister Mesh, the neighborhood superhero, with silver threads sparkling across his cape like moonlit netting."
    )


def clue_start(world: World, hero: Entity, hiding: HidingPlace) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'Mister Mesh tapped one tiny scuff on the ground and whispered, "{hiding.clue_line}"'
    )
    world.say(
        f'{hero.id} repeated it softly: "{hiding.clue_line}" Curiosity warmed in {hero.pronoun("possessive")} chest like a little lantern.'
    )


def quest_walk(world: World, hero: Entity, mentor: Entity, hiding: HidingPlace) -> None:
    hero.memes["quest"] += 1
    world.say(
        f"Together they hurried through the neighborhood on a quest, following bent grass, a sparkle on a rail, and one small clue after another."
    )
    world.say(hiding.intro)
    world.say(
        f'"{hiding.clue_line}" Mister Mesh said again, and this time {hero.id} said it back louder.'
    )


def inspect(world: World, hero: Entity, item: LostItem, hiding: HidingPlace) -> None:
    world.say(
        f"{hero.id} looked left, right, and then exactly where the clue seemed to point. There {item.phrase} {item.shine}."
    )
    world.say(hiding.found_text)


def risky_attempt(world: World, hero: Entity, hiding: HidingPlace) -> None:
    hero.memes["grab_by_hand"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} stretched a hand toward it, but {hiding.fail_text}"
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"For one beat, {hero.pronoun('possessive')} stomach fluttered. The quest suddenly felt big."
        )


def wise_turn(world: World, mentor: Entity, hero: Entity, gadget: Gadget, hiding: HidingPlace) -> None:
    pred = predict_snatch(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'"Heroes do not snatch when they can think," Mister Mesh said. "{hiding.clue_line}"'
    )
    world.say(
        f"He unhooked {gadget.phrase} from his belt and placed it in {hero.id}'s hands."
    )


def recover(world: World, hero: Entity, item: LostItem, gadget: Gadget) -> None:
    world.get("item").meters["stuck"] = 0.0
    world.get("item").meters["found"] += 1
    world.say(
        f"{hero.id} took a steady breath and {gadget.action_text}."
    )
    world.say(
        f"When the part landed safely in {hero.pronoun('possessive')} palms, {hero.pronoun()} grinned so wide that even the clouds seemed to notice."
    )


def restore(world: World, hero: Entity, mentor: Entity, mission: Mission, item: LostItem) -> None:
    machine = world.get("machine")
    machine.meters["missing"] = 0.0
    machine.meters["restored"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Back at {mission.place}, {hero.id} handed {item.phrase} to Mister Mesh, who clicked it back into the {mission.machine}."
    )
    world.say(mission.ending)
    world.say(
        f"{hero.id} stood a little taller. Curiosity had led the way, and careful courage had finished the job."
    )


def ending_image(world: World, hero: Entity, parent: Entity, mission: Mission) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} squeezed {hero.pronoun("possessive")} shoulder and smiled. "You followed the clue, asked good questions, and helped the whole city."'
    )
    world.say(
        f"As the evening light spread across the roofs, {hero.id} watched {mission.ending.lower()} and wondered what mystery might be next."
    )


def tell(
    mission: Mission,
    item: LostItem,
    hiding: HidingPlace,
    gadget: Gadget,
    hero_name: str = "Nia",
    hero_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["little", trait],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    mentor = world.add(Entity(
        id="Mister Mesh",
        kind="character",
        type="man",
        role="mentor",
        label="Mister Mesh",
        attrs={},
    ))
    machine = world.add(Entity(
        id="machine",
        type="machine",
        label=mission.machine,
        attrs={},
    ))
    item_ent = world.add(Entity(
        id="item",
        type="part",
        label=item.label,
        attrs={"material": item.material, "family": item.family},
    ))

    hero.meters["risk"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["quest"] = 0.0
    hero.memes["grab_by_hand"] = 0.0
    machine.meters["missing"] = 0.0
    machine.meters["trouble"] = 0.0
    machine.meters["restored"] = 0.0
    item_ent.meters["stuck"] = 1.0
    item_ent.meters["found"] = 0.0
    mentor.memes["urgency"] = 0.0
    mentor.memes["pride"] = 0.0

    hero_setup(world, hero, parent, mission)
    mission_call(world, mission, item)

    world.para()
    clue_start(world, hero, hiding)
    quest_walk(world, hero, mentor, hiding)
    inspect(world, hero, item, hiding)

    world.para()
    risky_attempt(world, hero, hiding)
    wise_turn(world, mentor, hero, gadget, hiding)
    recover(world, hero, item, gadget)

    world.para()
    restore(world, hero, mentor, mission, item)
    ending_image(world, hero, parent, mission)

    world.facts.update(
        hero=hero,
        parent=parent,
        mentor=mentor,
        machine=machine,
        mission=mission,
        item_cfg=item,
        hiding=hiding,
        gadget=gadget,
        found=item_ent.meters["found"] >= THRESHOLD,
        restored=machine.meters["restored"] >= THRESHOLD,
        risk=hero.meters["risk"],
        clue=hiding.clue_line,
    )
    return world


KNOWLEDGE = {
    "machine": [
        (
            "What is a machine part?",
            "A machine part is one piece of a bigger machine. If an important piece is missing, the whole machine may not work the way it should.",
        ),
        (
            "What does it mean to cripple a machine?",
            "It means to damage or weaken the machine so badly that it cannot do its job well. In this story, the missing part could stop an important city helper from working.",
        ),
    ],
    "mesh": [
        (
            "What is mesh?",
            "Mesh is a fabric or net made from many little holes and crossing strands. It can be strong enough to catch or scoop things while still letting air and water pass through.",
        ),
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet pulls certain kinds of metal toward it. That can help someone lift a metal object from a hard place to reach.",
        ),
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. Someone goes looking for something important and keeps following clues until the job is done.",
        ),
    ],
    "curiosity": [
        (
            "Why can curiosity help in a mystery?",
            "Curiosity makes you want to look closely and ask questions. That helps you notice clues other people might miss.",
        ),
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a bright signal light that helps people see or find their way. It is useful in dark or foggy weather.",
        ),
    ],
    "bridge": [
        (
            "Why does a bridge bell matter?",
            "A bridge bell warns people that the bridge is changing or that they should pay attention. A clear signal helps everyone move safely.",
        ),
    ],
    "garden": [
        (
            "Why would a garden need a fan?",
            "A garden fan can move air so plants do not get too hot and still. Good air helps delicate plants stay healthy.",
        ),
    ],
}
KNOWLEDGE_ORDER = ["quest", "curiosity", "machine", "mesh", "magnet", "beacon", "bridge", "garden"]


@dataclass
class StoryParams:
    mission: str
    item: str
    hiding: str
    gadget: str
    hero_name: str
    hero_type: str
    parent_type: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    item = f["item_cfg"]
    hiding = f["hiding"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "mesh", "mister", and "cripple".',
        f"Tell a superhero quest where Mister Mesh and a child hero named {hero.id} follow repeated clues to find {item.phrase} and save {mission.machine}.",
        f'Write a gentle mystery adventure where curiosity leads the hero to {hiding.label}, and the ending proves the city helper is working again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    mission = f["mission"]
    item = f["item_cfg"]
    hiding = f["hiding"]
    gadget = f["gadget"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child hero, and Mister Mesh, the neighborhood superhero. They work together like a team on one important quest.",
        ),
        (
            "What problem started the story?",
            f"{item.phrase.capitalize()} was missing from the {mission.machine}. Mister Mesh explained that losing an important part could cripple a machine and leave the city helper struggling.",
        ),
        (
            "What clue did they repeat?",
            f'They kept repeating, "{hiding.clue_line}" The repeated line helped them focus on where to search next.',
        ),
        (
            f"Why did {hero.id} go to {hiding.label}?",
            f"{hero.id} followed small clues there because curiosity made {hero.pronoun('object')} look closely instead of guessing. The repeated clue also pointed toward that hiding place.",
        ),
        (
            f"Why could {hero.id} not just grab the part by hand?",
            f"{hiding.fail_text} That made the moment risky, so the hero had to slow down and think.",
        ),
        (
            f"How did they get the missing part back?",
            f"{hero.id} used {gadget.label}. {gadget.qa_text.capitalize()}, which kept the part safe and stopped it from being lost again.",
        ),
        (
            "How did the story end?",
            f"Mister Mesh put the missing part back, and {mission.ending.lower()} That final picture shows the quest truly worked.",
        ),
        (
            f"How did {hero.id}'s {parent.label_word} feel at the end?",
            f"{hero.pronoun('possessive').capitalize()} {parent.label_word} felt proud and relieved. {parent.label_word.capitalize()} had watched {hero.id} use curiosity first and courage second.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mission = f["mission"]
    gadget = f["gadget"]
    tags = {"quest", "curiosity", "machine"}
    if gadget.id == "pocket_mesh":
        tags.add("mesh")
    if gadget.id == "magnet_line":
        tags.add("magnet")
    tags |= set(mission.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="beacon",
        item="sun_cell",
        hiding="kite_tree",
        gadget="zip_claw",
        hero_name="Nia",
        hero_type="girl",
        parent_type="mother",
        trait="curious",
    ),
    StoryParams(
        mission="bridge",
        item="echo_key",
        hiding="storm_grate",
        gadget="magnet_line",
        hero_name="Theo",
        hero_type="boy",
        parent_type="father",
        trait="steady",
    ),
    StoryParams(
        mission="garden",
        item="breeze_vane",
        hiding="storm_grate",
        gadget="pocket_mesh",
        hero_name="Ruby",
        hero_type="girl",
        parent_type="mother",
        trait="brave",
    ),
    StoryParams(
        mission="bridge",
        item="echo_key",
        hiding="statue_hand",
        gadget="zip_claw",
        hero_name="Max",
        hero_type="boy",
        parent_type="father",
        trait="quick",
    ),
    StoryParams(
        mission="beacon",
        item="sun_cell",
        hiding="statue_hand",
        gadget="magnet_line",
        hero_name="Ivy",
        hero_type="girl",
        parent_type="mother",
        trait="hopeful",
    ),
]


ASP_RULES = r"""
matches(M,I) :- mission_need(M,N), item_family(I,N).
usable(H,G)  :- hiding_reach(H,R), gadget_reach(G,R).
holds(I,G)   :- item_material(I,M), gadget_material(G,M).
valid(M,I,H,G) :- matches(M,I), usable(H,G), holds(I,G).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_need", mid, mission.need))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_family", iid, item.family))
        lines.append(asp.fact("item_material", iid, item.material))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("hiding_reach", hid, hiding.reach))
    for gid, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for reach in sorted(gadget.works_for):
            lines.append(asp.fact("gadget_reach", gid, reach))
        for material in sorted(gadget.materials):
            lines.append(asp.fact("gadget_material", gid, material))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_params = StoryParams(
        mission="beacon",
        item="sun_cell",
        hiding="kite_tree",
        gadget="zip_claw",
        hero_name="Nia",
        hero_type="girl",
        parent_type="mother",
        trait="curious",
        seed=0,
    )
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generated and emitted.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: Mister Mesh and a child hero solve a repeated-clue superhero quest."
    )
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hiding", choices=sorted(HIDING_PLACES))
    ap.add_argument("--gadget", choices=sorted(GADGETS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mission/item/hiding/gadget combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {args.mission})")
    if args.item and args.item not in ITEMS:
        raise StoryError(f"(Unknown item: {args.item})")
    if args.hiding and args.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {args.hiding})")
    if args.gadget and args.gadget not in GADGETS:
        raise StoryError(f"(Unknown gadget: {args.gadget})")

    if args.mission and args.item and args.hiding and args.gadget:
        mission = MISSIONS[args.mission]
        item = ITEMS[args.item]
        hiding = HIDING_PLACES[args.hiding]
        gadget = GADGETS[args.gadget]
        if not compatible(mission, item, hiding, gadget):
            raise StoryError(explain_rejection(mission, item, hiding, gadget))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.item is None or combo[1] == args.item)
        and (args.hiding is None or combo[2] == args.hiding)
        and (args.gadget is None or combo[3] == args.gadget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, item_id, hiding_id, gadget_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        mission=mission_id,
        item=item_id,
        hiding=hiding_id,
        gadget=gadget_id,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.gadget not in GADGETS:
        raise StoryError(f"(Unknown gadget: {params.gadget})")

    mission = MISSIONS[params.mission]
    item = ITEMS[params.item]
    hiding = HIDING_PLACES[params.hiding]
    gadget = GADGETS[params.gadget]
    if not compatible(mission, item, hiding, gadget):
        raise StoryError(explain_rejection(mission, item, hiding, gadget))

    world = tell(
        mission=mission,
        item=item,
        hiding=hiding,
        gadget=gadget,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        parent_type=params.parent_type,
        trait=params.trait,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, item, hiding, gadget) combos:\n")
        for mission, item, hiding, gadget in combos:
            print(f"  {mission:7} {item:11} {hiding:11} {gadget}")
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
            header = f"### {p.hero_name}: {p.mission} / {p.item} / {p.hiding} / {p.gadget}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
