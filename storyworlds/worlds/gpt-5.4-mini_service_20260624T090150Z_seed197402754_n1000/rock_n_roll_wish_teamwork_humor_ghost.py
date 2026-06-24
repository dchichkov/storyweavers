#!/usr/bin/env python3
"""
A tiny ghost-story world about a wished-for rock'n'roll performance, where
humor and teamwork turn a spooky problem into a cheerful ending.
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
    room: str = "the old attic"
    hero: str = "Mina"
    sidekick: str = "Otis"
    ghost_name: str = "Boo"
    instrument: str = "guitar"
    wish: str = "to play rock'n'roll"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    room: str
    hero: Entity
    sidekick: Entity
    ghost: Entity
    instrument: Entity
    bell: Entity
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


ROOMS = {
    "the old attic": {"spooky": True},
    "the music room": {"spooky": True},
    "the moonlit hall": {"spooky": True},
}

INSTRUMENTS = {
    "guitar": "guitar",
    "drum": "drum",
    "violin": "violin",
    "kazoo": "kazoo",
}

HERO_NAMES = ["Mina", "Jules", "Pia", "Nico", "Rae", "Theo"]
SIDEKICK_NAMES = ["Otis", "Pip", "Lena", "Bo", "Nia", "Sam"]
GHOST_NAMES = ["Boo", "Misty", "Spark", "Chime", "Wisp", "Glimmer"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with rock'n'roll, wish, teamwork, and humor.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--ghost-name")
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--wish")
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
    room = args.room or rng.choice(list(ROOMS))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    instrument = args.instrument or rng.choice(list(INSTRUMENTS))
    wish = args.wish or "to play rock'n'roll"
    if "rock'n'roll" not in wish and "rock and roll" not in wish and "rock-n-roll" not in wish:
        raise StoryError("The wish must include rock'n'roll so the story matches the seed theme.")
    return StoryParams(room=room, hero=hero, sidekick=sidekick, ghost_name=ghost_name, instrument=instrument, wish=wish)


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero == params.sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    if not params.room or not params.instrument or not params.ghost_name:
        raise StoryError("Missing a required story element.")


def tell(params: StoryParams) -> World:
    hero = Entity(params.hero, "child")
    sidekick = Entity(params.sidekick, "child")
    ghost = Entity(params.ghost_name, "ghost")
    instrument = Entity(params.instrument, "instrument")
    bell = Entity("old bell", "object")
    world = World(params.room, hero, sidekick, ghost, instrument, bell)

    hero.inc_meme("wish")
    hero.inc_meme("hope")
    ghost.inc_meme("mischief")
    ghost.inc_meme("lonely")
    instrument.inc_meter("dust", 1)
    bell.inc_meter("dust", 1)

    world.say(f"In {params.room}, {params.hero} found a dusty {params.instrument} and wished {params.wish}.")
    world.say(f"That was when {params.ghost_name} floated in, rattling an old bell with a spooky little hum.")
    world.para()

    hero.inc_meme("worry")
    sidekick.inc_meme("humor")
    ghost.inc_meme("humor")
    world.say(f"{params.hero} did not run away. {params.sidekick} winked and said, \"A ghost with a bell? That is the silliest drum solo I ever heard.\"")
    world.say(f"{params.ghost_name} blinked, then let out a tiny laugh like a squeaky violin.")
    world.say("The room grew a little less cold, because the laugh made the shadows feel friendlier.")

    world.para()
    hero.inc_meme("teamwork")
    sidekick.inc_meme("teamwork")
    ghost.inc_meme("teamwork")
    world.say(f"The three of them made a plan together: {params.hero} would strum, {params.sidekick} would tap the bell in rhythm, and {params.ghost_name} would sing the woo-woo chorus.")
    world.say(f"The first song sounded like rock'n'roll with a hiccup, but their teamwork kept the beat steady.")
    world.say(f"Then the dusty {params.instrument} rang bright and brave, and even the moon seemed to nod along.")

    world.para()
    ghost.inc_meme("joy")
    hero.inc_meme("joy")
    sidekick.inc_meme("joy")
    world.facts = {
        "room": params.room,
        "hero": params.hero,
        "sidekick": params.sidekick,
        "ghost_name": params.ghost_name,
        "instrument": params.instrument,
        "wish": params.wish,
        "resolved": True,
        "humor": True,
        "teamwork": True,
    }
    world.say(f"By the end, {params.ghost_name} was no longer scary at all; {params.hero} and {params.sidekick} were laughing, and the ghost was grinning in the glow of the lamp.")
    world.say(f"The wish came true in the happiest way: a little rock'n'roll, a little humor, and a lot of teamwork in {params.room}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly ghost story about {f['hero']} who wishes {f['wish']} in {f['room']}.",
        f"Tell a spooky-but-funny story where {f['hero']} and {f['sidekick']} team up with {f['ghost_name']} to make rock'n'roll music.",
        f"Write a short story with a ghost, a wish, humor, and teamwork ending in a cheerful music scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['hero']} wish for in {f['room']}?",
            answer=f"{f['hero']} wished {f['wish']}, and that wish led to a spooky music adventure.",
        ),
        QAItem(
            question=f"How did {f['hero']} and {f['sidekick']} handle {f['ghost_name']}?",
            answer=f"They used humor instead of fear, then used teamwork to make music with the ghost.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The ghost felt friendly, the children felt brave, and the room became a cheerful place for rock'n'roll.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character, but in a gentle story it can also be lonely, funny, or friendly.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help each other reach the same goal.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that can make people smile or laugh.",
        ),
        QAItem(
            question="What is rock'n'roll?",
            answer="Rock'n'roll is lively music with a strong beat that often makes people want to move and dance.",
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
    for e in [world.hero, world.sidekick, world.ghost, world.instrument, world.bell]:
        lines.append(f"  {e.name:10} ({e.kind:10}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_story(R, H, S, G, I) :- room(R), hero(H), sidekick(S), ghost(G), instrument(I),
                               H != S.
good_story(R, H, S, G, I) :- chosen_story(R, H, S, G, I), wish_word("rock'n'roll").
#show good_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h))
    for s in SIDEKICK_NAMES:
        lines.append(asp.fact("sidekick", s))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost", g))
    for i in INSTRUMENTS:
        lines.append(asp.fact("instrument", i))
    lines.append(asp.fact("wish_word", "rock'n'roll"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/5."))
    atoms = set(asp.atoms(model, "good_story"))
    python_ok = bool(ROOMS and HERO_NAMES and SIDEKICK_NAMES and GHOST_NAMES and INSTRUMENTS)
    if atoms and python_ok:
        print("OK: ASP gate produced at least one good story and Python registry is populated.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


CURATED = [
    StoryParams(room="the old attic", hero="Mina", sidekick="Otis", ghost_name="Boo", instrument="guitar"),
    StoryParams(room="the music room", hero="Jules", sidekick="Pip", ghost_name="Misty", instrument="drum"),
    StoryParams(room="the moonlit hall", hero="Rae", sidekick="Nia", ghost_name="Wisp", instrument="violin"),
]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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
        print(asp_program("#show good_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/5."))
        goods = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(goods)} compatible story sketches:")
        for item in goods:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.hero} in {p.room} with {p.ghost_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
