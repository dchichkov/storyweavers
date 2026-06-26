#!/usr/bin/env python3
"""
storyworlds/worlds/otter_dialogue_misunderstanding_twist_comedy.py
==================================================================

A standalone story world about an otter, a funny misunderstanding, and a twisty
dialogue-driven resolution.

Premise:
- An otter wants something ordinary, like a shiny bowl, shell, bell, or hat.
- Another character mishears the otter and assumes a wildly different problem.
- Their conversation escalates into a comic mix-up.
- The twist reveals the otter wanted something harmless all along.

The world models physical state with meters and emotional state with memes:
- physical: ownership, location, wetness, shine, tidiness, carried items
- emotional: curiosity, worry, embarrassment, relief, amusement, friendship

The resulting story should feel like a complete little comedy with:
- a beginning that introduces the otter and the ordinary desire,
- a middle full of misunderstanding through dialogue,
- a twist that changes the interpretation,
- an ending that proves the world state changed.
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    shiny: object | None = None
    friend: object | None = None
    otter: object | None = None
    prop: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"otter"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the riverbank"
    indoors: bool = False
    features: list[str] = field(default_factory=lambda: ["water", "stones", "reeds"])
    SETTING: object | None = None
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
class Want:
    id: str
    noun: str
    phrase: str
    verb: str
    twist_noun: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    shiny: bool = False
    ownerable: bool = True
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
        self.facts: dict[str, object] = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
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


def _r_wet_mess(world: World) -> list[str]:
    out: list[str] = []
    otter = world.get("otter")
    want = _safe_fact(world, world.facts, "want")
    if otter.meter("wetness") >= THRESHOLD and want.id not in world.fired:
        world.fired.add((want.id, "wet"))
        otter.memes["mischief"] = otter.meme("mischief") + 1
        out.append(f"Water dripped everywhere, which made the whole idea feel sillier.")
    return out


def _r_embarrassed_confusion(world: World) -> list[str]:
    out: list[str] = []
    otter = world.get("otter")
    friend = world.get("friend")
    if otter.meme("confusion") >= THRESHOLD and friend.meme("worry") >= THRESHOLD:
        sig = ("confusion", "exchange")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__dialogue_confusion__")
    return out


CAUSAL_RULES = [
    Rule("wet_mess", _r_wet_mess),
    Rule("embarrassed_confusion", _r_embarrassed_confusion),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__dialogue_confusion__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()

WANTS = {
    "bell": Want(
        id="bell",
        noun="bell",
        phrase="a little silver bell",
        verb="ring the bell",
        twist_noun="shell",
        risk="loud",
        keyword="bell",
        tags={"bell", "sound"},
    ),
    "bowl": Want(
        id="bowl",
        noun="bowl",
        phrase="a shiny blue bowl",
        verb="borrow the bowl",
        twist_noun="boat",
        risk="borrowed",
        keyword="bowl",
        tags={"bowl", "food"},
    ),
    "hat": Want(
        id="hat",
        noun="hat",
        phrase="a silly straw hat",
        verb="wear the hat",
        twist_noun="fish",
        risk="small",
        keyword="hat",
        tags={"hat", "clothes"},
    ),
    "shell": Want(
        id="shell",
        noun="shell",
        phrase="a striped shell",
        verb="polish the shell",
        twist_noun="bell",
        risk="hard",
        keyword="shell",
        tags={"shell", "beach"},
    ),
}

PROPS = {
    "bell": Prop("bell", "bell", "a tiny brass bell", "bell", "shelf", shiny=True),
    "bowl": Prop("bowl", "bowl", "a shiny blue bowl", "bowl", "table", shiny=True),
    "hat": Prop("hat", "hat", "a silly straw hat", "hat", "hook"),
    "shell": Prop("shell", "shell", "a striped shell", "shell", "basket", shiny=True),
    "bucket": Prop("bucket", "bucket", "a red bucket", "bucket", "dock"),
}

GIVE_OBJECTS = {
    "bell": "the bell",
    "bowl": "the bowl",
    "hat": "the hat",
    "shell": "the shell",
    "bucket": "the bucket",
}

OTTER_NAMES = ["Ollie", "Milo", "Poppy", "Nori", "Rory", "Tula"]
FRIEND_NAMES = ["Mabel", "Jasper", "Kiki", "Finn", "Luna", "Bram"]

TRAITS = ["curious", "silly", "eager", "bouncy", "bright"]


@dataclass
class StoryParams:
    want: str
    name: str
    friend: str
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
    ap = argparse.ArgumentParser(description="Otter comedy world with dialogue, misunderstanding, and twist.")
    ap.add_argument("--want", choices=sorted(WANTS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    want = getattr(args, "want", None) or rng.choice(sorted(WANTS))
    name = getattr(args, "name", None) or rng.choice(OTTER_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(want=want, name=name, friend=friend, trait=trait)


def _say_dialogue(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.id} said.')


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    otter = world.add(Entity(
        id=params.name,
        kind="character",
        type="otter",
        label=params.name,
        location="the riverbank",
        meters={"wetness": 0.0},
        memes={"curiosity": 1.0, "amusement": 0.0, "confusion": 0.0, "relief": 0.0},
    ))
    otter.id = "otter" if params.name == "otter" else params.name
    world.entities.pop(params.name)
    world.entities["otter"] = otter

    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="friend",
        label=params.friend,
        location="the riverbank",
        meters={"dryness": 1.0},
        memes={"worry": 0.0, "confusion": 0.0, "amusement": 0.0, "relief": 0.0},
    ))
    prop = world.add(Entity(
        id=params.want,
        kind="thing",
        type=_safe_lookup(PROPS, params.want).type,
        label=_safe_lookup(PROPS, params.want).label,
        phrase=_safe_lookup(PROPS, params.want).phrase,
        location=_safe_lookup(PROPS, params.want).location,
        shiny=_safe_lookup(PROPS, params.want).shiny,
    ))

    want = _safe_lookup(WANTS, params.want)
    world.facts.update(otter=otter, friend=friend, prop=prop, want=want)

    world.say(f"{otter.label} was a {params.trait} otter who liked neat things that made a tiny sound or a tiny sparkle.")
    world.say(f"One morning, {otter.label} looked at {want.phrase} on the bank and decided {otter.pronoun()} wanted to {want.verb}.")
    world.say(f"{otter.label} made a hopeful squeak, because {want.phrase} looked perfect for the day.")

    world.para()
    world.say(f"{friend.label} paddled over and listened.")
    _say_dialogue(world, otter, f"Could I please {want.verb} with {_safe_lookup(GIVE_OBJECTS, want.id)}?")
    _say_dialogue(world, friend, f"Of course! Wait, why do you need a boat?")
    world.say(f"{otter.label} blinked. {otter.pronoun().capitalize()} had asked for {want.phrase}, but {friend.label} had heard a very different thing.")

    world.para()
    otter.memes["confusion"] += 1
    friend.memes["worry"] += 1
    world.say(f"{friend.label} pointed at the wrong thing and whispered, \"A boat? But the bucket is much safer!\"")
    _say_dialogue(world, otter, f"No, no, I said {want.verb}. I did not say I wanted a boat!")
    _say_dialogue(world, friend, f"Then why are you staring at the bucket like that?")
    world.say(f"{otter.label} stared at the bucket too, because now even the bucket looked suspiciously important.")
    propagate(world)

    world.para()
    world.say(f"Then came the twist: a tiny shell rolled out of the bucket with a cheerful clack.")
    _say_dialogue(world, otter, f"Oh! That is the sound I wanted!")
    _say_dialogue(world, friend, f"You wanted the shell, not a boat?")
    _say_dialogue(world, otter, f"Exactly. I wanted to {want.verb}, and the shell is what needed the sparkle.")
    world.say(f"{friend.label} laughed so hard that little bubbles popped at the surface.")

    otter.memes["relief"] += 1
    otter.memes["amusement"] += 1
    friend.memes["amusement"] += 1
    friend.memes["relief"] += 1
    otter.meters["wetness"] = 1.0
    prop.meters["shine"] = 1.0
    world.facts["resolved"] = True
    world.facts["twist"] = "shell"
    world.facts["misunderstanding"] = True

    world.say(f"So {otter.label} and {friend.label} polished the shell together, and the whole bank looked ready for a tiny parade.")
    world.say(f"By the end, {otter.label} was grinning, {friend.label} was grinning, and the bucket had been promoted to a very respectable prop.")

    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    want: Want = _safe_fact(world, f, "want")
    otter: Entity = _safe_fact(world, f, "otter")
    friend: Entity = _safe_fact(world, f, "friend")
    return [
        f'Write a short comedy story for a young child about an otter who wants "{want.keyword}" and gets misunderstood.',
        f"Tell a dialogue-heavy story where {otter.label} asks for {want.phrase}, but {friend.label} hears the wrong thing at first.",
        f"Write a gentle, funny story with a twist ending where the big misunderstanding turns out to be about {want.twist_noun}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    otter: Entity = _safe_fact(world, f, "otter")
    friend: Entity = _safe_fact(world, f, "friend")
    want: Want = _safe_fact(world, f, "want")
    prop: Entity = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"What did {otter.label} want at the riverbank?",
            answer=f"{otter.label} wanted {want.phrase}. {otter.pronoun().capitalize()} asked to {want.verb}, which is why the story started with such a small, funny problem.",
        ),
        QAItem(
            question=f"Why did {friend.label} get mixed up during the conversation?",
            answer=f"{friend.label} heard the request in the wrong way and thought {otter.label} meant something else, so the two of them talked past each other for a while.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {otter.label} did not want {prop.label} as a big problem at all; {otter.label} wanted the shell-related thing and the sparkle turned out to be the real clue.",
        ),
        QAItem(
            question=f"How did the story end for {otter.label} and {friend.label}?",
            answer=f"They laughed, fixed the misunderstanding, and polished the shell together, so the ending felt happy and a little silly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an otter?",
            answer="An otter is a playful animal that likes water, swims well, and often looks like it is having a very busy day.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing, so people need to talk again and clear it up.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes how you understand what was happening before.",
        ),
        QAItem(
            question="Why can dialogue be funny in a story?",
            answer="Dialogue can be funny when characters answer each other in surprising ways or talk past one another for a silly reason.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when an otter wants one object, a friend hears it wrong,
% and the twist resolves the misunderstanding.
has_otter :- otter(X).
has_friend :- friend(X).
has_want(W) :- want(W).
misunderstood :- has_otter, has_friend, has_want(W).

twist(W) :- want(W), twist_noun(W, T), T != "".
comedy_story :- misunderstood, twist(_).

#show comedy_story/0.
#show misunderstood/0.
#show twist/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for wid, want in WANTS.items():
        lines.append(asp.fact("want", wid))
        lines.append(asp.fact("twist_noun", wid, want.twist_noun))
    lines.append(asp.fact("otter", "otter"))
    lines.append(asp.fact("friend", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show comedy_story/0."))
    ok = any(sym.name == "comedy_story" for sym in model)
    if ok:
        print("OK: ASP twin emits a comedy_story model.")
        return 0
    print("MISMATCH: ASP twin did not produce comedy_story.")
    return 1


def build_reasonable_worlds() -> list[tuple[str, str]]:
    return [(wid, want.twist_noun) for wid, want in WANTS.items()]


CURATED = [
    StoryParams(want="bell", name="Ollie", friend="Mabel", trait="curious"),
    StoryParams(want="bowl", name="Nori", friend="Jasper", trait="silly"),
    StoryParams(want="hat", name="Poppy", friend="Kiki", trait="eager"),
    StoryParams(want="shell", name="Rory", friend="Finn", trait="bright"),
]


def explain_rejection(_: Want) -> str:
    return "(No story: this world is designed so the otter's request always supports a real misunderstanding and twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    want = getattr(args, "want", None) or rng.choice(sorted(WANTS))
    name = getattr(args, "name", None) or rng.choice(OTTER_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(want=want, name=name, friend=friend, trait=trait)


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
        print(asp_program("#show comedy_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: wants {p.want}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
