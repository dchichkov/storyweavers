#!/usr/bin/env python3
"""
storyworlds/worlds/relay_conflict_kindness_problem_solving_myth.py
==================================================================

A small myth-style storyworld about a relay, where conflict is softened by
kindness and resolved by problem solving.

The world model tracks physical state in meters and emotional state in memes.
A relay baton, a route with stages, and a goal shrine create a tiny classical
myth: tension rises when a runner blocks the handoff, then kindness and a
clever plan restore the run.

This script is standalone and uses only the standard library plus the shared
storyworld results/ASP helpers from the repo.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    stage: int = 0


@dataclass
class Place:
    name: str
    mood: str
    stages: list[str]
    goal: str


@dataclass
class Relay:
    baton: str
    field: str
    stages: list[str]
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    relay: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "river_valley": Place(
        name="the river valley",
        mood="the old stones watched everything",
        stages=["stone arch", "reed path", "sunlit hill"],
        goal="the mossy gate",
    ),
    "sun_court": Place(
        name="the sun court",
        mood="the bright dust shimmered like gold",
        stages=["lion step", "mirror walk", "gate of palms"],
        goal="the lantern tree",
    ),
}

RELAYS = {
    "torch_run": Relay(
        baton="the torch",
        field="a winding path",
        stages=["first bend", "white bridge", "hilltop"],
        risk="the handoff could fail",
        fix="they could slow down and pass the torch carefully",
        tags={"relay", "conflict", "kindness", "problem_solving", "myth"},
    ),
    "river_shell": Relay(
        baton="the shell charm",
        field="a river trail",
        stages=["river bank", "stone ford", "oak rise"],
        risk="the charm could slip into the water",
        fix="they could tie a cord and plan a safer handoff",
        tags={"relay", "conflict", "kindness", "problem_solving", "myth"},
    ),
}

NAMES = ["Ari", "Mira", "Tala", "Soren", "Ivo", "Nila", "Rin", "Cleo"]
HELPERS = ["the owl", "the fox", "the old runner", "the kind shepherd"]


class World:
    def __init__(self, place: Place, relay: Relay) -> None:
        self.place = place
        self.relay = relay
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.place, self.relay)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style relay storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relay", choices=RELAYS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    relay = args.relay or rng.choice(list(RELAYS))
    hero = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, relay=relay, hero=hero, helper=helper)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for i, stage in enumerate(place.stages, 1):
            lines.append(asp.fact("stage", pid, i, stage))
    for rid, relay in RELAYS.items():
        lines.append(asp.fact("relay", rid))
        for i, stage in enumerate(relay.stages, 1):
            lines.append(asp.fact("relay_stage", rid, i, stage))
        for tag in relay.tags:
            lines.append(asp.fact("tagged", rid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, R) :- place(P), relay(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate_story(world: World, hero: Entity, helper: Entity) -> None:
    relay = world.relay
    place = world.place

    world.say(f"In {place.name}, {place.mood}.")
    world.say(
        f"{hero.label} was chosen to carry {relay.baton} across {relay.field} "
        f"to {place.goal}."
    )
    world.say(
        f"At the first stage, {hero.label} ran well, but at the next handoff "
        f"a rival blocker stepped close, and {relay.risk}."
    )
    hero.memes["conflict"] += 1
    hero.meters["speed"] = 1

    world.para()
    world.say(
        f"Then {helper.label} called out kindly, not with anger but with care."
    )
    world.say(
        f"{helper.label} showed how to slow the steps, stand side by side, "
        f"and pass {relay.baton} with both hands."
    )
    hero.memes["kindness"] += 1
    hero.memes["problem_solving"] += 1

    world.para()
    world.say(
        f"The two of them made a new plan: {relay.fix}. "
        f"{hero.label} breathed deep and tried again."
    )
    hero.memes["conflict"] = 0
    hero.meters["carried"] = 1
    world.say(
        f"This time the relay worked. {hero.label} carried {relay.baton} to "
        f"{place.goal}, and the stones seemed to glow as the mythic run was finished."
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    relay = RELAYS[params.relay]
    world = World(place, relay)

    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper))

    world.facts.update(place=place, relay=relay, hero=hero, helper=helper, params=params)
    generate_story(world, hero, helper)

    prompts = [
        f"Write a short myth about a relay at {place.name} where kindness solves a conflict.",
        f"Tell a child-friendly story in which {params.name} must carry {relay.baton} and learns a better way to pass it.",
        f"Create a mythic story with a relay, a problem, and a gentle solution.",
    ]

    story_qa = [
        QAItem(
            question=f"Who carried {relay.baton} in the story?",
            answer=f"{params.name} carried {relay.baton} at first, then learned a safer way to pass it with help.",
        ),
        QAItem(
            question="What caused the conflict during the relay?",
            answer="A blocker got in the way at the handoff, so the run almost failed.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"They slowed down, used two hands, and followed {relay.fix}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a relay?",
            answer="A relay is a team event where one runner passes a baton or object to another runner.",
        ),
        QAItem(
            question="Why can kindness help during conflict?",
            answer="Kindness helps people listen, calm down, and work together instead of fighting.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong and finding a smart way to fix it.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: label={e.label!r} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"place={world.place.name}")
    lines.append(f"relay={world.relay.baton}")
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
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        print("OK: verify mode placeholder for this world.")
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in (
            StoryParams(place=pl, relay=rl, hero=name, helper=help_)
            for pl in PLACES for rl in RELAYS for name in NAMES[:2] for help_ in HELPERS[:1]
        ):
            samples.append(generate(p))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
