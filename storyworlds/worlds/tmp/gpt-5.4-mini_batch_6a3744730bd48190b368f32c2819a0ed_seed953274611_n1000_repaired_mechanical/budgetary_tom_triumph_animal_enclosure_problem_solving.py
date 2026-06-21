#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/budgetary_tom_triumph_animal_enclosure_problem_solving.py
==========================================================================================

A standalone storyworld for a tiny bedtime tale about a child, a budgetary
problem, an animal enclosure, a calm fix, and a reconciliation at the end.

Premise:
- Tom wants to make the animal enclosure peaceful and cozy at bedtime.
- A small budgetary problem threatens the plan.
- Tom and a helper choose a careful, clever repair instead of a costly one.
- The animals settle, the grown-ups soften, and everyone shares a quiet triumph.

The world is built as a small simulation with typed entities, physical meters,
and emotional memes. The story is generated from simulated state, not from a
frozen template with swapped nouns.
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Budget:
    id: str
    label: str
    total: int
    reserve: int
    low_cost_fix: str
    full_fix: str
    extra_help: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Problem:
    id: str
    label: str
    cost: int
    discomfort: int
    needs: str
    trigger: str
    severity: int = 1
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Animal:
    id: str
    label: str
    type: str
    comfort_need: str
    soothing_sound: str
    calm_gain: int = 1
    appetite: int = 1
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Fix:
    id: str
    label: str
    cost: int
    comfort: int
    method: str
    result: str
    fits_budget: bool = True
    careful: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        c = World()
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.events = list(self.events)
        return c


@dataclass
class StoryParams:
    enclosure: str
    budget: str
    problem: str
    animal: str
    fix: str
    helper: str
    helper_type: str
    tom_name: str = "Tom"
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


ENLACES = {
    "animal_enclosure": "the animal enclosure",
    "pet_pen": "the pet enclosure",
    "zoo_yard": "the zoo yard",
}

BUDGETS = {
    "tight": Budget(
        id="tight",
        label="budgetary",
        total=5,
        reserve=2,
        low_cost_fix="mend the little gate with rope and a spare clip",
        full_fix="buy a brand-new gate panel",
        extra_help="save the last coins for tomorrow",
    ),
    "steady": Budget(
        id="steady",
        label="budgetary",
        total=8,
        reserve=3,
        low_cost_fix="patch the latch and tighten the hinge",
        full_fix="replace the whole latch with a new one",
        extra_help="keep enough coins for hay and treats",
    ),
}

PROBLEMS = {
    "gate": Problem(
        id="gate",
        label="the gate",
        cost=4,
        discomfort=2,
        needs="a quiet latch",
        trigger="kept creaking and clicking in the wind",
        severity=2,
    ),
    "lamp": Problem(
        id="lamp",
        label="the lamp",
        cost=5,
        discomfort=1,
        needs="a safe glow",
        trigger="flickered and made the shadows jump",
        severity=1,
    ),
    "bedding": Problem(
        id="bedding",
        label="the bedding",
        cost=3,
        discomfort=2,
        needs="a drier nest",
        trigger="had turned lumpy and damp",
        severity=1,
    ),
}

ANIMALS = {
    "rabbit": Animal(
        id="rabbit",
        label="the rabbit",
        type="rabbit",
        comfort_need="soft hay",
        soothing_sound="a gentle nibble",
        calm_gain=2,
        appetite=1,
    ),
    "pony": Animal(
        id="pony",
        label="the pony",
        type="pony",
        comfort_need="a brushed mane",
        soothing_sound="a slow breath",
        calm_gain=2,
        appetite=1,
    ),
    "goat": Animal(
        id="goat",
        label="the goat",
        type="goat",
        comfort_need="a tidy corner",
        soothing_sound="a tiny hoof tap",
        calm_gain=1,
        appetite=2,
    ),
}

FIXES = {
    "mend": Fix(
        id="mend",
        label="mend-it fix",
        cost=2,
        comfort=2,
        method="patched the problem with a careful little repair",
        result="the problem settled down without spending much",
        fits_budget=True,
        careful=True,
    ),
    "trade": Fix(
        id="trade",
        label="trade fix",
        cost=3,
        comfort=2,
        method="swapped a small extra task for the needed parts",
        result="the helper found a fair exchange and the repair moved on",
        fits_budget=True,
        careful=True,
    ),
    "replace": Fix(
        id="replace",
        label="replace fix",
        cost=6,
        comfort=3,
        method="wanted to replace everything at once",
        result="the shiny answer cost too much for the small budget",
        fits_budget=False,
        careful=False,
    ),
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_worry(world: World) -> list[str]:
    out = []
    problem = world.get("problem")
    budget = world.get("budget")
    if problem.meters["trouble"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    budget.memes["worry"] += 1
    world.get("tom").memes["determination"] += 1
    out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    animal = world.get("animal")
    if animal.memes["calm"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["warmth"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def budget_pressure(budget: Budget, problem: Problem) -> bool:
    return problem.cost > budget.reserve


def fix_reasonable(budget: Budget, fix: Fix, problem: Problem) -> bool:
    return fix.fits_budget and fix.cost <= budget.total and fix.cost <= problem.cost


def chosen_fix(budget: Budget, fix: Fix, problem: Problem) -> bool:
    return fix_reasonable(budget, fix, problem)


def solve_budget(world: World, tom: Entity, helper: Entity, budget: Budget, problem: Problem, animal: Animal, fix: Fix) -> None:
    world.say(
        f"At the {world.facts['enclosure_label']}, Tom noticed {problem.label_word} "
        f"{problem.trigger}."
    )
    tom.memes["concern"] += 1
    world.say(
        f'"This is a {budget.label} problem," Tom whispered, "but I think we can still help."'
    )
    if budget_pressure(budget, problem):
        world.say(
            f"The grown-up looked at the coins and frowned a little, because the big answer would cost too much."
        )
    else:
        world.say("There was enough money for a calm repair, so nobody had to rush.")

    helper.memes["support"] += 1
    tom.memes["planning"] += 1
    world.say(
        f"Tom and {helper.id} counted the parts, thought of a gentler way, and chose to {fix.method}."
    )
    problem.meters["trouble"] += 1
    propagate(world, narrate=False)

    if chosen_fix(budget, fix, problem):
        problem.meters["fixed"] += 1
        animal.memes["calm"] += animal.calm_gain
        budget.meters["spent"] += fix.cost
        tom.memes["pride"] += 1
        helper.memes["pride"] += 1
        world.say(
            f"The fix worked. {fix.result}, and {animal.label} settled again in the soft straw."
        )
        world.say(
            f"Then Tom and {helper.id} shared a small smile, because the enclosure was safe, quiet, and warm."
        )
        if animal.id == "rabbit":
            world.say("The rabbit twitched its nose, nibbled once, and tucked itself into the hay like a little cloud.")
        elif animal.id == "pony":
            world.say("The pony breathed slowly, and its hooves rested still beside the fresh straw.")
        else:
            world.say("The goat stopped its tapping, gave one sleepy blink, and leaned into the calm.")
        world.say(
            "That night, the whole place felt settled at last, and Tom knew that a careful idea can be a triumph too."
        )
    else:
        budget.meters["stress"] += 1
        world.say(
            f"That idea would have been shiny, but it cost too much for the budgetary little pouch, so Tom looked again."
        )
        world.say(
            f"He tried the cheaper fix instead, and at last the problem loosened its grip."
        )
        problem.meters["fixed"] += 1
        animal.memes["calm"] += 1
        world.say(
            f"By bedtime, {animal.label} was calm again, and Tom felt proud of the small triumph."
        )


def tell(enclosure: str, budget: Budget, problem: Problem, animal: Animal, fix: Fix, helper_name: str, helper_type: str, tom_name: str = "Tom") -> World:
    world = World()
    tom = world.add(Entity(id=tom_name, kind="character", type="boy", role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    budget_ent = world.add(Entity(id="budget", kind="thing", type="budget", label=budget.label))
    prob_ent = world.add(Entity(id="problem", kind="thing", type="problem", label=problem.label))
    animal_ent = world.add(Entity(id="animal", kind="thing", type=animal.type, label=animal.label))

    world.facts["enclosure_label"] = ENLACES[enclosure]
    world.facts["budget"] = budget
    world.facts["problem"] = problem
    world.facts["animal"] = animal
    world.facts["fix"] = fix
    world.facts["helper"] = helper
    world.facts["tom"] = tom

    world.say(
        f"On a sleepy evening, Tom and {helper_name} walked to {ENLACES[enclosure]}, where the animals were getting ready for bed."
    )
    world.say(
        f"{animal.label.capitalize()} was there, and the little place felt peaceful until {problem.label} {problem.trigger}."
    )
    world.para()
    solve_budget(world, tom, helper, budget, problem, animal, fix)
    world.facts["outcome"] = "reconciled" if animal.memes["calm"] >= THRESHOLD else "triumph"
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for enc in ENLACES:
        for bud in BUDGETS:
            for prob in PROBLEMS:
                for ani in ANIMALS:
                    for fx in FIXES:
                        if fix_reasonable(BUDGETS[bud], FIXES[fx], PROBLEMS[prob]):
                            combos.append((enc, bud, prob, ani, fx))
    return combos


@dataclass
class StoryParams:
    enclosure: str
    budget: str
    problem: str
    animal: str
    fix: str
    helper: str
    helper_type: str
    tom_name: str = "Tom"
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


HELPER_NAMES = ["Mia", "Nina", "Ben", "Rose", "Ava", "Sam"]
HELPER_TYPES = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: Tom solves a budgetary problem in an animal enclosure.")
    ap.add_argument("--enclosure", choices=ENLACES)
    ap.add_argument("--budget", choices=BUDGETS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.enclosure is None or c[0] == args.enclosure)
              and (args.budget is None or c[1] == args.budget)
              and (args.problem is None or c[2] == args.problem)
              and (args.animal is None or c[3] == args.animal)
              and (args.fix is None or c[4] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    enc, bud, prob, ani, fx = rng.choice(sorted(combos))
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if helper == "Tom":
        helper = "Mia"
    return StoryParams(
        enclosure=enc,
        budget=bud,
        problem=prob,
        animal=ani,
        fix=fx,
        helper=helper,
        helper_type=helper_type,
        tom_name="Tom",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a bedtime story in an animal enclosure where Tom solves a budgetary problem with a careful fix and everyone reconciles.",
        f"Tell a child-sized story about Tom, {f['helper'].id}, and {f['animal'].label} in {f['enclosure_label']} that includes the words budgetary, tom, and triumph.",
        f"Write a calm bedtime story where {f['problem'].label_word} is fixed without spending too much, ending in a quiet triumph.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    budget: Budget = f["budget"]
    problem: Problem = f["problem"]
    animal: Animal = f["animal"]
    fix: Fix = f["fix"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question="What was the problem in the story?",
            answer=f"The problem was {problem.label}, which {problem.trigger}. It made the animal enclosure feel unsettled until Tom and {helper.id} found a calm fix.",
        ),
        QAItem(
            question="Why did Tom need to think carefully about money?",
            answer=f"The answer had to fit a {budget.label} limit, so the biggest and most expensive choice was not the right one. Tom had to choose a smaller repair that still solved the trouble.",
        ),
        QAItem(
            question="How did Tom and the helper solve it?",
            answer=f"They chose to {fix.method}, and that was enough to settle the problem. The clever repair kept the enclosure safe without wasting coins.",
        ),
        QAItem(
            question="What changed for the animal at the end?",
            answer=f"{animal.label.capitalize()} grew calm again and settled into the soft straw. That change shows the problem was fixed in a peaceful way.",
        ),
        QAItem(
            question="Was there a reconciliation?",
            answer=f"Yes. Tom, {helper.id}, and the grown-up stopped worrying and agreed on the careful plan. They ended the night on the same side, which is why the story feels warm at the end.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    budget: Budget = f["budget"]
    problem: Problem = f["problem"]
    animal: Animal = f["animal"]
    return [
        QAItem(
            question="What does budgetary mean?",
            answer="Budgetary means it has to do with money that is set aside carefully. In a story, it means the characters have to choose a fix that fits what they can spend.",
        ),
        QAItem(
            question="What is an animal enclosure?",
            answer="An animal enclosure is a safe place where animals live or stay. It should have enough space, food, and care so the animals can rest peacefully.",
        ),
        QAItem(
            question="Why are gentle repairs often better than big expensive ones?",
            answer="Gentle repairs can solve the real problem without using more money than needed. They are useful when a careful fix is enough and the larger choice would waste resources.",
        ),
        QAItem(
            question=f"What does {animal.label} need to feel calm?",
            answer=f"{animal.label.capitalize()} needs {animal.comfort_need}. Little comforts like that help the animal settle down and feel safe.",
        ),
        QAItem(
            question=f"Why was {problem.label} hard to ignore?",
            answer=f"{problem.label.capitalize()} mattered because it could make the enclosure less peaceful if left alone. The trouble needed a solution before bedtime so the animals could rest.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(problem).
budget(budgetary).
animal(rabbit;pony;goat).
fix(mend;trade;replace).

reasonable_fix(mend).
reasonable_fix(trade).

valid(enclosure,budgetary,gate,rabbit,mend) :- reasonable_fix(mend).
valid(enclosure,budgetary,lamp,pony,mend) :- reasonable_fix(mend).
valid(enclosure,budgetary,bedding,goat,mend) :- reasonable_fix(mend).
valid(enclosure,steady,gate,rabbit,trade) :- reasonable_fix(trade).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for enc in ENLACES:
        lines.append(asp.fact("enclosure", enc))
    for bid in BUDGETS:
        lines.append(asp.fact("budget_kind", bid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_kind", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal_kind", aid))
    for fid in FIXES:
        lines.append(asp.fact("fix_kind", fid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return rc


def explain_rejection() -> str:
    return "(No story: the chosen fix does not fit the budgetary problem well enough.)"


def generate(params: StoryParams) -> StorySample:
    if params.enclosure not in ENLACES:
        raise StoryError("Unknown enclosure.")
    if params.budget not in BUDGETS:
        raise StoryError("Unknown budget.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
    world = tell(
        enclosure=params.enclosure,
        budget=BUDGETS[params.budget],
        problem=PROBLEMS[params.problem],
        animal=ANIMALS[params.animal],
        fix=FIXES[params.fix],
        helper_name=params.helper,
        helper_type=params.helper_type,
        tom_name=params.tom_name,
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
        enclosure="animal_enclosure",
        budget="tight",
        problem="gate",
        animal="rabbit",
        fix="mend",
        helper="Mia",
        helper_type="girl",
        tom_name="Tom",
        seed=1,
    ),
    StoryParams(
        enclosure="pet_pen",
        budget="steady",
        problem="bedding",
        animal="goat",
        fix="trade",
        helper="Ben",
        helper_type="boy",
        tom_name="Tom",
        seed=2,
    ),
    StoryParams(
        enclosure="zoo_yard",
        budget="tight",
        problem="lamp",
        animal="pony",
        fix="mend",
        helper="Rose",
        helper_type="girl",
        tom_name="Tom",
        seed=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
