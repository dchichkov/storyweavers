#!/usr/bin/env python3
"""
A small, nursery-rhyme style storyworld about a rocky shore, a jutting stone,
a brief conflict, a friendship turn, and a lesson learned.

The domain is intentionally tiny and constraint-checked:
- a child and a small shore friend explore a rocky shore
- a jutting rock creates a risky path or hiding place
- a conflict arises over a shiny shell or tide pool find
- friendship repairs the trouble
- the ending proves the lesson learned
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
class Place:
    name: str = "the rocky shore"
    has_tide: bool = True
    has_jut: bool = True


@dataclass
class Actor:
    name: str
    role: str
    kind: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectThing:
    name: str
    phrase: str
    owner: str = ""
    held_by: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str = "Mira"
    friend_name: str = "Pip"
    prize: str = "shell"
    seed: Optional[int] = None


NAMES = ["Mira", "Toby", "Lina", "Ned", "Ada", "Ivo", "Pia", "Ollie"]
FRIEND_NAMES = ["Pip", "Sami", "Wren", "Dot", "Bram", "Nori", "Tess", "Jory"]
PRIZES = {
    "shell": "a pearly shell",
    "pebble": "a smooth pebble",
    "starfish": "a tiny starfish toy",
}


@dataclass
class World:
    place: Place
    child: Actor
    friend: Actor
    prize: ObjectThing
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme rocky shore storyworld with a jutting rock, conflict, friendship, and lesson learned."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--prize", choices=PRIZES)
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
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if friend_name == name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != friend_name])
    prize = args.prize or rng.choice(list(PRIZES))
    return StoryParams(name=name, friend_name=friend_name, prize=prize)


def _initial_state(params: StoryParams) -> World:
    child = Actor(name=params.name, role="child", kind="child", phrase=f"little {params.name}")
    friend = Actor(name=params.friend_name, role="friend", kind="friend", phrase=f"dear {params.friend_name}")
    prize = ObjectThing(name=params.prize, phrase=PRIZES[params.prize], owner=params.name)
    world = World(place=Place(), child=child, friend=friend, prize=prize)
    return world


def _start(world: World) -> None:
    w = world
    w.say(f"On the rocky shore, under a silver sky, {w.child.name} went tap-tap-tap by the sea.")
    w.say(f"Near a jutting rock, {w.friend.name} came along with a smile so spry.")
    w.say(f"{w.child.name} found {w.prize.phrase}, bright as the moon in the foam-wet light.")
    w.say(f"{w.child.name} held it close and sang a tune, for it felt so small and right.")


def _conflict(world: World) -> None:
    w = world
    w.child.memes["delight"] = 1.0
    w.child.memes["possessive"] = 1.0
    w.friend.memes["curious"] = 1.0
    w.say(f"But {w.friend.name} said, “May I see it, please?” and reached with a gentle paw.")
    w.say(f"{w.child.name} cried, “No, no, it's mine, you see!” and the two grew stiff with awe.")
    w.child.memes["conflict"] = 1.0
    w.friend.memes["hurt"] = 1.0
    w.prize.meters["risk"] = 1.0
    w.say(f"The shell rolled near the jutting rock; one bump, and it might slip to the sea.")


def _turn(world: World) -> None:
    w = world
    w.say(f"Then {w.friend.name} bent and said, “Let's share the shore and keep it safe with care.”")
    w.say(f"{w.child.name} thought of the cliff and the foamy floor, and breathed the salty air.")
    w.child.memes["regret"] = 1.0
    w.child.memes["kindness"] = 1.0
    w.child.memes["conflict"] = 0.0
    w.friend.memes["hurt"] = 0.0
    w.friend.memes["friendship"] = 1.0
    w.child.memes["friendship"] = 1.0
    w.say(f"{w.child.name} said, “I'm sorry, friend; I spoke too fast. Let's look together, two by two.”")


def _resolution(world: World) -> None:
    w = world
    w.prize.held_by = "both"
    w.prize.meters["safe"] = 1.0
    w.say(f"So side by side by the jutting stone, they made a little shell parade.")
    w.say(f"They took turns peeking, left and right, and kept the tide away.")
    w.say(f"{w.child.name} learned a lesson on the shore: kind hands make sharing sweet.")
    w.say(f"And {w.friend.name} and {w.child.name} walked home as friends, with sandy feet.")


def generate_world(params: StoryParams) -> World:
    world = _initial_state(params)
    _start(world)
    world.lines.append("")
    _conflict(world)
    world.lines.append("")
    _turn(world)
    _resolution(world)
    world.facts = {
        "child": world.child,
        "friend": world.friend,
        "prize": world.prize,
        "place": world.place,
        "lesson": "sharing and kindness keep things safe",
        "conflict": True,
        "friendship": True,
        "lesson_learned": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short nursery-rhyme story set on a rocky shore with a jutting rock.",
        f"Tell a gentle story about {f['child'].name} and {f['friend'].name} where a small conflict turns into friendship.",
        f"Write a rhyming story where {f['child'].name} learns a lesson while sharing {f['prize'].phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.child.name
    f = world.friend.name
    prize = world.prize.phrase
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer="It happens on the rocky shore, near a jutting rock and the foamy sea.",
        ),
        QAItem(
            question=f"What did {c} find?",
            answer=f"{c} found {prize} and wanted to keep it close.",
        ),
        QAItem(
            question=f"What was the conflict about?",
            answer=f"The conflict was about who could look at and hold the shell, because {c} did not want to share at first.",
        ),
        QAItem(
            question=f"How did the friendship story end?",
            answer=f"{c} and {f} became friends again by sharing, looking together, and keeping the prize safe.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that sharing and kindness keep things safe and make friendship stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rocky shore?",
            answer="A rocky shore is the edge of the sea where stones, tide pools, and waves meet the land.",
        ),
        QAItem(
            question="What does jut mean?",
            answer="If something juts, it sticks out or pokes out from the rest of the surface.",
        ),
        QAItem(
            question="Why should children be careful near slippery rocks?",
            answer="Children should be careful near slippery rocks because wet stone can be hard to stand on.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.child, world.friend, world.prize]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent is world.prize:
            bits.append(f"held_by={ent.held_by!r}")
        lines.append(f"  {ent.name:10} ({ent.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(rocky_shore).
feature(jut).
feature(conflict).
feature(friendship).
feature(lesson_learned).

valid_story(P) :- place(P), feature(jut), feature(conflict), feature(friendship), feature(lesson_learned).
#show valid_story/1.
#show feature/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "rocky_shore"),
            asp.fact("feature", "jut"),
            asp.fact("feature", "conflict"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "lesson_learned"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("rocky_shore",)}
    if clingo_set == python_set:
        print("OK: clingo gate matches Python story gate (1 valid setting).")
        return 0
    print("MISMATCH between clingo and Python story gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def explain_rejection() -> str:
    return "(No story: this world always stays on the rocky shore with its jutting rock, conflict, friendship, and lesson learned.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story setting(s):")
        for item in stories:
            print(" ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mira", friend_name="Pip", prize="shell"),
            StoryParams(name="Toby", friend_name="Wren", prize="pebble"),
            StoryParams(name="Lina", friend_name="Dot", prize="starfish"),
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
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend_name} on the rocky shore"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
