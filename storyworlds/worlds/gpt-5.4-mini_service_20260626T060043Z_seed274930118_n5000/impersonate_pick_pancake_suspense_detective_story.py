#!/usr/bin/env python3
"""
storyworlds/worlds/impersonate_pick_pancake_suspense_detective_story.py
======================================================================

A small detective-story world with suspense, where a careful child detective
spots someone impersonating a helper, picks the right pancake clue, and helps
set the truth straight.

The seed prompt suggests three words to center the domain around:
- impersonate
- pick
- pancake

We model a tiny, child-facing mystery at a breakfast cafe. The main tension is
whether a helper is truly who they claim to be. The detective must pick the
right pancake clue from the evidence, follow the suspenseful trail, and resolve
the deception with a clear ending image.

The world uses:
- typed entities with physical meters and emotional memes
- a small causal simulation that drives the prose
- a Python reasonableness gate plus an inline ASP twin
- story QA and world-knowledge QA
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

SETTING_NAME = "the breakfast cafe"



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
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    helper: object | None = None
    imposter: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "mom", "waitress", "chef"}
        masculine = {"boy", "man", "father", "dad", "waiter", "chef"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
    place: str = SETTING_NAME
    affords: set[str] = field(default_factory=set)
    world: object | None = None
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
class SuspenseScene:
    id: str
    verb: str
    clue: str
    noise: str
    mess: str
    risk: str
    keyword: str = "pancake"
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "table"
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
    scene: str
    prize: str
    name: str
    gender: str
    helper: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SCENES = {
    "kitchen": SuspenseScene(
        id="kitchen",
        verb="look for the missing syrup",
        clue="a syrupy pancake",
        noise="a soft drip under the table",
        mess="sticky",
        risk="the breakfast would go cold",
        keyword="pancake",
    ),
    "counter": SuspenseScene(
        id="counter",
        verb="check the serving tray",
        clue="a stack with a hidden mark",
        noise="a whisper by the plates",
        mess="crumbly",
        risk="the wrong plate might get served",
        keyword="pancake",
    ),
    "hall": SuspenseScene(
        id="hall",
        verb="follow the footprints",
        clue="a maple-smudged napkin",
        noise="a tiny scrape near the door",
        mess="sticky",
        risk="the trail might disappear",
        keyword="pancake",
    ),
}

PRIZES = {
    "spoon": Prize(id="spoon", label="spoon", phrase="a shiny little spoon"),
    "badge": Prize(id="badge", label="badge", phrase="a bright detective badge"),
    "napkin": Prize(id="napkin", label="napkin", phrase="a folded blue napkin"),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Ivy", "Max"]
HELPERS = ["waiter", "waitress", "chef"]
TRAITS = ["careful", "curious", "brave", "sharp-eyed", "quiet"]


def reasonableness_gate(scene: SuspenseScene, prize: Prize) -> bool:
    if scene.keyword != "pancake":
        return False
    return prize.id in {"badge", "napkin", "spoon"}


def valid_combos() -> list[tuple[str, str]]:
    return [(scene_id, prize_id) for scene_id in SCENES for prize_id in PRIZES if reasonableness_gate(_safe_lookup(SCENES, scene_id), _safe_lookup(PRIZES, prize_id))]


def explain_rejection(scene: SuspenseScene, prize: Prize) -> str:
    return (
        f"(No story: the scene and prize do not make a clear pancake mystery. "
        f"Pick a clue that can honestly be part of the breakfast trail.)"
    )


def resolve_helper_word(helper: str) -> str:
    return helper


def build_world(params: StoryParams) -> World:
    scene = _safe_lookup(SCENES, params.scene)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(Setting())
    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.helper, "detective"],
        meters={"focus": 0.0},
        memes={"curiosity": 1.0, "suspense": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"nervous": 1.0},
        memes={"suspense": 1.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label=prize.label,
        phrase=prize.phrase,
        owner=detective.id,
        caretaker=helper.id,
    ))
    imposter = world.add(Entity(
        id="Imposter",
        kind="character",
        type="chef",
        label="the pretend helper",
        traits=["hush-hush"],
        meters={"anxiety": 1.0},
        memes={"secret": 1.0, "suspense": 2.0},
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        clue=clue,
        imposter=imposter,
        scene=scene,
        prize=prize,
    )

    world.say(f"{detective.id} was a little {detective.type} who loved detective games.")
    world.say(f"{detective.pronoun().capitalize()} liked {scene.verb} and watching small clues.")
    world.say(f"That morning, the cafe smelled like warm syrup and fresh pancakes.")

    world.para()
    world.say(f"{scene.noise} made {detective.id} lift {detective.pronoun('possessive')} head.")
    world.say(f"A helper in a clean apron smiled too quickly and said they knew where the missing breakfast item was.")
    world.say(f"But something felt off, because the helper's name tag looked crooked and {scene.risk}.")

    world.para()
    world.say(f"{detective.id} narrowed {detective.pronoun('possessive')} eyes and decided to impersonate no one, only to pay close attention.")
    detective.meters["focus"] += 1.0
    detective.memes["suspense"] += 1.0

    if scene.id == "kitchen":
        world.say(f"{detective.id} picked the pancake with the shiny syrup spot, because the spot matched the trail under the table.")
    elif scene.id == "counter":
        world.say(f"{detective.id} picked the pancake with the hidden mark, because it matched the plate stack at the counter.")
    else:
        world.say(f"{detective.id} picked the maple-smudged napkin, because it matched the footprints in the hall.")

    clue.meters["evidence"] = 1.0
    imposter.memes["caught"] = 1.0

    world.para()
    world.say(f"The pretend helper froze when {detective.id} held up the clue.")
    world.say(f"Then the real {helper.label_word if hasattr(helper, 'label_word') else helper.type} stepped in and said the helper had been impersonating someone kind.")
    world.say(f"The lie fell away, and the missing breakfast item was found beside the pancake stack.")

    world.para()
    world.say(f"In the end, {detective.id} ate a warm pancake while the true helper laughed softly at the table.")
    world.say(f"The cafe grew calm again, and the little clue had turned the suspense into a solved case.")

    world.facts["resolved"] = True
    world.facts["scene_id"] = scene.id
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    scene = _safe_fact(world, f, "scene")
    return [
        f'Write a short detective story for a small child about a {detective.type} named {detective.id}, suspense, and a pancake clue.',
        f'Tell a gentle mystery in {scene.place} where someone tries to impersonate a helper and the detective has to pick the right pancake clue.',
        f'Write a child-friendly suspense story that uses the word "pancake" and ends with the truth being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    scene = _safe_fact(world, f, "scene")
    prize = _safe_fact(world, f, "prize")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was the story about in {scene.place}?",
            answer=f"The story was about {detective.id}, a little {detective.type} detective.",
        ),
        QAItem(
            question=f"What did {detective.id} pick to follow the clue?",
            answer=f"{detective.id} picked the {prize.label}, because it matched the pancake trail and helped solve the case.",
        ),
        QAItem(
            question=f"Why did the detective feel suspense near the breakfast table?",
            answer=f"The detective felt suspense because someone was impersonating a helper, and the strange clue had to be checked carefully.",
        ),
        QAItem(
            question=f"What happened after the detective showed the clue?",
            answer=f"The pretend helper was exposed, the real {helper.type} stepped in, and the missing breakfast item was found.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "pancake": [
        QAItem(
            question="What is a pancake?",
            answer="A pancake is a soft, round breakfast food made from batter and cooked on a hot pan or griddle.",
        )
    ],
    "impersonate": [
        QAItem(
            question="What does it mean to impersonate someone?",
            answer="To impersonate someone means to pretend to be that person, often by copying how they look or act.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to figure out what happened.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important is about to happen, so you want to keep reading.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("pancake", "impersonate", "detective", "suspense") for item in WORLD_KNOWLEDGE.get(key, [])]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="kitchen", prize="badge", name="Mia", gender="girl", helper="waitress"),
    StoryParams(scene="counter", prize="spoon", name="Leo", gender="boy", helper="waiter"),
    StoryParams(scene="hall", prize="napkin", name="Nora", gender="girl", helper="chef"),
]


ASP_RULES = r"""
scene(kitchen). scene(counter). scene(hall).
pancake_scene(S) :- scene(S).
prize(spoon). prize(badge). prize(napkin).
valid(S,P) :- pancake_scene(S), prize(P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world with a pancake clue and suspense.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if getattr(args, "scene", None) and getattr(args, "prize", None):
        if (getattr(args, "scene", None), getattr(args, "prize", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos if (not getattr(args, "scene", None) or c[0] == getattr(args, "scene", None)) and (not getattr(args, "prize", None) or c[1] == getattr(args, "prize", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    scene, prize = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(scene=scene, prize=prize, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible scene/prize combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
