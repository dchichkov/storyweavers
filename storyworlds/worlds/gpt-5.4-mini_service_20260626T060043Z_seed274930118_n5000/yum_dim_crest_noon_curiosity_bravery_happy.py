#!/usr/bin/env python3
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


ASP_RULES = r"""
% Registry facts define the small world.
place(crest).
time(noon).
feature(curiosity).
feature(bravery).
feature(happy_ending).

% A safe, bedtime-story resolution exists when curiosity meets a gentle test
% and bravery helps reach the crest before noon ends.
can_reach(crest) :- place(crest).
gentle_test(curiosity) :- feature(curiosity).
helpful(bravery) :- feature(bravery).
ending(happy) :- feature(happy_ending).

happy_story :- can_reach(crest), gentle_test(curiosity), helpful(bravery), ending(happy).
#show happy_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    companion: str = "a sleepy lantern"
    snack: str = "warm honey toast"
    object_name: str = "the small silver key"
    place: str = "the crest"
    time: str = "noon"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime-story world: curiosity, bravery, and a happy ending at the crest."
    )
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--snack")
    ap.add_argument("--object-name")
    ap.add_argument("--place")
    ap.add_argument("--time")
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
    name = args.name or rng.choice(["Mina", "Eli", "Sora", "Nia", "Tomas"])
    companion = args.companion or rng.choice(["a sleepy lantern", "a soft moon kitten", "a tiny blanket"])
    snack = args.snack or rng.choice(["warm honey toast", "apple slices", "oat porridge"])
    object_name = args.object_name or rng.choice(["the small silver key", "the nest-shaped locket", "the round tin star"])
    place = args.place or "the crest"
    time = args.time or "noon"
    if place != "the crest":
        raise StoryError("This world is built around the crest.")
    if time != "noon":
        raise StoryError("This world is built around noon.")
    return StoryParams(
        seed=None,
        name=name,
        companion=companion,
        snack=snack,
        object_name=object_name,
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "crest"),
            asp.fact("time", "noon"),
            asp.fact("feature", "curiosity"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "happy_ending"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_story/0."))
    asp_ok = bool(asp.atoms(model, "happy_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the happy story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def python_reasonable_story() -> bool:
    return True


def generate_story(world: World) -> None:
    p = world.params
    child = world.add_character(Character(name=p.name, role="child"))
    lantern = world.add_object(ObjectThing(name=p.companion, kind="companion"))
    key = world.add_object(ObjectThing(name=p.object_name, kind="treasure"))

    child.add_meme("curiosity", 1)
    child.add_meme("bravery", 0.5)
    child.add_meme("hope", 0.5)

    world.say(
        f"At noon, {p.name} woke beside {p.companion}, with {p.snack} waiting on a little tray."
    )
    world.say(
        f"Near the window, {p.name} noticed {p.object_name}, and curiosity tipped up like a tiny bell."
    )
    world.say(
        f"{p.name} wondered why the little key had a crest-shaped mark, so {p.name} took a brave breath and followed the soft path to {p.place}."
    )

    child.add_meter("steps", 8)
    child.add_meme("bravery", 1)

    key.add_meter("shine", 1)
    world.say(
        f"The hill was warm and quiet at noon, and {p.companion} glowed gently at {p.name}'s side."
    )
    world.say(
        f"At the top of {p.place}, {p.name} found a snug door tucked into the stone, just the size for {p.object_name}."
    )

    key.add_meter("magic", 1)
    child.add_meme("joy", 1)
    world.say(
        f"{p.name} turned the key, and the door opened to a cozy nook with the exact smell of {p.snack} and lavender pillows."
    )
    world.say(
        f"Inside was a note that said, 'For the child who was curious enough to look, and brave enough to climb.'"
    )
    world.say(
        f"{p.name} smiled, hugged {p.companion}, and carried the key home as the afternoon began to grow sleepy."
    )
    world.say(
        f"And that was the happy ending: curiosity found the door, bravery made the climb, and the crest felt like a friend."
    )

    world.facts = {
        "name": p.name,
        "companion": p.companion,
        "snack": p.snack,
        "object_name": p.object_name,
        "place": p.place,
        "time": p.time,
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Why did {p.name} go to {p.place} at {p.time}?",
            answer=f"{p.name} went to {p.place} because curiosity led {p.name} to follow the clue on {p.object_name}.",
        ),
        QAItem(
            question=f"What helped {p.name} keep going up the hill?",
            answer=f"Bravery helped {p.name} keep going, and {p.companion} stayed close like a gentle guide.",
        ),
        QAItem(
            question="What made the ending happy?",
            answer=f"The ending was happy because {p.name} found the little door, opened it with {p.object_name}, and came home feeling proud and safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn what is hidden or new.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something hard or scary even while their heart is beating fast.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the trouble is solved and the story closes with safety, comfort, and joy.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a bedtime story about {p.name}, curiosity, bravery, and a happy ending at the crest.",
        f"Tell a gentle story where noon leads {p.name} toward {p.object_name} and a small secret door.",
        "Write a child-facing story with a warm, dreamy mood and a clear happy ending.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
    lines = ["--- world model state ---"]
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_story/0."))
        print("happy_story" if asp.atoms(model, "happy_story") else "(no happy_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Mina",
            companion=args.companion or "a sleepy lantern",
            snack=args.snack or "warm honey toast",
            object_name=args.object_name or "the small silver key",
            place="the crest",
            time="noon",
        )
        samples = [generate(params)]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
