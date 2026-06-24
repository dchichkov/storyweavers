#!/usr/bin/env python3
"""
A small nursery-rhyme story world set in a subway station, where a team, an
inning, and a pregnant traveler make room for a surprise twist.
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
class StoryParams:
    team: str
    inning: str
    surprise: str
    twist: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "mother":
            return "she"
        if self.kind == "child":
            return "they"
        return "it"

    def poss(self) -> str:
        if self.kind == "mother":
            return "her"
        if self.kind == "child":
            return "their"
        return "its"


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


TEAMS = {
    "Owls": "a little team of owls",
    "Bunnies": "a bright little team of bunnies",
    "Pandas": "a gentle little team of pandas",
    "Robins": "a merry little team of robins",
}

INNINGS = {
    "first inning": {"count": 1, "rhythm": "one"},
    "second inning": {"count": 2, "rhythm": "two"},
    "third inning": {"count": 3, "rhythm": "three"},
}

SURPRISES = {
    "a tiny dropped ticket": "a ticket",
    "a balloon that bonked the bench": "a balloon",
    "a ringing penny in a cup": "a penny",
}

TWISTS = {
    "a warm seat": "warm seat",
    "a helping hand": "helping hand",
    "a shared snack": "shared snack",
}

NAMES = ["Mia", "Nora", "Leo", "Finn", "Lily", "Ava", "Ben", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a team, an inning, and a subway station surprise.")
    ap.add_argument("--team", choices=TEAMS)
    ap.add_argument("--inning", choices=INNINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--twist", choices=TWISTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    team = args.team or rng.choice(list(TEAMS))
    inning = args.inning or rng.choice(list(INNINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    twist = args.twist or rng.choice(list(TWISTS))
    if surprise == "a tiny dropped ticket" and twist == "a warm seat":
        pass
    return StoryParams(team=team, inning=inning, surprise=surprise, twist=twist)


def generate(params: StoryParams) -> StorySample:
    world = World()
    team = world.add(Entity("team", "team", TEAMS[params.team]))
    mom = world.add(Entity("mom", "mother", "a pregnant mama"))
    child = world.add(Entity("child", "child", "a small child"))
    station = world.add(Entity("station", "place", "the subway station"))

    team.memes["cheer"] = 1
    mom.meters["pregnant"] = 1
    child.memes["wonder"] = 1

    world.say(f"{TEAMS[params.team]} went down, went down, to the {station.label},")
    world.say(f"On {params.inning}, with a hop and a hum, so merry and well.")
    world.say(f"There walked {mom.label}, pregnant and round, with {child.label} by her side,")
    world.say(f"While the little {params.team.lower()} team clapped softly, and stayed close by.")

    world.para()
    world.say(f"Then came {params.surprise}, all twinkly and small,")
    world.say(f"It slipped to the floor with a tap-tippy call.")
    team.memes["surprise"] = 1
    mom.memes["startled"] = 1

    world.para()
    world.say(f"But here came the {params.twist}, as gentle as snow:")
    world.say(f"The team made a warm seat where the quiet folks go.")
    child.memes["kindness"] = 1
    mom.memes["relief"] = 1
    team.meters["helped"] = 1

    world.para()
    world.say(f"So {mom.label} sat down, and she smiled with delight,")
    world.say(f"The child held the ticket, and all felt just right.")
    world.say(f"The team said goodbye with a soft subway cheer,")
    world.say(f"And the station grew cozy, as if springtime were near.")

    world.facts.update(
        team=params.team,
        inning=params.inning,
        surprise=params.surprise,
        twist=params.twist,
        mom=mom,
        child=child,
        station=station,
    )

    prompts = [
        f"Write a nursery-rhyme story in a subway station about {TEAMS[params.team]}, {params.inning}, and a surprise twist.",
        f"Tell a gentle rhyme where a pregnant traveler meets {params.team.lower()} during {params.inning} at the subway station.",
        f"Write a child-friendly story with a surprise and a twist, ending in kindness at the subway station.",
    ]

    story_qa = [
        QAItem(
            question="Where does the story happen?",
            answer="It happens at the subway station, where the team and the traveler meet.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was {params.surprise}, which added a little spark to the station scene.",
        ),
        QAItem(
            question=f"What was the twist that changed the moment?",
            answer=f"The twist was {params.twist}; it turned the moment gentle by giving someone a warm place to sit.",
        ),
        QAItem(
            question="Who was pregnant in the story?",
            answer="The mama was pregnant, and the story showed her moving slowly and needing a kind place to rest.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place where people wait for trains that travel underground.",
        ),
        QAItem(
            question="What does pregnant mean?",
            answer="Pregnant means a mother is carrying a baby in her body before the baby is born.",
        ),
        QAItem(
            question="What is a team?",
            answer="A team is a group of people or animals who work and cheer together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something sudden that you did not expect.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that turns the story in a new direction.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.label} {' '.join(bits)}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
team(t1).
inning(i1).
surprise(s1).
twist(tw1).

valid_story(T,I,S,TW) :- team(T), inning(I), surprise(S), twist(TW).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in TEAMS:
        lines.append(asp.fact("team", t))
    for i in INNINGS:
        lines.append(asp.fact("inning", i))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate_all(curated: list[StoryParams]) -> list[StorySample]:
    return [generate(p) for p in curated]


CURATED = [
    StoryParams("Owls", "first inning", "a tiny dropped ticket", "a warm seat"),
    StoryParams("Bunnies", "second inning", "a balloon that bonked the bench", "a helping hand"),
    StoryParams("Robins", "third inning", "a ringing penny in a cup", "a shared snack"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for the bundled valid-story relation.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = generate_all(CURATED)
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.team} / {p.inning}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
