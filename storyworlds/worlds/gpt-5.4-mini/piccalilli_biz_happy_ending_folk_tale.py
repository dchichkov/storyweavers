#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/piccalilli_biz_happy_ending_folk_tale.py
=========================================================================

A small standalone storyworld for a folk-tale flavored, happy-ending tale
about a village, a strange jar of piccalilli, and a child who learns that
helping with the family biz can turn a muddle into a feast.

Core premise:
- A child helps at a tiny village biz.
- A beloved jar of piccalilli is nearly lost or wasted.
- The child uses a sensible folk-tale turn: asks for help, fixes the problem,
  and the village ends in warmth, sharing, and praise.

This world is intentionally small and constraint-checked:
- typed entities with meters and memes
- a reasonableness gate
- a Python valid-combo checker
- an inline ASP twin
- three QA sets grounded in simulated state
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp

The seed words "piccalilli" and "biz" are woven into the story text.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CALM_MIN = 2

VILLAGE_NAMES = ["Hollow Hill", "Brindle Green", "Mossy Ford", "Willow Mere"]
CHILD_NAMES = ["Mina", "Pip", "Toby", "Mara", "Nell", "Robin", "Sana", "Jory"]
ADULT_NAMES = ["Gran", "Aunt Jo", "Uncle Bram", "Mum", "Dad"]
TRAITS = ["kind", "curious", "careful", "cheerful", "clever", "patient"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mum", "father": "dad"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    scene: str
    audience: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Biz:
    id: str
    label: str
    goods: str
    action: str
    pride: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    upset: str
    tags: set[str] = field(default_factory=set)
    spoil: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spill"] < THRESHOLD:
            continue
        sig = ("spoil", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "stock" in world.entities:
            world.get("stock").meters["lost"] += 1
        for k in list(world.entities.values()):
            if k.role in {"child", "helper"}:
                k.memes["worry"] += 1
        out.append("__spoil__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    stock = world.entities.get("stock")
    if not stock or stock.meters["lost"] < THRESHOLD:
        return out
    sig = ("mend", stock.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stock.meters["saved"] += 1
    out.append("__mend__")
    return out


CAUSAL_RULES = [Rule("spoil", "physical", _r_spoil), Rule("mend", "physical", _r_mend)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard(problem: Problem, stock_kind: str) -> bool:
    return problem.spoil and stock_kind == "piccalilli"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_good_fix(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= (1 + delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for biz in BIZS:
            for prob in PROBLEMS:
                if hazard(prob, "piccalilli") and sensible_fixes():
                    combos.append((place, biz, prob))
    return combos


def story_opening(world: World, child: Entity, helper: Entity, place: Place, biz: Biz) -> None:
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once in {place.label}, where {place.scene}, there lived {child.id} and {helper.id}."
    )
    world.say(
        f"They helped at the little {biz.label}, and the whole lane knew the {biz.goods} by its {biz.pride}."
    )


def introduce_piccalilli(world: World, child: Entity, stock: Entity, place: Place, biz: Biz) -> None:
    world.say(
        f"On market day the jar of piccalilli sat bright on the stall, green-gold as a summer field."
    )
    world.say(
        f"{child.id} watched closely, for the family {biz.label} needed that jar to keep the supper table cheerful."
    )


def mishap(world: World, child: Entity, stock: Entity, problem: Problem) -> None:
    child.memes["eagerness"] += 1
    stock.meters["spill"] += 1
    world.say(
        f"But in the bustle of the {problem.label}, {child.id} bumped the shelf, and a little spill began."
    )
    world.say(
        f"The {problem.danger} touched the jar, and everyone felt the first pinch of worry."
    )
    propagate(world, narrate=False)


def warning(world: World, helper: Entity, child: Entity, stock: Entity, problem: Problem) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"Easy now," said {helper.id}. "If the {problem.label} keeps slipping, the piccalilli may be lost."'
    )
    world.say(
        f"{helper.id} pointed to the jar and showed {child.pronoun('object')} how to steady it with both hands."
    )


def ask_for_help(world: World, child: Entity, helper: Entity, adult: Entity) -> None:
    child.memes["humility"] += 1
    world.say(
        f"{child.id} swallowed {child.pronoun('possessive')} pride and ran to {adult.id} for help."
    )
    world.say(
        f'"We can mend this," {adult.id} said, kind as a lantern in fog.'
    )


def fix_it(world: World, adult: Entity, fix: Fix, stock: Entity, problem: Problem) -> None:
    stock.meters["spill"] = 0.0
    stock.meters["saved"] += 1
    world.say(
        f"{adult.id} used {fix.text}."
    )
    world.say(
        f"The jar settled safe again, and the {problem.label} could not spoil the piccalilli after all."
    )


def lesson(world: World, child: Entity, helper: Entity, adult: Entity, biz: Biz) -> None:
    for e in (child, helper):
        e.memes["joy"] += 1
        e.memes["relief"] += 1
    world.say("For a moment, the whole stall went quiet.")
    world.say(
        f"Then {adult.id} smiled and hugged them both. "
        f'"A good {biz.label} is built on steady hands and honest help," {adult.id} said. '
        f'"That is how a small trouble becomes no trouble at all."'
    )
    world.say(
        f"{child.id} nodded, and the family kept the piccalilli for supper instead of wasting it."
    )


def feast_end(world: World, child: Entity, helper: Entity, adult: Entity, place: Place, biz: Biz) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At dusk the neighbors came by, and the {biz.label} smelled of bread, onions, and piccalilli."
    )
    world.say(
        f"{place.label} glowed with lamps, and {child.id} beamed as the little {biz.label} turned the saved jar into a feast."
    )


def tell(place: Place, biz: Biz, problem: Problem, fix: Fix,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         adult_name: str = "Gran", adult_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    stock = world.add(Entity(id="stock", kind="thing", type="jar", label="jar of piccalilli"))
    world.facts["place"] = place
    world.facts["biz"] = biz
    world.facts["problem"] = problem
    world.facts["fix"] = fix

    story_opening(world, child, helper, place, biz)
    introduce_piccalilli(world, child, stock, place, biz)
    world.para()
    mishap(world, child, stock, problem)
    warning(world, helper, child, stock, problem)
    ask_for_help(world, child, helper, adult)
    world.para()
    fix_it(world, adult, fix, stock, problem)
    lesson(world, child, helper, adult, biz)
    world.para()
    feast_end(world, child, helper, adult, place, biz)

    world.facts.update(child=child, helper=helper, adult=adult, stock=stock, outcome="happy")
    return world


PLACES = {
    "village": Place("village", "the village green", "the green was ringed with apple trees and little stone homes", "every face in the lane", tags={"village"}),
    "market": Place("market", "the market square", "the stalls were bright with cloth and baskets", "neighbors and travelers", tags={"market"}),
    "kitchen": Place("kitchen", "the kitchen hearth", "the kettle sang and the room smelled of warm bread", "the family table", tags={"kitchen"}),
}

BIZS = {
    "stall": Biz("stall", "stall", "herbs and jars", "set out the goods", "good order", tags={"biz", "stall"}),
    "shop": Biz("shop", "shop", "jam and pickles", "opened the door", "kind trade", tags={"biz", "shop"}),
    "cart": Biz("cart", "cart", "tea and biscuits", "rolled into the lane", "cheerful trade", tags={"biz", "cart"}),
}

PROBLEMS = {
    "jar": Problem("jar", "wobbly jar", "the shelf swayed", "would spoil the supper", tags={"jar", "spill"}),
    "crowd": Problem("crowd", "busy crowd", "the crowd pressed too close", "could knock the jar down", tags={"crowd", "spill"}),
    "ladder": Problem("ladder", "tippy ladder", "the ladder tipped", "could send the jar tumbling", tags={"ladder", "spill"}),
}

FIXES = {
    "steady": Fix("steady", 3, 2, "steadying the shelf with both hands", "trying to catch the jar too late", "steadied the shelf and saved the piccalilli", tags={"steady"}),
    "cloth": Fix("cloth", 2, 2, "wrapping the jar in a clean cloth and setting it on a flat board", "wrapping it badly and making the spill worse", "wrapped the jar safely and saved the piccalilli", tags={"cloth"}),
    "call_adult": Fix("call_adult", 3, 3, "calling for Gran before the spill grew", "hiding the trouble and hoping it would vanish", "called for help and saved the piccalilli", tags={"help"}),
}

CURATED = [
    dataclass
]


@dataclass
class StoryParams:
    place: str
    biz: str
    problem: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style happy-ending story that includes the words "piccalilli" and "biz".',
        f"Tell a gentle village tale where {f['child'].id} helps at the {f['biz'].label} and saves the piccalilli after a small mishap.",
        f"Write a happy story about a child, a family biz, and a jar of piccalilli that is nearly lost but ends up shared at supper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult = f["child"], f["helper"], f["adult"]
    biz, place, problem, fix = f["biz"], f["place"], f["problem"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who helps at the family {biz.label}, with {helper.id} and {adult.id} nearby."),
        ("What nearly went wrong?",
         f"The {problem.label} caused a small spill, and the jar of piccalilli might have been lost if nobody helped. The trouble was small, but it could have spoiled supper."),
        ("How was the problem fixed?",
         f"{adult.id} used {fix.text}, and that saved the piccalilli. Because they asked for help quickly, the jar stayed safe and the day stayed happy."),
        ("How did the story end?",
         f"It ended with a feast and warm lamps in {place.label}. The saved piccalilli became part of supper, so the ending was bright and kind."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is piccalilli?",
         "Piccalilli is a tangy pickle relish made from chopped vegetables and spices. People often eat it with bread, sandwiches, or a big supper."),
        ("What is a biz?",
         "A biz is a small business or trade. In a folk tale, it can be a little family shop, stall, or cart that helps the village."),
        ("Why do people ask for help when something starts to spill?",
         "Because quick help can stop the trouble from getting bigger. A steady hand or a grown-up can save the food and keep everyone calm."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "stall", "jar", "steady", "Mina", "girl", "Pip", "boy", "Gran", "woman", "kind"),
    StoryParams("market", "shop", "crowd", "cloth", "Toby", "boy", "Mara", "girl", "Mum", "woman", "careful"),
    StoryParams("kitchen", "cart", "ladder", "call_adult", "Nell", "girl", "Jory", "boy", "Dad", "man", "cheerful"),
]


def valid_story_params() -> list[StoryParams]:
    return CURATED[:]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.problem and not is_good_fix(FIXES[args.fix], PROBLEMS[args.problem], 0):
        raise StoryError("(No story: that fix is too weak for the trouble.)")
    place = args.place or rng.choice(list(PLACES))
    biz = args.biz or rng.choice(list(BIZS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice([f.id for f in sensible_fixes()])
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_gender = rng.choice(["girl", "boy"])
    helper_name = rng.choice([n for n in CHILD_NAMES if n != child_name])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult_name = args.adult or rng.choice(ADULT_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place, biz, problem, fix, child_name, child_gender, helper_name, helper_gender, adult_name, adult_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], BIZS[params.biz], PROBLEMS[params.problem], FIXES[params.fix],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender,
                 params.adult_name, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
hazard(P, S) :- problem(P), spoil(P), stock_kind(S).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(Place, Biz, Problem) :- place(Place), biz(Biz), problem(Problem), hazard(Problem, piccalilli), sensible(_).
outcome(happy) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid in BIZS:
        lines.append(asp.fact("biz", bid))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("stock_kind", "piccalilli"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-tested generate() on curated params.")
    except Exception as exc:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {exc}")
    try:
        rng = _random.Random(777)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        _ = sample.story
        print("OK: default-style resolve/generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAIL: default smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with piccalilli and a village biz.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--biz", choices=BIZS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    place = args.place or rng.choice(list(PLACES))
    biz = args.biz or rng.choice(list(BIZS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_name = args.adult or rng.choice(ADULT_NAMES)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    helper_name = rng.choice([n for n in CHILD_NAMES if n != child_name])
    helper_gender = rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, biz, problem, fix, child_name, child_gender, helper_name, helper_gender, adult_name, adult_gender, trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t in combos:
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
