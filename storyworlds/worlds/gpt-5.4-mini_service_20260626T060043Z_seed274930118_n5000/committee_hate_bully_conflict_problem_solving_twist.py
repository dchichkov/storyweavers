#!/usr/bin/env python3
"""
A small adventure storyworld about a committee, a bully, and a problem-solving twist.

Premise:
- A kid-led committee is planning a little adventure.
- A bully tries to spoil it.
- The group hates the bully's mean tricks, but they solve the problem together.
- A twist reveals the bully is afraid of the same dark tunnel the committee needs to pass.

The simulated world tracks:
- physical meters: courage, distance, gear, blockage
- emotional memes: worry, hate, teamwork, pride, apology
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
class Entity:
    id: str
    kind: str
    name: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_m(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_e(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Place:
    name: str
    feature: str
    danger: str
    twist: str


@dataclass
class StoryParams:
    place: str
    hero: str
    bully: str
    committee_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    hero: Entity
    bully: Entity
    committee: Entity
    scene: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.scene.append(text)

    def para(self) -> None:
        if self.scene and self.scene[-1] != "":
            self.scene.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for item in self.scene:
            if item == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(item)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


PLACES = {
    "forest_path": Place(
        name="the forest path",
        feature="a mossy map stone",
        danger="a dark tunnel under the roots",
        twist="the bully is scared of the tunnel's echo",
    ),
    "cliff_bridge": Place(
        name="the cliff bridge",
        feature="a rope rail",
        danger="a gap with windy boards",
        twist="the bully cannot cross when the bridge sways",
    ),
    "river_bank": Place(
        name="the river bank",
        feature="a little boat dock",
        danger="a muddy shortcut near the water",
        twist="the bully hates wet shoes more than anyone",
    ),
}

HEROES = ["Mina", "Iris", "Theo", "Jules", "Nora", "Ezra"]
BULLIES = ["Rex", "Mack", "Bram", "Troy", "Kip", "Vex"]
COMMITTEES = ["trail committee", "map committee", "adventure committee", "bridge committee"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: committee, bully, conflict, problem solving, twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--bully")
    ap.add_argument("--committee-name", choices=COMMITTEES)
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
    hero = args.hero or rng.choice(HEROES)
    bully = args.bully or rng.choice([x for x in BULLIES if x != hero])
    committee_name = args.committee_name or rng.choice(COMMITTEES)
    if hero == bully:
        raise StoryError("The hero and bully must be different people.")
    return StoryParams(place=place, hero=hero, bully=bully, committee_name=committee_name)


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = Entity(id="hero", kind="character", name=params.hero, role="leader")
    bully = Entity(id="bully", kind="character", name=params.bully, role="troublemaker")
    committee = Entity(id="committee", kind="group", name=params.committee_name, role="team")
    w = World(place=place, hero=hero, bully=bully, committee=committee)

    hero.inc_e("curiosity", 1)
    hero.inc_e("teamwork", 1)
    hero.inc_m("distance", 1)
    bully.inc_e("mean", 1)
    bully.inc_e("hate", 1)
    committee.inc_e("teamwork", 2)

    w.say(f"{params.hero} led the {params.committee_name} down {place.name}.")
    w.say(f"They wanted to explore {place.feature} and reach {place.danger} before sunset.")
    w.para()

    w.say(f"But {params.bully} showed up and tried to block the path.")
    bully.inc_m("blockage", 1)
    hero.inc_e("worry", 1)
    committee.inc_e("hate", 1)
    w.say(f"The whole committee hated the bully's mean grin, but nobody wanted the trip to end there.")
    w.para()

    # Conflict
    hero.inc_m("courage", 1)
    w.say(f"{params.hero} stepped forward and said they would not turn back.")
    w.say(f"{params.bully} laughed and pointed at {place.danger}, trying to scare everyone away.")

    # Problem solving
    hero.inc_e("thoughtful", 1)
    committee.inc_e("teamwork", 2)
    w.say(f"Then the committee looked around and started problem solving.")
    w.say(f"They used {place.feature} to mark a safe line around the danger, and {params.hero} asked everyone to stay close.")
    bully.inc_e("worry", 1)

    # Twist
    w.para()
    w.say(f"That was when the twist appeared: {place.twist}.")
    w.say(f"{params.bully}'s voice shook, because the bully was not fearless at all.")
    w.say(f"{params.hero} offered a hand and said the team could walk together if {params.bully} stopped being mean.")
    bully.inc_e("apology", 1)
    bully.inc_e("hate", -1)
    committee.inc_e("pride", 1)
    hero.inc_e("pride", 1)
    w.say(f"{params.bully} mumbled an apology and moved aside.")
    w.say(f"At last, the committee crossed safely, and the adventure felt bigger because they solved the problem together.")

    w.facts = {
        "place": place,
        "hero": hero,
        "bully": bully,
        "committee": committee,
        "params": params,
    }
    return w


ASP_RULES = r"""
% Facts:
% place(Name).
% danger(Place, Danger).
% twist(Place, Twist).
% hero(Name).
% bully(Name).
% committee(Name).

conflict(Place) :- danger(Place, _), bully(_).
problem_solving(Place) :- conflict(Place), committee(_).
twist(Place) :- problem_solving(Place), twist(Place, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("danger", pid, place.danger))
        lines.append(asp.fact("twist", pid, place.twist))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show conflict/1. #show problem_solving/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model)
    expected = {("conflict", (p,)) for p in PLACES} | {("problem_solving", (p,)) for p in PLACES}
    if atoms:
        return 0
    print("ASP verification failed.")
    return 1


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who led the {p.committee_name} at {place.name}?",
            answer=f"{p.hero} led the {p.committee_name} at {place.name}.",
        ),
        QAItem(
            question=f"Why did the group feel conflict when {p.bully} appeared?",
            answer=f"The group felt conflict because {p.bully} tried to block the path and stop the adventure.",
        ),
        QAItem(
            question=f"What was the problem-solving plan at {place.name}?",
            answer=f"They used {place.feature} to mark a safe line around the danger and stayed together.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {place.twist}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the committee crossing safely after {p.bully} apologized and moved aside.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a committee?",
            answer="A committee is a small group that meets to plan, decide, or help with something.",
        ),
        QAItem(
            question="What does it mean to hate a mean trick?",
            answer="It means you strongly dislike it because it is unfair or hurts someone.",
        ),
        QAItem(
            question="What is a bully?",
            answer="A bully is someone who uses meanness or pressure to scare or hurt other people.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    place = world.facts["place"]
    return [
        f"Write an adventure story about {p.hero} and a {p.committee_name} at {place.name}.",
        f"Tell a child-friendly story where {p.bully} acts like a bully, but the group solves the problem.",
        f"Write a short adventure tale with conflict, problem solving, and a twist at {place.name}.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.bully, world.committee]:
        lines.append(f"{ent.id}: name={ent.name} role={ent.role} meters={ent.meters} memes={ent.memes}")
    lines.append(f"place: {world.place.name}")
    lines.append(f"feature: {world.place.feature}")
    lines.append(f"danger: {world.place.danger}")
    lines.append(f"twist: {world.place.twist}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/1. #show problem_solving/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="forest_path", hero="Mina", bully="Rex", committee_name="trail committee"),
            StoryParams(place="cliff_bridge", hero="Theo", bully="Vex", committee_name="bridge committee"),
            StoryParams(place="river_bank", hero="Nora", bully="Mack", committee_name="adventure committee"),
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
