#!/usr/bin/env python3
"""
Tall Tale story world: a pocket-sized kernel, a sharing problem, and a clever fix.

A small, self-contained story simulation about a child who finds one kernel in a
pocket, wants to share, runs into a problem, and solves it in a fanciful but
grounded way. The story is driven by world state: who owns what, what fits in
the pocket, what gets shared, and how the problem changes the ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "they" if self.plural else "it"
        if case == "object":
            return "them" if self.plural else "it"
        return "their" if self.plural else "its"

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Character:
    id: str
    name: str
    kind: str = "character"
    type: str = "child"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    pocket: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the dusty lane"
    sky: str = "bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    kernel_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _capital(s: str) -> str:
    return s[:1].upper() + s[1:]


def character_intro(world: World, hero: Character, sidekick: Character) -> None:
    world.say(
        f"{hero.name} was a tall-tale child with a pocket that seemed as deep as a well, "
        f"and {sidekick.name} was the kind of friend who could laugh at a shadow and still help carry a bucket."
    )


def find_kernel(world: World, hero: Character, kernel: Item) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.pocket.append(kernel.id)
    kernel.carried_by = hero.id
    kernel.location = "pocket"
    world.say(
        f"One day, {hero.name} found a single {kernel.label} in {hero.pronoun('possessive')} pocket, "
        f"shining like a tiny moon in a brown canyon."
    )


def want_to_share(world: World, hero: Character, sidekick: Character, kernel: Item) -> None:
    hero.memes["share"] = hero.memes.get("share", 0) + 1
    world.say(
        f"{hero.name} wanted to share the {kernel.label} with {sidekick.name}, "
        f"because a good surprise feels bigger when two friends can hold the same grin."
    )


def problem_arises(world: World, hero: Character, sidekick: Character, kernel: Item) -> None:
    kernel.meters["hardness"] = kernel.meters.get("hardness", 0) + 1
    hero.memes["trouble"] = hero.memes.get("trouble", 0) + 1
    world.say(
        f"But the {kernel.label} was too hard to eat as it was, and there was no fire, no pan, and not a speck of steam in sight."
    )
    world.say(
        f"{hero.name} and {sidekick.name} looked at the little speck and knew they needed a clever trick."
    )


def problem_solve(world: World, hero: Character, sidekick: Character, kernel: Item) -> None:
    kernel.meters["split"] = kernel.meters.get("split", 0) + 1
    kernel.memes["shared"] = kernel.memes.get("shared", 0) + 1
    world.facts["solved"] = True
    world.say(
        f"{sidekick.name} tapped the side of an old tin cup, and {hero.name} rolled the {kernel.label} between two smooth stones."
    )
    world.say(
        f"With a tiny pop of imagination, they split the {kernel.label} into two buttery halves, "
        f"and each friend got an equal piece."
    )


def ending(world: World, hero: Character, sidekick: Character, kernel: Item) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0) + 1
    world.say(
        f"By sunset, the pocket was empty, the problem was solved, and {hero.name} and {sidekick.name} were smiling as if they had found a feast in a thimble."
    )
    world.say(
        f"Their laughter went down the lane like wagon wheels on a hill, and even the {kernel.label}'s tiny crumbs seemed proud to have been shared."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Character(id="hero", name=params.hero, traits=["curious", "generous"]))
    sidekick = world.add(Character(id="sidekick", name=params.sidekick, traits=["bright", "helpful"]))
    kernel = world.add(Item(id="kernel", label=params.kernel_kind))

    character_intro(world, hero, sidekick)
    world.para()
    find_kernel(world, hero, kernel)
    want_to_share(world, hero, sidekick, kernel)
    world.para()
    problem_arises(world, hero, sidekick, kernel)
    problem_solve(world, hero, sidekick, kernel)
    world.para()
    ending(world, hero, sidekick, kernel)

    world.facts.update(hero=hero, sidekick=sidekick, kernel=kernel, setting=setting)
    return world


SETTINGS = {
    "lane": Setting(place="the dusty lane", sky="bright", affords={"sharing", "problem_solving"}),
    "barn": Setting(place="the old red barn", sky="golden", affords={"sharing", "problem_solving"}),
    "meadow": Setting(place="the wide meadow", sky="windy", affords={"sharing", "problem_solving"}),
}

KERNELS = {
    "popcorn kernel": "popcorn kernel",
    "golden kernel": "golden kernel",
    "bean kernel": "bean kernel",
}

HERO_NAMES = ["Milo", "Nina", "Jo", "Teddy", "Luz", "June", "Otis", "Penny"]
SIDEKICK_NAMES = ["Bess", "Rory", "Willa", "Pip", "Hank", "Mira", "Sol", "Bea"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, kernel) for place in SETTINGS for kernel in KERNELS]


def explain_rejection(place: str, kernel: str) -> str:
    return f"(No story: {kernel} at {place} would not give this tall-tale a clear sharing problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a kernel in a pocket, sharing, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kernel", choices=KERNELS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if args.place or args.kernel:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.kernel is None or c[1] == args.kernel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, kernel = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(place=place, hero=hero, sidekick=sidekick, kernel_kind=kernel)


ASP_RULES = r"""
place(lane). place(barn). place(meadow).
kernel(popcorn_kernel). kernel(golden_kernel). kernel(bean_kernel).
valid(P,K) :- place(P), kernel(K).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", p) for p in SETTINGS] + [asp.fact("kernel", k) for k in KERNELS])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    sidekick: Character = f["sidekick"]
    kernel: Item = f["kernel"]
    return [
        f'Write a tall tale for children about {hero.name} finding a {kernel.label} in a pocket and sharing it with {sidekick.name}.',
        f"Tell a problem-solving story where {hero.name} and {sidekick.name} cannot eat a {kernel.label} at once, so they need a clever fix.",
        f'Write a short story that includes the words "kernel" and "pocket" and ends with two friends sharing something tiny.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    sidekick: Character = f["sidekick"]
    kernel: Item = f["kernel"]
    place: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.name} find in {hero.pronoun('possessive')} pocket?",
            answer=f"{hero.name} found a {kernel.label} in {hero.pronoun('possessive')} pocket.",
        ),
        QAItem(
            question=f"Why did {hero.name} and {sidekick.name} need a problem solved?",
            answer=f"They wanted to share the {kernel.label}, but it was too hard to eat the way it was.",
        ),
        QAItem(
            question=f"How did {hero.name} and {sidekick.name} solve the problem at {place.place}?",
            answer=f"They used a clever trick with a tin cup and smooth stones, then split the {kernel.label} into two equal pieces.",
        ),
        QAItem(
            question=f"How did the story end for {hero.name} and {sidekick.name}?",
            answer=f"They ended the day smiling because they had shared the tiny treat and solved the problem together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kernel?",
            answer="A kernel is a small hard seed, like the kind that can pop into popcorn when heated.",
        ),
        QAItem(
            question="What is a pocket for?",
            answer="A pocket is a small pouch in clothing where you can carry tiny things.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy part of something with you.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and finding a way to fix a trouble or make something work.",
        ),
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
    for e in world.entities.values():
        if isinstance(e, Character):
            lines.append(f"  {e.name:8} (character) pocket={e.pocket} memes={dict(e.memes)}")
        else:
            lines.append(f"  {e.id:8} ({e.kind}) owner={e.owner} carried_by={e.carried_by} location={e.location} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, kernel) combos:\n")
        for place, kernel in combos:
            print(f"  {place:8} {kernel}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place=p, hero="Milo", sidekick="Bess", kernel_kind=k)
            for p, k in [(place, kernel) for place in SETTINGS for kernel in KERNELS]
        ]
        samples = [generate(p) for p in params_list]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
