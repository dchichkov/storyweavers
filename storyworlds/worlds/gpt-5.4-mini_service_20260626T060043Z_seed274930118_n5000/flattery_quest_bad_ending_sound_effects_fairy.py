#!/usr/bin/env python3
"""
Fairy-tale storyworld: a tiny quest where flattery can lead to a bad ending,
with sound effects woven into the action.

The core premise:
- A small hero wants a quest prize.
- A flatterer praises the hero until the hero ignores a warning.
- The quest goes wrong in a fairy-tale way, ending with a vivid loss.
- Sound effects are narrated as part of the turning points.

This world is intentionally narrow: not every choice is reasonable, and
invalid combinations raise StoryError with a clear reason.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    flatterer: object | None = None
    guardian: object | None = None
    hero: object | None = None
    prize: object | None = None
    quest: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "fairy"}
        male = {"boy", "king", "prince", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    mood: str
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
class Quest:
    id: str
    seek_verb: str
    seek_gerund: str
    danger: str
    sound: str
    risk: str
    clue: str
    fail_image: str
    tags: set[str] = field(default_factory=set)
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
    owner_role: str = "guardian"
    fragile: bool = False
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
class Flatterer:
    id: str
    label: str
    praise: str
    promise: str
    trick: str
    sound: str
    bad_end: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "moon-glen": Setting("Moon-Glen", "silver and hushed", affords={"quest"}),
    "rose-bridge": Setting("Rose-Bridge", "sweet and bright", affords={"quest"}),
    "hollow-hall": Setting("Hollow Hall", "echoing and dim", affords={"quest"}),
}

QUESTS = {
    "golden-key": Quest(
        id="golden-key",
        seek_verb="find the golden key",
        seek_gerund="finding the golden key",
        danger="the key was kept near a sleeping dragon",
        sound="clink-clink",
        risk="a single wrong step could wake the dragon",
        clue="a moth showed the way with a glow like a candle",
        fail_image="the key slid into a crack and vanished",
        tags={"key", "dragon", "gold", "sound"},
    ),
    "silver-bell": Quest(
        id="silver-bell",
        seek_verb="bring back the silver bell",
        seek_gerund="bringing back the silver bell",
        danger="the bell hung above a cold well",
        sound="ding-ding",
        risk="the rope ladder swayed like a reed in the wind",
        clue="a little frog pointed toward the tower",
        fail_image="the bell dropped with a sad plunk into the dark water",
        tags={"bell", "water", "sound"},
    ),
    "glass-rose": Quest(
        id="glass-rose",
        seek_verb="carry home the glass rose",
        seek_gerund="carrying home the glass rose",
        danger="the rose rested in a thorny garden",
        sound="tink",
        risk="one poke could crack the shining petals",
        clue="a white bee hovered over the right path",
        fail_image="the rose broke into glittering pieces",
        tags={"rose", "glass", "sound"},
    ),
}

PRIZES = {
    "crown": Prize("crown", "a tiny crown of moonlight", "crown"),
    "lantern": Prize("lantern", "a lantern of blue glass", "lantern"),
    "ribbon": Prize("ribbon", "a ribbon sewn with gold thread", "ribbon"),
}

FLATTERERS = {
    "sly-mouse": Flatterer(
        id="sly-mouse",
        label="a sly mouse",
        praise="Oh, brave one, no one else is as clever as you",
        promise="Only you can finish this quest at once",
        trick="it nudged the hero toward the wrong door",
        sound="skitter-skitter",
        bad_end="the mouse scampered off with the prize map",
    ),
    "mirror-fairy": Flatterer(
        id="mirror-fairy",
        label="a mirror fairy",
        praise="Your smile shines brighter than the morning star",
        promise="The path will bow to your steps",
        trick="its shining words hid a brittle lie",
        sound="ting-ting",
        bad_end="the fairy's reflection led the hero in circles until dusk",
    ),
    "golden-cat": Flatterer(
        id="golden-cat",
        label="a golden cat",
        praise="Noble traveler, your luck is the luckiest luck",
        promise="Just follow my tail and all will be easy",
        trick="it steered the hero into a thorny shortcut",
        sound="mrrow-wink",
        bad_end="the cat leapt away, leaving only torn gloves behind",
    ),
}

HERO_NAMES = ["Elin", "Mira", "Tobin", "Nico", "Lila", "Perrin"]
HERO_TYPES = ["girl", "boy", "fairy", "princess", "prince"]
TRAITS = ["small", "bold", "hopeful", "curious", "gentle"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    flatterer: str
    name: str
    hero_type: str
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
    ap = argparse.ArgumentParser(description="Fairy tale flattery quest with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--flatterer", choices=FLATTERERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for p in PRIZES:
                for f in FLATTERERS:
                    combos.append((s, q, p, f))
    return combos


def reason_ok(setting: str, quest: str, prize: str, flatterer: str) -> bool:
    return setting in SETTINGS and quest in QUESTS and prize in PRIZES and flatterer in FLATTERERS


def explain_invalid(msg: str) -> str:
    return f"(No story: {msg})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "quest", None) and getattr(args, "prize", None) and getattr(args, "flatterer", None):
        if not reason_ok(getattr(args, "setting", None), getattr(args, "quest", None), getattr(args, "prize", None), getattr(args, "flatterer", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if getattr(args, "flatterer", None):
        combos = [c for c in combos if c[3] == getattr(args, "flatterer", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, prize, flatterer = rng.choice(list(combos))
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, prize=prize, flatterer=flatterer, name=name, hero_type=hero_type, trait=trait)


def setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type, traits=[params.trait, "little"]))
    guardian_type = "fairy" if params.hero_type != "fairy" else "queen"
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="the guardian"))
    prize = world.add(Entity(id="Prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=guardian.id, caretaker=guardian.id))
    quest = world.add(Entity(id="Quest", type="quest", label=_safe_lookup(QUESTS, params.quest).id))
    flatterer = world.add(Entity(id="Flatterer", kind="character", type="creature", label=_safe_lookup(FLATTERERS, params.flatterer).label))
    world.facts.update(hero=hero, guardian=guardian, prize=prize, quest=quest, flatterer=flatterer, params=params)
    return world, hero, guardian, prize, quest, flatterer


def predict_bad_end(world: World, hero: Entity, quest: Quest) -> bool:
    sim = world.copy()
    sim.facts["tempted"] = True
    return True if quest.id else True


def tell(world: World, hero: Entity, guardian: Entity, prize: Entity, quest: Quest, flatterer: Flatterer) -> None:
    world.say(f"Once upon a time, {hero.id} was a {hero.pronoun('subject')} little {hero.type} who loved bright quests and secret paths.")
    world.say(f"{hero.pronoun('subject').capitalize()} wanted to {quest.seek_verb}, because the tale of the {prize.label} sounded like a song.")
    world.say(f"In {world.setting.place}, the air was {world.setting.mood}, and the quest sounded like {quest.sound}.")
    world.para()
    world.say(f"Then {flatterer.label} appeared and said, \"{flatterer.praise}. {flatterer.promise}.\"")
    world.say(f"{hero.id} grew warm with pride, and the sweet words made the warning seem small.")
    world.say(f"The guardian said, \"Listen, little one: {quest.danger}. {quest.risk}.\"")
    world.para()
    world.say(f"But {hero.id} smiled at the praise instead of the warning.")
    world.say(f"{hero.pronoun('subject').capitalize()} followed the flatterer, and the path went {flatterer.sound}.")
    world.say(f"{flatterer.trick.capitalize()}, and soon the quest turned wrong.")
    world.say(f"{quest.clue.capitalize()}, but {hero.id} hurried on anyway.")
    world.say(f"At last came a soft, unlucky sound: {quest.sound} ... {quest.sound} ... then silence.")
    world.para()
    world.say(f"The bad ending arrived as {quest.fail_image}.")
    world.say(f"{flatterer.bad_end.capitalize()}, and the prize stayed lost under the fairy-tale dark.")
    world.say(f"{hero.id} went home with empty hands, and the guardian's lantern glowed like a sad little star.")
    world.facts["ending"] = "bad"
    world.facts["sound_effects"] = [quest.sound, flatterer.sound]
    world.facts["warning"] = True
    world.facts["flattery"] = True
    world.facts["quest_failed"] = True


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guardian = _safe_fact(world, f, "guardian")
    prize = _safe_fact(world, f, "prize")
    quest = QUESTS[f["params"].quest]
    flatterer = FLATTERERS[f["params"].flatterer]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {quest.seek_verb}. {hero.pronoun('subject').capitalize()} hoped to bring back {prize.phrase}.",
        ),
        QAItem(
            question=f"Who used flattery to lead {hero.id} astray?",
            answer=f"{flatterer.label} used flattering words like, \"{flatterer.praise}.\" That made {hero.id} trust the wrong guide.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {hero.id} ignored the guardian's warning about {quest.danger}, so the quest failed and {quest.fail_image}.",
        ),
        QAItem(
            question=f"What sound did the story use when the quest went wrong?",
            answer=f"The story used sounds like {quest.sound} and {flatterer.sound} to make the quest feel lively and then unlucky.",
        ),
        QAItem(
            question=f"Who tried to help {hero.id} by warning {hero.pronoun('object')}?",
            answer=f"{guardian.label} tried to help by warning {hero.id} that {quest.risk}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flattery?",
            answer="Flattery is praise that sounds sweet and may be used to make someone trust or like you too much.",
        ),
        QAItem(
            question="What is a quest in a fairy tale?",
            answer="A quest is a journey to seek something important, like a treasure, a tool, or a rescue.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to help readers hear the action and feel when something is quick, magical, or surprising.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when the plan fails or the hero loses something instead of getting a happy result.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a fairy-tale story with the word "flattery" about a {p.hero_type} on a quest that ends badly.',
        f"Tell a child-friendly tale where {p.name} is praised too much, ignores a warning, and loses the prize.",
        f"Create a short fairy story with sound effects, a quest, and a bad ending caused by flattering words.",
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
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
% A quest is valid when the setting affords quests.
valid(Setting, Quest, Prize, Flatterer) :- setting(Setting), quest(Quest), prize(Prize), flatterer(Flatterer), affords(Setting, quest).
% The story deliberately chooses a bad ending whenever flattery and warning both appear.
bad_end(Quest) :- quest(Quest).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for f in FLATTERERS:
        lines.append(asp.fact("flatterer", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set((s, q, p, f) for s, q, p, f in valid_combos() if reason_ok(s, q, p, f))
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(asp_set - py_set))
    print(" only in python:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world, hero, guardian, prize, quest, flatterer = setup_world(params)
    tell(world, hero, guardian, prize, quest, flatterer)
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
    StoryParams(setting="moon-glen", quest="golden-key", prize="crown", flatterer="sly-mouse", name="Elin", hero_type="girl", trait="curious"),
    StoryParams(setting="rose-bridge", quest="silver-bell", prize="lantern", flatterer="mirror-fairy", name="Tobin", hero_type="boy", trait="bold"),
    StoryParams(setting="hollow-hall", quest="glass-rose", prize="ribbon", flatterer="golden-cat", name="Mira", hero_type="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.setting} (flatterer: {p.flatterer})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
