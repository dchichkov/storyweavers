#!/usr/bin/env python3
"""
A small ghost-story world with kindness, friendship, problem solving, and a
touch of majesty.
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

MAJESTY_WORD = "majesty"


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        return mapping[case]


@dataclass
class Place:
    name: str
    spooky: bool = False
    kind: str = "house"
    majesty: str = "glimmer"


@dataclass
class Problem:
    id: str
    name: str
    clue: str
    cause: str
    fix: str
    solution_item: str


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


PLACES = {
    "old_castle": Place(name="the old castle", spooky=True, kind="castle", majesty="golden"),
    "moon_house": Place(name="the moonlit house", spooky=True, kind="house", majesty="silver"),
    "quiet_tower": Place(name="the quiet tower", spooky=True, kind="tower", majesty="bright"),
}

PROBLEMS = {
    "rattle": Problem(
        id="rattle",
        name="a rattling sound",
        clue="something was tapping in the dark hallway",
        cause="a loose spoon in a tin cup",
        fix="put the cup on a soft cloth so it would stop clinking",
        solution_item="soft cloth",
    ),
    "wind": Problem(
        id="wind",
        name="a crying wind",
        clue="the windows kept whistling like a lonely song",
        cause="one window was left open",
        fix="close the window and tuck a blanket under the sill",
        solution_item="blanket",
    ),
    "shadow": Problem(
        id="shadow",
        name="a strange shadow",
        clue="a giant shape kept moving across the wall",
        cause="a lantern was rocking in the draft",
        fix="steady the lantern and move it near the table",
        solution_item="lantern",
    ),
}

HEROES = {
    "Mina": {"type": "girl", "traits": ["small", "brave"]},
    "Eli": {"type": "boy", "traits": ["small", "curious"]},
    "Nora": {"type": "girl", "traits": ["small", "gentle"]},
    "Theo": {"type": "boy", "traits": ["small", "kind"]},
}

FRIENDS = ["ghost", "lantern-keeper", "small owl", "sleepy cat"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost story world with kindness and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice(list(FRIENDS))
    return StoryParams(place=place, problem=problem, hero=hero, friend=friend)


def _hero_subject(name: str) -> str:
    return name


def _hero_possessive(name: str) -> str:
    return "their"


def _hero_object(name: str) -> str:
    return "them"


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    hero_data = HEROES[params.hero]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=hero_data["type"],
        traits=hero_data["traits"] + ["kind"],
        memes={"curiosity": 1.0, "kindness": 1.0, "friendship": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=params.friend,
        traits=["helpful", "quiet"],
        memes={"kindness": 1.0, "friendship": 1.0, "joy": 0.0},
    ))
    clue_item = world.add(Entity(
        id="clue",
        type=problem.solution_item,
        label=problem.solution_item,
        phrase=problem.solution_item,
        owner=hero.id,
        caretaker=friend.id,
        meters={"dust": 1.0},
    ))

    world.say(
        f"One night, {hero.id} walked into {place.name}, where the air felt hushed and full of {MAJESTY_WORD}."
    )
    world.say(
        f"{hero.id} loved the soft glow there, even though {problem.clue}."
    )

    world.para()
    hero.memes["worry"] += 1.0
    world.say(
        f"{hero.id} listened carefully and did not run away."
    )
    world.say(
        f"Instead, {hero.id} found {params.friend}, and together they looked for the cause."
    )

    world.para()
    world.say(
        f"They checked the room one piece at a time, because good problem solving starts with looking closely."
    )
    world.say(
        f"At last, they found that {problem.cause}."
    )
    world.say(
        f"{params.friend} stayed calm and kind, and {hero.id} helped with a gentle hand."
    )

    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1.0
    hero.memes["friendship"] += 1.0
    friend.memes["joy"] += 1.0
    world.say(
        f"They worked together to {problem.fix}."
    )
    world.say(
        f"The scary sound faded away, and the room felt peaceful again."
    )
    world.say(
        f"By the end, {hero.id} and {params.friend} smiled in the moonlight, and the old place seemed full of quiet {MAJESTY_WORD}."
    )

    world.facts = {
        "hero": hero,
        "friend": friend,
        "place": place,
        "problem": problem,
        "clue_item": clue_item,
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f"Write a gentle ghost story about {hero.id} solving {problem.name} with kindness and friendship.",
        f"Tell a child-friendly story set in {world.place.name} that includes {MAJESTY_WORD} and a helpful ghostly mystery.",
        f"Write a short story where a brave child and a friend work together to fix something spooky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to {place.name}, which felt spooky but also calm and grand.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer=f"The problem was {problem.name}, and it was caused by {problem.cause}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=f"They solved it by working together and chose to {problem.fix}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and brave at the end because the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about something spooky, mysterious, or hidden, often told in a gentle way for children.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, and using gentle words and actions so someone else feels cared for.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and like being together.",
        ),
        QAItem(
            question=f"What does {MAJESTY_WORD} mean?",
            answer="Majesty means something feels grand, noble, or shining with special importance.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].spooky:
            lines.append(asp.fact("spooky", p))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("solves_with", pid, pr.solution_item))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for fr in FRIENDS:
        lines.append(asp.fact("friend_kind", fr))
    return "\n".join(lines)


ASP_RULES = r"""
resolved(P, Pr) :- problem(P), solves_with(P, Pr).
good_story(H, P) :- hero(H), place(P), resolved(_, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/2."))
    return 0 if model is not None else 1


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="old_castle", problem="rattle", hero="Mina", friend="ghost"),
    StoryParams(place="moon_house", problem="wind", hero="Eli", friend="small owl"),
    StoryParams(place="quiet_tower", problem="shadow", hero="Nora", friend="lantern-keeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
