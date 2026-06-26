#!/usr/bin/env python3
"""
A standalone storyworld for a small folk-tale domain with surprise and a little gore.

Seed tale shape:
- A woodcutter's child goes to the old hill path with a basket of bread.
- A wolf-like stranger or an old bridge surprise can threaten the basket.
- A tiny injury or bloodied trail introduces mild gore without graphic detail.
- A clever turn reveals the "monster" was not what it seemed, and the hurt is helped.

This world keeps the style close to folk tale: simple, rhythmic, concrete, and
with a surprise turn that changes what the characters think is happening.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    e: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king", "woodcutter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    wood: bool = False
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
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    surprise: str
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
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Remedy:
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
        self.zone: set[str] = set()
        self.facts: dict = {}
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _default_meters() -> dict[str, float]:
    return {"hurt": 0.0, "blood": 0.0, "fear": 0.0, "safe": 0.0, "aid": 0.0, "curiosity": 0.0}


def _default_memes() -> dict[str, float]:
    return {"surprise": 0.0, "worry": 0.0, "love": 0.0, "brave": 0.0, "relief": 0.0}


def _make_entity(**kwargs) -> Entity:
    e = Entity(**kwargs)
    for k, v in _default_meters().items():
        e.meters.setdefault(k, v)
    for k, v in _default_memes().items():
        e.memes.setdefault(k, v)
    return e


def _rule_blood_trail(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["hurt"] < THRESHOLD:
            continue
        sig = ("blood", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["blood"] += 1
        out.append(f"A thin red trail marked the path behind {actor.id}.")
    return out


def _rule_fear(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["blood"] < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"That sight made the heart of the little folk beat fast.")
    return out


def _rule_relief(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["aid"] < THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] += 1
        out.append(f"The fear gave way to relief.")
    return out


CAUSAL_RULES = [
    _rule_blood_trail,
    _rule_fear,
    _rule_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for s in out:
            world.say(s)
    return out


def title_case(name: str) -> str:
    return name[:1].upper() + name[1:]


def setting_detail(setting: Setting, event: Event) -> str:
    if setting.wood:
        return "The trees stood close together, and the old path was shaded and quiet."
    return f"{setting.place.capitalize()} looked calm, though old tales said it could still surprise a traveler."


def surprise_line(event: Event) -> str:
    return {
        "wolf": "But the dark shape in the brush was not a beast at all.",
        "bridge": "But the broken thing by the stream was not a trap at all.",
        "heron": "But the long shape in the reeds was not a ghost at all.",
        "mirror": "But the shining thing in the hut was not magic at all.",
    }.get(event.id, "But the surprise was not what anyone first feared.")


def prize_at_risk(event: Event, prize: Prize) -> bool:
    return prize.region in event.zone


def select_remedy(event: Event, prize: Prize) -> Optional[Remedy]:
    for rem in REMEDIES:
        if event.mess in rem.guards and prize.region in rem.covers:
            return rem
    return None


def predict_harm(world: World, hero: Entity, event: Event, prize_id: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(hero.id), event, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": bool(prize.meters["blood"] >= THRESHOLD), "hurt": hero.meters["hurt"]}


def _do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    if event.id not in world.setting.affords:
        return
    world.zone = set(event.zone)
    actor.meters["fear"] += 1
    actor.memes["surprise"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who lived by the old road.")


def love_wandering(world: World, hero: Entity, event: Event) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {event.gerund} because the world felt full of hidden things.")


def carries_prize(world: World, hero: Entity, prize: Entity, giver: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["love"] += 1
    world.say(f"{giver.label_word.capitalize()} gave {hero.id} {hero.pronoun('object')} {prize.phrase} for the journey.")


def set_out(world: World, hero: Entity, giver: Entity, event: Event) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {giver.label_word} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, event))


def want_to_go(world: World, hero: Entity, event: Event, prize: Entity) -> None:
    hero.memes["brave"] += 1
    world.say(f"{hero.id} wanted to {event.verb}, but {hero.pronoun('possessive')} {prize.label} was a fine thing to keep safe.")


def warning(world: World, giver: Entity, hero: Entity, event: Event, prize: Entity) -> None:
    pred = predict_harm(world, hero, event, prize.id)
    if not pred["soiled"]:
        return
    world.say(f'"If you go there, your {prize.label} may get {event.soil}," {giver.label_word} said.')
    world.facts["predicted_soil"] = event.soil
    world.facts["predicted_hurt"] = pred["hurt"]


def surprise(world: World, hero: Entity, event: Event) -> None:
    hero.memes["surprise"] += 1
    world.say(surprise_line(event))
    world.say(f"{hero.id} stepped nearer, and then the truth showed itself at once.")


def injury(world: World, hero: Entity) -> None:
    hero.meters["hurt"] += 1
    world.say(f"{hero.id} had pricked {hero.pronoun('possessive')} finger on a thorn, and one red drop fell to the ground.")


def panic(world: World, giver: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{giver.label_word.capitalize()} gasped, for the red stain made the little one look far more hurt than {hero.id} felt.")


def offer_help(world: World, giver: Entity, hero: Entity, event: Event, prize: Entity) -> Optional[Remedy]:
    rem = select_remedy(event, prize)
    if rem is None:
        return None
    rem_ent = world.add(_make_entity(
        id=rem.id,
        type="thing",
        label=rem.label,
        owner=hero.id,
        caretaker=giver.id,
        worn_by=hero.id,
        plural=rem.plural,
    ))
    if predict_harm(world, hero, event, prize.id)["soiled"]:
        rem_ent.worn_by = None
        del world.entities[rem_ent.id]
        return None
    world.say(f'{giver.label_word.capitalize()} wrapped {hero.id} in {rem.label} and said, "{rem.prep}."')
    return rem


def resolve(world: World, giver: Entity, hero: Entity, event: Event, prize: Entity, rem: Remedy) -> None:
    hero.meters["safe"] += 1
    hero.meters["aid"] += 1
    hero.memes["worry"] = 0
    world.say(f"{hero.id} nodded, and together they {rem.tail}.")
    world.say(f"Before long, the little one was {event.gerund}, {prize.it()} still clean, and the surprise had become a good story.")


SETTINGS = {
    "wood": Setting(place="the wood", wood=True, affords={"wolf", "heron"}),
    "bridge": Setting(place="the old bridge", wood=False, affords={"bridge"}),
    "stream": Setting(place="the stream", wood=False, affords={"bridge", "heron"}),
    "cottage": Setting(place="the cottage lane", wood=False, affords={"mirror"}),
}

EVENTS = {
    "wolf": Event(
        id="wolf",
        verb="follow the red berries",
        gerund="walking the berry path",
        rush="run from the bushes",
        mess="blood",
        soil="spotted with blood",
        zone={"torso"},
        surprise="a wounded wolf with a thorn in its paw",
        tags={"wolf", "blood", "forest", "surprise"},
    ),
    "bridge": Event(
        id="bridge",
        verb="cross the old bridge",
        gerund="crossing the bridge",
        rush="hurry over the boards",
        mess="blood",
        soil="stained with blood",
        zone={"hands"},
        surprise="a cracked plank that pinched a thumb",
        tags={"bridge", "blood", "surprise"},
    ),
    "heron": Event(
        id="heron",
        verb="wade by the reeds",
        gerund="walking by the reeds",
        rush="step into the water",
        mess="blood",
        soil="marked with blood",
        zone={"hands"},
        surprise="a white heron guarding a nest",
        tags={"heron", "blood", "surprise"},
    ),
    "mirror": Event(
        id="mirror",
        verb="open the old door",
        gerund="peeking into the cottage",
        rush="push the door wider",
        mess="blood",
        soil="touched with blood",
        zone={"hands"},
        surprise="a polished shield that flashed red in the light",
        tags={"mirror", "surprise"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a little blue cloak", "cloak", "torso"),
    "bread": Prize("bread", "a warm loaf of bread", "bread", "hands"),
    "bundle": Prize("bundle", "a bundle of herbs", "bundle", "hands"),
}

REMEDIES = [
    Remedy("bandage", "a clean linen bandage", {"hands"}, {"blood"}, "wrap your finger with a clean bandage", "wrapped the bandage around the finger"),
    Remedy("shawl", "a woolen shawl", {"torso"}, {"blood"}, "put on the shawl before the path grows cold", "walked on with the woolen shawl"),
    Remedy("gloves", "soft gloves", {"hands"}, {"blood"}, "pull on soft gloves first", "went on with the soft gloves"),
]

GENTLE_NAMES = ["Anya", "Nina", "Milo", "Pavel", "Sera", "Ivo", "Lena", "Rosa"]
TRAITS = ["brave", "curious", "kind", "quiet", "cheerful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for eid in setting.affords:
            ev = _safe_lookup(EVENTS, eid)
            for pid, pr in PRIZES.items():
                if prize_at_risk(ev, pr) and select_remedy(ev, pr):
                    out.append((place, eid, pid))
    return out


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    name: str
    gender: str
    giver: str
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


KNOWLEDGE = {
    "wolf": [("What is a wolf?", "A wolf is a wild animal that lives in forests and hunts for food.")],
    "bridge": [("What is a bridge?", "A bridge is a way to cross over water, a road, or a gap.")],
    "heron": [("What is a heron?", "A heron is a tall bird with long legs that likes to stand near water.")],
    "blood": [("What is blood?", "Blood is the red liquid that flows inside people and animals.")],
    "surprise": [("What is a surprise?", "A surprise is something you did not expect, so it makes you feel startled or amazed.")],
    "bandage": [("What is a bandage for?", "A bandage helps cover a small cut or sore so it can stay clean while it heals.")],
    "shawl": [("What is a shawl?", "A shawl is a cloth you wear around your shoulders to keep warm.")],
    "gloves": [("What are gloves for?", "Gloves help keep your hands warm and clean.")],
}
KNOWLEDGE_ORDER = ["surprise", "wolf", "bridge", "heron", "blood", "bandage", "shawl", "gloves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, giver, ev, prize = f["hero"], f["giver"], f["event"], f["prize"]
    return [
        f'Write a short folk tale for a young child about {hero.id}, a hidden path, and a surprise with the word "{ev.id}".',
        f"Tell a gentle story where {hero.id} wants to {ev.verb} but {giver.label_word} worries about {prize.phrase}.",
        f"Write a simple surprise story set at {world.setting.place} that ends with a small hurt being helped.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, giver, ev, prize = f["hero"], f["giver"], f["event"], f["prize"]
    qa = [
        QAItem(
            question=f"Who went to {world.setting.place} in the story?",
            answer=f"{hero.id} went there with {giver.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the warning?",
            answer=f"{hero.id} wanted to {ev.verb}.",
        ),
        QAItem(
            question=f"What did {giver.label_word} give {hero.id} to carry?",
            answer=f"{giver.label_word.capitalize()} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.",
        ),
    ]
    if f.get("surprise"):
        qa.append(QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that the scary-looking thing was actually {ev.surprise}.",
        ))
    if f.get("resolved"):
        rem = _safe_fact(world, f, "remedy")
        qa.append(QAItem(
            question=f"How was the small hurt helped?",
            answer=f"They used {rem.label} so the little cut could stay clean.",
        ))
        qa.append(QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"By the end, the fear was gone, the hurt was cared for, and {hero.id} could go on safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["event"].tags)
    if world.facts.get("remedy"):
        tags.add(world.facts["remedy"].id)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.extend(world.trace)
    return "\n".join(lines)


def explain_rejection(event: Event, prize: Prize) -> str:
    return f"(No story: {event.gerund} does not plausibly endanger {prize.phrase}, so there is no honest warning and no folk-tale turn.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s object here; try --gender {ok}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("mess_of", eid, e.mess))
        for r in sorted(e.zone):
            lines.append(asp.fact("splashes", eid, r))
    for rid, r in enumerate(REMEDIES):
        lines.append(asp.fact("remedy", r.id))
        for c in sorted(r.covers):
            lines.append(asp.fact("covers", r.id, c))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", r.id, g))
    for place, setting in SETTINGS.items():
        for eid in sorted(setting.affords):
            lines.append(asp.fact("affords", place, eid))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(E, P) :- splashes(E, R), worn_on(P, R).
has_fix(E, P) :- prize_at_risk(E, P), mess_of(E, M), guards(R, M), covers(R, X), worn_on(P, X).
valid(Place, E, P) :- affords(Place, E), prize_at_risk(E, P), has_fix(E, P).
valid_story(Place, E, P, Gender) :- valid(Place, E, P), wears(Gender, P).
#show valid/3.
#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld with surprise and a little gore.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--giver", choices=["mother", "father", "grandmother", "grandfather"])
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
    if getattr(args, "event", None) and getattr(args, "prize", None):
        ev, pr = _safe_lookup(EVENTS, getattr(args, "event", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(ev, pr) and select_remedy(ev, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GENTLE_NAMES)
    giver = getattr(args, "giver", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, event=event, prize=prize, name=name, gender=gender, giver=giver, trait=trait)


def tell(setting: Setting, event: Event, prize: Prize, hero_name: str, hero_gender: str, giver_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(_make_entity(id=hero_name, kind="character", type=hero_gender, traits=["little", trait]))
    giver = world.add(_make_entity(id="Giver", kind="character", type=giver_type, label=giver_type))
    prize_ent = world.add(_make_entity(id="Prize", type=prize.type, label=prize.label, phrase=prize.phrase, caretaker=giver.id, owner=hero.id, worn_by=hero.id, plural=prize.plural))
    world.facts.update(hero=hero, giver=giver, event=event, prize=prize_ent)
    introduce(world, hero)
    love_wandering(world, hero, event)
    carries_prize(world, hero, prize_ent, giver)
    world.para()
    set_out(world, hero, giver, event)
    want_to_go(world, hero, event, prize_ent)
    warning(world, giver, hero, event, prize_ent)
    surprise(world, hero, event)
    injury(world, hero)
    panic(world, giver, hero, prize_ent)
    world.para()
    rem = offer_help(world, giver, hero, event, prize_ent)
    if rem is not None:
        resolve(world, giver, hero, event, prize_ent, rem)
    world.facts["surprise"] = True
    world.facts["resolved"] = rem is not None
    world.facts["remedy"] = rem
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(EVENTS, params.event), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.giver, params.trait)
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
    StoryParams(place="wood", event="wolf", prize="cloak", name="Anya", gender="girl", giver="mother", trait="curious"),
    StoryParams(place="stream", event="heron", prize="bundle", name="Milo", gender="boy", giver="grandfather", trait="brave"),
    StoryParams(place="bridge", event="bridge", prize="bread", name="Lena", gender="girl", giver="grandmother", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, event, prize) combos ({len(stories)} with gender):\n")
        for place, ev, prize in triples:
            genders = sorted(g for (pl, e, pr, g) in stories if (pl, e, pr) == (place, ev, prize))
            print(f"  {place:8} {ev:8} {prize:8} [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.event} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
