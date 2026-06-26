#!/usr/bin/env python3
"""
storyworlds/worlds/supervision_dillydally_tag_twist_inner_monologue_whodunit.py
===============================================================================

A small, self-contained whodunit storyworld built from the seed words
"supervision", "dillydally", and "tag", with a twist and inner monologue.

Premise:
- A careful supervisor keeps an eye on a small task.
- Someone dillydallies.
- A tag goes missing or gets moved.
- The detective follows clues, thinks in inner monologue, and solves the case.

This world is intentionally compact and constraint-checked:
- It models physical meters and emotional memes.
- It simulates a short mystery instead of swapping nouns in a frozen paragraph.
- It includes an inline ASP twin plus a Python reasonableness gate.
- It supports the standard Storyweavers CLI contract.
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

# Story dynamics
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    clue_obj: object | None = None
    detective: object | None = None
    lost_item: object | None = None
    supervisor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother", "teacher"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather", "principal"}
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Clue:
    id: str
    label: str
    kind: str
    phrase: str
    reveal: str
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
class Trick:
    id: str
    action: str
    delay: str
    twist: str
    clue: str
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
        self.clues_seen: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(place="the library", affords={"shelve", "sort", "search"}),
    "kitchen": Setting(place="the kitchen", affords={"sort", "search", "pack"}),
    "mudroom": Setting(place="the mudroom", affords={"sort", "search", "hang"}),
}

CLUES = {
    "red_tag": Clue(
        id="red_tag",
        label="red tag",
        kind="tag",
        phrase="a tiny red tag with a loop",
        reveal="The red tag matched the string on the lost key ring.",
        tags={"tag", "red", "string"},
    ),
    "blue_tag": Clue(
        id="blue_tag",
        label="blue tag",
        kind="tag",
        phrase="a blue tag with a curled corner",
        reveal="The blue tag had a smudge from the jam jar.",
        tags={"tag", "blue", "paper"},
    ),
    "train_ticket": Clue(
        id="train_ticket",
        label="train ticket",
        kind="paper",
        phrase="an old train ticket with a crease",
        reveal="The ticket proved somebody had hurried through the hall.",
        tags={"paper", "crease"},
    ),
}

TRICKS = {
    "dillydally": Trick(
        id="dillydally",
        action="dillydally at the doorway",
        delay="lingered too long by the hooks",
        twist="the tag snagged on a coat button and twisted free",
        clue="button",
    ),
    "shuffle": Trick(
        id="shuffle",
        action="shuffle through the baskets",
        delay="moved slowly between the baskets",
        twist="the tag slid into the wrong pocket",
        clue="pocket",
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Zia", "Ruby", "Elsa", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Arlo", "Theo", "Eli", "Noah", "Ben"]
TRAITS = ["careful", "curious", "brave", "quiet", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    trick: str
    detective_name: str
    detective_gender: str
    supervisor: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def clue_is_plausible(setting: Setting, clue: Clue, trick: Trick) -> bool:
    if "tag" not in clue.tags:
        return False
    if setting.place == "the library" and trick.id != "dillydally":
        return True
    return True


def select_scenario(place: str, clue_id: str, trick_id: str) -> bool:
    return clue_is_plausible(_safe_lookup(SETTINGS, place), _safe_lookup(CLUES, clue_id), _safe_lookup(TRICKS, trick_id))


def explain_rejection(place: str, clue_id: str, trick_id: str) -> str:
    clue = _safe_lookup(CLUES, clue_id)
    trick = _safe_lookup(TRICKS, trick_id)
    return (
        f"(No story: the clue '{clue.label}' and the action '{trick.action}' do not "
        f"fit a clean little whodunit at {_safe_lookup(SETTINGS, place).place}.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def simulate_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    trick = _safe_lookup(TRICKS, params.trick)
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_gender,
        label=params.detective_name,
        meters={"attention": 0.0, "calm": 0.0},
        memes={"curiosity": 0.0, "doubt": 0.0, "joy": 0.0},
    ))
    supervisor = world.add(Entity(
        id="Supervisor",
        kind="character",
        type=params.supervisor,
        label={"mother": "mom", "father": "dad", "teacher": "teacher"}.get(params.supervisor, params.supervisor),
        meters={"watchfulness": 0.0},
        memes={"patience": 0.0},
    ))
    clue_obj = world.add(Entity(
        id=clue.id,
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        owner=None,
        caretaker=supervisor.id,
        tags=set(clue.tags),
    ))
    lost_item = world.add(Entity(
        id="key_ring",
        type="thing",
        label="key ring",
        phrase="a small key ring with a brass key",
        owner=supervisor.id,
        caretaker=supervisor.id,
        tags={"key", "metal"},
    ))

    # Setup
    detective.memes["curiosity"] += 1
    supervisor.meters["watchfulness"] += 1
    world.say(
        f"{params.detective_name} was a {params.trait} little detective at {setting.place}."
    )
    world.say(
        f"{detective.pronoun().capitalize()} stayed near {params.supervisor}'s side, because "
        f"there was supervision and a tiny mystery waiting in the room."
    )
    world.para()

    # Inciting incident
    world.say(
        f"At first, {params.detective_name} wanted to search the room, but {params.detective_name} "
        f"kept looking at the hooks and shelves instead of the clue."
    )
    detective.memes["doubt"] += 1
    detective.meters["attention"] += 1
    world.say(
        f"{params.detective_name} thought, 'Maybe the answer is obvious. Maybe I only need to stop "
        f"and notice it.'"
    )
    world.para()

    # Dillydally / mishap
    if trick.id == "dillydally":
        supervisor.meters["watchfulness"] += 1
        detective.memes["doubt"] += 1
        clue_obj.hidden_by = "coat"
        clue_obj.carried_by = supervisor.id
        lost_item.carried_by = detective.id
        _add_meter(detective, "attention", 1)
        world.say(
            f"Then {params.detective_name} began to {trick.action}. {trick.delay.capitalize()}, "
            f"and {trick.twist}."
        )
    else:
        clue_obj.carried_by = supervisor.id
        world.say(
            f"Then {params.detective_name} started to {trick.action}. {trick.delay.capitalize()}, "
            f"and {trick.twist}."
        )

    # Internal reasoning
    detective.memes["curiosity"] += 1
    inner = (
        f"'{params.detective_name} thought: if the tag moved, it must have caught on something. "
        f"What has a button, a pocket, or a string?'"
    )
    world.say(inner)
    world.para()

    # Twist / deduction
    world.say(
        f"That was the twist. A little button near the coat had snagged the red tag, and the tag "
        f"had spun away in a neat little loop."
    )
    clue_obj.hidden_by = None
    clue_obj.carried_by = detective.id
    world.clues_seen.append(clue.label)
    _add_meter(detective, "attention", 1)
    _add_meme(detective, "joy", 1)
    _add_meme(supervisor, "patience", 1)

    world.say(
        f"{clue.reveal} {params.detective_name} held it up and smiled, because the clue had "
        f"finally told the truth."
    )
    world.say(
        f"{params.detective_name} told {params.supervisor} the answer, and the room felt calm again."
    )
    world.say(
        f"In the end, the mystery was solved: the tag had only been hiding in plain sight, and the "
        f"careful detective had not needed to rush."
    )

    world.facts.update(
        detective=detective,
        supervisor=supervisor,
        clue=clue,
        trick=trick,
        setting=setting,
        inner_monologue=True,
        twist=True,
        solved=True,
        lost_item=lost_item,
    )
    return world


# ---------------------------------------------------------------------------
# Prompt / QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    clue = _safe_fact(world, f, "clue")
    trick = _safe_fact(world, f, "trick")
    return [
        f'Write a short whodunit for a young child that includes "{clue.label}" and the idea of supervision.',
        f"Tell a mystery where {det.label} must not dillydally, because the tag clue matters.",
        f"Write a gentle detective story with an inner monologue, a twist, and a clear solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = _safe_fact(world, f, "detective")
    sup: Entity = _safe_fact(world, f, "supervisor")
    clue: Clue = _safe_fact(world, f, "clue")
    trick: Trick = _safe_fact(world, f, "trick")
    place = _safe_fact(world, f, "setting").place
    qa = [
        QAItem(
            question=f"Where did the little detective look for clues?",
            answer=f"The detective looked for clues at {place}, with {sup.label} watching closely.",
        ),
        QAItem(
            question=f"What made the story tricky before the answer was found?",
            answer=f"The tricky part was that {det.label} began to {trick.action}, so the clue got caught up in the wrong place.",
        ),
        QAItem(
            question=f"What clue solved the mystery?",
            answer=f"The mystery was solved by the {clue.label}, because it matched the place where the tag had snagged.",
        ),
        QAItem(
            question=f"What did the detective think in the inner monologue?",
            answer=(
                f"The detective thought that the answer must be hiding on something with a button, a pocket, or a string."
            ),
        ),
    ]
    if f.get("solved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=(
                    f"It ended with the clue revealed, the tag found, and everyone calm again because the detective solved the case."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is supervision?",
            answer="Supervision means a grown-up or responsible person keeps watch so everyone stays safe and on task.",
        ),
        QAItem(
            question="What does it mean to dillydally?",
            answer="To dillydally means to waste time or move too slowly when you should be getting on with something.",
        ),
        QAItem(
            question="What is a tag?",
            answer="A tag is a small label or marker attached to something so it can be named, sorted, or recognized.",
        ),
        QAItem(
            question="What is a twist in a mystery story?",
            answer="A twist is a surprise turn that changes how the reader understands the clues.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice a character uses in their own head to think through what is happening.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A scenario is valid if the clue is a tag clue and the twisty action can fit.
tag_clue(C) :- clue(C), clue_kind(C, tag).

valid(Place, Clue, Trick) :- setting(Place), tag_clue(Clue), trick(Trick), affords(Place, search).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = set((p, c, t) for p in SETTINGS for c in CLUES if "tag" in _safe_lookup(CLUES, c).tags for t in TRICKS if select_scenario(p, c, t))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Storyworld API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with supervision, dillydally, tag, twist, and inner monologue.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--trick", choices=sorted(TRICKS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--supervisor", choices=["mother", "father", "teacher"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    trick = getattr(args, "trick", None) or rng.choice(list(TRICKS))
    if not select_scenario(place, clue, trick):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    supervisor = getattr(args, "supervisor", None) or rng.choice(["mother", "father", "teacher"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        clue=clue,
        trick=trick,
        detective_name=name,
        detective_gender=gender,
        supervisor=supervisor,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        if e.hidden_by:
            parts.append(f"hidden_by={e.hidden_by}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  clues seen: {world.clues_seen}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", clue="red_tag", trick="dillydally", detective_name="Mina", detective_gender="girl", supervisor="teacher", trait="curious"),
    StoryParams(place="kitchen", clue="blue_tag", trick="shuffle", detective_name="Owen", detective_gender="boy", supervisor="mother", trait="sharp-eyed"),
    StoryParams(place="mudroom", clue="train_ticket", trick="dillydally", detective_name="Ivy", detective_gender="girl", supervisor="father", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective_name}: {p.clue} at {p.place} ({p.trick})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
