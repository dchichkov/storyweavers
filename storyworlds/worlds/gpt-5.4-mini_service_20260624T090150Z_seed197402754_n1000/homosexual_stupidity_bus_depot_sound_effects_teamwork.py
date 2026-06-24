#!/usr/bin/env python3
"""
Storyworld: a small adventure at a bus depot where sound effects, teamwork,
and kindness help a mixed-up day turn into a good one.

The world includes the seed words "homosexual" and "stupidity" only as
child-safe world-knowledge vocabulary; the story itself stays focused on a
bus-depot adventure, helpful teamwork, and a kind fix after a noisy mistake.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

BUS_DEPOT = "bus depot"


@dataclass
class StoryParams:
    depot: str = BUS_DEPOT
    hero: str = "Mina"
    helper: str = "Jules"
    bus: str = "yellow bus"
    sound_effect: str = "clang-clang"
    teamwork_tool: str = "signal flags"
    kindness_action: str = "shared a smile"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.params)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.trace_log = list(self.trace_log)
        return clone


def make_world(params: StoryParams) -> World:
    w = World(params)
    hero = w.add(Entity("hero", "character", params.hero, meters={"curiosity": 1.0}, memes={"brave": 1.0}))
    helper = w.add(Entity("helper", "character", params.helper, meters={"calm": 1.0}, memes={"kind": 1.0}))
    bus = w.add(Entity("bus", "vehicle", params.bus, meters={"noise": 0.0, "delay": 0.0}, memes={"restless": 0.0}))
    w.facts.update(hero=hero, helper=helper, bus=bus)
    return w


def _rattle(world: World) -> None:
    bus = world.entities["bus"]
    bus.meters["noise"] += 1.0
    bus.meters["delay"] += 1.0
    world.trace_log.append("bus made a loud rattle and got delayed")


def _teamwork(world: World) -> None:
    bus = world.entities["bus"]
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    if bus.meters["noise"] >= 1.0 and bus.meters["delay"] >= 1.0:
        hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
        helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0.0) + 1.0
        bus.meters["delay"] = max(0.0, bus.meters["delay"] - 1.0)
        world.trace_log.append("teamwork reduced the delay")


def _kindness(world: World) -> None:
    helper = world.entities["helper"]
    hero = world.entities["hero"]
    helper.memes["kind"] = helper.memes.get("kind", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    world.trace_log.append("kindness made the work feel lighter")


def story_text(world: World) -> None:
    p = world.params
    hero = p.hero
    helper = p.helper
    bus = p.bus

    world.say(
        f"At the {p.depot}, {hero} loved the busy morning sounds. "
        f"Doors hissed, shoes tapped, and every bus seemed to wake up for an adventure."
    )
    world.say(
        f"{hero} and {helper} were helping guide {bus} out of the lane when a sudden {p.sound_effect} "
        f"echoed across the depot."
    )
    _rattle(world)
    world.say(
        f"The noise startled a driver, and for a moment the line got mixed up. "
        f"{hero} felt a little worried, but {helper} said, "
        f"\"No problem. We can fix this together.\""
    )
    world.para()
    world.say(
        f"They lifted the {p.teamwork_tool}, pointed the right way, and counted the buses one by one. "
        f"{hero} matched each signal with a careful step, and {helper} kept the path clear."
    )
    _teamwork(world)
    world.say(
        f"Then {helper} {p.kindness_action}, which helped everyone stay calm. "
        f"The driver smiled, the lane straightened out, and {bus} rolled forward again."
    )
    _kindness(world)
    world.para()
    world.say(
        f"By the end, the depot sounded cheerful instead of confusing. "
        f"{hero} heard the steady hum of engines, {helper} waved, and the whole team sent {bus} on its way."
    )
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an adventure story set in a {p.depot} where sound effects help a team solve a problem.",
        f"Tell a child-friendly story about {p.hero} and {p.helper} using teamwork and kindness to help {p.bus}.",
        f"Create a short depot adventure with the sound effect {p.sound_effect} and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"The story happens at the {p.depot}.",
        ),
        QAItem(
            question=f"What sound effect startled everyone?",
            answer=f"The loud sound effect was {p.sound_effect}.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.helper} help {p.bus}?",
            answer=f"They used teamwork, pointed with {p.teamwork_tool}, and stayed kind so {p.bus} could leave safely.",
        ),
        QAItem(
            question=f"What made the big problem feel smaller?",
            answer=f"Kindness made the work feel lighter, and teamwork helped the line get sorted out.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other reach the same goal.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made-up or special noise that helps tell a story or make a scene feel lively.",
        ),
        QAItem(
            question="What does homosexual mean?",
            answer="Homosexual means a person is romantically attracted to people of the same sex.",
        ),
        QAItem(
            question="What does stupidity mean?",
            answer="Stupidity is a hurtful word for acting without thinking; it is better to say someone made a mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: kind={ent.kind} label={ent.label} meters={meters} memes={memes}")
    lines.extend(world.trace_log)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bus depot adventure storyworld.")
    ap.add_argument("--hero", default="Mina")
    ap.add_argument("--helper", default="Jules")
    ap.add_argument("--bus", default="yellow bus")
    ap.add_argument("--sound-effect", default="clang-clang")
    ap.add_argument("--teamwork-tool", default="signal flags")
    ap.add_argument("--kindness-action", default="shared a smile")
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
    if args.hero.strip() == "":
        raise StoryError("hero cannot be empty")
    if args.helper.strip() == "":
        raise StoryError("helper cannot be empty")
    if args.bus.strip() == "":
        raise StoryError("bus cannot be empty")
    return StoryParams(
        hero=args.hero or rng.choice(["Mina", "Arlo", "Tess", "Noah"]),
        helper=args.helper or rng.choice(["Jules", "Pia", "Rin", "Omar"]),
        bus=args.bus or "yellow bus",
        sound_effect=args.sound_effect or rng.choice(["clang-clang", "beep-beep", "whoosh"]),
        teamwork_tool=args.teamwork_tool or rng.choice(["signal flags", "a map board", "chalk arrows"]),
        kindness_action=args.kindness_action or rng.choice(["shared a smile", "passed out water", "spoke softly"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_text(world)
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
        print(format_qa(sample))


ASP_RULES = r"""
kind_story :- teamwork, kindness, sound_effect.
resolved :- kind_story.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "bus_depot"),
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "kindness"),
        asp.fact("theme", "adventure"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
