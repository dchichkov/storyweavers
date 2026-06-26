#!/usr/bin/env python3
"""
storyworlds/worlds/motel_drowse_yank_transformation_misunderstanding_mystery.py
===============================================================================

A small mystery-style story world about a sleepy child at a motel, a mistaken
haunting, and a transformation that turns out to be something ordinary.

Premise:
- A tired child arrives at a roadside motel with a parent.
- The child notices strange sounds, grows drowsy, and yanks at a curtain or
  door because they think they have found a mystery.
- The apparent "monster" is really an ordinary thing transformed by light,
  shadows, and a simple change in state.
- The misunderstanding resolves when the child learns the truth and the night
  becomes calm again.

This world keeps the prose concrete and state-driven:
- physical meters include drowse, yank, glow, and transformed
- emotional memes include worry, curiosity, confusion, relief, and trust
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    name: str
    detail: str
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
class CharacterProfile:
    type: str
    gender: str
    name_pool: list[str]
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
class MysteryState:
    clue: str
    sound: str
    shadow: str
    transformation: str
    explanation: str
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


SETTINGS = {
    "roadside_motel": Setting(
        name="the motel",
        detail="The hallway smelled like old carpet, warm lamps, and rain on pavement.",
    ),
    "poolside_motel": Setting(
        name="the motel pool",
        detail="The pool flickered under the sign lights, and wet footprints dotted the tile.",
    ),
    "desert_motel": Setting(
        name="the motel by the highway",
        detail="The parking lot stretched wide and quiet, with one blinking sign over the office.",
    ),
}

CHILDREN = {
    "boy": CharacterProfile(type="boy", gender="boy", name_pool=["Milo", "Theo", "Nate", "Eli", "Ben"]),
    "girl": CharacterProfile(type="girl", gender="girl", name_pool=["Ivy", "Maya", "Luna", "Nora", "Zoe"]),
}

PARENTS = {
    "mother": CharacterProfile(type="mother", gender="girl", name_pool=["June", "Ada", "Mina", "Ruth"]),
    "father": CharacterProfile(type="father", gender="boy", name_pool=["Owen", "Jack", "Paul", "Evan"]),
}

MYSTERIES = {
    "neon_shade": MysteryState(
        clue="a neon sign that turned the curtains blue",
        sound="a soft buzz from the hallway light",
        shadow="a long blue shape on the wall",
        transformation="the blue sign light changed the towel rack into a strange-looking monster shape",
        explanation="the 'monster' was only a towel rack and a hanging towel in blue light",
    ),
    "ice_bucket": MysteryState(
        clue="an ice bucket left under a dripping vent",
        sound="a little clink from the bucket",
        shadow="a round silver shape under the desk lamp",
        transformation="the lamp and the wet floor made the bucket look like a tiny robot",
        explanation="the 'robot' was really an ice bucket with a shiny lid",
    ),
    "curtain_creature": MysteryState(
        clue="a curtain twitching in the draft from the air conditioner",
        sound="a flutter-flutter from the window",
        shadow="a tall shape that seemed to breathe",
        transformation="the moving curtain and the dim light turned a coat hanger into a pretend creature",
        explanation="the 'creature' was just a coat hanger with a jacket on it",
    ),
}

ACTIONS = {
    "drowse": {
        "verb": "drowse",
        "gerund": "drowsing",
        "meter": "drowse",
        "feels": "sleepy",
    },
    "yank": {
        "verb": "yank",
        "gerund": "yanking",
        "meter": "yank",
        "feels": "pull-happy",
    },
    "transform": {
        "verb": "transform",
        "gerund": "transforming",
        "meter": "transformed",
        "feels": "changed",
    },
}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    child_gender: str
    child_name: str
    parent_role: str
    parent_name: str
    mystery: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A motel mystery with drowse, yank, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--child-name")
    ap.add_argument("--parent-role", choices=["mother", "father"])
    ap.add_argument("--parent-name")
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def pick(rng: random.Random, seq: list[str]) -> str:
    return seq[rng.randrange(len(seq))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or pick(rng, list(SETTINGS))
    mystery = getattr(args, "mystery", None) or pick(rng, list(MYSTERIES))
    child_gender = getattr(args, "child_gender", None) or pick(rng, ["boy", "girl"])
    parent_role = getattr(args, "parent_role", None) or pick(rng, ["mother", "father"])

    child_profile = CHILDREN[child_gender]
    parent_profile = _safe_lookup(PARENTS, parent_role)

    child_name = getattr(args, "child_name", None) or pick(rng, child_profile.name_pool)
    parent_name = getattr(args, "parent_name", None) or pick(rng, parent_profile.name_pool)

    if getattr(args, "child_name", None) and getattr(args, "child_name", None) == getattr(args, "parent_name", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        setting=setting,
        child_gender=child_gender,
        child_name=child_name,
        parent_role=parent_role,
        parent_name=parent_name,
        mystery=mystery,
    )


def child_pronoun(gender: str, case: str = "subject") -> str:
    return CHILDREN[gender].type and ({"subject": "he", "object": "him", "possessive": "his"} if gender == "boy" else {"subject": "she", "object": "her", "possessive": "her"})[case]


def parent_pronoun(role: str, case: str = "subject") -> str:
    return ({"subject": "she", "object": "her", "possessive": "her"} if role == "mother" else {"subject": "he", "object": "him", "possessive": "his"})[case]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
motel(roadside_motel).
motel(poolside_motel).
motel(desert_motel).

mystery(neon_shade).
mystery(ice_bucket).
mystery(curtain_creature).

#show compatible/2.
compatible(S, M) :- motel(S), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("motel", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def python_compatible() -> list[tuple[str, str]]:
    return sorted((s, m) for s in SETTINGS for m in MYSTERIES)


def asp_verify() -> int:
    a = set(asp_compatible())
    b = set(python_compatible())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combinations).")
        return 0
    print("Mismatch:")
    if a - b:
        print(" only in ASP:", sorted(a - b))
    if b - a:
        print(" only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(place=setting.name)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meters={"drowse": 0.0, "yank": 0.0, "curiosity": 0.0},
        memes={"worry": 0.0, "confusion": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name,
        kind="character",
        type=params.parent_role,
        label=params.parent_name,
        meters={"care": 0.0},
        memes={"calm": 0.0, "patience": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label=mystery.clue,
        phrase=mystery.clue,
        meters={"glow": 0.0, "transformed": 0.0},
        memes={"odd": 1.0},
    ))
    world.facts.update(
        child=child,
        parent=parent,
        clue=clue,
        setting=setting,
        mystery=mystery,
    )
    return world


def narrate_opening(world: World) -> None:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    setting: Setting = _safe_fact(world, f, "setting")
    mystery: MysteryState = _safe_fact(world, f, "mystery")

    world.say(
        f"{child.id} and {parent.id} checked into {setting.name} late in the evening. "
        f"{setting.detail}"
    )
    world.say(
        f"{child.id} was so tired that {child.pronoun('subject')} started to drowse in the lobby chair."
    )
    child.meters["drowse"] += 1.0
    child.memes["worry"] += 0.5
    world.para()
    world.say(
        f"Then {child.id} noticed {mystery.clue}, and {mystery.sound} made the room feel strange."
    )
    child.memes["curiosity"] += 1.0
    child.memes["confusion"] += 1.0
    child.meters["curiosity"] = 1.0


def narrate_misunderstanding(world: World) -> None:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    mystery: MysteryState = _safe_fact(world, f, "mystery")

    world.say(
        f"{child.id} pointed at {mystery.shadow} and whispered that something was hiding there."
    )
    child.memes["worry"] += 1.0
    child.meters["yank"] += 1.0
    world.say(
        f"Before {parent.id} could answer, {child.id} gave the curtain a hard yank."
    )
    if child.meters["yank"] >= THRESHOLD:
        child.memes["confusion"] += 0.5
    world.say(
        f"The shape on the wall changed at once, because {mystery.transformation}."
    )
    child.meters["transformed"] = 1.0


def narrate_resolution(world: World) -> None:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    mystery: MysteryState = _safe_fact(world, f, "mystery")

    world.say(
        f"{parent.id} leaned closer and looked twice, then smiled and explained that {mystery.explanation}."
    )
    child.memes["confusion"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["trust"] += 1.0
    parent.memes["patience"] += 1.0
    world.para()
    world.say(
        f"{child.id} let go of the curtain, yawned, and felt the room become ordinary again."
    )
    world.say(
        f"With the mystery solved, {child.id} drowsed off beside {parent.id}, and the motel light looked friendly instead of spooky."
    )


def generate_story(world: World) -> str:
    narrate_opening(world)
    narrate_misunderstanding(world)
    narrate_resolution(world)
    return world.render()


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    mystery: MysteryState = _safe_fact(world, f, "mystery")
    return [
        f"Write a short mystery story for a young child about {child.id} at a motel, with a sleepy mistake and a gentle explanation.",
        f"Tell a child-friendly motel story where {child.id} gets drowsy, yanks at a curtain, and discovers that {mystery.explanation}.",
        f"Write a simple mystery with the words motel, drowse, and yank, ending with a calm parent explaining the strange shape.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    mystery: MysteryState = _safe_fact(world, f, "mystery")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Why did {child.id} think something strange was happening at {setting.name}?",
            answer=f"{child.id} was drowsy, saw {mystery.clue}, and mistook {mystery.shadow} for something scary.",
        ),
        QAItem(
            question=f"What did {child.id} do that caused the mystery to change?",
            answer=f"{child.id} gave the curtain a hard yank, which changed the shape right away.",
        ),
        QAItem(
            question=f"How did {parent.id} explain the strange sight in the end?",
            answer=f"{parent.id} explained that {mystery.explanation}, so the scary-looking thing was not a real monster.",
        ),
        QAItem(
            question=f"How did {child.id} feel after the misunderstanding was cleared up?",
            answer=f"{child.id} felt relieved and trusted {parent.id} more after the explanation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motel?",
            answer="A motel is a place where people can stay for a night while traveling, often with rooms near the parking lot.",
        ),
        QAItem(
            question="What does drowsy mean?",
            answer="Drowsy means sleepy and a little slow, like when your eyes want to close.",
        ),
        QAItem(
            question="What does yank mean?",
            answer="To yank means to pull something quickly and hard.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because they do not have all the facts yet.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or appearance to another.",
        ),
        QAItem(
            question="Why can motel lights make ordinary things look spooky?",
            answer="Because bright signs and shadows can change the color and shape of things, so your eyes may guess wrong for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sample selection
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="roadside_motel", child_gender="boy", child_name="Milo", parent_role="mother", parent_name="June", mystery="curtain_creature"),
    StoryParams(setting="poolside_motel", child_gender="girl", child_name="Ivy", parent_role="father", parent_name="Owen", mystery="ice_bucket"),
    StoryParams(setting="desert_motel", child_gender="boy", child_name="Theo", parent_role="father", parent_name="Jack", mystery="neon_shade"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_compatible()
        print(f"{len(pairs)} compatible motel/mystery combinations:\n")
        for s, m in pairs:
            print(f"  {s:16} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name} at {p.setting} with {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
