#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/entice_toupee_horrible_twist_space_adventure.py
===========================================================================

A standalone story world for a small Space Adventure domain: a young cadet and a
captain discover what looks like a floating toupee in a spaceship corridor. The
cadet learns that the sensible move is not to snatch at it, but to entice it
away from a fragile ship system with the right lure and tool. The twist is that
the "toupee" is really Twist, the captain's escaped fluff-pet.

The world model keeps the story grounded:
- a fluffy pet drifts near a ship system,
- the system becomes risky while the pet stays loose,
- only some lures honestly attract some pets,
- only some tools are safe for some pets,
- delay can make a weak tool fail, causing a darker but still child-facing ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/entice_toupee_horrible_twist_space_adventure.py
    python storyworlds/worlds/gpt-5.4/entice_toupee_horrible_twist_space_adventure.py --pet ion_puff --hazard vent
    python storyworlds/worlds/gpt-5.4/entice_toupee_horrible_twist_space_adventure.py --tool bare_hands
    python storyworlds/worlds/gpt-5.4/entice_toupee_horrible_twist_space_adventure.py --all --qa
    python storyworlds/worlds/gpt-5.4/entice_toupee_horrible_twist_space_adventure.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
        female = {"girl", "mother", "woman", "captain_f"}
        male = {"boy", "father", "man", "captain_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"captain_f", "captain_m"}:
            return "captain"
        return self.type
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
class PetKind:
    id: str
    label: str
    phrase: str
    resembles: str
    drift_line: str
    reveal: str
    prefers: set[str] = field(default_factory=set)
    safe_tools: set[str] = field(default_factory=set)
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
class Hazard:
    id: str
    place: str
    system: str
    cue: str
    consequence: str
    restore: str
    failure: str
    severity: int = 1
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
class Lure:
    id: str
    label: str
    phrase: str
    action: str
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    success: str
    fail: str
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


def _r_system_risk(world: World) -> list[str]:
    pet = world.get("twist")
    system = world.get("system")
    kid = world.get("kid")
    captain = world.get("captain")
    if pet.meters["loose"] < THRESHOLD:
        return []
    sig = ("risk", world.facts["hazard"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    system.meters["danger"] += 1
    kid.memes["fear"] += 1
    captain.memes["urgency"] += 1
    return ["__danger__"]


RULES = [
    Rule(name="system_risk", tag="physical", apply=_r_system_risk),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def lure_matches(pet: PetKind, lure: Lure) -> bool:
    return lure.id in pet.prefers


def tool_safe(pet: PetKind, tool: Tool) -> bool:
    return tool.id in pet.safe_tools


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def danger_score(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_contained(hazard: Hazard, tool: Tool, delay: int) -> bool:
    return tool.power >= danger_score(hazard, delay)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hazard_id in HAZARDS:
        for pet_id, pet in PETS.items():
            for lure_id, lure in LURES.items():
                if not lure_matches(pet, lure):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool.sense < SENSE_MIN:
                        continue
                    if tool_safe(pet, tool):
                        combos.append((hazard_id, pet_id, lure_id, tool_id))
    return combos


def explain_invalid_combo(pet: PetKind, lure: Lure, tool: Tool) -> str:
    if not lure_matches(pet, lure):
        return (
            f"(No story: {lure.label} would not honestly entice {pet.label}. "
            f"Pick a lure that this fluff-pet actually follows.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). The storyworld prefers calm, safer tools.)"
        )
    if not tool_safe(pet, tool):
        return (
            f"(No story: {tool.label} is not a safe way to catch {pet.label}. "
            f"Choose a gentler tool for that pet.)"
        )
    return "(No story: this combination is unreasonable.)"


def outcome_of(params: "StoryParams") -> str:
    return "contained" if is_contained(HAZARDS[params.hazard], TOOLS[params.tool], params.delay) else "blackout"


def predict_trouble(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    sim.get("twist").meters["loose"] = 1.0
    sim.facts["hazard"] = HAZARDS[hazard_id]
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("system").meters["danger"],
        "fear": sim.get("kid").memes["fear"],
    }


def opening(world: World, kid: Entity, captain: Entity, hazard: Hazard) -> None:
    kid.memes["wonder"] += 1
    world.say(
        f"{kid.id} was helping Captain {captain.attrs['name']} on the little scout ship Star Hopper. "
        f"They floated down to {hazard.place}, where the walls glowed blue and the stars looked close enough to touch."
    )
    world.say(
        f"Then something fuzzy drifted beside the {hazard.system}. It was so round and fluffy that, at first glance, "
        f"it looked exactly like a lost toupee turning slow circles in the air."
    )


def mistake(world: World, kid: Entity, hazard: Hazard, pet: PetKind) -> None:
    world.say(
        f'"Captain!" {kid.id} whispered. "Is that a toupee in {hazard.place}?"'
    )
    world.say(
        f"But the fluff bobbed past the {hazard.system} with a tiny wiggle, and {pet.drift_line}."
    )


def warning(world: World, kid: Entity, captain: Entity, hazard: Hazard) -> None:
    pred = predict_trouble(world, hazard.id)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    kid.memes["caution"] += 1
    world.say(
        f'Captain {captain.attrs["name"]} held out an arm to stop {kid.id}. '
        f'"Not yet," {captain.pronoun()} said. "If that fluff keeps bumping the {hazard.system}, '
        f'{hazard.consequence}. That alarm would sound horrible in this narrow hall."'
    )
    world.say(
        f'"We need to entice it away from the {hazard.system} before we try to catch it."'
    )


def plan(world: World, kid: Entity, captain: Entity, pet: PetKind, lure: Lure, tool: Tool) -> None:
    kid.memes["hope"] += 1
    captain.memes["calm"] += 1
    world.say(
        f"{kid.id} nodded and reached for {lure.phrase}. Captain {captain.attrs['name']} lifted {tool.phrase} and moved slowly."
    )
    world.say(
        f"{kid.id} {lure.action}, and {lure.shine}. The little fluff turned toward the sound and light at once."
    )


def catch_success(world: World, kid: Entity, captain: Entity, hazard: Hazard, pet: PetKind, lure: Lure, tool: Tool) -> None:
    twist = world.get("twist")
    system = world.get("system")
    twist.meters["loose"] = 0.0
    twist.meters["caught"] = 1.0
    system.meters["danger"] = 0.0
    kid.memes["fear"] = 0.0
    kid.memes["relief"] += 1
    kid.memes["joy"] += 1
    world.say(
        f"The fuzzy thing drifted closer and closer, following {lure.label}. Then Captain {captain.attrs['name']} {tool.success}."
    )
    world.say(
        f"At once, {hazard.restore}. The red warning light faded, and the ship gave a soft, happy hum again."
    )
    world.say(
        f'The fluff blinked two bright eyes from inside the {tool.label}. {pet.reveal}'
    )
    world.say(
        f'"That is Twist," Captain {captain.attrs["name"]} said with a laugh. "Not a toupee at all -- just my runaway {pet.label}."'
    )
    world.say(
        f"{kid.id} laughed too, this time without any fear. Twist curled up like a sleepy star in the {tool.label}, and the corridor felt safe again."
    )


def catch_fail(world: World, kid: Entity, captain: Entity, hazard: Hazard, pet: PetKind, lure: Lure, tool: Tool) -> None:
    twist = world.get("twist")
    system = world.get("system")
    system.meters["danger"] += 1
    system.meters["offline"] += 1
    kid.memes["fear"] += 1
    kid.memes["relief"] += 1
    kid.memes["lesson"] += 1
    world.say(
        f"The furry shape came toward {lure.label}, but just as Captain {captain.attrs['name']} tried to close in, "
        f"{tool.fail}."
    )
    world.say(
        f"{hazard.failure}. For a moment the ship went dark except for the stars outside, and the warning buzzer gave one horrible bark."
    )
    world.say(
        f'Captain {captain.attrs["name"]} slapped the backup switch, sealed the panel, and pulled {kid.id} close. '
        f'"You did the right thing by helping me calmly," {captain.pronoun()} said. "Next time we must be quicker."'
    )
    world.say(
        f"Only then did the fluff peek out from behind a pipe and blink its tiny eyes. It was not a toupee after all. It was Twist, the captain's little {pet.label}, looking embarrassed."
    )
    world.say(
        f"Later, when the lights were back, Twist rode in a brighter carrier with a bell on top so nobody would mistake him for space laundry -- or a toupee -- again."
    )


def tell(
    hazard: Hazard,
    pet: PetKind,
    lure: Lure,
    tool: Tool,
    kid_name: str = "Mira",
    kid_type: str = "girl",
    captain_name: str = "Orion",
    captain_type: str = "captain_m",
    delay: int = 0,
) -> World:
    world = World()
    kid = world.add(Entity(id="kid", kind="character", type=kid_type, label=kid_name, role="kid"))
    captain = world.add(
        Entity(
            id="captain",
            kind="character",
            type=captain_type,
            label="the captain",
            role="captain",
            attrs={"name": captain_name},
        )
    )
    system = world.add(Entity(id="system", type="system", label=hazard.system))
    twist = world.add(Entity(id="twist", type="pet", label="Twist"))
    twist.meters["loose"] = 1.0
    system.meters["danger"] = 0.0
    kid.memes["fear"] = 0.0
    captain.memes["urgency"] = 0.0
    world.facts["hazard"] = hazard
    world.facts["pet"] = pet
    world.facts["lure"] = lure
    world.facts["tool"] = tool
    world.facts["delay"] = delay
    world.facts["kid_name"] = kid_name
    world.facts["captain_name"] = captain_name

    opening(world, kid, captain, hazard)
    mistake(world, kid, hazard, pet)

    world.para()
    propagate(world, narrate=False)
    warning(world, kid, captain, hazard)
    plan(world, kid, captain, pet, lure, tool)

    world.para()
    if is_contained(hazard, tool, delay):
        catch_success(world, kid, captain, hazard, pet, lure, tool)
        outcome = "contained"
    else:
        catch_fail(world, kid, captain, hazard, pet, lure, tool)
        outcome = "blackout"

    world.facts.update(
        kid=kid,
        captain=captain,
        system=system,
        twist=twist,
        outcome=outcome,
        reveal_name="Twist",
        contained=outcome == "contained",
    )
    return world


PETS = {
    "ion_puff": PetKind(
        id="ion_puff",
        label="ion puff",
        phrase="a silver ion puff",
        resembles="a silver toupee",
        drift_line="a trail of blue sparks popped behind it like tiny fireworks",
        reveal="Under the fur, little blue whiskers crackled with static.",
        prefers={"hum_tuner"},
        safe_tools={"bubble_dome", "soft_net"},
        tags={"pet", "static", "sound"},
    ),
    "moss_mop": PetKind(
        id="moss_mop",
        label="moss mop",
        phrase="a green moss mop",
        resembles="a green toupee",
        drift_line="little leaves shivered on its back as if it were breathing",
        reveal="A pair of leaf-bright eyes opened, and a sweet garden smell drifted out.",
        prefers={"glow_berry"},
        safe_tools={"bubble_dome", "soft_net"},
        tags={"pet", "plants", "light"},
    ),
    "comet_curl": PetKind(
        id="comet_curl",
        label="comet curl",
        phrase="a golden comet curl",
        resembles="a golden toupee",
        drift_line="gold dust twinkled around it and curled into little spirals",
        reveal="Its tail unrolled in a glittery ribbon, warm as a sunbeam.",
        prefers={"star_mirror"},
        safe_tools={"bubble_dome", "magnet_scoop"},
        tags={"pet", "space", "light"},
    ),
}

HAZARDS = {
    "vent": Hazard(
        id="vent",
        place="the air-vent corridor",
        system="cooling vent",
        cue="red vent light",
        consequence="the cooling vent could choke and make the engine room wheeze",
        restore="fresh air rushed through the vent again",
        failure="The vent coughed and the scout ship shuddered",
        severity=2,
        tags={"vent", "air"},
    ),
    "map": Hazard(
        id="map",
        place="the star-map room",
        system="star projector",
        cue="blinking map crystal",
        consequence="the star projector could flicker and send the route spinning crooked",
        restore="the star map steadied into neat bright lines",
        failure="The map spun wild and sprayed stars across the ceiling",
        severity=1,
        tags={"map", "navigation"},
    ),
    "garden": Hazard(
        id="garden",
        place="the hydroponic ring",
        system="seed fan",
        cue="orange garden light",
        consequence="the seed fan could jam and toss baby leaves all over the ring",
        restore="the seed fan whirred softly and the leaves settled down",
        failure="The seed fan burst into a green whirl of leaves and seed fluff",
        severity=2,
        tags={"garden", "plants"},
    ),
}

LURES = {
    "hum_tuner": Lure(
        id="hum_tuner",
        label="the humming tuner",
        phrase="the little humming tuner",
        action="clicked the tuner on",
        shine="It sang a round silver note that seemed to roll through the air",
        tags={"sound"},
    ),
    "glow_berry": Lure(
        id="glow_berry",
        label="the glow berry",
        phrase="the glowing berry from the galley garden",
        action="lifted the berry in both hands",
        shine="Its gentle green light shone like a tiny moon",
        tags={"food", "light"},
    ),
    "star_mirror": Lure(
        id="star_mirror",
        label="the star mirror",
        phrase="the polished star mirror",
        action="tilted the mirror toward the ceiling lights",
        shine="Golden specks danced across the wall like baby comets",
        tags={"light"},
    ),
}

TOOLS = {
    "bubble_dome": Tool(
        id="bubble_dome",
        label="bubble dome",
        phrase="the clear bubble dome",
        sense=3,
        power=3,
        success="lowered the bubble dome over it in one smooth swoop",
        fail="the bubble dome clipped a pipe and Twist shot away",
        qa_text="caught Twist safely under a clear bubble dome",
        tags={"container"},
    ),
    "soft_net": Tool(
        id="soft_net",
        label="soft net",
        phrase="the soft net with padded rings",
        sense=3,
        power=2,
        success="cast the soft net around it and drew the strings closed without hurting a single hair",
        fail="the soft net closed a heartbeat too late and Twist bounced free",
        qa_text="gathered Twist up with a soft net",
        tags={"net"},
    ),
    "magnet_scoop": Tool(
        id="magnet_scoop",
        label="magnet scoop",
        phrase="the little magnet scoop",
        sense=2,
        power=2,
        success="slid the magnet scoop beneath it and lifted it away from the panel",
        fail="the magnet scoop tugged at a bolt, and the surprise made Twist dart away",
        qa_text="lifted Twist away with a magnet scoop",
        tags={"tool"},
    ),
    "bare_hands": Tool(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands",
        sense=1,
        power=1,
        success="grabbed it in midair",
        fail="reached out, but the fluff slipped through those fingers at once",
        qa_text="tried to grab Twist with bare hands",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mira", "Nova", "Lina", "Ayla", "Tess", "Rhea", "Kira", "Zuri"]
BOY_NAMES = ["Jett", "Leo", "Milo", "Orin", "Tao", "Nico", "Finn", "Arlo"]
CAPTAIN_NAMES_F = ["Vega", "Lyra", "Sera", "Iris"]
CAPTAIN_NAMES_M = ["Orion", "Sol", "Atlas", "Pax"]


@dataclass
class StoryParams:
    hazard: str
    pet: str
    lure: str
    tool: str
    kid_name: str
    kid_type: str
    captain_name: str
    captain_type: str
    delay: int = 0
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
    "pet": [
        (
            "What is a ship pet?",
            "A ship pet is a small animal or creature that lives on a spaceship with the crew. It still needs careful, gentle handling, especially around machines."
        )
    ],
    "static": [
        (
            "Why can static fluff be tricky near machines?",
            "Static can make light things cling or jump in odd ways. Around machines, that can make a tiny creature drift somewhere it should not."
        )
    ],
    "plants": [
        (
            "Why do plants need a fan in a space garden?",
            "A fan moves air around the plants so they can stay healthy. In space, air does not swirl around leaves the same way it does on Earth."
        )
    ],
    "space": [
        (
            "Why do things float inside a spaceship?",
            "Far from a planet, people and loose objects can float because they are in very weak gravity or freefall. That is why the crew must keep tools and pets secure."
        )
    ],
    "vent": [
        (
            "What does a cooling vent do on a spaceship?",
            "A cooling vent pushes air where the ship needs it so machines do not get too hot. If it is blocked, the ship can struggle."
        )
    ],
    "map": [
        (
            "What does a star projector do?",
            "A star projector shows the crew where stars and routes are. It helps them see where they are going."
        )
    ],
    "garden": [
        (
            "What is hydroponics?",
            "Hydroponics is a way to grow plants with water and nutrients instead of soil. Spaceships can use it to grow fresh food."
        )
    ],
    "sound": [
        (
            "Why might an animal follow a sound?",
            "Some animals and pets learn that a certain sound means food, play, or safety. A familiar sound can guide them without scaring them."
        )
    ],
    "light": [
        (
            "Why can light entice a creature?",
            "Some creatures are curious about glow and sparkle, just as children notice bright toys. A gentle light can help guide them where you want them to go."
        )
    ],
    "container": [
        (
            "Why is a clear dome a gentle way to catch a small creature?",
            "A clear dome lets you cover the creature without squeezing it. You can still see it and move it safely."
        )
    ],
    "net": [
        (
            "Why use a soft net instead of a rough one?",
            "A soft net bends and gives a little, so it is less likely to hurt a small creature. Gentle tools are usually the safer choice."
        )
    ],
    "tool": [
        (
            "Why should you use the right tool instead of grabbing quickly?",
            "The right tool gives you control and keeps both you and the creature safer. Quick grabbing can make a problem worse."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "pet",
    "space",
    "vent",
    "map",
    "garden",
    "static",
    "plants",
    "sound",
    "light",
    "container",
    "net",
    "tool",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hazard: Hazard = f["hazard"]
    pet: PetKind = f["pet"]
    lure: Lure = f["lure"]
    outcome = f["outcome"]
    base = (
        f'Write a short Space Adventure for a 3-to-5-year-old that includes the words "entice", '
        f'"toupee", and "horrible". A child spots something fluffy near a spaceship {hazard.system}.'
    )
    twist = (
        f"Use a twist ending where the scary fluff turns out to be Twist, a runaway {pet.label}, not a toupee at all."
    )
    if outcome == "contained":
        return [
            base,
            f"Tell a gentle space story where a cadet uses {lure.label} to entice a fuzzy creature away from the {hazard.system}, and a captain catches it safely.",
            twist,
        ]
    return [
        base,
        f"Tell a space story where the crew tries to entice the fluff away from the {hazard.system}, but they are a little too late and the ship suffers a brief scary problem before the reveal.",
        twist,
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid: Entity = f["kid"]
    captain: Entity = f["captain"]
    hazard: Hazard = f["hazard"]
    pet: PetKind = f["pet"]
    lure: Lure = f["lure"]
    tool: Tool = f["tool"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['kid_name']}, a young cadet, and Captain {f['captain_name']} on the Star Hopper. Together they had to solve a small spaceship problem calmly."
        ),
        (
            "What did the floating fluff look like at first?",
            f"At first it looked like a drifting toupee. That silly mistake is what made the later reveal feel surprising and funny."
        ),
        (
            f"Why did Captain {f['captain_name']} stop {f['kid_name']} from grabbing it right away?",
            f"Captain {f['captain_name']} knew the fluff was too close to the {hazard.system}. If it kept bumping that system, {hazard.consequence}.",
        ),
        (
            f"How did they try to entice the fluff away?",
            f"They used {lure.label} so the creature would come toward them instead of staying by the {hazard.system}. That safer plan let them guide it before trying to catch it."
        ),
    ]
    if outcome == "contained":
        qa.extend(
            [
                (
                    f"How did Captain {f['captain_name']} catch Twist?",
                    f"Captain {f['captain_name']} {tool.qa_text}. Because the lure matched what the pet liked, Twist drifted close enough for a gentle catch."
                ),
                (
                    "What was the twist at the end?",
                    f"The fluffy thing was not a toupee at all. It was Twist, the captain's runaway {pet.label}, which is why the ending turns from danger into laughter."
                ),
                (
                    "How did the story end?",
                    f"The {hazard.system} worked properly again, and the corridor felt safe. Twist curled up quietly in the {tool.label}, proving the problem had really changed."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    "Did their first try work in time?",
                    f"No. They almost had Twist, but the ship problem happened first and the {hazard.system} went wrong for a moment.",
                ),
                (
                    "What was the twist at the end?",
                    f"Even after the scary moment, the fluffy shape turned out not to be a toupee. It was Twist, the captain's little {pet.label}, blinking from behind the pipe."
                ),
                (
                    "How did the story end?",
                    f"The crew turned the lights back on and put Twist into a brighter, safer carrier. The ending image shows that they learned to keep calm and secure the pet better next time."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["pet"].tags) | set(f["hazard"].tags) | set(f["lure"].tags) | set(f["tool"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({e.type:10}) label={label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hazard="vent",
        pet="ion_puff",
        lure="hum_tuner",
        tool="bubble_dome",
        kid_name="Mira",
        kid_type="girl",
        captain_name="Orion",
        captain_type="captain_m",
        delay=0,
    ),
    StoryParams(
        hazard="map",
        pet="comet_curl",
        lure="star_mirror",
        tool="magnet_scoop",
        kid_name="Jett",
        kid_type="boy",
        captain_name="Lyra",
        captain_type="captain_f",
        delay=0,
    ),
    StoryParams(
        hazard="garden",
        pet="moss_mop",
        lure="glow_berry",
        tool="soft_net",
        kid_name="Nova",
        kid_type="girl",
        captain_name="Sol",
        captain_type="captain_m",
        delay=1,
    ),
    StoryParams(
        hazard="vent",
        pet="comet_curl",
        lure="star_mirror",
        tool="magnet_scoop",
        kid_name="Arlo",
        kid_type="boy",
        captain_name="Vega",
        captain_type="captain_f",
        delay=2,
    ),
]


ASP_RULES = r"""
valid(H, P, L, T) :- hazard(H), pet(P), lure(L), tool(T),
                     prefers(P, L), safe_tool(P, T),
                     sense(T, S), sense_min(M), S >= M.

severity(H, V + D) :- chosen_hazard(H), hazard_severity(H, V), delay(D).
tool_power(P)      :- chosen_tool(T), power(T, P).
contained          :- tool_power(P), severity(_, Need), P >= Need.
outcome(contained) :- contained.
outcome(blackout)  :- not contained.

sensible_tool(T)   :- tool(T), sense(T, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_severity", hid, hazard.severity))
    for pid, pet in PETS.items():
        lines.append(asp.fact("pet", pid))
        for lure_id in sorted(pet.prefers):
            lines.append(asp.fact("prefers", pid, lure_id))
        for tool_id in sorted(pet.safe_tools):
            lines.append(asp.fact("safe_tool", pid, tool_id))
    for lid in LURES:
        lines.append(asp.fact("lure", lid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("power", tid, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_tool", params.tool),
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

    c_tools = set(asp_sensible_tools())
    p_tools = {t.id for t in sensible_tools()}
    if c_tools == p_tools:
        print(f"OK: sensible tools match ({sorted(c_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_tools)} python={sorted(p_tools)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space Adventure storyworld: a fuzzy 'toupee' is really Twist the runaway ship pet."
    )
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--kid-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["female", "male"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pet and args.lure and not lure_matches(PETS[args.pet], LURES[args.lure]):
        raise StoryError(explain_invalid_combo(PETS[args.pet], LURES[args.lure], TOOLS.get(args.tool or "bubble_dome", TOOLS["bubble_dome"])))
    if args.pet and args.tool:
        pet = PETS[args.pet]
        tool = TOOLS[args.tool]
        lure = LURES.get(args.lure or next(iter(pet.prefers)), LURES[next(iter(pet.prefers))])
        if not (lure_matches(pet, lure) and tool_safe(pet, tool) and tool.sense >= SENSE_MIN):
            raise StoryError(explain_invalid_combo(pet, lure, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        pet = PETS[args.pet] if args.pet else next(iter(PETS.values()))
        lure_id = next(iter(pet.prefers))
        raise StoryError(explain_invalid_combo(pet, LURES[lure_id], TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hazard is None or combo[0] == args.hazard)
        and (args.pet is None or combo[1] == args.pet)
        and (args.lure is None or combo[2] == args.lure)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hazard_id, pet_id, lure_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    kid_name = args.kid_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    captain_gender = args.captain_gender or rng.choice(["female", "male"])
    if captain_gender == "female":
        captain_name = args.captain_name or rng.choice(CAPTAIN_NAMES_F)
        captain_type = "captain_f"
    else:
        captain_name = args.captain_name or rng.choice(CAPTAIN_NAMES_M)
        captain_type = "captain_m"

    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        hazard=hazard_id,
        pet=pet_id,
        lure=lure_id,
        tool=tool_id,
        kid_name=kid_name,
        kid_type=gender,
        captain_name=captain_name,
        captain_type=captain_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    hazard = HAZARDS[params.hazard]
    pet = PETS[params.pet]
    lure = LURES[params.lure]
    tool = TOOLS[params.tool]
    if not (lure_matches(pet, lure) and tool_safe(pet, tool) and tool.sense >= SENSE_MIN):
        raise StoryError(explain_invalid_combo(pet, lure, tool))

    world = tell(
        hazard=hazard,
        pet=pet,
        lure=lure,
        tool=tool,
        kid_name=params.kid_name,
        kid_type=params.kid_type,
        captain_name=params.captain_name,
        captain_type=params.captain_type,
        delay=params.delay,
    )
    story = world.render().replace("kid", params.kid_name)
    story = story.replace("Captain the captain", f"Captain {params.captain_name}")
    story = story.replace("kid's", f"{params.kid_name}'s")
    story = story.replace(" kid ", f" {params.kid_name} ")
    story = story.replace(" kid.", f" {params.kid_name}.")
    story = story.replace(" kid,", f" {params.kid_name},")
    story = story.replace("captain", "captain", 0)

    # Replace the entity id "kid" with the actual spoken name in a controlled way.
    story = story.replace("kid", params.kid_name)

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
        print(asp_program("", "#show valid/4.\n#show sensible_tool/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hazard, pet, lure, tool) combos:\n")
        for hazard, pet, lure, tool in combos:
            print(f"  {hazard:7} {pet:11} {lure:11} {tool}")
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
            header = f"### {p.kid_name}: {p.pet} near {p.hazard} ({p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
