#!/usr/bin/env python3
"""
Standalone story world: aeronautic talent surprise pirate tale.

A small, classical simulation about a pirate crew on a flying ship, where a
hidden aeronautic talent causes a surprise that changes the day's course.
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
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    prize: object | None = None
    ship: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"lift": 0.0, "speed": 0.0, "damage": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "joy": 0.0, "surprise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "pirate girl"}
        male = {"boy", "man", "father", "pirate boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    sky: str
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
class Talent:
    id: str
    name: str
    verb: str
    gerund: str
    risk: str
    surprise: str
    effect: str
    keyword: str = "talent"
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.events: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _apply_lift(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("crew")
    ship = world.get("ship")
    if crew.meters["lift"] >= THRESHOLD and ("lift",) not in world.fired:
        world.fired.add(("lift",))
        ship.meters["speed"] += 1
        out.append("The flying ship rose higher on a bright pocket of wind.")
    return out


def _apply_damage(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    if ship.meters["damage"] >= THRESHOLD and ("damage",) not in world.fired:
        world.fired.add(("damage",))
        out.append("The boards groaned, but the ship still held together.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_lift, _apply_damage):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, talent: Talent, prize_id: str) -> dict:
    sim = world.copy()
    perform_talent(sim, sim.get(actor.id), talent, narrate=False)
    prize = sim.get(prize_id)
    return {
        "surprise": actor.memes["surprise"] > 0,
        "damage": prize.meters["damage"] >= THRESHOLD,
        "lift": sim.get("ship").meters["speed"],
    }


def setup_story(world: World, captain: Entity, hero: Entity, prize: Entity, talent: Talent) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} on the pirate ship, quick with a grin and "
        f"quiet about {hero.pronoun('possessive')} secret {talent.keyword} talent."
    )
    world.say(
        f"The crew loved the clean snap of sails and the silver shine of the sky, but "
        f"{hero.id} loved {talent.gerund} best of all."
    )
    world.say(
        f"One day, {captain.id} showed {hero.id} {prize.phrase} and said it had to stay safe "
        f"until the voyage ended."
    )
    prize.worn_by = hero.id


def build_tension(world: World, captain: Entity, hero: Entity, prize: Entity, talent: Talent) -> None:
    world.para()
    world.say(
        f"Then a storm puffed up over the sea, and the pirate ship rocked hard in the wind."
    )
    world.say(
        f"{hero.id} wanted to help right away, but {hero.pronoun('possessive')} chest felt tight with worry."
    )
    predicted = predict(world, hero, talent, prize.id)
    world.facts["predicted"] = predicted
    if predicted["damage"]:
        world.say(
            f'"If you use that {talent.name} in the wrong way, {prize.label} could get ruined," '
            f'{captain.id} warned.'
        )
    else:
        world.say(
            f'"If you try to help, be careful," {captain.id} said, peering at the storm.'
        )


def perform_talent(world: World, hero: Entity, talent: Talent, narrate: bool = True) -> None:
    ship = world.get("ship")
    hero.memes["surprise"] += 1
    hero.memes["pride"] += 1
    ship.meters["lift"] += 1
    ship.meters["speed"] += 1
    ship.memes["joy"] += 1
    world.events.append("talent")
    if narrate:
        world.say(
            f"{hero.id} took a breath, opened {hero.pronoun('possessive')} arms, and began {talent.gerund}."
        )
        world.say(
            f"To everyone's surprise, the motion caught the wind and the ship answered at once."
        )
        world.say(
            f"{talent.effect}"
        )


def resolve(world: World, captain: Entity, hero: Entity, prize: Entity, talent: Talent, tool: Tool) -> None:
    ship = world.get("ship")
    world.para()
    hero.memes["joy"] += 1
    captain.memes["joy"] += 1
    world.say(
        f"{captain.id} laughed, because {hero.id}'s surprise talent was exactly what the crew needed."
    )
    world.say(
        f"They used {tool.phrase}, and the pirate ship flew cleanly above the waves."
    )
    world.say(
        f"{tool.tail.capitalize()}. The storm slid away beneath them, and {prize.label} stayed safe."
    )
    world.say(
        f"By the end, {hero.id} was still {talent.gerund}, but now the whole crew knew what {hero.pronoun('subject')} could do."
    )
    ship.meters["speed"] += 1


SETTINGS = {
    "harbor": Setting(place="the harbor sky", sky="windy", affords={"flight"}),
    "reef": Setting(place="the reef line", sky="stormy", affords={"flight"}),
    "open_sea": Setting(place="the open sea", sky="bright", affords={"flight"}),
}

TALENTS = {
    "kite": Talent(
        id="kite",
        name="kite-steering",
        verb="kite-steer the sails",
        gerund="kite-steering the sails",
        risk="the rigging might tangle",
        surprise="the sails rose like a bright kite",
        effect="The ropes sang, and the mast leaned into the wind like it had been waiting for this all along.",
    ),
    "glide": Talent(
        id="glide",
        name="gliding",
        verb="glide through gusts",
        gerund="gliding through gusts",
        risk="the deck might slip",
        surprise="the ship skimmed the air like a gull",
        effect="The ship balanced itself on the gusts, as neat as a bird on warm air.",
    ),
    "whistle": Talent(
        id="whistle",
        name="wind-whistling",
        verb="whistle to the wind",
        gerund="whistling to the wind",
        risk="the storm might answer too loud",
        surprise="the clouds turned, as if listening",
        effect="The wind shifted kindly, and the storm opened a path of blue sky.",
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a rolled treasure map", type="map"),
    "lantern": Prize(label="lantern", phrase="a brass lantern", type="lantern"),
    "compass": Prize(label="compass", phrase="a shiny compass", type="compass"),
}

TOOLS = {
    "spar": Tool(
        id="spar",
        label="the spar",
        phrase="the long spar and a coil of rope",
        helps={"kite", "glide"},
        prep="they tied the rope to the spar",
        tail="With the rope firm and the spar steady, the ship caught the wind",
    ),
    "glass": Tool(
        id="glass",
        label="the lookout glass",
        phrase="a lookout glass and a calm hand",
        helps={"whistle"},
        prep="they shaded the glass and watched the clouds",
        tail="With a careful look and a steady breath, the storm split open",
    ),
}

GENDERS = ["girl", "boy"]
PIRATE_NAMES = ["Nia", "Milo", "Rae", "Finn", "Pip", "Lena", "Toby", "Mara"]
CAPTAIN_NAMES = ["Captain Sable", "Captain Reed", "Captain Brine", "Captain Coral"]


@dataclass
class StoryParams:
    setting: str
    talent: str
    prize: str
    name: str
    gender: str
    captain: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in setting.affords:
            for pid in PRIZES:
                combos.append((sid, tid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with aeronautic talent and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--talent", choices=TALENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "talent", None) is None or c[1] == getattr(args, "talent", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, talent, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(PIRATE_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    return StoryParams(setting=setting, talent=talent, prize=prize, name=name, gender=gender, captain=captain)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    talent = _safe_lookup(TALENTS, params.talent)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    captain = world.add(Entity(id=params.captain, kind="character", type="pirate captain", label=params.captain))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="flying ship"))
    prize = world.add(Entity(id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id))
    tool = TOOLS["spar"] if talent.id in TOOLS["spar"].helps else TOOLS["glass"]

    setup_story(world, captain, hero, prize, talent)
    build_tension(world, captain, hero, prize, talent)
    perform_talent(world, hero, talent, narrate=True)
    resolve(world, captain, hero, prize, talent, tool)

    world.facts.update(hero=hero, captain=captain, ship=ship, prize=prize, talent=talent, tool=tool, setting=setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a small child that includes a surprise aeronautic talent.',
        f"Tell a gentle story where {f['hero'].id} surprises the pirate crew by {f['talent'].gerund}.",
        f"Write a story about a pirate ship in the {world.setting.place} where a hidden talent helps save {f['prize'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    prize: Entity = _safe_fact(world, f, "prize")
    talent: Talent = _safe_fact(world, f, "talent")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What surprise did {hero.id} have on the pirate ship?",
            answer=f"{hero.id} had a surprise {talent.keyword} talent, and it helped the ship move with the wind.",
        ),
        QAItem(
            question=f"Why did {captain.id} worry before {hero.id} helped?",
            answer=f"{captain.id} worried the storm could damage {prize.label}, so the crew needed a careful plan.",
        ),
        QAItem(
            question=f"What did the crew use to make the plan work?",
            answer=f"They used {tool.phrase}, which helped the ship hold steady while {hero.id} used {talent.gerund}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the ship was flying cleanly, the storm had moved away, and {prize.label} stayed safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used by pirates to travel, carry gear, and sail across the sea.",
        ),
        QAItem(
            question="What does wind do to a flying ship?",
            answer="Wind can push the sails and help a flying ship move faster and rise higher.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes people stop and notice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Setting,Talent,Prize) :- setting(Setting), talent(Talent), prize(Prize), affords(Setting,Talent).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TALENTS:
        lines.append(asp.fact("talent", tid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(setting="harbor", talent="kite", prize="map", name="Nia", gender="girl", captain="Captain Sable"),
    StoryParams(setting="reef", talent="whistle", prize="lantern", name="Milo", gender="boy", captain="Captain Brine"),
    StoryParams(setting="open_sea", talent="glide", prize="compass", name="Rae", gender="girl", captain="Captain Coral"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
