#!/usr/bin/env python3
"""
Fairy-tale story world: an ass, a china portrait, and repeated attempts to solve
a fragile problem.

Seed tale premise:
- A kind little ass carries a painted china portrait for a queen.
- The portrait is precious and brittle.
- The ass must cross a small bridge and reach a sunny hall without cracking it.
- Each failed attempt teaches a better way: first haste, then padding, then a careful solve.

The world supports:
- repetition as a narrative instrument,
- problem solving as the resolution engine,
- physical meters and emotional memes on all entities,
- a Python reasonableness gate with an inline ASP twin.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fragile": 0.0, "safe": 0.0, "travel": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "woman", "princess"}
        male = {"boy", "king", "man", "prince", "ass", "donkey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the royal lane"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    repeated: str
    stumble: str
    danger: str
    fix_hint: str
    route: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    action: str
    protects: set[str]
    safe_with: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the royal lane", affords={"carry"}),
    "bridge": Setting(place="the little bridge", affords={"carry"}),
    "hall": Setting(place="the castle hall", affords={"carry"}),
}

CHALLENGES = {
    "portrait_run": Challenge(
        id="portrait_run",
        verb="carry the china portrait",
        repeated="carry the china portrait again",
        stumble="the painted frame wobbled",
        danger="the china portrait could crack",
        fix_hint="find a softer, steadier way",
        route="cross the lane and bridge",
        tags={"china", "portrait", "repetition"},
    ),
}

SOLUTIONS = [
    Solution(
        id="straw_wrap",
        label="a bundle of straw",
        phrase="a soft bundle of straw",
        action="wrap the portrait in straw",
        protects={"fragile"},
        safe_with={"carry"},
    ),
    Solution(
        id="cloth_wrap",
        label="a linen cloth",
        phrase="a clean linen cloth",
        action="wrap the portrait in linen",
        protects={"fragile"},
        safe_with={"carry"},
    ),
    Solution(
        id="slow_steps",
        label="slow steps",
        phrase="slow careful steps",
        action="walk slowly and hold the frame with two hands",
        protects={"travel"},
        safe_with={"carry"},
    ),
]

# Must include ass, china, portrait words.
GIRL_NAMES = ["Mira", "Lena", "Clara", "Nina"]
BOY_NAMES = ["Robin", "Tomas", "Elias", "Hugo"]
ASS_NAMES = ["Bray", "Merry", "Buckle", "Patch"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CHALLENGES]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def can_solve(world: World, solution: Solution) -> bool:
    return "fragile" in solution.protects or "travel" in solution.protects


def choose_solution(world: World) -> Optional[Solution]:
    for sol in SOLUTIONS:
        if can_solve(world, sol):
            return sol
    return None


def narrate_attempt(world: World, hero: Entity, portrait: Entity, challenge: Challenge, attempt: int) -> None:
    if attempt == 1:
        world.say(
            f"Once in the morning, {hero.id} tried to {challenge.verb} as the bells rang softly."
        )
        world.say(
            f"But on the first try, {challenge.stumble}, and everyone feared that {portrait.label} would crack."
        )
        hero.memes["worry"] += 1
        portrait.meters["fragile"] += 1
    elif attempt == 2:
        world.say(
            f"Then {hero.id} tried again, because {hero.pronoun()} did not want to give up."
        )
        world.say(
            f"On the second try, {challenge.stumble} once more, and {hero.id} learned that haste was the wrong road."
        )
        hero.memes["worry"] += 1
        hero.memes["hope"] += 1
        portrait.meters["fragile"] += 1
    else:
        world.say(
            f"At last, {hero.id} paused and chose to {challenge.fix_hint}."
        )


def apply_solution(world: World, hero: Entity, portrait: Entity, solution: Solution) -> None:
    hero.meters["work"] += 1
    hero.memes["hope"] += 1
    hero.memes["joy"] += 1
    portrait.meters["safe"] += 1
    world.say(
        f"So {hero.id} found {solution.phrase} and chose to {solution.action}."
    )
    world.say(
        f"This time, the china portrait stayed safe, and {hero.id} carried {portrait.item_pronoun()} all the way to the hall."
    )
    hero.memes["pride"] += 1


def tell(setting: Setting, challenge: Challenge, hero_name: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type="ass", label="the ass"))
    queen = world.add(Entity(id="Queen", kind="character", type="queen", label="the queen"))
    portrait = world.add(
        Entity(
            id="Portrait",
            type="thing",
            label="the china portrait",
            phrase="a delicate china portrait",
            owner=queen.id,
            caretaker=queen.id,
        )
    )

    world.say(
        f"Long ago, {hero.id} was a gentle ass who loved to help in the royal lane."
    )
    world.say(
        f"{hero.id} was given {portrait.phrase}, because the queen wanted it hung in her sunny hall."
    )
    world.say(
        f"The portrait was beautiful, but it was also china, so everyone knew it must be carried with care."
    )
    world.para()

    narrate_attempt(world, hero, portrait, challenge, 1)
    world.para()
    narrate_attempt(world, hero, portrait, challenge, 2)
    world.para()

    solution = choose_solution(world)
    if solution is None:
        raise StoryError("(No story: the problem has no gentle solution.)")

    narrate_attempt(world, hero, portrait, challenge, 3)
    apply_solution(world, hero, portrait, solution)

    world.say(
        f"By evening, {hero.id} smiled beside the queen, and the china portrait shone on the wall like a little moon."
    )

    world.facts.update(
        hero=hero,
        queen=queen,
        portrait=portrait,
        challenge=challenge,
        solution=solution,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    return [
        'Write a short fairy tale about an ass, a china portrait, and a problem that takes more than one try to solve.',
        f"Tell a gentle story where {hero.id}, a kind ass, must {challenge.verb} without breaking it.",
        'Write a fairy tale that repeats the mistake, then shows a smarter solution for the fragile portrait.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    queen: Entity = f["queen"]
    portrait: Entity = f["portrait"]
    challenge: Challenge = f["challenge"]
    solution: Solution = f["solution"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a kind ass who wanted to help the queen with the china portrait.",
        ),
        QAItem(
            question=f"What was the problem with the portrait?",
            answer=f"The problem was that the china portrait was fragile, so it could crack if {hero.id} rushed or bumped it.",
        ),
        QAItem(
            question=f"What changed after the repeated tries?",
            answer=f"After trying again and again, {hero.id} stopped rushing and used {solution.label} to solve the problem safely.",
        ),
        QAItem(
            question=f"Why did the queen need care with the portrait?",
            answer=f"The queen needed care because the portrait was made of china and was precious, so it had to reach the hall without damage.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} carrying {portrait.label} safely to the hall, while the queen smiled at the finished job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is china?",
            answer="China is a hard, smooth material often used for cups, plates, and pretty things that can break if dropped.",
        ),
        QAItem(
            question="What is a portrait?",
            answer="A portrait is a picture of a person, often made to help people remember their face.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when a story repeats a sound, action, or try more than once so it feels rhythmic and clear.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means trying to understand what is wrong and then choosing a better way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(P) :- portrait(P), fragile(P).
needs_fix(P) :- at_risk(P), solution(S), protects(S, fragile).
valid_story(Place, C) :- setting(Place), challenge(C), at_risk(P), needs_fix(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    lines.append(asp.fact("portrait", "Portrait"))
    lines.append(asp.fact("fragile", "Portrait"))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol.id))
        for p in sol.protects:
            lines.append(asp.fact("protects", sol.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show at_risk/1."))
    asp_set = set(asp.atoms(model, "at_risk"))
    py_set = {("Portrait",)} if valid_combos() else set()
    if asp_set == py_set:
        print("OK: ASP and Python parity holds.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world: an ass, a china portrait, and repeated problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.challenge:
        combos = [c for c in combos if c[1] == args.challenge]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge = rng.choice(combos)
    name = args.name or rng.choice(ASS_NAMES)
    return StoryParams(place=place, challenge=challenge, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], params.name)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show at_risk/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show at_risk/1."))
        print("ASP at_risk:", sorted(asp.atoms(model, "at_risk")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, challenge in valid_combos():
            p = StoryParams(place=place, challenge=challenge, name="Bray")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
