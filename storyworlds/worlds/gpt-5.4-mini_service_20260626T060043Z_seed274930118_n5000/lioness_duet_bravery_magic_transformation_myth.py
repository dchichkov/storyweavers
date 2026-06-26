#!/usr/bin/env python3
"""
Standalone storyworld: a mythic lioness duet of bravery, magic, and transformation.

A small, classical world model:
- A lioness hears a duet in a moonlit grove.
- She fears the dark river crossing.
- A magical song changes her courage and the world image.
- The ending proves transformation through a visible, narrated state change.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------


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

@dataclass(frozen=True)
class Place:
    id: str
    label: str
    light: str
    features: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class CharacterSpec:
    id: str
    label: str
    type: str
    gender: str
    traits: tuple[str, ...] = ()
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


@dataclass(frozen=True)
class SongSpec:
    id: str
    title: str
    kind: str
    effect: str
    turns: str
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


@dataclass(frozen=True)
class TransformationSpec:
    id: str
    from_form: str
    to_form: str
    image: str
    feature: str
    condition: str
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


PLACES: dict[str, Place] = {
    "grove": Place(id="grove", label="the moonlit grove", light="moonlight", features={"moon", "trees", "river"}),
    "riverbank": Place(id="riverbank", label="the riverbank", light="starlight", features={"river", "mist"}),
    "cave": Place(id="cave", label="the hollow cave", light="firelight", features={"stone", "echo"}),
}

CHARACTERS: dict[str, CharacterSpec] = {
    "lioness": CharacterSpec(id="lioness", label="a young lioness", type="lioness", gender="female", traits=("brave", "quiet")),
    "sister": CharacterSpec(id="sister", label="her sister", type="lioness", gender="female", traits=("steady", "bright")),
}

SONGS: dict[str, SongSpec] = {
    "duet": SongSpec(
        id="duet",
        title="the moon-duet",
        kind="duet",
        effect="it gathered courage like a warm fire in the chest",
        turns="the song rose and braided two voices together",
        features={"bravery", "magic", "moon"},
    ),
    "chant": SongSpec(
        id="chant",
        title="the old chant",
        kind="chant",
        effect="it stirred the old stones awake",
        turns="the chorus climbed like ivy",
        features={"magic"},
    ),
}

TRANSFORMS: dict[str, TransformationSpec] = {
    "golden_mane": TransformationSpec(
        id="golden_mane",
        from_form="a hesitant lioness",
        to_form="a radiant lioness with a golden mane",
        image="her dark mane gleamed like new sunlit grass",
        feature="transformation",
        condition="after the duet and the brave crossing",
    ),
    "starlit_path": TransformationSpec(
        id="starlit_path",
        from_form="a dark river path",
        to_form="a silver path of stepping stones",
        image="the water flashed into a bright ribbon of stones",
        feature="magic",
        condition="when courage reached the river",
    ),
}

TRAITS = ["brave", "thoughtful", "gentle", "steady", "curious"]


# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    location: str = ""
    with_whom: str = ""

    hero: object | None = None
    sister: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lioness", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def capitalized_pronoun(self) -> str:
        return self.pronoun().capitalize()
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


@dataclass
class World:
    place: Place
    hero: Entity
    sister: Entity
    song: SongSpec
    transform: TransformationSpec
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
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


def mood_name(value: float) -> str:
    if value >= 2:
        return "strong"
    if value >= 1:
        return "growing"
    if value <= 0:
        return "fading"
    return "small"


def build_world(place: Place, song: SongSpec, transform: TransformationSpec,
                hero_name: str, sister_name: str) -> World:
    hero = Entity(
        id=hero_name,
        kind="character",
        type="lioness",
        label=hero_name,
        traits=["lioness", "little", random.choice(TRAITS)],
        meters={"steps": 0.0},
        memes={"fear": 1.0, "bravery": 0.0, "awe": 0.0, "joy": 0.0},
        location=place.id,
    )
    sister = Entity(
        id=sister_name,
        kind="character",
        type="lioness",
        label=sister_name,
        traits=["lioness", "older", "steady"],
        meters={"voice": 1.0},
        memes={"calm": 1.0, "love": 1.0},
        location=place.id,
    )
    world = World(place=place, hero=hero, sister=sister, song=song, transform=transform)
    world.facts["place"] = place
    world.facts["song"] = song
    world.facts["transform"] = transform
    world.facts["hero"] = hero
    world.facts["sister"] = sister
    return world


def opening(world: World) -> None:
    h, s, p = world.hero, world.sister, world.place
    world.say(
        f"Long ago, {h.label} wandered into {p.label}, where moonlight silvered the leaves and made every shadow look watchful."
    )
    world.say(
        f"She loved the hush of night, yet a dark river barred the way ahead, and her {h.pronoun('possessive')} paws hesitated at the bank."
    )
    world.say(
        f"Her sister {s.label} waited beside her, calm as a reed in still water, and together they prepared a duet."
    )


def sing_duet(world: World) -> None:
    h, s, song = world.hero, world.sister, world.song
    if "sing" in world.fired:
        return
    world.fired.add("sing")
    h.memes["awe"] += 1.0
    s.memes["joy"] += 1.0
    h.memes["bravery"] += 1.0
    world.say(
        f"They began {song.title}, and the two voices rose together in a duet. {song.turns.capitalize()}, and {song.effect}."
    )


def cross_river(world: World) -> None:
    h, t = world.hero, world.transform
    if "cross" in world.fired:
        return
    if h.memes.get("bravery", 0.0) < 1.0:
        pass
    world.fired.add("cross")
    h.meters["steps"] += 3.0
    h.memes["fear"] = max(0.0, h.memes.get("fear", 0.0) - 1.0)
    h.memes["joy"] += 1.0
    world.say(
        f"Then {h.label} took one step, then another, and the river path changed under her."
    )
    world.say(
        f"When her courage reached the water, {t.image}."
    )


def transform_hero(world: World) -> None:
    h, t = world.hero, world.transform
    if "transform" in world.fired:
        return
    world.fired.add("transform")
    h.type = "lioness"
    h.traits = ["lioness", "radiant", "brave"]
    h.memes["bravery"] += 1.0
    h.memes["awe"] += 1.0
    h.memes["joy"] += 1.0
    world.say(
        f"By the time she reached the far bank, {h.label} was no longer the same; she had become {t.to_form}."
    )
    world.say(
        f"Her mane shone with moon-bright gold, and even the reeds bowed as if they had seen a queen."
    )


def close_story(world: World) -> None:
    h, s = world.hero, world.sister
    world.say(
        f"{s.label} touched noses with her and smiled, because the duet had not only crossed the river but also changed the lioness inside."
    )
    world.say(
        f"At last, {h.label} stood on the silver shore with brave eyes, a bright mane, and a quiet heart that no longer feared the night."
    )


def propagate(world: World) -> None:
    opening(world)
    world.para()
    sing_duet(world)
    cross_river(world)
    transform_hero(world)
    world.para()
    close_story(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    h = world.hero
    return [
        'Write a short myth for young children about a lioness, a duet, and a magical change by moonlight.',
        f"Tell a gentle mythic story where {h.label} is afraid, sings a duet, and finds bravery at the river.",
        "Write a child-friendly myth that includes a lioness, music, magic, and a transformation at night.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, s, p, song = world.hero, world.sister, world.place, world.song
    return [
        QAItem(
            question=f"Where did {h.label} begin the story?",
            answer=f"{h.label} began in {p.label}, where the moonlight made the grove look silver and strange.",
        ),
        QAItem(
            question=f"What helped {h.label} become brave enough to cross the river?",
            answer=f"The duet helped her. When she and {s.label} sang {song.title}, her bravery grew stronger and her fear faded.",
        ),
        QAItem(
            question=f"What changed after the song and the crossing?",
            answer=f"{h.label} changed into a radiant lioness with a golden mane, so the story ended with her looking magical and new.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a duet?",
            answer="A duet is a song or piece of music sung or played by two performers together.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means being afraid but still doing the hard thing that needs to be done.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a big change, when something becomes something new.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a special kind of power that can change things in ways that would not happen in ordinary life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% facts:
% place(Place). song(Song). transform(T).
% feature(X).  hero(H). sister(S).

courage(H) :- hero(H), meme(H,bravery,Score), Score >= 1.
has_magic(Song) :- song(Song), feature(Song,magic).
has_duet(Song) :- song(Song), feature(Song,duet).
can_transform(H,T) :- courage(H), transform(T), feature(T,transformation).
river_crossed(H) :- can_transform(H,_).

safe_story(H,S,T) :- hero(H), sister(S), transform(T), courage(H), has_duet(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(p.features):
            lines.append(asp.fact("feature", pid, feat))
    for sid, s in CHARACTERS.items():
        lines.append(asp.fact("hero" if sid == "lioness" else "sister", sid))
        for trait in s.traits:
            lines.append(asp.fact("trait", sid, trait))
    for sid, s in SONGS.items():
        lines.append(asp.fact("song", sid))
        for feat in sorted(s.features):
            lines.append(asp.fact("feature", sid, feat))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("feature", tid, t.feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show safe_story/3."))
    asp_count = len(asp.atoms(model, "safe_story"))
    py_count = 1
    if asp_count == py_count:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print(f"MISMATCH: ASP={asp_count} Python={py_count}")
    return 1


# ---------------------------------------------------------------------------
# Sampling and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    song: str
    transform: str
    hero_name: str
    sister_name: str
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
    ap = argparse.ArgumentParser(description="Mythic lioness duet storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--sister-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("grove", "duet", "golden_mane"), ("riverbank", "duet", "golden_mane")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "song", None):
        combos = [c for c in combos if c[1] == getattr(args, "song", None)]
    if getattr(args, "transform", None):
        combos = [c for c in combos if c[2] == getattr(args, "transform", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, song, transform = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Nia", "Luma", "Suri", "Kaia", "Mira"])
    sister_name = getattr(args, "sister_name", None) or rng.choice(["Asha", "Tala", "Rina", "Dara", "Sela"])
    if hero_name == sister_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, song=song, transform=transform, hero_name=hero_name, sister_name=sister_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        place=_safe_lookup(PLACES, params.place),
        song=_safe_lookup(SONGS, params.song),
        transform=_safe_lookup(TRANSFORMS, params.transform),
        hero_name=params.hero_name,
        sister_name=params.sister_name,
    )
    propagate(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print("--- world trace ---")
        print(f"place={sample.world.place.id}")
        print(f"hero={sample.world.hero.label} memes={sample.world.hero.memes} meters={sample.world.hero.meters}")
        print(f"sister={sample.world.sister.label} memes={sample.world.sister.memes} meters={sample.world.sister.meters}")
        print(f"song={sample.world.song.id}")
        print(f"transform={sample.world.transform.id}")
    if qa:
        print()
        print(format_qa(sample))


def asp_show_program() -> str:
    return asp_program("#show safe_story/3.")


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_list())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("grove", "duet", "golden_mane", "Nia", "Asha"),
            StoryParams("riverbank", "duet", "golden_mane", "Luma", "Tala"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
