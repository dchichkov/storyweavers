#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/olympic_delicious_blind_flashback_inner_monologue_problem.py
=============================================================================================================================

A small Storyweavers storyworld about an Olympic day, a delicious snack, and a blind hero
who uses a flashback, inner monologue, and problem solving to find the way.

The story is designed to read like a rhyming TinyStories-style tale, while still being
driven by a simple simulated world model with physical meters and emotional memes.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    paths: list[str] = field(default_factory=list)
    goal: str = ""
    noise: str = ""


@dataclass
class Snack:
    label: str
    phrase: str
    smell: str
    reward: str


@dataclass
class StoryParams:
    place: str
    snack: str
    hero_name: str
    hero_type: str
    guide_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_hungry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    snack = world.get(world.facts["snack"].id)
    if hero.memes.get("hungry", 0) < THRESHOLD:
        return out
    if hero.meters.get("distance", 0) < THRESHOLD:
        return out
    sig = ("want_snack", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    out.append(f"{hero.id} smelled {snack.phrase} and wished for a bite.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    if hero.memes.get("lost", 0) < THRESHOLD:
        return out
    sig = ("worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append(f"{hero.id}'s heart went thump and thrum; the path felt vague, not fun.")
    return out


def _r_guided(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    guide = world.get(world.facts["guide"].id)
    if guide.meters.get("near", 0) < THRESHOLD:
        return out
    sig = ("guided", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    out.append(f"{guide.id} tapped the rail, and {hero.id} heard the beat as a trail.")
    return out


CAUSAL_RULES = [_r_hungry, _r_worry, _r_guided]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


def flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(
        f"{hero.id} remembered a bright old lane, with cones in a row and a song in the rain."
    )


def inner_monologue(world: World, hero: Entity) -> None:
    hero.memes["thought"] = hero.memes.get("thought", 0) + 1
    world.say(
        f'"I can do this," {hero.id} thought. "One small step, one tidy hop, then I will not stop."'
    )


def problem_solving(world: World, hero: Entity, guide: Entity, snack: Entity) -> None:
    hero.meters["distance"] = 0
    guide.meters["near"] = 1
    hero.memes["lost"] = 0
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} counted three tiles, then five little paces; {guide.id} rang a bell to mark the places."
    )
    propagate(world)
    world.say(
        f"At last they found the snack stand, neat and bright, with {snack.phrase} shining like light."
    )


def build_story_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    snack = SNACKS[params.snack]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name.lower(),
        meters={"distance": 2},
        memes={"hungry": 1, "lost": 1},
    ))
    guide = world.add(Entity(
        id=params.guide_name,
        kind="character",
        type="friend",
        label=params.guide_name.lower(),
        meters={"near": 0},
        memes={"kind": 1},
    ))
    snack_ent = world.add(Entity(
        id="snack",
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        meters={"smell": 1},
    ))

    world.facts.update(hero=hero, guide=guide, snack=snack_ent, snack_cfg=snack, place=place)

    world.say(
        f"At the Olympic hall, {hero.id} went with a grin, but the room seemed huge from within."
    )
    world.say(
        f"{hero.id} was blind, yet brave and bright, and followed the echo of steps just right."
    )
    world.para()

    flashback(world, hero)
    inner_monologue(world, hero)
    world.say(
        f"{hero.id} tried to go on, but the path spun around; the snack was there, yet not yet found."
    )
    propagate(world)
    world.say(
        f"{guide.id} heard the pause and stayed close by, with a soft little chime to guide."
    )
    world.para()

    problem_solving(world, hero, guide, snack_ent)
    world.say(
        f"{hero.id} took a bite of the delicious treat, and the day felt golden from head to feet."
    )
    world.say(
        f"In the Olympic hall they laughed in tune; the blind hero shone like a silver moon."
    )

    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    snack_ent.meters["eaten"] = 1
    world.facts["resolved"] = True
    return world


PLACES = {
    "hall": Place(
        name="the Olympic hall",
        indoors=True,
        paths=["tile lane", "rail", "snack stand"],
        goal="find the snack stand",
        noise="soft echoes",
    ),
    "village": Place(
        name="the Olympic village",
        indoors=False,
        paths=["path", "bench", "counter"],
        goal="reach the snack table",
        noise="happy chatter",
    ),
}

SNACKS = {
    "bun": Snack(
        label="cinnamon bun",
        phrase="a warm cinnamon bun",
        smell="sweet and cozy",
        reward="warm comfort",
    ),
    "cookie": Snack(
        label="jam cookie",
        phrase="a delicious jam cookie",
        smell="bright and fruity",
        reward="sticky joy",
    ),
    "bread": Snack(
        label="honey bread",
        phrase="a delicious honey bread slice",
        smell="golden and sweet",
        reward="gentle energy",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Tessa", "Rory", "Lena", "Eli"]
GUIDE_NAMES = ["Bea", "Jax", "Noa", "Iris", "Owen", "Maya"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, snack) for place in PLACES for snack in SNACKS]


def explain_rejection(place: str, snack: str) -> str:
    return f"(No story: the place '{place}' or snack '{snack}' is not valid here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming Olympic story world with a blind hero.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    snack = args.snack or rng.choice(list(SNACKS))
    if (place, snack) not in valid_combos():
        raise StoryError(explain_rejection(place, snack))
    hero_name = args.name or rng.choice(HERO_NAMES)
    guide_name = args.guide or rng.choice(GUIDE_NAMES)
    hero_type = "girl" if args.gender == "girl" else "boy" if args.gender == "boy" else rng.choice(["girl", "boy"])
    return StoryParams(place=place, snack=snack, hero_name=hero_name, hero_type=hero_type, guide_name=guide_name)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
        'Write a short rhyming story about an olympic day, a delicious snack, and a blind child.',
        f"Tell a gentle rhyming tale where {world.facts['hero'].id} gets lost at {world.place.name} but solves the problem with help.",
        "Use flashback, inner monologue, and problem solving in a child-friendly rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    snack = world.facts["snack"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"The story is about {hero.id}, a blind child who is trying to find {snack.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered a bright old lane with cones and practice steps, which helped make the path feel familiar.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} counted steps, followed {guide.id}'s bell, and found the snack stand safely.",
        ),
        QAItem(
            question=f"What delicious thing did they get at the end?",
            answer=f"They got {snack.phrase}, and {hero.id} took a happy bite at the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does blind mean?",
            answer="Blind means a person cannot see well or cannot see at all, so they may use sound, touch, or help from others to get around.",
        ),
        QAItem(
            question="What is an Olympic place?",
            answer="An Olympic place is a special sports area where people practice, compete, and cheer each other on.",
        ),
        QAItem(
            question="Why can a delicious snack make a day nicer?",
            answer="A delicious snack can make a day nicer because good food can fill you up and make you feel happy and strong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"place={world.place.name}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place,snack) :- place_fact(place), snack_fact(snack).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for s in SNACKS:
        lines.append(asp.fact("snack_fact", s))
    return "\n".join(lines)


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
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(place="hall", snack="cookie", hero_name="Milo", hero_type="boy", guide_name="Bea"),
    StoryParams(place="village", snack="bun", hero_name="Nina", hero_type="girl", guide_name="Jax"),
    StoryParams(place="hall", snack="bread", hero_name="Lena", hero_type="girl", guide_name="Iris"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
