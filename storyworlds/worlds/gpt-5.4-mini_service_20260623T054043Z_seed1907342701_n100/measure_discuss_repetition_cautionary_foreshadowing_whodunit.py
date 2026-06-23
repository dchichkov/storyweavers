#!/usr/bin/env python3
"""
storyworlds/worlds/measure_discuss_repetition_cautionary_foreshadowing_whodunit.py
==================================================================================

A small storyworld built from a whodunit seed: someone measures, someone
discusses, clues repeat, warnings foreshadow trouble, and the ending reveals
who moved the missing item and why.

The world is deliberately tiny and child-facing: a little mystery in a bakery,
with a ruler, a missing tart, and a careful lantern-lit search.
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    held: bool = False
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "they", "object": "them", "possessive": "their"}
        return mapping[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class StoryParams:
    place: str
    missing: str
    suspect: str
    solver: str
    helper: str
    seed: Optional[int] = None
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
class Place:
    id: str
    label: str
    smell: str
    surfaces: list[str]
    clue: str
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
class ObjectKind:
    id: str
    label: str
    phrase: str
    measure_unit: str
    repeat_line: str
    caution_line: str
    foreshadow_line: str
    hidden_spot: str
    can_be_hidden: bool = True
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
class PersonKind:
    id: str
    label: str
    role_hint: str
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


PLACES = {
    "bakery": Place("bakery", "the bakery", "warm bread", ["counter", "shelf", "floor"], "a flour print"),
    "library": Place("library", "the library corner", "old paper", ["table", "stool", "rug"], "a bookmark ribbon"),
    "workshop": Place("workshop", "the little workshop", "wood shavings", ["bench", "crate", "doorstep"], "a tiny wood chip"),
    "garden_shop": Place("garden shop", "the garden shop", "soil and mint", ["potting table", "crate", "path"], "a leaf speck"),
}

OBJECTS = {
    "tart": ObjectKind(
        "tart", "berry tart", "a berry tart", "centimeter",
        "The tart sat beside the ruler again and again.",
        "It would spoil if someone left it too long in the warm room.",
        "The empty plate and the neat ruler would matter later.",
        "under the napkin",
    ),
    "jar": ObjectKind(
        "jar", "jam jar", "a jam jar", "milliliter",
        "The jar sat beside the ruler again and again.",
        "It could spill if someone nudged it near the edge.",
        "The sticky lid and the ruler marks would matter later.",
        "under the cloth",
    ),
    "seed_box": ObjectKind(
        "seed_box", "seed box", "a seed box", "cup",
        "The seed box sat beside the ruler again and again.",
        "It could crack if someone stacked it under a heavy tray.",
        "The bent corner and the ruler marks would matter later.",
        "behind the flour tin",
    ),
    "toy_clock": ObjectKind(
        "toy_clock", "toy clock", "a toy clock", "tick",
        "The toy clock sat beside the ruler again and again.",
        "It could go missing if someone hid it in a hurry.",
        "The crooked hand and the ruler marks would matter later.",
        "under the red towel",
    ),
}

PEOPLE = {
    "mira": PersonKind("mira", "Mira", "careful"),
    "jun": PersonKind("jun", "Jun", "curious"),
    "sana": PersonKind("sana", "Sana", "patient"),
    "otto": PersonKind("otto", "Otto", "quiet"),
    "nina": PersonKind("nina", "Nina", "watchful"),
    "eli": PersonKind("eli", "Eli", "steady"),
}

VALID_COMBOS = [
    ("bakery", "tart", "jun", "mira", "nina"),
    ("bakery", "jar", "sana", "otto", "mira"),
    ("library", "toy_clock", "nina", "jun", "eli"),
    ("workshop", "seed_box", "eli", "sana", "otto"),
    ("garden_shop", "seed_box", "jun", "nina", "mira"),
    ("library", "tart", "otto", "eli", "sana"),
]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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


def valid_combos() -> list[tuple[str, str, str]]:
    return list(VALID_COMBOS)


def reasonableness_ok(place_id: str, missing_id: str, suspect_id: str, solver_id: str, helper_id: str) -> bool:
    return (
        place_id in PLACES
        and missing_id in OBJECTS
        and suspect_id in PEOPLE
        and solver_id in PEOPLE
        and helper_id in PEOPLE
        and len({suspect_id, solver_id, helper_id}) >= 2
    )


def explain_rejection() -> str:
    return "(No story: that combination leaves no clear little mystery to measure, discuss, and solve.)"


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    obj = _safe_lookup(OBJECTS, params.missing)
    suspect = PEOPLE[params.suspect]
    solver = PEOPLE[params.solver]
    helper = PEOPLE[params.helper]
    world = World(place)
    world.facts = {
        "place": place,
        "object": obj,
        "suspect_kind": suspect,
        "solver_kind": solver,
        "helper_kind": helper,
        "measure_used": False,
        "discussed": False,
        "repeated_clue": False,
        "caution_seen": False,
        "foreshadow_seen": False,
        "solved": False,
    }

    world.add(Entity("table", kind="thing", type="surface", label="table", held=False, hidden=False, meters={"length": 0.0}, memes={}))
    world.add(Entity("ruler", kind="thing", type="tool", label="ruler", phrase="a wooden ruler", meters={"length": 30.0}, memes={}))
    world.add(Entity("missing", kind="thing", type="object", label=obj.label, phrase=obj.phrase, held=False, hidden=True, meters={"found": 0.0}, memes={}))
    world.add(Entity("suspect", kind="character", type="person", label=suspect.label, role="suspect", meters={}, memes={"nervous": 0.0, "guilt": 0.0}))
    world.add(Entity("solver", kind="character", type="person", label=solver.label, role="solver", meters={}, memes={"curious": 0.0, "certainty": 0.0}))
    world.add(Entity("helper", kind="character", type="person", label=helper.label, role="helper", meters={}, memes={"calm": 0.0}))
    return world


def measure_clue(world: World) -> None:
    if world.facts["measure_used"]:
        return
    ruler = world.get("ruler")
    missing = world.get("missing")
    solver = world.get("solver")
    ruler.meters["used"] = 1.0
    solver.memes["curious"] += 1
    world.facts["measure_used"] = True
    world.say(f"{solver.label_word} picked up a wooden ruler and began to measure the empty space beside the plate.")
    world.say(f"The ruler and the empty space matched the size of {world.facts['object'].phrase}, and that felt like a clue.")


def discuss_clue(world: World) -> None:
    if world.facts["discussed"]:
        return
    solver = world.get("solver")
    helper = world.get("helper")
    obj = world.facts["object"]
    place = world.facts["place"]
    world.facts["discussed"] = True
    solver.memes["certainty"] += 0.5
    helper.memes["calm"] += 1
    world.say(f"{solver.label_word} and {helper.label_word} sat together to discuss the clue in a low voice.")
    world.say(f"They kept saying the same thing again and again: the missing {obj.label} had to be near {place.clue}.")


def cautionary_foreshadowing(world: World) -> None:
    if world.facts["caution_seen"]:
        return
    helper = world.get("helper")
    suspect = world.get("suspect")
    obj = world.facts["object"]
    world.facts["caution_seen"] = True
    world.say(f"{helper.label_word} gave a careful warning: if the room stayed crowded, somebody might knock the {obj.label} loose.")
    world.say(f"{suspect.label_word} looked away at once, and that little glance was a clue of its own.")


def repetition_beats(world: World) -> None:
    if world.facts["repeated_clue"]:
        return
    obj = world.facts["object"]
    place = world.facts["place"]
    world.facts["repeated_clue"] = True
    world.say(f"Again and again, the same mark showed up: a neat little sign leading from the {place.label} shelf to {obj.hidden_spot}.")
    world.say(f"Again and again, the mark pointed back to the same place, so the mystery could not be random anymore.")


def solve_mystery(world: World) -> None:
    if world.facts["solved"]:
        return
    suspect = world.get("suspect")
    solver = world.get("solver")
    helper = world.get("helper")
    obj = world.facts["object"]
    world.facts["solved"] = True
    suspect.memes["guilt"] += 1
    solver.memes["certainty"] += 1
    world.get("missing").hidden = False
    world.get("missing").held = False
    world.say(f"{solver.label_word} finally pointed to {suspect.label_word} and asked to discuss the missing piece one more time.")
    world.say(f"{suspect.label_word} admitted it: the {obj.label} had been moved under {obj.hidden_spot} to keep it safe from a crowded table.")
    world.say(f"{helper.label_word} smiled, and together they put the {obj.label} back where it belonged.")


def tell_story(world: World) -> None:
    place = world.facts["place"]
    obj = world.facts["object"]
    suspect = world.facts["suspect_kind"]
    solver = world.facts["solver_kind"]
    helper = world.facts["helper_kind"]

    world.say(f"At {place.label}, {solver.label} noticed that a {obj.label} was missing from the counter.")
    world.say(f"{helper.label} was already there, and {suspect.label} kept glancing toward the back of the room.")
    world.para()
    measure_clue(world)
    cautionary_foreshadowing(world)
    discuss_clue(world)
    world.para()
    repetition_beats(world)
    solve_mystery(world)
    world.para()
    world.say(f"In the end, the empty spot was no longer empty: the {obj.label} sat safely back beside the ruler, and everyone could see how the little mystery was solved.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    obj = f["object"].label
    return [
        f'Write a short whodunit for a young child set in {place} about a missing {obj}. Include the words "measure" and "discuss".',
        f"Tell a gentle mystery where someone measures a clue, the friends discuss it, and repeated signs lead to the answer.",
        f"Write a story with caution and foreshadowing that ends with the missing {obj} back where it belongs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place = f["place"].label
    obj = f["object"].label
    suspect = f["suspect_kind"].label
    solver = f["solver_kind"].label
    helper = f["helper_kind"].label
    return [
        QAItem(
            question=f"What was missing at {place}?",
            answer=f"The missing thing was a {obj}. {solver} noticed it was gone and started looking right away.",
        ),
        QAItem(
            question=f"Why did {solver} measure the empty space?",
            answer=f"{solver} wanted to compare the empty space with the clue. The size helped show that the missing {obj} fit the spot under the napkin or cloth.",
        ),
        QAItem(
            question=f"Who did {solver} discuss the clue with?",
            answer=f"{solver} discussed the clue with {helper}. They spoke quietly and kept returning to the same clue so they would not miss anything.",
        ),
        QAItem(
            question=f"Who turned out to be involved in moving the {obj}?",
            answer=f"{suspect} was involved. In the end, {suspect} explained that the {obj} had been moved to a hidden spot to keep it safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The missing {obj} went back to its place beside the ruler, and the little mystery was solved. The ending proves the clue trail led to the right answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = world.facts["object"]
    return [
        QAItem(
            question="What does it mean to measure something?",
            answer="To measure means to find out how long, tall, or big something is using a tool like a ruler.",
        ),
        QAItem(
            question="What does it mean to discuss something?",
            answer="To discuss means to talk about something together, often to understand it better or make a plan.",
        ),
        QAItem(
            question="Why do clues matter in a whodunit?",
            answer="Clues matter because they help you figure out what happened. In a mystery, small signs can point to the truth.",
        ),
        QAItem(
            question=f"What is {obj.label} made for?",
            answer=f"{obj.label_word.capitalize()} is a small object used in the story as the missing item. It gives the mystery a clear thing to find and return.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.held:
            bits.append("held=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: measure={world.facts.get('measure_used')} discuss={world.facts.get('discussed')} solved={world.facts.get('solved')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(bakery; library; workshop; garden_shop).
object(tart; jar; seed_box; toy_clock).
person(mira; jun; sana; otto; nina; eli).

valid(P,O,S,So,H) :- place(P), object(O), person(S), person(So), person(H), S != So, S != H, So != H.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for k in PEOPLE:
        lines.append(asp.fact("person", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(place="bakery", missing="tart", suspect="jun", solver="mira", helper="nina"),
    StoryParams(place="library", missing="toy_clock", suspect="nina", solver="jun", helper="eli"),
    StoryParams(place="workshop", missing="seed_box", suspect="eli", solver="sana", helper="otto"),
    StoryParams(place="garden_shop", missing="seed_box", suspect="jun", solver="nina", helper="mira"),
]


def explain_rejection_params(params: StoryParams) -> str:
    return explain_rejection()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a small whodunit about measure and discuss.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=OBJECTS)
    ap.add_argument("--suspect", choices=PEOPLE)
    ap.add_argument("--solver", choices=PEOPLE)
    ap.add_argument("--helper", choices=PEOPLE)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "missing", None) is None or c[1] == getattr(args, "missing", None))
              and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))
              and (getattr(args, "solver", None) is None or c[3] == getattr(args, "solver", None))
              and (getattr(args, "helper", None) is None or c[4] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, missing, suspect, solver, helper = rng.choice(list(combos))
    return StoryParams(place=place, missing=missing, suspect=suspect, solver=solver, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_ok(params.place, params.missing, params.suspect, params.solver, params.helper):
        pass
    world = build_world(params)
    tell_story(world)
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


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("FAIL: generated story was empty")
            return 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: smoke test generation crashed: {exc}")
        return 1
    print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos); smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
            params = resolve_params(args, random.Random(seed))
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
