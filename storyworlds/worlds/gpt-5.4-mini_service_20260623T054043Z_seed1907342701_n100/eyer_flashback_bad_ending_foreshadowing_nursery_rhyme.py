#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/eyer_flashback_bad_ending_foreshadowing_nursery_rhyme.py
=============================================================================================================================

A tiny nursery-rhyme storyworld about a little character named Eyer, with
foreshadowing, a brief flashback, and a bad ending that still feels complete.

Premise:
- A child wants to do a small, simple task in a bright place.

Tension:
- A warning sign and a remembered earlier mistake foreshadow trouble.
- The child keeps going anyway, and the physical world changes in a way that
  ruins the simple task.

Turn:
- The story flashes back to the earlier lesson, but the child is already in the
  new trouble.

Resolution:
- The ending is sad or messy rather than happy; the final image proves what
  changed.

The style is intentionally close to a nursery rhyme: short lines, plain words,
soft repeated sounds, and a lightly rhythmic voice.
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    role: str = ""
    place: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Place:
    id: str
    label: str
    bright: bool
    risk: str
    foreshadow: str
    flashback: str
    ending: str
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
class Task:
    id: str
    verb: str
    object_label: str
    object_phrase: str
    risk_meter: str
    spill_word: str
    place_tags: set[str] = field(default_factory=set)
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
class Warning:
    id: str
    line: str
    flashback_line: str
    helper: str
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
class Ending:
    id: str
    line: str
    image: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _meter(m: dict[str, float], key: str) -> float:
    return m.get(key, 0.0)


def _mark(m: dict[str, float], key: str, amount: float = 1.0) -> None:
    m[key] = m.get(key, 0.0) + amount


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    task: Task = world.facts["task"]
    place: Place = world.facts["place_cfg"]
    if world.facts["spill_done"]:
        return out
    child = world.get("eyer")
    if _meter(child.meters, task.risk_meter) < THRESHOLD:
        return out
    if task.id == "berries":
        world.get("basket").meters["empty"] = 1.0
    elif task.id == "milk":
        world.get("jug").meters["empty"] = 1.0
    elif task.id == "muddle":
        world.get("shoes").meters["muddy"] = 1.0
    elif task.id == "bells":
        world.get("bells").meters["dull"] = 1.0
    elif task.id == "bread":
        world.get("loaf").meters["crumbled"] = 1.0
    world.facts["spill_done"] = True
    out.append("__spill__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_spill(world):
            changed = True
            if s != "__spill__":
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    task: str
    warning: str
    ending: str
    name: str = "Eyer"
    parent: str = "mother"
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


PLACES = {
    "brook": Place(
        id="brook",
        label="the brook",
        bright=True,
        risk="slick stones",
        foreshadow="The stones are slick and the reeds lean low.",
        flashback="Last time, a little slip made a splashy mess.",
        ending="The brook stays high and the basket stays empty.",
        tags={"water", "brook", "slick"},
    ),
    "meadow": Place(
        id="meadow",
        label="the meadow",
        bright=True,
        risk="windy hill",
        foreshadow="The wind is keen and the grass bends away.",
        flashback="Once before, the wind carried a toy right out of sight.",
        ending="The kite lies flat, its tail all tangled in the grass.",
        tags={"wind", "meadow", "kite"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        bright=False,
        risk="busy floor",
        foreshadow="A spoon clinks and the floor is busy and slick.",
        flashback="Yesterday, one dropped cup made a milky moon on the floor.",
        ending="The floor is spattered, and the clean cloth hangs still.",
        tags={"milk", "kitchen", "floor"},
    ),
    "hill": Place(
        id="hill",
        label="the little hill",
        bright=True,
        risk="breezy edge",
        foreshadow="The clouds go quick and the top of the hill hums.",
        flashback="Before, a hat blew off and rolled and rolled.",
        ending="The bells go dull in the grass, and the hill keeps the sound.",
        tags={"hill", "bells", "wind"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        bright=True,
        risk="dusty step",
        foreshadow="Dust puffs up at every little tap.",
        flashback="A crumb trail once drew ants to the door.",
        ending="The loaf is crumbled, and crumbs shine like sand.",
        tags={"porch", "bread", "dust"},
    ),
}

TASKS = {
    "berries": Task("berries", "gather berries", "basket", "a little basket", "empty", "spilled berries", {"brook"}, {"berries"}),
    "milk": Task("milk", "carry milk", "jug", "a small jug of milk", "empty", "spilled milk", {"kitchen"}, {"milk"}),
    "muddle": Task("muddle", "dance in the mud", "shoes", "a pair of clean shoes", "muddy", "mud on the shoes", {"meadow"}, {"mud"}),
    "bells": Task("bells", "ring bells", "bells", "a tiny row of bells", "dull", "dull bells", {"hill"}, {"bells"}),
    "bread": Task("bread", "carry bread", "loaf", "a fresh round loaf", "crumbled", "crumbs on the porch", {"porch"}, {"bread"}),
}

WARNINGS = {
    "brook": Warning("brook", "Don't hop too near the stones.", "Last time, a little slip made a splashy mess.", "grandmother", {"brook"}),
    "meadow": Warning("meadow", "Don't run where the wind can snatch.", "Once before, the wind carried a toy right out of sight.", "father", {"meadow"}),
    "kitchen": Warning("kitchen", "Don't hurry on the busy floor.", "Yesterday, one dropped cup made a milky moon on the floor.", "mother", {"kitchen"}),
    "hill": Warning("hill", "Don't climb too high where the wind can sway.", "Before, a hat blew off and rolled and rolled.", "grandfather", {"hill"}),
    "porch": Warning("porch", "Don't step too hard or the crumbs will fly.", "A crumb trail once drew ants to the door.", "mother", {"porch"}),
}

ENDINGS = {
    "brook": Ending("brook", "The basket is all gone now.", "The brook stays high and the basket stays empty.", {"brook"}),
    "meadow": Ending("meadow", "The kite is caught in grass.", "The kite lies flat, its tail all tangled in the grass.", {"meadow"}),
    "kitchen": Ending("kitchen", "The milk is on the floor.", "The floor is spattered, and the clean cloth hangs still.", {"kitchen"}),
    "hill": Ending("hill", "The bells are dull and gone soft.", "The bells go dull in the grass, and the hill keeps the sound.", {"hill"}),
    "porch": Ending("porch", "The loaf is crumbs and dust.", "The loaf is crumbled, and crumbs shine like sand.", {"porch"}),
}

GIRL_NAMES = ["Eyer", "Mina", "Lila", "Nora", "Mabel", "Pip"]
BOY_NAMES = ["Eyer", "Toby", "Bram", "Owen", "Ari", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, w) for p in PLACES for t in TASKS for w in WARNINGS if p == t or p in _safe_lookup(TASKS, t).place_tags]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with foreshadowing, flashback, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "warning", None) is None or c[2] == getattr(args, "warning", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, warning = rng.choice(list(combos))
    ending = getattr(args, "ending", None) or task
    if ending not in ENDINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or "Eyer"
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(place=place, task=task, warning=warning, ending=ending, name=name, parent=parent)


def _scene_line(place: Place, task: Task) -> str:
    return f"{place.label.capitalize()} was bright and neat, and little Eyer had a little task to do."


def tell(params: StoryParams) -> World:
    world = World()
    place = _safe_lookup(PLACES, params.place)
    task = _safe_lookup(TASKS, params.task)
    warn = _safe_lookup(WARNINGS, params.warning)
    ending = _safe_lookup(ENDINGS, params.ending)
    child = world.add(Entity(id="eyer", kind="character", type="boy", label=params.name, role="child", place=place.id, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent, role="parent", place=place.id, meters={}, memes={}))
    world.add(Entity(id="basket", label="basket", meters={"empty": 0.0}))
    world.add(Entity(id="jug", label="jug", meters={"empty": 0.0}))
    world.add(Entity(id="shoes", label="shoes", meters={"muddy": 0.0}))
    world.add(Entity(id="bells", label="bells", meters={"dull": 0.0}))
    world.add(Entity(id="loaf", label="loaf", meters={"crumbled": 0.0}))
    world.facts.update(place_cfg=place, task=task, warning=warn, ending_cfg=ending, spill_done=False)
    child.meters[task.risk_meter] = 0.0
    child.memes["hope"] = 1.0
    world.say(_scene_line(place, task))
    world.say(f"Hey diddle, diddle, and off went Eyer's prickle of will.")
    world.say(place.foreshadow)
    world.say(f'"{warn.line}" said {warn.helper}, and Eyer went still.')
    world.para()
    child.meters[task.risk_meter] = 1.0
    child.memes["want"] = 1.0
    world.say(f"Eyer tried to {task.verb}, with {task.object_phrase} held tight and bright.")
    world.say(f"Then the day turned sly, and the old tune came back: {warn.flashback_line}")
    propagate(world, narrate=False)
    if task.id == "berries":
        world.get("basket").meters["empty"] = 1.0
    elif task.id == "milk":
        world.get("jug").meters["empty"] = 1.0
    elif task.id == "muddle":
        world.get("shoes").meters["muddy"] = 1.0
    elif task.id == "bells":
        world.get("bells").meters["dull"] = 1.0
    elif task.id == "bread":
        world.get("loaf").meters["crumbled"] = 1.0
    world.para()
    world.say(ending.line)
    world.say(ending.image)
    world.facts.update(child=child, parent=parent, task=task, place=place, ending=ending, spilled=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p, t, w = f["place_cfg"], f["task"], f["warning"]
    return [
        f'Write a short nursery-rhyme story about Eyer at {p.label} with the line "{w.line}".',
        f"Tell a gentle rhyme where Eyer tries to {t.verb}, but a warning and an old memory foreshadow a bad ending.",
        f'Write a simple story that uses the word "eyer" and ends with {p.ending.lower()}',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p, t, w, e = f["place_cfg"], f["task"], f["warning"], f["ending_cfg"]
    return [
        QAItem(
            question=f"Who is the story about at {p.label}?",
            answer=f"It is about little Eyer. {p.label.capitalize()} is the place where Eyer tries to {t.verb}."
        ),
        QAItem(
            question=f"Why did {w.helper} warn Eyer?",
            answer=f"{w.helper.capitalize()} warned Eyer because the place looked risky and the old trouble could happen again. The warning foreshadowed the bad ending that came later."
        ),
        QAItem(
            question=f"What old memory comes back in the middle of the story?",
            answer=f"The story flashes back to {w.flashback_line.lower()}. That memory shows why the warning mattered."
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {e.image.lower()}. The final image proves that Eyer's little task did not stay neat and happy."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is foreshadowing?", "Foreshadowing is a clue that hints something will happen later in the story."),
        QAItem("What is a flashback?", "A flashback is a part of the story that looks back to something that happened before."),
        QAItem("What is a bad ending in a story?", "A bad ending is when the story finishes with trouble, loss, or a sad change."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P,T,W) :- place(P), task(T), warning(W), task_place(T,P), warn_place(W,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if pid in {"brook", "meadow", "hill", "porch"}:
            lines.append(asp.fact("task_place", "berries" if pid=="brook" else "muddle" if pid=="meadow" else "bells" if pid=="hill" else "bread", pid))
        if pid == "kitchen":
            lines.append(asp.fact("task_place", "milk", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for wid, w in WARNINGS.items():
        lines.append(asp.fact("warning", wid))
        for t in w.tags:
            lines.append(asp.fact("warn_place", wid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between python and clingo.")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: {len(py)} combos; smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.warning not in WARNINGS or params.ending not in ENDINGS:
        pass
    world = tell(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="brook", task="berries", warning="brook", ending="brook", name="Eyer", parent="mother"),
    StoryParams(place="meadow", task="muddle", warning="meadow", ending="meadow", name="Eyer", parent="father"),
    StoryParams(place="kitchen", task="milk", warning="kitchen", ending="kitchen", name="Eyer", parent="mother"),
    StoryParams(place="hill", task="bells", warning="hill", ending="hill", name="Eyer", parent="grandfather"),
    StoryParams(place="porch", task="bread", warning="porch", ending="porch", name="Eyer", parent="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return
    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
