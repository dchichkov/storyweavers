#!/usr/bin/env python3
"""
storyworlds/worlds/file_tuckus_shrink_sharing_twist_transformation_ghost.py
============================================================================

A small ghost-story world about a frightened child, a shared file, a strange
tuckus, a shrinking twist, and a gentle transformation.

The seed tale is intentionally simple and eerie:
A child finds a dusty file in an old room, hears a little tuckus of bumps from
the dark, and thinks a ghost is near. The child shares the file with a lonely
ghost who only wanted to be remembered. That kindness causes a twist: the ghost
shrinks from a scary shape into a tiny, bright companion, and the room changes
from cold and spooky to warm and calm.

This script models that premise with a causal world state:
- meters track physical size, chill, and light
- memes track fear, courage, loneliness, and comfort
- sharing lowers loneliness and can trigger transformation
- a tuckus is a little eerie bump or knock that raises fear
- shrink is the visible physical change that accompanies the twist
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
    plural: bool = False
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    h: object | None = None
    hero: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ("size", "chill", "light"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "courage", "loneliness", "comfort", "wonder", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    mood: str
    affordances: set[str] = field(default_factory=set)
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
class Artifact:
    label: str
    phrase: str
    file_word: str = "file"
    secret: str = "memory"
    tags: set[str] = field(default_factory=set)
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
class Haunt:
    label: str
    phrase: str
    tuckus_word: str = "tuckus"
    starting_size: float = 3.0
    tags: set[str] = field(default_factory=set)
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
    setting: str
    artifact: str
    haunt: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "attic": Setting("the attic", "dusty and dim", {"sharing", "twist", "transformation"}),
    "library": Setting("the old library", "quiet and moonlit", {"sharing", "twist", "transformation"}),
    "cellar": Setting("the cellar", "cool and echoing", {"sharing", "twist", "transformation"}),
}

ARTIFACTS = {
    "file": Artifact(
        label="file",
        phrase="a brittle file with fading labels",
        file_word="file",
        secret="old memory",
        tags={"file", "sharing"},
    ),
    "note": Artifact(
        label="note",
        phrase="a folded note with a careful crease",
        file_word="note",
        secret="small promise",
        tags={"sharing"},
    ),
    "box": Artifact(
        label="box",
        phrase="a thin box tied with ribbon",
        file_word="box",
        secret="kept story",
        tags={"sharing", "twist"},
    ),
}

HAUNTS = {
    "ghost": Haunt(
        label="ghost",
        phrase="a tall pale ghost with a soft cold glow",
        tuckus_word="tuckus",
        starting_size=3.0,
        tags={"ghost", "twist", "transformation"},
    ),
    "wisp": Haunt(
        label="wisp",
        phrase="a fluttering wisp with a shaky little sigh",
        tuckus_word="tuckus",
        starting_size=1.8,
        tags={"ghost", "transformation"},
    ),
    "shade": Haunt(
        label="shade",
        phrase="a quiet shade with a moon-gray outline",
        tuckus_word="tuckus",
        starting_size=2.4,
        tags={"ghost", "twist"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Etta", "Maya", "Lena", "Rosa"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Jude", "Eli", "Noah", "Bram", "Leo"]
TRAITS = ["curious", "brave", "careful", "gentle", "lonely", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ARTIFACTS:
            for h in HAUNTS:
                out.append((s, a, h))
    return out


def _do_tuckus(world: World, hero: Entity, haunt: Entity) -> None:
    if ("tuckus", haunt.id) in world.fired:
        return
    world.fired.add(("tuckus", haunt.id))
    haunt.memes["fear"] += 1
    hero.memes["fear"] += 1
    world.say(f"From the dark came a little tuckus, like knuckles tapping wood.")


def _share(world: World, hero: Entity, haunt: Entity, artifact: Entity) -> None:
    if ("share", hero.id, haunt.id, artifact.id) in world.fired:
        return
    world.fired.add(("share", hero.id, haunt.id, artifact.id))
    hero.memes["courage"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    haunt.memes["loneliness"] = max(0.0, haunt.memes["loneliness"] - 1.2)
    haunt.memes["trust"] += 1.0
    artifact.shared_with.add(haunt.id)
    world.say(
        f"{hero.id} did not hide the {artifact.label}. {hero.pronoun().capitalize()} shared "
        f"the {artifact.label} and read its words out loud."
    )


def _transform(world: World, hero: Entity, haunt: Entity, artifact: Entity) -> None:
    if ("transform", haunt.id) in world.fired:
        return
    if haunt.memes["trust"] < THRESHOLD or haunt.memes["loneliness"] > 0.6:
        return
    world.fired.add(("transform", haunt.id))
    haunt.meters["size"] = 0.7
    haunt.meters["chill"] = 0.2
    haunt.meters["light"] = 1.6
    haunt.memes["comfort"] += 2.0
    haunt.memes["wonder"] += 1.5
    hero.memes["wonder"] += 1.0
    world.say(
        f"Then came the twist: the ghost began to shrink, not from hurt, but from relief."
    )
    world.say(
        f"The big cold shape folded into a tiny bright friend who looked warm enough to keep."
    )


def tell(world: World, hero: Entity, parent: Entity, artifact: Entity, haunt: Entity) -> None:
    world.say(
        f"{hero.id} lived in {world.setting.place}, where everything felt {world.setting.mood}."
    )
    world.say(
        f"One evening, {hero.id} found {artifact.phrase} tucked behind an old shelf."
    )
    world.say(
        f"{hero.id} also heard {haunt.phrase} drifting near the shadows."
    )
    world.para()
    _do_tuckus(world, hero, haunt)
    hero.memes["fear"] += 0.5
    world.say(
        f"{hero.id}'s heart jumped, because the tuckus sounded like a ghost looking for trouble."
    )
    world.say(
        f"But {hero.id} noticed that {haunt.label} was lonely, not mean."
    )
    world.para()
    _share(world, hero, haunt, artifact)
    _transform(world, hero, haunt, artifact)
    if haunt.meters["size"] < 1.0:
        world.say(
            f"The little ghost floated beside {hero.pronoun('object')}, and the room no longer felt scary."
        )
    world.say(
        f"{parent.id} smiled at the small glow and said the old {artifact.file_word} had turned a fright into a friend."
    )

    world.facts.update(hero=hero, parent=parent, artifact=artifact, haunt=haunt)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes if False), '')}"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    artifact = _safe_fact(world, f, "artifact")
    haunt = _safe_fact(world, f, "haunt")
    return [
        'Write a short ghost story for a small child that includes a file, a tuckus, and a shrink.',
        f"Tell a spooky-but-kind story where {hero.id} shares a {artifact.label} and the ghost changes.",
        f"Write a gentle ghost story about {hero.id}, {parent.id}, and a {haunt.label} that ends with a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    artifact = _safe_fact(world, f, "artifact")
    haunt = _safe_fact(world, f, "haunt")
    return [
        QAItem(
            question=f"What did {hero.id} find in the old room?",
            answer=f"{hero.id} found {artifact.phrase}. It was a {artifact.file_word} that held an old memory.",
        ),
        QAItem(
            question=f"What made {hero.id} think a ghost was near?",
            answer=f"A little tuckus came from the dark, like soft bumps on wood, and that made {hero.id} think a ghost was nearby.",
        ),
        QAItem(
            question=f"How did the story change when {hero.id} shared the {artifact.label}?",
            answer=(
                f"Sharing the {artifact.label} helped the {haunt.label} feel less lonely. "
                f"That turned the spooky moment into a twist, and the ghost shrank into a tiny, bright friend."
            ),
        ),
        QAItem(
            question=f"Who was smiling at the end of the story?",
            answer=f"{parent.id} was smiling because the old fright became a calm, friendly ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a ghost in a ghost story?",
            answer="A ghost in a ghost story is usually a spooky spirit character that can seem cold, pale, or mysterious.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, see, or enjoy something with you instead of keeping it only for yourself.",
        ),
        QAItem(
            question="What does shrink mean?",
            answer="To shrink means to get smaller.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new way.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means a big change, like when something becomes different from what it was before.",
        ),
    ]
    if f["artifact"].file_word == "file":
        out.append(QAItem(
            question="What is a file?",
            answer="A file can mean a folder or packet for keeping papers or memories together.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", artifact="file", haunt="ghost", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="library", artifact="note", haunt="wisp", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(setting="cellar", artifact="box", haunt="shade", name="Ivy", gender="girl", parent="mother", trait="brave"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "artifact", None):
        combos = [c for c in combos if c[1] == getattr(args, "artifact", None)]
    if getattr(args, "haunt", None):
        combos = [c for c in combos if c[2] == getattr(args, "haunt", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, artifact, haunt = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, artifact=artifact, haunt=haunt, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    artifact = _safe_lookup(ARTIFACTS, params.artifact)
    haunt = _safe_lookup(HAUNTS, params.haunt)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    art = world.add(Entity(id="Artifact", type="thing", label=artifact.label, phrase=artifact.phrase))
    h = world.add(Entity(
        id="Ghost", kind="character", type="ghost", label=haunt.label, phrase=haunt.phrase,
        meters={"size": haunt.starting_size, "chill": 1.5, "light": 0.1},
        memes={"fear": 0.4, "courage": 0.0, "loneliness": 1.6, "comfort": 0.0, "wonder": 0.0, "trust": 0.0},
    ))
    hero.memes["fear"] = 0.5
    hero.memes["courage"] = 0.2
    hero.memes["wonder"] = 0.2
    parent.memes["comfort"] = 0.5

    world.say(
        f"{hero.id} was a little {params.trait} child who lived in {setting.place}."
    )
    world.say(
        f"One day, {hero.id} found {artifact.phrase} and heard {haunt.phrase} nearby."
    )
    world.para()
    world.say(
        f"The quiet room held its breath, as if waiting for someone to make the first kind move."
    )

    tell(world, hero, parent, art, h)

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


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
    ap = argparse.ArgumentParser(description="Ghost story world with sharing, twist, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_storyworld_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
artifact(A) :- artifact_fact(A).
haunt(H) :- haunt_fact(H).

shared(A) :- sharing_event(A).
twist(H) :- fear_event(H), shared_event(H).
transformation(H) :- twist(H), trust(H).

#show shared/1.
#show twist/1.
#show transformation/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact_fact", a))
    for h in HAUNTS:
        lines.append(asp.fact("haunt_fact", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    models = asp.solve(asp_program("#show shared/1. #show twist/1. #show transformation/1."), models=1)
    if not models:
        print("MISMATCH: no ASP model found.")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show shared/1. #show twist/1. #show transformation/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for verification, but this world generates directly in Python.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_storyworld_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.artifact} in {p.setting} with {p.haunt}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
