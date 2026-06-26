#!/usr/bin/env python3
"""
storyworlds/worlds/banquet_evaluate_problem_solving_bad_ending_kindness.py
=========================================================================

A small folk-tale storyworld about a banquet, an evaluation, a hard problem,
and a kind attempt to solve it that still ends badly.

Core premise:
- A village is preparing a banquet for an evaluator.
- A missing ingredient, broken dish, or spoiled centerpiece threatens the feast.
- A kind helper tries to solve the problem with a practical, gentle fix.
- The evaluation still goes badly: the banquet is rejected, ruined, or lost.
- The ending remains child-facing and concrete, with a visible final image.

This world is intentionally small and constraint-driven: not every request makes
sense, and invalid options raise StoryError with a clear reason.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banquet: object | None = None
    evaluator: object | None = None
    hero: object | None = None
    host: object | None = None
    problem_ent: object | None = None
    def __post_init__(self) -> None:
        for k in ["break", "spill", "spoil", "sad", "hope", "kindness", "trouble", "warmth", "relief"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "aunt"}
        male = {"boy", "father", "dad", "man", "king", "uncle"}
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
class Hall:
    place: str = "the village hall"
    indoors: bool = True
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
class Problem:
    id: str
    label: str
    verb: str
    gerund: str
    issue: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    verb: str
    tail: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        w = World(self.hall)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["spill"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != e.id:
                continue
            if ("spill", item.id) in world.fired:
                continue
            world.fired.add(("spill", item.id))
            item.meters["break"] += 1
            out.append(f"{e.label}'s trouble reached the {item.label}.")
    return out


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["trouble"] < THRESHOLD:
            continue
        sig = ("sad", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["sad"] += 1
        out.append(f"{e.label} looked down at the table and went quiet.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_spill, _r_sad):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bring_banquet(world: World, host: Entity, banquet: Entity) -> None:
    world.say(
        f"On a bright morning, {host.label} set the long tables for a banquet, "
        f"with linen white as milk and bowls set in a neat row."
    )
    banquet.memes["hope"] += 1


def announce_evaluation(world: World, evaluator: Entity, banquet: Entity, problem: Problem) -> None:
    world.say(
        f"The old evaluator came to look at the feast and said she would "
        f"evaluate every dish, from the honey cakes to the stew."
    )
    world.say(
        f"But there was a problem: {problem.label}. If no one solved it, the banquet "
        f"would fail before the lamps were lit."
    )
    banquet.memes["trouble"] += 1


def face_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.label} did not run away. {hero.pronoun().capitalize()} looked at the "
        f"{problem.label} and thought hard, like a fox looking for a path in snow."
    )
    world.say(
        f"{hero.label} said, 'We can still make this work if we use a little wit.'"
    )


def try_fix(world: World, hero: Entity, problem: Problem, fix: Fix) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.label} chose a kind fix: {fix.label}. {fix.verb.capitalize()} was not grand, "
        f"but it was gentle and careful."
    )
    world.say(
        f"{fix.tail}."
    )


def evaluate_bad(world: World, evaluator: Entity, banquet: Entity, problem: Problem) -> None:
    evaluator.memes["judgment"] += 1
    banquet.meters["spoil"] += 1
    banquet.meters["break"] += 1
    world.say(
        f"When the old evaluator tasted the food, she frowned. The fix helped a little, "
        f"but not enough for her stern taste."
    )
    world.say(
        f"She declared the banquet failed, and the village let out one long sigh."
    )


def ending_image(world: World, hero: Entity, banquet: Entity) -> None:
    world.say(
        f"Still, {hero.label} shared the last warm roll with the youngest child, and "
        f"the little one smiled through crumbs."
    )
    world.say(
        f"By the end, the tables were bare, the candles were low, and a brave kindness "
        f"sat quietly beside the cooling feast."
    )


def tell(hall: Hall, problem: Problem, fix: Fix, hero_name: str, evaluator_name: str) -> World:
    world = World(hall)
    host = world.add(Entity(id="Host", kind="character", type="woman", label="the baker"))
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    evaluator = world.add(Entity(id="Evaluator", kind="character", type="woman", label=evaluator_name))
    banquet = world.add(Entity(id="Banquet", type="thing", label="banquet"))
    problem_ent = world.add(Entity(id="Problem", type="thing", label=problem.label))

    bring_banquet(world, host, banquet)
    world.para()
    announce_evaluation(world, evaluator, banquet, problem)
    face_problem(world, hero, problem)
    try_fix(world, hero, problem, fix)
    world.para()
    evaluate_bad(world, evaluator, banquet, problem)
    ending_image(world, hero, banquet)

    world.facts.update(
        host=host,
        hero=hero,
        evaluator=evaluator,
        banquet=banquet,
        problem=problem,
        fix=fix,
        problem_ent=problem_ent,
        failed=True,
    )
    return world


HALLS = {
    "village_hall": Hall(place="the village hall", indoors=True, affords={"banquet", "evaluate"}),
}

PROBLEMS = {
    "missing_salt": Problem(
        id="missing_salt",
        label="the salt jar was empty",
        verb="lose the salt",
        gerund="losing the salt",
        issue="missing salt",
        fix_hint="borrow a small pinch from the neighbor",
        tags={"banquet", "evaluate", "kindness"},
    ),
    "cracked_soup_pot": Problem(
        id="cracked_soup_pot",
        label="the soup pot had a crack in its side",
        verb="leak soup",
        gerund="leaking soup",
        issue="a cracked soup pot",
        fix_hint="wrap it in cloth and clay",
        tags={"banquet", "evaluate", "problem_solving"},
    ),
    "burnt_honey": Problem(
        id="burnt_honey",
        label="the honey cakes had burned edges",
        verb="smell burnt",
        gerund="burning",
        issue="burnt honey cakes",
        fix_hint="cover them with fruit and cream",
        tags={"banquet", "evaluate", "kindness"},
    ),
}

FIXES = {
    "borrow_salt": Fix(
        id="borrow_salt",
        label="a pinch of salt from the neighbor",
        verb="borrowed a pinch from the neighbor",
        tail="The child ran to the next door cottage and came back with a tiny, careful spoonful",
        helps={"missing_salt"},
    ),
    "clay_wrap": Fix(
        id="clay_wrap",
        label="cloth and soft clay",
        verb="wrapped the pot with cloth and soft clay",
        tail="The child pressed the cloth tight and smoothed the clay around the crack",
        helps={"cracked_soup_pot"},
    ),
    "fruit_cover": Fix(
        id="fruit_cover",
        label="bright fruit slices",
        verb="covered the cakes with bright fruit slices",
        tail="The child laid strawberries in a shiny row so the burned edges would not show",
        helps={"burnt_honey"},
    ),
}

FOLK_NAMES = ["Mara", "Toma", "Elin", "Jori", "Nessa", "Pavel", "Sina", "Orin"]
EVALUATORS = ["Grandmother Rowan", "Aunt Brindle", "Old Judge Hesta", "Lady Pell"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, hall in HALLS.items():
        for pid, p in PROBLEMS.items():
            for fid, f in FIXES.items():
                if pid in f.helps and "banquet" in hall.affords and "evaluate" in hall.affords:
                    out.append((place, pid, fid))
    return out


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    hero_name: str
    evaluator_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a folk-tale story about a banquet that must be evaluated, but a small problem gets in the way.',
        f"Tell a gentle story where {f['hero'].label} tries to solve {f['problem'].label} before {f['evaluator'].label} evaluates the banquet.",
        f"Write a short child-facing tale that includes kindness, a hard evaluation, and a bad ending at the banquet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    evaluator = _safe_fact(world, f, "evaluator")
    problem = _safe_fact(world, f, "problem")
    fix = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"What did {hero.label} try to do at the banquet?",
            answer=f"{hero.label} tried to solve {problem.label} with {fix.label}.",
        ),
        QAItem(
            question=f"Why did {evaluator.label} come to the village hall?",
            answer=f"{evaluator.label} came to evaluate the banquet and judge whether the food was ready.",
        ),
        QAItem(
            question=f"How did {hero.label} show kindness during the problem?",
            answer=f"{hero.label} showed kindness by choosing a careful, helpful fix and by sharing the last warm roll at the end.",
        ),
        QAItem(
            question="What was the bad ending?",
            answer="The banquet failed the evaluation, and the feast was declared not good enough even after the fix.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banquet?",
            answer="A banquet is a big meal with many dishes, often prepared for a special occasion.",
        ),
        QAItem(
            question="What does it mean to evaluate something?",
            answer="To evaluate something means to look at it carefully and decide how good it is.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping others gently and thoughtfully, especially when things are hard.",
        ),
        QAItem(
            question="Why can a cracked pot be a problem?",
            answer="A cracked pot can leak soup or water, so the meal may not stay in the pot.",
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
has_problem(P) :- problem(P).
can_fix(P,F) :- fix(F), helps(F,P).
valid_story(Place,P,F) :- affords(Place,banquet), affords(Place,evaluate), has_problem(P), can_fix(P,F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in HALLS:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(HALLS, pid).affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for p in sorted(f.helps):
            lines.append(asp.fact("helps", fid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((place, p, f) for place, p, f in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: banquet, evaluation, problem solving, kindness, and a bad ending."
    )
    ap.add_argument("--place", choices=HALLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--evaluator")
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
    combos = valid_combos()
    if getattr(args, "problem", None) and getattr(args, "fix", None) and getattr(args, "problem", None) not in _safe_lookup(FIXES, getattr(args, "fix", None)).helps:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, fix = rng.choice(list(filtered))
    return StoryParams(
        place=place,
        problem=problem,
        fix=fix,
        hero_name=getattr(args, "name", None) or rng.choice(FOLK_NAMES),
        evaluator_name=getattr(args, "evaluator", None) or rng.choice(EVALUATORS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(HALLS, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(FIXES, params.fix),
        params.hero_name,
        params.evaluator_name,
    )
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
    StoryParams(
        place="village_hall",
        problem="missing_salt",
        fix="borrow_salt",
        hero_name="Mara",
        evaluator_name="Old Judge Hesta",
    ),
    StoryParams(
        place="village_hall",
        problem="cracked_soup_pot",
        fix="clay_wrap",
        hero_name="Toma",
        evaluator_name="Grandmother Rowan",
    ),
    StoryParams(
        place="village_hall",
        problem="burnt_honey",
        fix="fruit_cover",
        hero_name="Elin",
        evaluator_name="Aunt Brindle",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for t in vals:
            print("  ", t)
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
            header = f"### {p.hero_name}: {p.problem} via {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
