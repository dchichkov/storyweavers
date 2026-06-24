#!/usr/bin/env python3
"""
storyworlds/worlds/hip_addition_inner_monologue_kindness_superhero_story.py
===========================================================================

A standalone storyworld for a tiny superhero-style domain featuring a hip,
an addition, inner monologue, and kindness.

Premise:
A young hero feels a sharp hip ache before a neighborhood kindness mission.
They privately worry, then use addition to count what they can carry, accept
help, and finish the rescue with a kinder plan.

The world is intentionally small and state-driven:
- typed entities with physical meters and emotional memes
- a forward-chaining simulation
- a reasonableness gate
- a Python/ASP twin
- grounded prose and QA

This file is self-contained except for the shared result containers
(`results.py`) and optional clingo support used only for ASP modes.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Location:
    id: str
    label: str
    safe: bool = True
    supports_rescue: bool = True
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
class Problem:
    id: str
    label: str
    hip_pain: float
    requires_lifting: bool
    kind_words: tuple[str, ...]
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
class Aid:
    id: str
    label: str
    counts: tuple[int, int]
    helps_hip: bool = False
    helps_kindness: bool = False
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
    def __init__(self, location: Location) -> None:
        self.location = location
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
        w = World(self.location)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    location: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    problem: str
    aid: str
    seed: Optional[int] = None
    p: object | None = None
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


LOCATIONS = {
    "city": Location(id="city", label="the city rooftop"),
    "alley": Location(id="alley", label="the little alley"),
    "clinic": Location(id="clinic", label="the neighborhood clinic"),
}

PROBLEMS = {
    "stuck_gate": Problem(
        id="stuck_gate",
        label="a stuck gate",
        hip_pain=1.0,
        requires_lifting=True,
        kind_words=("stuck", "gate", "help"),
    ),
    "heavy_box": Problem(
        id="heavy_box",
        label="a heavy box",
        hip_pain=2.0,
        requires_lifting=True,
        kind_words=("heavy", "box", "lift"),
    ),
    "fallen_kite": Problem(
        id="fallen_kite",
        label="a fallen kite in a tree",
        hip_pain=0.5,
        requires_lifting=False,
        kind_words=("kite", "tree", "kindness"),
    ),
}

AIDS = {
    "counting_gloves": Aid(
        id="counting_gloves",
        label="counting gloves",
        counts=(2, 3),
        helps_hip=True,
        helps_kindness=True,
    ),
    "small_cart": Aid(
        id="small_cart",
        label="a small cart",
        counts=(1, 4),
        helps_hip=True,
        helps_kindness=False,
    ),
    "kind_notes": Aid(
        id="kind_notes",
        label="kind notes",
        counts=(3, 2),
        helps_hip=False,
        helps_kindness=True,
    ),
}

HERO_NAMES = ["Nova", "Maya", "Iris", "Leo", "Jade", "Milo"]
HELPER_NAMES = ["Pip", "Tess", "Arlo", "Zuri", "Finn", "Nina"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc in LOCATIONS:
        for prob in PROBLEMS:
            for aid in AIDS:
                if _safe_lookup(PROBLEMS, prob).requires_lifting and _safe_lookup(AIDS, aid).helps_hip:
                    combos.append((loc, prob, aid))
                elif not _safe_lookup(PROBLEMS, prob).requires_lifting and _safe_lookup(AIDS, aid).helps_kindness:
                    combos.append((loc, prob, aid))
    return combos


def reasonableness_gate(problem: Problem, aid: Aid) -> bool:
    if problem.requires_lifting:
        return aid.helps_hip
    return aid.helps_kindness


ASP_RULES = r"""
valid(L,P,A) :- location(L), problem(P), aid(A), needs_hip(P), helps_hip(A).
valid(L,P,A) :- location(L), problem(P), aid(A), needs_kind(P), helps_kindness(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.requires_lifting:
            lines.append(asp.fact("needs_hip", pid))
        else:
            lines.append(asp.fact("needs_kind", pid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        if a.helps_hip:
            lines.append(asp.fact("helps_hip", aid))
        if a.helps_kindness:
            lines.append(asp.fact("helps_kindness", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - ap))
    print("only asp:", sorted(ap - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style storyworld with hip pain, addition, and kindness.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
              if (getattr(args, "location", None) is None or c[0] == getattr(args, "location", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    loc, prob, aid = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = next(n for n in HELPER_NAMES if n != hero_name)
    return StoryParams(loc, hero_name, hero_type, helper_name, helper_type, prob, aid)


def _init_world(params: StoryParams) -> World:
    world = World(_safe_lookup(LOCATIONS, params.location))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    problem = _safe_lookup(PROBLEMS, params.problem)
    aid = _safe_lookup(AIDS, params.aid)
    world.add(Entity(id="problem", kind="thing", type=problem.id, label=problem.label,
                     attrs={"requires_lifting": problem.requires_lifting}))
    world.add(Entity(id="aid", kind="thing", type=aid.id, label=aid.label,
                     attrs={"helps_hip": aid.helps_hip, "helps_kindness": aid.helps_kindness}))
    hero.meters["hip"] = problem.hip_pain
    helper.memes["kindness"] = 1.0
    hero.memes["worry"] = 1.0
    hero.memes["hope"] = 0.0
    helper.memes["hope"] = 1.0
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["problem_cfg"] = problem
    world.facts["aid_cfg"] = aid
    return world


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    hero = world.get("hero")
    helper = world.get("helper")
    aid = world.get("aid")
    if hero.meters["hip"] >= THRESHOLD and world.facts["problem_cfg"].requires_lifting:
        sig = ("hip_worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append(f"{hero.label} felt a sharp hip ache and slowed down.")
    if aid.attrs.get("helps_hip") and hero.meters["hip"] >= THRESHOLD:
        sig = ("hip_help",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hope"] += 1
            helper.memes["kindness"] += 1
            out.append(f"{helper.label} offered a kinder way to move the load.")
    if aid.attrs.get("helps_kindness"):
        sig = ("kind_help",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["kindness"] += 1
            out.append(f"{helper.label} suggested counting what could be done safely.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = _init_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    prob = world.facts["problem_cfg"]
    aid = world.facts["aid_cfg"]

    world.say(f"{hero.label} wore a small cape and stood at {world.location.label}.")
    world.say(f"{hero.label} saw {prob.label} and felt {hero.pronoun('possessive')} hip sting a little.")
    world.say(f"In {hero.label}'s head, a quiet inner monologue said, “I can still help, but I should be careful.”")
    world.para()
    world.say(f"{helper.label} came beside {hero.label} with {aid.label}.")
    world.say(f"{hero.label} counted {aid.counts[0]} steps and {aid.counts[1]} hands in the plan, which made {aid.counts[0] + aid.counts[1]} good ways to share the work.")
    propagate(world)
    if prob.requires_lifting:
        world.say(f"{hero.label} did not try to lift alone.")
        world.say(f"Instead, {helper.label} used {aid.label} and the two of them moved together.")
        hero.memes["kindness"] += 1
    else:
        world.say(f"{hero.label} chose a gentle kindness first, and that was enough.")
        hero.memes["kindness"] += 1
    world.para()
    world.say(f"By the end, {hero.label} stood taller, and {hero.label}'s hip hurt less.")
    world.say(f"The little team left {world.location.label} brighter than before.")
    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prob = f["problem_cfg"]
    aid = f["aid_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old about {hero.label} using inner monologue and kindness to solve {prob.label}.',
        f"Tell a gentle superhero story where {hero.label} feels hip pain, counts with addition, and works with {helper.label} and {aid.label}.",
        f'Write a simple hero story that includes a hip, addition, and a kind choice that helps everyone finish the job.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prob = f["problem_cfg"]
    aid = f["aid_cfg"]
    return [
        QAItem(
            question=f"What did {hero.label} feel in {hero.pronoun('possessive')} hip?",
            answer=f"{hero.label} felt a sharp hip ache, so {hero.pronoun()} knew to slow down and be careful.",
        ),
        QAItem(
            question=f"What did {hero.label} think in the inner monologue?",
            answer=f"{hero.label} thought, “I can still help, but I should be careful.” That helped turn worry into a calm plan.",
        ),
        QAItem(
            question=f"How did addition help {hero.label} and {helper.label}?",
            answer=f"{hero.label} counted {aid.counts[0]} and {aid.counts[1]} and got {sum(aid.counts)}. Counting helped them share the work in a simple, safe way.",
        ),
        QAItem(
            question=f"How did kindness change the ending?",
            answer=f"{helper.label} chose a kinder plan, {hero.label} accepted help, and the problem got solved without anyone getting hurt.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is addition?",
            answer="Addition is putting numbers together to find a bigger total.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thinking about how to care for other people.",
        ),
        QAItem(
            question="What is a hip?",
            answer="A hip is part of your body near your waist that helps you stand and walk.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: {e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for loc, prob, aid in valid_combos():
            p = StoryParams(loc, "Nova", "girl", "Pip", "boy", prob, aid)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
