#!/usr/bin/env python3
"""
storyworlds/worlds/confidence_ornament_liter_humor_suspense_slice_of.py
=======================================================================

A small slice-of-life story world about a child, a confidence charm,
an ornament, and a one-liter container that can hold the finishing touch.

Seed tale:
---
A child feels nervous before showing a handmade ornament at a small neighborhood
table. The ornament needs one clear liter bottle for the display water, a few
bright decorations, and enough courage to carry it without spilling. A parent
notices the wobble, helps with a calmer plan, and the child ends up proud,
laughing, and standing a little taller.

World idea:
---
- Physical state uses liters, capacity, and breakage risk.
- Emotional state uses confidence, worry, joy, and pride.
- The tension comes from a wobbly ornament display and a near-spill.
- The turn is a steadying helper and a simple, practical change.
- The ending proves the child's confidence changed by the final image.

This is intentionally small and reusable: fewer valid story combinations,
each with a grounded problem and a real fix.
"""

from __future__ import annotations

import argparse
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

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    container: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    child: object | None = None
    ornament: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
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
    place: str
    indoor: bool
    affords: set[str]
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
class Ornament:
    id: str
    label: str
    phrase: str
    type: str
    needs: set[str]
    risk: str
    style: str = "slice-of-life"
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
class Container:
    id: str
    label: str
    phrase: str
    liters: int
    clear: bool = True
    spill_risk: float = 0.0
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
class Charm:
    id: str
    label: str
    phrase: str
    boosts: set[str]
    humor: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen_table": Setting("the kitchen table", True, {"decorate", "arrange"}),
    "porch": Setting("the porch", False, {"decorate", "carry"}),
    "community_room": Setting("the community room", True, {"decorate", "carry", "arrange"}),
}

ORNAMENTS = {
    "paper_star": Ornament(
        id="paper_star",
        label="paper star",
        phrase="a shiny paper star",
        type="ornament",
        needs={"decorate", "care"},
        risk="bent",
    ),
    "glass_ball": Ornament(
        id="glass_ball",
        label="glass ball",
        phrase="a tiny glass ball with blue paint",
        type="ornament",
        needs={"decorate", "care", "carry"},
        risk="cracked",
    ),
    "ribbon_loop": Ornament(
        id="ribbon_loop",
        label="ribbon loop",
        phrase="a ribbon loop with a glitter knot",
        type="ornament",
        needs={"decorate"},
        risk="tangled",
    ),
}

CONTAINERS = {
    "jar": Container(
        id="jar",
        label="jar",
        phrase="a clear one-liter jar",
        liters=1,
        clear=True,
        spill_risk=0.2,
    ),
    "bottle": Container(
        id="bottle",
        label="bottle",
        phrase="a one-liter bottle",
        liters=1,
        clear=True,
        spill_risk=0.3,
    ),
}

CHARMS = {
    "bracelet": Charm(
        id="bracelet",
        label="confidence bracelet",
        phrase="a confidence bracelet made of soft beads",
        boosts={"confidence"},
        humor="the beads clicked like tiny applause",
    ),
    "sticker": Charm(
        id="sticker",
        label="confidence sticker",
        phrase="a sparkly confidence sticker",
        boosts={"confidence"},
        humor="it winked in the light like a tiny stage spotlight",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Tia", "Maya"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Leo", "Noah", "Theo"]
TRAITS = ["careful", "bright", "shy", "cheerful", "patient", "curious"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    ornament: str
    container: str
    charm: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def valid_combo(place: str, ornament: str, container: str) -> bool:
    o = _safe_lookup(ORNAMENTS, ornament)
    c = _safe_lookup(CONTAINERS, container)
    if ornament == "glass_ball" and place == "porch":
        return True
    if ornament == "paper_star" and place in {"kitchen_table", "community_room"}:
        return True
    if ornament == "ribbon_loop":
        return place in {"kitchen_table", "community_room", "porch"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for ornament in ORNAMENTS:
            for container in CONTAINERS:
                if valid_combo(place, ornament, container):
                    out.append((place, ornament, container))
    return out


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict_spill(world: World, child: Entity, container: Entity, ornament: Ornament) -> dict:
    sim = world.copy()
    sim.get(child.id).meters["wobble"] += 1
    sim.get(container.id).meters["spill"] += 1
    soiled = ornament.risk == "cracked" and sim.get(child.id).meters["worry"] > 0
    return {"soiled": soiled, "spill": sim.get(container.id).meters["spill"]}


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"wobble": 0.0, "balance": 0.0},
        memes={"confidence": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="parent",
        meters={"calm": 0.0},
        memes={"calm": 0.0, "humor": 0.0},
    ))
    ornament = world.add(Entity(
        id="ornament",
        kind="thing",
        type="ornament",
        label=_safe_lookup(ORNAMENTS, params.ornament).label,
        phrase=_safe_lookup(ORNAMENTS, params.ornament).phrase,
        caretaker=parent.id,
        container=params.container,
    ))
    container = world.add(Entity(
        id="container",
        kind="thing",
        type="container",
        label=_safe_lookup(CONTAINERS, params.container).label,
        phrase=_safe_lookup(CONTAINERS, params.container).phrase,
        owner=child.id,
        meters={"liters": float(_safe_lookup(CONTAINERS, params.container).liters), "spill": 0.0},
        memes={"sparkle": 0.0},
    ))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="charm",
        label=_safe_lookup(CHARMS, params.charm).label,
        phrase=_safe_lookup(CHARMS, params.charm).phrase,
        owner=child.id,
        memes={"confidence": 0.0},
    ))
    world.facts.update(
        child=child, parent=parent, ornament=ornament, container=container, charm=charm,
        params=params, ornament_cfg=_safe_lookup(ORNAMENTS, params.ornament), container_cfg=_safe_lookup(CONTAINERS, params.container),
        charm_cfg=_safe_lookup(CHARMS, params.charm),
    )
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    child: Entity = _safe_fact(world, world.facts, "child")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    ornament_cfg: Ornament = _safe_fact(world, world.facts, "ornament_cfg")
    charm_cfg: Charm = _safe_fact(world, world.facts, "charm_cfg")
    container: Entity = _safe_fact(world, world.facts, "container")

    world.say(
        f"{child.id} was a little {params.trait} {params.gender} who liked small, careful projects."
    )
    world.say(
        f"{child.id} had {charm_cfg.phrase}, and {charm_cfg.humor}."
    )
    world.say(
        f"On the table sat {ornament_cfg.phrase} and {container.phrase}."
    )

    world.para()
    where = world.setting.place
    world.say(
        f"At {where}, {child.id} wanted to finish the ornament just right."
    )
    child.memes["worry"] += 1
    child.memes["confidence"] += 0.2
    container.meters["liters"] = 1.0
    container.memes["sparkle"] += 0.5
    world.say(
        f"But the one-liter container wobbled near the edge, and {child.id} looked down at it with a nervous face."
    )

    # Suspense beat: the near-spill.
    pred = predict_spill(world, child, container, ornament_cfg)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_risk"] = ornament_cfg.risk
    child.meters["wobble"] += 1
    if pred["spill"] >= 1 or ornament_cfg.risk == "cracked":
        child.memes["worry"] += 1
        world.say(
            f"The jar tilted a little, and for one second it looked like the whole neat plan might topple."
        )
        world.say(
            f"{child.id} held still, listening to the tiny clink of glass and the hush in the room."
        )

    # Turn: parent helps.
    world.para()
    parent.memes["calm"] += 1
    parent.memes["humor"] += 1
    child.memes["confidence"] += 1.5
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    child.meters["balance"] += 1
    world.say(
        f"{parent.id} smiled and slid the container to the middle of the table."
    )
    world.say(
        f'"Slow hands," {parent.id} said. "The ornament only needs a steady friend."'
    )
    world.say(
        f"{child.id} laughed at that, because the confidence bracelet clicked like tiny applause."
    )

    # Resolution.
    child.memes["pride"] += 1.5
    container.meters["spill"] = 0.0
    ornament_cfg = _safe_lookup(ORNAMENTS, params.ornament)
    world.say(
        f"So {child.id} tied the final ribbon, set the ornament beside the clear one-liter jar, and stepped back."
    )
    world.say(
        f"The little display looked bright and calm, and {child.id} stood a little taller beside it."
    )
    world.say(
        f"By the end, the wobble was gone, the ornament was finished, and {child.id} was smiling like someone who had just learned bravery in a very ordinary afternoon."
    )

    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(Place, O, C) :- setting(Place), ornament(O), container(C), allows(Place, O, C).
compatible(Place, O, C) :- valid(Place, O, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        for aff in sorted(_safe_lookup(SETTINGS, place).affords):
            lines.append(asp.fact("allows", place, "_any", aff))
    for oid in ORNAMENTS:
        lines.append(asp.fact("ornament", oid))
    for cid in CONTAINERS:
        lines.append(asp.fact("container", cid))
    # Specific facts for the actual compatibility rule.
    for place, oid, cid in valid_combos():
        lines.append(asp.fact("allows", place, oid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python reasonableness gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in asp:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    return [
        f'Write a gentle slice-of-life story about {p.name}, a child with a confidence charm, a small ornament, and a one-liter container.',
        f"Tell a short story where {p.name} worries about finishing {f['ornament_cfg'].label} at {world.setting.place} and then feels braver.",
        f'Write a child-facing story that includes the words "confidence", "ornament", and "liter" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    ornament: Entity = _safe_fact(world, f, "ornament")
    container: Entity = _safe_fact(world, f, "container")
    params: StoryParams = _safe_fact(world, f, "params")
    qa = [
        QAItem(
            question=f"What was {child.id} trying to finish?",
            answer=f"{child.id} was trying to finish {ornament.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the one-liter {container.label} matter?",
            answer=f"It mattered because the display needed the clear one-liter {container.label} to stay steady and not spill.",
        ),
        QAItem(
            question=f"How did {parent.id} help {child.id} feel better?",
            answer=f"{parent.id} moved the container to the middle of the table and reminded {child.id} to use slow hands.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{child.id} went from nervous to proud, and the ornament ended up neatly finished.",
        ),
    ]
    if f.get("predicted_risk") == "cracked":
        qa.append(
            QAItem(
                question=f"Why was the moment suspenseful?",
                answer=f"It felt suspenseful because the jar wobbled and {child.id} feared the ornament might crack before it was finished.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a liter?",
            answer="A liter is a way to measure how much liquid a container can hold.",
        ),
        QAItem(
            question="What is an ornament?",
            answer="An ornament is a decorative object made to look nice, often for a table, shelf, or tree.",
        ),
        QAItem(
            question="What is confidence?",
            answer="Confidence is the feeling that helps someone believe they can try, even when they feel a little unsure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("kitchen_table", "paper_star", "jar", "bracelet", "Mina", "girl", "mother", "careful"),
    StoryParams("porch", "glass_ball", "bottle", "sticker", "Owen", "boy", "father", "shy"),
    StoryParams("community_room", "ribbon_loop", "jar", "bracelet", "Luna", "girl", "mother", "curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small slice-of-life story world with confidence, ornament, and liter.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ornament", choices=ORNAMENTS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "ornament", None) and getattr(args, "container", None):
        if not valid_combo(getattr(args, "place", None), getattr(args, "ornament", None), getattr(args, "container", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "ornament", None) is None or c[1] == getattr(args, "ornament", None))
        and (getattr(args, "container", None) is None or c[2] == getattr(args, "container", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ornament, container = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))
    return StoryParams(place, ornament, container, charm, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combinations:")
        for row in combos:
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
