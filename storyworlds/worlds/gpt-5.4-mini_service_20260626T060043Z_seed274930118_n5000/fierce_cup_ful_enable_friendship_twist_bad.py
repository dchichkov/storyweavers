#!/usr/bin/env python3
"""
storyworlds/worlds/fierce_cup_ful_enable_friendship_twist_bad.py
===============================================================

A small mythic story world about friendship, a cup-ful gift, a fierce trial,
and a twist that ends badly.

The seed image behind this world:
- Two companions meet at a sacred spring.
- One carries a cup-ful of bright water that can enable a holy crossing.
- A fierce guardian tests them.
- A twist turns the gift into a loss.
- The ending is tragic, but complete, and the friendship changes forever.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- shared QA containers imported from storyworlds/results.py
- lazy ASP import through storyworlds/asp.py
- typed entities with meters and memes
- inline ASP twin and Python reasonableness gate
- generate/emit/main plus parser support for default run, -n, --all, --seed,
  --trace, --qa, --json, --asp, --verify, and --show-asp
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    sacred: bool = False
    cup: object | None = None
    friend: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
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
class Rite:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    twist: str
    keyword: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    sacred: bool = False
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _has(world: World, actor: Entity, key: str) -> bool:
    return actor.memes.get(key, 0.0) >= THRESHOLD


def _rise(memes: dict[str, float], key: str, amt: float = 1.0) -> None:
    memes[key] = memes.get(key, 0.0) + amt


def _set(memes: dict[str, float], key: str, value: float) -> None:
    memes[key] = value


def _narrate_chars(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return " and ".join(names)


def _do_rite(world: World, actor: Entity, rite: Rite, narrate: bool = True) -> None:
    actor.meters["use"] = actor.meters.get("use", 0.0) + 1
    _rise(actor.memes, "hope")
    _rise(actor.meters, rite.id)  # type: ignore[arg-type]
    if narrate:
        world.say(f"{actor.id} began the {rite.gerund}.")


def _twist_fires(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    friend = world.get("Friend")
    cup = world.get("Cup")
    rite: Rite = _safe_fact(world, world.facts, "rite")

    if hero.meters.get("rite", 0.0) >= THRESHOLD and cup.meters.get("held", 0.0) >= THRESHOLD:
        sig = ("twist",)
        if sig not in world.fired:
            world.fired.add(sig)
            _rise(hero.memes, "shock")
            _rise(friend.memes, "fear")
            _rise(hero.meters, "omen")
            out.append(
                f"Then came the twist: the cup-ful light was not a blessing alone, "
                f"but a wake-up call for the fierce one beneath the stone."
            )
            out.append(
                f"The water flashed, the shrine answered, and the rite moved from hope to peril."
            )
    return out


def _break_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    friend = world.get("Friend")
    cup = world.get("Cup")
    if hero.memes.get("shock", 0.0) < THRESHOLD:
        return out
    if friend.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("break",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _rise(hero.memes, "hurt")
    _rise(friend.memes, "guilt")
    _set(hero.memes, "trust", max(0.0, hero.memes.get("trust", 0.0) - 2.0))
    _set(friend.memes, "trust", max(0.0, friend.memes.get("trust", 0.0) - 2.0))
    cup.meters["broken"] = cup.meters.get("broken", 0.0) + 1
    out.append("The cup struck the altar and split like thin ice.")
    out.append("Their friendship did not vanish at once, but it cracked, and neither could mend it in that hour.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_twist_fires, _break_friendship):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    rite: str
    cup: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None
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
    "shrine": Setting(place="the old shrine", mood="silent", affords={"ritual"}),
    "spring": Setting(place="the moon spring", mood="bright", affords={"ritual"}),
    "grove": Setting(place="the sacred grove", mood="green", affords={"ritual"}),
}

RITES = {
    "ritual": Rite(
        id="ritual",
        verb="wake the sleeping gate",
        gerund="waking the sleeping gate",
        rush="hurry to the stone door",
        danger="fierce",
        twist="the gate answers back",
        keyword="enable",
        tags={"friendship", "twist", "bad", "myth", "fierce", "cup-ful", "enable"},
    ),
}

CUPS = {
    "goldcup": Vessel(
        id="Cup",
        label="gold cup",
        phrase="a cup-ful of bright water",
        region="hand",
        sacred=True,
    ),
    "shellcup": Vessel(
        id="Cup",
        label="shell cup",
        phrase="a cup-ful of silver water",
        region="hand",
        sacred=True,
    ),
}

HERO_NAMES = ["Aster", "Mira", "Nox", "Iris", "Leto"]
FRIEND_NAMES = ["Cai", "Rhea", "Dorian", "Sela", "Orin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic friendship story world with a fierce twist and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--cup", choices=CUPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "priestess", "priest"])
    ap.add_argument("--friend-type", choices=["girl", "boy", "priestess", "priest"])
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


def reasonableness_gate(place: str, rite: str, cup: str) -> bool:
    return place in SETTINGS and rite in RITES and cup in CUPS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    rite = getattr(args, "rite", None) or rng.choice(list(RITES))
    cup = getattr(args, "cup", None) or rng.choice(list(CUPS))
    if not reasonableness_gate(place, rite, cup):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy", "priestess"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["boy", "girl", "priest"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        rite=rite,
        cup=cup,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_type=hero_type,
        friend_type=friend_type,
    )


def tell(setting: Setting, rite: Rite, cup_cfg: Vessel, hero_name: str, friend_name: str,
         hero_type: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label=friend_name))
    cup = world.add(Entity(id="Cup", type="cup", label=cup_cfg.label, phrase=cup_cfg.phrase, sacred=True))
    world.facts["rite"] = rite
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["cup"] = cup
    world.facts["setting"] = setting

    hero.memes["trust"] = 2.0
    friend.memes["trust"] = 2.0
    hero.memes["hope"] = 1.0
    friend.memes["hope"] = 1.0

    world.say(f"In {setting.place}, {hero_name} and {friend_name} walked together as friends under a quiet sky.")
    world.say(f"They had heard of a fierce guardian below the stones, and yet they came with steady feet.")
    world.say(f"{friend_name} held up {cup_cfg.phrase}, a small thing meant to enable the rite.")
    world.para()
    world.say(f"{hero_name} wanted to {rite.verb}, because the old songs said the gate kept the land safe.")
    world.say(f"{hero_name} reached for courage, while {friend_name} watched the shrine and listened for any fierce sound.")
    cup.meters["held"] = 1.0
    _do_rite(world, hero, rite, narrate=False)
    world.say(f"The cup-ful glow lit the mossy steps, and for one breath the friends thought the path was open.")
    world.para()
    propagate(world, narrate=True)
    world.para()
    if hero.memes.get("hurt", 0.0) >= THRESHOLD:
        world.say(f"By dawn, {hero_name} stood apart from {friend_name}, and the shrine kept its silence.")
        world.say(f"The gate remained shut, the cup lay broken, and their friendship became a sad tale told by the reeds.")
    else:
        world.say("But the night still felt heavy, and the old place remembered what had been lost.")
    return world


KNOWLEDGE = {
    "friendship": [
        ("What is friendship?", "Friendship is a bond between people who care for each other, help each other, and want good things for one another."),
    ],
    "cup-ful": [
        ("What does cup-ful mean?", "Cup-ful means the amount that fits in one cup."),
    ],
    "fierce": [
        ("What does fierce mean?", "Fierce means very strong, wild, or intense."),
    ],
    "myth": [
        ("What is a myth?", "A myth is an old story about gods, heroes, or magical events that explains something important or teaches a lesson."),
    ],
    "twist": [
        ("What is a twist in a story?", "A twist is a surprise change that makes the story go in a new direction."),
    ],
    "bad": [
        ("What is a bad ending?", "A bad ending is when the story finishes with loss, sadness, or trouble instead of a happy fix."),
    ],
    "enable": [
        ("What does enable mean?", "Enable means to make something possible or easier to do."),
    ],
}

KNOWLEDGE_ORDER = ["myth", "friendship", "fierce", "cup-ful", "enable", "twist", "bad"]


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "setting").place
    r = _safe_fact(world, world.facts, "rite")
    return [
        f"Write a short myth about friendship at {p} that includes a fierce test and a cup-ful gift.",
        f"Tell a mythic story where friends bring a cup-ful of water to enable the rite of {r.verb}.",
        f"Create a child-friendly legend with a twist and a bad ending, using the words fierce, cup-ful, and enable.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    cup: Entity = _safe_fact(world, world.facts, "cup")
    rite: Rite = _safe_fact(world, world.facts, "rite")
    setting: Setting = _safe_fact(world, world.facts, "setting")

    qa = [
        QAItem(
            question=f"Who were the two friends in the story at {setting.place}?",
            answer=f"The story was about {hero.label} and {friend.label}, who came together as friends to the old place.",
        ),
        QAItem(
            question=f"What did the cup-ful of water help them do?",
            answer=f"It was meant to enable {rite.gerund}, so the friends could try the holy task at {setting.place}.",
        ),
        QAItem(
            question="Why did the story feel fierce before it turned sad?",
            answer="Because the friends were trying to face a fierce guardian and a dangerous mystery beneath the stones.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the bright cup-ful was not only helpful; it also woke the danger and turned the blessing into trouble.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the cup broke, the gate stayed shut, and the friendship was left cracked and sorrowful.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["rite"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(r[0] for r in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shrine", rite="ritual", cup="goldcup", hero_name="Aster", friend_name="Cai", hero_type="girl", friend_type="boy"),
    StoryParams(place="spring", rite="ritual", cup="shellcup", hero_name="Mira", friend_name="Rhea", hero_type="priestess", friend_type="girl"),
]


ASP_RULES = r"""
place(shrine). place(spring). place(grove).
rite(ritual).
cup(goldcup). cup(shellcup).
friendship(ritual) :- rite(ritual).
twist(ritual) :- rite(ritual).
bad_ending(ritual) :- rite(ritual).
valid(Place,Rite,Cup) :- place(Place), rite(Rite), cup(Cup).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in RITES:
        lines.append(asp.fact("rite", r))
    for c in CUPS:
        lines.append(asp.fact("cup", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, r, c) for p in SETTINGS for r in RITES for c in CUPS if reasonableness_gate(p, r, c)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(RITES, params.rite),
        _safe_lookup(CUPS, params.cup),
        params.hero_name,
        params.friend_name,
        params.hero_type,
        params.friend_type,
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


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    rite = getattr(args, "rite", None) or rng.choice(list(RITES))
    cup = getattr(args, "cup", None) or rng.choice(list(CUPS))
    if not reasonableness_gate(place, rite, cup):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy", "priestess"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["boy", "girl", "priest"])
    return StoryParams(
        place=place,
        rite=rite,
        cup=cup,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_type=hero_type,
        friend_type=friend_type,
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [build_story(p) for p in CURATED]
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.rite} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
