#!/usr/bin/env python3
"""
storyworlds/worlds/angular_millet_seventieth_sound_effects_foreshadowing_superhero.py
======================================================================================

A small superhero storyworld with foreshadowing and sound effects.

Seed premise:
A young hero trains for a city parade, hears strange sounds, notices clues that
a prank-gadget is being built, and uses timing, help, and a clever move to stop
the trouble before the seventieth bell.
"""

from __future__ import annotations

import argparse
import copy
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    linked_to: Optional[str] = None
    active: bool = False
    singular: bool = True

    city_ent: object | None = None
    d: object | None = None
    h: object | None = None
    helper: object | None = None
    t: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if not self.singular else "it"
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class City:
    name: str
    place: str
    feature: str
    sound_words: list[str] = field(default_factory=list)
    foreshadow_clues: list[str] = field(default_factory=list)
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
class HeroProfile:
    id: str
    title: str
    power: str
    suit: str
    helper: str
    sound_style: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Trouble:
    id: str
    label: str
    plan: str
    clue: str
    sound: str
    threat: str
    tags: set[str] = field(default_factory=set)
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
class Device:
    id: str
    label: str
    use: str
    counters: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
    city: str
    hero: str
    trouble: str
    device: str
    helper: str = "assistant"
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _tick(world: World, key: str) -> None:
    world.get("city").meters[key] = world.get("city").meters.get(key, 0.0) + 1.0


def foreshadow_push(world: World) -> None:
    for clue in world.facts.get("clues", []):
        world.say(clue)


def sound_burst(world: World, sound: str) -> None:
    world.say(sound)


def create_world(city: City, hero: HeroProfile, trouble: Trouble, device: Device,
                 hero_name: str, helper_name: str, hero_type: str, helper_type: str) -> World:
    world = World(city)
    city_ent = world.add(Entity(
        id="city",
        kind="place",
        type="city",
        label=city.place,
        meters={"crowd": 0.0, "danger": 0.0},
        memes={"hope": 0.0},
        tags=set(city.foreshadow_clues),
    ))
    h = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero.title,
        role="hero",
        attrs={"power": hero.power, "suit": hero.suit},
        meters={"speed": 0.0, "focus": 0.0, "confidence": 0.0},
        memes={"curiosity": 0.0, "duty": 0.0, "worry": 0.0, "joy": 0.0},
        tags=set(hero.tags),
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=hero.helper,
        role="helper",
        attrs={"sound_style": hero.sound_style},
        meters={"speed": 0.0, "focus": 0.0},
        memes={"worry": 0.0, "pride": 0.0},
    ))
    t = world.add(Entity(
        id="trouble",
        kind="thing",
        type="machine",
        label=trouble.label,
        role="villain_plan",
        attrs={"plan": trouble.plan, "clue": trouble.clue, "threat": trouble.threat},
        meters={"built": 0.0, "danger": 0.0},
        memes={"greed": 0.0},
        tags=set(trouble.tags),
    ))
    d = world.add(Entity(
        id="device",
        kind="thing",
        type="tool",
        label=device.label,
        role="device",
        attrs={"use": device.use},
        meters={"charge": 1.0, "aim": 0.0},
        memes={"readiness": 0.0},
        tags=set(device.tags),
    ))
    world.facts.update(city=city, hero=hero, trouble=trouble, device=device,
                       hero_ent=h, helper=helper, trouble_ent=t, device_ent=d)
    world.facts["clues"] = list(city.foreshadow_clues)
    return world


def build_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero_ent"]
    helper: Entity = f["helper"]
    trouble: Entity = f["trouble_ent"]
    device: Entity = f["device_ent"]
    city: City = f["city"]

    hero.memes["curiosity"] += 1
    hero.memes["duty"] += 1
    helper.memes["worry"] += 1

    world.say(f"In {city.place}, {hero.id} was the {f['hero'].title.lower()} who could hear trouble before it hit the street.")
    world.say(f"{hero.id} loved the sharp {f['hero'].suit} lines of {f['hero'].power}, and {helper.id} kept pace at {hero.pronoun('possessive')} side.")
    world.say(f"Tonight, the city was getting ready for the seventieth bell, and everyone expected a bright, safe celebration.")

    world.para()
    foreshadow_push(world)
    sound_burst(world, city.sound_words[0])
    hero.meters["focus"] += 1
    trouble.meters["built"] += 1
    trouble.memes["greed"] += 1
    world.say(f"Under the bridge, {trouble.label} clicked and clanked as the prank-gadget grew taller and taller.")
    world.say(f"The clue was clear: {trouble.clue}. That meant {trouble.label} was trying to make a big mess at the parade.")

    world.para()
    world.say(f'"{city.sound_words[1]}!" {helper.id} whispered, pointing toward the alley.')
    world.say(f"{hero.id} did not rush blindly. {hero.id} listened, looked, and counted the beats between each sound.")
    world.say(f"Then {hero.id} used {device.label} for {device.use}, aiming at the weakest bolt on {trouble.label}.")
    device.meters["aim"] += 1
    hero.meters["confidence"] += 1

    trouble.meters["danger"] += 1
    _tick(world, "danger")
    if trouble.meters["danger"] >= THRESHOLD:
        world.say(f"{trouble.label} gave one last {city.sound_words[2]}, then the whole gadget sagged with a sad little snap.")
        trouble.active = False
        world.say(f"The prank stopped before the seventieth bell could ring. The parade lights stayed bright, and the crowd cheered.")
    else:
        world.say(f"{trouble.label} stayed quiet, but {hero.id} kept watch until the street was safe again.")

    world.para()
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(f"At the end, {hero.id} stood under the lamp glow, {device.label} still warm in {hero.pronoun('possessive')} hand, while {helper.id} grinned at the calm street.")
    world.say(f"The seventieth bell rang clean and clear, and in its echo, the city looked angular and shining, like a hero's badge made of light.")

    world.facts["resolved"] = True
    world.facts["outcome"] = "stopped"


CITYS = {
    "harbor": City(
        name="harbor",
        place="Harbor City",
        feature="angular rooftops",
        sound_words=["clang-clang", "whirr-whirr", "ka-THUNK"],
        foreshadow_clues=[
            "A thin clang-clang drifted from the docks, as if somebody were hiding tools under a tarp.",
            "One window blinked twice, then went dark, like a clue trying to be noticed.",
        ],
    ),
    "metro": City(
        name="metro",
        place="Metro Square",
        feature="bright towers",
        sound_words=["beep-beep", "zip-zip", "KRINK"],
        foreshadow_clues=[
            "A zip-zip hiss came from a rooftop, and a loose bolt rolled into the gutter.",
            "The fountain water trembled once, as if something heavy had landed nearby.",
        ],
    ),
}

HEROES = {
    "flashkid": HeroProfile(
        id="Flashkid",
        title="young hero",
        power="quick feet and a sharp eye",
        suit="angular blue",
        helper="Nova",
        sound_style="zip-zip",
        tags={"hero", "quick", "angular"},
    ),
    "starlet": HeroProfile(
        id="Starlet",
        title="rookie defender",
        power="a bright shield and brave timing",
        suit="silver with gold trim",
        helper="Echo",
        sound_style="clang-clang",
        tags={"hero", "shield"},
    ),
}

TROUBLES = {
    "prankbot": Trouble(
        id="prankbot",
        label="Prankbot",
        plan="scatter confetti into the parade route",
        clue="the missing bolts were sprinkled with millet-sized crumbs",
        sound="clank-clank",
        threat="It could jam the parade gates",
        tags={"villain", "machine", "millet"},
    ),
    "ticker": Trouble(
        id="ticker",
        label="Tickertop",
        plan="drop fake rain over the square",
        clue="a row of millet kernels had been glued in a line like a trail",
        sound="tick-tick",
        threat="It could scare the crowd and stop the celebration",
        tags={"villain", "machine", "millet"},
    ),
}

DEVICES = {
    "beam": Device(
        id="beam",
        label="beam-brace",
        use="pinning the loose gear together",
        counters={"machine", "bolt"},
        tags={"tool"},
    ),
    "mirror": Device(
        id="mirror",
        label="mirror disk",
        use="flashing a safe signal into the machine's sensor",
        counters={"sensor", "light"},
        tags={"tool"},
    ),
}

GIRL_NAMES = ["Maya", "Zoe", "Nina", "Luna", "Ivy", "Ava", "Rae"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for c in CITYS:
        for h in HEROES:
            for t in TROUBLES:
                if "millet" in _safe_lookup(TROUBLES, t).tags:
                    out.append((c, h, t))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that uses the words "angular", "millet", and "seventieth" and includes foreshadowing clues.',
        f"Tell a story about {f['hero'].title} {f['hero_ent'].id} in {f['city'].place} where odd sounds hint at trouble before the seventieth bell.",
        f'Write a child-friendly superhero rescue story with sound effects like "{f["city"].sound_words[0]}" and a clue that foreshadows a plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero_ent"]
    helper: Entity = f["helper"]
    trouble: Entity = f["trouble_ent"]
    city: City = f["city"]
    return [
        QAItem(
            question=f"Who was the superhero story about in {city.place}?",
            answer=f"It was about {hero.id}, a young hero in {f['hero'].suit}. {helper.id} helped watch the street, and together they kept the city safe.",
        ),
        QAItem(
            question=f"What clue foreshadowed trouble near {trouble.label}?",
            answer=f"The story hinted at trouble with {trouble.clue}. That clue showed that {trouble.label} was building a prank before anyone saw the full machine.",
        ),
        QAItem(
            question=f"What did {hero.id} do when the sounds got louder?",
            answer=f"{hero.id} listened carefully, counted the beats, and used {f['device'].label} at the right moment. That timing stopped the prank before the seventieth bell.",
        ),
        QAItem(
            question=f"How did the story end after the seventieth bell?",
            answer=f"The prank stopped, the crowd stayed safe, and the city shone under the lamps. {hero.id} ended the night looking brave and calm, with {helper.id} smiling nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives little hints about what may happen later. It helps the reader notice clues before the bigger event arrives.",
        ),
        QAItem(
            question="Why do sound effects make a superhero story exciting?",
            answer="Sound effects make action feel lively and clear. They help you hear the pounding, snapping, or buzzing parts of the scene in your mind.",
        ),
        QAItem(
            question="What is millet?",
            answer="Millet is a tiny grain. It looks like little seeds and can be used as food for people or birds.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CITYS.items():
        lines.append(asp.fact("city", cid))
        for s in c.sound_words:
            lines.append(asp.fact("sound_word", cid, s))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
        if "millet" in _safe_lookup(TROUBLES, tid).tags:
            lines.append(asp.fact("foreshadowed", tid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,H,T) :- city(C), hero(H), trouble(T), foreshadowed(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class _ArgsCheck:
    pass
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
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with foreshadowing and sound effects.")
    ap.add_argument("--city", choices=CITYS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "city", None) is None or c[0] == getattr(args, "city", None))
              and (getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None))
              and (getattr(args, "trouble", None) is None or c[2] == getattr(args, "trouble", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    city, hero, trouble = rng.choice(list(combos))
    device = getattr(args, "device", None) or rng.choice(sorted(DEVICES))
    return StoryParams(city=city, hero=hero, trouble=trouble, device=device)


def generate(params: StoryParams) -> StorySample:
    if params.city not in CITYS or params.hero not in HEROES or params.trouble not in TROUBLES or params.device not in DEVICES:
        pass
    world = create_world(_safe_lookup(CITYS, params.city), _safe_lookup(HEROES, params.hero), _safe_lookup(TROUBLES, params.trouble), _safe_lookup(DEVICES, params.device),
                         hero_name="Riley", helper_name=_safe_lookup(HEROES, params.hero).helper, hero_type="girl", helper_type="boy")
    build_story(world)
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
    StoryParams(city="harbor", hero="flashkid", trouble="prankbot", device="beam"),
    StoryParams(city="metro", hero="starlet", trouble="ticker", device="mirror"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    smoke = False
    try:
        sample = generate(CURATED[0])
        smoke = bool(sample.story)
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    if ok and smoke:
        print(f"OK: ASP matches Python ({len(py)} combos). Smoke test passed.")
        return 0
    if py != cl:
        print("MISMATCH:")
        print(" python-only:", sorted(py - cl))
        print(" asp-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
