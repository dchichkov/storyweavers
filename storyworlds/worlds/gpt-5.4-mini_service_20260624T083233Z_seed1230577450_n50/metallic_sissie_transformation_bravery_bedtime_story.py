#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a shiny object, a shy feeling, and a
gentle transformation into bravery.

Seed tale shape:
- A little child named Sissie feels shy at bedtime.
- A metallic star or charm is too bright to place under the pillow at first.
- A small fear about the dark or a creaky sound creates tension.
- A comforting bedtime ritual transforms the mood.
- By the end, Sissie feels brave and the metallic thing becomes part of a cozy
  lullaby-like ending image.

The world is intentionally small and constraint-checked:
- There is one child, one caregiver, one bedtime setting, one meaningful object.
- The "transformation" is emotional and symbolic rather than magical chaos.
- Bravery must arise from a concrete bedtime helper/action that resolves fear.

The script follows the shared storyworld contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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

    caregiver: object | None = None
    child: object | None = None
    obj: object | None = None
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    place: str = "the nursery"
    indoor: bool = True
    gentle: bool = True
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    shiny: bool = False
    gives_comfort: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Change:
    id: str
    trigger: str
    result: str
    required: str
    cue: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, gentle=True),
    "bedroom": Setting(place="the bedroom", indoor=True, gentle=True),
    "attic_room": Setting(place="the attic room", indoor=True, gentle=True),
}

OBJECTS = {
    "star": Object(id="star", label="metallic star", phrase="a tiny metallic star", shiny=True, gives_comfort=True),
    "bell": Object(id="bell", label="metallic bell", phrase="a small metallic bell", shiny=True, gives_comfort=True),
    "button": Object(id="button", label="metallic button", phrase="a round metallic button", shiny=True, gives_comfort=False),
}

CHANGES = {
    "bravery": Change(
        id="bravery",
        trigger="soft_lamp",
        result="brave",
        required="comfort",
        cue="the lamp glowed like a little moon",
    ),
    "transformation": Change(
        id="transformation",
        trigger="lullaby",
        result="settled",
        required="comfort",
        cue="the lullaby turned the room quiet and smooth",
    ),
}

GIRL_NAMES = ["Sissie", "Mina", "Lila", "Nora", "Miri"]
BOY_NAMES = ["Toby", "Finn", "Noel", "Owen", "Pip"]
CAREGIVERS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    object_id: str
    name: str = "Sissie"
    gender: str = "girl"
    caregiver: str = "mother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _is_shy(child: Entity) -> bool:
    return child.memes.get("shy", 0.0) >= THRESHOLD


def _is_brave(child: Entity) -> bool:
    return child.memes.get("brave", 0.0) >= THRESHOLD


def _is_comforted(child: Entity) -> bool:
    return child.memes.get("comfort", 0.0) >= THRESHOLD


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=params.caregiver))
    obj_cfg = _safe_lookup(OBJECTS, params.object_id)
    obj = world.add(Entity(
        id=obj_cfg.id,
        type="thing",
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
        caretaker=caregiver.id,
    ))

    child.memes["shy"] = 1.0
    child.memes["wonder"] = 1.0
    obj.meters["shiny"] = 1.0 if obj_cfg.shiny else 0.2
    obj.meters["comfort"] = 1.0 if obj_cfg.gives_comfort else 0.0

    world.facts.update(child=child, caregiver=caregiver, obj=obj, obj_cfg=obj_cfg)
    return world


def tell(world: World) -> World:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    obj: Entity = f["obj"]
    obj_cfg: Object = f["obj_cfg"]

    world.say(
        f"{child.id} was a little {child.type} who loved bedtime, but {child.pronoun('possessive')} heart sometimes fluttered like a moth in the dark."
    )
    world.say(
        f"On the pillow sat {obj_cfg.phrase}, and it looked so metallic and bright that {child.id} could not stop staring at it."
    )

    world.para()
    world.say(
        f"That night, {child.id} heard a tiny creak from the hall and hugged {obj.it()} close."
    )
    child.memes["shy"] += 1.0
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0

    if obj_cfg.gives_comfort:
        world.say(
            f"{caregiver.pronoun().capitalize()} noticed the worry and lit a soft lamp beside the bed."
        )
        child.memes["comfort"] += 1.0
        child.memes["shy"] = 0.0
        world.say(
            f'"The lamp glows like a little moon," {caregiver.pronoun()} whispered. "You can be brave while we keep the room cozy."'
        )
        child.memes["brave"] += 1.0

        world.para()
        world.say(
            f"Then {caregiver.pronoun()} hummed a slow lullaby, and the whole room felt as smooth as a tucked-in blanket."
        )
        child.memes["settled"] = 1.0
        world.say(
            f"{child.id} smiled, held the metallic {obj.label.split()[-1]} against {child.pronoun('possessive')} chest, and found that brave feelings could grow right beside sleepy ones."
        )
    else:
        world.say(
            f"{caregiver.pronoun().capitalize()} sat beside the bed and spoke in a quiet voice until {child.id} could breathe slowly again."
        )
        child.memes["comfort"] += 1.0
        child.memes["brave"] += 1.0
        child.memes["settled"] = 1.0
        world.say(
            f"By the time the room grew still, {child.id} was no longer shaking, but the little metallic {obj.label.split()[-1]} stayed on the shelf instead of under the pillow."
        )

    world.facts["resolved"] = _is_brave(child) and _is_comforted(child)
    return world


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    obj_cfg: Object = f["obj_cfg"]
    return [
        f"Write a bedtime story for a young child about {child.id}, a {obj_cfg.label}, and a gentle transformation into bravery.",
        f"Tell a cozy story where {child.id} feels shy at bedtime, notices something {obj_cfg.label}, and becomes brave with help from a caregiver.",
        f"Write a short bedtime tale that includes the words 'metallic' and 'bravery' and ends with a calm, cozy feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    obj: Entity = f["obj"]
    obj_cfg: Object = f["obj_cfg"]

    qas = [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {child.id}, a little {child.type}, and the bedtime moment {child.id} shares with {caregiver.pronoun('possessive')} caregiver.",
        ),
        QAItem(
            question=f"What metallic thing did {child.id} notice at bedtime?",
            answer=f"{child.id} noticed {obj_cfg.phrase}. It was the shiny little thing that made the room feel extra special.",
        ),
        QAItem(
            question=f"What changed in {child.id} by the end of the story?",
            answer=f"{child.id} changed from shy and worried to calm and brave. The bedtime fear softened, and the child settled down peacefully.",
        ),
    ]
    if f.get("resolved"):
        qas.append(
            QAItem(
                question=f"How did the caregiver help {child.id} become brave?",
                answer=f"The caregiver helped by lighting a soft lamp and humming a lullaby, which gave {child.id} comfort and made bravery feel possible.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does metallic mean?",
            answer="Metallic means shiny, like metal. A metallic thing can sparkle when light touches it.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being able to face a scary feeling or hard moment and keep going anyway.",
        ),
        QAItem(
            question="Why can a lullaby help at bedtime?",
            answer="A lullaby can help because its slow, soft sounds make the room feel safe and sleepy.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for obj_id, obj in OBJECTS.items():
            if setting.gentle and obj.shiny:
                out.append((place, obj_id))
    return out


def explain_rejection(place: str, obj_id: str) -> str:
    return f"(No story: the combination of {place} and {obj_id} does not fit the gentle bedtime shape.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
obj(O) :- object(O).

shiny_obj(O) :- shiny(O).
comfort_obj(O) :- comforts(O).

valid(P, O) :- place(P), obj(O), gentle(P), shiny_obj(O).

transforms_into_brave(C) :- comforted(C), brave(C).
story_ok(P, O) :- valid(P, O), transforms_into_brave(child).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.gentle:
            lines.append(asp.fact("gentle", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.shiny:
            lines.append(asp.fact("shiny", oid))
        if o.gives_comfort:
            lines.append(asp.fact("comforts", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a metallic bedtime transformation into bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    if getattr(args, "place", None) and getattr(args, "object_id", None):
        if (getattr(args, "place", None), getattr(args, "object_id", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object_id", None) is None or c[1] == getattr(args, "object_id", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, object_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or "girl"
    name = getattr(args, "name", None) or ("Sissie" if gender == "girl" else rng.choice(BOY_NAMES))
    caregiver = getattr(args, "caregiver", None) or rng.choice(CAREGIVERS)
    return StoryParams(place=place, object_id=object_id, name=name, gender=gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world)
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
    StoryParams(place="nursery", object_id="star", name="Sissie", gender="girl", caregiver="mother"),
    StoryParams(place="bedroom", object_id="bell", name="Mina", gender="girl", caregiver="father"),
    StoryParams(place="attic_room", object_id="button", name="Toby", gender="boy", caregiver="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object) combos:\n")
        for place, obj in combos:
            print(f"  {place:12} {obj}")
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
            header = f"### {p.name}: {p.object_id} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
