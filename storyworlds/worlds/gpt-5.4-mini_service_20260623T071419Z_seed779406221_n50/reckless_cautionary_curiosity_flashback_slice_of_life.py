#!/usr/bin/env python3
"""
storyworlds/worlds/reckless_cautionary_curiosity_flashback_slice_of_life.py
===========================================================================

A small slice-of-life storyworld about a curious child, a cautious reminder,
and a flashback that helps them choose the safer way.

Premise:
- A child wants something just out of reach in an ordinary home setting.
- Their curiosity gets a little reckless.
- A cautionary flashback makes the risk feel real.
- They choose a safer method and end with a calm, concrete image.

This world is intentionally compact: a kitchen or hallway task, one child,
one caring adult, and one small object on a high shelf or counter.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    kind: str
    mood: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    verb: str
    noun: str
    reason: str
    risk: str
    zone: str
    reckless_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    safe_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    prop = world.get("prop")
    if child.meters["climb"] < THRESHOLD or prop.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    world.get("adult").memes["alert"] += 1
    out.append("The chair gave a little wobble, and the room felt suddenly too small.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["flashback"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("adult").memes["caution"] += 1
    out.append("A remembered tumble made the warning feel extra real.")
    return out


CAUSAL_RULES = [Rule(name="wobble", apply=_r_wobble), Rule(name="flashback", apply=_r_flashback)]


def valid_choice(goal: Goal, helper: Helper) -> bool:
    return goal.id in helper.safe_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for goal_id, goal in GOALS.items():
            for helper_id, helper in HELPERS.items():
                if valid_choice(goal, helper):
                    combos.append((place, goal_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    goal: str
    helper: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", kind="home", mood="ordinary", afford={"reach"}),
    "hallway": Setting(place="the hallway", kind="home", mood="quiet", afford={"reach"}),
    "laundry": Setting(place="the laundry room", kind="home", mood="warm", afford={"reach"}),
}

GOALS = {
    "jar": Goal(
        id="jar",
        verb="reach",
        noun="the jam jar",
        reason="they wanted the jam for toast",
        risk="the chair might tip",
        zone="feet",
        reckless_hint="the child climbed up too quickly",
        tags={"jar", "jam", "reach", "reckless"},
    ),
    "cookies": Goal(
        id="cookies",
        verb="reach",
        noun="the cookie tin",
        reason="they could smell cookies inside",
        risk="the stool might slip",
        zone="feet",
        reckless_hint="the child stretched up on tiptoe",
        tags={"cookies", "reach", "reckless"},
    ),
    "book": Goal(
        id="book",
        verb="reach",
        noun="the picture book",
        reason="they had seen a bright cover on the shelf",
        risk="the old chair could wobble",
        zone="feet",
        reckless_hint="the child leaned far over the edge",
        tags={"book", "reach", "curiosity"},
    ),
}

HELPERS = {
    "stepstool": Helper(
        id="stepstool",
        label="step stool",
        phrase="a small step stool",
        safe_for={"jar", "cookies", "book"},
        tags={"stepstool"},
    ),
    "bell": Helper(
        id="bell",
        label="calling bell",
        phrase="a little calling bell",
        safe_for={"jar", "cookies", "book"},
        tags={"bell"},
    ),
    "ask_help": Helper(
        id="ask_help",
        label="grown-up help",
        phrase="a grown-up helping hand",
        safe_for={"jar", "cookies", "book"},
        tags={"help"},
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Theo", "Eli"]
TRAITS = ["curious", "careful", "restless", "thoughtful", "reckless"]


def tell(setting: Setting, goal: Goal, helper: Helper, name: str, gender: str, adult: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, attrs={"trait": trait}))
    parent = world.add(Entity(id="adult", kind="character", type=adult, label=f"the {adult}"))
    prop = world.add(Entity(id="prop", kind="thing", type="thing", label=goal.noun, owner=child.id, tags=goal.tags))
    safe = world.add(Entity(id="safe", kind="thing", type="thing", label=helper.label, attrs={"phrase": helper.phrase}))
    child.memes["curiosity"] = 2
    child.memes["reckless"] = 1 if trait == "reckless" else 0
    child.memes["care"] = 0
    child.meters["climb"] = 0
    prop.meters["wobble"] = 0
    parent.memes["caution"] = 1
    child.memes["flashback"] = 0
    world.facts["goal"] = goal
    world.facts["helper"] = helper
    world.facts["prop"] = prop
    world.facts["child"] = child
    world.facts["adult"] = parent
    world.say(f"{name} was a {trait} little {gender} who noticed everything in {setting.place}.")
    world.say(f"{name} kept thinking about {goal.noun} because {goal.reason}.")
    world.para()
    world.say(f"One afternoon, {name} spotted {goal.noun} up high.")
    world.say(f'{name} wanted to {goal.verb} right away, even though {goal.risk}.')
    child.meters["climb"] += 1
    prop.meters["wobble"] += 1
    propagate(world)
    world.para()
    world.say(f'{name} had almost made a reckless choice when {parent.label_word} spoke up.')
    world.say(f'"Let’s slow down," {parent.label_word} said. "{goal.risk}."')
    child.memes["flashback"] += 1
    world.say(f"That reminder brought back a flashback of a smaller tumble and a dusty knee.")
    propagate(world)
    world.say(f"{name} looked at the {helper.label} and listened this time.")
    if helper.id == "stepstool":
        child.meters["climb"] = 0
        prop.meters["wobble"] = 0
        child.memes["curiosity"] += 1
        world.para()
        world.say(f"Together they got {helper.phrase}, and {name} reached carefully.")
        world.say(f"In the end, {name} got the {goal.noun} down safely and set it on the counter.")
        world.say(f"The {goal.noun} sat beside a clean plate, and the room felt calm again.")
    else:
        world.para()
        world.say(f"Together they used {helper.phrase}, and {name} found a safe way to ask for it.")
        world.say(f"In the end, the {goal.noun} came down gently, and nobody needed to scold anyone.")
        world.say(f"The {goal.noun} waited on the table while tea steamed nearby.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    return [
        f"Write a short slice-of-life story about {child.label} being curious about {goal.noun}, but choosing the safe way after a cautionary flashback.",
        f"Tell a gentle story in an ordinary home where {child.label} gets a reckless urge, then remembers a wobble and listens to a grown-up.",
        f"Write a small child-facing story that includes curiosity, a flashback, and a calm ending with {goal.noun}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    a = world.facts["adult"]
    g = world.facts["goal"]
    h = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {c.label} want to do in {world.setting.place}?",
            answer=f"{c.label} wanted to {g.verb} so {c.label.lower()} could get {g.noun}. {g.reason.capitalize()}.",
        ),
        QAItem(
            question=f"Why did {a.label_word} warn {c.label}?",
            answer=f"{a.label_word.capitalize()} warned {c.label} because {g.risk}. {a.label_word.capitalize()} did not want the chair or stool to slip.",
        ),
        QAItem(
            question=f"What did the flashback remind {c.label} of?",
            answer="It brought back a memory of a smaller tumble and a dusty knee. That made the caution feel real instead of like a grown-up being fussy.",
        ),
        QAItem(
            question=f"How did {c.label} get {g.noun} safely at the end?",
            answer=f"{c.label} used {h.phrase} and took the careful way down. In the ending, {g.noun} sat safely on the counter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more, look closer, or ask questions about something interesting.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you do not get hurt or break something. It helps you pause and think first.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a remembered moment comes back into your mind. It can help you notice a lesson from before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", goal="jar", helper="stepstool", name="Mia", gender="girl", adult="mother", trait="curious"),
    StoryParams(place="hallway", goal="book", helper="bell", name="Leo", gender="boy", adult="father", trait="reckless"),
    StoryParams(place="laundry", goal="cookies", helper="ask_help", name="Nora", gender="girl", adult="mother", trait="thoughtful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: reckless curiosity, caution, and a helpful flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goal is None or c[1] == args.goal)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, helper=helper, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.goal not in GOALS or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.place], GOALS[params.goal], HELPERS[params.helper], params.name, params.gender, params.adult, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
valid(P,G,H) :- place(P), goal(G), helper(H), safe_for(H,G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GOALS:
        lines.append(asp.fact("goal", g))
    for h, helper in HELPERS.items():
        lines.append(asp.fact("helper", h))
        for g in sorted(helper.safe_for):
            lines.append(asp.fact("safe_for", h, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    print("OK" if py == cl else "MISMATCH")
    return 0 if py == cl else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
