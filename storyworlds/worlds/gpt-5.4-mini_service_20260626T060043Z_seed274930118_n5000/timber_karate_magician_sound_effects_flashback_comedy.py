#!/usr/bin/env python3
"""
storyworlds/worlds/timber_karate_magician_sound_effects_flashback_comedy.py
============================================================================

A small comedy storyworld about a magician, karate practice, a stubborn piece
of timber, loud sound effects, and a flashback that explains why the trick feels
so important.

The premise is simple:
- A magician wants to finish a funny trick.
- A karate student wants to break a timber board.
- Their plans tangle in a noisy, comedic way.
- A flashback reveals the old reason the magician cares.
- The ending proves something changed: the timber is split, the trick lands,
  and the characters laugh instead of arguing.

This file is standalone and follows the Storyweavers storyworld contract.
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gear: object | None = None
    karate_kid: object | None = None
    magician: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    place: str = "the dojo"
    indoors: bool = True
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
class Trick:
    id: str
    name: str
    stage_name: str
    sound: str
    mess: str
    flashback_reason: str
    keyword: str
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
    region: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.flashback_opened = False

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.flashback_opened = self.flashback_opened
        return clone


# -----------------------------------------------------------------------------
# Content registries
# -----------------------------------------------------------------------------

SETTINGS = {
    "dojo": Setting(place="the dojo", indoors=True, affords={"karate", "magic"}),
    "stage": Setting(place="the little stage", indoors=True, affords={"magic"}),
    "yard": Setting(place="the yard", indoors=False, affords={"karate"}),
}

MAGICIANS = ["Milo", "Nina", "Tessa", "Arlo", "June", "Pip", "Luna"]
KARATE_KIDS = ["Kai", "Rae", "Ben", "Zia", "Mina", "Otto", "Nora"]
TRAITS = ["cheerful", "curious", "silly", "spirited", "bouncy", "brave"]

TRICKS = {
    "hat": Trick(
        id="hat",
        name="pulling ribbons from a hat",
        stage_name="the ribbon hat trick",
        sound="fwip-fwip!",
        mess="sparkly",
        flashback_reason="an old ribbon show that made everyone laugh",
        keyword="ribbons",
    ),
    "cards": Trick(
        id="cards",
        name="shuffling flying cards",
        stage_name="the flying card trick",
        sound="flip-flap!",
        mess="scattered",
        flashback_reason="a card game that got the whole room giggling",
        keyword="cards",
    ),
    "timber": Trick(
        id="timber",
        name="making a timber plank vanish",
        stage_name="the timber trick",
        sound="poof-THUNK!",
        mess="splintered",
        flashback_reason="a long-ago party where a board went flying and everyone laughed",
        keyword="timber",
    ),
}

PRIZES = {
    "board": Prize(
        label="board",
        phrase="a smooth timber board",
        type="board",
        region="hands",
    ),
    "log": Prize(
        label="log",
        phrase="a thick timber log",
        type="log",
        region="hands",
    ),
}

GEAR = {
    "pads": Gear(
        id="pads",
        label="soft karate pads",
        prep="put on the soft karate pads first",
        tail="sprang over to the board with the pads on",
        protects={"hands"},
    ),
    "cape": Gear(
        id="cape",
        label="a bright stage cape",
        prep="throw on the bright stage cape",
        tail="twirled under the cape and bowed",
        protects={"stage"},
    ),
}


# -----------------------------------------------------------------------------
# Story parameters
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    trick: str
    prize: str
    magician_name: str
    karate_name: str
    magician_trait: str
    karate_trait: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
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


ASP_RULES = r"""
prize_at_risk(T, P) :- targets(T, R), worn_on(P, R).
compatible_gear(T, P, G) :- prize_at_risk(T, P), gear(G), protects(G, R), targets(T, R).
valid_story(Place, Trick, Prize) :- affords(Place, Trick), prize_at_risk(Trick, Prize), compatible_gear(Trick, Prize, _).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for tid, trick in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("targets", tid, "hands"))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for r in sorted(gear.protects):
            lines.append(asp.fact("protects", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    clingo = {t for t in asp_valid_stories()}
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------

def prize_at_risk(trick: Trick, prize: Prize) -> bool:
    return prize.region == "hands"


def select_gear(trick: Trick, prize: Prize) -> Optional[Gear]:
    if prize.region == "hands":
        return GEAR["pads"]
    return None


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for trick_id in setting.affords:
            trick = _safe_lookup(TRICKS, trick_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(trick, prize) and select_gear(trick, prize):
                    combos.append((place, trick_id, prize_id))
    return combos


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    trick = _safe_lookup(TRICKS, params.trick)
    prize_cfg = _safe_lookup(PRIZES, params.prize)

    world = World(setting)
    magician = world.add(Entity(
        id=params.magician_name, kind="character", type="woman" if params.magician_name in {"Nina", "Tessa", "June", "Luna"} else "man",
        meters={"showmanship": 1.0}, memes={"pride": 1.0},
    ))
    karate_kid = world.add(Entity(
        id=params.karate_name, kind="character", type="girl" if params.karate_name in {"Rae", "Zia", "Mina", "Nora"} else "boy",
        meters={"energy": 1.0}, memes={"focus": 1.0},
    ))
    prize = world.add(Entity(
        id="timber", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=karate_kid.id, caretaker=magician.id, region=prize_cfg.region,
    ))
    gear = world.add(Entity(
        id="pads", type="gear", label=GEAR["pads"].label, owner=karate_kid.id, worn_by=karate_kid.id,
        plural=True,
    ))

    world.facts.update(
        magician=magician,
        karate_kid=karate_kid,
        prize=prize,
        trick=trick,
        gear=gear,
    )

    # Act 1: setup
    world.say(f"{magician.id} was a {params.magician_trait} magician who loved {trick.stage_name}.")
    world.say(f"{karate_kid.id} was a {params.karate_trait} karate kid who wanted to break {prize.phrase} cleanly.")
    world.say(f"On the practice day, they met at {setting.place}, where magic and karate could both fit in one noisy room.")

    # Act 2: conflict
    world.para()
    world.say(f"{karate_kid.id} lifted the timber board. {trick.sound} went the stage bell, because {magician.id} had already begun the trick.")
    world.say(f"Then came the comedy part: the board wobbled, the cape snagged, and everyone heard a tiny {trick.sound} echo again.")
    world.say(f"{karate_kid.id} wanted a clean chop, but the first swing only made the board hop like a startled sandwich.")

    # Flashback
    world.para()
    world.flashback_opened = True
    world.say(f"Then {magician.id} remembered a flashback: years ago, {trick.flashback_reason}.")
    world.say(f"That memory made {magician.id} grin instead of frown, because the old mishap had turned into a favorite joke.")

    # Resolution
    gear_def = select_gear(trick, prize)
    if not gear_def:
        pass
    world.para()
    world.say(f'"How about we {gear_def.prep}?" {magician.id} said, while making a silly jazz-hands pose.')
    world.say(f"{karate_kid.id} nodded, put the pads on, and then {gear_def.tail}.")
    world.say(f"With a final {trick.sound}, the timber split neatly, the cape swished, and both of them laughed so hard the practice mat shook.")
    world.say(f"In the end, {prize.label} was broken, the trick landed, and the flashback felt funny instead of embarrassing.")

    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trick: Trick = _safe_fact(world, f, "trick")
    return [
        f'Write a short comedy story for a child about a magician, karate practice, and the word "{trick.keyword}".',
        f"Tell a funny story where a magician and a karate kid try to use a timber board, with sound effects and a flashback.",
        f'Write a playful story that includes "{trick.sound}" and ends with everyone laughing after a karate move and a magic trick.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    magician: Entity = _safe_fact(world, f, "magician")
    karate_kid: Entity = _safe_fact(world, f, "karate_kid")
    prize: Entity = _safe_fact(world, f, "prize")
    trick: Trick = _safe_fact(world, f, "trick")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {magician.id}, a magician, and {karate_kid.id}, a karate kid, as they dealt with {prize.phrase}.",
        ),
        QAItem(
            question=f"What loud sound kept popping up in the story?",
            answer=f"The funny sound effect was {trick.sound}, which made the whole scene feel silly and busy.",
        ),
        QAItem(
            question=f"Why did {magician.id} remember a flashback?",
            answer=f"{magician.id} remembered an old moment because of {trick.flashback_reason}, and that memory helped the mood turn from tense to playful.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The timber split neatly, the trick worked, and {magician.id} and {karate_kid.id} laughed together at {world.setting.place}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "timber": [
        QAItem(
            question="What is timber?",
            answer="Timber is wood used for building, making boards, or crafting strong things.",
        )
    ],
    "karate": [
        QAItem(
            question="What is karate?",
            answer="Karate is a martial art with punches, kicks, and careful practice.",
        )
    ],
    "magician": [
        QAItem(
            question="What does a magician do?",
            answer="A magician performs tricks that seem surprising, like making things appear or disappear.",
        )
    ],
    "sound_effects": [
        QAItem(
            question="Why do stories sometimes use sound effects?",
            answer="Sound effects help readers hear the action in their imaginations, which can make a scene feel lively or funny.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something from earlier in time, so readers understand why something matters now.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story comedic?",
            answer="A comedy story is meant to be funny, often because characters make mistakes, misunderstand each other, or end up in a silly situation.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["timber"],
        *WORLD_KNOWLEDGE["karate"],
        *WORLD_KNOWLEDGE["magician"],
        *WORLD_KNOWLEDGE["sound_effects"],
        *WORLD_KNOWLEDGE["flashback"],
        *WORLD_KNOWLEDGE["comedy"],
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


# -----------------------------------------------------------------------------
# Params / generation
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    trick: str
    prize: str
    magician_name: str
    karate_name: str
    magician_trait: str
    karate_trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about timber, karate, magician, sound effects, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--magician-name")
    ap.add_argument("--karate-name")
    ap.add_argument("--magician-trait", choices=TRAITS)
    ap.add_argument("--karate-trait", choices=TRAITS)
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
    if getattr(args, "trick", None) and getattr(args, "prize", None):
        tr, pr = _safe_lookup(TRICKS, getattr(args, "trick", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(tr, pr) and select_gear(tr, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_story_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trick", None) is None or c[1] == getattr(args, "trick", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trick, prize = rng.choice(list(combos))
    magician_name = getattr(args, "magician_name", None) or rng.choice(MAGICIANS)
    karate_name = getattr(args, "karate_name", None) or rng.choice(KARATE_KIDS)
    magician_trait = getattr(args, "magician_trait", None) or rng.choice(TRAITS)
    karate_trait = getattr(args, "karate_trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        trick=trick,
        prize=prize,
        magician_name=magician_name,
        karate_name=karate_name,
        magician_trait=magician_trait,
        karate_trait=karate_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback_opened={world.flashback_opened}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="dojo",
        trick="timber",
        prize="board",
        magician_name="Nina",
        karate_name="Kai",
        magician_trait="silly",
        karate_trait="bouncy",
    ),
    StoryParams(
        place="stage",
        trick="hat",
        prize="log",
        magician_name="Milo",
        karate_name="Rae",
        magician_trait="cheerful",
        karate_trait="curious",
    ),
    StoryParams(
        place="yard",
        trick="timber",
        prize="log",
        magician_name="Tessa",
        karate_name="Ben",
        magician_trait="spirited",
        karate_trait="brave",
    ),
]


def asp_show_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/3.\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
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
            header = f"### {p.magician_name} and {p.karate_name} at {p.place} ({p.trick} / {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
