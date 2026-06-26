#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gloom_comfy_restriction_bad_ending_surprise_foreshadowing.py
==================================================================================================

A tiny comedy-leaning storyworld about a gloomy day, a cozy plan, and a
restriction that makes things go sideways. The world is deliberately small:
characters want comfort, a rule gets in the way, a surprise arrives, and the
ending lands in a mildly bad-but-funny place.

Seed premise:
- gloom
- comfy
- restriction

Narrative instruments:
- Foreshadowing
- Surprise
- Bad Ending

The story engine simulates a live world model with physical meters and emotional
memes, then renders a child-facing tale from the resulting state.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    comfort: object | None = None
    hero: object | None = None
    parent: object | None = None
    restriction: object | None = None
    surprise: object | None = None
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
class Setting:
    place: str
    indoors: bool
    gloomy: bool
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
class Comfort:
    id: str
    label: str
    phrase: str
    kind: str
    zone: str
    cozy_gain: str
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
class Restriction:
    id: str
    label: str
    rule: str
    consequence: str
    blocks: set[str] = field(default_factory=set)
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


@dataclass
class Surprise:
    id: str
    label: str
    event: str
    effect: str
    comedic_tag: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    comfort: str
    restriction: str
    surprise: str
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "living_room": Setting(place="the living room", indoors=True, gloomy=True, affords={"nest", "tea", "reading"}),
    "den": Setting(place="the den", indoors=True, gloomy=True, affords={"nest", "tea", "reading"}),
    "porch": Setting(place="the porch", indoors=False, gloomy=True, affords={"tea", "reading"}),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket", label="blanket nest", phrase="a very soft blanket nest",
        kind="nest", zone="floor", cozy_gain="made the floor feel like a cloud", fragile=False
    ),
    "cocoa": Comfort(
        id="cocoa", label="mug of cocoa", phrase="a mug of cocoa with tiny marshmallows",
        kind="tea", zone="table", cozy_gain="warmed little hands right up", fragile=True
    ),
    "book": Comfort(
        id="book", label="picture book", phrase="a picture book with bright animals",
        kind="reading", zone="lap", cozy_gain="made the gloom feel smaller", fragile=False
    ),
}

RESTRICTIONS = {
    "no_shoes": Restriction(
        id="no_shoes", label="the no-shoes rule", rule="keep shoes off the rug",
        consequence="the rug stays clean", blocks={"stomp", "jump"}
    ),
    "no_snacks": Restriction(
        id="no_snacks", label="the no-snacks rule", rule="keep snacks away from the couch",
        consequence="the couch stays crumb-free", blocks={"munch", "spill"}
    ),
    "quiet": Restriction(
        id="quiet", label="the quiet rule", rule="keep voices low after dinner",
        consequence="the house stays calm", blocks={"shout", "sing"}
    ),
}

SURPRISES = {
    "cat": Surprise(
        id="cat", label="the cat", event="a cat hopped onto the blanket pile",
        effect="the blanket pile wobbled like a sleepy tower",
        comedic_tag="cat hair"
    ),
    "spring": Surprise(
        id="spring", label="the couch spring", event="a squeaky couch spring popped loose",
        effect="the cushion gave a loud boing",
        comedic_tag="boing"
    ),
    "tray": Surprise(
        id="tray", label="the snack tray", event="the snack tray slid off the armrest",
        effect="the marshmallows skittered everywhere",
        comedic_tag="marshmallow"
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ruby", "Ivy", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Max", "Eli"]
TRAITS = ["cheerful", "curious", "silly", "gentle", "bouncy", "bright"]


class StoryWorld:
    def __init__(self, world: World, hero: Entity, parent: Entity, comfort: Entity,
                 restriction: Entity, surprise: Entity) -> None:
        self.world = world
        self.hero = hero
        self.parent = parent
        self.comfort = comfort
        self.restriction = restriction
        self.surprise = surprise


def _apply_mood(world: World, hero: Entity) -> None:
    hero.memes["gloom"] = 1.0
    hero.memes["desire"] = 1.0
    world.say(f"{hero.id} looked out at the gloomy day and felt like the clouds had moved into the house.")


def _introduce_comfort(world: World, hero: Entity, comfort: Entity) -> None:
    hero.memes["hope"] = 1.0
    world.say(
        f"Then {hero.id} found {hero.pronoun('possessive')} {comfort.label}, "
        f"and it seemed wonderfully comfy."
    )


def _restriction_warning(world: World, parent: Entity, hero: Entity, restriction: Entity, comfort: Entity) -> None:
    hero.memes["curiosity"] = 1.0
    world.say(
        f"But {hero.pronoun('possessive')} {parent.label} pointed at {restriction.label} and said, "
        f'"We have to {restriction.phrase}, {hero.id}. That is the house rule."'
    )
    world.say(f"That way, {restriction.consequence.lower()}.")


def _foreshadow(world: World, surprise: Entity) -> None:
    if surprise.id == "spring":
        world.say("The couch gave one tiny squeak, like it was trying not to laugh.")
    elif surprise.id == "cat":
        world.say("Somewhere nearby, a cat thumped its tail once, as if it had a secret.")
    else:
        world.say("The snack tray sat very still, which was somehow suspicious.")


def _cross_restriction(world: World, hero: Entity, restriction: Entity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1.0
    world.say(
        f"{hero.id} tried to ignore the rule and went to {restriction.blocks and 'reach' or 'reach'} "
        f"for the comfiest spot anyway."
    )


def _trigger_surprise(world: World, surprise: Entity, comfort: Entity, hero: Entity) -> None:
    if surprise.id == "cat":
        comfort.meters["mess"] = comfort.meters.get("mess", 0.0) + 1.0
        hero.memes["startle"] = 1.0
        world.say("Surprise! The cat hopped onto the blanket pile, and the whole thing wobbled like a sleepy tower.")
    elif surprise.id == "spring":
        comfort.meters["broken"] = 1.0
        hero.memes["startle"] = 1.0
        world.say("Surprise! A squeaky couch spring popped loose with a loud boing.")
    else:
        comfort.meters["spilled"] = 1.0
        hero.memes["startle"] = 1.0
        world.say("Surprise! The snack tray slid off the armrest, and the marshmallows skittered everywhere.")


def _bad_ending(world: World, hero: Entity, parent: Entity, comfort: Entity, surprise: Entity) -> None:
    hero.memes["disappointment"] = 1.0
    world.say(
        f"In the end, {hero.id} had a lopsided pile instead of a perfect cozy corner, "
        f"and {hero.pronoun('possessive')} {parent.label} had to sweep up the mess."
    )
    world.say(
        f"The funniest part was that the {surprise.label} stayed stuck in the scene, "
        f"so the house looked even sillier than before."
    )


def tell(setting: Setting, comfort_cfg: Comfort, restriction_cfg: Restriction,
         surprise_cfg: Surprise, hero_name: str, hero_type: str, parent_type: str) -> StoryWorld:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    comfort = world.add(Entity(id=comfort_cfg.id, type=comfort_cfg.kind, label=comfort_cfg.label, phrase=comfort_cfg.phrase))
    restriction = world.add(Entity(id=restriction_cfg.id, type="rule", label=restriction_cfg.label, phrase=restriction_cfg.rule))
    surprise = world.add(Entity(id=surprise_cfg.id, type="surprise", label=surprise_cfg.label, phrase=surprise_cfg.event))

    _apply_mood(world, hero)
    _introduce_comfort(world, hero, comfort)
    world.say(f"{hero.id} wanted to make the room extra comfy, so {hero.id} started gathering cushions and blankets.")
    _restriction_warning(world, parent, hero, restriction, comfort)
    world.para()
    _foreshadow(world, surprise)
    world.say(f"{hero.id} tried to follow the cozy plan, but the rule kept getting in the way.")
    _cross_restriction(world, hero, restriction)
    _trigger_surprise(world, surprise, comfort, hero)
    world.para()
    _bad_ending(world, hero, parent, comfort, surprise)

    world.facts.update(
        hero=hero,
        parent=parent,
        comfort=comfort,
        restriction=restriction,
        surprise=surprise,
        setting=setting,
        comfy=comfort_cfg,
        rule=restriction_cfg,
        surprise_cfg=surprise_cfg,
        ended_bad=True,
    )
    return StoryWorld(world, hero, parent, comfort, restriction, surprise)


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for comfort_id, comfort in COMFORTS.items():
            if comfort.kind not in setting.affords:
                continue
            for restriction_id in RESTRICTIONS:
                for surprise_id in SURPRISES:
                    combos.append((place, comfort_id, restriction_id + ":" + surprise_id))
    return combos


def explain_rejection(place: str, comfort: str, restriction: str) -> str:
    setting = _safe_lookup(SETTINGS, place)
    comf = _safe_lookup(COMFORTS, comfort)
    rule = _safe_lookup(RESTRICTIONS, restriction)
    if comf.kind not in setting.affords:
        return f"(No story: {comf.label} does not fit {setting.place}, so the cozy plan would not make sense there.)"
    if comf.kind in rule.blocks:
        return f"(No story: the {rule.label} blocks this kind of cozy move too directly; the conflict would be too thin.)"
    return "(No story: this combination does not create a clear, child-sized restriction problem.)"


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.world.facts
    hero, parent, comfort, rule, surprise = f["hero"], f["parent"], f["comfort"], f["rule"], f["surprise_cfg"]
    return [
        f'Write a short comedy story for a young child about {hero.id} on a gloomy day, with something very comfy and a house rule in the way.',
        f"Tell a gentle but funny story where {hero.id} wants {comfort.phrase}, but {parent.label} reminds them about {rule.label}, and a surprise makes things worse.",
        f'Write a simple story that uses the word "gloom" and ends with a bad ending that still feels playful and complete.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.world.facts
    hero, parent, comfort, rule, surprise = f["hero"], f["parent"], f["comfort"], f["rule"], f["surprise_cfg"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want on the gloomy day?",
            answer=f"{hero.id} wanted {comfort.phrase} because it seemed very comfy on the gloomy day.",
        ),
        QAItem(
            question=f"What rule did {parent.label} remind {hero.id} about?",
            answer=f"{parent.label} reminded {hero.id} about {rule.label}, which said to {rule.rule}.",
        ),
        QAItem(
            question=f"What surprise happened in the middle of the story?",
            answer=f"{surprise.event.capitalize()}. That surprise made the cozy plan wobble, spill, or break in a funny way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly for the cozy plan: {hero.id} did not get the perfect comfy spot, and the grown-up had to clean up the mess.",
        ),
    ]
    return qa


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does gloomy mean?",
            answer="Gloomy means dark, gray, or sad-looking, like a day when the sky feels sleepy and the light is weak.",
        ),
        QAItem(
            question="What does comfy mean?",
            answer="Comfy means soft, warm, and pleasant, like a blanket nest or a favorite chair that feels nice to sit in.",
        ),
        QAItem(
            question="What is a restriction?",
            answer="A restriction is a rule or limit that says what you should not do, or what you must do first.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens suddenly and changes the plan.",
        ),
    ]


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


def dump_trace(sw: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in sw.world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        if s.gloomy:
            lines.append(asp.fact("gloomy", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("kind_of", cid, c.kind))
        lines.append(asp.fact("zone", cid, c.zone))
    for rid, r in RESTRICTIONS.items():
        lines.append(asp.fact("restriction", rid))
        for b in sorted(r.blocks):
            lines.append(asp.fact("blocks", rid, b))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Comfort, Restriction, Surprise) :-
    setting(Place),
    comfort(Comfort),
    restriction(Restriction),
    surprise(Surprise),
    affords(Place, Kind),
    kind_of(Comfort, Kind),
    not impossible(Place, Comfort, Restriction).

impossible(Place, Comfort, Restriction) :-
    setting(Place),
    comfort(Comfort),
    restriction(Restriction),
    kind_of(Comfort, Kind),
    blocks(Restriction, Kind),
    not affords(Place, Kind).

#show valid/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = sorted((p, c, rs.split(":")[0], rs.split(":")[1]) for p, c, rs in valid_story_combos())
    cl = asp_valid_stories()
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py != cl:
        print("python:", py)
        print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy-leaning gloomy comfy restriction storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--restriction", choices=RESTRICTIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = []
    for place, setting in SETTINGS.items():
        if getattr(args, "place", None) and getattr(args, "place", None) != place:
            continue
        for comfort_id, comfort in COMFORTS.items():
            if getattr(args, "comfort", None) and getattr(args, "comfort", None) != comfort_id:
                continue
            if comfort.kind not in setting.affords:
                continue
            for restriction_id in RESTRICTIONS:
                if getattr(args, "restriction", None) and getattr(args, "restriction", None) != restriction_id:
                    continue
                for surprise_id in SURPRISES:
                    if getattr(args, "surprise", None) and getattr(args, "surprise", None) != surprise_id:
                        continue
                    combos.append((place, comfort_id, restriction_id, surprise_id))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, comfort, restriction, surprise = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, comfort=comfort, restriction=restriction, surprise=surprise, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(COMFORTS, params.comfort),
        _safe_lookup(RESTRICTIONS, params.restriction),
        _safe_lookup(SURPRISES, params.surprise),
        params.name,
        params.gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.world.render(),
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
    StoryParams(place="living_room", comfort="blanket", restriction="no_snacks", surprise="spring", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="den", comfort="book", restriction="quiet", surprise="cat", name="Leo", gender="boy", parent="father"),
    StoryParams(place="living_room", comfort="cocoa", restriction="no_snacks", surprise="tray", name="Nora", gender="girl", parent="mother"),
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
        stories = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.comfort} / {p.restriction} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
