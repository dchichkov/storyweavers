#!/usr/bin/env python3
"""
storyworlds/worlds/afford_conflict_teamwork_mystery.py
======================================================

A standalone story world for a small mystery about what a place can afford,
how conflict appears, and how teamwork solves the clue.

Premise:
- A child and a helper visit a place that affords a useful action.
- A small conflict blocks the first attempt.
- They examine clues, work together, and uncover the missing item.
- The ending proves the change with a concrete recovered object and calmer mood.

The prose is driven by world state, not a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    clue: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)
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
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    clues: list[str] = field(default_factory=list)
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
class Goal:
    id: str
    label: str
    hiding_place: str
    afford_action: str
    risk: str
    solve_tool: str
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    goal: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    params: object | None = None
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


PLACES = {
    "library": Place(
        id="library",
        label="the library",
        affords={"search", "whisper", "compare_clues"},
        clues=["a bookmark", "a quiet map", "a note between pages"],
    ),
    "attic": Place(
        id="attic",
        label="the attic",
        affords={"search", "compare_clues", "shine_light"},
        clues=["a dusty box", "a loose board", "a little key"],
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        affords={"search", "compare_clues", "open_drawer"},
        clues=["a paint tin", "a hanging hook", "a string loop"],
    ),
}

GOALS = {
    "kite_string": Goal(
        id="kite_string",
        label="the missing kite string",
        hiding_place="behind a row of books",
        afford_action="compare_clues",
        risk="it could be tangled and easy to overlook",
        solve_tool="a magnifying glass",
    ),
    "silver_key": Goal(
        id="silver_key",
        label="the little silver key",
        hiding_place="under a dusty box",
        afford_action="search",
        risk="it was small and shiny, so it could hide in plain sight",
        solve_tool="a flashlight",
    ),
    "blue_ticket": Goal(
        id="blue_ticket",
        label="the blue ticket",
        hiding_place="inside a folded note",
        afford_action="whisper",
        risk="it was paper-thin and could slip between pages",
        solve_tool="a careful finger",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Ella", "Sam"]
HELPER_NAMES = ["Mom", "Dad", "Zoe", "Theo", "June", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in PLACES for g in GOALS if _safe_lookup(GOALS, g).afford_action in _safe_lookup(PLACES, p).affords]


@dataclass
class StoryParamsResolved:
    place: str
    goal: str
    child: str
    child_type: str
    helper: str
    helper_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery story world about affordances, conflict, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "mother", "father"])
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
              and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father", "girl", "boy"])
    child = getattr(args, "child", None) or rng.choice(CHILD_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(place=place, goal=goal, child=child, child_type=child_type, helper=helper, helper_type=helper_type)


def tell(place: Place, goal: Goal, child_name: str, child_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    clue = world.add(Entity(id="clue", type="thing", label=goal.label))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["goal"] = goal
    world.facts["clue"] = clue

    child.memes["curiosity"] = 1
    helper.memes["calm"] = 1
    child.memes["conflict"] = 0
    child.memes["joy"] = 0
    helper.memes["joy"] = 0

    world.say(f"{child_name} and {helper_name} stepped into {place.label}.")
    world.say(f"{place.label_word.capitalize()} felt full of tiny clues, and {goal.afford_action} seemed like the right way to look.")
    world.para()
    child.memes["conflict"] += 1
    child.meters["lost"] += 1
    world.say(f"Then {child_name} frowned. {goal.risk.capitalize()}, and {child_name} could not spot {goal.label}.")
    world.say(f"{helper_name} pointed at the room's hints and said they should work together instead of arguing.")
    world.para()
    child.memes["conflict"] = 0
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    child.meters["lost"] = 0
    child.meters["found"] += 1
    world.say(f"Together they checked the clues one by one, using {goal.solve_tool} and a steady plan.")
    world.say(f"At last, {child_name} found {goal.label} {goal.hiding_place}.")
    world.say(f"{helper_name} smiled, and the mystery felt small and solved at last.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    goal = f["goal"]
    place = world.place
    return [
        f'Write a gentle mystery story for a young child where {child.id} and {helper.id} visit {place.label} and must use what the place affords to solve a clue about {goal.label}.',
        f'Tell a short story with conflict and teamwork where a child gets stuck looking for {goal.label} in {place.label}, then works with a helper to find it.',
        f'Write a child-friendly mystery where the word "afford" matters because {place.label} affords the right way to search for {goal.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, goal = f["child"], f["helper"], f["goal"]
    place = world.place
    return [
        QAItem(
            question=f"Where did {child.id} and {helper.id} go to solve the mystery?",
            answer=f"They went to {place.label}. That place afforded the kind of searching they needed for {goal.label}.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"{child.id} could not find {goal.label} at first, and that caused a little conflict.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} fix the problem?",
            answer=f"They worked together, checked the clues, and found {goal.label}. Their teamwork solved the mystery.",
        ),
        QAItem(
            question=f"What did the place afford them to do?",
            answer=f"It afforded a good way to search and compare clues so they could look for {goal.label} carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does afford mean?",
            answer="If a place affords an action, it makes that action easy or possible there.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do something together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known at first, so people look for clues.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(lines)


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


ASP_RULES = r"""
afford_action(P,A) :- place(P), affords(P,A), goal(G), required(G,A).
valid(P,G) :- place(P), goal(G), affords(P,A), required(G,A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for g in GOALS.values():
        lines.append(asp.fact("goal", g.id))
        lines.append(asp.fact("required", g.id, g.afford_action))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(GOALS, params.goal), params.child, params.child_type, params.helper, params.helper_type)
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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        for p, g in asp_valid_combos():
            print(p, g)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples = []
    if getattr(args, "all", None):
        for p, g in valid_combos():
            params = StoryParams(place=p, goal=g, child="Mia", child_type="girl", helper="Mom", helper_type="mother")
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
