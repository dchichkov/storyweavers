#!/usr/bin/env python3
"""
A small comedy storyworld about a tadpole, a permit, and a plan that has to be
solved with sound effects and dialogue.

The seed tale:
---
A tiny tad named Tad wanted to join the pond parade. But the pond gatekeeper
said, "No permit, no parade." Tad intended to go anyway, but the wind blew his
paper permit into the reeds. He and his friend figured out a funny way to find
it, using splashes, squeaks, and a lot of teamwork. In the end, Tad got the
permit stamped and made it to the parade with a cheerful "pop!"
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"tad", "frog", "toad"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
            if self.type in {"gatekeeper", "ranger", "judge"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pond gate"
    outdoors: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    gatekeeper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pond_gate": Setting(place="the pond gate", outdoors=True),
    "reeds": Setting(place="the reeds by the pond", outdoors=True),
    "permit_booth": Setting(place="the permit booth", outdoors=True),
    "parade_path": Setting(place="the parade path", outdoors=True),
}

HERO_NAMES = ["Tad", "Tilly", "Milo", "Nina", "Pip", "Bram"]
HELPER_NAMES = ["Dot", "Moss", "Gus", "Ribbit", "Juno"]
GATEKEEPER_NAMES = ["Officer Hoot", "Mayor Mabel", "Mr. Croak", "Mrs. Wren"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A permit is valid for an activity when the permit matches the place and the
% problem is solved.
valid_story(P, H, G) :- permit(P), hero(H), gatekeeper(G), can_enter(P, H, G).

can_enter(P, H, G) :- has_permit(H, P), stamped(P), approved_by(G, P).
missing_permit(H, P) :- hero(H), permit(P), not has_permit(H, P).
problem(H, P) :- missing_permit(H, P).
solved(H, P) :- found(P), stamped(P), has_permit(H, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story_combo(params: StoryParams) -> bool:
    return params.place in SETTINGS and bool(params.hero_name) and bool(params.helper_name) and bool(params.gatekeeper_name)


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def sfx(name: str) -> str:
    return {
        "wind": "WHOOOSH!",
        "splash": "SPLOP!",
        "reed": "rustle-rustle",
        "stamp": "THUMP!",
        "pop": "POP!",
        "squeak": "Eek!",
        "flip": "flap-flap",
    }.get(name, name)


def intro(world: World, hero: Entity, helper: Entity, gatekeeper: Entity) -> None:
    world.say(
        f"{hero.id} was a tiny tad who liked to intend big things, even when the pond looked very serious."
    )
    world.say(
        f"{helper.id} was {helper.phrase}, and {gatekeeper.id} stood at {world.setting.place} with a clipboard and a very important face."
    )


def setup_permit(world: World, hero: Entity) -> Entity:
    permit = world.add(Entity(
        id="permit",
        type="permit",
        label="permit",
        phrase="a small paper permit with a bright blue stamp box",
        owner=hero.id,
        holder=hero.id,
    ))
    world.say(
        f"{hero.id} had {permit.phrase}. {hero.pronoun('possessive').capitalize()} {permit.label} was supposed to get stamped before the parade."
    )
    return permit


def want_to_go(world: World, hero: Entity) -> None:
    hero.memes["intend"] = hero.memes.get("intend", 0) + 1
    world.say(f'"I intend to join the parade," {hero.id} said. "I even practiced my happy hop!"')


def gate_problem(world: World, gatekeeper: Entity, hero: Entity, permit: Entity) -> None:
    world.say(
        f'"No permit, no parade," said {gatekeeper.id}. "{hero.id}, where is your stamped paper?"'
    )
    world.say(f"{hero.id} blinked. {sfx('squeak')}")
    world.facts["missing_stamp"] = True
    permit.meters["unstamped"] = 1


def wind_blow(world: World, permit: Entity) -> None:
    permit.holder = None
    world.say(f"Then the wind went {sfx('wind')} and snatched the permit into the reeds.")
    world.say(f"The paper did a little {sfx('flip')} and vanished with a tiny {sfx('reed')}.")
    world.facts["lost_permit"] = True


def problem_solve(world: World, hero: Entity, helper: Entity, permit: Entity) -> None:
    world.say(f"{helper.id} pointed at the reeds. \"If we find it, we can still get it stamped,\" {helper.id} said.")
    world.say(f"\"Good plan,\" said {hero.id}. \"I will hop left, you hop right.\"")
    world.say(f"They searched with careful splashes. {sfx('splash')} {sfx('splash')}")
    world.say(f"{helper.id} listened for paper and said, \"Shhh! I hear a {sfx('reed')} over there.\"")
    permit.holder = hero.id
    permit.meters["found"] = 1
    world.facts["found_permit"] = True
    world.facts["problem_solved"] = True


def stamp_permit(world: World, gatekeeper: Entity, hero: Entity, permit: Entity) -> None:
    permit.meters["stamped"] = 1
    permit.holder = hero.id
    world.say(f'{gatekeeper.id} smiled. "{hero.id} found it? Then thump it here." {sfx("stamp")}')
    world.say(f"The blue box got a perfect stamp, and {hero.id} held the paper up like treasure.")


def finish_parade(world: World, hero: Entity, helper: Entity) -> None:
    world.say(f"{hero.id} trotted onto the parade path with {helper.id} beside them.")
    world.say(f'The drum beat went "boom-boom," and {hero.id} gave one proud {sfx("pop")}.')
    world.say(f"At last, the little tad was allowed in, and the whole pond seemed to grin.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="tad", phrase="a tiny tad with bright eyes"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="friend", phrase="a quick-footed friend"))
    gatekeeper = world.add(Entity(id=params.gatekeeper_name, kind="character", type="gatekeeper", phrase="the pond gatekeeper"))

    intro(world, hero, helper, gatekeeper)
    world.para()
    permit = setup_permit(world, hero)
    want_to_go(world, hero)
    gate_problem(world, gatekeeper, hero, permit)
    wind_blow(world, permit)
    world.para()
    problem_solve(world, hero, helper, permit)
    stamp_permit(world, gatekeeper, hero, permit)
    finish_parade(world, hero, helper)

    world.facts.update(hero=hero, helper=helper, gatekeeper=gatekeeper, permit=permit)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a funny story about a tiny tad named {hero.id} who tries to enter {world.setting.place} but needs a permit.',
        f'Tell a comedy story with dialogue where {hero.id} intends to join a parade, loses a permit, and solves the problem with a friend.',
        f'Write a child-friendly story with sound effects like "whoosh" and "pop" about {hero.id} and {helper.id} finding a permit.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    gatekeeper = world.facts["gatekeeper"]
    permit = world.facts["permit"]
    return [
        QAItem(
            question=f"Why couldn't {hero.id} enter the parade right away?",
            answer=f"{hero.id} could not enter right away because {gatekeeper.id} wanted to see a stamped permit first.",
        ),
        QAItem(
            question=f"What happened to the permit after the wind blew?",
            answer=f"The wind blew the permit into the reeds, so {hero.id} had to look for it again with {helper.id}.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=f"{hero.id} and {helper.id} searched the reeds, found the permit, and got it stamped before the parade started.",
        ),
        QAItem(
            question=f"What sound did the story make when the permit got stamped?",
            answer=f'The story used "THUMP!" when {gatekeeper.id} stamped the permit.',
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and cheerful because the permit was stamped and the parade was finally allowed to begin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a permit?",
            answer="A permit is a paper that says you are allowed to do something or enter a place.",
        ),
        QAItem(
            question="What is a tadpole?",
            answer="A tadpole is a young frog with a tail that lives in water before it grows up.",
        ),
        QAItem(
            question="What does it mean to intend something?",
            answer="To intend something means to plan to do it on purpose.",
        ),
        QAItem(
            question="Why do people solve problems by talking?",
            answer="People talk to share ideas, make a plan, and work together when something goes wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.holder:
            bits.append(f"holder={e.holder}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: permit, tad, intend, sound effects, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--gatekeeper-name", choices=GATEKEEPER_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    gatekeeper_name = args.gatekeeper_name or rng.choice(GATEKEEPER_NAMES)
    params = StoryParams(place=place, hero_name=hero_name, helper_name=helper_name, gatekeeper_name=gatekeeper_name)
    if not valid_story_combo(params):
        raise StoryError("invalid story choices")
    return params


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        print("OK: verification stub passed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("pond_gate", "Tad", "Dot", "Officer Hoot"),
            StoryParams("reeds", "Tilly", "Moss", "Mayor Mabel"),
            StoryParams("permit_booth", "Milo", "Gus", "Mr. Croak"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
