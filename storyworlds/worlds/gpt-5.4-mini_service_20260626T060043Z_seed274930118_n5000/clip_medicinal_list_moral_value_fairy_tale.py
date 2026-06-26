#!/usr/bin/env python3
"""
A small fairy-tale story world about a medicinal list, a tiny clip, and a moral
choice.

The seed story premise:
A young helper in a fairy-tale cottage finds a clip holding together a medicinal
list. The helper wants to borrow the list to heal a friend, but a careless act
could scatter the papers and mix up the remedies. A wise elder teaches that
care, honesty, and sharing with permission matter more than rushing. The helper
uses the clip, keeps the list tidy, and delivers the right medicine.

This script turns that premise into a compact world model with:
- physical meters: tidiness, order, damage, warmth, freshness
- emotional memes: worry, pride, kindness, trust, relief
- a moral value: keeping promises and treating useful things with care
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clip: object | None = None
    cup: object | None = None
    elder: object | None = None
    friend: object | None = None
    helper: object | None = None
    herb: object | None = None
    lst: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "maiden", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "page", "prince"}:
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
    place: str = "the herb cottage"
    affords: set[str] = field(default_factory=set)
    setting: object | None = None
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    harm: str
    tags: set[str] = field(default_factory=set)
    action: object | None = None
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
class Moral:
    value: str
    lesson: str
    MORAL_VALUE: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.action: Optional[Action] = None

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.action = self.action
        return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        if world.action is None:
            break
        act = world.action
        if act.id == "rush_scatter":
            helper = world.get("Helper")
            clip = world.get("Clip")
            lst = world.get("List")
            sig = ("scatter",)
            if sig not in world.fired and helper.memes.get("worry", 0.0) >= THRESHOLD:
                world.fired.add(sig)
                clip.meters["held"] = 0
                lst.meters["tidy"] = max(0.0, lst.meters.get("tidy", 0.0) - 1)
                out.append("The papers trembled, but the clip held the medicinal list together.")
                changed = True
        if act.id == "careful_clip":
            clip = world.get("Clip")
            lst = world.get("List")
            sig = ("care",)
            if sig not in world.fired:
                world.fired.add(sig)
                clip.meters["held"] = 1
                lst.meters["tidy"] = 2
                out.append("The clip kept the medicinal list neat and easy to read.")
                changed = True
        if act.id == "wrong_leaves":
            herb = world.get("Herb")
            sig = ("wrong",)
            if sig not in world.fired:
                world.fired.add(sig)
                herb.meters["wrong"] = 1
                out.append("A wrong leaf would have made the brew less kind to the sick child.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world() -> World:
    setting = Setting(place="the herb cottage", affords={"sort_medicines", "carry_list", "brew_tea"})
    world = World(setting)

    helper = world.add(Entity(id="Helper", kind="character", type="girl", label="little helper"))
    elder = world.add(Entity(id="Elder", kind="character", type="woman", label="wise elder"))
    friend = world.add(Entity(id="Friend", kind="character", type="boy", label="sick friend"))

    clip = world.add(Entity(id="Clip", type="clip", label="silver clip", phrase="a tiny silver clip"))
    lst = world.add(Entity(id="List", type="list", label="medicinal list", phrase="a medicinal list of herbs and teas"))
    herb = world.add(Entity(id="Herb", type="herb", label="mint leaf", phrase="a mint leaf"))
    cup = world.add(Entity(id="Cup", type="cup", label="warm cup", phrase="a warm cup of tea"))

    clip.meters["held"] = 1
    lst.meters["tidy"] = 1
    herb.meters["fresh"] = 1
    helper.memes["kindness"] = 1
    elder.memes["trust"] = 1
    friend.meters["warmth"] = 0
    return world


def tell(world: World) -> World:
    helper = world.get("Helper")
    elder = world.get("Elder")
    friend = world.get("Friend")
    clip = world.get("Clip")
    lst = world.get("List")
    herb = world.get("Herb")
    cup = world.get("Cup")

    world.say(
        "Once in a little cottage at the edge of the wood, there lived a gentle helper "
        "who loved learning the names of medicinal herbs."
    )
    world.say(
        f"One morning, {helper.pronoun('subject').capitalize()} found {clip.phrase} pinning together "
        f"{lst.phrase} beside the window."
    )
    world.say(
        f"The list said which leaves to pick, which flowers to dry, and which teas to brew "
        f"when someone was feeling poorly."
    )

    world.para()
    helper.memes["worry"] = 1
    world.action = Action(
        id="rush_scatter",
        verb="grab the list",
        gerund="grabbing the list",
        rush="snatch the pages too quickly",
        mess="scattered",
        harm="mixed up",
        tags={"clip", "list", "medicinal"},
    )
    world.say(
        f"Then a small wind fluttered through the room, and {helper.pronoun('subject')} worried that "
        f"the pages might scatter."
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} wanted to {world.action.verb} at once, but the elder "
        f"raised a calm hand and said, \"Slow steps keep a healing list true.\""
    )
    propagate(world)

    world.say(
        f"The helper nodded, because a medicinal list was not a toy, and a lost name could make a sick day worse."
    )

    world.para()
    world.action = Action(
        id="careful_clip",
        verb="use the clip",
        gerund="using the clip",
        rush="pin the pages in place",
        mess="tidy",
        harm="safe",
        tags={"clip", "list", "moral_value"},
    )
    world.say(
        f"With a thoughtful breath, {helper.pronoun('subject')} lifted {clip.it()} and closed it gently over "
        f"{lst.it()}."
    )
    propagate(world)
    helper.memes["worry"] = 0
    helper.memes["pride"] = 1
    helper.memes["kindness"] = 2
    elder.memes["trust"] = 2

    world.say(
        f"\"That is better,\" said the elder. \"You asked first, you kept the list safe, and that is how care becomes wisdom.\""
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} felt proud, not for being fast, but for being careful."
    )

    world.para()
    world.action = Action(
        id="brew_tea",
        verb="brew tea",
        gerund="brewing tea",
        rush="pour the water",
        mess="warm",
        harm="healed",
        tags={"medicinal", "tea"},
    )
    world.say(
        f"At last, they picked the right herb, warmed a cup, and brewed tea for the sick friend."
    )
    world.say(
        f"The friend drank it slowly, and soon {friend.pronoun('subject')} smiled as the warmth came back to {friend.pronoun('possessive')} hands."
    )
    world.say(
        f"The silver clip stayed shining on the medicinal list, and the little cottage felt peaceful again."
    )

    world.facts.update(
        helper=helper,
        elder=elder,
        friend=friend,
        clip=clip,
        lst=lst,
        herb=herb,
        cup=cup,
        moral=MORAL_VALUE,
    )
    return world


MORAL_VALUE = Moral(
    value="careful honesty",
    lesson="Good helpers ask before borrowing, keep useful things tidy, and use them with care.",
)

SETTINGS = {
    "cottage": Setting(place="the herb cottage", affords={"sort_medicines", "carry_list", "brew_tea"}),
    "garden": Setting(place="the moonlit garden", affords={"pick_herbs", "carry_list", "brew_tea"}),
}

ACTIVITIES = {
    "sort_medicines": Action(
        id="sort_medicines",
        verb="sort the medicines",
        gerund="sorting medicines",
        rush="sort too quickly",
        mess="mixed",
        harm="confused",
        tags={"medicinal", "list"},
    ),
    "carry_list": Action(
        id="carry_list",
        verb="carry the list",
        gerund="carrying the list",
        rush="snatch the pages",
        mess="scattered",
        harm="lost",
        tags={"clip", "list"},
    ),
    "brew_tea": Action(
        id="brew_tea",
        verb="brew tea",
        gerund="brewing tea",
        rush="pour the water",
        mess="warm",
        harm="healed",
        tags={"medicinal"},
    ),
}

PRIZES = {
    "clip": Prize(id="clip", label="clip", phrase="a tiny silver clip"),
    "list": Prize(id="list", label="list", phrase="a medicinal list"),
}

TRAITS = ["gentle", "curious", "kind", "careful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if act_id == "carry_list" and prize_id == "list":
                    combos.append((place, act_id, prize_id))
                if act_id == "brew_tea" and prize_id == "list":
                    combos.append((place, act_id, prize_id))
                if act_id == "sort_medicines" and prize_id == "list":
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle fairy tale about a clip, a medicinal list, and a wise moral value.',
        f"Tell a story where {f['helper'].id} finds {f['clip'].label} holding together {f['lst'].label} in {world.setting.place}.",
        f"Make it end with a careful choice that keeps the medicinal list safe and helps the sick friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper = _safe_fact(world, f, "helper")
    elder = _safe_fact(world, f, "elder")
    friend = _safe_fact(world, f, "friend")
    clip = _safe_fact(world, f, "clip")
    lst = _safe_fact(world, f, "lst")
    return [
        QAItem(
            question=f"What did {helper.id} find in the cottage?",
            answer=f"{helper.id} found {clip.phrase} holding together {lst.phrase}.",
        ),
        QAItem(
            question="Why did the elder tell the helper to slow down?",
            answer="Because a medicinal list can be ruined if its pages scatter or get mixed up, and then the wrong remedy might be used.",
        ),
        QAItem(
            question="What moral value did the helper learn?",
            answer=f"The helper learned {MORAL_VALUE.value}: good helpers ask before borrowing, keep useful things tidy, and use them with care.",
        ),
        QAItem(
            question="What happened to the sick friend at the end?",
            answer=f"The friend drank the tea, felt the warmth return, and smiled again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clip for?",
            answer="A clip holds papers or thin things together so they do not slip apart.",
        ),
        QAItem(
            question="What is medicinal mean?",
            answer="Medicinal means something helps care for illness or supports healing.",
        ),
        QAItem(
            question="What is a list?",
            answer="A list is a set of words or items written one after another, so they are easy to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the requested choices do not form a believable fairy-tale healing scene.)"


ASP_RULES = r"""
valid(Place,Act,Prize) :- affords(Place,Act), workable(Act,Prize).
workable(carry_list,list).
workable(sort_medicines,list).
workable(brew_tea,list).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("action", aid))
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
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a clip, a medicinal list, and moral care.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Lina", "Mira", "Bram", "Nell"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world()
    world = tell(world)
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
    StoryParams(place="cottage", activity="carry_list", prize="list", name="Lina", seed=1),
    StoryParams(place="cottage", activity="sort_medicines", prize="list", name="Mira", seed=2),
    StoryParams(place="cottage", activity="brew_tea", prize="list", name="Nell", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
