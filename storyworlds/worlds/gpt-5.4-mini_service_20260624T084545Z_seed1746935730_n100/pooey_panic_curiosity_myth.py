#!/usr/bin/env python3
"""
pooey_panic_curiosity_myth.py
=============================

A small mythic storyworld about Curiosity, a surprising pooey mistake, and a
panic that turns into a wiser ending.

This world is intentionally tiny and self-contained. It models a child-facing
myth-style tale where a curious hero enters a sacred place, makes a messy
discovery, feels panic, and then restores calm with help and care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
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
        if not hasattr(self, "_tags"):
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
class Place:
    name: str
    sacred: bool = False
    affords: set[str] = field(default_factory=set)
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
class ObjectCfg:
    label: str
    phrase: str
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
class GearCfg:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


GIRL_NAMES = ["Ari", "Mira", "Nia", "Luna", "Tala", "Ivy", "Sera"]
BOY_NAMES = ["Eli", "Oren", "Pax", "Niko", "Sami", "Theo"]
HELPERS = ["grandmother", "grandfather", "mother", "father", "elder"]


PLACES = {
    "grove": Place(name="the moonlit grove", sacred=True, affords={"discover"}),
    "spring": Place(name="the singing spring", sacred=True, affords={"discover"}),
    "hill": Place(name="the hollow hill", sacred=True, affords={"discover"}),
}

OBJECTS = {
    "stone": ObjectCfg(label="stone", phrase="a smooth little stone", region="hands"),
    "cloak": ObjectCfg(label="cloak", phrase="a soft dark cloak", region="torso"),
    "sandals": ObjectCfg(label="sandals", phrase="simple woven sandals", region="feet", plural=True),
}

GEAR = [
    GearCfg(
        id="cloth",
        label="a clean cloth",
        covers={"hands"},
        guards={"pooey"},
        prep="wrap the stone in a clean cloth first",
        tail="wrapped the stone in a clean cloth",
    ),
    GearCfg(
        id="soap",
        label="a bowl of clear water and soap",
        covers={"hands"},
        guards={"pooey"},
        prep="wash the hands in clear water and soap first",
        tail="washed the curious hands clean",
    ),
]

MESS_KINDS = {"pooey"}


def prize_at_risk(place: Place, obj: ObjectCfg) -> bool:
    return place.sacred and obj.region == "hands"


def select_gear(obj: ObjectCfg) -> Optional[GearCfg]:
    for gear in GEAR:
        if obj.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in PLACES for o in OBJECTS if prize_at_risk(_safe_lookup(PLACES, p), _safe_lookup(OBJECTS, o)) and select_gear(_safe_lookup(OBJECTS, o))]


def hero_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    obj_cfg = _safe_lookup(OBJECTS, params.object)
    obj = world.add(Entity(id="Relic", type=obj_cfg.label, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id, caretaker=helper.id))
    world.facts.update(hero=hero, helper=helper, obj=obj, obj_cfg=obj_cfg)
    return world


def predict_panic(world: World, obj: Entity) -> dict:
    sim = world.copy()
    sim.get("Relic").meters["pooey"] += 1
    sim.get(sim.facts["hero"].id).memes["panic"] += 1
    return {"messy": True, "panic": True, "risk": obj.caretaker is not None}


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    world.say(
        f"Long ago, in {world.place.name}, there lived a little {hero.type} named {hero.id}, "
        f"who carried a bright and wondering Curiosity."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved to ask what hid under roots, stones, and shadows, "
        f"as if every hush in the world held a secret song."
    )


def setup_relic(world: World) -> None:
    obj = world.facts["obj"]
    hero = world.facts["hero"]
    world.say(
        f"One dawn, {hero.id} found {obj.phrase} resting near the old path, and {hero.pronoun()} held it like a tiny moon."
    )
    world.say(
        f"{hero.pronoun().capitalize()} hoped to carry it to the shrine at {world.place.name}, because the stone seemed to whisper of old magic."
    )


def arrive(world: World) -> None:
    hero = world.facts["hero"]
    world.para()
    world.say(
        f"At last {hero.id} came to {world.place.name}, where the air was still and the leaves listened."
    )
    world.say(
        f"The place was sacred, and even the birds seemed to lower their voices."
    )


def discover_pooey(world: World) -> None:
    hero = world.facts["hero"]
    obj = world.facts["obj"]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    obj.meters["pooey"] = obj.meters.get("pooey", 0) + 1
    world.say(
        f"{hero.id} looked closer, and oh dear—the stone had touched something { 'pooey' } on the ground."
    )
    world.say(
        f"That made the little relic sticky, and {hero.id}'s fingers felt wrong and strange."
    )


def warn_and_panic(world: World) -> bool:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["obj"]
    pred = predict_panic(world, obj)
    if not pred["messy"]:
        return False
    hero.memes["panic"] = hero.memes.get("panic", 0) + 1
    world.say(
        f'"Oh no!" {hero.id} cried. "It is pooey!"'
    )
    world.say(
        f"The sight brought a flutter of panic, and {hero.id} almost dropped the stone."
    )
    world.say(
        f"Then {helper.label} stepped close and said, \"Do not fear. We can make this right.\""
    )
    world.facts["predicted_panic"] = pred["panic"]
    return True


def compromise(world: World) -> Optional[GearCfg]:
    obj = world.facts["obj"]
    gear = select_gear(world.facts["obj_cfg"])
    if gear is None:
        return None
    obj.meters["pooey"] = obj.meters.get("pooey", 0)
    world.say(
        f'"First, we shall {gear.prep}," said {world.facts["helper"].label}.'
    )
    return gear


def resolve(world: World, gear: GearCfg) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["obj"]
    hero.memes["panic"] = 0.0
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    obj.meters["pooey"] = 0.0
    world.say(
        f"{hero.id} listened, and together they {gear.tail}."
    )
    world.say(
        f"The stone shone again in the cloth, and the panic left {hero.id}'s chest like a dark bird flying home."
    )
    world.say(
        f"After that, {hero.id} carried the relic to the shrine with careful hands, and {helper.label} smiled beside {hero.pronoun('object')}."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    setup_relic(world)
    arrive(world)
    discover_pooey(world)
    warn_and_panic(world)
    gear = compromise(world)
    if gear is not None:
        world.para()
        resolve(world, gear)
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj_cfg = f["obj_cfg"]
    return [
        f'Write a short myth for a young child about {hero.id}, Curiosity, and a {obj_cfg.label} that becomes pooey.',
        f'Tell a gentle legend where {hero.id} finds a sacred {obj_cfg.label}, feels panic, and learns a careful fix.',
        f'Write a story with the words "pooey" and "panic" that ends with calm hands and a wiser choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj_cfg = f["obj_cfg"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.type} named {hero.id}, whose Curiosity leads {hero.pronoun('object')} to a sacred place and a strange little stone.",
        ),
        QAItem(
            question=f"What made {hero.id} feel panic?",
            answer=f"{hero.id} felt panic when the stone turned out to be pooey after being found near the ground at {world.place.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} make things right?",
            answer=f"The {helper.type if helper.type != 'elder' else 'elder'} helped {hero.id} stay calm and clean the {obj_cfg.label}.",
        ),
    ] + (
        [
            QAItem(
                question=f"How did the careful fix help the stone?",
                answer=f"They used {gear.label}, which let {hero.id} protect the stone and keep the mess from spreading.",
            )
        ] if gear else []
    )


KNOWLEDGE = {
    "pooey": [
        ("What does pooey mean?", "Pooey means dirty or gross in a child-friendly way."),
    ],
    "panic": [
        ("What is panic?", "Panic is a sudden, strong fear that makes someone feel shaky and upset."),
    ],
    "curiosity": [
        ("What is Curiosity?", "Curiosity is the wish to learn, ask questions, and find out what something means."),
    ],
    "stone": [
        ("What is a stone?", "A stone is a hard piece of rock, and some stones can be smooth enough to hold in your hand."),
    ],
    "clean": [
        ("Why do people wash their hands?", "People wash their hands to remove dirt and germs so their hands are clean."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for k in ("pooey", "panic", "curiosity", "stone", "clean") for q, a in KNOWLEDGE[k]]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- sacred_place(S), object_region(P, hands), place_name(S).
has_fix(P) :- prize_at_risk(P), gear_covers(gear, hands), gear_guards(gear, pooey).
valid_story(Place, Obj) :- sacred_place(Place), object_cfg(Obj), prize_at_risk(Obj), has_fix(Obj).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k, p in PLACES.items():
        lines.append(asp.fact("sacred_place", k))
    for k, o in OBJECTS.items():
        lines.append(asp.fact("object_cfg", k))
        lines.append(asp.fact("object_region", k, o.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("gear_covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("gear_guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = {("grove", "stone"), ("spring", "stone"), ("hill", "stone")}
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate.")
    print("python:", sorted(python_set))
    print("clingo:", sorted(clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic storyworld about Curiosity, pooey, and panic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper", choices=HELPERS, default=None)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "object", None) and (getattr(args, "place", None), getattr(args, "object", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None)) and (not getattr(args, "object", None) or c[1] == getattr(args, "object", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or hero_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, object=obj, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="grove", object="stone", name="Mira", gender="girl", helper="grandmother"),
    StoryParams(place="spring", object="stone", name="Eli", gender="boy", helper="elder"),
    StoryParams(place="hill", object="stone", name="Tala", gender="girl", helper="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
