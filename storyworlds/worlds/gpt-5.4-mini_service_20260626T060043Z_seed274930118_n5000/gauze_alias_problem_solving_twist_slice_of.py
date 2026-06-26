#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gauze_alias_problem_solving_twist_slice_of.py
================================================================================================

A standalone slice-of-life storyworld about a small problem, a gentle fix,
and a twist that changes what the characters think they know.

Seed tale used to build the world model:
---
A child finds a shy cat in the apartment courtyard. The cat has a sore paw
and a collar tag that says an alias the child does not recognize. The child and
parent use gauze to wrap the paw, then notice the alias on the tag matches a
missing-cat flyer from the bakery next door. The cat was not a stray at all.
It was a neighbor's pet with a secret nickname, and the little mystery gets
solved with a phone call, a soft wrap, and a warm homecoming.

Causal state updates:
---
    careful help + shaky paw -> paw pain drops, trust rises
    gauze wrap + clean hands -> wound protected
    tag check + missing flyer -> alias recognized, owner identified
    owner found -> worry falls, homecoming joy rises

Narrative instruments:
---
    Problem solving: the child notices clues, checks the tag, and compares it
                     with the flyer.
    Twist: the "stray" cat already has a home; the unfamiliar name is only an
           alias.
    Slice of life: the scene stays small, concrete, and domestic.
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
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    cat: object | None = None
    child: object | None = None
    flyer: object | None = None
    gauze: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    indoors: bool = False
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
class Problem:
    id: str
    noun: str
    verb: str
    risk: str
    symptom: str
    clue: str
    tags: set[str] = field(default_factory=set)
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
class Solution:
    id: str
    label: str
    phrase: str
    helps: set[str]
    uses: set[str]
    prep: str
    result: str
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


SETTINGS = {
    "courtyard": Setting(place="the apartment courtyard", indoors=False),
    "hallway": Setting(place="the building hallway", indoors=True),
    "kitchen": Setting(place="the kitchen table", indoors=True),
}

PROBLEMS = {
    "paw_scrape": Problem(
        id="paw_scrape",
        noun="scraped paw",
        verb="feel sore",
        risk="the cat might keep limping",
        symptom="a little red scrape on the paw",
        clue="a narrow collar tag",
        tags={"cat", "paw", "scrape"},
    ),
    "lost_name": Problem(
        id="lost_name",
        noun="mystery name",
        verb="stay unknown",
        risk="the owner might not be found",
        symptom="an unfamiliar word on the tag",
        clue="the tag says alias",
        tags={"alias", "tag", "name"},
    ),
}

SOLUTIONS = {
    "gauze_wrap": Solution(
        id="gauze_wrap",
        label="gauze",
        phrase="a soft roll of gauze",
        helps={"paw_scrape"},
        uses={"wrap", "protect"},
        prep="gently wrap the paw with gauze",
        result="kept the scrape safe and snug",
    ),
    "flyer_match": Solution(
        id="flyer_match",
        label="flyer",
        phrase="the missing-cat flyer from the bakery",
        helps={"lost_name"},
        uses={"match", "compare"},
        prep="compare the tag with the flyer",
        result="showed the cat had a home",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Lia", "Rosa", "Ivy", "Tess"]
BOY_NAMES = ["Owen", "Miles", "Noah", "Finn", "Theo", "Ben"]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    parent_type: str
    problem: str
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
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with gauze, alias, and a gentle twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, child_name=name, child_gender=gender, parent_type=parent, problem=problem)


ASP_RULES = r"""
problem(paw_scrape).
problem(lost_name).
solution(gauze_wrap).
solution(flyer_match).
helps(gauze_wrap,paw_scrape).
helps(flyer_match,lost_name).
uses(gauze_wrap,wrap).
uses(gauze_wrap,protect).
uses(flyer_match,match).
uses(flyer_match,compare).
valid(SP,SO) :- problem(SP), solution(SO), helps(SO,SP).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    for sid, sol in SOLUTIONS.items():
        for p in sorted(sol.helps):
            lines.append(asp.fact("helps", sid, p))
        for u in sorted(sol.uses):
            lines.append(asp.fact("uses", sid, u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, s) for p in PROBLEMS for s, sol in SOLUTIONS.items() if p in sol.helps}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def _render_story(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    cat = world.get("cat")
    flyer = world.get("flyer")
    gauze = world.get("gauze")
    problem = _safe_lookup(PROBLEMS, world.facts.get("problem"))
    if world.facts["problem"] == "paw_scrape":
        world.say(
            f"{c.id} found a shy cat by {world.setting.place} and noticed that one paw was sore."
        )
        world.say(
            f"The cat stayed still while {p.pronoun().capitalize()} got {gauze.label} ready, because the little scrape looked tender."
        )
        world.say(
            f"{c.id} remembered the narrow collar tag and read the strange word on it out loud: {cat.phrase}."
        )
        world.para()
        world.say(
            f"{c.id} and {p.id} walked to the bakery door, where a flyer asked for a missing cat."
        )
        world.say(
            f"Then came the twist: the flyer used the same alias as the tag."
        )
        world.say(
            f"It was not a stray after all. It was a family cat with a secret nickname, and the paw wrap had helped everyone slow down long enough to notice."
        )
        world.para()
        world.say(
            f"{p.id} made a phone call, {c.id} held the flyer, and the cat sat very politely in its gauze wrap."
        )
        world.say(
            f"By the time the owner arrived, the cat's paw was safe, the alias made sense, and the little courtyard mystery was solved."
        )
    else:
        world.say(
            f"{c.id} found a cat with a tag that said alias, but the name on the tag did not match the cat's shy little face."
        )
        world.say(
            f"With a flyer from the bakery and a careful look at the collar, {c.id} realized the odd word was only a nickname."
        )
        world.say(
            f"The cat was somebody's pet, not a stray at all, and the gauze was ready in case the paw needed help after the walk home."
        )
        world.para()
        world.say(
            f"{p.id} made the call, the owner answered, and the alias on the tag finally fit into place."
        )
        world.say(
            f"That was the twist, and it turned a small worry into a warm homecoming."
        )
    world.facts.update(
        child=c,
        parent=p,
        cat=cat,
        gauze=gauze,
        flyer=flyer,
        problem=problem,
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={"worry": 0.0, "delight": 0.0},
        memes={"curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        meters={"calm": 1.0},
        memes={"care": 1.0},
    ))
    cat = world.add(Entity(
        id="cat",
        kind="animal",
        type="cat",
        label="cat",
        phrase="Bean",
        meters={"paw_pain": 1.0 if params.problem == "paw_scrape" else 0.4},
        memes={"trust": 0.2},
        tags={"alias", "tag", "cat"},
    ))
    gauze = world.add(Entity(
        id="gauze",
        kind="thing",
        type="medical_supply",
        label="gauze",
        phrase="a soft roll of gauze",
        tags={"gauze", "wrap"},
    ))
    flyer = world.add(Entity(
        id="flyer",
        kind="thing",
        type="paper",
        label="flyer",
        phrase="a missing-cat flyer",
        tags={"flyer", "alias"},
    ))
    world.facts["problem"] = params.problem
    world.facts["place"] = params.place
    world.facts["child_name"] = params.child_name
    _render_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a young child that includes "gauze" and "alias".',
        f"Tell a gentle problem-solving story where {f['child_name']} helps a cat at {f['place']} and learns a surprising alias.",
        "Write a small domestic story with a twist: a simple fix becomes a clue that solves a tiny mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    p = _safe_fact(world, world.facts, "parent")
    cat = _safe_fact(world, world.facts, "cat")
    problem = _safe_fact(world, world.facts, "problem")
    if problem == "paw_scrape":
        return [
            QAItem(
                question=f"What problem did {c.id} notice first?",
                answer=f"{c.id} noticed that the cat had a sore paw with a small scrape.",
            ),
            QAItem(
                question=f"What did {p.id} use to help the cat?",
                answer=f"{p.id} used gauze to gently wrap the paw and keep it safe.",
            ),
            QAItem(
                question=f"What was surprising about the cat's name?",
                answer=f"The strange word on the tag was only an alias, not a brand-new owner name.",
            ),
        ]
    return [
        QAItem(question="What clue helped solve the mystery?", answer="The clue was the word alias on the tag and the matching missing-cat flyer."),
        QAItem(question="Why was the cat not a stray?", answer="The cat had a home, and the alias on the tag matched the flyer from the bakery."),
        QAItem(question="What gentle helper was ready in the story?", answer="Gauze was ready in case the paw needed a soft wrap."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gauze for?",
            answer="Gauze is a soft cloth used to wrap and protect a scrape or cut.",
        ),
        QAItem(
            question="What is an alias?",
            answer="An alias is another name, like a nickname or a secret name someone uses.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    return "\n".join(parts)


def valid_combos() -> list[tuple[str, str]]:
    return [("paw_scrape", "gauze_wrap"), ("lost_name", "flyer_match")]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="courtyard", child_name="Maya", child_gender="girl", parent_type="mother", problem="paw_scrape"),
    StoryParams(place="hallway", child_name="Owen", child_gender="boy", parent_type="father", problem="lost_name"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    p = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, child_name=name, child_gender=gender, parent_type=parent, problem=p)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
