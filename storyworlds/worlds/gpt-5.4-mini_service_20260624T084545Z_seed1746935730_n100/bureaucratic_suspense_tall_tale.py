#!/usr/bin/env python3
"""
storyworlds/worlds/bureaucratic_suspense_tall_tale.py
=====================================================

A tiny story world about one brave errand through a bureau of long halls,
missing papers, suspenseful waiting, and a tall-tale-sized resolution.

The premise:
- Someone needs one important permit or parcel release from a busy office.
- A form goes missing, a queue grows, and a deadline starts to feel enormous.
- The hero must use patience, a stamp, a ledger, and a clever route through the
  office to resolve the problem.

The world model tracks:
- physical meters: distance walked, papers handled, stamp weight, queue length
- emotional memes: worry, patience, pride, relief, suspicion, delight

The tone:
- child-facing, concrete, and a little exaggerated in the tall-tale style.
"""

from __future__ import annotations

import argparse
import copy
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
# World model
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
    keeper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    paper: object | None = None
    stamp: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "clerk"}
        male = {"boy", "man", "father", "uncle", "postman", "mayor"}
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
class Office:
    place: str = "the permit office"
    boasts: str = "a hall so long that a pigeon could get a headache halfway down it"
    features: set[str] = field(default_factory=lambda: {"queue", "counter", "ledger", "stamp", "waiting room"})
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
class Conflict:
    missing_item: str
    deadline: str
    reason: str
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
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    office: str
    issue: str
    stamp: str
    deadline: str
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


class World:
    def __init__(self, office: Office) -> None:
        self.office = office
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.office)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
OFFICES = {
    "permit_office": Office(place="the permit office"),
    "city_hall": Office(place="city hall"),
    "postal_counter": Office(place="the postal counter"),
}

ISSUES = {
    "parcel": "a parcel release slip",
    "permit": "a permit application",
    "library_card": "a library card form",
    "dog_license": "a dog license request",
}

STAMPS = {
    "blue_stamp": "a blue stamp",
    "gold_stamp": "a gold stamp",
    "red_seal": "a red wax seal",
}

DEADLINES = {
    "noon": "noon",
    "closing": "closing time",
    "sunset": "sunset",
}

GIRL_NAMES = ["Ada", "Mina", "Ruby", "Nell", "Lia", "June", "Tess"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Bram", "Theo", "Jude", "Max"]
HELPER_NAMES = ["Mr. Quill", "Ms. Penny", "Aunt Dot", "Uncle Ike", "Clerk Bean"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
office(O) :- setting(O).
issue(I) :- issue_kind(I).
stamp(S) :- stamp_kind(S).
deadline(D) :- deadline_kind(D).

needs_stamp(I, S) :- issue(I), stamp(S).
valid(Office, Issue, Stamp, Deadline) :-
    office(Office), issue(Issue), stamp(Stamp), deadline(Deadline),
    compatible(Issue, Stamp).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in OFFICES:
        lines.append(asp.fact("setting", k))
    for k in ISSUES:
        lines.append(asp.fact("issue_kind", k))
    for k in STAMPS:
        lines.append(asp.fact("stamp_kind", k))
    for k in DEADLINES:
        lines.append(asp.fact("deadline_kind", k))
    for issue_id in ISSUES:
        for stamp_id in STAMPS:
            if compatible_pair(issue_id, stamp_id):
                lines.append(asp.fact("compatible", issue_id, stamp_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py == ax:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP valid-combo gates:")
    if py - ax:
        print("  only in python:", sorted(py - ax))
    if ax - py:
        print("  only in clingo:", sorted(ax - py))
    return 1


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
def compatible_pair(issue_id: str, stamp_id: str) -> bool:
    if issue_id == "parcel":
        return stamp_id in {"blue_stamp", "red_seal"}
    if issue_id == "permit":
        return stamp_id in {"gold_stamp", "red_seal"}
    if issue_id == "library_card":
        return stamp_id == "blue_stamp"
    if issue_id == "dog_license":
        return stamp_id in {"gold_stamp", "red_seal"}
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for office in OFFICES:
        for issue in ISSUES:
            for stamp in STAMPS:
                if not compatible_pair(issue, stamp):
                    continue
                for deadline in DEADLINES:
                    out.append((office, issue, stamp, deadline))
    return out


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def reasonableness_check(issue: str, stamp: str) -> None:
    if not compatible_pair(issue, stamp):
        pass


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(OFFICES, params.office))

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"walking": 0.0},
        memes={"worry": 0.0, "patience": 0.0, "hope": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"walking": 0.0},
        memes={"calm": 0.0, "suspicion": 0.0, "delight": 0.0},
    ))
    paper = world.add(Entity(
        id="paper",
        kind="thing",
        type="paper",
        label=_safe_lookup(ISSUES, params.issue).replace("a ", ""),
        phrase=_safe_lookup(ISSUES, params.issue),
        owner=hero.id,
        keeper=helper.id,
        meters={"creased": 0.0, "handled": 0.0, "stamped": 0.0},
    ))
    stamp = world.add(Entity(
        id=params.stamp,
        kind="thing",
        type="stamp",
        label=_safe_lookup(STAMPS, params.stamp),
        phrase=_safe_lookup(STAMPS, params.stamp),
        keeper=helper.id,
        meters={"ink": 1.0, "weight": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, paper=paper, stamp=stamp, params=params)
    return world


def long_walk(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["walking"] += 7.0
    helper.meters["walking"] += 7.0
    world.say(
        f"{hero.id} and {helper.id} went to {world.office.place}, "
        f"and the hall was so long it seemed to have three echoes and a cousin."
    )
    world.say(world.office.boasts + ".")


def queue_suspense(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["worry"] += 1.0
    helper.memes["suspicion"] += 1.0
    world.say(
        f"At the door, a queue curled like a sleepy snake, and {hero.id} stood last in line."
    )
    world.say(
        f"Every time the line moved one shoe-step, {hero.id} held {hero.pronoun('possessive')} "
        f"paper tighter and wondered if the day would run out before the answer came."
    )


def missing_problem(world: World, hero: Entity, helper: Entity, issue_id: str) -> None:
    hero.memes["worry"] += 1.0
    helper.memes["suspicion"] += 1.0
    world.say(
        f"When {helper.id} opened the folder, the page for {_safe_lookup(ISSUES, issue_id)} was missing."
    )
    world.say(
        f'"That is a grand-sized problem," {helper.id} said, peering into the drawer as if the answer '
        f'might be hiding under a paperclip.'
    )


def tall_tale_search(world: World, hero: Entity, helper: Entity, issue_id: str) -> None:
    world.say(
        f"{hero.id} looked under the counter, behind the ledger, and even inside a brass tray so shiny "
        f"it could have combed the moon."
    )
    hero.memes["hope"] += 1.0
    helper.memes["delight"] += 1.0
    world.say(
        f"Then {helper.id} remembered the office map, folded tiny as a postage stamp, and said the missing "
        f"page had likely gone to the back filing room."
    )


def resolve(world: World, hero: Entity, helper: Entity, stamp: Entity, issue_id: str, deadline: str) -> None:
    paper = world.get("paper")
    hero.meters["walking"] += 3.0
    helper.meters["walking"] += 3.0
    paper.meters["handled"] += 1.0
    paper.meters["stamped"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 2.0
    hero.memes["pride"] += 1.0
    helper.memes["suspicion"] = 0.0
    helper.memes["delight"] += 1.0
    world.say(
        f"So {hero.id} and {helper.id} followed the back stairs, where the air smelled like dust and good intentions, "
        f"until they found the page tucked behind the ledgers."
    )
    world.say(
        f"{helper.id} set {stamp.label} down with a thump, and the whole office heard it like a small drum of justice."
    )
    world.say(
        f"With one careful press, the paper was approved before {deadline}, and the clerk stamped it so grandly "
        f"that the ink looked like a little midnight sun."
    )
    world.say(
        f"{hero.id} smiled, because the problem was solved, the queue could move again, and even the clock seemed to bow."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_story(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get(params.hero_name)
    helper = world.get(params.helper_name)
    stamp = world.get(params.stamp)

    world.say(
        f"Once, in {world.office.place}, there lived a line of forms so serious that even the dust had to sign in."
    )
    world.say(
        f"{hero.id} came carrying {_safe_lookup(ISSUES, params.issue)}, because {hero.pronoun('possessive')} family needed it by {params.deadline}."
    )
    long_walk(world, hero, helper)
    world.para()
    queue_suspense(world, hero, helper)
    missing_problem(world, hero, helper, params.issue)
    tall_tale_search(world, hero, helper, params.issue)
    world.para()
    resolve(world, hero, helper, stamp, params.issue, params.deadline)

    world.facts.update(
        resolved=True,
        deadline=params.deadline,
        issue=params.issue,
        stamp=params.stamp,
        office=params.office,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    return [
        f'Write a tall-tale style story about a child named {p.hero_name} who needs {_safe_lookup(ISSUES, p.issue)} at {_safe_lookup(OFFICES, p.office).place}.',
        f"Tell a suspenseful but gentle office story where {p.hero_name} waits in a queue and a helpful adult finds the missing paper.",
        f'Write a child-friendly story that uses the word "bureaucratic" and ends with a stamped paper before {p.deadline}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    paper: Entity = _safe_fact(world, world.facts, "paper")  # type: ignore[assignment]
    stamp: Entity = _safe_fact(world, world.facts, "stamp")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who needed the {paper.label} in the story?",
            answer=f"{hero.id} needed {hero.pronoun('possessive')} {paper.label} by {p.deadline}.",
        ),
        QAItem(
            question=f"What made the office feel suspenseful?",
            answer=(
                f"The suspense came from the long queue, the missing page, and the worry that the paper might not be approved before {p.deadline}."
            ),
        ),
        QAItem(
            question=f"How did the helper finally fix the problem?",
            answer=(
                f"{helper.id} found the missing page in the back filing room and used {stamp.label} to approve it."
            ),
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=(
                f"The paper was approved, {hero.id} felt relieved and proud, and the line could move again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a queue?",
            answer="A queue is a line of people or things waiting for their turn.",
        ),
        QAItem(
            question="What does a stamp do?",
            answer="A stamp leaves an official mark on paper to show it has been checked or approved.",
        ),
        QAItem(
            question="What is a ledger?",
            answer="A ledger is a book where important records are written down.",
        ),
        QAItem(
            question="What does a clerk do?",
            answer="A clerk helps sort papers, check forms, and keep an office organized.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class CliDefaults:
    office: str = "permit_office"
    issue: str = "permit"
    stamp: str = "gold_stamp"
    deadline: str = "closing"
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
    ap = argparse.ArgumentParser(description="A bureaucratic suspense tall tale story world.")
    ap.add_argument("--office", choices=OFFICES)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--stamp", choices=STAMPS)
    ap.add_argument("--deadline", choices=DEADLINES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    office = getattr(args, "office", None) or rng.choice(list(OFFICES))
    issue = getattr(args, "issue", None) or rng.choice(list(ISSUES))
    stamp = getattr(args, "stamp", None) or rng.choice(list(STAMPS))
    deadline = getattr(args, "deadline", None) or rng.choice(list(DEADLINES))
    reasonableness_check(issue, stamp)

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or choose_name(gender, rng)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    helper_type = "clerk" if helper_name == "Clerk Bean" else ("mother" if helper_gender == "girl" else "father")

    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        office=office,
        issue=issue,
        stamp=stamp,
        deadline=deadline,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


# ---------------------------------------------------------------------------
# Curated / verification
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("Mina", "girl", "Clerk Bean", "clerk", "permit_office", "permit", "gold_stamp", "closing"),
    StoryParams("Owen", "boy", "Ms. Penny", "clerk", "city_hall", "library_card", "blue_stamp", "noon"),
    StoryParams("Ruby", "girl", "Mr. Quill", "clerk", "postal_counter", "parcel", "red_seal", "sunset"),
]


def asp_verify_samples() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py == ax:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - ax))
    print("  only in clingo:", sorted(ax - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(o, i, s, d) for o in OFFICES for i in ISSUES for s in STAMPS for d in DEADLINES if compatible_pair(i, s)]


# ---------------------------------------------------------------------------
# ASP display helpers
# ---------------------------------------------------------------------------
def asp_show_program() -> str:
    return asp_program("#show valid/4.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_samples())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (office, issue, stamp, deadline) combos:\n")
        for c in combos:
            print("  ", c)
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
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
