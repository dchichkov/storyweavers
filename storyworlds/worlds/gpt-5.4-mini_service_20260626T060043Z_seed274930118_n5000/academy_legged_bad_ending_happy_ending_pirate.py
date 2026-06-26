#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/academy_legged_bad_ending_happy_ending_pirate.py
==============================================================================================================

A small pirate-tale story world about an academy lesson, a legged danger,
a bad ending that is avoided, and a happy ending that follows from a real fix.

The seed words suggest a story domain with an academy and something legged.
This world turns that into a pirate academy where the child hero must cross a
wobbly legged dock to reach class, but a loose peg-leg gadget can trip them up.
A careful mentor notices the risk, warns the child, and offers a better route
with a steady boardwalk instead of a risky dash.

The domain is deliberately tiny and state-driven:
- physical meters: balance, splash, damage, wobble, safety
- emotional memes: courage, worry, pride, relief, delight

The bad ending is the plausible unsafe branch; the happy ending is the
resolution when the crew uses the safe route instead.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("balance", "splash", "damage", "wobble", "safety"):
            self.meters.setdefault(k, 0.0)
        for k in ("courage", "worry", "pride", "relief", "delight", "alarm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "captain", "pirate", "mate", "man"}
        female = {"girl", "woman", "captainess", "pirateess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    legged_danger: bool = False
    safe_route: bool = False
    unsafe_route: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    mentor: str
    mentor_type: str
    seed: Optional[int] = None


PLACES = {
    "academy_dock": "the academy dock",
    "academy_yard": "the academy yard",
    "academy_hall": "the academy hall",
}

HERO_NAMES = ["Pip", "Mira", "Ned", "Tia", "Jory", "Luna"]
MENTOR_NAMES = ["Captain Brine", "Old Sal", "Mate Wren"]
TRAITS = ["brave", "curious", "bouncy", "quick", "stubborn"]


@dataclass
class Hazard:
    id: str
    label: str
    verb: str
    danger: str
    fix: str
    zone: set[str]


HAZARD = Hazard(
    id="legged_plank",
    label="the legged plank",
    verb="dash across the legged plank",
    danger="a nasty tumble",
    fix="a steady boardwalk",
    zone={"feet"},
)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


GEAR = Gear(
    id="boardwalk",
    label="a steady boardwalk",
    covers={"feet"},
    guards={"wobble", "splash"},
    prep="walk the steady boardwalk instead",
    tail="crossed the steady boardwalk",
)


def init_world(params: StoryParams) -> World:
    w = World(place=PLACES[params.place])
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    mentor = w.add(Entity(id=params.mentor, kind="character", type=params.mentor_type, label=params.mentor))
    plank = w.add(Entity(
        id="plank",
        type="thing",
        label="legged plank",
        phrase="a legged plank with crooked wooden legs",
        protective=False,
    ))
    boardwalk = w.add(Entity(
        id=GEAR.id,
        type="thing",
        label=GEAR.label,
        phrase=GEAR.label,
        protective=True,
        covers=set(GEAR.covers),
    ))
    hero.memes["courage"] += 1
    mentor.memes["pride"] += 1
    w.facts.update(hero=hero, mentor=mentor, plank=plank, boardwalk=boardwalk)
    return w


def _r_wobble(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    if hero.meters["balance"] < THRESHOLD:
        return out
    if world.safe_route:
        return out
    if world.unsafe_route and ("wobble", hero.id) not in world.fired:
        world.fired.add(("wobble", hero.id))
        hero.meters["wobble"] += 1
        hero.meters["damage"] += 1
        hero.memes["alarm"] += 1
        out.append(f"The legged plank wobbled hard under {hero.id}.")
    return out


def _r_splash(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    if hero.meters["splash"] < THRESHOLD:
        return out
    if ("splash", hero.id) in world.fired:
        return out
    world.fired.add(("splash", hero.id))
    hero.meters["damage"] += 1
    hero.memes["worry"] += 1
    out.append(f"Cold harbor water splashed up at {hero.id}'s boots.")
    return out


def _r_relief(world: World) -> list[str]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    if world.safe_route and hero.memes["relief"] < THRESHOLD and ("relief", hero.id) not in world.fired:
        world.fired.add(("relief", hero.id))
        hero.memes["relief"] += 1
        mentor.memes["pride"] += 1
        return [f"That made {hero.id} feel safe and made {mentor.id} smile."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_wobble, _r_splash, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_intro(world: World) -> None:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    world.say(f"{hero.id} was a little {hero.type} at {world.place}, and {hero.id} loved pirate academy day.")
    world.say(f"{mentor.id} taught ropes, maps, and brave feet, and {hero.id} wanted to learn every trick.")


def story_setup(world: World) -> None:
    hero = world.facts["hero"]
    hero.memes["courage"] += 1
    hero.meters["balance"] += 1
    world.say(f"One bright morning, {hero.id} hurried to {world.place} with a grin and a lesson book tucked under one arm.")
    world.say(f"{hero.id} wanted to {HAZARD.verb}, because the academy bell was already ringing.")


def story_warning(world: World) -> None:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    world.say(f'"If you rush over that {HAZARD.label}, you may have {HAZARD.danger}," {mentor.id} warned.')
    hero.memes["worry"] += 1


def bad_ending(world: World) -> None:
    hero = world.facts["hero"]
    world.unsafe_route = True
    hero.meters["balance"] += 1
    hero.meters["splash"] += 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} slipped, dropped the lesson book, and got a tear in the page.")
    world.say(f"The academy bell ended before the lesson even began, which was a very bad ending.")


def offer_fix(world: World) -> None:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    world.say(f"Then {mentor.id} pointed to {GEAR.label} and said, 'Let's {GEAR.prep}.'")
    world.say(f"{hero.id} nodded, because the safer path would keep the lesson book dry.")


def happy_ending(world: World) -> None:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    world.safe_route = True
    hero.meters["balance"] += 1
    hero.meters["safety"] += 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} {GEAR.tail} and reached the academy in time.")
    world.say(f"The lesson book stayed dry, {mentor.id} laughed kindly, and the day ended with a happy ending.")


def tell(params: StoryParams) -> World:
    world = init_world(params)
    story_intro(world)
    world.para()
    story_setup(world)
    story_warning(world)
    world.para()
    bad_ending(world)
    world.para()
    offer_fix(world)
    happy_ending(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    return [
        'Write a short pirate tale for a young child about an academy lesson, a legged danger, and a safer way to cross.',
        f"Tell a gentle story where {hero.id} wants to reach pirate academy, but {mentor.id} worries about the legged plank and offers a better path.",
        'Write a story that includes the words "academy" and "legged" and ends with a happy ending after a bad ending is avoided.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    return [
        QAItem(
            question=f"Who wanted to reach pirate academy in this story?",
            answer=f"{hero.id} wanted to reach pirate academy and learn from {mentor.id}.",
        ),
        QAItem(
            question=f"Why did {mentor.id} warn {hero.id} about the legged plank?",
            answer=f"{mentor.id} warned {hero.id} because rushing over the legged plank could lead to a nasty tumble and a torn lesson book.",
        ),
        QAItem(
            question=f"How did the story move from a bad ending to a happy ending?",
            answer=f"At first {hero.id} slipped on the unsafe path, but then {mentor.id} предложed the steady boardwalk, and that safer choice led to the happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an academy?",
            answer="An academy is a place where people go to learn lessons and practice skills.",
        ),
        QAItem(
            question="What does legged mean?",
            answer="Legged means something has legs or supports that stand on legs, like a table or a wobbly plank.",
        ),
        QAItem(
            question="Why do sailors like a steady boardwalk?",
            answer="A steady boardwalk helps people cross safely without slipping into the water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  safe_route={world.safe_route} unsafe_route={world.unsafe_route}")
    return "\n".join(lines)


ASP_RULES = r"""
% A legged danger is present when the unsafe route is chosen.
legged_danger :- unsafe_route.

% A safe ending is possible when the boardwalk is used instead of the unsafe route.
happy_ending :- safe_route, boardwalk.

% A bad ending is what happens on the unsafe route.
bad_ending :- unsafe_route, legged_danger.

% An acceptable story includes both the risk and the resolution.
valid_story :- legged_danger, happy_ending.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("academy"))
    lines.append(asp.fact("legged"))
    lines.append(asp.fact("boardwalk"))
    lines.append(asp.fact("unsafe_route"))
    lines.append(asp.fact("safe_route"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    asp_ok = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python parity check passed.")
        return 0
    print("MISMATCH: ASP and Python parity differ.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate academy story world with a legged hazard.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-type", choices=["captain", "pirate", "mate"])
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
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    mentor = args.mentor or rng.choice(MENTOR_NAMES)
    mentor_type = args.mentor_type or rng.choice(["captain", "pirate", "mate"])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, mentor=mentor, mentor_type=mentor_type)


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
    StoryParams(place="academy_dock", hero="Pip", hero_type="boy", mentor="Captain Brine", mentor_type="captain"),
    StoryParams(place="academy_yard", hero="Mira", hero_type="girl", mentor="Old Sal", mentor_type="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:", " ".join(sorted(str(s) for s in model)))
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
