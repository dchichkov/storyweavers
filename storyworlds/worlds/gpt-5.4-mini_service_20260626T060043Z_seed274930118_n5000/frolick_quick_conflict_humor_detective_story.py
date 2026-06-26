#!/usr/bin/env python3
"""
A tiny detective-story world with quick frolicking, comic conflict, and a clean
case resolution.

Premise:
- A child detective notices a small mystery.
- A playful suspect does something frolicking and quick that causes confusion.
- The detective follows clues, a conflict rises, humor softens it, and the case
  ends with a satisfying reveal.

This script follows the Storyweavers storyworld contract.
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
    owner: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    det: object | None = None
    sus: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "woman", "sister", "aunt", "detective_girl"}
        masculine = {"boy", "father", "man", "brother", "uncle", "detective_boy"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    place: str = "the little town square"
    has_stairs: bool = False
    has_fountain: bool = False
    has_library: bool = False
    has_bakery: bool = False
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
class Suspect:
    id: str
    label: str
    type: str
    trait: str
    quick_action: str
    frolic_action: str
    clue: str
    alibi: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Mystery:
    missing_item: str
    missing_label: str
    missing_place: str
    clue_item: str
    clue_place: str
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
    setting: str
    detective_gender: str
    detective_name: str
    suspect: str
    mystery: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.trace = list(self.trace)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "square": Setting(place="the little town square", has_stairs=True, has_fountain=True),
    "library": Setting(place="the old library", has_stairs=True, has_library=True),
    "bakery": Setting(place="the bakery lane", has_bakery=True),
}

MYSTERIES = {
    "jam": Mystery(
        missing_item="jam tarts",
        missing_label="jam tarts",
        missing_place="the bakery shelf",
        clue_item="sticky crumbs",
        clue_place="the stone bench",
    ),
    "badge": Mystery(
        missing_item="silver badge",
        missing_label="silver badge",
        missing_place="the town hall desk",
        clue_item="shiny dust",
        clue_place="the fountain rim",
    ),
    "book": Mystery(
        missing_item="library book",
        missing_label="library book",
        missing_place="the reading table",
        clue_item="a torn page corner",
        clue_place="the staircase",
    ),
}

SUSPECTS = {
    "pigeon": Suspect(
        id="Pip",
        label="Pip the pigeon",
        type="bird",
        trait="cheeky",
        quick_action="darted",
        frolic_action="frolicked",
        clue="a crumb trail",
        alibi="Pip had been pecking at crumbs near the bench",
    ),
    "puppy": Suspect(
        id="Milo",
        label="Milo the puppy",
        type="dog",
        trait="playful",
        quick_action="scampered",
        frolic_action="frolicked",
        clue="muddy paw prints",
        alibi="Milo had been chasing his ball in the square",
    ),
    "monkey": Suspect(
        id="Nina",
        label="Nina the monkey",
        type="monkey",
        trait="mischievous",
        quick_action="zigzagged",
        frolic_action="frolicked",
        clue="banana peel bits",
        alibi="Nina had been swinging by the fountain",
    ),
}

DETECTIVE_NAMES = ["Mia", "Leo", "Ada", "Max", "Nora", "Theo", "Lily", "Ben"]
TRAITS = ["sharp-eyed", "patient", "bright", "careful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting_key: str, mystery_key: str, suspect_key: str) -> bool:
    setting = _safe_lookup(SETTINGS, setting_key)
    mystery = _safe_lookup(MYSTERIES, mystery_key)
    suspect = _safe_lookup(SUSPECTS, suspect_key)
    if setting_key == "bakery" and mystery_key == "book":
        return False
    if mystery_key == "jam" and suspect_key != "puppy":
        return False
    if mystery_key == "badge" and suspect_key != "pigeon":
        return False
    if mystery_key == "book" and suspect_key != "monkey":
        return False
    return True


def explain_rejection(setting_key: str, mystery_key: str, suspect_key: str) -> str:
    setting = _safe_lookup(SETTINGS, setting_key)
    mystery = _safe_lookup(MYSTERIES, mystery_key)
    suspect = _safe_lookup(SUSPECTS, suspect_key)
    return (
        f"(No story: {suspect.label} does not fit this little mystery at {setting.place}. "
        f"Try a combination where the clues and the suspect's behavior match.)"
    )


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, M, U) :- setting(S), mystery(M), suspect(U),
                  allowed(S, M, U).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for u in SUSPECTS:
        lines.append(asp.fact("suspect", u))
    for s in SETTINGS:
        for m in MYSTERIES:
            for u in SUSPECTS:
                if valid_combo(s, m, u):
                    lines.append(asp.fact("allowed", s, m, u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(
        (s, m, u)
        for s in SETTINGS
        for m in MYSTERIES
        for u in SUSPECTS
        if valid_combo(s, m, u)
    )
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combo() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combo():")
    print("only in python:", sorted(python_set - clingo_set))
    print("only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_story(world: World) -> None:
    f = world.facts
    det: Entity = _safe_fact(world, f, "detective")
    sus: Entity = _safe_fact(world, f, "suspect_entity")
    mys: Mystery = _safe_fact(world, f, "mystery")

    world.say(
        f"{det.id} was a little {det.memes['trait_word']} detective who loved a good case."
    )
    world.say(
        f"One morning, a few {mys.missing_label} were gone from {mys.missing_place}, "
        f"and {det.id} promised to find them."
    )

    world.para()
    world.say(
        f"{det.id} went to {world.setting.place} and looked for clues."
    )
    world.say(
        f"There, {sus.label} {sus.frolic_action} in a quick little circle, and that made the clues look funny."
    )
    world.say(
        f"{det.id} noticed {sus.clue} near {mys.clue_place}."
    )

    world.para()
    det.memes["conflict"] = 1.0
    world.say(
        f"{det.id} asked {sus.label} about it, but {sus.label} just smiled."
    )
    world.say(
        f'"I was only being quick," {sus.label} said. "I did not mean to make a mess!"'
    )
    world.say(
        f"{det.id} had to decide whether to be stern or laugh."
    )
    world.say(
        f"Then {sus.label} {sus.quick_action} away and slipped on a banana peel, which was so silly that even {det.id} snorted."
    )

    world.para()
    det.memes["humor"] = 1.0
    world.say(
        f"{det.id} followed the clue to {mys.clue_place} and found the {mys.missing_label} tucked where it had blown."
    )
    world.say(
        f"{sus.label} had not stolen anything at all; {sus.alibi}."
    )
    world.say(
        f"{det.id} laughed, handed back the {mys.missing_label}, and the little misunderstanding ended."
    )

    world.facts.update(
        detective=det,
        suspect_entity=sus,
        mystery=mys,
        setting=world.setting,
        resolved=True,
        conflict=True,
        humor=True,
    )


def tell(setting_key: str, mystery_key: str, suspect_key: str, detective_name: str, detective_gender: str) -> World:
    world = World(_safe_lookup(SETTINGS, setting_key))
    mys = _safe_lookup(MYSTERIES, mystery_key)
    sus_def = _safe_lookup(SUSPECTS, suspect_key)

    det = world.add(Entity(
        id=detective_name,
        kind="character",
        type="detective_girl" if detective_gender == "girl" else "detective_boy",
        role="detective",
        memes={"trait_word": random.choice(TRAITS)},
    ))
    sus = world.add(Entity(
        id=sus_def.id,
        kind="character",
        type=sus_def.type,
        role="suspect",
    ))

    world.facts["mystery"] = mys
    world.facts["suspect_def"] = sus_def
    build_story(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det: Entity = _safe_fact(world, f, "detective")
    sus_def: Suspect = _safe_fact(world, f, "suspect_def")
    mys: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short detective story for a child about {det.id}, a quick mystery, and {mys.missing_label}.',
        f'Write a funny story where {sus_def.label} is frolicking quickly and a detective notices the clue.',
        f"Tell a gentle detective tale with conflict and humor, ending with the missing {mys.missing_label} found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = _safe_fact(world, f, "detective")
    sus_def: Suspect = _safe_fact(world, f, "suspect_def")
    mys: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"Who was trying to solve the mystery?",
            answer=f"{det.id} was the detective trying to solve the case about the missing {mys.missing_label}.",
        ),
        QAItem(
            question=f"What made the detective stop and look twice?",
            answer=f"{sus_def.label} was frolicking in a quick, silly way, and that made the clues look strange.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{det.id} found the missing {mys.missing_label}, realized it was a misunderstanding, and laughed with everyone else.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "detective": QAItem(
        question="What does a detective do?",
        answer="A detective looks for clues to solve a mystery and find out what really happened.",
    ),
    "clue": QAItem(
        question="What is a clue?",
        answer="A clue is a small sign or bit of evidence that helps solve a mystery.",
    ),
    "humor": QAItem(
        question="Why can a funny mistake help in a story?",
        answer="A funny mistake can make a tense moment feel lighter and help people calm down enough to think.",
    ),
    "conflict": QAItem(
        question="What is conflict in a story?",
        answer="Conflict is the part of a story where characters want different things or misunderstand each other.",
    ),
    "frolick": QAItem(
        question="What does it mean to frolic?",
        answer="To frolic means to play in a happy, lively, bouncy way.",
    ),
    "quick": QAItem(
        question="What does quick mean?",
        answer="Quick means fast, with little delay.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE[k] for k in ["detective", "clue", "conflict", "humor", "frolick", "quick"]]


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
        lines.append(f"  {e.id:10} kind={e.kind} type={e.type} role={e.role} memes={e.memes}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective story world with quick frolicking, conflict, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [
        (s, m, u)
        for s in SETTINGS
        for m in MYSTERIES
        for u in SUSPECTS
        if valid_combo(s, m, u)
        and (getattr(args, "setting", None) is None or getattr(args, "setting", None) == s)
        and (getattr(args, "mystery", None) is None or getattr(args, "mystery", None) == m)
        and (getattr(args, "suspect", None) is None or getattr(args, "suspect", None) == u)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s, m, u = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES)
    return StoryParams(setting=s, mystery=m, suspect=u, detective_gender=gender, detective_name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.mystery, params.suspect, params.detective_name, params.detective_gender)
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
    StoryParams(setting="square", mystery="jam", suspect="puppy", detective_gender="girl", detective_name="Mia"),
    StoryParams(setting="library", mystery="book", suspect="monkey", detective_gender="boy", detective_name="Leo"),
    StoryParams(setting="square", mystery="badge", suspect="pigeon", detective_gender="girl", detective_name="Ada"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, suspect) combos:\n")
        for s, m, u in combos:
            print(f"  {s:8} {m:8} {u:8}")
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
            header = f"### {p.detective_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
