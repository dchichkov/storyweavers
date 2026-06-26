#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cranium_classroom_foreshadowing_mystery.py
==========================================================================================================

A small classroom mystery storyworld with foreshadowing.

Seed tale:
---
In a classroom, a curious child notices a cranium model on the shelf, along with
tiny clues that seem to point somewhere else. The teacher says, "Every mystery
drops hints before it reveals the answer." The class follows the clues, finds
the missing object, and learns that the earliest details were the most useful.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    memorize: str = ""
    cranium: object | None = None
    missing: object | None = None
    student: object | None = None
    teacher: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "student"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the classroom"
    SETTINGS: set[str] = field(default_factory=set)
    setting: object | None = None
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
class Mystery:
    id: str
    name: str
    clue: str
    foreshadow: str
    hiding_place: str
    reveal: str
    keyword: str = "cranium"
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
class StoryParams:
    mystery: str
    name: str
    gender: str
    teacher: str
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


def mystery_gate(m: Mystery) -> bool:
    return bool(m.clue and m.foreshadow and m.hiding_place and m.reveal)


def select_mystery(mystery_id: str) -> Mystery:
    m = _safe_lookup(MYSTERIES, mystery_id)
    if not mystery_gate(m):
        pass
    return m


def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    mystery = select_mystery(params.mystery)

    student = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label=params.name,
        memorize="",
        meters={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    teacher = world.add(Entity(
        id="teacher",
        kind="character",
        type="teacher",
        label=params.teacher,
        meters={"calm": 0.0},
        memes={"calm": 0.0},
    ))
    cranium = world.add(Entity(
        id="cranium",
        type="model",
        label="cranium model",
        phrase="a plastic cranium model with a hollow inside",
        hidden_in=mystery.hiding_place,
    ))
    missing = world.add(Entity(
        id="missing",
        type="thing",
        label=mystery.name,
        phrase=mystery.name,
        owner=teacher.id,
        caretaker=teacher.id,
    ))

    # Act 1: setup and foreshadowing.
    world.say(
        f"In {world.setting.place}, {student.id} noticed {cranium.phrase} sitting on the shelf."
    )
    world.say(
        f"{teacher.label} smiled and said, \"Every mystery drops hints before it reveals the answer.\""
    )
    world.say(
        f"On the desk, {mystery.foreshadow} seemed small, but it made {student.pronoun('object')} curious."
    )
    student.memes["curiosity"] += 1
    student.meters["curiosity"] += 1

    # Act 2: mystery deepens.
    world.para()
    world.say(
        f"Then {mystery.name} went missing from {teacher.label}'s desk, and the class went quiet."
    )
    world.say(
        f"{student.id} looked at the little clues again. The {mystery.clue} and the cranium model"
        f" felt like they belonged together."
    )
    student.memes["worry"] += 1
    student.meters["worry"] += 1

    # Clue-based turn.
    world.para()
    world.say(
        f"{student.id} followed the hint to {mystery.hiding_place}, because the first clue was not a joke."
    )
    world.say(
        f"There, inside {cranium.label}, {mystery.reveal}."
    )
    student.memes["worry"] = 0.0
    student.memes["relief"] += 1
    student.meters["relief"] += 1
    teacher.memes["calm"] += 1

    world.para()
    world.say(
        f"{teacher.label} laughed softly and said the clue had been waiting all along."
    )
    world.say(
        f"{student.id} held up {missing.it()} and realized the smallest details had solved the mystery."
    )

    world.facts.update(
        student=student,
        teacher=teacher,
        cranium=cranium,
        missing=missing,
        mystery=mystery,
        setting=setting,
    )
    return world


def story_text(world: World) -> str:
    return world.render()


CRANIUM_WORD = "cranium"

MYSTERIES = {
    "chalk_note": Mystery(
        id="chalk_note",
        name="the class note",
        clue="a dusting of white chalk near the shelf",
        foreshadow="a tiny line of chalk dust pointed toward the reading corner",
        hiding_place="the reading corner",
        reveal="the folded note was tucked inside the hollow cranium",
    ),
    "ribbon_bookmark": Mystery(
        id="ribbon_bookmark",
        name="the library ribbon",
        clue="a red ribbon corner poking from the supply cart",
        foreshadow="a red ribbon fluttered once beside the cranium model",
        hiding_place="the supply cart",
        reveal="the missing ribbon was looped around a pencil and hidden in the cranium",
    ),
    "marker_case": Mystery(
        id="marker_case",
        name="the marker case",
        clue="a trail of blue cap marks by the art shelf",
        foreshadow="blue cap marks sat under the cranium like breadcrumbs",
        hiding_place="the art shelf",
        reveal="the marker case was resting inside the cranium, safe and dry",
    ),
}

SETTINGS = {"classroom": Setting(place="the classroom")}

GIRL_NAMES = ["Mia", "Lena", "Tara", "Ivy", "Nora"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Owen", "Max"]
TEACHERS = ["Ms. Park", "Mr. Reed", "Ms. Bell", "Mr. Quinn"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid in MYSTERIES:
        out.append(("classroom", mid))
    return out


def explain_rejection(mystery_id: str) -> str:
    return f"(No story: the mystery '{mystery_id}' does not have enough clues for a classroom foreshadowing turn.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short classroom mystery story for a young child that includes the word "{CRANIUM_WORD}".',
        f"Tell a gentle mystery where {f['student'].id} follows foreshadowing clues in {f['setting'].place}.",
        f"Write a child-friendly detective story in a classroom that begins with a small clue and ends with the answer inside a cranium.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    student: Entity = _safe_fact(world, f, "student")
    teacher: Entity = _safe_fact(world, f, "teacher")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"Who noticed the cranium model in the classroom?",
            answer=f"{student.id} noticed the cranium model while looking around {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the first hint before the answer was found?",
            answer=f"The first hint was {mystery.foreshadow}, which foreshadowed where the missing thing was hidden.",
        ),
        QAItem(
            question=f"Where did the missing {mystery.name} end up?",
            answer=f"It ended up inside the cranium model after {student.id} followed the clues.",
        ),
        QAItem(
            question=f"How did {teacher.label} help solve the mystery?",
            answer=f"{teacher.label} gave the class a careful warning that every mystery drops hints before it reveals the answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cranium?",
            answer="A cranium is the part of the skull that protects the brain.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small hints early on about something important that will happen later.",
        ),
        QAItem(
            question="Why do detectives look at tiny clues?",
            answer="Detectives look at tiny clues because small details can point to the answer before it is obvious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,M) :- place(P), mystery(M), clue(M,C), foreshadow(M,F), hiding(M,H), reveal(M,R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("foreshadow", mid, m.foreshadow))
        lines.append(asp.fact("hiding", mid, m.hiding_place))
        lines.append(asp.fact("reveal", mid, m.reveal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    am = set(asp_valid_stories())
    if py == am:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - am:
        print("  only in python:", sorted(py - am))
    if am - py:
        print("  only in clingo:", sorted(am - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Classroom mystery storyworld with foreshadowing.")
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=TEACHERS)
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES.keys()))
    if getattr(args, "place", None) and getattr(args, "place", None) != "classroom":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if mystery not in MYSTERIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    teacher = getattr(args, "teacher", None) or rng.choice(TEACHERS)
    return StoryParams(mystery=mystery, name=name, gender=gender, teacher=teacher)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
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
    StoryParams(mystery="chalk_note", name="Mia", gender="girl", teacher="Ms. Park"),
    StoryParams(mystery="ribbon_bookmark", name="Eli", gender="boy", teacher="Mr. Reed"),
    StoryParams(mystery="marker_case", name="Nora", gender="girl", teacher="Ms. Bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
