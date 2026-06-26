#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/platter_image_constraint_mystery_to_solve_slice.py
=========================================================================================================

A small slice-of-life mystery storyworld about a child, a platter, an image,
and one practical constraint that must be noticed to solve the problem.

Premise seed:
- A family or helper needs a platter arranged for a simple everyday moment.
- An image gives the clue to how it should look.
- A constraint makes the first attempt fail.
- The mystery is solved by reading the image carefully and respecting the constraint.

The domain stays gentle and concrete: a quiet home or café moment, snack or
fruit platters, careful arranging, and a pleasant resolution.
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
# World data model
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
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
    indoors: bool
    vibe: str
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
class Platter:
    label: str
    phrase: str
    kind: str
    size: str
    image: str
    constraint: str
    clues: list[str] = field(default_factory=list)
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
class Mystery:
    problem: str
    reveal: str
    fix: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, vibe="quiet and homey"),
    "cafe": Setting(place="the little café", indoors=True, vibe="warm and busy"),
    "picnic": Setting(place="the picnic table", indoors=False, vibe="bright and calm"),
}

PLATTERS = {
    "round_fruit": Platter(
        label="round fruit platter",
        phrase="a round fruit platter with grapes, apple slices, and berries",
        kind="fruit",
        size="round",
        image="a circle with fruit arranged like a sun",
        constraint="must be round",
        clues=["circle", "round", "sun"],
    ),
    "long_snacks": Platter(
        label="long snack platter",
        phrase="a long snack platter with crackers, cheese, and cucumber sticks",
        kind="snack",
        size="long",
        image="a neat row with snacks lined up from left to right",
        constraint="must be long",
        clues=["row", "line", "left", "right"],
    ),
    "heart_cookies": Platter(
        label="heart cookie platter",
        phrase="a heart-shaped cookie platter with tiny cookies around the edge",
        kind="cookies",
        size="heart",
        image="a heart with little cookies tracing the edge",
        constraint="must be heart-shaped",
        clues=["heart", "edge", "shape"],
    ),
}

MYSTERIES = {
    "missing_shape": Mystery(
        problem="the first platter did not match the picture",
        reveal="the image showed a different shape than the one they guessed",
        fix="they rearranged the food to match the shape in the image",
    ),
    "wrong_order": Mystery(
        problem="the snacks looked neat, but they were in the wrong order",
        reveal="the image showed a left-to-right order that mattered",
        fix="they put the pieces back in the same order as the image",
    ),
    "constraint_notice": Mystery(
        problem="the platter was almost right, but one rule had been missed",
        reveal="the image and the note together made the rule clear",
        fix="they followed the note and the picture at the same time",
    ),
}

CHARACTER_NAMES = ["Maya", "Leo", "Nina", "Sam", "Iris", "Owen", "Luna", "Ben"]
TRAITS = ["thoughtful", "curious", "gentle", "careful", "quiet", "helpful"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    platter: str
    mystery: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def valid_combo(place: str, platter: str, mystery: str) -> bool:
    if place not in SETTINGS or platter not in PLATTERS or mystery not in MYSTERIES:
        return False
    p = _safe_lookup(PLATTERS, platter)
    if mystery == "wrong_order" and p.size == "heart":
        return False
    if place == "picnic" and p.kind == "cookies":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for platter in PLATTERS:
            for mystery in MYSTERIES:
                if valid_combo(place, platter, mystery):
                    out.append((place, platter, mystery))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def article(phrase: str) -> str:
    return ("an " if phrase[:1].lower() in "aeiou" else "a ") + phrase


def intro(world: World, hero: Entity, helper: Entity, platter: Platter) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait']} {hero.type} who liked small jobs that made a day feel tidy."
    )
    world.say(
        f"One morning, {hero.id} helped {helper.pronoun('object')} carry {article(platter.phrase)} to the table."
    )


def setting_line(world: World) -> None:
    if world.setting.indoors:
        world.say(f"The room was {world.setting.vibe}, and the table was waiting in {world.setting.place}.")
    else:
        world.say(f"The air at {world.setting.place} felt {world.setting.vibe}, and the table was already set out.")


def observe_image(world: World, hero: Entity, platter: Platter) -> None:
    world.say(
        f"{hero.id} found a little image on the note beside the plate: {platter.image}."
    )
    world.say(
        f"The note also said the platter {platter.constraint}, so the picture was not just decoration."
    )


def first_try(world: World, hero: Entity, platter: Platter, mystery: Mystery) -> None:
    if mystery.problem == "the first platter did not match the picture":
        world.say(
            f"{hero.id} guessed at first and set the food down in a hurry, but something looked off."
        )
    elif mystery.problem == "the snacks looked neat, but they were in the wrong order":
        world.say(
            f"{hero.id} lined up the snacks neatly, yet the order still felt wrong."
        )
    else:
        world.say(
            f"{hero.id} thought the platter was done, but one small rule still did not fit."
        )


def solve(world: World, hero: Entity, helper: Entity, platter: Platter, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} looked again at the image and noticed the clue hidden in plain sight."
    )
    world.say(
        f"Then {hero.id} told {helper.pronoun('object')} what the picture showed, and they fixed the platter together."
    )
    world.say(
        f"{mystery.fix.capitalize()}, and soon the {platter.label} matched the note exactly."
    )
    world.say(
        f"At the end, the platter sat on the table looking calm and right, as if it had always belonged there."
    )


def tell(setting: Setting, platter: Platter, mystery: Mystery,
         hero_name: str, gender: str, trait: str, helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    hero.memes["trait"] = trait
    world.facts.update(hero=hero, helper=helper, platter=platter, mystery=mystery)

    intro(world, hero, helper, platter)
    world.para()
    setting_line(world)
    observe_image(world, hero, platter)
    first_try(world, hero, platter, mystery)
    world.para()
    solve(world, hero, helper, platter, mystery)
    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(Place, Platter, Mystery) :- setting(Place), platter(Platter), mystery(Mystery),
    not invalid(Place, Platter, Mystery).

invalid(picnic, heart_cookies, _) :- true.
invalid(picnic, _, wrong_order) :- false.
invalid(_, Platter, wrong_order) :- platter_shape(Platter, heart).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        if _safe_lookup(SETTINGS, s).indoors:
            lines.append(asp.fact("indoors", s))
    for p in PLATTERS:
        lines.append(asp.fact("platter", p))
        lines.append(asp.fact("platter_shape", p, _safe_lookup(PLATTERS, p).size))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "platter")
    m = _safe_fact(world, world.facts, "mystery")
    return [
        f"Write a gentle slice-of-life mystery story that includes a {p.label} and an image clue.",
        f"Tell a short story about a child solving a platter mystery by noticing a constraint in the picture.",
        f"Write a simple everyday story where an image helps a child fix a platter that does not quite look right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    platter = _safe_fact(world, world.facts, "platter")
    mystery = _safe_fact(world, world.facts, "mystery")
    return [
        QAItem(
            question=f"What was {hero.id} helping with?",
            answer=f"{hero.id} was helping arrange {article(platter.phrase)} with {helper.pronoun('object')} at {world.setting.place}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The little image on the note helped, because it showed {platter.image}.",
        ),
        QAItem(
            question="What was the constraint?",
            answer=f"The platter {platter.constraint}, and that rule mattered when they put the food in place.",
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{mystery.fix.capitalize()}, so the platter finally matched the picture.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    platter = _safe_fact(world, world.facts, "platter")
    return [
        QAItem(
            question="What is a platter?",
            answer="A platter is a large plate or tray for serving food.",
        ),
        QAItem(
            question="What is an image?",
            answer="An image is a picture or drawing that shows what something looks like.",
        ),
        QAItem(
            question="What is a constraint?",
            answer="A constraint is a rule or limit that tells you what you must do or what you must avoid.",
        ),
        QAItem(
            question=f"Why would someone use an image when arranging {platter.label}?",
            answer="They would use the image to check the shape, order, or layout so the platter matches the plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={e.memes}")
    lines.append(f"setting={world.setting.place}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()


def explain_rejection(place: str, platter: str, mystery: str) -> str:
    if place == "picnic" and platter == "heart_cookies":
        return "(No story: heart cookies at the picnic table would not fit this simple slice-of-life setup.)"
    if platter == "heart_cookies" and mystery == "wrong_order":
        return "(No story: a heart cookie platter is about shape, not left-to-right order.)"
    return "(No story: that combination does not make a clean, solvable everyday mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life platter mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--platter", choices=PLATTERS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "platter", None) and getattr(args, "mystery", None):
        if not valid_combo(getattr(args, "place", None), getattr(args, "platter", None), getattr(args, "mystery", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "platter", None) is None or c[1] == getattr(args, "platter", None))
        and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, platter, mystery = rng.choice(list(filtered))
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, platter=platter, mystery=mystery, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PLATTERS, params.platter), _safe_lookup(MYSTERIES, params.mystery),
                 params.name, params.gender, params.trait)
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
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", platter="round_fruit", mystery="missing_shape", name="Maya", gender="girl", trait="curious"),
    StoryParams(place="cafe", platter="long_snacks", mystery="wrong_order", name="Leo", gender="boy", trait="careful"),
    StoryParams(place="kitchen", platter="heart_cookies", mystery="constraint_notice", name="Nina", gender="girl", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
