#!/usr/bin/env python3
"""
A tiny storyworld set in a toy library, with nursery-rhyme cadence, repetition,
curiosity, and reconciliation.

A child keeps asking to borrow a special pass for the toy library. The pass is
not just a key; it is a little promise that lets the child choose one toy at a
time, return it, and try again. The child gets curious, makes a small mistake by
asking for too many toys, then reconciles with the librarian by following the
rules and sharing the turn.

The world is modeled as entities with physical meters and emotional memes.
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

# -----------------------------------------------------------------------------
# World constants
# -----------------------------------------------------------------------------
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    librarian: object | None = None
    passcard: object | None = None
    toy: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

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
    place: str = "the toy library"
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
class Toy:
    id: str
    label: str
    phrase: str
    token: str
    size: str
    plural: bool = False
    genres: set[str] = field(default_factory=set)
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
class PassCard:
    id: str
    label: str
    phrase: str
    rule: str
    token: str
    keeps: set[str] = field(default_factory=set)
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "plural": v.plural, "owner": v.owner,
            "caretaker": v.caretaker, "held_by": v.held_by,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _say_nursery_repeat(world: World, line: str, times: int = 2) -> None:
    for _ in range(times):
        world.say(line)


def _propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for child in world.children():
            if child.memes.get("too_many", 0) >= THRESHOLD and ("apology", child.id) not in world.fired:
                world.fired.add(("apology", child.id))
                child.memes["shy"] = child.memes.get("shy", 0) + 1
                world.say(f"{child.id} grew quiet and looked down at {child.pronoun('possessive')} shoes.")
                changed = True
            if child.memes.get("shared", 0) >= THRESHOLD and ("joy", child.id) not in world.fired:
                world.fired.add(("joy", child.id))
                child.memes["joy"] = child.memes.get("joy", 0) + 1
                changed = True


SETTINGS = {
    "toy_library": Setting(place="the toy library", affords={"pass"}),
}

TOYS = {
    "train": Toy(
        id="train",
        label="toy train",
        phrase="a red toy train",
        token="train",
        size="small",
        genres={"rolling"},
    ),
    "bear": Toy(
        id="bear",
        label="toy bear",
        phrase="a soft brown bear",
        token="bear",
        size="small",
        genres={"cuddly"},
    ),
    "blocks": Toy(
        id="blocks",
        label="blocks",
        phrase="a bright stack of blocks",
        token="blocks",
        size="small",
        plural=True,
        genres={"stacking"},
    ),
    "drum": Toy(
        id="drum",
        label="drum",
        phrase="a round little drum",
        token="drum",
        size="small",
        genres={"noisy"},
    ),
}

PASSES = {
    "pass": PassCard(
        id="pass",
        label="toy library pass",
        phrase="a little toy library pass",
        rule="one toy at a time",
        token="pass",
        keeps={"one"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tia", "Ada"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Owen", "Jude", "Leo"]
TRAITS = ["curious", "cheery", "small", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    toy: str
    passcard: str
    name: str
    gender: str
    librarian: str
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


def _child_desc(hero: Entity) -> str:
    trait = next((t for t in hero.meters.keys()), "")
    return trait


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"small": 1},
        memes={"curiosity": 0, "want": 0},
    ))
    librarian = world.add(Entity(
        id="Librarian",
        kind="character",
        type="adult",
        label=params.librarian,
        memes={"calm": 1},
    ))
    toy = world.add(Entity(
        id=params.toy,
        type="toy",
        label=_safe_lookup(TOYS, params.toy).label,
        phrase=_safe_lookup(TOYS, params.toy).phrase,
        plural=_safe_lookup(TOYS, params.toy).plural,
        owner="library",
        caretaker="Librarian",
    ))
    passcard = world.add(Entity(
        id=params.passcard,
        type="pass",
        label=_safe_lookup(PASSES, params.passcard).label,
        phrase=_safe_lookup(PASSES, params.passcard).phrase,
        owner="library",
        caretaker="Librarian",
    ))

    # Act 1: repetition, invitation.
    world.say(f"{hero.id} came to {setting.place} in a soft little morning light.")
    _say_nursery_repeat(world, f"{hero.id} said, “May I have the pass?”")
    world.say(f"The {librarian.label} smiled and held up {passcard.phrase}.")
    world.say(f"“Yes,” said the {librarian.label}, “but only one toy at a time.”")

    # Act 2: curiosity and trouble.
    world.para()
    world.say(f"{hero.id} looked at the shelves and grew curious, curious, curious.")
    world.say(f"{hero.id} wanted the {toy.label} and then another toy, and then another.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    hero.memes["too_many"] = hero.memes.get("too_many", 0) + 1
    world.say(f"{hero.id} reached for three toys at once, and the pass gave a tiny wobble.")
    world.say(f"The {librarian.label} said, “The pass says one toy. One toy, one turn.”")

    # Act 3: reconciliation.
    world.para()
    world.say(f"{hero.id} paused, then nodded slow and small.")
    world.say(f"“One toy, one turn,” {hero.id} whispered, and handed back the extra toys.")
    hero.memes["shared"] = hero.memes.get("shared", 0) + 1
    hero.memes["too_many"] = 0
    _propagate(world)
    world.say(f"The {librarian.label} nodded back and gave the pass a gentle tap.")
    world.say(f"{hero.id} took the {toy.label} with both hands, and the pass stayed warm and true.")
    world.say(f"One toy in, one toy out; one soft step, then another step about.")
    world.say(f"By the end, the shelves were neat, the pass was safe, and {hero.id} was smiling.")

    world.facts.update(
        hero=hero,
        librarian=librarian,
        toy=toy,
        passcard=passcard,
        setting=setting,
        repeated=True,
        curious=True,
        reconciled=True,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    toy = _safe_fact(world, f, "toy")
    return [
        f'Write a short nursery-rhyme story set in {world.setting.place} about a child asking for a {f["passcard"].token}.',
        f"Tell a gentle story where {hero.id} grows curious, asks for {toy.label}, and learns to wait for one turn.",
        f'Write a rhyme-like story about a pass, a toy shelf, and a happy reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    librarian = _safe_fact(world, f, "librarian")
    toy = _safe_fact(world, f, "toy")
    passcard = _safe_fact(world, f, "passcard")
    return [
        QAItem(
            question=f"What did {hero.id} keep asking for at the toy library?",
            answer=f"{hero.id} kept asking for the {passcard.label}. The pass was the little rule that let {hero.id} borrow one toy at a time.",
        ),
        QAItem(
            question=f"Why did the {librarian.label} remind {hero.id} about the pass?",
            answer=f"The {librarian.label} reminded {hero.id} because the pass meant only one toy at a time. {hero.id} had reached for too many toys, so the rule needed a calm reminder.",
        ),
        QAItem(
            question=f"How did {hero.id} and the {librarian.label} make things right?",
            answer=f"{hero.id} handed back the extra toys, listened to the rule, and then took the {toy.label} the proper way. That was their reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a library?",
            answer="A library is a place where people borrow books or other things for a little while and then bring them back.",
        ),
        QAItem(
            question="What does it mean to wait for a turn?",
            answer="Waiting for a turn means letting someone else go first and taking your chance after they are done.",
        ),
        QAItem(
            question="What is a rule?",
            answer="A rule is a guide that helps everyone know how to play, share, and stay safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.kind == "character":
            bits.append("kind=character")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Content registry
# -----------------------------------------------------------------------------
CURATED = [
    StoryParams(place="toy_library", toy="train", passcard="pass", name="Mina", gender="girl", librarian="Ms. Dot", trait="curious"),
    StoryParams(place="toy_library", toy="bear", passcard="pass", name="Leo", gender="boy", librarian="Mr. Bean", trait="gentle"),
]


def valid_choices() -> list[tuple[str, str, str]]:
    return [(p, t, "pass") for p in SETTINGS for t in TOYS if p == "toy_library"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) != "toy_library":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "toy", None) and getattr(args, "toy", None) not in TOYS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_choices()
    if getattr(args, "toy", None):
        combos = [c for c in combos if c[1] == getattr(args, "toy", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    _, toy, passcard = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    librarian = getattr(args, "librarian", None) or rng.choice(["Ms. Dot", "Mr. Bean", "Ms. Sera", "Mr. Tuck"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place="toy_library",
        toy=toy,
        passcard=passcard,
        name=name,
        gender=gender,
        librarian=librarian,
        trait=trait,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy library nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=["toy_library"])
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--passcard", choices=sorted(PASSES), default="pass")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--librarian")
    ap.add_argument("--trait")
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


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
place(toy_library).
toy(train). toy(bear). toy(blocks). toy(drum).
passcard(pass).

#show valid/3.
valid(P,T,Pass) :- place(P), toy(T), passcard(Pass), P = toy_library.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    for pid in PASSES:
        lines.append(asp.fact("passcard", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_choices())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_choices() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_choices():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# -----------------------------------------------------------------------------
# Emit / main
# -----------------------------------------------------------------------------
def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid()
        print(f"{len(triples)} compatible choices:\n")
        for p, t, pa in triples:
            print(f"  {p:12} {t:8} {pa:8}")
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
            header = f"### {p.name}: {p.toy} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
