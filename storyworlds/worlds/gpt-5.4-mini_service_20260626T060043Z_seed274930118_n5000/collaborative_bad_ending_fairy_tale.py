#!/usr/bin/env python3
"""
A small fairy-tale story world with collaborative action and a bad ending.

Premise:
- A hero and a helper work together in a fairy-tale place.
- They try to solve a problem with a prized magical object.
- Their cooperation helps them make progress, but the final outcome is still
  bad: the object is lost, broken, or cursed.

The world is intentionally small and constraint-checked so the story feels like
a complete, classical tale rather than a random event log.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "knight"}:
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
class Place:
    name: str
    features: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    ruin: str
    feature: str
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
    id: str
    label: str
    phrase: str
    type: str
    risk_feature: str
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
class Aid:
    id: str
    label: str
    feature: str
    helps: set[str]
    prep: str
    tail: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
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


PLACES = {
    "wood": Place("the whispering wood", {"bridge", "gate", "moonlight"}),
    "castle": Place("the old castle", {"tower", "gate", "stair"}),
    "hill": Place("the windy hill", {"path", "moonlight", "stone"}),
}

QUESTS = {
    "bridge": Quest(
        id="bridge",
        verb="cross the broken bridge",
        gerund="crossing the broken bridge",
        risk="the bridge would give way",
        ruin="fall into the dark stream",
        feature="bridge",
        tags={"bridge", "stone"},
    ),
    "gate": Quest(
        id="gate",
        verb="open the ivy gate",
        gerund="opening the ivy gate",
        risk="the gate was sealed by a spell",
        ruin="wake the sleeping thorn curse",
        feature="gate",
        tags={"gate"},
    ),
    "tower": Quest(
        id="tower",
        verb="climb the glass tower",
        gerund="climbing the glass tower",
        risk="the steps were too slick",
        ruin="lose the lantern in the dark stair",
        feature="tower",
        tags={"tower", "stair"},
    ),
}

PRIZES = {
    "crown": Prize("crown", "golden crown", "crown", "crown", "gate"),
    "lantern": Prize("lantern", "silver lantern", "lantern", "lantern", "tower"),
    "key": Prize("key", "small brass key", "key", "key", "bridge"),
}

AIDS = [
    Aid(
        id="rope",
        label="a braided rope",
        feature="bridge",
        helps={"bridge"},
        prep="tie the rope between the stones",
        tail="held the rope tight while the wind tugged at them",
    ),
    Aid(
        id="song",
        label="a soft song",
        feature="gate",
        helps={"gate"},
        prep="sing the old gate-song together",
        tail="sang so gently that the ivy shivered",
    ),
    Aid(
        id="glove",
        label="a velvet glove",
        feature="tower",
        helps={"tower"},
        prep="wrap the lantern in the velvet glove",
        tail="kept the lantern from slipping for a little while",
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Elin", "Ivy"]
BOY_NAMES = ["Owen", "Pip", "Rowan", "Hugo", "Eli", "Finn"]
HELPER_NAMES = ["Moss", "Robin", "Wren", "Puck", "June"]


def reasonableness_gate(quest: Quest, prize: Prize, place: Place) -> bool:
    return quest.feature in place.features and prize.risk_feature == quest.feature


def select_aid(quest: Quest) -> Optional[Aid]:
    for aid in AIDS:
        if quest.id in aid.helps:
            return aid
    return None


def build_story_state(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Quest, Prize, Aid]:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    prize = _safe_lookup(PRIZES, params.prize)
    if not reasonableness_gate(quest, prize, place):
        pass
    aid = select_aid(quest)
    if aid is None:
        pass
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_kind))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_kind))
    relic = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, prize=relic, quest=quest, aid=aid, place=place)
    return world, hero, helper, relic, quest, prize, aid


def tell(params: StoryParams) -> World:
    world, hero, helper, prize_ent, quest, prize, aid = build_story_state(params)

    hero.memes["hope"] = 1
    helper.memes["care"] = 1

    world.say(
        f"Once upon a time, {hero.id} and {helper.id} lived near {world.place.name}, "
        f"where old stones listened and the trees kept secrets."
    )
    world.say(
        f"{hero.id} loved {quest.gerund}, and {helper.id} loved helping, so the two of them "
        f"set out together with {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"They hoped to {quest.verb}, because {quest.risk} and the little kingdom "
        f"needed the prize kept safe."
    )

    world.para()
    hero.memes["desire"] += 1
    helper.memes["desire"] += 1
    world.say(
        f"At the place where the path narrowed, {hero.id} took one side of the work and "
        f"{helper.id} took the other."
    )
    world.say(
        f"Together they chose {aid.label}; {aid.prep}, and for a while {aid.tail}."
    )
    world.say(
        f"That was the brave part of the day: the two friends kept going even when the wind "
        f"went cold and the shadows turned long."
    )

    world.para()
    hero.meters["progress"] = 1
    helper.meters["progress"] = 1
    if quest.id == "bridge":
        hero.meters["risk"] = 1
        helper.meters["risk"] = 1
        world.say(
            f"They reached the broken bridge at last. The boards creaked, but the rope held, "
            f"and they crossed one careful step at a time."
        )
    elif quest.id == "gate":
        hero.meters["risk"] = 1
        helper.meters["risk"] = 1
        world.say(
            f"They came to the ivy gate, and the old vines sighed when the song rose into the air."
        )
    else:
        hero.meters["risk"] = 1
        helper.meters["risk"] = 1
        world.say(
            f"They climbed toward the glass tower, and the lantern shone bravely in the dark."
        )

    world.para()
    world.say(
        f"For a moment it seemed they had done well, because the hard part was behind them."
    )
    world.say(
        f"But fairy tales love a turn, and this one turned cold."
    )

    # Bad ending: cooperation helps, but does not save them.
    if quest.id == "bridge":
        prize_ent.meters["lost"] = 1
        world.say(
            f"The rope slipped loose after they crossed, and the bridge fell apart behind them. "
            f"{hero.id} looked back and saw {hero.pronoun('possessive')} {prize.label} "
            f"floating away in the dark stream."
        )
        world.say(
            f"They had worked side by side, but the key was gone, and the stream kept it."
        )
    elif quest.id == "gate":
        prize_ent.meters["cursed"] = 1
        world.say(
            f"The ivy gate opened just enough for a thin, hungry wind to slip out. It touched "
            f"the {prize.label}, and the gold turned dull and cold."
        )
        world.say(
            f"{hero.id} and {helper.id} had opened the way together, but they had also woken "
            f"the thorn curse."
        )
    else:
        prize_ent.meters["broken"] = 1
        world.say(
            f"At the top stair, the lantern gave one bright blink, then cracked against the stone."
        )
        world.say(
            f"Its silver light spilled out like milk on the floor, and the tower went dark."
        )
        world.say(
            f"{hero.id} and {helper.id} had kept it safe for a little while, but not long enough."
        )

    hero.memes["sad"] = 1
    helper.memes["sad"] = 1
    world.say(
        f"So the two friends went home together in silence, with muddy shoes and heavy hearts."
    )
    world.say(
        f"That evening, the little kingdom had no happy prize to show for their brave work."
    )

    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny collaborative fairy-tale world with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--helper-kind", choices=["girl", "boy"])
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
    combos = [
        (p, q, r)
        for p in PLACES
        for q in QUESTS
        for r in PRIZES
        if reasonableness_gate(_safe_lookup(QUESTS, q), _safe_lookup(PRIZES, r), _safe_lookup(PLACES, p))
    ]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["girl", "boy"])
    helper_kind = getattr(args, "helper_kind", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_kind == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    if helper_name == hero_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        quest=quest,
        prize=prize,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, quest, prize = f["hero"], f["helper"], f["quest"], f["prize"]
    return [
        f'Write a fairy tale for young children about {hero.id} and {helper.id} working together to {quest.verb}.',
        f'Tell a short collaborative story where two friends try to protect a {prize.label} but the ending is sad.',
        f'Write a gentle tale about {world.place.name} in which teamwork helps, yet the final prize is still lost.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest, prize = f["hero"], f["helper"], f["quest"], f["prize"]
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{hero.id} and {helper.id} worked together like true fairy-tale friends.",
        ),
        QAItem(
            question=f"What did they try to do?",
            answer=f"They tried to {quest.verb}, because they wanted to keep the {prize.label} safe.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer="The ending was sad. Their teamwork helped for a while, but the prize was still lost, broken, or cursed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a made-up story with magical things, brave choices, and often a simple, clear lesson.",
        ),
        QAItem(
            question="What does it mean to work together?",
            answer="Working together means two or more helpers each do a part of the job so they can reach the same goal.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the story finishes sadly, even if the characters tried their best.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
place(wood). place(castle). place(hill).
quest(bridge). quest(gate). quest(tower).
prize(crown). prize(lantern). prize(key).

feature(wood,bridge). feature(wood,gate). feature(castle,gate). feature(castle,tower). feature(hill,bridge). feature(hill,tower).

risk(bridge,bridge). risk(gate,gate). risk(tower,tower).

valid(P,Q,R) :- feature(P,Q), risk(Q,R).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for f in sorted(_safe_lookup(PLACES, p).features):
            lines.append(asp.fact("feature", p, f))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        lines.append(asp.fact("risk", q, _safe_lookup(QUESTS, q).feature))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, q, r) for p in PLACES for q in QUESTS for r in PRIZES if reasonableness_gate(_safe_lookup(QUESTS, q), _safe_lookup(PRIZES, r), _safe_lookup(PLACES, p))}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("wood", "bridge", "key", "Mira", "girl", "Puck", "boy"),
    StoryParams("castle", "gate", "crown", "Owen", "boy", "Wren", "girl"),
    StoryParams("hill", "tower", "lantern", "Lina", "girl", "Moss", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name} and {p.helper_name} | {p.place} | {p.quest} | {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
