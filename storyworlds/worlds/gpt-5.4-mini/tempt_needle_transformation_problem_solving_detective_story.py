#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tempt_needle_transformation_problem_solving_detective_story.py
=============================================================================================

A small standalone storyworld for a child-facing detective tale about a lost
needle, a tempting wrong choice, a transformation, and a clever problem-solving
ending.

The world model tracks typed entities with physical meters and emotional memes.
A detective-style clue hunt begins with a tempting shortcut, turns on a careful
observation, then resolves through a transformation: the needle changes from
being "lost" to being safely magnetized to a pin cushion, proving the problem
was solved.

The seed words are intentionally present:
- tempt
- needle

The style aim is detective-story: clues, suspicion, deduction, reveal, and a
clear ending image.
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
REASONABLE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    id: str
    place: str
    clue_spot: str
    hides: str
    details: str


@dataclass
class Temptation:
    id: str
    label: str
    wrong_use: str
    is_bad: bool = True


@dataclass
class ObjectNeedle:
    id: str
    label: str
    phrase: str
    source: str
    fragile: bool = True


@dataclass
class Transformation:
    id: str
    label: str
    tool: str
    result: str
    prose: str


@dataclass
class Solution:
    id: str
    label: str
    method: str
    proof: str
    strength: int


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes["suspicion"] >= THRESHOLD and ("alarm",) not in world.fired:
        world.fired.add(("alarm",))
        detective.memes["focus"] += 1
        out.append("__alarm__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    pin = world.get("pin")
    needle = world.get("needle")
    if pin.meters["magnet_ready"] >= THRESHOLD and needle.meters["lost"] >= THRESHOLD:
        sig = ("transform",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        needle.meters["lost"] = 0.0
        needle.meters["found"] += 1
        needle.attrs["attached_to"] = pin.id
        out.append("__transform__")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    needle = world.get("needle")
    detective = world.get("detective")
    if needle.meters["found"] >= THRESHOLD and ("solved",) not in world.fired:
        world.fired.add(("solved",))
        detective.memes["pride"] += 1
        out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
    Rule("transform", "physical", _r_transform),
    Rule("solved", "social", _r_solved),
]


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


def tempting_choice(world: World, detective: Entity, temptation: Temptation, needle: Entity) -> None:
    detective.memes["temptation"] += 1
    world.say(
        f"At the little workshop, {detective.id} and the others were looking for the lost {needle.label}."
    )
    world.say(
        f"Then {detective.id} saw a tempting shortcut: {temptation.label}. "
        f'"Maybe I can use it for {temptation.wrong_use}," {detective.id} thought.'
    )


def clue_warning(world: World, helper: Entity, detective: Entity, needle: Entity) -> None:
    helper.memes["care"] += 1
    detective.memes["suspicion"] += 1
    world.say(
        f'{helper.id} frowned. "That would only hide the truth," {helper.pronoun()} said. '
        f'"A real clue should help us find the {needle.label}."'
    )


def search(world: World, detective: Entity, setting: Setting) -> None:
    detective.meters["searching"] += 1
    world.say(
        f"{detective.id} checked the desk, the floor, and the tiny space beside {setting.clue_spot}. "
        f"{setting.details}"
    )


def reveal(world: World, needle: Entity, solution: Solution, transformation: Transformation) -> None:
    needle.meters["lost"] += 1
    world.say(
        f"At last, {solution.label} gave the answer. {solution.method}."
    )
    world.say(
        f"Then the story changed shape: {transformation.prose}"
    )


def solve(world: World, detective: Entity, helper: Entity, needle: Entity,
          transformation: Transformation, solution: Solution) -> None:
    pin = world.get("pin")
    pin.meters["magnet_ready"] += 1
    needle.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.id} pointed to a magnet on the table. "{solution.proof}," {helper.pronoun()} said. '
        f'"We can use {transformation.tool} and bring the {needle.label} safely home."'
    )
    needle.meters["found"] += 1
    if needle.attrs.get("attached_to") == pin.id:
        world.say(
            f"The {needle.label} clicked right onto the pin cushion, as neat as a clue sliding into place."
        )


def finish(world: World, detective: Entity, helper: Entity, needle: Entity) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{detective.id} grinned. The lost {needle.label} was found, and the case was solved."
    )
    world.say(
        f"By the end, the tiny {needle.label} was no longer lost at all; it rested safely where everyone could see it."
    )


SETTINGS = {
    "workshop": Setting(
        "workshop",
        "the little workshop",
        "the workbench",
        "the clue shelf",
        "Light from the window made the screws, buttons, and thread sparkle like evidence."
    ),
    "sewing_room": Setting(
        "sewing_room",
        "the sewing room",
        "the sewing table",
        "the cloth basket",
        "A soft lamp glowed over the spools, and every shadow looked like it might hide a clue."
    ),
    "attic": Setting(
        "attic",
        "the attic",
        "the old trunk",
        "the dust-covered shelf",
        "The attic was quiet except for the creak of boards and the whisper of hanging cloth."
    ),
}

TEMPTATIONS = {
    "borrow_pins": Temptation("borrow_pins", "a handful of shiny pins", "hide the missing needle problem"),
    "fake_story": Temptation("fake_story", "a made-up story", "pretend the needle was never lost"),
    "rush_ahead": Temptation("rush_ahead", "the urge to rush ahead", "skip the careful search"),
}

NEEDLES = {
    "needle": ObjectNeedle("needle", "needle", "a small silver needle", "the sewing box"),
    "darning": ObjectNeedle("darning", "darning needle", "a strong darning needle", "the mending tin"),
    "gold": ObjectNeedle("gold", "gold needle", "a bright gold needle", "the velvet case"),
}

TRANSFORMATIONS = {
    "magnet": Transformation(
        "magnet",
        "magnet trick",
        "a magnet wrapped in cloth",
        "a safely found needle",
        "the magnet changed a loose metal needle from lost to found, as if the clue itself had come alive"
    ),
    "pin_cushion": Transformation(
        "pin_cushion",
        "pin-cushion plan",
        "a pin cushion",
        "a tidy resting place",
        "the needle transformed from a hidden problem into a tidy clue, tucked into the pin cushion where no one would lose it again"
    ),
}

SOLUTIONS = {
    "careful_search": Solution(
        "careful_search",
        "careful searching",
        "search every likely spot instead of guessing",
        "the clue was simple: look where the needle could have rolled",
        3,
    ),
    "magnet_help": Solution(
        "magnet_help",
        "the magnet clue",
        "use a magnet to pull the needle from under the shelf",
        "the needle could be drawn back without anyone poking a finger",
        4,
    ),
    "label_order": Solution(
        "label_order",
        "label the tools",
        "sort the tools and check the labels one by one",
        "a detective sorts evidence before making a guess",
        2,
    ),
}

NAMES = ["Mina", "Leo", "Ava", "Noah", "Ivy", "Eli", "Maya", "Theo"]
HELPER_NAMES = ["Mabel", "Jonah", "Ruby", "Owen", "Nia", "Cal"]
TRAITS = ["careful", "curious", "patient", "sharp-eyed", "brave"]


@dataclass
class StoryParams:
    setting: str
    temptation: str
    needle: str
    transformation: str
    solution: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TEMPTATIONS:
            for n in NEEDLES:
                if n == "needle":
                    combos.append((s, t, n))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.needle not in NEEDLES:
        raise StoryError("Unknown needle choice.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Unknown solution choice.")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation choice.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world about a temptingly wrong choice and a found needle."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--needle", choices=NEEDLES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if not combos:
        raise StoryError("No valid combinations available.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    temptation = args.temptation or rng.choice(sorted(TEMPTATIONS))
    needle = args.needle or "needle"
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    solution = args.solution or rng.choice(sorted(SOLUTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    detective = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting, temptation, needle, transformation, solution, detective, gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    needle = world.add(Entity(id="needle_obj", kind="thing", type="thing", label=NEEDLES[params.needle].label))
    pin = world.add(Entity(id="pin", kind="thing", type="tool", label="pin cushion"))
    world.add(Entity(id="desk", kind="thing", type="thing", label="desk"))
    world.facts.update(
        detective=detective,
        helper=helper,
        needle=needle,
        pin=pin,
        setting=SETTINGS[params.setting],
        temptation=TEMPTATIONS[params.temptation],
        transformation=TRANSFORMATIONS[params.transformation],
        solution=SOLUTIONS[params.solution],
    )
    tempting_choice(world, detective, TEMPTATIONS[params.temptation], needle)
    world.para()
    clue_warning(world, helper, detective, needle)
    search(world, detective, SETTINGS[params.setting])
    world.para()
    world.say("The case did not want to stay ordinary. It was time to solve it.")
    solve(world, detective, helper, needle, TRANSFORMATIONS[params.transformation], SOLUTIONS[params.solution])
    reveal(world, needle, SOLUTIONS[params.solution], TRANSFORMATIONS[params.transformation])
    finish(world, detective, helper, needle)
    world.facts["solved"] = needle.meters["found"] >= THRESHOLD
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "{f["temptation"].label.split()[0].lower()}" and the word "needle".',
        f"Tell a mystery story where {f['detective'].id} is tempted to take a shortcut, but instead solves the problem with help from {f['helper'].id}.",
        f"Write a story with a clue hunt, a transformation, and a happy ending where a needle is found safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    setting = f["setting"]
    temptation = f["temptation"]
    transformation = f["transformation"]
    solution = f["solution"]
    needle = f["needle"]
    return [
        ("Who is the story about?",
         f"It is about {det.id}, who acted like a little detective, and {helper.id}, who helped solve the mystery."),
        ("What was tempting?",
         f"{temptation.label.capitalize()} was tempting, but it would have hidden the real problem instead of solving it. "
         f"{det.id} had to resist the easy choice and keep looking for the {needle.label}."),
        ("How was the problem solved?",
         f"{solution.method.capitalize()}. That led to {transformation.prose}, which changed the lost needle into something safely found."),
        ("What changed by the end?",
         f"The {needle.label} was no longer lost. It had been transformed into a clue that could stay in the pin cushion, and the case was solved."),
    ]


KNOWLEDGE = {
    "needle": [("What is a needle?",
                "A needle is a very thin tool used for sewing. It is small and sharp, so people handle it carefully.")],
    "detective": [("What does a detective do?",
                   "A detective looks for clues and uses careful thinking to solve a mystery.")],
    "clue": [("What is a clue?",
              "A clue is a small piece of information that helps you figure something out.")],
    "magnet": [("What does a magnet do?",
                "A magnet can pull some metal objects closer to it without touching them.")],
    "pin_cushion": [("What is a pin cushion for?",
                     "A pin cushion holds pins or needles safely so they do not get lost.")],
    "problem_solve": [("What does it mean to solve a problem?",
                       "It means to figure out what to do and make the trouble go away.")],
}
KNOWLEDGE_ORDER = ["detective", "clue", "needle", "magnet", "pin_cushion", "problem_solve"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "clue", "needle", "magnet", "pin_cushion", "problem_solve"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
tempting(T) :- temptation(T).
lost(N) :- needle(N).
transformable(N) :- lost(N), pin_ready.
solved :- transformable(_), solution_good.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for nid in NEEDLES:
        lines.append(asp.fact("needle", nid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show tempting/1."))
    _ = asp.atoms(model, "tempting")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: empty story")
        return 1
    print("OK: ASP parsed and a normal story generated.")
    return 0


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def explain_rejection() -> str:
    return "(No story: this world only works when a real needle is lost and then found through detective work.)"


CURATED = [
    StoryParams("workshop", "borrow_pins", "needle", "magnet", "magnet_help", "Mina", "girl", "Mabel", "girl"),
    StoryParams("sewing_room", "fake_story", "needle", "pin_cushion", "careful_search", "Leo", "boy", "Jonah", "boy"),
    StoryParams("attic", "rush_ahead", "needle", "magnet", "label_order", "Ava", "girl", "Owen", "boy"),
]


def valid_story(params: StoryParams) -> bool:
    return params.needle == "needle"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.needle and args.needle != "needle":
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(sorted(SETTINGS))
    temptation = args.temptation or rng.choice(sorted(TEMPTATIONS))
    needle = "needle"
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    solution = args.solution or rng.choice(sorted(SOLUTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    detective = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting, temptation, needle, transformation, solution, detective, gender, helper, helper_gender)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate_default_sample() -> StorySample:
    return generate(CURATED[0])


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show tempting/1.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible story shapes are simple in this world: a real lost needle plus a detective solution.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} and {p.helper}: {p.setting}, {p.temptation}, {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
