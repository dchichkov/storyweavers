#!/usr/bin/env python3
"""
A small mystery storyworld about a missing cranapple, a wig, and a friendship
that solves the puzzle. The world is constraint-checked and state-driven:
characters notice clues, worry, implore each other to help, and discover that
the odd wig was not a prank at all, but a hiding place for a shiny cranapple.

The story style stays close to mystery, with foreshadowing and a gentle
friendship turn at the end.
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
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    clue: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the old library"
    indoors: bool = True
    has_mirrors: bool = False
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
class Clue:
    id: str
    label: str
    kind: str
    reveal: str
    hint: str
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    clue_kind: str
    hiding_place: str
    can_hide: bool = False
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    clue: str
    item: str
    name_a: str
    name_b: str
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


SETTINGS = {
    "library": Setting(place="the old library", indoors=True, has_mirrors=False),
    "greenhouse": Setting(place="the greenhouse", indoors=True, has_mirrors=True),
    "attic": Setting(place="the dusty attic", indoors=True, has_mirrors=False),
}

CLUES = {
    "cranapple": Clue(
        id="cranapple",
        label="cranapple",
        kind="fruit",
        reveal="a bright red cranapple with a sweet tart smell",
        hint="The air smelled fruity near the clue.",
    ),
    "wig": Clue(
        id="wig",
        label="wig",
        kind="hairpiece",
        reveal="a curly wig with a tiny ribbon",
        hint="Something soft and fluffy sat where it should not.",
    ),
    "foreshadowing": Clue(
        id="foreshadowing",
        label="foreshadowing",
        kind="note",
        reveal="a note that seemed silly at first, but made sense later",
        hint="A small note hinted that the answer was hiding in plain sight.",
    ),
}

ITEMS = {
    "cranapple": Item(
        id="cranapple",
        label="cranapple",
        phrase="a shiny cranapple",
        clue_kind="fruit",
        hiding_place="wig",
        can_hide=True,
    ),
    "wig": Item(
        id="wig",
        label="wig",
        phrase="a curly wig",
        clue_kind="hairpiece",
        hiding_place="hook",
        can_hide=True,
    ),
    "note": Item(
        id="note",
        label="note",
        phrase="a folded note",
        clue_kind="note",
        hiding_place="book",
        can_hide=True,
    ),
}

NAMES = ["Mira", "Jasper", "Nina", "Otis", "Lena", "Eli"]
TRAITS = ["curious", "gentle", "careful", "brave", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery about a cranapple, a wig, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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


def _choose_pair(rng: random.Random) -> tuple[str, str]:
    a, b = rng.sample(NAMES, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    item = getattr(args, "item", None) or clue
    if clue == "cranapple" and item != "cranapple":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if clue == "wig" and item == "wig":
        pass
    if clue == "foreshadowing" and item == "cranapple":
        pass
    if clue not in CLUES or item not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) is None:
        place = rng.choice(list(SETTINGS))
    else:
        place = getattr(args, "place", None)
    name_a = getattr(args, "name_a", None) or rng.choice(NAMES)
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in NAMES if n != name_a])
    return StoryParams(place=place, clue=clue, item=item, name_a=name_a, name_b=name_b)


class StoryWorld(World):
    pass


def _setup(world: World, params: StoryParams) -> None:
    a = world.add(Entity(id=params.name_a, kind="character", type="girl", meters={}, memes={"curiosity": 0.0, "friendship": 1.0}))
    b = world.add(Entity(id=params.name_b, kind="character", type="boy", meters={}, memes={"curiosity": 0.0, "friendship": 1.0}))
    clue = world.add(Entity(id="clue", type=_safe_lookup(CLUES, params.clue).kind, label=_safe_lookup(CLUES, params.clue).label, phrase=_safe_lookup(CLUES, params.clue).reveal, owner=a.id))
    item = world.add(Entity(id="item", type="thing", label=_safe_lookup(ITEMS, params.item).label, phrase=_safe_lookup(ITEMS, params.item).phrase, owner=b.id, hidden_in=_safe_lookup(ITEMS, params.item).hiding_place))
    world.facts.update(hero=a, friend=b, clue=clue, item=item, params=params)


def _introduce(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    world.say(f"{hero.id} and {friend.id} were friends who loved solving little mysteries together.")
    world.say(f"At {world.setting.place}, they noticed a clue that felt important even before they knew why.")


def _foreshadow(world: World) -> None:
    clue: Entity = _safe_fact(world, world.facts, "clue")
    if clue.label == "foreshadowing":
        world.say("A tiny note winked from the table, like it already knew the ending.")
    else:
        world.say("Something about the room felt odd, as if the answer were waiting nearby.")


def _discover(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    item: Entity = _safe_fact(world, world.facts, "item")
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    if item.label == "cranapple":
        hero.meters["search"] = hero.meters.get("search", 0.0) + 1
        friend.meters["search"] = friend.meters.get("search", 0.0) + 1
        world.say(f"{hero.id} pointed at a soft wig on the shelf and implored {friend.id} to look closer.")
        world.say(f"Under the wig, they found {item.phrase}, tucked away like a secret.")
    elif item.label == "wig":
        world.say(f"{hero.id} found {item.phrase} hanging where a coat should be.")
        world.say(f"{friend.id} implored {hero.id} to think about why it looked so out of place.")
    else:
        world.say(f"{hero.id} found {item.phrase}, but it only deepened the puzzle.")


def _resolve(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    item: Entity = _safe_fact(world, world.facts, "item")
    world.say(f"Then {friend.id} smiled and said the mystery was never really about a trick.")
    world.say(f"It was about paying attention, and about how friends help each other look again.")
    world.say(f"Together they put the {item.label} back where it belonged, and the room felt calm at last.")
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1


def tell(setting: Setting, params: StoryParams) -> World:
    world = StoryWorld(setting)
    _setup(world, params)
    _introduce(world)
    world.para()
    _foreshadow(world)
    _discover(world)
    world.para()
    _resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short mystery story for young children that includes "{p.clue}", "{p.item}", and friendship.',
        f"Tell a gentle mystery set at {world.setting.place} where {p.name_a} implores {p.name_b} to help solve a clue.",
        f"Write a story with foreshadowing that starts with a strange {p.item} and ends with friends finding the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    item: Entity = _safe_fact(world, world.facts, "item")
    qa = [
        QAItem(
            question=f"Who are the two friends in the mystery at {world.setting.place}?",
            answer=f"The friends are {hero.id} and {friend.id}. They work together to solve the little mystery.",
        ),
        QAItem(
            question=f"What did {hero.id} implore {friend.id} to look at?",
            answer=f"{hero.id} implored {friend.id} to look at the strange {item.label}. That helped them notice the clue.",
        ),
        QAItem(
            question=f"What did they find under the wig or strange hiding place?",
            answer=f"They found {item.phrase} hidden there. The hidden thing was the answer to the mystery.",
        ),
    ]
    if p.clue == "foreshadowing":
        qa.append(QAItem(
            question="Why did the tiny note matter?",
            answer="The tiny note mattered because it hinted that the answer was hiding in plain sight. That was the foreshadowing.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    out = [
        QAItem(
            question="What is a cranapple?",
            answer="A cranapple is a made-up fruit name for this storyworld, treated like a small, shiny, fruity treasure.",
        ),
        QAItem(
            question="What does implore mean?",
            answer="To implore means to ask someone very earnestly or urgently for help.",
        ),
        QAItem(
            question="What is a wig?",
            answer="A wig is a covering for hair, often made to look like real hair.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint early on about something important that will matter later.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind, helpful bond between people who care about each other and work together.",
        ),
    ]
    if p.item == "cranapple":
        out.append(QAItem(
            question="Why might a cranapple be easy to miss?",
            answer="A cranapple might be easy to miss if it is hidden under something larger or if everyone expects the mystery to be about something else.",
        ))
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_relevant(c) :- clue(c).
hints_at(C, I) :- clue(C), item(I), clue_kind(C, K), item_kind(I, K).
mystery_resolved(I) :- item(I), hidden_in(I, H), revealed(H, I).
friendship_grows(A, B) :- friends(A, B), helped(A, B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.has_mirrors:
            lines.append(asp.fact("has_mirrors", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_kind", iid, it.clue_kind))
        lines.append(asp.fact("hidden_in", iid, it.hiding_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show clue_relevant/1."))
    atoms = set(asp.atoms(model, "clue_relevant"))
    python = {(cid,) for cid in CLUES}
    if atoms == python:
        print(f"OK: clingo gate matches Python registry ({len(atoms)} clues).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(python))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hints_at/2."))
    return sorted(set(asp.atoms(model, "hints_at")))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params)
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
    StoryParams(place="library", clue="cranapple", item="cranapple", name_a="Mira", name_b="Jasper"),
    StoryParams(place="greenhouse", clue="wig", item="wig", name_a="Nina", name_b="Otis"),
    StoryParams(place="attic", clue="foreshadowing", item="cranapple", name_a="Lena", name_b="Eli"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show hints_at/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show hints_at/2."))
        print(sorted(set(asp.atoms(model, "hints_at"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
            header = f"### {p.name_a} and {p.name_b}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
