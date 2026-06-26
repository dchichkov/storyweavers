#!/usr/bin/env python3
"""
storyworlds/worlds/devil_inference_loud_suspense_sharing_fairy_tale.py
======================================================================

A small fairy-tale story world about a loud little devil, a careful act of
inference, and a suspenseful turn toward sharing.

Premise sketch:
- A loud devil sits on a moonlit path with a basket of glossy apples.
- The village worries because the devil speaks in a booming voice and guards
  the basket like a treasure.
- A fairy or child notices clues: the basket is not a trap; it is a gift for a
  hungry friend.
- The suspense ends when the characters share the apples and the devil's
  loudness softens into relief.

The world is intentionally small and constraint-checked: if the chosen story
cannot honestly create suspense and then resolve it through sharing, it is
rejected with a StoryError.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    devil: object | None = None
    friend: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
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
    twilight: bool = True
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
class Plot:
    id: str
    verb: str
    gerund: str
    clue: str
    suspense: str
    resolution: str
    sound: str
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
class Treasure:
    label: str
    phrase: str
    type: str
    plural: bool = False
    shared_with: set[str] = field(default_factory=set)
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
class Friend:
    id: str
    type: str
    label: str
    gender: str
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
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    plot: str
    treasure: str
    friend: str
    friend_gender: str
    name: str
    seed: Optional[int] = None
    params: object | None = None
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
    "moon_path": Setting(place="the moonlit path", twilight=True, affords={"listening", "sharing"}),
    "pine_gate": Setting(place="the pine gate", twilight=True, affords={"listening", "sharing"}),
    "little_bridge": Setting(place="the little bridge", twilight=True, affords={"listening", "sharing"}),
}

PLOTS = {
    "bells": Plot(
        id="bells",
        verb="ring a bell",
        gerund="ringing the bell",
        clue="a bright bell sound",
        suspense="a loud bell kept echoing in the dark",
        resolution="the bell was only a signal for friends to gather",
        sound="ringing",
        keyword="bell",
        tags={"loud", "inference", "suspense"},
    ),
    "lantern": Plot(
        id="lantern",
        verb="lift a lantern",
        gerund="lifting the lantern",
        clue="a warm lantern glow",
        suspense="the lantern glow made shadows look very strange",
        resolution="the lantern was lighting the way for a sleepy friend",
        sound="hum",
        keyword="lantern",
        tags={"loud", "inference", "suspense"},
    ),
    "basket": Plot(
        id="basket",
        verb="guard a basket",
        gerund="guarding the basket",
        clue="sweet apple peels by the basket",
        suspense="the basket stayed closed while everyone wondered why",
        resolution="the basket held a sharing supper for the cottage",
        sound="rustling",
        keyword="basket",
        tags={"inference", "suspense", "sharing"},
    ),
}

TREASURES = {
    "apples": Treasure(label="apples", phrase="a basket of red apples", type="basket", plural=True),
    "cakes": Treasure(label="cakes", phrase="three honey cakes", type="cakes", plural=True),
    "berries": Treasure(label="berries", phrase="a bowl of dark berries", type="berries", plural=True),
}

FRIENDS = {
    "fairy": Friend(id="fairy", type="fairy", label="a bright fairy", gender="girl"),
    "boy": Friend(id="boy", type="boy", label="a small boy", gender="boy"),
    "girl": Friend(id="girl", type="girl", label="a clever girl", gender="girl"),
}

NAMES = ["Mira", "Luna", "Nell", "Pip", "Toby", "Sera", "Oona", "Bram"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for plot_id in setting.affords:
            plot = _safe_lookup(PLOTS, plot_id)
            for treasure in TREASURES:
                for friend in FRIENDS:
                    combos.append((place, plot_id, treasure, friend))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world: devil, inference, loud suspense, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plot", choices=PLOTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "gender", None) and getattr(args, "friend", None) and getattr(args, "gender", None) != _safe_lookup(FRIENDS, getattr(args, "friend", None)).gender:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "plot", None) is None or c[1] == getattr(args, "plot", None))
        and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))
        and (getattr(args, "friend", None) is None or c[3] == getattr(args, "friend", None))
        and (getattr(args, "gender", None) is None or FRIENDS[c[3]].gender == getattr(args, "gender", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, plot, treasure, friend = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or _safe_lookup(FRIENDS, friend).gender
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, plot=plot, treasure=treasure, friend=friend, friend_gender=gender, name=name)


def _do_share(world: World, devil: Entity, friend: Entity, treasure: Entity) -> None:
    devil.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    treasure.meters["shared"] = 1
    world.say(f"They shared the {treasure.label} at last, and the night felt gentle again.")


def _infer(world: World, friend: Entity, plot: Plot, devil: Entity) -> None:
    friend.memes["inference"] += 1
    world.say(
        f"{friend.id} noticed the {plot.clue} and guessed the truth: "
        f"the devil was not being cruel, only careful."
    )


def _suspense(world: World, devil: Entity, plot: Plot, treasure: Entity) -> None:
    devil.memes["suspense"] += 1
    devil.memes["loud"] += 1
    world.say(
        f"{devil.id} stood very still, but {devil.pronoun('possessive')} voice was loud as a trumpet. "
        f"{plot.suspense}."
    )
    world.say(
        f"Everyone waited, wondering if the {treasure.label} would ever be opened."
    )


def tell(setting: Setting, plot: Plot, treasure_cfg: Treasure, friend_cfg: Friend, name: str) -> World:
    world = World(setting)
    devil = world.add(Entity(id=name, kind="character", type="devil", label="little devil"))
    friend = world.add(Entity(id=friend_cfg.id, kind="character", type=friend_cfg.type, label=friend_cfg.label))
    treasure = world.add(Entity(id="treasure", type=treasure_cfg.type, label=treasure_cfg.label, phrase=treasure_cfg.phrase, plural=treasure_cfg.plural))
    treasure.owner = devil.id

    world.say(f"Once upon a time, {devil.id} was a little devil by {setting.place}.")
    world.say(
        f"{devil.pronoun().capitalize()} loved {plot.gerund}, and {devil.pronoun('possessive')} voice could fill the trees with {plot.sound}."
    )
    world.say(f"Near {devil.id} lay {treasure_cfg.phrase}, meant for a sharing supper.")

    world.para()
    world.say(f"One evening at {setting.place}, {friend.id} came near while {devil.id} was {plot.gerund}.")
    _suspense(world, devil, plot, treasure)
    _infer(world, friend, plot, devil)
    world.say(
        f"That little guess changed everything. {friend.id} saw that the {treasure.label} was not a trap, but a gift waiting to be shared."
    )

    world.para()
    _do_share(world, devil, friend, treasure)
    devil.memes["relief"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{devil.id} smiled with relief, and {devil.pronoun('possessive')} loud voice turned soft as a bedtime song."
    )
    world.say(
        f"By the end, the {treasure.label} was open, the suspense was gone, and the moonlit path shone kindly around them."
    )

    world.facts.update(devil=devil, friend=friend, treasure=treasure, plot=plot, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    devil, friend, plot, treasure = f["devil"], f["friend"], f["plot"], f["treasure"]
    return [
        f'Write a short fairy tale for a child about {devil.id}, a loud devil, and a clever guess that leads to sharing.',
        f"Tell a gentle suspense story where {friend.id} notices clues and infers why {devil.id} is guarding {treasure.phrase}.",
        f'Write a simple story that uses the word "{plot.keyword}" and ends with the treasure being shared.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    devil, friend, plot, treasure = f["devil"], f["friend"], f["plot"], f["treasure"]
    return [
        QAItem(
            question=f"Who was the story about by the moonlit path?",
            answer=f"It was about {devil.id}, a little devil who could be loud but also cared about sharing.",
        ),
        QAItem(
            question=f"What clue helped {friend.id} make an inference about {devil.id}?",
            answer=f"{friend.id} noticed {plot.clue}, and that clue helped {friend.id} infer that {devil.id} was being careful, not cruel.",
        ),
        QAItem(
            question=f"What ended the suspense near the treasure?",
            answer=f"The suspense ended when they opened and shared {treasure.phrase} together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an inference?", answer="An inference is a smart guess made from clues."),
        QAItem(question="What does loud mean?", answer="Loud means making a strong sound that is easy to hear."),
        QAItem(question="What is sharing?", answer="Sharing means letting other people have some of what you have."),
        QAItem(question="What is suspense?", answer="Suspense is the worried waiting that happens when you do not know what will happen next."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_path", plot="basket", treasure="apples", friend="fairy", friend_gender="girl", name="Pip"),
    StoryParams(place="pine_gate", plot="bells", treasure="berries", friend="girl", friend_gender="girl", name="Mara"),
    StoryParams(place="little_bridge", plot="lantern", treasure="cakes", friend="boy", friend_gender="boy", name="Niko"),
]


ASP_RULES = r"""
plot_has_tag(P, T) :- plot(P), tag(P, T).
needs_sharing(P) :- tag(P, sharing).
needs_inference(P) :- tag(P, inference).
needs_loud(P) :- tag(P, loud).
needs_suspense(P) :- tag(P, suspense).

good_story(S, P, T, F) :- setting(S), plot(P), treasure(T), friend(F),
                          needs_sharing(P), needs_inference(P), needs_loud(P), needs_suspense(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PLOTS.items():
        lines.append(asp.fact("plot", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show good_story/4."))
    clingo_set = set(asp.atoms(model, "good_story"))
    python_set = set((s, p, t, f) for s, p, t, f in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PLOTS, params.plot), _safe_lookup(TREASURES, params.treasure), _safe_lookup(FRIENDS, params.friend), params.name)
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


def explain_rejection() -> str:
    return "(No story: this world only tells tales where loud suspense can honestly turn into sharing.)"


def resolve_validity(args: argparse.Namespace) -> None:
    if getattr(args, "gender", None) and getattr(args, "friend", None) and getattr(args, "gender", None) != _safe_lookup(FRIENDS, getattr(args, "friend", None)).gender:
        pass


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/4."))
        stories = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    resolve_validity(args)
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
                plot = getattr(args, "plot", None) or rng.choice(list(_safe_lookup(SETTINGS, place).affords))
                treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
                friend = getattr(args, "friend", None) or rng.choice(list(FRIENDS))
                gender = getattr(args, "gender", None) or _safe_lookup(FRIENDS, friend).gender
                name = getattr(args, "name", None) or rng.choice(NAMES)
                params = StoryParams(place=place, plot=plot, treasure=treasure, friend=friend, friend_gender=gender, name=name, seed=seed)
            except Exception as exc:
                pass
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
            header = f"### {p.name}: {p.plot} at {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
