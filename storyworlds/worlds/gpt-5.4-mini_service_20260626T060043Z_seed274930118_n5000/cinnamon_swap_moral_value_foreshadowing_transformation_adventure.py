#!/usr/bin/env python3
"""
A standalone storyworld for a small adventure about a cinnamon swap,
foreshadowing, moral value, and transformation.

Seed tale premise:
A child wants to borrow a cinnamon bun token for a festival map. A tempting swap
promises a shortcut, but it may break trust. The story follows the warning,
the choice, and a transformation from selfish hurry to honest help.
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

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
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


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
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
class QuestItem:
    label: str
    phrase: str
    type: str
    value: str
    risk: str
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
class SwapOffer:
    id: str
    label: str
    phrase: str
    covers: set[str]
    protects: set[str]
    trade_line: str
    ending_line: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    item: str
    offer: str
    name: str
    gender: str
    helper: str
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


PLACES = {
    "market": Place("the market", affords={"swap", "search"}),
    "cabin": Place("the cabin", affords={"swap"}),
    "festival": Place("the festival lane", affords={"swap", "search"}),
    "garden": Place("the garden stall", affords={"swap", "search"}),
}

ITEMS = {
    "cinnamon": QuestItem(
        label="cinnamon stick",
        phrase="a warm cinnamon stick",
        type="cinnamon stick",
        value="special",
        risk="missing",
        region="hand",
    ),
    "bun": QuestItem(
        label="cinnamon bun",
        phrase="a glazed cinnamon bun",
        type="bun",
        value="sweet",
        risk="squished",
        region="hand",
    ),
}

OFFERS = [
    SwapOffer(
        id="map",
        label="paper map",
        phrase="a paper map with a shortcut",
        covers={"hand"},
        protects={"missing"},
        trade_line="trade the cinnamon stick for a shortcut map",
        ending_line="followed the map and reached the gate in time",
    ),
    SwapOffer(
        id="lantern",
        label="small lantern",
        phrase="a small lantern for the dark path",
        covers={"hand"},
        protects={"missing"},
        trade_line="swap the cinnamon bun for a lantern",
        ending_line="carried the lantern and found the path home",
    ),
    SwapOffer(
        id="token",
        label="festival token",
        phrase="a festival token stamped with a star",
        covers={"hand"},
        protects={"squished"},
        trade_line="swap the bun for a festival token",
        ending_line="kept the token safe and still had a sweet snack later",
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Aya"]
BOY_NAMES = ["Eli", "Jon", "Arlo", "Milo", "Pax"]
TRAITS = ["curious", "brave", "hurried", "careful", "stubborn"]


def reasonableness(item: QuestItem, offer: SwapOffer) -> bool:
    return item.risk in offer.protects and "hand" in offer.covers


ASP_RULES = r"""
item_at_risk(I,O) :- item(I), offer(O), risk(I,R), protects(O,R).
compatible(I,O) :- item_at_risk(I,O), covers(O,hand).
valid_story(P,I,O) :- place(P), affords(P,swap), compatible(I,O).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, item.risk))
    for off in OFFERS:
        lines.append(asp.fact("offer", off.id))
        for r in sorted(off.protects):
            lines.append(asp.fact("protects", off.id, r))
        for c in sorted(off.covers):
            lines.append(asp.fact("covers", off.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PLACES:
        for iid, item in ITEMS.items():
            for off in OFFERS:
                if reasonableness(item, off):
                    out.append((pid, iid, off.id))
    return sorted(set(out))


def _story_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "item", None) and getattr(args, "offer", None):
        item, off = _safe_lookup(ITEMS, getattr(args, "item", None)), next(o for o in OFFERS if o.id == getattr(args, "offer", None))
        if not reasonableness(item, off):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
        and (getattr(args, "offer", None) is None or c[2] == getattr(args, "offer", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, offer = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or _story_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandmother", "older sibling"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, offer=offer, name=name, gender=gender, helper=helper, trait=trait)


def intro(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'curious')} {hero.type} who loved the smell of cinnamon."
    )
    world.say(
        f"At {world.place.name}, {helper.label} gave {hero.pronoun('object')} {item.phrase} to carry carefully."
    )
    world.say(
        f"{hero.id} liked how warm and special the cinnamon felt, as if it could guide the whole day."
    )


def foreshadow(world: World, hero: Entity, item: Entity, offer: SwapOffer) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"Near the lane, a traveler held up {offer.phrase} and smiled at {hero.id}."
    )
    world.say(
        f'"If you trade away the {item.label}, you can go faster," the traveler said.'
    )
    world.say(
        f"{hero.id} noticed the shortcut, but {hero.pronoun('possessive')} fingers tightened around the cinnamon."
    )


def warn(world: World, helper: Entity, hero: Entity, item: Entity, offer: SwapOffer) -> None:
    world.say(
        f"{helper.label.capitalize()} glanced at the offer and said, "
        f'"A fast swap can feel clever, but it can also leave you with nothing steady to trust."'
    )
    world.say(
        f"{helper.label.capitalize()} pointed at the cinnamon and reminded {hero.id} that true value is not only about speed."
    )


def choose(world: World, hero: Entity, item: Entity, offer: SwapOffer) -> None:
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} wanted the shortcut and the safe treasure at the same time."
    )
    world.say(
        f"At last, {hero.id} chose to keep the {item.label} and use {offer.trade_line.replace('swap ', 'ask about ')} instead."
    )


def transform(world: World, hero: Entity, helper: Entity, item: Entity, offer: SwapOffer) -> None:
    hero.memes["wisdom"] += 1
    hero.memes["conflict"] = 0.0
    hero.meters["trust"] += 1
    world.say(
        f"{hero.id} offered the traveler a fair question instead of a hasty trade."
    )
    world.say(
        f"The traveler admired that choice and gave a honest clue, so {hero.id} could keep the cinnamon and still move ahead."
    )
    world.say(
        f"By the end, {hero.id} felt taller inside, as if the careful choice had turned into a new kind of courage."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, because the cinnamon stayed with the right owner and the path still opened."
    )


def tell(place: Place, item_cfg: QuestItem, offer: SwapOffer, hero_name: str, gender: str, helper_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, memes={"trait": trait}))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label=f"the {helper_name}"))
    item = world.add(Entity(id="Item", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    item.worn_by = hero.id

    intro(world, hero, helper, item)
    world.para()
    foreshadow(world, hero, item, offer)
    warn(world, helper, hero, item, offer)
    choose(world, hero, item, offer)
    world.para()
    transform(world, hero, helper, item, offer)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        item_cfg=item_cfg,
        offer=offer,
        trait=trait,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short adventure story for a young child that includes cinnamon and a tempting swap.',
        f"Tell a story where {f['hero'].id} considers a {f['offer'].label} swap at {f['place'].name} but learns a moral lesson about honesty.",
        f"Write a child-friendly adventure where cinnamon matters, a warning is foreshadowed, and the ending shows a transformation in choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, item, offer = f["hero"], f["helper"], f["item"], f["offer"]
    return [
        QAItem(
            question=f"Who was the story mainly about at {f['place'].name}?",
            answer=f"The story was mainly about {hero.id}, who was carrying the {item.label} and learning how to choose wisely.",
        ),
        QAItem(
            question=f"What tempting thing did {hero.id} see during the adventure?",
            answer=f"{hero.id} saw {offer.phrase}, which looked useful but would have pulled attention away from the cinnamon.",
        ),
        QAItem(
            question=f"What did {helper.label} warn {hero.id} about?",
            answer=f"{helper.label.capitalize()} warned that a fast swap can feel clever but still leave someone with a poorer choice and a weaker trust.",
        ),
        QAItem(
            question=f"What changed in {hero.id} by the end?",
            answer=f"{hero.id} changed from being tempted by the shortcut to acting with honesty and care, which is the story's moral value and transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cinnamon?",
            answer="Cinnamon is a fragrant spice from the bark of a tree. People use it to make food smell warm and sweet.",
        ),
        QAItem(
            question="What does a swap mean?",
            answer="A swap means two sides trade things. A good swap should be fair so nobody ends up cheated.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and choosing what is fair, even when a faster choice looks tempting.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind of good rule for living, like honesty, kindness, or fairness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
item_risky(I,O) :- item(I), offer(O), risk(I,R), protects(O,R).
valid(P,I,O) :- place(P), affords(P,swap), item_risky(I,O).
"""


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about cinnamon, a swap, and a moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--offer", choices=[o.id for o in OFFERS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "older sibling"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ITEMS, params.item), next(o for o in OFFERS if o.id == params.offer),
                 params.name, params.gender, params.helper, params.trait)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "item", None) and getattr(args, "offer", None):
        item = _safe_lookup(ITEMS, getattr(args, "item", None))
        offer = next(o for o in OFFERS if o.id == getattr(args, "offer", None))
        if not reasonableness(item, offer):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
        and (getattr(args, "offer", None) is None or c[2] == getattr(args, "offer", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, offer = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or _story_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandmother", "older sibling"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, offer=offer, name=name, gender=gender, helper=helper, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, offer) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("market", "cinnamon", "map", "Mira", "girl", "mother", "curious"),
            StoryParams("festival", "bun", "token", "Eli", "boy", "father", "brave"),
            StoryParams("garden", "cinnamon", "lantern", "Tessa", "girl", "grandmother", "careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
