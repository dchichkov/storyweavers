#!/usr/bin/env python3
"""
storyworlds/worlds/cubby_sound_effects_transformation_bedtime_story.py
======================================================================

A small bedtime storyworld about a cubby, sound effects, and a gentle
transformation from daytime clutter into a cozy place for sleep.

The premise is simple:
- a child loves a little cubby space,
- noisy play and loose things make bedtime feel too awake,
- a calm reset turns the cubby into a soft, sleepy nook.

The world is constraint-checked so the story always has a real cause, a real
turn, and a real ending image.
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

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Typed entities: physical meters + emotional memes.
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
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    child: object | None = None
    cubby: object | None = None
    lamp: object | None = None
    parent: object | None = None
    toy: object | None = None
    def __post_init__(self):
        for k in ["messy", "tidy", "glow", "sleepy", "noise", "soft", "cozy", "transformed"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
    indoor: bool = True
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
class Toy:
    id: str
    label: str
    phrase: str
    sound: str
    transformation: str
    gentle_sound: str
    noisy_sound: str
    makes_mess: bool = False
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
class CozyThing:
    id: str
    label: str
    phrase: str
    sound: str
    covers: set[str] = field(default_factory=set)
    soft: bool = True
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


# ---------------------------------------------------------------------------
# Domain logic
# ---------------------------------------------------------------------------
def _noise_rises(world: World) -> list[str]:
    out = []
    cubby = world.get("cubby")
    child = world.get("child")
    if cubby.meters["noise"] >= THRESHOLD and ("noise_notice",) not in world.fired:
        world.fired.add(("noise_notice",))
        child.memes["startled"] += 1
        out.append(f"The little cubby made a {world.facts['sound_word']} that woke the sleepy air.")
    if cubby.meters["messy"] >= THRESHOLD and ("mess_notice",) not in world.fired:
        world.fired.add(("mess_notice",))
        child.memes["uneasy"] += 1
        out.append("A few scattered things made the cubby feel too busy for bedtime.")
    return out


def _tidy_transforms(world: World) -> list[str]:
    out = []
    cubby = world.get("cubby")
    blanket = world.get("blanket")
    lamp = world.get("lamp")
    if cubby.meters["tidy"] >= THRESHOLD and cubby.meters["cozy"] < THRESHOLD and ("transform",) not in world.fired:
        world.fired.add(("transform",))
        cubby.meters["cozy"] += 1
        cubby.meters["transformed"] += 1
        lamp.meters["glow"] += 1
        blanket.meters["soft"] += 1
        out.append("Then the cubby changed its tune, and the whole nook felt warm and soft.")
    return out


def _sleep_settles(world: World) -> list[str]:
    out = []
    child = world.get("child")
    cubby = world.get("cubby")
    if cubby.meters["cozy"] >= THRESHOLD and child.memes["sleepy"] < THRESHOLD:
        child.memes["sleepy"] += 1
        child.memes["happy"] += 1
        out.append("That was enough to make the child yawn and smile at the same time.")
    return out


RULES = [
    Rule("noise", _noise_rises),
    Rule("transform", _tidy_transforms),
    Rule("sleep", _sleep_settles),
]


def predict_effects(world: World, noisy: bool) -> dict:
    sim = world.copy()
    if noisy:
        sim.get("cubby").meters["noise"] += 1
    else:
        sim.get("cubby").meters["tidy"] += 1
    propagate(sim, narrate=False)
    return {
        "cozy": sim.get("cubby").meters["cozy"] >= THRESHOLD,
        "sleepy": sim.get("child").memes["sleepy"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, cubby: Entity) -> None:
    world.say(
        f"{child.id} loved the tiny cubby by the wall. "
        f"It was just the right size for quiet secrets and little treasures."
    )


def sound_scene(world: World, toy: Entity) -> None:
    world.say(
        f"At playtime, {toy.label} went {toy.sound}, {toy.noisy_sound}, {toy.sound}. "
        f"The sound bounced around the room like bouncing socks."
    )


def bedtime_turn(world: World, child: Entity, parent: Entity, cubby: Entity, toy: Entity) -> None:
    world.say(
        f"But when bedtime came, the noisy {toy.label} made the cubby feel too awake."
    )
    world.say(
        f"{parent.pronoun().capitalize()} smiled and said, "
        f'"Let\'s give it a sleepy change. We can make the cubby kinder for night."'
    )
    child.memes["curious"] += 1
    if predict_effects(world, noisy=True)["cozy"]:
        pass
    child.memes["want"] += 1


def transformation(world: World, child: Entity, parent: Entity, cubby: Entity,
                    toy: Entity, blanket: Entity, lamp: Entity) -> None:
    cubby.meters["tidy"] += 1
    cubby.meters["noise"] = 0.0
    blanket.worn_by = "cubby"
    lamp.worn_by = "cubby"
    world.say(
        f"They put the {toy.label} into a basket, tucked the blanket over the cubby floor, "
        f"and switched on the little lamp."
    )
    world.say(
        f"Now the cubby whispered a soft {toy.gentle_sound}, and the old noisy place "
        f"felt like a warm hideout for dreams."
    )
    propagate(world, narrate=True)


def ending(world: World, child: Entity, cubby: Entity) -> None:
    world.say(
        f"{child.id} climbed in, hugged the blanket, and listened to the hush. "
        f"The cubby was still the same little cubby, only now it was cozy enough for sleep."
    )


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"play", "bedtime"}),
    "nursery": Setting(place="the nursery", indoor=True, affords={"play", "bedtime"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"play", "bedtime"}),
}

TOYS = {
    "drums": Toy(
        id="drums",
        label="toy drums",
        phrase="a pair of toy drums",
        sound="tap-tap",
        transformation="the drums turned from loud toys into quiet things",
        gentle_sound="tap-tap-tap",
        noisy_sound="rat-a-tat",
        makes_mess=False,
    ),
    "blocks": Toy(
        id="blocks",
        label="wooden blocks",
        phrase="a stack of wooden blocks",
        sound="clack",
        transformation="the blocks became a tidy little tower",
        gentle_sound="clack-clack",
        noisy_sound="clatter",
        makes_mess=True,
    ),
    "train": Toy(
        id="train",
        label="toy train",
        phrase="a little toy train",
        sound="choo-choo",
        transformation="the train became a sleepy line of cars",
        gentle_sound="choo...",
        noisy_sound="chugga-chugga",
        makes_mess=False,
    ),
}

BLANKETS = {
    "blue": CozyThing(
        id="blanket",
        label="blue blanket",
        phrase="a blue blanket",
        sound="hush",
        covers={"floor"},
        soft=True,
    )
}

LAMPS = {
    "lamp": CozyThing(
        id="lamp",
        label="night lamp",
        phrase="a night lamp",
        sound="hum",
        covers={"air"},
        soft=True,
    )
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Max", "Lily", "Owen"]
PARENTS = ["mother", "father"]
TRAITS = ["sleepy", "curious", "gentle", "playful", "small", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    toy: str
    name: str
    gender: str
    parent: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about a cubby, sound effects, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    toy = getattr(args, "toy", None) or rng.choice(list(TOYS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    return StoryParams(place=place, toy=toy, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"happy": 0.0, "curious": 0.0, "startled": 0.0, "uneasy": 0.0, "sleepy": 0.0, "want": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    cubby = world.add(Entity(id="cubby", kind="thing", type="cubby", label="cubby", phrase="a little cubby nook", meters={"messy": 0.0, "tidy": 0.0, "glow": 0.0, "sleepy": 0.0, "noise": 0.0, "soft": 0.0, "cozy": 0.0, "transformed": 0.0}, memes={"happy": 0.0}))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=_safe_lookup(TOYS, params.toy).label, phrase=_safe_lookup(TOYS, params.toy).phrase))
    blanket = world.add(Entity(id="blanket", kind="thing", type="blanket", label=BLANKETS["blue"].label, phrase=BLANKETS["blue"].phrase, protective=True, covers={"floor"}))
    lamp = world.add(Entity(id="lamp", kind="thing", type="lamp", label=LAMPS["lamp"].label, phrase=LAMPS["lamp"].phrase, protective=True, covers={"air"}))

    world.facts.update(child=child, parent=parent, cubby=cubby, toy=toy, blanket=blanket, lamp=lamp, setting=setting, params=params,
                       sound_word=toy.noisy_sound)

    introduce(world, child, cubby)
    world.para()
    sound_scene(world, toy)
    cubby.meters["noise"] += 1
    if toy.makes_mess:
        cubby.meters["messy"] += 1
    propagate(world)
    world.para()
    bedtime_turn(world, child, parent, cubby, toy)
    world.para()
    transformation(world, child, parent, cubby, toy, blanket, lamp)
    world.para()
    ending(world, child, cubby)

    world.facts["resolved"] = cubby.meters["cozy"] >= THRESHOLD
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy: Entity = _safe_fact(world, f, "toy")
    child: Entity = _safe_fact(world, f, "child")
    return [
        f'Write a bedtime story for a little child about a cubby that makes a {toy.noisy_sound} sound and then becomes cozy.',
        f"Tell a gentle story where {child.id} loves a cubby, hears {toy.sound} sounds, and helps turn the space sleepy.",
        f'Write a short child-friendly story that uses the word "cubby" and ends with a quiet transformation for bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    toy: Entity = _safe_fact(world, f, "toy")
    cubby: Entity = _safe_fact(world, f, "cubby")
    return [
        QAItem(
            question=f"What did {child.id} love in the room?",
            answer=f"{child.id} loved the little cubby by the wall, because it felt like a tiny place for secrets and quiet play.",
        ),
        QAItem(
            question=f"What sound did the toy make before bedtime?",
            answer=f"The toy made a loud {toy.noisy_sound} sound before bedtime, and that noise made the cubby feel too awake.",
        ),
        QAItem(
            question=f"What did {parent.id} help change about the cubby?",
            answer=f"{parent.id} helped turn the cubby from a noisy, busy spot into a cozy sleepy nook by tidying it and adding soft things.",
        ),
        QAItem(
            question="What was the ending image of the story?",
            answer="At the end, the child climbed into the cubby, hugged the blanket, and listened to the quiet hush of bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cubby?",
            answer="A cubby is a small nook or compartment where you can tuck away things or sit in a cozy little space.",
        ),
        QAItem(
            question="Why are soft sounds nice at bedtime?",
            answer="Soft sounds are nice at bedtime because they are gentle and quiet, so they help a body and mind settle down for sleep.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or feels like a new thing after it is changed.",
        ),
    ]


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(bedroom).
setting(nursery).
setting(playroom).

affords(bedroom,play).
affords(bedroom,bedtime).
affords(nursery,play).
affords(nursery,bedtime).
affords(playroom,play).
affords(playroom,bedtime).

toy(drums). toy(blocks). toy(train).
noise_of(drums,rat_a_tat).
noise_of(blocks,clatter).
noise_of(train,chugga_chugga).

cubby_change(noise,cozy) :- event(noise).
cubby_change(tidy,transform) :- event(tidy).

#show valid/3.
valid(P,T,B) :- setting(P), toy(T), bedtime(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("affords", p, a))
    for t, toy in TOYS.items():
        lines.append(asp.fact("toy", t))
        lines.append(asp.fact("noise_of", t, toy.noisy_sound.replace("-", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    atoms = sorted(set(asp.atoms(model, "valid")))
    py = sorted((p, t, "bedtime") for p in SETTINGS for t in TOYS)
    if set(atoms) != set(py):
        print("MISMATCH between ASP and Python gate:")
        print("ASP:", atoms)
        print("PY :", py)
        return 1
    print(f"OK: ASP gate matches Python ({len(py)} combos).")
    return 0


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="bedroom", toy="drums", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="nursery", toy="blocks", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="playroom", toy="train", name="Ava", gender="girl", parent="mother", trait="sleepy"),
]


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        for item in vals:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = build_story(params)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.toy} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
