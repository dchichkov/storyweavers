#!/usr/bin/env python3
"""
storyworlds/worlds/somersault_sanitary_sound_effects_fable.py
=============================================================

A small fable world about a child-facing lesson: a playful creature wants to
do a somersault, but a sanitary concern changes the plan. The story uses sound
effects as a narrative instrument and resolves with a wiser, cleaner choice.

The world is intentionally tiny and constraint-checked:
- a scene with a simple public place,
- one hero who wants to do a flip,
- one sanitary risk that makes the move unwise,
- a helper or elder who offers a clean workaround,
- a final image proving the change.

The style is close to a fable: concrete, gentle, and lesson-shaped.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gear_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "goat"}
        male = {"boy", "father", "dad", "man", "fox", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the schoolyard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    mess: str
    soil: str
    risky_region: str
    keyword: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))


SETTINGS = {
    "schoolyard": Setting(place="the schoolyard", indoor=False, affords={"somersault"}),
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"somersault"}),
    "porch": Setting(place="the porch", indoor=True, affords={"somersault"}),
}


ACTIONS = {
    "somersault": Action(
        id="somersault",
        verb="do a somersault",
        gerund="doing somersaults",
        rush="flip over the stones",
        sound="whoosh",
        mess="dusty",
        soil="dusty and smudged",
        risky_region="hands",
        keyword="somersault",
    ),
    "stomp": Action(
        id="stomp",
        verb="stomp in the puddles",
        gerund="stomping in puddles",
        rush="rush into the wet ground",
        sound="splish",
        mess="muddy",
        soil="muddy and wet",
        risky_region="feet",
        keyword="sound effect",
    ),
}

PRIZES = {
    "cloth": Prize(label="cloth", phrase="a bright white cloth", type="cloth", region="hands"),
    "apron": Prize(label="apron", phrase="a clean little apron", type="apron", region="torso"),
}

GEAR = [
    Gear(
        id="mat",
        label="a clean mat",
        covers={"hands", "torso", "feet"},
        guards={"dusty", "muddy"},
        prep="set down a clean mat first",
        tail="set down the clean mat and tried again",
    ),
    Gear(
        id="washcloth",
        label="a wet washcloth",
        covers={"hands"},
        guards={"dusty"},
        prep="wipe the floor with a wet washcloth first",
        tail="wiped the floor with the wet washcloth and then tried again",
    ),
]

HERO_NAMES = ["Milo", "Pip", "Nia", "Tess", "Bram", "Luna"]
HELPER_NAMES = ["Aunt Fern", "Grandpa Reed", "Mother Owl", "Old Hare"]


@dataclass(frozen=True)
class Incident:
    title: str
    setup: str
    hazard: str
    wrong_turn: str
    clue: str
    helper_line: str
    safe_plan: str
    result: str
    ending_image: str
    lesson: str
    sound: str


INCIDENTS = [
    Incident(
        title="the muddy pawprints",
        setup="A delivery cart had left a fan of muddy pawprints beside the practice square.",
        hazard="A hurried roll could carry mud from the path onto the mat and everyone else's paws.",
        wrong_turn="The little hare nearly covered the prints with a banner, which would only have hidden the mess.",
        clue="A brown wheel mark led from the gate to the dampest print.",
        helper_line='"Hiding dirt is not the same as cleaning it," the helper said.',
        safe_plan="They marked the wet patch, asked the caretaker to mop it, and waited while a fresh mat dried in the sun.",
        result="The brown marks disappeared, the mat passed a clean-cloth check, and the path reopened.",
        ending_image="Only the cart's clean wheel pattern remained, pressed like a flower in the dust beyond the practice rope.",
        lesson="A clean-looking shortcut cannot replace an honest cleanup.",
        sound="squish-scritch",
    ),
    Incident(
        title="the leaking water jug",
        setup="A drinking-water jug had dripped a silver trail across one corner of the practice mat.",
        hazard="Even clean water can make an acrobatics mat slippery enough for paws to skid.",
        wrong_turn="The little hare proposed turning the mat around and using the dry-looking half.",
        clue="When a paper towel touched the seam, a dark wet stripe spread through it.",
        helper_line='"Sanitary also means safe to use," the helper reminded them.',
        safe_plan="They moved the jug, hung a KEEP CLEAR sign, and chose a spare mat that an adult had checked from edge to edge.",
        result="The leaking lid was tightened, the wet mat was hung to dry, and nobody slipped.",
        ending_image="Sunlight shone through the last drop on the repaired lid while the damp mat fluttered safely on the rail.",
        lesson="Careful testing catches hazards that eyes alone can miss.",
        sound="drip-drip, squeak",
    ),
    Incident(
        title="the shared chalk hands",
        setup="The practice group had passed bright chalk from paw to paw until every block felt dusty.",
        hazard="Touching faces and snack cloths with chalky paws would spread the powder beyond the game.",
        wrong_turn="The little hare wanted to brush both paws on the prize cloth and begin at once.",
        clue="A blue pawprint appeared on the white practice card after just one tap.",
        helper_line='"Keep the keepsake clean; use the wash station for paws," the helper said.',
        safe_plan="Everyone put the chalk in its own tray, washed and dried their paws, and saved snacks for after practice.",
        result="The white check card stayed white, and each chalk block had a tidy place of its own.",
        ending_image="A row of clean paws waved above a rainbow of chalk blocks, none of them touching the picnic cloth.",
        lesson="Shared fun works best when shared objects have clean boundaries.",
        sound="tap-tap, swish",
    ),
    Incident(
        title="the sneeze near the mat",
        setup="Just before practice, a young squirrel sneezed beside the equipment basket.",
        hazard="The nearby mat and hand markers needed attention before the group could safely share them.",
        wrong_turn="The little hare first suggested pretending nobody had heard the sneeze.",
        clue="The squirrel pointed out exactly which marker they had been holding.",
        helper_line='"Telling us helps us care for one another; it is nothing to tease about," the helper said.',
        safe_plan="The squirrel washed their paws, an adult cleaned the shared marker and mat, and the group practiced farther apart while the squirrel rested.",
        result="The equipment was cleaned without blaming anyone, and the squirrel felt cared for rather than embarrassed.",
        ending_image="The squirrel watched from a sunny bench, wrapped in a scarf and holding a cup, as friends waved from the clean square.",
        lesson="Honest notice and kind cleanup protect a whole group.",
        sound="achoo, wipe-wipe",
    ),
    Incident(
        title="the berry spill",
        setup="A bowl of crushed berries tipped near the practice boundary and painted the paving stones purple.",
        hazard="Sticky juice could attract insects and make a landing paw slide.",
        wrong_turn="The little hare reached for dry leaves to scatter over the puddle.",
        clue="One leaf stuck fast while an ant followed the sweet-smelling edge.",
        helper_line='"Covering a spill gives it a disguise, not a solution," the helper said.',
        safe_plan="They guarded the spot, fetched the caretaker, and moved practice to a clean mat well away from food.",
        result="The stones were washed, the bowl went onto a steady table, and the ant trail turned back toward the garden.",
        ending_image="A single purple berry rested safely in its bowl while a clean mat glowed gold in the afternoon light.",
        lesson="Food and tumbling need separate, well-kept places.",
        sound="splut, buzz-buzz",
    ),
    Incident(
        title="the dusty ceiling cloth",
        setup="A gust shook dust from an old shade cloth above the practice corner.",
        hazard="The fine dust made the mat gritty and could bother eyes and noses.",
        wrong_turn="The little hare thought three quick somersaults might blow the dust away.",
        clue="A finger drawn along the mat left a pale, powdery line.",
        helper_line='"Acrobatics cannot be our broom," the helper said with a smile.',
        safe_plan="They closed the corner, asked an adult to inspect the shade, and unrolled a covered spare mat in clean air.",
        result="The loose shade was secured, the dusty mat was cleaned properly, and the new practice corner stayed clear.",
        ending_image="The mended shade held still above them as one tiny dust mote drifted outside the rope and vanished.",
        lesson="Stop the source of a mess before starting the game again.",
        sound="fuff-fuff, whisk",
    ),
    Incident(
        title="the soap-bubble patch",
        setup="Soap bubbles from a cleaning bucket had escaped onto the smooth courtyard stones.",
        hazard="Soap helps clean in the right place, but a soapy landing area is dangerously slick.",
        wrong_turn="The little hare wanted to pop every bubble with dancing feet.",
        clue="A wooden marker slid sideways when the helper nudged it from outside the wet patch.",
        helper_line='"Cleaners must be rinsed away before feet return," the helper explained.',
        safe_plan="They set cones around the patch, told the custodian, and waited for rinsing and a dry-surface check.",
        result="Clear water carried away the soap, the stones dried, and the marker no longer slid.",
        ending_image="The final bubble floated over the cones, flashed seven colors, and popped far from the dry mat.",
        lesson="A cleaning tool is safe only when it is used and finished correctly.",
        sound="pop-pop, slosh",
    ),
    Incident(
        title="the birdseed surprise",
        setup="A torn birdseed pouch had sprinkled seeds across the porch practice lane.",
        hazard="Rolling over hard seeds could hurt a paw, and leaving food scattered would draw animals into the play area.",
        wrong_turn="The little hare offered to kick the seeds through the railing.",
        clue="A sparrow pecked near the lane while one round seed rolled beneath the mat's edge.",
        helper_line='"Moving litter out of sight can move the problem onto someone else," the helper said.',
        safe_plan="They stopped practice, asked an adult for a brush and pan, sealed the pouch, and checked beneath every mat corner.",
        result="The seeds returned to a feeder tray, the floor was swept, and the mat lay flat again.",
        ending_image="Three sparrows ate from the proper feeder while the empty porch lane stretched clean and smooth below.",
        lesson="Put a spill where it belongs instead of passing it along.",
        sound="tick-tick, brush-brush",
    ),
    Incident(
        title="the borrowed mat",
        setup="A rolled mat arrived from another club with no cleaning tag attached.",
        hazard="Nobody knew where it had been used or whether it had been cleaned between groups.",
        wrong_turn="Because it smelled like lemons, the little hare assumed it must be ready.",
        clue="The logbook showed a blank space where the cleaning check should have been signed.",
        helper_line='"A pleasant smell is not a safety record," the helper said.',
        safe_plan="They kept the mat rolled, asked the equipment keeper to clean and inspect it, and used their documented spare.",
        result="The keeper added a dated tag, repaired a loose edge, and returned the borrowed mat only after it dried.",
        ending_image="Two neat tags dangled from two rolled mats, each bearing a fresh green check.",
        lesson="Good records make shared equipment trustworthy.",
        sound="rrrip, click",
    ),
    Incident(
        title="the muddy shoe shortcut",
        setup="Visitors crossed the practice square in muddy shoes while carrying garden pots.",
        hazard="Small clods hid along the mat border where a tumbling paw could land.",
        wrong_turn="The little hare suggested jumping over each clod during the somersault run.",
        clue="A pebble-sized lump crumbled when the helper pressed it with a broom handle.",
        helper_line='"A safe landing should not depend on dodging surprises," the helper said.',
        safe_plan="They redirected visitors along a marked path, asked for the border to be swept, and inspected the clean mat together.",
        result="The garden pots arrived by the new route, and the practice square stayed free of clods.",
        ending_image="Fresh arrow signs pointed one way to the garden and another to the spotless blue mat.",
        lesson="A clear route prevents the same mess from returning.",
        sound="clop-clop, skritch",
    ),
    Incident(
        title="the forgotten bandage wrapper",
        setup="A sealed bandage wrapper lay beside the mat after the first-aid kit had been checked.",
        hazard="Even harmless litter does not belong where hands and heads touch the ground.",
        wrong_turn="The little hare planned to tuck the wrapper beneath the mat until practice ended.",
        clue="The raised corner rocked when a beanbag rolled across it.",
        helper_line='"Under the mat is still in the practice space," the helper said.',
        safe_plan="They used a litter picker, put the wrapper in the proper bin, washed their paws, and flattened every mat edge.",
        result="The beanbag rolled straight across the cleared border, proving there was no hidden bump.",
        ending_image="The little beanbag came to rest beside a clean, perfectly flat corner as the bin lid clicked shut.",
        lesson="Small pieces of litter deserve a complete cleanup too.",
        sound="crinkle, clack",
    ),
    Incident(
        title="the mystery paw rash",
        setup="A friend noticed an itchy patch after using a shared costume cuff near the practice area.",
        hazard="The group did not know whether the cuff carried an irritant, so sharing it again would be unwise.",
        wrong_turn="The little hare offered the friend a random scented lotion from the prop box.",
        clue="The costume label listed a new detergent, but it did not explain the rash by itself.",
        helper_line='"We do not guess at treatments; we tell a trusted adult and pause the shared item," the helper said.',
        safe_plan="An adult cared for the friend, sealed the cuff for inspection, cleaned shared surfaces, and gave everyone plain wrist ribbons instead.",
        result="The friend rested comfortably, the uncertain cuff stayed out of use, and practice continued without sharing skin-contact props.",
        ending_image="Matching clean ribbons fluttered from raised paws while the sealed costume bag waited on the caretaker's shelf.",
        lesson="When a health cause is uncertain, pause, report, and choose a safer alternative.",
        sound="zip, flutter-flutter",
    ),
]


OPENING_ROUTES = [
    "The practice bell had barely rung when {hero} noticed something was different.",
    "On the morning of the little tumbling show, {hero} arrived early to help {helper}.",
    "A curious sound interrupted {hero}'s warm-up before the first roll began.",
    "The clean practice square looked ready from afar, but {hero} decided to inspect it closely.",
    "Everyone expected a quick game until {hero} heard {sound} near the mat.",
    "{hero} had promised to demonstrate one careful somersault, yet the promise had to wait.",
    "At {place}, a small sanitation puzzle appeared just before practice.",
    "{helper} invited {hero} to be the day's safety checker as well as an acrobat.",
    "The group began with a listening game: every sound might reveal whether the space was ready.",
    "{hero} carried a cherished {prize} toward the mat and stopped at an unexpected sight.",
]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def reasonability_gate(setting: Setting, action: Action, prize: Prize) -> bool:
    return prize.region == action.risky_region and action.id in setting.affords


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and action.mess in gear.guards:
            return gear
    return None


def predict_world(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: dataclasses.replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in world.entities.items()}
    actor2 = sim.get(actor.id)
    actor2.meters[action.mess] = actor2.meters.get(action.mess, 0.0) + 1.0
    prize = sim.get(prize_id)
    dirty = actor2.meters[action.mess] >= THRESHOLD and not sim.covered(actor2, prize.region)
    return {"soiled": dirty}


def tell(
    setting: Setting,
    action: Action,
    prize_cfg: Prize,
    hero_name: str,
    helper_name: str,
    seed: Optional[int],
) -> World:
    world = World(setting)
    story_seed = seed if seed is not None else 0
    incident = INCIDENTS[story_seed % len(INCIDENTS)]
    route = OPENING_ROUTES[(story_seed // len(INCIDENTS)) % len(OPENING_ROUTES)]

    hero = world.add(Entity(id=hero_name, kind="character", type="hare", traits=["small", "bright-eyed"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="owl", traits=["wise"]))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=helper.id,
        region=prize_cfg.region,
    ))

    world.say(route.format(hero=hero.id, helper=helper.id, sound=incident.sound, place=setting.place, prize=prize.label))
    world.say(
        f"{hero.id}, a small hare who loved {action.gerund}, had come to {setting.place} with {helper.id}."
    )
    world.say(f"{hero.id} wanted to {action.verb} at {setting.place}.")
    world.say(
        f"They brought {prize.phrase} and planned a supervised somersault on a clean, dry mat with plenty of clear space."
    )
    world.say(f"Instead, they faced {incident.title}: {incident.setup} Nearby came the sound {incident.sound}.")

    world.para()
    world.say(incident.hazard)
    world.say(incident.wrong_turn)
    world.say(incident.helper_line.replace("the helper", helper.id))
    world.say(f"{hero.id} paused the game and looked for evidence instead of tumbling through the problem.")

    world.para()
    world.say(incident.clue)
    world.say(f'"That clue tells us what to check before anyone flips," {hero.id} said.')
    world.say(incident.safe_plan)
    world.say(
        "Only after a responsible adult or helper confirmed that the surface was sanitary, dry, flat, and clear did the practice rope come down."
    )

    world.para()
    world.say(incident.result)
    world.say(
        f"With {helper.id} watching and no one crowding the landing space, {hero.id} performed one controlled somersault on the inspected mat: {action.sound}, then thump."
    )
    world.say(f"The {prize.label} stayed clean, and {hero.id} bowed instead of rushing into another turn.")
    world.say(incident.ending_image)
    world.say(f"The fable's lesson was this: {incident.lesson}")

    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    hero.meters[action.mess] = 0.0
    prize.meters["clean"] = 1.0
    gear_ent = world.add(
        Entity(id="mat", type="gear", label="a clean, dry practice mat", protective=True, covers={"hands", "torso", "feet"})
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        action=action,
        gear=gear_ent,
        setting=setting,
        incident=incident,
        clue=incident.clue,
        safe_plan=incident.safe_plan,
        result=incident.result,
        lesson=incident.lesson,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    incident = f["incident"]
    return [
        f"Write a short fable for children about {hero.id}, {incident.title}, and a sanitary choice before a {action.keyword} game.",
        f"Tell a gentle story where {hero.id} uses the clue '{incident.clue}' before trying to {action.verb}.",
        f"Write a fable with the sound effects '{incident.sound}' and '{action.sound}', keeping {prize.phrase} clean and ending with: {incident.ending_image}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    incident = f["incident"]
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who wanted to {action.verb} at {place}?",
            answer=f"{hero.id} wanted to {action.verb} at {place}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} understand {incident.title}?",
            answer=incident.clue,
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} make the activity sanitary and safe?",
            answer=incident.safe_plan,
        ),
        QAItem(
            question="What changed before the somersault could begin?",
            answer=incident.result,
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=f"The fable taught that {incident.lesson.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a somersault?",
            answer="A somersault is a turn or flip where the body rolls over in a quick arc, often with feet and hands moving in a neat pattern.",
        ),
        QAItem(
            question="What does sanitary mean?",
            answer="Sanitary means clean and safe from dirt or germs, so people can use the place without making it messy or unhealthy.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to help readers hear the action in their minds, like a whoosh for a flip or a thump for a landing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="schoolyard", action="somersault", prize="cloth", name="Milo", helper="Mother Owl"),
    StoryParams(place="courtyard", action="somersault", prize="apron", name="Nia", helper="Aunt Fern"),
]


ASP_RULES = r"""
% A prize is at risk when the action affects the same body region.
prize_at_risk(A, P) :- risky(A, R), worn_on(P, R).

% A gear item fixes the problem only if it covers the risky region and guards the mess.
fix(G, A, P) :- prize_at_risk(A, P), covers(G, R), worn_on(P, R), guards(G, M), mess_of(A, M).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), fix(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("risky", aid, a.risky_region))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            if aid not in setting.affords:
                continue
            for pid, prize in PRIZES.items():
                if prize.region == action.risky_region and select_gear(action, prize):
                    out.append((place, aid, pid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about somersaults, sanitary choices, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = []
    for place, action, prize in valid_combos():
        if getattr(args, "place", None) and getattr(args, "place", None) != place:
            continue
        if getattr(args, "action", None) and getattr(args, "action", None) != action:
            continue
        if getattr(args, "prize", None) and getattr(args, "prize", None) != prize:
            continue
        combos.append((place, action, prize))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIONS, params.action),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.helper,
        params.seed,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for v in vals:
            print(v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
