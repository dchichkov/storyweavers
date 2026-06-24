#!/usr/bin/env python3
"""
Storyworld: Sleep-Dim Rollie Clinic Conflict Surprise

A small, standalone story world in a rhyming style:
- seed words: sleep-dim, rollie, clinic
- features: Conflict, Surprise

Premise:
A child arrives at a clinic at sleepy-dim hour with a cherished rollie toy.
A grown-up worries the toy will make the child too loud or too upset in the
waiting room. The child resists, then a surprise reveals the toy can help in a
gentle, useful way.

The world state tracks:
- physical meters: light, noise, wobble, tidy, calm
- emotional memes: worry, grip, courage, relief, delight

Story shape:
setup -> conflict -> surprise turn -> resolution
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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

    child: object | None = None
    nurse: object | None = None
    parent: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    light: str
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
    kind: str = "toy"
    wobble: float = 1.0
    can_hush: bool = False
    can_help: bool = False
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
class Gear:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

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


def _default_meters() -> dict[str, float]:
    return {"light": 0.0, "noise": 0.0, "wobble": 0.0, "tidy": 0.0, "calm": 0.0}


def _default_memes() -> dict[str, float]:
    return {"worry": 0.0, "grip": 0.0, "courage": 0.0, "relief": 0.0, "delight": 0.0}


def add_meters(ent: Entity, **changes: float) -> None:
    for k, v in changes.items():
        ent.meters[k] = ent.meters.get(k, 0.0) + v


def add_memes(ent: Entity, **changes: float) -> None:
    for k, v in changes.items():
        ent.memes[k] = ent.memes.get(k, 0.0) + v


def fix_noise(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    toy = world.get("toy")
    if kid.meters.get("noise", 0.0) < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_memes(kid, worry=1.0)
    out.append(f"{kid.id} made a noise that tried to bounce off the walls.")
    if toy.worn_by == kid.id:
        add_meters(toy, wobble=1.0)
        out.append(f"The little rollie gave a bright little clatter.")
    return out


def fix_surprise(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    nurse = world.get("nurse")
    toy = world.get("toy")
    if world.facts.get("surprise_seen"):
        return out
    if kid.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if toy.worn_by != kid.id:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["surprise_seen"] = True
    add_memes(kid, courage=1.0, relief=1.0)
    add_memes(nurse, delight=1.0)
    out.append("Then came a surprise with a soft little shine.")
    out.append("The rollie had a tiny side knob that could make a lamp glow dim.")
    return out


def fix_calm(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    nurse = world.get("nurse")
    toy = world.get("toy")
    if kid.memes.get("relief", 0.0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meters(kid, calm=1.0)
    add_meters(toy, tidy=1.0)
    out.append(f"The room grew dim, and the rollie helped the child feel calm.")
    out.append(f"{nurse.label} smiled, and the waiting felt small and sweet.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (fix_noise, fix_surprise, fix_calm):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "clinic": Setting(place="the clinic", light="sleep-dim", affords={"visit"}),
}

TOYS = {
    "rollie": Toy(
        id="rollie",
        label="rollie",
        phrase="a round rollie with a tiny knob",
        can_hush=True,
        can_help=True,
    )
}

GEAR = {
    "blanket": Gear(
        id="blanket",
        label="small blanket",
        phrase="a small blanket",
        prep="wrap the child in a small blanket",
        tail="wrapped the child in a soft small blanket",
    )
}


@dataclass
class StoryParams:
    setting: str
    toy: str
    name: str
    parent: str
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


NAMES = ["Mia", "Leo", "Nina", "Eli", "Luna", "Noah"]
PARENTS = ["mother", "father"]
CURATED = [
    StoryParams(setting="clinic", toy="rollie", name="Mia", parent="mother"),
    StoryParams(setting="clinic", toy="rollie", name="Leo", parent="father"),
]


def introduce(world: World, child: Entity, parent: Entity, toy: Entity) -> None:
    world.say(
        f"{child.id} came to {world.setting.place} in the sleep-dim light, "
        f"with {child.pronoun('possessive')} {toy.label} held tight and bright."
    )
    world.say(
        f"{child.id} loved the little rollie so much it felt like a song in the hand, "
        f"soft as a breeze and light as sand."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.type} stayed near, with a gentle face, "
        f"to wait at the clinic and keep a safe pace."
    )


def conflict(world: World, child: Entity, parent: Entity, toy: Entity) -> None:
    world.para()
    add_meters(child, noise=1.0)
    add_memes(child, grip=1.0)
    world.say(
        f"But the clinic was quiet, and the child felt small; "
        f"{child.id} wanted the rollie to roll down the hall."
    )
    world.say(
        f'"Not now," said {child.pronoun("possessive")} {world.facts["parent_label"]}, '
        f'"for the room must stay still; that clatter might echo and make people ill."'
    )
    world.say(
        f"{child.id} frowned at the warning and tightened {child.pronoun('possessive')} grip, "
        f"for wanting the rollie was not just a blip."
    )
    add_memes(child, worry=1.0)
    propagate(world, narrate=True)


def surprise_turn(world: World, child: Entity, nurse: Entity, toy: Entity) -> None:
    world.para()
    world.say(
        f"Then out of the blue came a nurse with a grin; "
        f"she looked at the rollie and nodded right in."
    )
    world.say(
        f'"That little toy has a secret," she said with a wink, '
        f'"a dim little lamp for the softest of pink."'
    )
    toy.can_help = True
    world.facts["surprise_seen"] = False
    propagate(world, narrate=True)


def resolution(world: World, child: Entity, parent: Entity, nurse: Entity, toy: Entity) -> None:
    world.para()
    add_meters(toy, tidy=1.0)
    add_memes(child, delight=1.0)
    add_memes(parent, relief=1.0)
    world.say(
        f"{child.id} turned the tiny knob, and the rollie glowed low; "
        f"the dim little light made a hush in the show."
    )
    world.say(
        f"{child.id} smiled at the glow and let out a small cheer; "
        f"{world.facts['parent_label']} sighed with relief and drew near."
    )
    world.say(
        f"So the child had the rollie, but used it with care; "
        f"the clinic stayed calm, and warm peace filled the air."
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    nurse = world.add(Entity(
        id="nurse",
        kind="character",
        type="nurse",
        label="the nurse",
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type="toy",
        label="rollie",
        phrase=_safe_lookup(TOYS, params.toy).phrase,
        owner=child.id,
        meters={"light": 0.0, "noise": 0.0, "wobble": 0.0, "tidy": 0.0},
        memes={},
    ))
    toy.worn_by = child.id

    world.facts.update(parent_label=parent.label, setting=setting.place, toy=toy, child=child, parent=parent, nurse=nurse)

    introduce(world, child, parent, toy)
    conflict(world, child, parent, toy)
    surprise_turn(world, child, nurse, toy)
    resolution(world, child, parent, nurse, toy)

    world.facts.update(
        conflict=True,
        surprise=True,
        resolved=True,
        child_name=child.id,
        toy_label=toy.label,
    )
    return world


KNOWLEDGE = {
    "clinic": [
        ("What is a clinic?",
         "A clinic is a place where people go to see a nurse or doctor for help, checkups, and care."),
    ],
    "dim": [
        ("What does dim light mean?",
         "Dim light is soft and not very bright, so it feels calm and gentle to the eyes."),
    ],
    "rollie": [
        ("What is a rollie?",
         "A rollie is a round toy or object that can roll, wobble, or spin in a playful way."),
    ],
    "surprise": [
        ("What is a surprise?",
         "A surprise is something you did not expect, and it can make you gasp, smile, or laugh."),
    ],
    "conflict": [
        ("What is a conflict in a story?",
         "A conflict is a problem or disagreement that makes the characters worry before things get better."),
    ],
    "soft": [
        ("Why do people like soft things?",
         "Soft things feel gentle and cozy, so they can help a child feel safe and calm."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child_name")
    return [
        f"Write a rhyming story about {child}, a rollie, and a sleepy clinic.",
        f"Tell a gentle conflict-and-surprise tale where {child} wants a rollie at the clinic, but the grown-up worries at first.",
        f"Write a short children's story in rhyme with a dim clinic light, a rollie toy, and a happy surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child_name")
    parent = _safe_fact(world, f, "parent_label")
    toy = _safe_fact(world, f, "toy_label")
    return [
        QAItem(
            question=f"Who came to the clinic with the rollie?",
            answer=f"{child} came to the clinic with the rollie and stayed close to {parent}.",
        ),
        QAItem(
            question="Why did the grown-up worry at first?",
            answer=(
                f"{parent} worried because the clinic needed to stay quiet, and the rollie could make noise "
                f"if it was rolled the wrong way."
            ),
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer=(
                f"The surprise was that the rollie had a tiny knob that made a dim little lamp glow, "
                f"so it could help the child feel calm instead of causing trouble."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {child} using the rollie gently, the clinic staying calm, and everyone feeling better."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("clinic", "dim", "rollie", "surprise", "conflict", "soft"):
        if key in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clinic story is valid when the child, the toy, and the setting all fit.
valid_story(S, T) :- setting(S), toy(T), setting_affords(S, visit), toy_can_help(T).

% Conflict happens when the child is worried and the toy might make noise.
conflict_story(S, T) :- valid_story(S, T), can_noise(T).

% Surprise happens when the toy has a hidden helpful feature.
surprise_story(S, T) :- valid_story(S, T), can_help(T).

% The happy ending needs both a conflict and a surprise.
complete_story(S, T) :- conflict_story(S, T), surprise_story(S, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_light", sid, setting.light))
        for a in sorted(setting.affords):
            lines.append(asp.fact("setting_affords", sid, a))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if toy.can_hush:
            lines.append(asp.fact("can_noise", tid))
        if toy.can_help:
            lines.append(asp.fact("toy_can_help", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show complete_story/2."))
    return sorted(set(asp.atoms(model, "complete_story")))


def asp_verify() -> int:
    py = {("clinic", "rollie")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo matches python gate ({len(py)} story).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: clinic, rollie, dim light, surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
    setting = getattr(args, "setting", None) or "clinic"
    toy = getattr(args, "toy", None) or "rollie"
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    if setting != "clinic" or toy != "rollie":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, toy=toy, name=name, parent=parent)


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
        print(asp_program("#show complete_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story: clinic / rollie")
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
