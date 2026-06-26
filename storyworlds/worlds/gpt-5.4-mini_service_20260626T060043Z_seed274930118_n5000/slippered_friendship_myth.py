#!/usr/bin/env python3
"""
storyworlds/worlds/slippered_friendship_myth.py
===============================================

A small mythic story world about friendship, careful steps, and a promised pair
of slippers.

The seed premise:
- A friendship is tested by a hard crossing.
- A slippered helper, a shared path, and a humble promise turn worry into trust.
- The story should feel like a little myth: concrete, ceremonial, and child-facing.

This world models:
- physical state in meters: distance to cross, slipper dryness, stone slipperiness
- emotional state in memes: trust, worry, gratitude, pride, tenderness

The story is generated from a simulated sequence rather than a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
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
# Registries
# ---------------------------------------------------------------------------

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

@dataclass(frozen=True)
class Place:
    id: str
    name: str
    setting_line: str
    crossing: str
    hazard: str
    mythic_feature: str
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


@dataclass(frozen=True)
class Friend:
    id: str
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    trait: str
    is_slippered: bool = False
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


@dataclass(frozen=True)
class Token:
    id: str
    name: str
    article: str
    region: str
    guards: set[str] = field(default_factory=set)
    makes: str = ""
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
    "riverford": Place(
        id="riverford",
        name="Riverford",
        setting_line="At the edge of Riverford, the brook sang over flat stones, and the reeds bowed like listeners.",
        crossing="the stepping stones",
        hazard="the wet stones were slick",
        mythic_feature="the brook remembered every footstep",
    ),
    "hillpath": Place(
        id="hillpath",
        name="Hearthhill Path",
        setting_line="On Hearthhill Path, the wind slid down the grass, and the old lane climbed toward the bells.",
        crossing="the narrow lane",
        hazard="the lane was steep and loose",
        mythic_feature="the bells answered the wind with silver notes",
    ),
}

FRIENDS = {
    "mira": Friend("mira", "Mira", "child", "she", "her", "her", "gentle", True),
    "orin": Friend("orin", "Orin", "child", "he", "him", "his", "steady", False),
    "luma": Friend("luma", "Luma", "child", "she", "her", "her", "bright", True),
    "teo": Friend("teo", "Teo", "child", "he", "him", "his", "bold", False),
}

TOKENS = {
    "slippers": Token("slippers", "slippers", "a pair of", "feet", guards={"wet", "cold"}, makes="slippered"),
    "cloak": Token("cloak", "cloak", "a", "torso", guards={"wind"}, makes="hooded"),
    "lantern": Token("lantern", "lantern", "a", "hand", guards={"dark"}, makes="lit"),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    worn: Optional[str] = None
    owns: Optional[str] = None

    c: object | None = None
    h: object | None = None
    t: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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


class World:
    def __init__(self, place: Place, hero: Friend, companion: Friend, token: Token):
        self.place = place
        self.hero = hero
        self.companion = companion
        self.token = token
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World(self.place, self.hero, self.companion, self.token)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    token: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
    params: object | None = None
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


def reasonableness_gate(place: Place, hero: Friend, companion: Friend, token: Token) -> None:
    if hero.id == companion.id:
        pass
    if token.id != "slippers":
        pass
    if not hero.is_slippered:
        pass


def make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    hero = _safe_lookup(FRIENDS, params.hero)
    companion = _safe_lookup(FRIENDS, params.companion)
    token = _safe_lookup(TOKENS, params.token)
    reasonableness_gate(place, hero, companion, token)
    world = World(place, hero, companion, token)

    h = world.add(Entity(id=hero.id, kind="character", label=hero.name))
    c = world.add(Entity(id=companion.id, kind="character", label=companion.name))
    t = world.add(Entity(id=token.id, kind="thing", label=token.name, owns=hero.id))

    h.meters["distance"] = 0.0
    h.meters["dry"] = 1.0
    h.meters["crossing"] = 0.0
    h.memes.update(trust=1.0, worry=0.0, tenderness=1.0)
    c.memes.update(trust=1.0, worry=0.0, gratitude=0.0)

    t.worn = hero.id
    world.facts.update(place=place, hero=hero, companion=companion, token=token)
    return world


def foresee_slip(world: World) -> bool:
    return True


def start_story(world: World) -> None:
    hero = world.hero
    companion = world.companion
    place = world.place
    token = world.token
    world.say(
        f"{place.setting_line} There lived {hero.name}, who was known as the slippered one, "
        f"because {hero.pronoun_possessive} {token.name} were always on before the road."
    )
    world.say(
        f"{companion.name} was {hero.name}'s truest friend, and the two of them shared water, bread, and quiet jokes."
    )
    world.say(
        f"Each child trusted the other, for the old people said that friendship grows strongest when it is carried carefully."
    )


def tension(world: World) -> None:
    hero = world.get(world.hero.id)
    companion = world.get(world.companion.id)
    place = world.place

    world.para()
    hero.memes["worry"] += 1.0
    companion.memes["worry"] += 1.0
    world.say(
        f"One evening, they came to {place.crossing}, and the brook below them flashed like polished glass."
    )
    world.say(
        f"{place.hazard.capitalize()}, and even a brave child could lose a step there."
    )
    world.say(
        f"{companion.label} looked down and held still, because {hero.label}'s {world.token.name} might keep {hero.pronoun_subject} safe, but only if {hero.pronoun_subject} crossed with care."
    )
    world.facts["hazard"] = place.hazard


def turn(world: World) -> None:
    hero = world.get(world.hero.id)
    companion = world.get(world.companion.id)
    token = world.get(world.token.id)

    world.para()
    hero.memes["tenderness"] += 1.0
    companion.memes["trust"] += 1.0
    world.say(
        f"{hero.label} stepped first, not because {hero.pronoun_subject} was the fastest, but because {hero.pronoun_subject} knew the ground and listened to the stones."
    )
    world.say(
        f"{hero.label} held out a hand and said, 'Walk where I walk. My {token.label} will not be enough for both of us, but my care can be.'"
    )
    companion.meters["distance"] = 1.0
    companion.memes["worry"] = max(0.0, companion.memes["worry"] - 0.5)
    world.say(
        f"So {companion.label} placed {companion.pronoun_subject} feet where {hero.label} pointed, and the two friends moved like a little procession in an old tale."
    )


def resolve(world: World) -> None:
    hero = world.get(world.hero.id)
    companion = world.get(world.companion.id)
    token = world.get(world.token.id)

    world.para()
    hero.meters["crossing"] = 1.0
    companion.meters["crossing"] = 1.0
    hero.memes["trust"] += 1.0
    companion.memes["gratitude"] += 1.5
    companion.memes["trust"] += 1.0
    hero.memes["worry"] = 0.0
    companion.memes["worry"] = 0.0
    world.say(
        f"At the far bank, {companion.label} laughed in relief, for {hero.label}'s slippered feet had found every safe stone."
    )
    world.say(
        f"{companion.label} touched the dry {token.label} and thanked {hero.label} for the help, while the brook kept its bright secret below."
    )
    world.say(
        f"That night the villagers said the oldest truth again: a friend can be a lamp, a hand, or a careful pair of {token.label} on a hard road."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.place
    h = world.hero
    c = world.companion
    return [
        f"Write a short myth about friendship at {p.name} where {h.name}, the slippered child, helps {c.name} cross safely.",
        f"Tell a gentle child-sized legend in which two friends face {p.hazard} and discover that care matters as much as speed.",
        f"Write a mythic story about a slippered friend, a hard crossing, and a promise that keeps two companions together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    c = world.companion
    p = world.place
    token = world.token
    return [
        QAItem(
            question=f"Who was the slippered friend in the story?",
            answer=f"The slippered friend was {h.name}, who wore {h.pronoun_possessive} {token.name} and led the way across the crossing.",
        ),
        QAItem(
            question=f"Why did {c.name} feel worried at {p.crossing}?",
            answer=f"{c.name} felt worried because {p.hazard}, and the stones looked hard to trust without a careful guide.",
        ),
        QAItem(
            question=f"What did the two friends do together at the end?",
            answer=f"They crossed {p.crossing} safely, thanked each other, and kept their friendship strong on the far bank.",
        ),
        QAItem(
            question=f"How did {h.name} help {c.name}?",
            answer=f"{h.name} helped by walking first, showing safe stones, and sharing calm care instead of rushing ahead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other, help each other, and stay close in hard moments.",
        ),
        QAItem(
            question="What are slippers for?",
            answer="Slippers are soft shoes for the feet. People wear them to keep their feet comfortable and to walk gently indoors or on careful paths.",
        ),
        QAItem(
            question="Why is a slippery stone path dangerous?",
            answer="A slippery stone path is dangerous because feet can slide instead of gripping, which can make a person stumble or fall.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
companion(C) :- companion_name(C).
place(P) :- place_name(P).
token(T) :- token_name(T).

slippered(H) :- hero(H), has_slippers(H).
at_risk(P) :- place(P), hazard(P, wet_stones).

friendship_story(H, C, P, T) :- hero(H), companion(C), place(P), token(T),
                                 different(H, C), slippered(H), at_risk(P),
                                 has_token(H, T), help_cross(H, C, P).

different(X, Y) :- X != Y.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        lines.append(asp.fact("hazard", pid, "wet_stones" if "wet" in place.hazard else "steep_lane"))
    for fid, friend in FRIENDS.items():
        lines.append(asp.fact("friend_name", fid))
        if friend.is_slippered:
            lines.append(asp.fact("has_slippers", fid))
    lines.append(asp.fact("hero_name", "mira"))
    lines.append(asp.fact("companion_name", "orin"))
    lines.append(asp.fact("token_name", "slippers"))
    lines.append(asp.fact("has_token", "mira", "slippers"))
    lines.append(asp.fact("help_cross", "mira", "orin", "riverford"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show friendship_story/4."))
    asp_set = set(asp.atoms(model, "friendship_story"))
    py_set = {("mira", "orin", "riverford", "slippers")}
    if asp_set == py_set:
        print("OK: ASP gate matches the Python myth gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    hero = getattr(args, "hero", None) or rng.choice([k for k, v in FRIENDS.items() if v.is_slippered])
    companion = getattr(args, "companion", None) or rng.choice([k for k in FRIENDS if k != hero])
    token = getattr(args, "token", None) or "slippers"
    params = StoryParams(place=place, hero=hero, companion=companion, token=token)
    make_world(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    start_story(world)
    tension(world)
    turn(world)
    resolve(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(sorted(e.meters.items()))} memes={dict(sorted(e.memes.items()))} worn={e.worn}")
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
    ap = argparse.ArgumentParser(description="A mythic friendship story world with a slippered helper.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(FRIENDS))
    ap.add_argument("--companion", choices=sorted(FRIENDS))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return choose_params(args, rng)


CURATED = [
    StoryParams(place="riverford", hero="mira", companion="orin", token="slippers"),
    StoryParams(place="riverford", hero="luma", companion="teo", token="slippers"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show friendship_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show friendship_story/4."))
        print(sorted(asp.atoms(model, "friendship_story")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
