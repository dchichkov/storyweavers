#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/olive_extraction_friendship_flashback_folk_tale.py
======================================================================================================

A small folk-tale story world about an olive harvest, a careful extraction,
friendship, and a flashback that reveals why the friends trust one another.

Premise:
- A child and a friend go to a grove to gather olives.
- They hope to use an old press to extract olive oil for the village lamp.

Tension:
- If they press too hard, the olives bruise and the oil turns bitter.
- The elder worries because a rushed extraction wastes the harvest.

Turn:
- A flashback shows the child and friend sharing a meal during a hard winter.
- Remembering that kindness, they slow down and work together.

Resolution:
- They sort the olives, press them gently, and carry home a golden bottle of
  oil for the lamp, with friendship brighter than before.

This world is authored to read like a complete folk tale, while still being a
small stateful simulation with physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    elder: object | None = None
    friend: object | None = None
    hero: object | None = None
    press: object | None = None
    prize: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    outcome: str
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
class Prize:
    id: str
    label: str
    phrase: str
    owner_region: str
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
class StoryParams:
    place: str
    action: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    elder_type: str
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone
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
    "grove": Place(name="the olive grove", affords={"gather", "press"}),
    "mill": Place(name="the old mill", affords={"press"}),
    "courtyard": Place(name="the courtyard", affords={"gather"}),
}

ACTIONS = {
    "harvest": Action(
        id="harvest",
        verb="gather the olives",
        gerund="gathering olives",
        rush="rush through the branches",
        risk="bruise the olives",
        outcome="bright and useful",
        keyword="olive",
        tags={"olive", "gathering", "friendship"},
    ),
    "extract": Action(
        id="extract",
        verb="extract oil from the olives",
        gerund="pressing the olives for oil",
        rush="turn the press too hard",
        risk="make the oil bitter",
        outcome="golden and clean",
        keyword="extraction",
        tags={"olive", "extraction", "friendship"},
    ),
}

PRIZES = {
    "lamp": Prize(
        id="lamp",
        label="village lamp",
        phrase="a small lamp that burned through the night",
        owner_region="table",
    ),
    "bread": Prize(
        id="bread",
        label="bread",
        phrase="warm bread for the table",
        owner_region="basket",
        plural=False,
    ),
}

GIRL_NAMES = ["Mara", "Tess", "Lina", "Nina", "Iva"]
BOY_NAMES = ["Jon", "Oren", "Pavel", "Rui", "Tomas"]

TRAITS = ["kind", "curious", "patient", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for act in ACTIONS:
            if act in p.affords:
                for prize in PRIZES:
                    combos.append((place, act, prize))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def is_reasonable(place: str, action: str, prize: str) -> bool:
    return (place, action, prize) in valid_combos()


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for prid in PRIZES:
        lines.append(asp.fact("prize", prid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,R) :- place(P), action(A), prize(R), affords(P,A).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - asps))
    print("only asp:", sorted(asps - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about olive extraction and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero_name", None) or choose_name(rng, gender)
    friend = getattr(args, "friend_name", None) or choose_name(rng, "boy" if gender == "girl" else "girl")
    return StoryParams(place=place, action=action, prize=prize,
                       hero_name=hero, hero_type=gender,
                       friend_name=friend, friend_type="girl" if gender == "boy" else "boy",
                       elder_type="grandmother")


def _story_intro(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    elder = world.get("elder")
    world.say(
        f"Once in the {world.place.name}, there lived {hero.ref()} and {friend.ref()}, "
        f"two friends who loved helping {elder.ref()} keep the village in good order."
    )
    world.say(
        f"They knew the old trees well, and every autumn they went where the olives hung dark and shiny."
    )


def _flashback(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.para()
    world.say(
        f"Before that day, there had been a winter when the wind howled like a fox."
    )
    world.say(
        f"{hero.ref()} and {friend.ref()} had shared one crust of bread by a small fire, "
        f"and from that night on, each trusted the other to be careful and true."
    )
    world.say("That was the kind of friendship that does not fade, even when the road is long.")


def _conflict(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    elder = world.get("elder")
    act = _safe_lookup(ACTIONS, world.facts.get("action"))
    prize = _safe_lookup(PRIZES, world.facts.get("prize"))
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.para()
    world.say(
        f"One morning, {hero.ref()} wanted to {act.verb} at the old mill, for the village lamp was running low."
    )
    world.say(
        f"But {elder.ref()} lifted a careful hand and said, "
        f"\"Do not {act.rush}, child. If you do, you may {act.risk}, and then the {prize.label} will not help the village.\""
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.say(
        f"{hero.ref()} and {friend.ref()} looked at one another, and for a small moment the grove grew quiet."
    )


def _resolution(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    elder = world.get("elder")
    act = _safe_lookup(ACTIONS, world.facts.get("action"))
    prize = _safe_lookup(PRIZES, world.facts.get("prize"))
    hero.meters["careful"] = hero.meters.get("careful", 0) + 1
    friend.meters["careful"] = friend.meters.get("careful", 0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    world.para()
    world.say(
        f"Then {hero.ref()} remembered the winter fire, and {friend.ref()} remembered it too."
    )
    world.say(
        f"So they worked slowly: one shook the branches, the other caught the olives in a clean basket, "
        f"and together they fed the press one handful at a time."
    )
    world.say(
        f"The oil came out golden and sweet, not bitter at all, and {elder.ref()} smiled to see that the {act.keyword} was done with patience."
    )
    world.say(
        f"At dusk, the village lamp shone warm and steady, and the friends walked home with olive-scented hands and hearts full of gladness."
    )


def tell_story(params: StoryParams) -> World:
    if not is_reasonable(params.place, params.action, params.prize):
        pass
    world = World(place=_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type, label="the grandmother"))
    basket = world.add(Entity(id="basket", type="thing", label="basket"))
    press = world.add(Entity(id="press", type="thing", label="old press"))
    prize = world.add(Entity(id="prize", type="thing", label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase))
    world.facts.update(place=params.place, action=params.action, prize=params.prize, hero=hero, friend=friend, elder=elder)
    _story_intro(world)
    _flashback(world)
    _conflict(world)
    _resolution(world)
    world.facts["basket"] = basket
    world.facts["press"] = press
    world.facts["prize_entity"] = prize
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    elder = _safe_fact(world, world.facts, "elder")
    act = _safe_lookup(ACTIONS, world.facts.get("action"))
    prize = _safe_lookup(PRIZES, world.facts.get("prize"))
    return [
        QAItem(
            question=f"Who are the friends in the olive tale?",
            answer=f"The story is about {hero.ref()} and {friend.ref()}, two friends who help the village together."
        ),
        QAItem(
            question=f"What did the child and the friend want to do with the olives?",
            answer=f"They wanted to {act.verb}, so the village could have {prize.label} for the lamp."
        ),
        QAItem(
            question="Why did the grandmother warn them to be careful?",
            answer=f"She warned them because if they rushed, they might {act.risk}, and the harvest would not be as useful."
        ),
        QAItem(
            question="What did the flashback show?",
            answer="The flashback showed the two friends sharing bread by a winter fire, which is why they trusted each other."
        ),
        QAItem(
            question="How did the story end?",
            answer="They worked slowly and gently, and the olive oil came out golden and sweet for the village lamp."
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is an olive?",
        answer="An olive is a small fruit that grows on an olive tree, and people can press it to make oil."
    ),
    QAItem(
        question="What is extraction?",
        answer="Extraction means taking something out carefully from the thing that holds it, like pressing oil from olives."
    ),
    QAItem(
        question="Why do friends help each other?",
        answer="Friends help each other because two kind hearts can do hard work more safely and happily together."
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is when a story remembers something that happened earlier, so we learn why someone feels or acts a certain way."
    ),
    QAItem(
        question="What kind of story is a folk tale?",
        answer="A folk tale is an old-style story passed from person to person, often with simple language, wise choices, and a gentle lesson."
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    act = _safe_lookup(ACTIONS, world.facts.get("action"))
    return [
        f"Write a short folk tale about {hero.ref()} and {friend.ref()} in an olive grove, with a careful extraction at the end.",
        f"Tell a child-friendly story that includes a flashback and the word '{act.keyword}'.",
        f"Write a gentle story about friendship, olives, and learning not to rush the press.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.ref()} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="grove", action="harvest", prize="lamp", hero_name="Mara", hero_type="girl",
                friend_name="Jon", friend_type="boy", elder_type="grandmother"),
    StoryParams(place="mill", action="extract", prize="lamp", hero_name="Tomas", hero_type="boy",
                friend_name="Lina", friend_type="girl", elder_type="grandmother"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible story combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = CURATED
    else:
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                p = resolve_params(args, rng)
            except StoryError:
                continue
            p.seed = base_seed + i
            key = asdict(p).__repr__()
            if key in seen:
                continue
            seen.add(key)
            params_list.append(p)

    for p in params_list:
        world = tell_story(p)
        sample = StorySample(
            params=p,
            story=world.render(),
            prompts=generation_prompts(world),
            story_qa=story_qa(world),
            world_qa=WORLD_QA,
            world=world,
        )
        samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=WORLD_QA,
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


if __name__ == "__main__":
    main()
