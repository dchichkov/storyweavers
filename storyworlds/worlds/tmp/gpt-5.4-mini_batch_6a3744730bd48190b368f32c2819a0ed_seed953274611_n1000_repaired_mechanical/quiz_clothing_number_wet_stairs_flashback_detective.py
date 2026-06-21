#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quiz_clothing_number_wet_stairs_flashback_detective.py
=======================================================================================

A small detective-style story world for a child mystery set on wet stairs.

Premise
-------
A young detective notices a quiz book, a lost clothing tag, and a strange number
written on a stair. A flashback reveals who last used the stairs and why they
were wet. The detective follows the clues, solves the mystery, and ends with a
clear image of the truth.

The world is intentionally tiny and classical:
- one small setting: wet stairs
- a handful of typed entities
- physical meters and emotional memes
- a causal rule engine
- a Python reasonableness gate plus an inline ASP twin
- three QA sets grounded in simulated state, not by parsing the rendered story

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/quiz_clothing_number_wet_stairs_flashback_detective.py
    python storyworlds/worlds/gpt-5.4-mini/quiz_clothing_number_wet_stairs_flashback_detective.py --qa
    python storyworlds/worlds/gpt-5.4-mini/quiz_clothing_number_wet_stairs_flashback_detective.py --verify
    python storyworlds/worlds/gpt-5.4-mini/quiz_clothing_number_wet_stairs_flashback_detective.py --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

STAIN_THRESHOLD = 1.0
CLUE_THRESHOLD = 1.0
WET_THRESHOLD = 1.0


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    label: str
    number: int
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Clothing:
    id: str
    label: str
    phrase: str
    type: str
    owner_kind: str
    number: int
    wet_risk: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Setting:
    place: str
    detail: str
    wet: bool = True
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
class StoryParams:
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    parent: str
    clothing: str
    clue_number: str
    setting: str = "wet stairs"
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_wet_marks(world: World) -> list[str]:
    out: list[str] = []
    stairs = world.entities.get("stairs")
    if not stairs or stairs.meters["wet"] < WET_THRESHOLD:
        return out
    if ("wet_marks",) in world.fired:
        return out
    world.fired.add(("wet_marks",))
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["alert"] += 1
    stairs.meters["slippery"] += 1
    out.append("__wet__")
    return out


def _r_clue_found(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "object":
            continue
        if e.meters["clue"] < CLUE_THRESHOLD:
            continue
        sig = ("clue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("detective").memes["suspicion"] += 1
        out.append(f"{e.label} looked important.")
    return out


CAUSAL_RULES = [Rule("wet_marks", "physical", _r_wet_marks), Rule("clue_found", "social", _r_clue_found)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def has_reasonable_clue(cn: Clue) -> bool:
    return cn.number >= 1 and cn.number <= 9


def has_reasonable_clothing(cl: Clothing) -> bool:
    return cl.wet_risk and cl.number >= 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for c in CLOTHING:
        for n in CLUES:
            if has_reasonable_clothing(c) and has_reasonable_clue(n):
                combos.append((c.id, n.id))
    return combos


def flashback(world: World, detective: Entity, helper: Entity, cloth: Clothing, clue: Clue) -> None:
    detective.memes["memory"] += 1
    world.say(
        f"Then the detective remembered something from earlier: {helper.id} had hurried down the stairs with {cloth.label}, "
        f"and {clue.label} had been left behind like a tiny breadcrumb."
    )
    world.say(
        f"In the flashback, the stairs were already wet, so every step looked shiny and nervous."
    )


def opening(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"On the wet stairs, {detective.id} became a little detective and studied the shiny steps like a case file."
    )
    world.say(
        f"{helper.id} stood nearby, holding still, while the hallway echoed with drip, drip, drip."
    )


def clue_scene(world: World, cloth: Clothing, clue: Clue) -> None:
    cloth_ent = world.get(cloth.id)
    clue_ent = world.get(clue.id)
    cloth_ent.meters["stained"] += 1
    clue_ent.meters["clue"] += 1
    world.say(
        f"One clue was a piece of {cloth.label}, and another was the number {clue.number} on the stair."
    )
    world.say(
        f"The {cloth.label} was not neat anymore; it had picked up a little stain from the wet steps."
    )
    propagate(world, narrate=False)


def ask_quiz(world: World, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.memes["thinking"] += 1
    world.say(
        f"{detective.id} squinted and said, 'Quiz time: what does the number {clue.number} mean?'"
    )
    world.say(
        f"{helper.id} frowned and said it was not a game number at all; it was a hint about who had gone first."
    )


def solve(world: World, detective: Entity, helper: Entity, parent: Entity, cloth: Clothing, clue: Clue) -> None:
    detective.memes["joy"] += 1
    helper.memes["relief"] += 1
    parent.memes["pride"] += 1
    world.say(
        f"At last, {detective.id} put the clues together and solved the case."
    )
    world.say(
        f"The wet stairs were from a quick spill, {helper.id} had rushed to fetch dry clothing, and the number {clue.number} marked the step where the trouble began."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled, dried the stair rail, and folded the {cloth.label} into a neat stack."
    )


def ending(world: World, detective: Entity, helper: Entity, cloth: Clothing, clue: Clue) -> None:
    world.say(
        f"By the end, the stairs were dry, the clothing was safe, and the detective had one final look at the little number that cracked the mystery."
    )
    world.say(
        f"It was a tiny case, but the answer fit perfectly, like a glove on a clean hand."
    )


def tell(params: StoryParams) -> World:
    world = World()
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother", role="parent", label="the parent"))
    stairs = world.add(Entity(id="stairs", kind="setting", type="stairs", label="the wet stairs"))
    cloth = world.add(Entity(id=params.clothing, kind="object", type="clothing", label=CLOTHING_BY_ID[params.clothing].label))
    clue = world.add(Entity(id=params.clue_number, kind="object", type="clue", label=f"number {CLUE_BY_ID[params.clue_number].number}"))
    stairs.meters["wet"] = 1

    opening(world, detective, helper, SETTINGS[params.setting])
    world.para()
    clue_scene(world, CLOTHING_BY_ID[params.clothing], CLUE_BY_ID[params.clue_number])
    ask_quiz(world, detective, helper, CLUE_BY_ID[params.clue_number])
    world.para()
    flashback(world, detective, helper, CLOTHING_BY_ID[params.clothing], CLUE_BY_ID[params.clue_number])
    solve(world, detective, helper, parent, CLOTHING_BY_ID[params.clothing], CLUE_BY_ID[params.clue_number])
    world.para()
    ending(world, detective, helper, CLOTHING_BY_ID[params.clothing], CLUE_BY_ID[params.clue_number])

    world.facts.update(
        detective=detective,
        helper=helper,
        parent=parent,
        clothing=CLOTHING_BY_ID[params.clothing],
        clue=CLUE_BY_ID[params.clue_number],
        setting=SETTINGS[params.setting],
        outcome="solved",
    )
    return world


SETTINGS = {
    "wet stairs": Setting(place="wet stairs", detail="shiny steps and a damp rail", wet=True),
}

CLOTHING_BY_ID = {
    "raincoat": Clothing(id="raincoat", label="raincoat", phrase="a blue raincoat", type="raincoat", owner_kind="child", number=1, tags={"clothing"}),
    "sweater": Clothing(id="sweater", label="sweater", phrase="a striped sweater", type="sweater", owner_kind="child", number=2, tags={"clothing"}),
    "socks": Clothing(id="socks", label="socks", phrase="a pair of socks", type="socks", owner_kind="child", number=2, tags={"clothing"}),
}

CLUES_BY_ID = {
    "one": Clue(id="one", label="the number one", number=1, tags={"number"}),
    "two": Clue(id="two", label="the number two", number=2, tags={"number"}),
    "three": Clue(id="three", label="the number three", number=3, tags={"number"}),
}

CLOTHING = list(CLOTHING_BY_ID.values())
CLUES = list(CLUES_BY_ID.values())


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cloth = f["clothing"]
    clue = f["clue"]
    return [
        f'Write a detective story for a young child that includes the words "quiz", "clothing", and "number".',
        f"Tell a short mystery set on wet stairs where a detective notices {cloth.label} and the number {clue.number}, then remembers a flashback.",
        f"Write a gentle detective story with a flashback where wet stairs, clothing, and a number help solve a tiny case.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    parent = f["parent"]
    cloth = f["clothing"]
    clue = f["clue"]
    qa = [
        ("Who solved the mystery?", f"{detective.id} solved the mystery by studying the wet stairs, the clothing clue, and the number on the step."),
        ("What made the detective think of the past?", f"The flashback came when {detective.id} noticed how the clothing and the number matched what had happened earlier. That memory helped the detective understand why the stairs were wet."),
        ("Why was the parent pleased?", f"{parent.id} was pleased because the mystery was solved safely and calmly. The parent could dry the stairs and fold the clothing once the answer was clear."),
    ]
    qa.append((
        "What were the quiz words doing in the story?",
        "The quiz words became part of the clue trail. The detective used the quiz idea to ask questions, and the answers came from the clothing, the number, and the flashback."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"number", "clothing"}
    out = []
    if "number" in tags:
        out.append(("What is a number?", "A number tells how many things there are, or which one comes in order. It can be written as a digit, like 1 or 2."))
    if "clothing" in tags:
        out.append(("What is clothing?", "Clothing is what people wear to cover their bodies, like shirts, socks, coats, and sweaters."))
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def has_reasonable_params(clothing: Clothing, clue: Clue) -> bool:
    return clothing.wet_risk and clue.number >= 1


def explain_rejection(clothing: Clothing, clue: Clue) -> str:
    return f"(No story: {clothing.label} and the number {clue.number} do not form a useful wet-stairs detective clue.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clothing and args.quiz_number and not has_reasonable_params(CLOTHING_BY_ID[args.clothing], CLUES_BY_ID[args.quiz_number]):
        raise StoryError(explain_rejection(CLOTHING_BY_ID[args.clothing], CLUES_BY_ID[args.quiz_number]))
    choices = [c for c in CLOTHING if args.clothing is None or c.id == args.clothing]
    clues = [q for q in CLUES if args.quiz_number is None or q.id == args.quiz_number]
    if not choices or not clues:
        raise StoryError("(No valid combination matches the given options.)")
    clothing = rng.choice(choices)
    clue = rng.choice(clues)
    return StoryParams(
        detective=args.detective or rng.choice(["Nina", "Milo", "Iris", "Theo"]),
        detective_gender=args.detective_gender or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(["Bea", "Owen", "June", "Max"]),
        helper_gender=args.helper_gender or rng.choice(["girl", "boy"]),
        parent=args.parent or "Parent",
        clothing=clothing.id,
        clue_number=clue.id,
        setting="wet stairs",
    )


def generate(params: StoryParams) -> StorySample:
    if params.clothing not in CLOTHING_BY_ID or params.clue_number not in CLUES_BY_ID or params.setting not in SETTINGS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
wet_stairs.
quiz_word(quiz).
quiz_word(clothing).
quiz_word(number).

clue_number(1).
clue_number(2).
clue_number(3).

valid(C, N) :- clothing(C), clue_number(N).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CLOTHING_BY_ID.items():
        lines.append(asp.fact("clothing", cid))
        if c.wet_risk:
            lines.append(asp.fact("wet_risk", cid))
    for qid, q in CLUES_BY_ID.items():
        lines.append(asp.fact("clue_number", q.number))
        lines.append(asp.fact("quiz_word", "number"))
    lines.append(asp.fact("quiz_word", "quiz"))
    lines.append(asp.fact("quiz_word", "clothing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        story = generate(StoryParams(detective="Nina", detective_gender="girl", helper="Bea", helper_gender="girl", parent="Parent", clothing="raincoat", clue_number="one", setting="wet stairs"))
        if not story.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"FAILED: generate smoke test: {e}")
        return 1
    py = set((c.id, q.id) for c in CLOTHING for q in CLUES if has_reasonable_params(c, q))
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP parity ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP.")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world on wet stairs.")
    ap.add_argument("--clothing", choices=sorted(CLOTHING_BY_ID))
    ap.add_argument("--quiz-number", choices=sorted(CLUES_BY_ID))
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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


CURATED = [
    StoryParams(detective="Nina", detective_gender="girl", helper="Bea", helper_gender="girl", parent="Parent", clothing="raincoat", clue_number="one", setting="wet stairs"),
    StoryParams(detective="Milo", detective_gender="boy", helper="Owen", helper_gender="boy", parent="Parent", clothing="sweater", clue_number="two", setting="wet stairs"),
    StoryParams(detective="Iris", detective_gender="girl", helper="June", helper_gender="girl", parent="Parent", clothing="socks", clue_number="three", setting="wet stairs"),
]


def generation_pool(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return CURATED
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    out = []
    seen = set()
    i = 0
    while len(out) < args.n and i < max(50, args.n * 50):
        params = resolve_params(args, random.Random(base_seed + i))
        i += 1
        key = (params.detective, params.helper, params.clothing, params.clue_number)
        if key in seen:
            continue
        seen.add(key)
        out.append(params)
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c, n in asp_valid_combos():
            print(f"  {c} {n}")
        return

    samples = []
    for params in generation_pool(args):
        sample = generate(params)
        samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.detective}: {sample.params.clothing} and {sample.params.clue_number}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
