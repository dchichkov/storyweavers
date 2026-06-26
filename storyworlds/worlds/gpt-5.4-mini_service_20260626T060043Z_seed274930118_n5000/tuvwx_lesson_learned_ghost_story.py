#!/usr/bin/env python3
"""
A small storyworld for a child-friendly ghost story with a lesson learned.

Premise:
- A child enters a quiet old room and meets a shy ghost.
- The ghost keeps making spooky little noises to get attention.
- The child learns the ghost is not mean, just lonely.
- They solve the problem by helping the ghost find a gentle way to be noticed.

The seed word "tuvwx" appears as the name of a little lantern charm in the room.
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
    room: str = "attic"
    hero_name: str = "Mina"
    ghost_name: str = "Murmur"
    lesson: str = "not every spooky thing is mean"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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


ROOMS = {
    "attic": {
        "place": "the attic",
        "detail": "Dust floated in the slanted light, and old boxes lined the walls.",
        "sound": "soft creaks",
    },
    "hall": {
        "place": "the hallway",
        "detail": "The long hallway was quiet, with a cold draft near the floorboards.",
        "sound": "little taps",
    },
    "basement": {
        "place": "the basement",
        "detail": "The basement smelled like damp stone, and one lamp made a tiny pool of light.",
        "sound": "echoes",
    },
}

ASP_RULES = r"""
room(Room) :- room_name(Room).
spooky(Room) :- has_sound(Room), has_old_things(Room).
lonely(G) :- ghost(G), wants_attention(G), not heard_kindly(G).
lesson_learned(G) :- lonely(G), helped(G).
"""

HEROES = ["Mina", "Nico", "Lena", "Toby", "Iris"]
GHOSTS = ["Murmur", "Pale Pip", "Whisper", "Flick", "Hush"]
LESSONS = [
    "not every spooky thing is mean",
    "a quiet voice can ask for help",
    "friends can solve scary problems with kindness",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Child-friendly ghost story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--ghost", choices=GHOSTS)
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
    room = args.room or rng.choice(list(ROOMS))
    hero_name = args.name or rng.choice(HEROES)
    ghost_name = args.ghost or rng.choice(GHOSTS)
    lesson = rng.choice(LESSONS)
    return StoryParams(room=room, hero_name=hero_name, ghost_name=ghost_name, lesson=lesson)


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room_name", room))
        lines.append(asp.fact("has_old_things", room))
    lines.append(asp.fact("has_sound", "attic"))
    lines.append(asp.fact("has_sound", "hall"))
    lines.append(asp.fact("has_sound", "basement"))
    lines.append(asp.fact("ghost", "murmur"))
    lines.append(asp.fact("ghost", "whisper"))
    lines.append(asp.fact("wants_attention", "murmur"))
    lines.append(asp.fact("wants_attention", "whisper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1."))
    learned = set(asp.atoms(model, "lesson_learned"))
    expected = {("murmur",), ("whisper",)}
    if learned == expected:
        print("OK: ASP reasoning matches the Python world.")
        return 0
    print("MISMATCH between ASP and Python world.")
    print("ASP:", sorted(learned))
    print("Expected:", sorted(expected))
    return 1


def _ghost_rattle(world: World) -> None:
    ghost = world.get("ghost")
    ghost.meters["spook"] = ghost.meters.get("spook", 0) + 1
    ghost.memes["lonely"] = ghost.memes.get("lonely", 0) + 1
    if ("rattle", ghost.id) not in world.fired:
        world.fired.add(("rattle", ghost.id))
        world.say(f"Then there came a rattly sound, like a spoon in a teacup. It was {ghost.label} trying to be noticed.")


def generate_story(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    world = World(room=params.room)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="child",
        type="girl",
        label=params.hero_name,
        phrase=f"a curious child named {params.hero_name}",
    ))
    ghost = world.add(Entity(
        id=params.ghost_name.lower().replace(" ", "_"),
        kind="ghost",
        type="ghost",
        label=params.ghost_name,
        phrase=f"a shy ghost named {params.ghost_name}",
    ))
    charm = world.add(Entity(
        id="tuvwx",
        kind="thing",
        type="charm",
        label="tuvwx",
        phrase="a tiny lantern charm called tuvwx",
        caretaker=hero.id,
    ))

    world.say(f"One evening, {hero.label} wandered into {room['place']}. {room['detail']}")
    world.say(f"On a small shelf sat {charm.phrase}, and its glass blinked like a sleepy star.")
    world.para()
    world.say(f"{hero.label} heard {room['sound']}, and then {ghost.label} drifted out from behind a box.")
    world.say(f"{ghost.label} made a wobbling boo sound, but it did not sound cruel. It sounded lonely.")
    _ghost_rattle(world)
    world.say(f"{hero.label} stopped and held {charm.label} up high. The little light made the shadows feel smaller.")
    world.say(f'"Are you trying to scare me?" {hero.label} asked. "{ghost.label}, do you want a friend instead?"')
    world.para()
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1
    ghost.memes["friendship"] = ghost.memes.get("friendship", 0) + 1
    world.say(f"{ghost.label} nodded. It had been making spooky noises because nobody had listened before.")
    world.say(f"So {hero.label} hung tuvwx on a nail by the door and asked {ghost.label} to ring it when it wanted attention.")
    world.say(f"After that, {ghost.label} gave one soft chime and one tiny wave. {hero.label} smiled back.")
    world.say(f"That was the lesson learned: {params.lesson}.")
    world.say(f"And the attic stayed quiet and kind, with tuvwx glowing in the dark like a brave little promise.")

    world.facts.update(
        hero=hero,
        ghost=ghost,
        charm=charm,
        room=params.room,
        lesson=params.lesson,
    )

    prompts = [
        f"Write a gentle ghost story for children set in {room['place']} that includes tuvwx.",
        f"Tell a spooky-but-kind story where {params.hero_name} meets {params.ghost_name} and learns a lesson.",
        "Write a short story about a lonely ghost, a brave child, and a helpful little charm.",
    ]

    story_qa = [
        QAItem(
            question=f"Where did {params.hero_name} meet {params.ghost_name}?",
            answer=f"{params.hero_name} met {params.ghost_name} in {room['place']}.",
        ),
        QAItem(
            question=f"Why was {params.ghost_name} making spooky noises?",
            answer=f"{params.ghost_name} was trying to be noticed because it felt lonely.",
        ),
        QAItem(
            question="What was tuvwx?",
            answer="tuvwx was a tiny lantern charm that made the dark feel a little friendlier.",
        ),
        QAItem(
            question="What lesson did the story learn?",
            answer=f"The lesson was that {params.lesson}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a ghost like in this story?",
            answer="The ghost is shy, lonely, and not truly mean.",
        ),
        QAItem(
            question="What can a lantern charm do in a dark place?",
            answer="A lantern charm can give a little light and make a scary place feel calmer.",
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
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:12} ({ent.kind:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(room="attic", hero_name="Mina", ghost_name="Murmur", lesson="not every spooky thing is mean"),
    StoryParams(room="hall", hero_name="Nico", ghost_name="Whisper", lesson="a quiet voice can ask for help"),
    StoryParams(room="basement", hero_name="Iris", ghost_name="Flick", lesson="friends can solve scary problems with kindness"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show lesson_learned/1."))
        print(sorted(set(asp.atoms(model, "lesson_learned"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate_story(params)
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
            header = f"### {p.hero_name} and {p.ghost_name} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
