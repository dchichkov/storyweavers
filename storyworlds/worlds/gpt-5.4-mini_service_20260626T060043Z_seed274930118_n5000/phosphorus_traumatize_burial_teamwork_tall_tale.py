#!/usr/bin/env python3
"""
storyworlds/worlds/phosphorus_traumatize_burial_teamwork_tall_tale.py
=====================================================================

A tall-tale storyworld about a glowing phosphorus trouble, a frightened beast,
and a teamwork fix: bury the thing before it traumatizes the whole camp.

Seed tale sketch:
---
On the prairie, Aunt Mabel had a little phosphorus lantern that shone like a
captured star. Mose the mule was brave about storms, thunder, and rattling pots,
but that phosphorus glow made him skitter and snort so hard the fence boards
wobbled.

So Mabel called for help. Gus fetched the shovel, Junie brought a bucket of
river clay, and together they buried the lantern deep in a safe pit behind the
cottonwoods. The mule settled, the night softened, and the whole camp agreed
that teamwork can tame even the brightest trouble.

Causal state updates:
---
    phosphorus glow near a vulnerable beast   -> beast.fear += 1 ; beast.memes["traumatized"] += 1
    teamwork + burial tools + safe ground     -> object.hidden += 1 ; fear drops ; calm rises
    helper work on a hard job                 -> helper.memes["pride"] += 1 ; hero.memes["relief"] += 1
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "animal"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "aunt", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "uncle", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    ground: str
    affords_burial: bool = True


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    glow: str
    threat: str
    risk_meter: str
    zone: str = "nearby"
    tags: set[str] = field(default_factory=set)


@dataclass
class Burier:
    id: str
    label: str
    tool: str
    method: str
    finish: str
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


SETTINGS = {
    "prairie": Setting(place="the prairie", ground="loamy earth"),
    "canyon": Setting(place="the canyon rim", ground="red dirt"),
    "riverbank": Setting(place="the riverbank", ground="soft mud"),
    "orchard": Setting(place="the orchard", ground="packed soil"),
}

PROBLEMS = {
    "lantern": Problem(
        id="lantern",
        label="lantern",
        phrase="a little phosphorus lantern",
        glow="phosphorus-bright",
        threat="traumatize",
        risk_meter="fear",
        tags={"phosphorus", "glow"},
    ),
    "rock": Problem(
        id="rock",
        label="rock",
        phrase="a phosphorus rock",
        glow="ghost-bright",
        threat="traumatize",
        risk_meter="fear",
        tags={"phosphorus"},
    ),
}

BURIERS = {
    "teamwork": Burier(
        id="teamwork",
        label="teamwork",
        tool="shovel",
        method="buried",
        finish="covered it over with dirt and a flat stone",
        tags={"teamwork", "burial"},
    ),
}

HEROES = [
    ("Aunt Mabel", "aunt"),
    ("Uncle Gus", "uncle"),
    ("Junie", "girl"),
    ("Ned", "boy"),
]

HELPERS = [
    ("Mose", "mule"),
    ("Old Bess", "horse"),
    ("Ruff", "dog"),
]

TRAITS = ["steady", "brave", "hush-voiced", "lively"]


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld of phosphorus, burial, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
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


def _hero_type(name: str) -> str:
    for n, t in HEROES:
        if n == name:
            return t
    return "person"


def _helper_type(name: str) -> str:
    for n, t in HELPERS:
        if n == name:
            return t
    return "animal"


def _capital(name: str) -> str:
    return name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or rng.choice([h for h, _ in HELPERS])
    if hero == helper:
        raise StoryError("Hero and helper must be different characters.")
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, hero=hero, helper=helper, trait=trait)


def _do_burial(world: World, problem: Entity, hero: Entity, helper: Entity) -> None:
    problem.meters["exposed"] = 0
    problem.meters["buried"] = 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    if helper.kind == "animal":
        helper.memes["calm"] = helper.memes.get("calm", 0) + 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero_type = _hero_type(params.hero)
    helper_type = _helper_type(params.helper)
    problem_cfg = PROBLEMS[params.problem]

    hero = world.add(Entity(id=params.hero, kind="character", type=hero_type))
    helper = world.add(Entity(id=params.helper, kind="animal" if helper_type in {"mule", "horse", "dog"} else "character", type=helper_type))
    problem = world.add(Entity(
        id=problem_cfg.id,
        kind="thing",
        type=problem_cfg.label,
        label=problem_cfg.label,
        phrase=problem_cfg.phrase,
        meters={"glow": 1.0, "exposed": 1.0},
        memes={"fear": 0.0, "traumatized": 0.0},
    ))

    # Act 1
    world.say(
        f"Out on {world.setting.place}, {hero.id} was a {params.trait} old soul who loved a good job done right."
    )
    world.say(
        f"One evening, {hero.id} found {problem.phrase}, and it glowed {problem_cfg.glow} like a jar of captured lightning."
    )
    world.say(
        f"{helper.id} was nearby, but that phosphorus shine made {helper.id} skitter and snort; it could even {problem_cfg.threat} a beast with a tender heart."
    )

    # Act 2
    world.para()
    world.say(
        f"{hero.id} whistled up a helper and called for {params.helper.lower()}-strong {BURIERS['teamwork'].label}."
    )
    world.say(
        f"Together, they got a shovel, chose the {world.setting.ground}, and made a safe pit behind a low hill."
    )
    world.say(
        f"{hero.id} said the glow had to be put away before it could {problem_cfg.threat} anybody else."
    )

    # Act 3
    world.para()
    _do_burial(world, problem, hero, helper)
    world.say(
        f"Then, with true teamwork, they {BURIERS['teamwork'].method} the {problem.label}, {BURIERS['teamwork'].finish}."
    )
    world.say(
        f"The bright trouble vanished under the earth, and {helper.id} settled down so calm the night seemed to breathe easier."
    )
    world.say(
        f"{hero.id} tipped {hero.pronoun('possessive')} hat and grinned, because the biggest fix in town had been a whole lot of teamwork."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "problem": problem,
        "setting": world.setting,
        "params": params,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    setting = f["setting"]
    return [
        f"Write a tall tale about {hero.id} on {setting.place} where a phosphorus glow must be buried with teamwork.",
        f"Tell a child-friendly story in which {helper.id} gets frightened and {hero.id} solves the problem by burial.",
        f"Make a brief tall tale that uses the words phosphorus, traumatize, and burial, and ends with teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Why did {helper.id} get upset when {hero.id} found the {problem.label}?",
            answer=(
                f"{helper.id} got scared because the {problem.phrase} glowed phosphorus-bright, "
                f"and that kind of shine could traumatize a gentle animal."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do to fix the trouble on {setting.place}?",
            answer=(
                f"They used teamwork, dug a safe pit, and carried out a burial so the glowing thing would stay out of sight."
            ),
        ),
        QAItem(
            question=f"What happened after the {problem.label} was buried?",
            answer=(
                f"The bright glow disappeared under the earth, {helper.id} calmed down, and {hero.id} felt relieved."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is phosphorus in a story like this?",
            answer="Phosphorus is a substance that can glow, so it can seem bright and strange in the dark.",
        ),
        QAItem(
            question="What does burial mean?",
            answer="Burial means putting something under the ground, usually to hide it or to lay it to rest.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or helpers work together to get a hard job done.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(Place, Problem, Helper) :- setting(Place), problem(Problem), helper(Helper), different(Problem, Helper), needs_burial(Problem), teamwork_fix(Problem, Helper).
different(A,B) :- A != B.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
        lines.append(asp.fact("needs_burial", pr))
    for h, _ in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("teamwork_fix", "lantern", "Mose"))
    lines.append(asp.fact("teamwork_fix", "rock", "Mose"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for problem in PROBLEMS:
            for helper in HELPERS:
                if helper[0] != "Mose":
                    continue
                combos.append((place, problem, helper[0]))
    return combos


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def _rejection_reason(place: str, problem: str, helper: str) -> str:
    return (
        f"(No story: {problem} is a good candidate for burial, but only Mose is written as the helper who can do the heavy teamwork cleanly in {place}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.helper != "Mose":
        raise StoryError(_rejection_reason(args.place or "the setting", args.problem or "the problem", args.helper))
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or "Mose"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, hero=hero, helper=helper, trait=trait)


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


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

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, helper) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="prairie", problem="lantern", hero="Aunt Mabel", helper="Mose", trait="steady"),
            StoryParams(place="canyon", problem="rock", hero="Junie", helper="Mose", trait="lively"),
            StoryParams(place="riverbank", problem="lantern", hero="Uncle Gus", helper="Mose", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
