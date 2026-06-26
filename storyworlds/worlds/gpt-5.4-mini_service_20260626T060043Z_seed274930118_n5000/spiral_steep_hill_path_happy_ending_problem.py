#!/usr/bin/env python3
"""
Standalone storyworld: a funny steep hill path tale with a spiral problem,
kindness, and a happy ending.

Premise:
A child and a helper are walking up a steep hill path that curls in a spiral.
A small practical problem blocks the way: a loose wheel, a runaway snack, a
tangled kite string, or a stuck cart.

Turn:
The problem gets worse when the path bends around and the item starts to slide,
roll, or wobble downhill.

Resolution:
They solve it together with a kind, concrete fix: sharing a rope, bracing a
cart, scooping spilled things, or making a safer plan.

The world is intentionally small and child-facing. State changes drive the
story text, QA, and verification.
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
# Core world entities
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class PathSetting:
    place: str = "the steep hill path"
    spiral: bool = True
    kind: str = "outdoor"


@dataclass
class Problem:
    id: str
    name: str
    verb: str
    state: str
    clue: str
    risk: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    use: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: PathSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "steep_hill_path": PathSetting(place="the steep hill path", spiral=True, kind="outdoor"),
}

PROBLEMS = {
    "snack_roll": Problem(
        id="snack_roll",
        name="runaway snack",
        verb="roll away",
        state="rolling",
        clue="The snack box bumped a stone and started to wobble downhill.",
        risk="the snacks would tumble into the ditch",
        solution="They sat the box in a shallow basket and held it steady with a ribbon.",
        tags={"roll", "snack", "spiral"},
    ),
    "kite_tangle": Problem(
        id="kite_tangle",
        name="tangled kite string",
        verb="tangle up",
        state="twisted",
        clue="The kite string wrapped once around a post and then once around itself.",
        risk="the kite would never get up the hill in one piece",
        solution="They unwound the string together, one careful loop at a time.",
        tags={"string", "kite", "spiral"},
    ),
    "cart_wobble": Problem(
        id="cart_wobble",
        name="wobbly cart wheel",
        verb="wobble",
        state="wobbly",
        clue="One cart wheel kept bumping the stones and making a silly clack-clack sound.",
        risk="the cart might tip and spill everything on the path",
        solution="They tightened the wheel and let the helper push from the lower side.",
        tags={"cart", "wheel", "spiral"},
    ),
    "apple_spill": Problem(
        id="apple_spill",
        name="spilled apples",
        verb="spill",
        state="scattered",
        clue="A basket of apples tipped and rolled in little red circles across the path.",
        risk="the apples would keep rolling downhill like happy marbles",
        solution="They laughed, picked up the apples, and built a steadier basket stack.",
        tags={"apple", "roll", "spiral"},
    ),
}

AIDS = {
    "ribbon": Aid(
        id="ribbon",
        label="a bright ribbon",
        use="tie the basket steady",
        helps="it keeps the snack box from slipping",
        tags={"snack", "steady"},
    ),
    "gloves": Aid(
        id="gloves",
        label="soft gloves",
        use="hold the string without poking fingers",
        helps="they make the string easier to untwist",
        tags={"string"},
    ),
    "wrench": Aid(
        id="wrench",
        label="a small wrench",
        use="tighten the wheel",
        helps="it stops the cart from wobbling",
        tags={"cart", "wheel"},
    ),
    "basket": Aid(
        id="basket",
        label="a shallow basket",
        use="catch the rolling apples",
        helps="it gives the apples a safe place to rest",
        tags={"apple", "roll"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Owen", "Nia", "Benny", "Iris", "Sam"]
HELPER_NAMES = ["Pip", "Jules", "Aunt Jo", "Mr. Pebble", "Nana", "Rae"]
TRAITS = ["cheerful", "curious", "silly", "brave", "gentle", "funny"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def setting_detail(setting: PathSetting) -> str:
    if setting.spiral:
        return "The path curled upward in a wide spiral, like a drawn snail shell."
    return "The path climbed sharply uphill."


def problem_at_risk(problem: Problem) -> bool:
    return True


def select_aid(problem: Problem) -> Optional[Aid]:
    for aid in AIDS.values():
        if problem.tags & aid.tags:
            return aid
    return None


def predict_problem(world: World, problem: Problem) -> bool:
    sim = world.copy()
    p = sim.facts["problem"]
    sim.facts["problem"] = p
    return True


def narrate_setup(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a {world.facts['trait']} {hero.type} who liked climbing {world.setting.place} "
        f"because the path made a funny spiral turn."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.id} were carrying {problem.name}, and everybody "
        f"thought it looked easy until the hill joined the joke."
    )


def narrate_problem(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(setting_detail(world.setting))
    world.say(problem.clue)
    world.say(
        f"Then the {problem.name} started to {problem.verb}, and {hero.pronoun('possessive')} "
        f"{helper.label_word} made a face as if the hill had just told a pun."
    )


def narrate_kindness(world: World, hero: Entity, helper: Entity, aid: Aid, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{helper.id} said, \"No worries. We'll fix it together,\" and handed over {aid.label}."
    )
    world.say(
        f"{hero.id} nodded, and both of them used {aid.label} to {aid.use}."
    )


def narrate_resolution(world: World, hero: Entity, helper: Entity, aid: Aid, problem: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"That worked right away, because {aid.helps}. Soon the path was calm again."
    )
    world.say(
        f"{problem.solution} After that, {hero.id} and {helper.id} kept climbing, laughing at the bouncy little mess."
    )
    world.say(
        f"At the top of the spiral hill, everything stayed in place, and the day ended with a grin."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[params.trait, "little"],
        memes={"joy": 0, "worry": 0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        memes={"kindness": 0, "joy": 0},
    ))
    world.facts.update(problem=problem, trait=params.trait, hero=hero, helper=helper)

    narrate_setup(world, hero, helper, problem)
    world.para()
    narrate_problem(world, hero, helper, problem)
    aid = select_aid(problem)
    if aid is None:
        raise StoryError("No kind, problem-solving aid fits this spiral-hill problem.")
    world.facts["aid"] = aid
    world.para()
    narrate_kindness(world, hero, helper, aid, problem)
    narrate_resolution(world, hero, helper, aid, problem)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        "Write a funny short story about a steep hill path with a spiral bend, a small problem, and a kind fix.",
        f"Tell a comedy story where {hero.id} and {helper.id} solve {p.name} together on a steep hill path.",
        f"Write a child-friendly story that includes a spiral path, kindness, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Problem = world.facts["problem"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    aid: Aid = world.facts["aid"]
    return [
        QAItem(
            question=f"Where were {hero.id} and {helper.id} walking?",
            answer=f"They were walking on the steep hill path, which curled upward in a spiral.",
        ),
        QAItem(
            question=f"What problem made the walk tricky?",
            answer=f"The story's problem was {p.name}. It began to {p.verb}, which made the hill feel extra wobbly and funny.",
        ),
        QAItem(
            question=f"How did they solve the problem kindly?",
            answer=f"They used {aid.label} together and fixed the problem by working side by side.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} and {helper.id} laughing at the top of the hill after the problem was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spiral?",
            answer="A spiral is a shape that turns around and around while moving outward or inward.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping someone, being gentle, and making things easier for them.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a way to fix a trouble or make it better.",
        ),
        QAItem(
            question="Why can a steep hill path be hard to walk on?",
            answer="A steep hill path can be hard because your feet must work harder to climb upward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

valid_story(P, Problem, Aid) :-
    setting(P),
    problem(Problem),
    aid(Aid),
    needs(Problem, Need),
    helps(Aid, Need),
    on_hill(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("on_hill", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, next(iter(sorted(p.tags))) if p.tags else "general"))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for tag in sorted(aid.tags):
            lines.append(asp.fact("helps", aid.id, tag))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for pid, p in PROBLEMS.items():
        aid = select_aid(p)
        if aid is not None:
            out.append(("steep_hill_path", pid, aid.id))
    return sorted(out)


def asp_verify() -> int:
    import asp
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld on a steep hill path with a spiral turn."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    place = args.place or "steep_hill_path"
    problem = args.problem or rng.choice(list(PROBLEMS.keys()))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    return StoryParams(
        place=place,
        problem=problem,
        hero_name=hero_name,
        hero_type=hero_gender,
        helper_name=helper_name,
        helper_type=helper_gender,
        trait=trait,
    )


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


CURATED = [
    StoryParams("steep_hill_path", "snack_roll", "Mina", "girl", "Pip", "boy", "cheerful"),
    StoryParams("steep_hill_path", "kite_tangle", "Toby", "boy", "Aunt Jo", "girl", "funny"),
    StoryParams("steep_hill_path", "cart_wobble", "Lena", "girl", "Mr. Pebble", "boy", "curious"),
    StoryParams("steep_hill_path", "apple_spill", "Owen", "boy", "Nana", "girl", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
