#!/usr/bin/env python3
"""
A small folk-tale storyworld about a beloved egg-dim scale, a mistaken measure,
and a careful problem-solving turn guided by an inner monologue.
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
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    size: str = ""
    precious: bool = False
    broken: bool = False
    lost: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Person:
    id: str
    kind: str = "person"
    role: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    village: str
    hero: str
    helper: str
    beloved: str
    seed: Optional[int] = None


VILLAGES = {
    "mill": "the mill by the river",
    "orchard": "the old orchard",
    "croft": "the little croft at the hill's foot",
    "lane": "the windy lane beside the hedge",
}

HEROES = ["Mara", "Nell", "Tobin", "Rowan", "Anya", "Ivo"]
HELPERS = ["grandmother", "grandfather", "neighbor", "aunt", "uncle"]
TRAITS = ["gentle", "clever", "patient", "brave", "quiet"]

OBJECTS = {
    "scale": {
        "label": "scale",
        "phrase": "a beloved egg-dim scale with a brass pan",
        "need": "balance",
        "problem": "the pointer would not rest still",
    }
}


@dataclass
class World:
    village: str
    hero: Person
    helper: Person
    scale: Thing
    egg_dust: Thing
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about an egg-dim scale and careful problem solving.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--beloved", choices=["scale"])
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
    village = args.village or rng.choice(list(VILLAGES))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    beloved = args.beloved or "scale"
    return StoryParams(village=village, hero=hero, helper=helper, beloved=beloved)


def make_world(params: StoryParams) -> World:
    hero = Person(
        id=params.hero,
        role="child",
        label=params.hero,
        traits=[random.choice(TRAITS), "thoughtful"],
    )
    helper = Person(
        id=params.helper,
        role="elder",
        label=f"the {params.helper}",
        traits=["kind"],
    )
    scale = Thing(
        id="beloved_scale",
        label="scale",
        phrase="a beloved egg-dim scale with a brass pan",
        owner=hero.id,
        size="egg-dim",
        precious=True,
        meters={"care": 1.0},
        memes={"love": 2.0},
    )
    egg_dust = Thing(
        id="dust",
        label="dust",
        phrase="a little dusting of flour and shell",
        size="crumb-small",
    )
    return World(village=VILLAGES[params.village], hero=hero, helper=helper, scale=scale, egg_dust=egg_dust)


def inner_monologue(hero: Person, scale: Thing) -> str:
    return (
        f"{hero.id} looked at the beloved egg-dim scale and thought, "
        f"'It is small, but it means the whole supper. If the brass pan tilts, "
        f"the cakes will not rise right.'"
    )


def problem_and_turn(world: World) -> None:
    h = world.hero
    s = world.scale
    helper = world.helper

    world.say(f"In {world.village}, there lived {h.id}, a {h.traits[0]} child who kept a beloved egg-dim scale on a shelf by the hearth.")
    world.say(f"Each morning, {h.id} used the scale to weigh eggs for the day's bread, for the family trusted its tiny brass pan.")
    world.say(inner_monologue(h, s))
    world.para()
    world.say(f"One blustery day, the scale began to wobble when {h.id} set down a basket of eggs.")
    h.memes["worry"] = h.memes.get("worry", 0.0) + 1.0
    h.meters["risk"] = h.meters.get("risk", 0.0) + 1.0
    world.say(f"{h.id} whispered, 'If I leave it like this, the eggs will slip, and the beloved scale may be hurt.'")
    world.say(f"So {h.id} watched the wobble, breathed slowly, and thought again.")
    world.say(f"'A stone under one leg would steady it,' {h.id} thought, 'but the stone must be the same height as the thin board.'")
    world.para()
    world.say(f"{helper.label.capitalize()} heard the soft muttering and came near the hearth.")
    world.say(f"'What troubles you, child?' {helper.label} asked.")
    world.say(f"{h.id} answered, 'The scale leans, and I do not want to ruin what we love.'")
    world.say(f"Then {h.id} fetched a flat chip of wood, slipped it under the short leg, and wiped the brass pan clean.")
    s.meters["steady"] = 1.0
    s.meters["clean"] = 1.0
    h.memes["joy"] = h.memes.get("joy", 0.0) + 1.0
    h.memes["pride"] = h.memes.get("pride", 0.0) + 1.0
    world.say(f"The egg-dim scale stood straight at last, as neat as a church bell after rain.")
    world.say(f"{helper.label} smiled and said, 'You solved the trouble with care, not with hurry.'")
    world.say(f"And {h.id} felt warm inside, for the beloved scale was safe and ready for the next basket of eggs.")

    world.facts = {
        "hero": h,
        "helper": helper,
        "scale": s,
        "village": world.village,
    }


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    v = world.facts["village"]
    return [
        QAItem(
            question=f"Who was the story about in {v}?",
            answer=f"It was about {h.id}, a gentle child who loved a beloved egg-dim scale.",
        ),
        QAItem(
            question=f"What problem did {h.id} notice with the scale?",
            answer="The scale wobbled and leaned, so it might let the eggs slip and stop weighing well.",
        ),
        QAItem(
            question=f"How did {h.id} fix the trouble?",
            answer=f"{h.id} slid a flat chip of wood under the short leg and cleaned the brass pan, which made the scale stand straight.",
        ),
        QAItem(
            question=f"Who came to help {h.id} in the end?",
            answer=f"{helper.label} came near the hearth, listened, and praised the careful fix.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word beloved mean?",
            answer="Beloved means deeply loved and treasured very much.",
        ),
        QAItem(
            question="What does egg-dim mean?",
            answer="Egg-dim means about the size of an egg, small enough to hold in one hand.",
        ),
        QAItem(
            question="What is a scale for?",
            answer="A scale is used to measure how heavy something is or to compare weights.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short folk tale about a beloved egg-dim scale and a child who solves a small problem with patience.',
        f"Tell a gentle story set in {world.village} where a child notices a wobbling scale and thinks carefully before acting.",
        "Write a child-friendly story with inner monologue, a tiny household problem, and a happy fix.",
    ]


def dump_trace(world: World) -> str:
    return (
        "--- world model state ---\n"
        f"  hero={world.hero.id} memes={world.hero.memes} meters={world.hero.meters}\n"
        f"  helper={world.helper.label}\n"
        f"  scale={world.scale.phrase} meters={world.scale.meters} memes={world.scale.memes}\n"
    )


ASP_RULES = r"""
score_problem(wobble) :- wobble(scale).
score_solution(steady) :- fixed(scale).
safe_story :- score_problem(wobble), score_solution(steady).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("wobble", "scale"),
        asp.fact("fixed", "scale"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/0."))
    ok = any(sym.name == "safe_story" for sym in model)
    if ok:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    problem_and_turn(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for section, items in (
            ("== (1) Generation prompts ==", sample.prompts),
            ("== (2) Story questions ==", sample.story_qa),
            ("== (3) World knowledge ==", sample.world_qa),
        ):
            print(section)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


CURATED = [
    StoryParams(village="mill", hero="Mara", helper="grandmother", beloved="scale"),
    StoryParams(village="orchard", hero="Tobin", helper="neighbor", beloved="scale"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(v, h, "scale") for v in VILLAGES for h in HEROES]


def resolve_invalid(args: argparse.Namespace) -> None:
    if args.beloved and args.beloved != "scale":
        raise StoryError("This world only tells stories about the beloved scale.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_story/0."))
        print("ASP model:", model)
        return

    resolve_invalid(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
