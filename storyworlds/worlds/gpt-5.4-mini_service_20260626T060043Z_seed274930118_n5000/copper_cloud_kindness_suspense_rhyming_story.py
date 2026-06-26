#!/usr/bin/env python3
"""
A small rhyming storyworld about a copper cloud, a kindness test, and a tense
little rescue.

The seed tale behind this world:
- A child finds a small copper cloud charm that rings like a bell.
- The charm is meant to help a sleepy garden fountain start singing again.
- A shy friend worries the charm may be lost in the dark.
- The child chooses kindness, shares the lantern, and the charm is found.
"""

from __future__ import annotations

import argparse
import dataclasses
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fountain: object | None = None
    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    lantern: object | None = None
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
class Setting:
    place: str
    indoors: bool = False
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
class ItemSpec:
    id: str
    label: str
    phrase: str
    location: str
    shimmer: str
    risky: str
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
class MoodSpec:
    id: str
    verb: str
    rhyme: str
    tension_word: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the garden", indoors=False),
    "courtyard": Setting(place="the courtyard", indoors=False),
    "porch": Setting(place="the porch", indoors=True),
}

ITEMS = {
    "copper_cloud": ItemSpec(
        id="copper_cloud",
        label="copper cloud",
        phrase="a tiny copper cloud charm",
        location="on the bench",
        shimmer="gleaming gold",
        risky="lost in the dusk",
    ),
    "kettle": ItemSpec(
        id="copper_kettle",
        label="copper kettle",
        phrase="a round copper kettle",
        location="by the fountain",
        shimmer="bright and warm",
        risky="spilled on the stones",
    ),
    "bell": ItemSpec(
        id="little_bell",
        label="little bell",
        phrase="a little silver bell",
        location="near the rose bush",
        shimmer="soft and bright",
        risky="too easy to misplace",
    ),
}

MOODS = {
    "kindness": MoodSpec(
        id="kindness",
        verb="be kind",
        rhyme="shine",
        tension_word="kindness",
        keyword="Kindness",
    ),
    "suspense": MoodSpec(
        id="suspense",
        verb="stay in suspense",
        rhyme="glow",
        tension_word="suspense",
        keyword="Suspense",
    ),
    "help": MoodSpec(
        id="help",
        verb="help",
        rhyme="cheer",
        tension_word="help",
        keyword="help",
    ),
}

GIRL_NAMES = ["Mina", "Lola", "Nia", "Pia", "Tessa", "June", "Mabel"]
BOY_NAMES = ["Owen", "Rafi", "Milo", "Arlo", "Ezra", "Theo", "Finn"]
TRAITS = ["gentle", "cheerful", "curious", "brave", "soft-spoken", "bright"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    item: str
    mood: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
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
    for place in SETTINGS:
        for item in ITEMS:
            for mood in MOODS:
                combos.append((place, item, mood))
    return combos


def explain_rejection(place: str, item: str, mood: str) -> str:
    return f"(No story: {item} with {mood} at {place} was not a reasonable fit.)"


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, and {b}."


def article(phrase: str) -> str:
    return phrase if phrase.startswith(("a ", "an ", "the ")) else f"a {phrase}"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"care": 0.0, "search": 0.0},
        memes={"joy": 0.0, "kindness": 0.0, "suspense": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_gender,
        meters={"care": 0.0, "search": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "trust": 0.0},
    ))
    item_spec = _safe_lookup(ITEMS, params.item)
    item = world.add(Entity(
        id=item_spec.id,
        kind="thing",
        type="treasure",
        label=item_spec.label,
        phrase=item_spec.phrase,
        location=item_spec.location,
        owner=hero.id,
        caretaker=friend.id,
        meters={"shine": 1.0, "lost": 0.0},
        memes={"wonder": 1.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a small brass lantern",
        owner=hero.id,
        carried_by=hero.id,
        meters={"light": 1.0},
        memes={"warmth": 1.0},
    ))
    fountain = world.add(Entity(
        id="fountain",
        kind="thing",
        type="fountain",
        label="fountain",
        phrase="the sleepy fountain",
        location=params.place,
        meters={"thirst": 1.0},
        memes={"quiet": 1.0},
    ))

    mood = _safe_lookup(MOODS, params.mood)

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} {params.gender} who loved a little {mood.keyword.lower()} in rhyme."
    )
    world.say(
        f"By {item.label}, {hero.id} found {item.phrase}, {item.shimmer} in the light, "
        f"and the day felt snug and bright."
    )
    world.say(
        f"{hero.id} wished to {mood.verb} with {friend.id}, and the fountain waited quiet at {params.place}."
    )

    # Act 2
    world.say(
        f"One dusk they went to {params.place}, where shadows could stretch and the breeze could race."
    )
    hero.meters["search"] += 1
    hero.memes["suspense"] += 1
    friend.memes["worry"] += 1
    item.meters["lost"] += 1
    world.say(
        f"But then the {item.label} slipped from sight, and both small hearts went still as night."
    )
    world.say(
        f"{friend.id} whispered that the charm might be {item.risky}, and the hush grew long with tense delay."
    )

    # Act 3
    hero.meters["care"] += 1
    hero.memes["kindness"] += 1
    friend.memes["trust"] += 1
    lantern.meters["light"] += 1
    item.meters["lost"] = 0.0
    item.carried_by = hero.id

    world.say(
        f"Then {hero.id} shared the lantern glow, because {mood.keyword.lower()} made {hero.id} want to help and show."
    )
    world.say(
        f"They looked where the copper hush had shone, and found the {item.label} by a stone."
    )
    world.say(
        f"So {hero.id} held {item.label} high and bright; {friend.id} smiled, and the fountain sang that night."
    )
    world.say(
        f"The little copper cloud was safe at last, and the tense dusk drifted gently past."
    )

    world.facts = {
        "hero": hero,
        "friend": friend,
        "item": item,
        "lantern": lantern,
        "fountain": fountain,
        "mood": mood,
        "place": params.place,
        "item_spec": item_spec,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item_spec")
    mood = _safe_fact(world, f, "mood")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short rhyming story for a child about {hero.id}, {item.label}, and {mood.keyword} at {place}.',
        f"Tell a gentle, suspenseful story where {hero.id} shares a lantern, finds {item.label}, and ends in kindness.",
        f"Write a simple rhyme about a small copper thing getting lost, then found again with a kind friend nearby.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    item_spec: ItemSpec = _safe_fact(world, f, "item_spec")
    mood: MoodSpec = _safe_fact(world, f, "mood")
    place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Who found the {item_spec.label} in {place}?",
            answer=f"{hero.id} found the {item_spec.label} in {place} after the small search grew tense."
        ),
        QAItem(
            question=f"Why did the story feel like {mood.keyword.lower()} before the ending?",
            answer=f"It felt like {mood.keyword.lower()} because the {item_spec.label} slipped from sight and no one knew where it was."
        ),
        QAItem(
            question=f"What did {hero.id} do to help {friend.id} feel better?",
            answer=f"{hero.id} shared the lantern light, searched kindly, and brought the {item_spec.label} back."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {item_spec.label} was safe again, {friend.id} smiled, and the fountain sang softly."
        ),
    ]


KNOWLEDGE = {
    "copper": QAItem(
        question="What is copper?",
        answer="Copper is a reddish-brown metal that can shine warmly and is often used for coins, pots, and bells.",
    ),
    "cloud": QAItem(
        question="What is a cloud?",
        answer="A cloud is a soft-looking group of tiny water drops or ice crystals floating in the sky.",
    ),
    "kindness": QAItem(
        question="What is kindness?",
        answer="Kindness means being gentle, helpful, and caring to other people.",
    ),
    "suspense": QAItem(
        question="What is suspense?",
        answer="Suspense is the nervous feeling you get when you do not yet know what will happen next.",
    ),
    "lantern": QAItem(
        question="What does a lantern do?",
        answer="A lantern gives light so people can see better in the dark.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"copper", "cloud", "kindness", "suspense", "lantern"}
    out: list[QAItem] = []
    for tag in tags:
        out.append(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- treasure(I).
mood(M) :- feeling(M).

valid_story(P, I, M) :- place(P), item(I), mood(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("treasure", iid))
    for mid in MOODS:
        lines.append(asp.fact("feeling", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.item in ITEMS and params.mood in MOODS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "item", None) and getattr(args, "item", None) not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "mood", None) and getattr(args, "mood", None) not in MOODS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
        and (getattr(args, "mood", None) is None or c[2] == getattr(args, "mood", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, item, mood = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = rng.choice(["girl", "boy"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        item=item,
        mood=mood,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


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
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: copper, cloud, kindness, suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--name")
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


def generate_all() -> list[StorySample]:
    return [generate(StoryParams(place=p, item=i, mood=m, name="Mina", gender="girl",
                                 friend_name="Owen", friend_gender="boy", trait="gentle"))
            for p, i, m in valid_combos()]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    if getattr(args, "all", None):
        samples = generate_all()
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
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
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {idx + 1}: {p.name} with {p.item} at {p.place}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
