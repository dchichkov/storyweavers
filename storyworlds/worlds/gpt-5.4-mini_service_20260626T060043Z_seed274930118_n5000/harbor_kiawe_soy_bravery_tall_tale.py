#!/usr/bin/env python3
"""
Story world: Harbor Bravery Tall Tale

A small, standalone story simulation inspired by a tall-tale harbor legend:
a child at the harbor wants to prove bravery, but the wind, the tide, and a
sudden mishap with soy sauce force a clever, courageous turn.

The simulation keeps a concrete world model with meters and memes:
- physical meters: wet, slippery, laden, carried, steady, stormy
- emotional memes: bravery, worry, pride, relief, wonder

The seed words are woven into the world:
- harbor
- kiawe
- soy

The story style aims for a child-facing tall tale: vivid, concrete, slightly
exaggerated, but still state-driven and causal.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    soy: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.meme(key) + amount

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the harbor"
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    helper: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"tide", "storm", "cargo"}),
    "dock": Setting(place="the dock", affords={"tide", "cargo"}),
    "quay": Setting(place="the quay", affords={"storm", "tide"}),
}

PRIZES = {
    "hat": ObjectCfg("hat", "straw hat", "a straw hat with a ribbon", "head"),
    "cloak": ObjectCfg("cloak", "blue cloak", "a blue cloak that snapped like a sail", "torso"),
    "boots": ObjectCfg("boots", "sea boots", "tall sea boots", "feet", plural=True),
    "basket": ObjectCfg("basket", "market basket", "a market basket full of bright things", "hands"),
}

HELPERS = {
    "kiawe": {
        "label": "kiawe pole",
        "phrase": "a smooth kiawe pole",
        "method": "braced the pole against the dock and leaned into the wind",
        "fix": "used the kiawe pole to keep the basket high and dry",
    },
    "rope": {
        "label": "braided rope",
        "phrase": "a braided rope looped like a lasso",
        "method": "tied the line to the post and made a brave anchor",
        "fix": "used the rope to steady the load",
    },
}

ACTS = {
    "tide": {
        "verb": "cross the harbor path",
        "gerund": "crossing the harbor path",
        "rush": "dash across the wet boards",
        "mess": "wet",
        "soil": "sprayed and slick",
        "zone": {"feet", "hands"},
        "trouble": "the tide could splash the prize and make it slippery",
    },
    "storm": {
        "verb": "carry the prize through the storm wind",
        "gerund": "carrying the prize through the storm wind",
        "rush": "run with the prize into the wind",
        "mess": "stormy",
        "soil": "blown crooked and damp",
        "zone": {"torso", "hands"},
        "trouble": "the wind could toss the prize and tangle every corner",
    },
    "cargo": {
        "verb": "haul cargo by the quay",
        "gerund": "hauling cargo by the quay",
        "rush": "heave the load too fast",
        "mess": "laden",
        "soil": "worn and salty",
        "zone": {"hands", "torso"},
        "trouble": "the cargo could scrape the prize and leave it battered",
    },
}

NAMES = {
    "girl": ["Kia", "Mina", "Lani", "Nora", "Meli"],
    "boy": ["Kai", "Toma", "Eli", "Pono", "Niko"],
}
TRAITS = ["bold", "brave", "bright-eyed", "stubborn", "cheerful", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if _safe_lookup(ACTS, act)["zone"].intersection({prize.region}):
                    combos.append((place, act, prize_id))
    return combos


def _story_word(prize: ObjectCfg) -> str:
    return prize.label


def _prize_phrase(prize: ObjectCfg) -> str:
    return prize.phrase


def _hero_desc(hero: Entity, trait: str) -> str:
    return f"a {trait} {hero.type} named {hero.id}"


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    act = _safe_lookup(ACTS, params.prize) if params.prize in ACTS else None
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"steady": 1.0},
        memes={"bravery": 1.0},
    ))
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="elder",
        label=helper_cfg["label"],
        phrase=helper_cfg["phrase"],
        meters={"steady": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=_safe_lookup(PRIZES, params.prize).label,
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id if _safe_lookup(PRIZES, params.prize).region != "hands" else None,
        carried_by=hero.id if _safe_lookup(PRIZES, params.prize).region == "hands" else None,
        plural=_safe_lookup(PRIZES, params.prize).plural,
        meters={"clean": 1.0},
    ))

    act = _safe_lookup(ACTS, params.place if params.place in ACTS else "tide")

    return world


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"steady": 1.0},
        memes={"bravery": 1.0, "wonder": 0.5},
    ))
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="elder",
        label=helper_cfg["label"],
        phrase=helper_cfg["phrase"],
        meters={"steady": 1.0},
        memes={"calm": 1.0},
    ))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id if prize_cfg.region != "hands" else None,
        carried_by=hero.id if prize_cfg.region == "hands" else None,
        plural=prize_cfg.plural,
        meters={"clean": 1.0},
    ))
    act = _safe_lookup(ACTS, params.prize if params.prize in ACTS else "tide")

    # Better: choose an actual act using place.
    act_key = random.choice(sorted(world.setting.affords))
    act = _safe_lookup(ACTS, act_key)

    world.say(
        f"At {world.setting.place}, {hero.id} was {_hero_desc(hero, random.choice(TRAITS))}, "
        f"and everyone said {hero.id} had more bravery than a thundercloud has rain."
    )
    world.say(
        f"{hero.id} loved the harbor best when the gulls wheeled over the water like loose white ribbons, "
        f"and {hero.pronoun('possessive')} {prize.label} shone like a tiny flag."
    )

    world.para()
    world.say(
        f"One day, a long wind came skipping between the pilings, and {hero.id} wanted to {act['verb']}."
    )
    world.say(
        f"But {helper.label} pointed at the water and said, "
        f'"That wind could leave {hero.pronoun("possessive")} {prize.label} {act["soil"]}."'
    )
    hero.add_meme("worry", 1.0)
    world.say(
        f"{hero.id} took a breath as big as a sail and said {hero.pronoun('subject')} would be brave anyway."
    )

    # Physical consequence.
    hero.add_meter(act["mess"], 1.0)
    if prize.region in act["zone"]:
        prize.add_meter("wet", 1.0)
        prize.add_meter("messy", 1.0)

    world.para()
    world.say(
        f"{hero.id} stepped onto the boards, and the harbor answered with a slap of spray and a whistle of wind."
    )
    if prize.meter("messy") >= THRESHOLD:
        world.say(
            f"The first splash reached {hero.pronoun('possessive')} {prize.label}, and it went {act['soil']} in a blink."
        )
        hero.add_meme("pride", 0.5)
        hero.add_meme("worry", 0.5)
    world.say(
        f"Then {helper.id} held up a {helper_cfg['label']} and called, "
        f'"Bravery is not rushing, child. Bravery is choosing the good way through."'
    )

    # Turn: soy appears as the practical complication and comic detail.
    soy = world.add(Entity(
        id="soy",
        kind="thing",
        type="bottle",
        label="soy sauce bottle",
        phrase="a small soy bottle tied with twine",
        meters={"full": 1.0},
    ))
    world.say(
        f"At that very moment, a fishmonger sent over a crate with a soy bottle, and the bottle began to wobble like a sleepy gull."
    )
    if act_key == "cargo":
        world.say(
            f"{hero.id} caught it fast, but a dark ribbon of soy marked the boards."
        )
    else:
        world.say(
            f"{hero.id} caught it fast before it could tip, and the crowd blinked because the quick catch was braver than any boast."
        )
    hero.add_meme("bravery", 1.0)
    hero.add_meme("pride", 1.0)

    world.para()
    world.say(
        f"With the {helper.label} in hand and the soy bottle safe, {hero.id} climbed the last slick plank, "
        f"then used {helper_cfg['method']}."
    )
    world.say(
        f"That kept {hero.pronoun('possessive')} {prize.label} high, and the tide could only sigh below like a sleepy drum."
    )
    if prize.meter("messy") >= THRESHOLD:
        world.say(
            f"The prize was already spotted from the first splash, but now it stayed safe from getting any worse."
        )
    else:
        world.say(
            f"The prize stayed clean as a gull feather, because the helper's clever trick put the harbor between danger and disaster."
        )

    world.para()
    world.say(
        f"In the end, the wind ran out of puff, the water turned silver, and {hero.id} stood tall enough to seem like a lighthouse in little shoes."
    )
    world.say(
        f"{hero.id} laughed, the helper laughed, and even the soy bottle sat quiet, because the bravest thing at the harbor was using a smart hand instead of a reckless dash."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        soy=soy,
        act=act,
        act_key=act_key,
        place=params.place,
        params=params,
        prize_cfg=prize_cfg,
        helper_cfg=helper_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    act = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "act")
    return [
        f'Write a tall tale for a young child about bravery at the harbor, with kiawe, soy, and a {prize.label}.',
        f"Tell a story where {hero.id} wants to {act['verb']} but learns a brave, careful way to keep a {prize.label} safe.",
        f'Write a harbor adventure where the words "harbor", "kiawe", and "soy" all appear, and the ending shows what bravery changed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    act = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "act")
    act_key = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "act_key")
    qa = [
        QAItem(
            question=f"Who was the story about at the harbor?",
            answer=f"It was about {hero.id}, a child with plenty of bravery, and the helper called {helper.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the wind caused trouble?",
            answer=f"{hero.id} wanted to {act['verb']}.",
        ),
        QAItem(
            question=f"Why did the helper worry about the {prize.label}?",
            answer=f"The helper worried because the tide and wind at the harbor could leave it {act['soil']}.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay brave without making a bigger mess?",
            answer=f"The {helper.label} and the careful plan helped {hero.id} stay brave and keep the {prize.label} safe.",
        ),
        QAItem(
            question=f"What happened with the soy bottle?",
            answer="It wobbled like it might spill, but {0} caught it before it could make a fuss.".format(hero.id),
        ),
    ]
    if act_key == "cargo":
        qa.append(QAItem(
            question="What changed by the end of the story?",
            answer=f"{hero.id} learned that real bravery can be steady and careful, not just fast, and the {prize.label} stayed safer because of it.",
        ))
    else:
        qa.append(QAItem(
            question="What changed by the end of the story?",
            answer=f"{hero.id} learned that bravery can mean listening, using help, and choosing the safer way through the harbor.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harbor?",
            answer="A harbor is a place near the water where boats can stop safely, and people can load, unload, or watch the tide.",
        ),
        QAItem(
            question="What is kiawe wood?",
            answer="Kiawe is a strong tree that grows in warm places, and its wood can be tough and useful for poles or fire.",
        ),
        QAItem(
            question="What is soy sauce?",
            answer="Soy sauce is a dark, salty liquid used to flavor food. It can spill easily and make a sticky mess.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something hard or scary while still trying to do the right thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(harbor). place(dock). place(quay).
affords(harbor,tide). affords(harbor,storm). affords(harbor,cargo).
affords(dock,tide). affords(dock,cargo).
affords(quay,storm). affords(quay,tide).

activity(tide). activity(storm). activity(cargo).
mess_of(tide,wet). mess_of(storm,stormy). mess_of(cargo,laden).

prize(hat). prize(cloak). prize(boots). prize(basket).
worn_on(hat,head). worn_on(cloak,torso). worn_on(boots,feet). worn_on(basket,hands).

gear(kiawe_pole). gear(rope).
covers(kiawe_pole,hands). covers(kiawe_pole,torso). guards(kiawe_pole,wet). guards(kiawe_pole,stormy).
covers(rope,hands). covers(rope,torso). guards(rope,laden). guards(rope,stormy).

splashes(tide,feet). splashes(tide,hands).
splashes(storm,torso). splashes(storm,hands).
splashes(cargo,hands). splashes(cargo,torso).

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act, data in ACTS.items():
        lines.append(asp.fact("activity", act))
        lines.append(asp.fact("mess_of", act, data["mess"]))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    lines.append(asp.fact("gear", "kiawe_pole"))
    lines.append(asp.fact("gear", "rope"))
    lines.append(asp.fact("covers", "kiawe_pole", "hands"))
    lines.append(asp.fact("covers", "kiawe_pole", "torso"))
    lines.append(asp.fact("guards", "kiawe_pole", "wet"))
    lines.append(asp.fact("guards", "kiawe_pole", "stormy"))
    lines.append(asp.fact("covers", "rope", "hands"))
    lines.append(asp.fact("covers", "rope", "torso"))
    lines.append(asp.fact("guards", "rope", "laden"))
    lines.append(asp.fact("guards", "rope", "stormy"))
    lines.append(asp.fact("splashes", "tide", "feet"))
    lines.append(asp.fact("splashes", "tide", "hands"))
    lines.append(asp.fact("splashes", "storm", "torso"))
    lines.append(asp.fact("splashes", "storm", "hands"))
    lines.append(asp.fact("splashes", "cargo", "hands"))
    lines.append(asp.fact("splashes", "cargo", "torso"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_py() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize.region in _safe_lookup(ACTS, act)["zone"]:
                    combos.append((place, act, prize_id))
    return sorted(combos)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos_py())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Harbor bravery tall tale storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) not in PRIZES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None), "tide", getattr(args, "prize", None)) not in valid_combos_py() and \
           (getattr(args, "place", None), "storm", getattr(args, "prize", None)) not in valid_combos_py() and \
           (getattr(args, "place", None), "cargo", getattr(args, "prize", None)) not in valid_combos_py():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos_py()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, _, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, prize=prize, name=name, gender=gender, helper=helper)


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
    StoryParams(place="harbor", prize="cloak", name="Kia", gender="girl", helper="kiawe"),
    StoryParams(place="dock", prize="boots", name="Kai", gender="boy", helper="rope"),
    StoryParams(place="quay", prize="basket", name="Lani", gender="girl", helper="kiawe"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for item in vals:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i - 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.prize} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
