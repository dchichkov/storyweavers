#!/usr/bin/env python3
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
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class World:
    place: str
    hero: Character
    friend: Character
    inspector: str
    project: str
    advance_check: bool = False
    inspection_done: bool = False
    twist: bool = False
    friendship: float = 0.0
    comedy: float = 0.0
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


@dataclass
class StoryParams:
    place: str
    project: str
    hero_name: str
    friend_name: str
    inspector: str
    seed: Optional[int] = None


PLACES = {
    "gym": "the school gym",
    "hall": "the community hall",
    "library": "the library room",
    "yard": "the sunny yard",
}

PROJECTS = {
    "tower": "a wobbly cardboard tower",
    "banner": "a bright paper banner",
    "cart": "a snack cart on squeaky wheels",
    "mask": "a glittery parade mask",
}

INSPECTORS = ["a serious teacher", "a polite coach", "a tiny city clerk", "a cheerful parent"]
HEROES = ["Mina", "Ollie", "Pip", "Nora", "Ben", "Lena"]
FRIENDS = ["Toby", "Maya", "Zed", "Ruby", "Finn", "Ivy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about an advance inspection, a twist, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--inspector", choices=INSPECTORS)
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
    place = args.place or rng.choice(list(PLACES))
    project = args.project or rng.choice(list(PROJECTS))
    hero = args.hero_name or rng.choice(HEROES)
    friend_choices = [n for n in FRIENDS if n != hero]
    friend = args.friend_name or rng.choice(friend_choices)
    inspector = args.inspector or rng.choice(INSPECTORS)
    return StoryParams(place=place, project=project, hero_name=hero, friend_name=friend, inspector=inspector)


def generate(params: StoryParams) -> StorySample:
    world = World(
        place=PLACES[params.place],
        hero=Character(params.hero_name, "hero"),
        friend=Character(params.friend_name, "friend"),
        inspector=params.inspector,
        project=PROJECTS[params.project],
    )
    world.hero.meters["worry"] = 0
    world.friend.meters["worry"] = 0
    world.friendship = 1.0
    world.comedy = 1.0

    world.say(f"{world.hero.name} and {world.friend.name} were building {world.project} for the big day at {world.place}.")
    world.say(f"They wanted to make an advance inspection look easy, so they checked every tape strip and every crooked corner.")
    world.para()

    world.advance_check = True
    world.hero.meters["worry"] += 1
    world.friend.meters["worry"] += 1
    world.say(f"Then {world.hero.name} spotted a tiny wobble and said, \"We need one more advance inspection before anyone sees this!\"")
    world.say(f"{world.friend.name} nodded, but the wobble kept sliding away like it had its own secret joke.")

    world.para()
    world.inspection_done = True
    world.twist = True
    world.hero.memes["surprise"] = 1.0
    world.friend.memes["surprise"] = 1.0
    world.say(f"Just then, {world.inspector} arrived for the inspection.")
    world.say(f"Twist: the 'serious' inspector turned out to be wearing a sticker that said, 'I like silly snacks and good repairs.'")
    world.say(f"They peered at {world.project}, laughed at the wobble, and showed the friends how to fix it with one brave strip of tape.")

    world.para()
    world.friendship += 1.0
    world.comedy += 1.0
    world.say(f"{world.hero.name} and {world.friend.name} giggled, fixed the wobble, and gave {world.inspector} a tiny bow.")
    world.say(f"In the end, their project stood steady, the inspection passed, and their friendship felt even stronger than the tape.")

    world.facts = {
        "place": params.place,
        "project": params.project,
        "hero": params.hero_name,
        "friend": params.friend_name,
        "inspector": params.inspector,
        "advance_check": world.advance_check,
        "inspection_done": world.inspection_done,
        "twist": world.twist,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a funny story about {world.hero.name} and {world.friend.name} doing an advance inspection on {world.project}.",
        f"Tell a comedy story where a twist during an inspection helps two friends fix {world.project} at {world.place}.",
        f"Write a child-friendly friendship story that includes the words advance and inspection.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who worked on {world.project}?",
            answer=f"{world.hero.name} and {world.friend.name} worked on {world.project} together.",
        ),
        QAItem(
            question="What did they do before the big day?",
            answer="They did an advance inspection to catch a small wobble before anyone else saw it.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {world.inspector} was friendly and helped fix the project instead of being scary.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The project stood steady, the inspection passed, and the friends felt proud and happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inspection?",
            answer="An inspection is a careful look at something to check whether it is safe, neat, or ready.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, helping each other, and enjoying time together.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story different from what you expected.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place}")
    lines.append(f"project: {world.project}")
    lines.append(f"hero worry: {world.hero.meters.get('worry', 0)}")
    lines.append(f"friend worry: {world.friend.meters.get('worry', 0)}")
    lines.append(f"advance_check: {world.advance_check}")
    lines.append(f"inspection_done: {world.inspection_done}")
    lines.append(f"twist: {world.twist}")
    lines.append(f"friendship: {world.friendship}")
    lines.append(f"comedy: {world.comedy}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(gym;hall;library;yard).
project(tower;banner;cart;mask).
inspector(serious_teacher;polite_coach;tiny_city_clerk;cheerful_parent).

advance_ok(P,J) :- place(P), project(J).
twist_story(P,J,I) :- advance_ok(P,J), inspector(I).
friendship_story(P,J,I) :- twist_story(P,J,I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for j in PROJECTS:
        lines.append(asp.fact("project", j))
    for i, insp in enumerate(INSPECTORS):
        safe = insp.replace(" ", "_")
        lines.append(asp.fact("inspector", safe))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show advance_ok/2.\n#show twist_story/3.\n#show friendship_story/3."))
    ok = bool(model)
    python_ok = True
    if ok != python_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1
    print("OK: ASP parity check passed.")
    return 0


def resolve_all_params() -> list[StoryParams]:
    out = []
    for p in PLACES:
        for j in PROJECTS:
            out.append(StoryParams(p, j, HEROES[0], FRIENDS[1], INSPECTORS[0]))
    return out


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
        print(asp_program("#show advance_ok/2.\n#show twist_story/3.\n#show friendship_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show advance_ok/2.\n#show twist_story/3.\n#show friendship_story/3."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(resolve_all_params()):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
