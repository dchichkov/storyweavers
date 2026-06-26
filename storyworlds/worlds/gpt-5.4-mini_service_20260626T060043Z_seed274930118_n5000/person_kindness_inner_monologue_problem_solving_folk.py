#!/usr/bin/env python3
"""
A small folk-tale storyworld about a person, a problem, a kind choice,
and the quiet inner monologue that turns worry into helpful action.
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


@dataclass
class Person:
    id: str
    role: str
    kind: str = "person"
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Problem:
    id: str
    name: str
    trouble: str
    need: str
    solution_kind: str
    solution_action: str
    solved_image: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    hero: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "village": Setting(place="the village", detail="A little village sat between green hills and a winding brook."),
    "market": Setting(place="the market square", detail="The market square hummed with carts, bells, and baskets of apples."),
    "woods": Setting(place="the woods", detail="The woods were hushed, with mossy stones and birdsong in the branches."),
    "river": Setting(place="the riverbank", detail="The riverbank sparkled, and reeds leaned over the water like careful listeners."),
}

PROBLEMS = {
    "broken_cart": Problem(
        id="broken_cart",
        name="a broken cart wheel",
        trouble="the wheel had split and would not roll",
        need="some sturdy help to get the cart home",
        solution_kind="kindness",
        solution_action="mended the wheel with a wooden peg and a strip of cord",
        solved_image="the cart rolled again, soft as a sigh",
    ),
    "lost_lamb": Problem(
        id="lost_lamb",
        name="a lost lamb",
        trouble="the little lamb kept bleating at the edge of the path",
        need="a calm hand and a safe way back to the pen",
        solution_kind="kindness",
        solution_action="whistled softly, offered a crumb of bread, and walked slowly beside it",
        solved_image="the lamb tucked back near the pen and stopped trembling",
    ),
    "leaky_bucket": Problem(
        id="leaky_bucket",
        name="a leaky bucket",
        trouble="water dripped from a crack near the bottom",
        need="a way to carry water without losing most of it",
        solution_kind="problem_solving",
        solution_action="lined the crack with pine pitch and wrapped it with cloth",
        solved_image="the bucket held water like a small moon",
    ),
    "cold_soup": Problem(
        id="cold_soup",
        name="a cold soup pot",
        trouble="the soup had gone chilly before supper",
        need="a quick way to make it warm again",
        solution_kind="problem_solving",
        solution_action="set the pot by the fire and stirred in circles until it steamed",
        solved_image="the soup rose warm and fragrant, ready for bowls",
    ),
}

HEROES = ["Mara", "Ivo", "Nina", "Taro", "Lina", "Jon", "Sena", "Pavel"]
HELPERS = ["the old baker", "the miller", "the shepherd", "the potter", "the ferryman", "the gardener"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Person] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, person: Person) -> Person:
        self.entities[person.id] = person
        return person

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)

    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {problem}")

    return StoryParams(setting=setting, problem=problem, hero=hero, helper=helper)


def _inner_monologue(hero: str, problem: Problem) -> str:
    return {
        "kindness": f'"I should help," {hero} thought. "If I can ease this trouble, the day will grow brighter."',
        "problem_solving": f'"I can think of a clever way," {hero} thought. "Small steps can fix a big worry."',
    }[problem.solution_kind]


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Person(id=params.hero, role="hero", place=world.setting.place))
    helper = world.add(Person(id=params.helper, role="helper", place=world.setting.place))
    problem = PROBLEMS[params.problem]

    hero.memes["care"] = 1
    hero.memes["worry"] = 1

    world.say(world.setting.detail)
    world.say(
        f"In {world.setting.place}, {hero.id} saw {problem.name}; {problem.trouble}, and {problem.need}."
    )
    world.say(_inner_monologue(hero.id, problem))

    world.para()
    world.say(
        f"{hero.id} went to {helper.id} and spoke kindly, asking what could be done."
    )
    world.say(
        f"Together they {problem.solution_action}; that was the sort of work a kind heart could begin."
    )

    hero.memes["care"] = 2
    hero.memes["worry"] = 0
    hero.memes["satisfaction"] = 1
    helper.memes["gratitude"] = 1
    world.facts.update(
        hero=hero.id,
        helper=helper.id,
        problem=problem.id,
        problem_name=problem.name,
        setting=world.setting.place,
        solution_kind=problem.solution_kind,
        solved_image=problem.solved_image,
    )

    world.para()
    world.say(
        f"In the end, {problem.solved_image}, and {helper.id} thanked {hero.id} with a warm smile."
    )
    world.say(
        f"{hero.id} walked home with a lighter step, thinking that kindness can be its own kind of magic."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a person in {f["setting"]} who notices {f["problem_name"]} and chooses kindness.',
        f'Tell a gentle story where {f["hero"]} has an inner monologue about helping {f["helper"]} solve a problem.',
        f'Write a simple folk tale that ends with {f["hero"]} feeling glad after solving trouble with a kind act.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['hero']} notice in the story?",
            answer=f"{f['hero']} noticed {f['problem_name']} in {f['setting']}.",
        ),
        QAItem(
            question=f"What was {f['hero']}'s quiet thought before helping?",
            answer=f"{f['hero']} thought about helping and believed that kindness could make the day brighter.",
        ),
        QAItem(
            question=f"How did {f['hero']} solve the trouble with {f['helper']}?",
            answer=f"{f['hero']} and {f['helper']} worked together so the trouble could be fixed in a gentle, practical way.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The problem was solved, and {f['hero']} felt lighter and glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, care, or speak gently to another person.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your mind when you think to yourself.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving is thinking carefully and trying a useful way to fix a trouble.",
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
        bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_kind(hero).
helper_kind(helper).

kind_deeds(hero, kindness) :- care(hero), worries(hero), solves(hero).
solves(hero) :- helps(hero, helper), fixed(trouble).
"""

def asp_facts(params: StoryParams) -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", params.setting),
        asp.fact("problem", params.problem),
        asp.fact("hero", params.hero),
        asp.fact("helper", params.helper),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts(StoryParams('village','broken_cart','Mara','the old baker'))}\n{ASP_RULES}\n#show kind_deeds/2.\n#show solves/1.\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    shown = set((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model)
    expected = {("kind_deeds", ("hero", "kindness")), ("solves", ("hero",))}
    if shown == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python twin.")
    print("ASP:", sorted(shown))
    print("PY :", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    generate_story(world, params)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about kindness, inner monologue, and problem solving.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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


CURATED = [
    StoryParams("village", "broken_cart", "Mara", "the old baker"),
    StoryParams("market", "cold_soup", "Ivo", "the potter"),
    StoryParams("woods", "lost_lamb", "Nina", "the shepherd"),
    StoryParams("river", "leaky_bucket", "Lina", "the ferryman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print([str(s) for s in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
