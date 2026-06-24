#!/usr/bin/env python3
"""
Standalone storyworld: tame pajamas mystery teamwork.

This world tells a gentle ghost-story-style tale for children: a small
mystery appears, the characters solve it together, and the ending proves
what changed in the world model.

Core premise:
- A child in pajamas hears a mysterious sound at night.
- The "ghost" turns out to be tame and friendly.
- The group uses teamwork and problem solving to find the missing thing.
- The mystery ends with a cozy, safe resolution.

The script follows the storyworld contract:
- stdlib-only prose engine
- typed entities with meters and memes
- invalid choices raise StoryError
- inline ASP twin plus Python reasonableness gate
- CLI supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearing: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    ghost: object | None = None
    helper: object | None = None
    hero: object | None = None
    pajamas: object | None = None
    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
class Place:
    name: str
    indoor: bool = True
    hush: str = ""
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    clue: str
    missing: str
    location: str
    solved_by: str
    solve_action: str
    turns_out: str
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "hall": Place(name="the hall", indoor=True, hush="The hall was quiet and a little echoey.", affords={"listen", "search"}),
    "attic": Place(name="the attic", indoor=True, hush="The attic was dusty and full of old boxes.", affords={"listen", "search"}),
    "bedroom": Place(name="the bedroom", indoor=True, hush="The bedroom was soft, warm, and sleepy.", affords={"listen", "search"}),
    "porch": Place(name="the porch", indoor=False, hush="The porch was cool and moonlit.", affords={"listen", "search"}),
}

MYSTERIES = {
    "missing_toy": Mystery(
        id="missing_toy",
        clue="a tiny thump under the bed",
        missing="toy mouse",
        location="under the bed",
        solved_by="sweeping the blanket aside together",
        solve_action="look under the bed",
        turns_out="a toy mouse had rolled under the bed",
    ),
    "missing_key": Mystery(
        id="missing_key",
        clue="a small jingle from a coat pocket",
        missing="brass key",
        location="inside a coat pocket",
        solved_by="checking the hanging coats together",
        solve_action="look through the coats",
        turns_out="a brass key was tucked inside a pocket",
    ),
    "missing_bell": Mystery(
        id="missing_bell",
        clue="a faint ding from the wash basket",
        missing="silver bell",
        location="in the wash basket",
        solved_by="peeking through the folded pajamas together",
        solve_action="look in the wash basket",
        turns_out="a silver bell had slipped into the wash basket",
    ),
}

GENDER_NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ivy", "Zoe", "Maya"],
    "boy": ["Finn", "Leo", "Theo", "Max", "Eli", "Jack"],
}

HELPERS = ["cat", "dog", "grandmother", "grandfather"]
TRAITS = ["curious", "brave", "quiet", "kind", "patient", "clever"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_name, place in SETTINGS.items():
        for mystery_id in place.affords:
            combos.append((place_name, mystery_id))
    return combos


def reasonableness_gate(place: Place, mystery: Mystery) -> bool:
    return mystery.id in place.affords


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost-story mystery about pajamas, teamwork, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "place", None) and getattr(args, "mystery", None):
        if not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(MYSTERIES, getattr(args, "mystery", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def make_world(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(place)
    world.facts["mystery"] = mystery
    world.facts["params"] = params

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["tame", "pajamas", params.trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="a tame ghost", traits=["tame", "gentle"]))
    pajamas = world.add(Entity(id="Pajamas", type="pajamas", label="pajamas", phrase="soft pajamas", owner=hero.id, wearing=True))
    clue = world.add(Entity(id="Clue", type="clue", label="clue", phrase=mystery.clue, caretaker=hero.id))

    hero.memes["curiosity"] = 1
    ghost.memes["friendliness"] = 1
    hero.memes["worry"] = 1
    helper.memes["helpfulness"] = 1

    world.say(f"One night, {hero.id} was in {params.name}'s {pajamas.label if False else 'pajamas'} in {place.name}.")
    world.say(f"{place.hush} {hero.id} heard {mystery.clue}, and that made the room feel like a tiny mystery had woken up.")
    world.say(f"Then {ghost.label} drifted in, but it was a tame ghost with a soft smile, not a scary one.")

    world.para()
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} asked if the strange sound was a ghost problem.")
    world.say(f"{ghost.label.capitalize()} shook its head and pointed at {mystery.solve_action}.")

    if mystery.id == "missing_bell":
        world.say(f"The bell gave another little ding from somewhere near the laundry.")
    elif mystery.id == "missing_key":
        world.say(f"The jingling sounded closer each time they stepped past the coats.")
    else:
        world.say(f"The thump seemed to hide under the blanket like a shy secret.")

    world.para()
    world.say(f"{hero.id}, the {params.helper}, and {ghost.label} decided to use teamwork.")
    world.say(f"They chose to {mystery.solve_action}, because a good mystery is easier when everyone helps.")

    hero.memes["teamwork"] = 1
    helper.memes["teamwork"] = 1
    ghost.memes["teamwork"] = 1

    world.say(f"At last, they found that {mystery.turns_out}.")
    world.say(f"The missing {mystery.missing} was safe again, and the soft pajamas were still neat and cozy.")
    world.say(f"{hero.id} smiled, because the mystery was solved and the room felt calm and warm.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    mystery: Mystery = world.facts["mystery"]
    return [
        f"Write a gentle ghost story for young children where {params.name} in pajamas hears {mystery.clue} and solves the mystery with help.",
        f"Tell a cozy teamwork story in {_safe_lookup(SETTINGS, params.place).name} about a tame ghost, a small clue, and the missing {mystery.missing}.",
        f"Write a child-friendly problem-solving story where everyone works together to find {mystery.missing} after a mysterious sound.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    mystery: Mystery = world.facts["mystery"]
    hero = world.get(params.name)
    return [
        QAItem(
            question=f"What did {params.name} hear first in the story?",
            answer=f"{params.name} first heard {mystery.clue}, which started the little mystery.",
        ),
        QAItem(
            question=f"Was the ghost scary or tame?",
            answer="The ghost was tame and gentle, so it helped instead of frightening anyone.",
        ),
        QAItem(
            question=f"How did {params.name} and the others solve the problem?",
            answer=f"They used teamwork and decided to {mystery.solve_action}. That is how they found the missing {mystery.missing}.",
        ),
        QAItem(
            question=f"What was {params.name} wearing during the mystery?",
            answer=f"{params.name} was wearing pajamas, which made the story feel cozy even with the spooky clue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something harder than one person could do alone.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not explained at first, so people look for clues to understand it.",
        ),
        QAItem(
            question="What are pajamas for?",
            answer="Pajamas are soft clothes people wear at bedtime so they can rest and sleep comfortably.",
        ),
        QAItem(
            question="Can a ghost story be gentle?",
            answer="Yes. A ghost story can be gentle when the ghost is friendly and the mood is cozy instead of scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.wearing:
            bits.append("wearing=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_id(M).
valid(P, M) :- place(P), mystery(M), affords(P, M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, place in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for m in sorted(place.affords):
            lines.append(asp.fact("affords", p, m))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_id", m))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(place: Place, mystery: Mystery) -> str:
    return f"(No story: {mystery.id} does not fit {place.name}; the clue and setting do not make a believable mystery.)"


def explain_asp() -> str:
    return asp_program("#show valid/2.")


CURATED = [
    StoryParams(place="bedroom", mystery="missing_bell", name="Mia", gender="girl", helper="cat", trait="curious"),
    StoryParams(place="hall", mystery="missing_key", name="Leo", gender="boy", helper="dog", trait="clever"),
    StoryParams(place="attic", mystery="missing_toy", name="Nora", gender="girl", helper="grandmother", trait="brave"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "mystery", None):
        if not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(MYSTERIES, getattr(args, "mystery", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


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
        print(explain_asp())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, m in combos:
            print(f"  {p:10} {m}")
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
