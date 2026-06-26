#!/usr/bin/env python3
"""
A standalone storyworld for a tiny myth-like tale with a free melody, a twist,
and a lesson learned.

Premise:
- A small hero wants to make something beautiful and free.
- A song, a river, a mountain, or a bell can be involved.

Tension:
- Someone or something tries to keep the melody trapped, hidden, or owned.

Twist:
- The thing everyone thought was a problem turns out to be the key.

Lesson learned:
- Beauty grows when it is shared, not caged.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    bound: bool = False
    free: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    keeper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "brother"}:
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
    id: str
    label: str
    echoes: bool = False
    affords: set[str] = field(default_factory=set)
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
class Melody:
    id: str
    title: str
    phrase: str
    instrument: str
    nature: str
    twist_key: str
    can_free: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Chain:
    id: str
    label: str
    phrase: str
    breaks_on: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
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

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    keeper: str
    melody: str
    chain: str
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
    "cave": Place(id="cave", label="the echo cave", echoes=True, affords={"sing", "listen", "hide"}),
    "well": Place(id="well", label="the old wishing well", echoes=True, affords={"sing", "listen"}),
    "hill": Place(id="hill", label="the windy hill", echoes=False, affords={"sing", "listen", "run"}),
}

HEROES = [
    ("Nia", "girl"),
    ("Tarin", "boy"),
    ("Luma", "girl"),
    ("Orin", "boy"),
]

KEEPERS = [
    ("king", "the king"),
    ("queen", "the queen"),
    ("farmer", "the farmer"),
    ("warden", "the warden"),
]

MELODIES = {
    "free": Melody(
        id="free",
        title="the free melody",
        phrase="a free melody",
        instrument="voice",
        nature="bright",
        twist_key="freedom",
    ),
    "river": Melody(
        id="river",
        title="the river melody",
        phrase="a river melody",
        instrument="reed flute",
        nature="soft",
        twist_key="river",
    ),
    "star": Melody(
        id="star",
        title="the star melody",
        phrase="a star melody",
        instrument="little harp",
        nature="high",
        twist_key="star",
    ),
}

CHAINS = {
    "golden": Chain(id="golden", label="a golden chain", phrase="a golden chain", breaks_on={"free", "river"}),
    "glass": Chain(id="glass", label="a glass chain", phrase="a glass chain", breaks_on={"free", "star"}),
    "stone": Chain(id="stone", label="a stone seal", phrase="a stone seal", breaks_on={"river", "star"}),
}

TALES = {
    "free": {
        "setup": "The child loved to sing a free melody, one that belonged to no cage and no crown.",
        "hook": "But the keeper had locked the song behind a chain so only the palace could hear it.",
    },
    "melody": {
        "setup": "The child found a melody in the wind and wanted to share it with the whole valley.",
        "hook": "But the keeper said the tune must stay hidden, as if beauty could be owned.",
    },
    "twist": {
        "setup": "The child listened to an old melody that everyone had forgotten.",
        "hook": "But the forgotten tune was tied to a secret door, and the keeper feared what it might reveal.",
    },
}

MOTIFS = ["free", "melody", "twist", "lesson learned", "myth"]


def choose_chain(melody: Melody) -> Chain:
    for ch in CHAINS.values():
        if melody.id in ch.breaks_on or melody.twist_key in ch.breaks_on:
            return ch
    pass


def predict_free(world: World, melody: Melody, chain: Chain) -> bool:
    sim = world.copy()
    sim.facts["song_played"] = melody.id
    return melody.id in chain.breaks_on or melody.twist_key in chain.breaks_on


def awaken(world: World, hero: Entity, melody: Melody) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"{hero.id} had heard of {melody.phrase}, and {hero.pronoun()} carried it in "
        f"{hero.pronoun('possessive')} heart like a tiny flame."
    )


def bind(world: World, keeper: Entity, chain: Chain, melody: Melody) -> None:
    keeper.memes["fear"] = keeper.memes.get("fear", 0) + 1
    world.say(
        f"{keeper.label.capitalize()} had wrapped {chain.phrase} around the song, "
        f"so the people could not hear its full joy."
    )


def seek(world: World, hero: Entity, place: Place) -> None:
    hero.meters["journey"] = hero.meters.get("journey", 0) + 1
    world.say(f"One dusk, {hero.id} went to {place.label}, where the stones kept old secrets.")


def sing(world: World, hero: Entity, melody: Melody) -> None:
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    world.say(
        f"{hero.id} began to sing {melody.phrase}, and the air filled with a "
        f"{melody.nature} sound that shimmered like water."
    )


def twist_reveal(world: World, melody: Melody, chain: Chain, keeper: Entity) -> None:
    world.facts["twist"] = True
    world.say(
        f"Then came the twist: the chain did not guard the song at all. "
        f"It guarded a door, and {melody.phrase} was the only key that could wake it."
    )
    world.say(
        f"When {melody.title} rang out, the chain split with a soft cry, and the keeper "
        f"stepped back, stunned by the sound."
    )
    keeper.memes["shame"] = keeper.memes.get("shame", 0) + 1


def lesson(world: World, hero: Entity, keeper: Entity, melody: Melody) -> None:
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0) + 1
    keeper.memes["relief"] = keeper.memes.get("relief", 0) + 1
    world.say(
        f"Lesson learned: a beautiful thing grows stronger when it is shared. "
        f"{hero.id} smiled, and even {keeper.label} could hear that a free melody "
        f"was never meant to stay locked away."
    )


def tell(place: Place, hero_name: str, hero_type: str, keeper_kind: str, melody: Melody, chain: Chain) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_kind, label=keeper_kind))

    world.say(f"In {place.label}, the wind remembered old songs.")
    world.say(_safe_lookup(TALES, melody.id)["setup"])
    awaken(world, hero, melody)

    world.para()
    bind(world, keeper, chain, melody)
    world.say(_safe_lookup(TALES, melody.id)["hook"])
    seek(world, hero, place)

    world.para()
    sing(world, hero, melody)
    if predict_free(world, melody, chain):
        twist_reveal(world, melody, chain, keeper)
    else:
        pass

    world.para()
    lesson(world, hero, keeper, melody)

    world.facts.update(
        hero=hero,
        keeper=keeper,
        place=place,
        melody=melody,
        chain=chain,
        broken=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    melody: Melody = _safe_fact(world, f, "melody")
    keeper: Entity = _safe_fact(world, f, "keeper")
    place: Place = _safe_fact(world, f, "place")
    return [
        f'Write a short myth for a child about a free melody at {place.label}.',
        f"Tell a story where {hero.id} sings {melody.phrase}, the keeper tries to stop it, "
        f"and a twist changes the meaning of the song.",
        f"Write a gentle myth with the words 'free' and 'melody' and end with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    keeper: Entity = _safe_fact(world, f, "keeper")
    melody: Melody = _safe_fact(world, f, "melody")
    chain: Chain = _safe_fact(world, f, "chain")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who discovered the free melody in {place.label}?",
            answer=f"{hero.id} discovered it after following the old echo path into {place.label}.",
        ),
        QAItem(
            question=f"What did {keeper.label} use to keep the song hidden?",
            answer=f"{keeper.label.capitalize()} used {chain.phrase} to keep the song hidden.",
        ),
        QAItem(
            question=f"What was the twist in the story about {melody.title}?",
            answer="The twist was that the chain was not only a lock; it was also the key that opened the secret door.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer="The lesson was that a beautiful thing becomes stronger when it is shared freely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a melody?",
            answer="A melody is a sequence of notes that sounds like a tune you can hum or sing.",
        ),
        QAItem(
            question="What does it mean for something to be free?",
            answer="Something free is not locked up, owned, or trapped, so it can move or belong to everyone.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes you see the story in a new way.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the useful idea the story teaches by the end.",
        ),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.bound:
            parts.append("bound=True")
        if e.free:
            parts.append("free=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-like storyworld with a free melody, a twist, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--keeper", choices=[k for k, _ in KEEPERS])
    ap.add_argument("--melody", choices=MELODIES)
    ap.add_argument("--chain", choices=CHAINS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    melody_id = getattr(args, "melody", None) or rng.choice(list(MELODIES))
    melody = _safe_lookup(MELODIES, melody_id)
    chain_id = getattr(args, "chain", None) or choose_chain(melody).id
    hero_name, hero_type = (getattr(args, "hero", None), getattr(args, "hero_type", None)) if getattr(args, "hero", None) and getattr(args, "hero_type", None) else rng.choice(HEROES)
    keeper_kind, _ = rng.choice(KEEPERS)
    if getattr(args, "keeper", None):
        keeper_kind = getattr(args, "keeper", None)
    return StoryParams(place=place, hero=hero_name, hero_type=hero_type, keeper=keeper_kind, melody=melody_id, chain=chain_id)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    melody = _safe_lookup(MELODIES, params.melody)
    chain = _safe_lookup(CHAINS, params.chain)
    world = tell(place, params.hero, params.hero_type, params.keeper, melody, chain)
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


ASP_RULES = r"""
place(cave). place(well). place(hill).
melody(free). melody(river). melody(star).
chain(golden). chain(glass). chain(stone).

breaks(golden, free). breaks(golden, river).
breaks(glass, free). breaks(glass, star).
breaks(stone, river). breaks(stone, star).

has_twist(M,C) :- melody(M), chain(C), breaks(C,M).
valid_story(P,M,C) :- place(P), melody(M), chain(C), has_twist(M,C).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MELODIES:
        lines.append(asp.fact("melody", m))
    for c in CHAINS:
        lines.append(asp.fact("chain", c))
    for cid, chain in CHAINS.items():
        for m in chain.breaks_on:
            lines.append(asp.fact("breaks", cid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = []
    for p in PLACES:
        for m in MELODIES:
            for c in CHAINS:
                if m in _safe_lookup(CHAINS, c).breaks_on or _safe_lookup(MELODIES, m).twist_key in _safe_lookup(CHAINS, c).breaks_on:
                    combos.append((p, m, c))
    asp_set = set(asp_valid_stories())
    py_set = set(combos)
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


CURATED = [
    StoryParams(place="cave", hero="Nia", hero_type="girl", keeper="king", melody="free", chain="golden"),
    StoryParams(place="well", hero="Tarin", hero_type="boy", keeper="queen", melody="melody", chain="glass"),
    StoryParams(place="hill", hero="Luma", hero_type="girl", keeper="warden", melody="star", chain="stone"),
]


def asp_valid_combos() -> list[tuple]:
    return asp_valid_stories()


def asp_program_text() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_text())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} compatible (place, melody, chain) combos:\n")
        for place, melody, chain in models:
            print(f"  {place:5} {melody:8} {chain:8}")
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.hero}: {p.melody} at {p.place} (chain: {p.chain})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
